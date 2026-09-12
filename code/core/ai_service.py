"""
AI service layer for message interpretation, image understanding, and explanation generation.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date
import json
import os


@dataclass
class AIResponse:
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    tokens_used: Dict[str, int]
    cost_estimate: float


class AIService:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "local")
        self.model = os.getenv("AI_MODEL", "local-fallback")
        self.api_key = os.getenv("AI_API_KEY")
        self.total_tokens = {"input": 0, "output": 0, "total": 0}
        self.call_count = 0
        self.cost_per_token = 0.00001  # Rough estimate
    
    def _track_usage(self, input_tokens: int, output_tokens: int):
        self.call_count += 1
        self.total_tokens["input"] += input_tokens
        self.total_tokens["output"] += output_tokens
        self.total_tokens["total"] += input_tokens + output_tokens
    
    def interpret_message(self, message_text: str, context: Dict[str, Any]) -> AIResponse:
        """
        Interpret a message for financial relevance.
        Returns structured data about confirmations, amendments, cancellations, etc.
        """
        # Local deterministic fallback
        result = {
            "confirms_income": False,
            "amends_income": None,
            "cancels_income": False,
            "delays_income": None,
            "confirms_expense": False,
            "changes_expense_amount": None,
            "cancels_expense": False,
            "delays_payment": None,
            "clarifies_transaction": False,
            "provides_context": message_text[:200],
        }
        
        text_lower = message_text.lower()
        if "confirmed" in text_lower or "confirms" in text_lower:
            result["confirms_income"] = "salary" in text_lower or "income" in text_lower
            result["confirms_expense"] = "expense" in text_lower or "bill" in text_lower or "payment" in text_lower
        if "delay" in text_lower:
            result["delays_payment"] = "delayed"
        if "cancel" in text_lower:
            result["cancels_expense"] = "expense" in text_lower
            result["cancels_income"] = "income" in text_lower or "salary" in text_lower
        
        self._track_usage(100, 50)
        return AIResponse(True, result, None, {"input": 100, "output": 50, "total": 150}, 0.0015)
    
    def extract_image_facts(self, image_path: str, image_description: str, context: Dict[str, Any]) -> AIResponse:
        """
        Extract financial facts from an image.
        In production, this would use a multimodal model.
        """
        # Local deterministic fallback - parse description
        result = {
            "amount": None,
            "currency": None,
            "date": None,
            "type": None,
            "net_salary": None,
            "bill_amount": None,
            "receipt_total": None,
            "payment_amount": None,
            "confidence": 0.5,
        }
        
        desc_lower = image_description.lower()
        if "salary" in desc_lower or "payroll" in desc_lower:
            result["type"] = "income"
            result["net_salary"] = "extracted from image"
        elif "bill" in desc_lower or "invoice" in desc_lower:
            result["type"] = "expense"
            result["bill_amount"] = "extracted from image"
        elif "receipt" in desc_lower:
            result["type"] = "expense"
            result["receipt_total"] = "extracted from image"
        elif "payslip" in desc_lower:
            result["type"] = "income"
            result["net_salary"] = "extracted from image"
        elif "statement" in desc_lower:
            result["type"] = "expense"
            result["payment_amount"] = "extracted from image"
        
        self._track_usage(200, 100)
        return AIResponse(True, result, None, {"input": 200, "output": 100, "total": 300}, 0.003)
    
    def generate_explanation(self, plan_data: Dict[str, Any]) -> AIResponse:
        """
        Generate human-readable explanation for a financial decision.
        """
        method = plan_data.get("payment_method", "unknown")
        amount = plan_data.get("amount_safe_to_pay", 0)
        requested = plan_data.get("requested_amount", 0)
        status = plan_data.get("affordability_status", "unknown")
        
        explanations = {
            "full_payment": f"Full payment of {amount} is safe. Your forecast shows you'll stay above minimum balance.",
            "partial_payment": f"Partial payment of {amount} now, remaining {requested - amount} later. This keeps you within safe limits.",
            "installments": f"Installment plan spreads the cost over manageable payments while maintaining your minimum balance.",
            "wait": f"Waiting until {plan_data.get('earliest_full_payment_date', 'a later date')} allows full payment safely.",
            "not_recommended": f"The request of {requested} cannot be safely accommodated within your 90-day forecast.",
        }
        
        explanation = explanations.get(method, "Unable to generate explanation.")
        
        self._track_usage(150, 100)
        return AIResponse(True, {"explanation": explanation}, None, {"input": 150, "output": 100, "total": 250}, 0.0025)
    
    def understand_request(self, request_text: str, user_context: Dict[str, Any]) -> AIResponse:
        """
        Parse natural language request to extract structured intent.
        """
        result = {
            "request_type": "purchase",
            "amount_mentioned": None,
            "currency_mentioned": None,
            "deadline_mentioned": None,
            "urgency": "normal",
        }
        
        text_lower = request_text.lower()
        if "laptop" in text_lower:
            result["request_type"] = "purchase"
        elif "travel" in text_lower or "trip" in text_lower:
            result["request_type"] = "travel"
        elif "course" in text_lower or "education" in text_lower:
            result["request_type"] = "education"
        elif "transfer" in text_lower or "send" in text_lower:
            result["request_type"] = "family_transfer"
        elif "loan" in text_lower or "debt" in text_lower or "repayment" in text_lower:
            result["request_type"] = "debt_repayment"
        elif "invest" in text_lower:
            result["request_type"] = "investment"
        elif "deposit" in text_lower or "housing" in text_lower or "rent" in text_lower:
            result["request_type"] = "housing"
        elif "repair" in text_lower or "emergency" in text_lower or "urgent" in text_lower:
            result["request_type"] = "emergency_expense"
        elif "membership" in text_lower:
            result["request_type"] = "other"
        
        # Try to extract amount (simplified)
        import re
        amounts = re.findall(r'[\d,]+\.?\d*', request_text)
        if amounts:
            result["amount_mentioned"] = amounts[0].replace(",", "")
        
        self._track_usage(150, 75)
        return AIResponse(True, result, None, {"input": 150, "output": 75, "total": 225}, 0.00225)
    
    def get_usage_report(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "total_calls": self.call_count,
            "input_tokens": self.total_tokens["input"],
            "output_tokens": self.total_tokens["output"],
            "total_tokens": self.total_tokens["total"],
            "avg_tokens_per_request": self.total_tokens["total"] / max(1, self.call_count),
            "estimated_total_cost": self.total_tokens["total"] * self.cost_per_token,
            "estimated_cost_per_request": (self.total_tokens["total"] * self.cost_per_token) / max(1, self.call_count),
        }


# Global AI service instance
_ai_service = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service