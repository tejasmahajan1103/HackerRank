"""
FastAPI backend for Buy or Wait financial analysis.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from decimal import Decimal

# Import shared core
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.engine import create_engine, FinancialEngine
from core.data_loader import Request, FinancialProfile


# Global engine instance
engine: Optional[FinancialEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    dataset_path = os.getenv("DATASET_PATH", os.path.join(os.path.dirname(__file__), '..', '..', 'dataset'))
    engine = create_engine(dataset_path)
    yield
    engine = None


app = FastAPI(
    title="Buy or Wait API",
    description="AI-powered financial decision agent",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class AnalyzeRequest(BaseModel):
    user_id: str
    request_date: date
    request_type: str
    requested_amount: float
    desired_completion_date: date
    allows_partial_payment: bool
    request_text: str


class PaymentPlanItem(BaseModel):
    date: date
    amount: float


class AnalyzeResponse(BaseModel):
    request_id: str
    amount_safe_to_pay: float
    affordability_status: str
    recommended_payment_method: str
    payment_plan: List[PaymentPlanItem]
    earliest_date_for_full_payment: Optional[date]
    spending_changes_needed: List[str]
    decision_explanation: str


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    analysis: Optional[AnalyzeResponse] = None


class ForecastResponse(BaseModel):
    user_id: str
    start_date: date
    daily_balances: List[dict]


# Dependency to get engine
def get_engine() -> FinancialEngine:
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    return engine


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "buy-or-wait-api"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_request(request: AnalyzeRequest, eng: FinancialEngine = Depends(get_engine)):
    """Analyze a financial request."""
    # Create a Request object
    req = Request(
        request_id=f"api_{request.user_id}_{request.request_date.isoformat()}",
        user_id=request.user_id,
        request_date=request.request_date,
        request_type=request.request_type,
        requested_amount=Decimal(str(request.requested_amount)),
        desired_completion_date=request.desired_completion_date,
        allows_partial_payment=request.allows_partial_payment,
        request_text=request.request_text,
    )
    
    # We need to temporarily add this request to the engine's loader
    # For simplicity, analyze using the engine's logic directly
    from core.planner import plan_request
    from core.validator import validate_plan
    from core.ai_service import get_ai_service
    
    plan = plan_request(eng.loader, eng.normalizer, eng.forecast, req)
    
    # Validate
    validation = validate_plan(eng.loader, plan, req)
    if not validation.is_valid:
        plan = type(plan)(
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
    
    # Format response
    payment_plan_items = [
        PaymentPlanItem(date=d, amount=float(a))
        for d, a in plan.payment_plan
    ]
    
    spending_changes = []
    for event_id, (change_type, amount) in plan.spending_changes.items():
        if change_type == "stop":
            spending_changes.append(f"stop:{event_id}")
        elif change_type == "reduce":
            spending_changes.append(f"reduce_to:{event_id}:{int(amount)}")
    
    # Generate explanation
    ai = get_ai_service()
    plan_data = {
        "payment_method": plan.payment_method.value,
        "amount_safe_to_pay": float(plan.amount_safe_to_pay),
        "requested_amount": float(request.requested_amount),
        "affordability_status": plan.affordability_status.value,
        "earliest_full_payment_date": plan.earliest_full_payment_date.isoformat() if plan.earliest_full_payment_date else "",
    }
    ai_response = ai.generate_explanation(plan_data)
    explanation = ai_response.data.get("explanation", plan.explanation) if ai_response.success else plan.explanation
    
    return AnalyzeResponse(
        request_id=req.request_id,
        amount_safe_to_pay=float(plan.amount_safe_to_pay),
        affordability_status=plan.affordability_status.value,
        recommended_payment_method=plan.payment_method.value,
        payment_plan=payment_plan_items,
        earliest_date_for_full_payment=plan.earliest_full_payment_date,
        spending_changes_needed=spending_changes,
        decision_explanation=explanation,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, eng: FinancialEngine = Depends(get_engine)):
    """AI financial chat endpoint."""
    ai = eng.ai
    
    # First, try to understand if this is an affordability request
    understanding = ai.understand_request(request.message, {"user_id": request.user_id})
    
    if understanding.success and understanding.data:
        data = understanding.data
        # If it looks like a specific request, analyze it
        if data.get("amount_mentioned") and data.get("request_type") != "unknown":
            # This would need more context - for now just return AI response
            pass
    
    # Generate conversational response
    response = f"I understand you're asking about: {request.message}. "
    response += "To give you a precise answer, I'd need to analyze your specific financial situation. "
    response += "Could you provide more details about the amount, timeline, and type of expense?"
    
    return ChatResponse(response=response)


@app.get("/api/users/{user_id}", response_model=dict)
async def get_user_profile(user_id: str, eng: FinancialEngine = Depends(get_engine)):
    """Get user financial profile."""
    profile = eng.loader.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": profile.user_id,
        "current_balance": float(profile.current_balance),
        "minimum_balance_to_keep": float(profile.minimum_balance_to_keep),
        "home_currency": profile.home_currency,
        "financial_priorities": profile.financial_priorities,
        "protected_categories": profile.protected_categories,
        "reducible_categories": profile.reducible_categories,
        "stoppable_categories": profile.stoppable_categories,
        "payment_methods_user_will_consider": profile.payment_methods_user_will_consider,
        "max_installment_months": profile.max_installment_months,
    }


@app.get("/api/users/{user_id}/overview")
async def get_user_overview(user_id: str, eng: FinancialEngine = Depends(get_engine)):
    """Get user financial overview."""
    profile = eng.loader.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    events = eng.normalizer.get_normalized_events(user_id)
    recurring = [e for e in events if e.is_recurring]
    income = [e for e in events if e.is_income and e.is_recurring]
    expenses = [e for e in events if e.is_expense and e.is_recurring]
    
    return {
        "user_id": user_id,
        "current_balance": float(profile.current_balance),
        "minimum_balance": float(profile.minimum_balance_to_keep),
        "safe_to_spend": float(profile.current_balance - profile.minimum_balance_to_keep),
        "monthly_income": float(sum(e.amount_home for e in income)),
        "monthly_expenses": float(sum(e.amount_home for e in expenses)),
        "recurring_expenses_count": len(expenses),
        "currency": profile.home_currency,
    }


@app.get("/api/users/{user_id}/forecast")
async def get_forecast(user_id: str, days: int = 90, eng: FinancialEngine = Depends(get_engine)):
    """Get 90-day forecast."""
    profile = eng.loader.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    from datetime import date, timedelta
    start_date = date.today()
    result = eng.forecast.build_forecast(user_id, start_date, days)
    
    daily_data = []
    for db in result.daily_balances:
        daily_data.append({
            "date": db.date.isoformat(),
            "starting_balance": float(db.starting_balance),
            "income": float(db.income),
            "expenses": float(db.expenses),
            "ending_balance": float(db.ending_balance),
        })
    
    return {
        "user_id": user_id,
        "start_date": start_date.isoformat(),
        "forecast_days": days,
        "minimum_balance": float(profile.minimum_balance_to_keep),
        "min_projected_balance": float(result.min_balance),
        "min_balance_date": result.min_balance_date.isoformat(),
        "daily_balances": daily_data,
    }


@app.get("/api/requests/{request_id}")
async def get_request(request_id: str, eng: FinancialEngine = Depends(get_engine)):
    """Get request details and analysis."""
    request = eng.loader.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Re-analyze
    from core.planner import plan_request
    from core.validator import validate_plan
    
    plan = plan_request(eng.loader, eng.normalizer, eng.forecast, request)
    
    return {
        "request_id": request.request_id,
        "user_id": request.user_id,
        "request_date": request.request_date.isoformat(),
        "request_type": request.request_type,
        "requested_amount": float(request.requested_amount),
        "desired_completion_date": request.desired_completion_date.isoformat(),
        "allows_partial_payment": request.allows_partial_payment,
        "request_text": request.request_text,
        "analysis": {
            "amount_safe_to_pay": float(plan.amount_safe_to_pay),
            "affordability_status": plan.affordability_status.value,
            "recommended_payment_method": plan.payment_method.value,
            "payment_plan": [{"date": d.isoformat(), "amount": float(a)} for d, a in plan.payment_plan],
            "earliest_date_for_full_payment": plan.earliest_full_payment_date.isoformat() if plan.earliest_full_payment_date else None,
            "spending_changes_needed": [
                f"stop:{eid}" if ct == "stop" else f"reduce_to:{eid}:{int(amt)}"
                for eid, (ct, amt) in plan.spending_changes.items()
            ],
            "decision_explanation": plan.explanation,
        }
    }


@app.get("/api/payment-options/{request_id}")
async def get_payment_options(request_id: str, eng: FinancialEngine = Depends(get_engine)):
    """Get available payment options for a request."""
    options = eng.loader.get_payment_options(request_id)
    if not options:
        raise HTTPException(status_code=404, detail="No payment options found")
    
    return {
        "request_id": request_id,
        "options": [
            {
                "payment_option_id": opt.payment_option_id,
                "payment_method": opt.payment_method,
                "number_of_payments": opt.number_of_payments,
                "first_payment_date": opt.first_payment_date.isoformat(),
                "recurring_interval_days": opt.recurring_interval_days,
                "financing_fee": float(opt.financing_fee),
                "total_payable_amount": float(opt.total_payable_amount),
            }
            for opt in options
        ]
    }


@app.post("/api/upload")
async def upload_file():
    """Upload financial document for processing."""
    # Placeholder for file upload handling
    return {"message": "File upload endpoint - not fully implemented", "status": "placeholder"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)