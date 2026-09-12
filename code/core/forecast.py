"""
90-day cash flow forecast engine.
Builds chronological timeline, calculates safe amounts, and earliest safe dates.
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from .data_loader import DataLoader, FinancialProfile, Request
from .normalizer import EventNormalizer, NormalizedEvent


@dataclass
class DailyBalance:
    date: date
    starting_balance: Decimal
    income: Decimal
    expenses: Decimal
    ending_balance: Decimal
    events: List[Tuple[str, str, Decimal]]  # (event_id, type, amount)


@dataclass
class ForecastResult:
    daily_balances: List[DailyBalance]
    min_balance: Decimal
    min_balance_date: date
    safe_to_pay_today: Decimal
    earliest_full_payment_date: Optional[date]


class ForecastEngine:
    def __init__(self, loader: DataLoader, normalizer: EventNormalizer):
        self.loader = loader
        self.normalizer = normalizer

    def _generate_recurring_dates(self, event: NormalizedEvent, start_date: date, end_date: date) -> List[date]:
        """Generate all occurrence dates for a recurring event within the forecast window."""
        dates = []
        if not event.is_recurring or not event.recurring_frequency or not event.recurring_day_of_month:
            return dates
        
        current = event.event_date
        # If the first occurrence is before start_date, find the first occurrence >= start_date
        while current < start_date:
            if event.recurring_frequency == "monthly":
                # Add one month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            elif event.recurring_frequency == "weekly":
                current += timedelta(weeks=1)
            elif event.recurring_frequency == "daily":
                current += timedelta(days=1)
            else:
                break
        
        while current <= end_date:
            dates.append(current)
            if event.recurring_frequency == "monthly":
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            elif event.recurring_frequency == "weekly":
                current += timedelta(weeks=1)
            elif event.recurring_frequency == "daily":
                current += timedelta(days=1)
            else:
                break
        
        return dates

    def build_forecast(
        self,
        user_id: str,
        start_date: date,
        forecast_days: int = 90,
        additional_payments: Optional[List[Tuple[date, Decimal]]] = None,
        spending_changes: Optional[Dict[str, Tuple[str, Decimal]]] = None,
        initial_balance: Optional[Decimal] = None,
    ) -> ForecastResult:
        """
        Build 90-day cash flow forecast.
        
        Args:
            user_id: User to forecast for
            start_date: Forecast start date (typically request_date)
            forecast_days: Number of days to forecast (default 90)
            additional_payments: List of (date, amount) for proposed payments
            spending_changes: Dict of event_id -> (change_type, new_amount) where change_type is "stop" or "reduce"
            initial_balance: Starting balance (defaults to profile.current_balance)
        """
        profile = self.loader.get_profile(user_id)
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")
        
        end_date = start_date + timedelta(days=forecast_days - 1)
        events = self.normalizer.get_normalized_events(user_id)
        
        # Use provided initial balance or profile current_balance
        starting_balance = initial_balance if initial_balance is not None else profile.current_balance
        
        # Build daily cash flows
        daily_flows = defaultdict(lambda: {"income": Decimal("0"), "expenses": Decimal("0"), "events": []})
        
        # Add recurring events
        for event in events:
            if event.is_recurring:
                dates = self._generate_recurring_dates(event, start_date, end_date)
                for d in dates:
                    if spending_changes and event.event_id in spending_changes:
                        change_type, new_amount = spending_changes[event.event_id]
                        if change_type == "stop":
                            continue  # Skip this event
                        elif change_type == "reduce":
                            amount = new_amount
                        else:
                            amount = event.amount_home
                    else:
                        amount = event.amount_home
                    
                    if event.is_income:
                        daily_flows[d]["income"] += amount
                        daily_flows[d]["events"].append((event.event_id, "income", amount))
                    else:
                        daily_flows[d]["expenses"] += amount
                        daily_flows[d]["events"].append((event.event_id, "expense", amount))
            else:
                # One-time event within forecast window
                if start_date <= event.event_date <= end_date:
                    if spending_changes and event.event_id in spending_changes:
                        change_type, new_amount = spending_changes[event.event_id]
                        if change_type == "stop":
                            continue
                        elif change_type == "reduce":
                            amount = new_amount
                        else:
                            amount = event.amount_home
                    else:
                        amount = event.amount_home
                    
                    if event.is_income:
                        daily_flows[event.event_date]["income"] += amount
                        daily_flows[event.event_date]["events"].append((event.event_id, "income", amount))
                    else:
                        daily_flows[event.event_date]["expenses"] += amount
                        daily_flows[event.event_date]["events"].append((event.event_id, "expense", amount))
        
        # Add additional payments (proposed request payments)
        if additional_payments:
            for pay_date, amount in additional_payments:
                if start_date <= pay_date <= end_date:
                    daily_flows[pay_date]["expenses"] += amount
                    daily_flows[pay_date]["events"].append(("request_payment", "expense", amount))
        
        # Calculate daily balances
        daily_balances = []
        current_balance = starting_balance
        min_balance = current_balance
        min_balance_date = start_date
        
        for i in range(forecast_days):
            d = start_date + timedelta(days=i)
            flows = daily_flows.get(d, {"income": Decimal("0"), "expenses": Decimal("0"), "events": []})
            
            starting = current_balance
            income = flows["income"]
            expenses = flows["expenses"]
            ending = starting + income - expenses
            
            daily_balances.append(DailyBalance(
                date=d,
                starting_balance=starting,
                income=income,
                expenses=expenses,
                ending_balance=ending,
                events=flows["events"],
            ))
            
            if ending < min_balance:
                min_balance = ending
                min_balance_date = d
            
            current_balance = ending
        
        return ForecastResult(
            daily_balances=daily_balances,
            min_balance=min_balance,
            min_balance_date=min_balance_date,
            safe_to_pay_today=Decimal("0"),  # Will be calculated separately
            earliest_full_payment_date=None,  # Will be calculated separately
        )

    def build_forecast_from_balance(
        self,
        user_id: str,
        start_date: date,
        initial_balance: Decimal,
        forecast_days: int = 90,
        additional_payments: Optional[List[Tuple[date, Decimal]]] = None,
        spending_changes: Optional[Dict[str, Tuple[str, Decimal]]] = None,
    ) -> ForecastResult:
        """Build forecast with a specific initial balance."""
        return self.build_forecast(user_id, start_date, forecast_days, additional_payments, spending_changes, initial_balance)

    def calculate_safe_amount(
        self,
        user_id: str,
        request_date: date,
        requested_amount: Decimal,
        min_balance: Decimal,
    ) -> Decimal:
        """
        Calculate the maximum amount that can be safely paid on request_date
        without breaking minimum balance over 90-day forecast.
        """
        profile = self.loader.get_profile(user_id)
        if not profile:
            return Decimal("0")
        
        # Binary search for maximum safe amount
        low = Decimal("0")
        high = min(requested_amount, profile.current_balance - min_balance)
        if high <= 0:
            return Decimal("0")
        
        best = Decimal("0")
        # Use integer-based binary search for exact precision
        low_int = 0
        high_int = int(high)
        best_int = 0
        
        while low_int <= high_int:
            mid_int = (low_int + high_int) // 2
            mid = Decimal(str(mid_int))
            forecast = self.build_forecast(
                user_id, request_date,
                additional_payments=[(request_date, mid)]
            )
            if forecast.min_balance >= min_balance:
                best_int = mid_int
                low_int = mid_int + 1
            else:
                high_int = mid_int - 1
        
        return Decimal(str(best_int))

    def calculate_earliest_full_payment_date(
        self,
        user_id: str,
        request_date: date,
        requested_amount: Decimal,
        min_balance: Decimal,
        max_days: int = 90,
    ) -> Optional[date]:
        """
        Find the earliest date when full amount can be paid safely.
        """
        profile = self.loader.get_profile(user_id)
        if not profile:
            return None
        
        # First, build a baseline forecast from request_date to get projected balances
        baseline = self.build_forecast(user_id, request_date, max_days)
        balance_by_date = {db.date: db.ending_balance for db in baseline.daily_balances}
        balance_by_date[request_date - timedelta(days=1)] = profile.current_balance
        
        end_search = request_date + timedelta(days=max_days)
        current = request_date
        
        while current <= end_search:
            # Get the projected balance at the start of this date
            start_balance = balance_by_date.get(current - timedelta(days=1), profile.current_balance)
            
            # Build forecast from this date with correct starting balance
            forecast = self.build_forecast_from_balance(
                user_id, current, start_balance,
                additional_payments=[(current, requested_amount)]
            )
            if forecast.min_balance >= min_balance:
                return current
            current += timedelta(days=1)
        
        return None

    def check_plan_safety(
        self,
        user_id: str,
        request_date: date,
        payment_plan: List[Tuple[date, Decimal]],
        min_balance: Decimal,
    ) -> Tuple[bool, ForecastResult]:
        """
        Check if a payment plan is safe over 90-day forecast.
        Returns (is_safe, forecast_result)
        """
        forecast = self.build_forecast(
            user_id, request_date,
            additional_payments=payment_plan
        )
        return forecast.min_balance >= min_balance, forecast


def build_forecast(loader: DataLoader, normalizer: EventNormalizer) -> ForecastEngine:
    return ForecastEngine(loader, normalizer)