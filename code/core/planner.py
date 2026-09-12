"""
Payment planner - generates and evaluates candidate payment plans.
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .data_loader import DataLoader, Request, RequestPaymentOption, FinancialProfile
from .normalizer import EventNormalizer
from .forecast import ForecastEngine, ForecastResult


class AffordabilityStatus(Enum):
    AFFORDABLE_NOW = "affordable_now"
    AFFORDABLE_WITH_PLAN = "affordable_with_plan"
    AFFORDABLE_LATER = "affordable_later"
    NOT_AFFORDABLE = "not_affordable"


class PaymentMethod(Enum):
    FULL_PAYMENT = "full_payment"
    PARTIAL_PAYMENT = "partial_payment"
    INSTALLMENTS = "installments"
    WAIT = "wait"
    NOT_RECOMMENDED = "not_recommended"


@dataclass
class CandidatePlan:
    payment_method: PaymentMethod
    payment_option_id: Optional[str]
    payment_plan: List[Tuple[date, Decimal]]  # [(date, amount), ...]
    amount_safe_to_pay: Decimal
    affordability_status: AffordabilityStatus
    earliest_full_payment_date: Optional[date]
    spending_changes: Dict[str, Tuple[str, Decimal]]  # event_id -> (type, amount)
    total_amount_paid: Decimal
    num_payments: int
    first_payment_date: date
    explanation: str
    is_safe: bool


@dataclass
class PlanRanking:
    completes_by_deadline: bool
    requires_spending_changes: bool
    total_amount_paid: Decimal
    first_payment_date: date
    num_payments: int
    payment_option_id: Optional[str]


class Planner:
    def __init__(self, loader: DataLoader, normalizer: EventNormalizer, forecast_engine: ForecastEngine):
        self.loader = loader
        self.normalizer = normalizer
        self.forecast = forecast_engine

    def _format_payment_plan(self, payments: List[Tuple[date, Decimal]]) -> str:
        if not payments:
            return "none"
        return "|".join(f"{d.isoformat()}:{int(a)}" for d, a in payments)

    def _parse_spending_changes(self, changes: Dict[str, Tuple[str, Decimal]]) -> str:
        if not changes:
            return "none"
        parts = []
        for event_id, (change_type, amount) in changes.items():
            if change_type == "stop":
                parts.append(f"stop:{event_id}")
            elif change_type == "reduce":
                parts.append(f"reduce_to:{event_id}:{int(amount)}")
        return "|".join(parts) if parts else "none"

    def generate_candidate_plans(
        self,
        request: Request,
        profile: FinancialProfile,
        amount_safe_to_pay: Decimal,
        earliest_full_payment_date: Optional[date],
    ) -> List[CandidatePlan]:
        plans = []
        min_balance = profile.minimum_balance_to_keep
        requested_amount = request.requested_amount
        request_date = request.request_date
        desired_completion = request.desired_completion_date
        accepts_partial = request.allows_partial_payment
        accepted_methods = profile.payment_methods_user_will_consider
        max_installments = profile.max_installment_months
        
        payment_options = self.loader.get_payment_options(request.request_id)
        
        # 1. Full payment
        if "full_payment" in accepted_methods:
            is_safe, _ = self.forecast.check_plan_safety(
                request.user_id, request_date,
                [(request_date, requested_amount)], min_balance
            )
            if is_safe:
                plans.append(CandidatePlan(
                    payment_method=PaymentMethod.FULL_PAYMENT,
                    payment_option_id=None,
                    payment_plan=[(request_date, requested_amount)],
                    amount_safe_to_pay=amount_safe_to_pay,
                    affordability_status=AffordabilityStatus.AFFORDABLE_NOW,
                    earliest_full_payment_date=request_date,
                    spending_changes={},
                    total_amount_paid=requested_amount,
                    num_payments=1,
                    first_payment_date=request_date,
                    explanation="Full payment is safe on request date.",
                    is_safe=True,
                ))
        
        # 2. Partial payment
        if accepts_partial and "partial_payment" in accepted_methods and amount_safe_to_pay > 0 and amount_safe_to_pay < requested_amount:
            if earliest_full_payment_date and earliest_full_payment_date <= desired_completion:
                remaining = requested_amount - amount_safe_to_pay
                payment_plan = [
                    (request_date, amount_safe_to_pay),
                    (earliest_full_payment_date, remaining),
                ]
                is_safe, _ = self.forecast.check_plan_safety(
                    request.user_id, request_date, payment_plan, min_balance
                )
                if is_safe:
                    plans.append(CandidatePlan(
                        payment_method=PaymentMethod.PARTIAL_PAYMENT,
                        payment_option_id=None,
                        payment_plan=payment_plan,
                        amount_safe_to_pay=amount_safe_to_pay,
                        affordability_status=AffordabilityStatus.AFFORDABLE_WITH_PLAN,
                        earliest_full_payment_date=earliest_full_payment_date,
                        spending_changes={},
                        total_amount_paid=requested_amount,
                        num_payments=2,
                        first_payment_date=request_date,
                        explanation=f"Pay {amount_safe_to_pay} now, remaining {remaining} on {earliest_full_payment_date}.",
                        is_safe=True,
                    ))
        
        # 3. Installments
        if "installments" in accepted_methods and max_installments and max_installments > 0:
            for option in payment_options:
                if option.payment_method != "installments":
                    continue
                if option.number_of_payments > max_installments:
                    continue
                if option.first_payment_date < request_date:
                    continue
                
                # Build installment schedule
                payment_plan = []
                current_date = option.first_payment_date
                interval = option.recurring_interval_days
                per_payment = option.total_payable_amount / option.number_of_payments
                
                for i in range(option.number_of_payments):
                    payment_plan.append((current_date, per_payment))
                    current_date += timedelta(days=interval)
                
                # Check if completes by deadline
                last_payment = payment_plan[-1][0]
                if last_payment > desired_completion:
                    continue
                
                is_safe, _ = self.forecast.check_plan_safety(
                    request.user_id, request_date, payment_plan, min_balance
                )
                if is_safe:
                    plans.append(CandidatePlan(
                        payment_method=PaymentMethod.INSTALLMENTS,
                        payment_option_id=option.payment_option_id,
                        payment_plan=payment_plan,
                        amount_safe_to_pay=amount_safe_to_pay,
                        affordability_status=AffordabilityStatus.AFFORDABLE_WITH_PLAN,
                        earliest_full_payment_date=earliest_full_payment_date,
                        spending_changes={},
                        total_amount_paid=option.total_payable_amount,
                        num_payments=option.number_of_payments,
                        first_payment_date=option.first_payment_date,
                        explanation=f"Installment plan {option.payment_option_id}: {option.number_of_payments} payments of {per_payment:.2f}.",
                        is_safe=True,
                    ))
        
        # 4. Wait (full payment becomes safe later)
        if "full_payment" in accepted_methods and earliest_full_payment_date and earliest_full_payment_date > request_date:
            if earliest_full_payment_date <= desired_completion:
                is_safe, _ = self.forecast.check_plan_safety(
                    request.user_id, request_date,
                    [(earliest_full_payment_date, requested_amount)], min_balance
                )
                if is_safe:
                    plans.append(CandidatePlan(
                        payment_method=PaymentMethod.WAIT,
                        payment_option_id=None,
                        payment_plan=[(earliest_full_payment_date, requested_amount)],
                        amount_safe_to_pay=amount_safe_to_pay,
                        affordability_status=AffordabilityStatus.AFFORDABLE_LATER,
                        earliest_full_payment_date=earliest_full_payment_date,
                        spending_changes={},
                        total_amount_paid=requested_amount,
                        num_payments=1,
                        first_payment_date=earliest_full_payment_date,
                        explanation=f"Full payment becomes safe on {earliest_full_payment_date}.",
                        is_safe=True,
                    ))
        
        # 5. Try with spending changes for partial and installments
        flexible_events = self.normalizer.get_flexible_recurring_events(request.user_id)
        
        # Try partial with spending changes
        if accepts_partial and "partial_payment" in accepted_methods and amount_safe_to_pay < requested_amount:
            # Try to find spending changes that make full payment possible
            for i in range(min(3, len(flexible_events))):
                for j in range(i + 1, min(3, len(flexible_events))):
                    changes = {}
                    # Stop event i
                    changes[flexible_events[i].event_id] = ("stop", Decimal("0"))
                    # Reduce event j
                    changes[flexible_events[j].event_id] = ("reduce", flexible_events[j].amount_home / 2)
                    
                    # Recalculate safe amount with changes
                    new_safe = self.forecast.calculate_safe_amount(
                        request.user_id, request_date, requested_amount, min_balance
                    )
                    
                    # Check if this enables partial payment
                    if new_safe > amount_safe_to_pay and new_safe < requested_amount:
                        if earliest_full_payment_date and earliest_full_payment_date <= desired_completion:
                            remaining = requested_amount - new_safe
                            payment_plan = [
                                (request_date, new_safe),
                                (earliest_full_payment_date, remaining),
                            ]
                            is_safe, _ = self.forecast.check_plan_safety(
                                request.user_id, request_date, payment_plan, min_balance, changes
                            )
                            if is_safe:
                                plans.append(CandidatePlan(
                                    payment_method=PaymentMethod.PARTIAL_PAYMENT,
                                    payment_option_id=None,
                                    payment_plan=payment_plan,
                                    amount_safe_to_pay=new_safe,
                                    affordability_status=AffordabilityStatus.AFFORDABLE_WITH_PLAN,
                                    earliest_full_payment_date=earliest_full_payment_date,
                                    spending_changes=changes,
                                    total_amount_paid=requested_amount,
                                    num_payments=2,
                                    first_payment_date=request_date,
                                    explanation=f"Partial payment with spending changes: stop {flexible_events[i].event_id}, reduce {flexible_events[j].event_id}.",
                                    is_safe=True,
                                ))
        
        # Try installments with spending changes
        if "installments" in accepted_methods and max_installments and max_installments > 0:
            for option in payment_options:
                if option.payment_method != "installments":
                    continue
                if option.number_of_payments > max_installments:
                    continue
                
                for i in range(min(3, len(flexible_events))):
                    changes = {}
                    changes[flexible_events[i].event_id] = ("stop", Decimal("0"))
                    
                    payment_plan = []
                    current_date = option.first_payment_date
                    interval = option.recurring_interval_days
                    per_payment = option.total_payable_amount / option.number_of_payments
                    
                    for k in range(option.number_of_payments):
                        payment_plan.append((current_date, per_payment))
                        current_date += timedelta(days=interval)
                    
                    last_payment = payment_plan[-1][0]
                    if last_payment > desired_completion:
                        continue
                    
                    is_safe, _ = self.forecast.check_plan_safety(
                        request.user_id, request_date, payment_plan, min_balance, changes
                    )
                    if is_safe:
                        plans.append(CandidatePlan(
                            payment_method=PaymentMethod.INSTALLMENTS,
                            payment_option_id=option.payment_option_id,
                            payment_plan=payment_plan,
                            amount_safe_to_pay=amount_safe_to_pay,
                            affordability_status=AffordabilityStatus.AFFORDABLE_WITH_PLAN,
                            earliest_full_payment_date=earliest_full_payment_date,
                            spending_changes=changes,
                            total_amount_paid=option.total_payable_amount,
                            num_payments=option.number_of_payments,
                            first_payment_date=option.first_payment_date,
                            explanation=f"Installment plan {option.payment_option_id} with spending reduction.",
                            is_safe=True,
                        ))
        
        return plans

    def rank_plans(self, plans: List[CandidatePlan], request: Request) -> List[CandidatePlan]:
        """
        Rank plans according to specification:
        1. Complete full request by desired_completion_date
        2. Require no spending changes
        3. Minimize total amount paid
        4. Start payment earlier
        5. Use fewer payments
        6. Lowest payment_option_id
        """
        def rank_key(plan: CandidatePlan) -> PlanRanking:
            completes_by_deadline = plan.payment_plan[-1][0] <= request.desired_completion_date
            requires_spending_changes = bool(plan.spending_changes)
            return PlanRanking(
                completes_by_deadline=completes_by_deadline,
                requires_spending_changes=requires_spending_changes,
                total_amount_paid=plan.total_amount_paid,
                first_payment_date=plan.first_payment_date,
                num_payments=plan.num_payments,
                payment_option_id=plan.payment_option_id or "zzz",
            )
        
        return sorted(plans, key=lambda p: (
            not rank_key(p).completes_by_deadline,
            rank_key(p).requires_spending_changes,
            rank_key(p).total_amount_paid,
            rank_key(p).first_payment_date,
            rank_key(p).num_payments,
            rank_key(p).payment_option_id,
        ))

    def select_best_plan(self, request: Request) -> CandidatePlan:
        profile = self.loader.get_profile(request.user_id)
        if not profile:
            return CandidatePlan(
                payment_method=PaymentMethod.NOT_RECOMMENDED,
                payment_option_id=None,
                payment_plan=[],
                amount_safe_to_pay=Decimal("0"),
                affordability_status=AffordabilityStatus.NOT_AFFORDABLE,
                earliest_full_payment_date=None,
                spending_changes={},
                total_amount_paid=Decimal("0"),
                num_payments=0,
                first_payment_date=request.request_date,
                explanation="User profile not found.",
                is_safe=False,
            )
        
        min_balance = profile.minimum_balance_to_keep
        
        # Calculate safe amount and earliest full payment date
        amount_safe_to_pay = self.forecast.calculate_safe_amount(
            request.user_id, request.request_date, request.requested_amount, min_balance
        )
        
        earliest_full_payment_date = self.forecast.calculate_earliest_full_payment_date(
            request.user_id, request.request_date, request.requested_amount, min_balance
        )
        
        # Generate candidates
        plans = self.generate_candidate_plans(
            request, profile, amount_safe_to_pay, earliest_full_payment_date
        )
        
        if not plans:
            return CandidatePlan(
                payment_method=PaymentMethod.NOT_RECOMMENDED,
                payment_option_id=None,
                payment_plan=[],
                amount_safe_to_pay=amount_safe_to_pay,
                affordability_status=AffordabilityStatus.NOT_AFFORDABLE,
                earliest_full_payment_date=earliest_full_payment_date,
                spending_changes={},
                total_amount_paid=Decimal("0"),
                num_payments=0,
                first_payment_date=request.request_date,
                explanation="No safe payment plan found within forecast period.",
                is_safe=False,
            )
        
        # Rank and select best
        ranked = self.rank_plans(plans, request)
        best = ranked[0]
        
        # Set affordability status based on method
        if best.payment_method == PaymentMethod.FULL_PAYMENT:
            best.affordability_status = AffordabilityStatus.AFFORDABLE_NOW
        elif best.payment_method in (PaymentMethod.PARTIAL_PAYMENT, PaymentMethod.INSTALLMENTS):
            best.affordability_status = AffordabilityStatus.AFFORDABLE_WITH_PLAN
        elif best.payment_method == PaymentMethod.WAIT:
            best.affordability_status = AffordabilityStatus.AFFORDABLE_LATER
        else:
            best.affordability_status = AffordabilityStatus.NOT_AFFORDABLE
        
        return best


def plan_request(loader: DataLoader, normalizer: EventNormalizer, forecast: ForecastEngine, request: Request) -> CandidatePlan:
    planner = Planner(loader, normalizer, forecast)
    return planner.select_best_plan(request)