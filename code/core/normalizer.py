"""
Normalizer for financial events.
Handles currency conversion, lifecycle resolution, and event categorization.
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from .data_loader import DataLoader, FinancialEvent, FinancialProfile, ExchangeRate


@dataclass
class NormalizedEvent:
    event_id: str
    user_id: str
    event_date: date
    event_type: str
    amount_home: Decimal  # Amount in user's home currency
    currency: str
    status: str
    is_recurring: bool
    recurring_frequency: Optional[str]
    recurring_day_of_month: Optional[int]
    linked_event_id: Optional[str]
    description: str
    is_income: bool
    is_expense: bool
    is_protected: bool
    is_flexible: bool
    is_stoppable: bool
    is_reducible: bool
    category: str


class EventNormalizer:
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.normalized_events: Dict[str, NormalizedEvent] = {}
        self.events_by_user: Dict[str, List[NormalizedEvent]] = defaultdict(list)

    def _get_category(self, event: FinancialEvent, profile: FinancialProfile) -> str:
        desc = event.description.lower()
        if any(kw in desc for kw in ["rent", "housing", "mortgage"]):
            return "housing"
        elif any(kw in desc for kw in ["food", "groceries", "restaurant"]):
            return "food"
        elif any(kw in desc for kw in ["utilities", "electric", "water", "gas", "internet"]):
            return "utilities"
        elif any(kw in desc for kw in ["transport", "fuel", "bus", "train", "uber"]):
            return "transportation"
        elif any(kw in desc for kw in ["salary", "income", "wage", "payroll"]):
            return "income"
        elif any(kw in desc for kw in ["debt", "loan", "repayment", "emi"]):
            return "debt_payment"
        elif any(kw in desc for kw in ["investment", "invest", "mutual fund", "stock"]):
            return "investment"
        elif any(kw in desc for kw in ["entertainment", "movie", "game", "streaming"]):
            return "entertainment"
        elif any(kw in desc for kw in ["shopping", "purchase", "amazon", "flipkart"]):
            return "shopping"
        elif any(kw in desc for kw in ["subscription", "netflix", "spotify", "gym"]):
            return "subscriptions"
        elif any(kw in desc for kw in ["medical", "health", "doctor", "hospital", "pharmacy"]):
            return "medical"
        elif any(kw in desc for kw in ["education", "course", "tuition", "training"]):
            return "education"
        elif any(kw in desc for kw in ["travel", "flight", "hotel", "vacation"]):
            return "travel"
        elif any(kw in desc for kw in ["family", "transfer", "remittance"]):
            return "family_transfer"
        elif any(kw in desc for kw in ["emergency", "repair", "urgent"]):
            return "emergency"
        elif any(kw in desc for kw in ["insurance", "premium"]):
            return "insurance"
        return "other"

    def _is_protected(self, category: str, profile: FinancialProfile) -> bool:
        return category in profile.protected_categories

    def _is_flexible(self, category: str, profile: FinancialProfile) -> bool:
        return category in profile.reducible_categories

    def _is_stoppable(self, category: str, profile: FinancialProfile) -> bool:
        return category in profile.stoppable_categories

    def _is_reducible(self, category: str, profile: FinancialProfile) -> bool:
        return category in profile.reducible_categories

    def _convert_amount(self, amount: Optional[Decimal], from_currency: str, to_currency: str, rate_date: date) -> Optional[Decimal]:
        if amount is None:
            return None
        if from_currency == to_currency:
            return amount
        rate = self.loader.get_exchange_rate(rate_date, from_currency, to_currency)
        if rate is None:
            return None
        return (amount * rate).quantize(Decimal("0.01"))

    def _resolve_linked_events(self, event: FinancialEvent) -> Optional[FinancialEvent]:
        """Resolve linked event lifecycle - return the most authoritative event."""
        if not event.linked_event_id:
            return event
        linked = self.loader.get_event(event.linked_event_id)
        if not linked:
            return event
        
        # Priority: settled > scheduled > pending > cancelled/failed
        status_priority = {"settled": 4, "scheduled": 3, "pending": 2, "cancelled": 1, "failed": 0}
        event_priority = status_priority.get(event.status, 0)
        linked_priority = status_priority.get(linked.status, 0)
        
        # If linked is more authoritative, use linked for amount/status
        if linked_priority > event_priority:
            return linked
        return event

    def _find_master_recurring_event(self, event: FinancialEvent) -> FinancialEvent:
        """Find the master recurring event (the one that defines the recurring pattern)."""
        # Follow linked_event_id chain to find the root
        current = event
        visited = set()
        while current.linked_event_id and current.linked_event_id not in visited:
            visited.add(current.linked_event_id)
            linked = self.loader.get_event(current.linked_event_id)
            if not linked:
                break
            current = linked
        return current

    def normalize_all(self):
        for user_id, profile in self.loader.profiles.items():
            events = self.loader.get_events_for_user(user_id)
            home_currency = profile.home_currency
            
            # First pass: identify master recurring events
            master_events = {}  # event_id -> master event
            for event in events:
                if event.recurring_frequency:
                    master = self._find_master_recurring_event(event)
                    master_events[event.event_id] = master
            
            # Second pass: normalize events, but only generate recurring from master
            processed_masters = set()
            
            for event in events:
                # Resolve linked events for amount/status
                authoritative = self._resolve_linked_events(event)
                
                # Convert amount to home currency
                amount_home = self._convert_amount(
                    authoritative.amount,
                    authoritative.currency,
                    home_currency,
                    authoritative.event_date
                )
                
                # If amount is still None, try to extract from image
                if amount_home is None and authoritative.amount is None:
                    images = self.loader.get_images_for_event(authoritative.event_id)
                    for img in images:
                        pass
                
                category = self._get_category(authoritative, profile)
                
                # For recurring events, only the master should have is_recurring=True
                is_master = False
                if event.recurring_frequency:
                    master = master_events.get(event.event_id, event)
                    is_master = (master.event_id == event.event_id)
                    if master.event_id in processed_masters:
                        # This is a duplicate occurrence, skip normalization
                        continue
                    processed_masters.add(master.event_id)
                
                normalized = NormalizedEvent(
                    event_id=event.event_id,
                    user_id=event.user_id,
                    event_date=event.event_date,
                    event_type=event.event_type,
                    amount_home=amount_home if amount_home is not None else Decimal("0"),
                    currency=home_currency,
                    status=event.status,
                    is_recurring=is_master and event.recurring_frequency is not None,
                    recurring_frequency=event.recurring_frequency if is_master else None,
                    recurring_day_of_month=event.recurring_day_of_month if is_master else None,
                    linked_event_id=event.linked_event_id,
                    description=event.description,
                    is_income=event.event_type == "income",
                    is_expense=event.event_type == "expense",
                    is_protected=self._is_protected(category, profile),
                    is_flexible=self._is_flexible(category, profile),
                    is_stoppable=self._is_stoppable(category, profile),
                    is_reducible=self._is_reducible(category, profile),
                    category=category,
                )
                self.normalized_events[event.event_id] = normalized
                self.events_by_user[user_id].append(normalized)
            
            # Sort by date
            self.events_by_user[user_id].sort(key=lambda e: e.event_date)

    def get_normalized_events(self, user_id: str) -> List[NormalizedEvent]:
        return self.events_by_user.get(user_id, [])

    def get_normalized_event(self, event_id: str) -> Optional[NormalizedEvent]:
        return self.normalized_events.get(event_id)

    def get_recurring_events(self, user_id: str) -> List[NormalizedEvent]:
        return [e for e in self.events_by_user.get(user_id, []) if e.is_recurring]

    def get_flexible_recurring_events(self, user_id: str) -> List[NormalizedEvent]:
        return [e for e in self.get_recurring_events(user_id) if e.is_flexible]

    def get_protected_events(self, user_id: str) -> List[NormalizedEvent]:
        return [e for e in self.events_by_user.get(user_id, []) if e.is_protected]

    def get_confirmed_income(self, user_id: str, start_date: date, end_date: date) -> List[NormalizedEvent]:
        events = self.events_by_user.get(user_id, [])
        return [
            e for e in events
            if e.is_income and e.status in ("settled", "scheduled")
            and start_date <= e.event_date <= end_date
        ]

    def get_confirmed_expenses(self, user_id: str, start_date: date, end_date: date) -> List[NormalizedEvent]:
        events = self.events_by_user.get(user_id, [])
        return [
            e for e in events
            if e.is_expense and e.status in ("settled", "scheduled")
            and start_date <= e.event_date <= end_date
        ]


def normalize_events(loader: DataLoader) -> EventNormalizer:
    normalizer = EventNormalizer(loader)
    normalizer.normalize_all()
    return normalizer