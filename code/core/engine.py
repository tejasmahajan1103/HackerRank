"""
Core financial engine - main orchestrator.
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import List, Optional

from .data_loader import DataLoader, Request, FinancialProfile
from .normalizer import EventNormalizer, normalize_events
from .forecast import ForecastEngine, build_forecast
from .planner import CandidatePlan, plan_request
from .validator import validate_plan, OutputValidator
from .ai_service import get_ai_service


@dataclass
class AnalysisResult:
    request_id: str
    amount_safe_to_pay: Decimal
    affordability_status: str
    recommended_payment_method: str
    payment_plan: str
    earliest_date_for_full_payment: str
    spending_changes_needed: str
    decision_explanation: str


class FinancialEngine:
    def __init__(self, dataset_path: str):
        self.loader = DataLoader(dataset_path)
        self.normalizer = normalize_events(self.loader)
        self.forecast = build_forecast(self.loader, self.normalizer)
        self.ai = get_ai_service()
        self.validator = OutputValidator(self.loader)
    
    def analyze_request(self, request: Request) -> AnalysisResult:
        """Analyze a single request and return the recommendation."""
        plan = plan_request(self.loader, self.normalizer, self.forecast, request)
        
        # Validate
        validation = validate_plan(self.loader, plan, request)
        if not validation.is_valid:
            # Fallback to not_recommended
            plan = CandidatePlan(
                payment_method=plan.payment_method,
                payment_option_id=plan.payment_option_id,
                payment_plan=[],
                amount_safe_to_pay=plan.amount_safe_to_pay,
                affordability_status=plan.affordability_status,
                earliest_full_payment_date=plan.earliest_full_payment_date,
                spending_changes={},
                total_amount_paid=Decimal("0"),
                num_payments=0,
                first_payment_date=request.request_date,
                explanation="Validation failed: " + "; ".join(validation.errors),
                is_safe=False,
            )
        
        # Format payment plan
        if plan.payment_plan:
            payment_plan_str = "|".join(f"{d.isoformat()}:{int(a)}" for d, a in plan.payment_plan)
        else:
            payment_plan_str = "none"
        
        # Format earliest date
        earliest_str = plan.earliest_full_payment_date.isoformat() if plan.earliest_full_payment_date else ""
        
        # Format spending changes
        if plan.spending_changes:
            parts = []
            for event_id, (change_type, amount) in plan.spending_changes.items():
                if change_type == "stop":
                    parts.append(f"stop:{event_id}")
                elif change_type == "reduce":
                    parts.append(f"reduce_to:{event_id}:{int(amount)}")
            spending_changes_str = "|".join(parts)
        else:
            spending_changes_str = "none"
        
        # Generate explanation using AI
        plan_data = {
            "payment_method": plan.payment_method.value,
            "amount_safe_to_pay": float(plan.amount_safe_to_pay),
            "requested_amount": float(request.requested_amount),
            "affordability_status": plan.affordability_status.value,
            "earliest_full_payment_date": earliest_str,
        }
        ai_response = self.ai.generate_explanation(plan_data)
        explanation = ai_response.data.get("explanation", plan.explanation) if ai_response.success else plan.explanation
        
        return AnalysisResult(
            request_id=request.request_id,
            amount_safe_to_pay=plan.amount_safe_to_pay,
            affordability_status=plan.affordability_status.value,
            recommended_payment_method=plan.payment_method.value,
            payment_plan=payment_plan_str,
            earliest_date_for_full_payment=earliest_str,
            spending_changes_needed=spending_changes_str,
            decision_explanation=explanation,
        )
    
    def analyze_all_requests(self) -> List[AnalysisResult]:
        """Analyze all requests in the dataset."""
        results = []
        for request in self.loader.get_all_requests():
            result = self.analyze_request(request)
            results.append(result)
        return results
    
    def export_to_csv(self, results: List[AnalysisResult], output_path: str):
        """Export results to CSV format."""
        import csv
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "request_id", "amount_safe_to_pay", "affordability_status",
                "recommended_payment_method", "payment_plan",
                "earliest_date_for_full_payment", "spending_changes_needed",
                "decision_explanation"
            ])
            for r in results:
                writer.writerow([
                    r.request_id,
                    str(r.amount_safe_to_pay),
                    r.affordability_status,
                    r.recommended_payment_method,
                    r.payment_plan,
                    r.earliest_date_for_full_payment,
                    r.spending_changes_needed,
                    r.decision_explanation,
                ])
    
    def get_usage_report(self) -> dict:
        return self.ai.get_usage_report()


def create_engine(dataset_path: str) -> FinancialEngine:
    return FinancialEngine(dataset_path)