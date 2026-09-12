"""
Output validator - validates all invariants and constraints.
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import List, Optional, Tuple

from .data_loader import DataLoader, Request, FinancialProfile, RequestPaymentOption
from .planner import CandidatePlan, PaymentMethod, AffordabilityStatus


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class OutputValidator:
    def __init__(self, loader: DataLoader):
        self.loader = loader

    def validate_amount_bounds(self, plan: CandidatePlan, request: Request) -> List[str]:
        errors = []
        if plan.amount_safe_to_pay < 0:
            errors.append(f"amount_safe_to_pay negative: {plan.amount_safe_to_pay}")
        if plan.amount_safe_to_pay > request.requested_amount:
            errors.append(f"amount_safe_to_pay exceeds requested: {plan.amount_safe_to_pay} > {request.requested_amount}")
        return errors

    def validate_status_values(self, plan: CandidatePlan) -> List[str]:
        errors = []
        valid_statuses = [s.value for s in AffordabilityStatus]
        if plan.affordability_status.value not in valid_statuses:
            errors.append(f"Invalid affordability_status: {plan.affordability_status.value}")
        
        valid_methods = [m.value for m in PaymentMethod]
        if plan.payment_method.value not in valid_methods:
            errors.append(f"Invalid recommended_payment_method: {plan.payment_method.value}")
        return errors

    def validate_payment_plan(self, plan: CandidatePlan, request: Request) -> List[str]:
        errors = []
        if not plan.payment_plan:
            if plan.payment_method != PaymentMethod.NOT_RECOMMENDED and plan.payment_method != PaymentMethod.WAIT:
                errors.append("Empty payment plan for non-wait/not_recommended method")
            return errors
        
        # Check chronological order
        for i in range(1, len(plan.payment_plan)):
            if plan.payment_plan[i][0] < plan.payment_plan[i-1][0]:
                errors.append("Payment plan not in chronological order")
                break
        
        # Check amounts are positive
        for d, a in plan.payment_plan:
            if a <= 0:
                errors.append(f"Non-positive payment amount: {a} on {d}")
        
        # Validate partial payment specific rules
        if plan.payment_method == PaymentMethod.PARTIAL_PAYMENT:
            if len(plan.payment_plan) != 2:
                errors.append("Partial payment must have exactly 2 payments")
            else:
                first_date, first_amt = plan.payment_plan[0]
                second_date, second_amt = plan.payment_plan[1]
                if first_date != request.request_date:
                    errors.append("First partial payment must be on request_date")
                if first_amt != plan.amount_safe_to_pay:
                    errors.append("First partial payment must equal amount_safe_to_pay")
                if second_amt != request.requested_amount - plan.amount_safe_to_pay:
                    errors.append("Second partial payment must equal remaining amount")
                if first_amt + second_amt != request.requested_amount:
                    errors.append("Partial payments must sum to requested_amount")
                if plan.earliest_full_payment_date and second_date != plan.earliest_full_payment_date:
                    errors.append("Second partial payment date must match earliest_date_for_full_payment")
        
        # Validate installment plan matches an option
        if plan.payment_method == PaymentMethod.INSTALLMENTS:
            if not plan.payment_option_id:
                errors.append("Installment plan missing payment_option_id")
            else:
                options = self.loader.get_payment_options(request.request_id)
                matched = None
                for opt in options:
                    if opt.payment_option_id == plan.payment_option_id:
                        matched = opt
                        break
                if not matched:
                    errors.append(f"Installment plan references unknown payment_option_id: {plan.payment_option_id}")
                else:
                    # Verify payment dates and amounts match
                    expected_payments = []
                    current = matched.first_payment_date
                    per_payment = matched.total_payable_amount / matched.number_of_payments
                    for i in range(matched.number_of_payments):
                        expected_payments.append((current, per_payment))
                        current += timedelta(days=matched.recurring_interval_days)
                    
                    if len(plan.payment_plan) != len(expected_payments):
                        errors.append("Installment payment count mismatch")
                    else:
                        for (pd, pa), (ed, ea) in zip(plan.payment_plan, expected_payments):
                            if pd != ed:
                                errors.append(f"Installment date mismatch: {pd} vs {ed}")
                            if abs(pa - ea) > Decimal("0.01"):
                                errors.append(f"Installment amount mismatch: {pa} vs {ea}")
        
        # Validate wait method
        if plan.payment_method == PaymentMethod.WAIT:
            if len(plan.payment_plan) != 1:
                errors.append("Wait method must have exactly 1 payment")
            elif plan.payment_plan[0][1] != request.requested_amount:
                errors.append("Wait payment must equal full requested amount")
        
        return errors

    def validate_earliest_full_payment(self, plan: CandidatePlan, request: Request) -> List[str]:
        errors = []
        if plan.affordability_status == AffordabilityStatus.AFFORDABLE_NOW:
            if plan.earliest_full_payment_date != request.request_date:
                errors.append("earliest_date_for_full_payment must equal request_date for affordable_now")
        elif plan.earliest_full_payment_date and plan.earliest_full_payment_date < request.request_date:
            errors.append("earliest_date_for_full_payment cannot be before request_date")
        return errors

    def validate_spending_changes(self, plan: CandidatePlan, request: Request) -> List[str]:
        errors = []
        changes_str = plan.spending_changes
        if not changes_str or changes_str == "none":
            return errors
        
        # Parse changes
        parts = changes_str.split("|")
        if len(parts) > 3:
            errors.append("More than 3 spending changes")
        
        seen_events = set()
        for part in parts:
            if part.startswith("stop:"):
                event_id = part[5:]
                if event_id in seen_events:
                    errors.append(f"Duplicate event in spending changes: {event_id}")
                seen_events.add(event_id)
                # Check if event exists and is flexible recurring
                event = self.loader.get_event(event_id)
                if not event:
                    errors.append(f"Spending change references unknown event: {event_id}")
                # In real implementation, check if flexible recurring
            elif part.startswith("reduce_to:"):
                # Format: reduce_to:event_id:new_amount
                rest = part[10:]
                if ":" not in rest:
                    errors.append(f"Invalid reduce_to format: {part}")
                else:
                    event_id, amount_str = rest.split(":", 1)
                    if event_id in seen_events:
                        errors.append(f"Duplicate event in spending changes: {event_id}")
                    seen_events.add(event_id)
                    event = self.loader.get_event(event_id)
                    if not event:
                        errors.append(f"Spending change references unknown event: {event_id}")
                    try:
                        Decimal(amount_str)
                    except:
                        errors.append(f"Invalid amount in reduce_to: {amount_str}")
            else:
                errors.append(f"Unknown spending change format: {part}")
        
        return errors

    def validate_minimum_balance(self, plan: CandidatePlan, request: Request) -> List[str]:
        errors = []
        profile = self.loader.get_profile(request.user_id)
        if not profile:
            return ["Profile not found for validation"]
        
        # This would require re-running forecast - simplified check
        if plan.amount_safe_to_pay > profile.current_balance - profile.minimum_balance_to_keep:
            errors.append("amount_safe_to_pay would breach minimum balance immediately")
        return errors

    def validate_deadline(self, plan: CandidatePlan, request: Request) -> List[str]:
        errors = []
        if plan.affordability_status in (AffordabilityStatus.AFFORDABLE_NOW, AffordabilityStatus.AFFORDABLE_WITH_PLAN):
            if plan.payment_plan:
                last_payment_date = plan.payment_plan[-1][0]
                if last_payment_date > request.desired_completion_date:
                    errors.append(f"Payment plan completes after desired_completion_date: {last_payment_date} > {request.desired_completion_date}")
        return errors

    def validate_plan(self, plan: CandidatePlan, request: Request) -> ValidationResult:
        all_errors = []
        all_errors.extend(self.validate_amount_bounds(plan, request))
        all_errors.extend(self.validate_status_values(plan))
        all_errors.extend(self.validate_payment_plan(plan, request))
        all_errors.extend(self.validate_earliest_full_payment(plan, request))
        all_errors.extend(self.validate_spending_changes(plan, request))
        all_errors.extend(self.validate_minimum_balance(plan, request))
        all_errors.extend(self.validate_deadline(plan, request))
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=[],
        )

    def validate_output_row(self, row: dict, request: Request) -> ValidationResult:
        """Validate a row from output.csv"""
        errors = []
        
        # Required columns
        required = [
            "request_id", "amount_safe_to_pay", "affordability_status",
            "recommended_payment_method", "payment_plan",
            "earliest_date_for_full_payment", "spending_changes_needed",
            "decision_explanation"
        ]
        for col in required:
            if col not in row:
                errors.append(f"Missing column: {col}")
        
        if errors:
            return ValidationResult(False, errors, [])
        
        # Validate request_id matches
        if row["request_id"] != request.request_id:
            errors.append(f"Request ID mismatch: {row['request_id']} vs {request.request_id}")
        
        # Validate amount bounds
        try:
            amount = Decimal(row["amount_safe_to_pay"])
            if amount < 0 or amount > request.requested_amount:
                errors.append(f"amount_safe_to_pay out of bounds: {amount}")
        except:
            errors.append("amount_safe_to_pay not a valid decimal")
        
        # Validate status
        valid_statuses = [s.value for s in AffordabilityStatus]
        if row["affordability_status"] not in valid_statuses:
            errors.append(f"Invalid affordability_status: {row['affordability_status']}")
        
        # Validate payment method
        valid_methods = [m.value for m in PaymentMethod]
        if row["recommended_payment_method"] not in valid_methods:
            errors.append(f"Invalid recommended_payment_method: {row['recommended_payment_method']}")
        
        return ValidationResult(len(errors) == 0, errors, [])


def validate_plan(loader: DataLoader, plan: CandidatePlan, request: Request) -> ValidationResult:
    validator = OutputValidator(loader)
    return validator.validate_plan(plan, request)