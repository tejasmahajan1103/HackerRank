"""
Data loader for financial datasets.
Loads CSVs, validates schemas, and builds indexed lookups.
"""
import csv
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import date


@dataclass
class FinancialProfile:
    user_id: str
    current_balance: Decimal
    minimum_balance_to_keep: Decimal
    home_currency: str
    financial_priorities: List[str]
    protected_categories: List[str]
    reducible_categories: List[str]
    stoppable_categories: List[str]
    payment_methods_user_will_consider: List[str]
    max_installment_months: Optional[int]


@dataclass
class FinancialEvent:
    event_id: str
    user_id: str
    event_date: date
    event_type: str
    amount: Optional[Decimal]
    currency: str
    status: str
    recurring_frequency: Optional[str]
    recurring_day_of_month: Optional[int]
    linked_event_id: Optional[str]
    description: str


@dataclass
class ExchangeRate:
    rate_date: date
    from_currency: str
    to_currency: str
    rate: Decimal


@dataclass
class RequestPaymentOption:
    payment_option_id: str
    request_id: str
    payment_method: str
    number_of_payments: int
    first_payment_date: date
    recurring_interval_days: int
    financing_fee: Decimal
    total_payable_amount: Decimal


@dataclass
class Request:
    request_id: str
    user_id: str
    request_date: date
    request_type: str
    requested_amount: Decimal
    desired_completion_date: date
    allows_partial_payment: bool
    request_text: str


@dataclass
class Message:
    message_id: str
    user_id: str
    request_id: Optional[str]
    related_event_id: Optional[str]
    message_date: date
    message_text: str


@dataclass
class Image:
    image_id: str
    user_id: str
    request_id: Optional[str]
    related_event_id: Optional[str]
    image_description: str


class DataLoader:
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.profiles: Dict[str, FinancialProfile] = {}
        self.events: Dict[str, FinancialEvent] = {}
        self.events_by_user: Dict[str, List[FinancialEvent]] = {}
        self.exchange_rates: List[ExchangeRate] = {}
        self.payment_options: Dict[str, List[RequestPaymentOption]] = {}
        self.requests: List[Request] = []
        self.messages: List[Message] = []
        self.messages_by_user: Dict[str, List[Message]] = {}
        self.messages_by_request: Dict[str, List[Message]] = {}
        self.messages_by_event: Dict[str, List[Message]] = {}
        self.images: List[Image] = []
        self.images_by_user: Dict[str, List[Image]] = {}
        self.images_by_request: Dict[str, List[Image]] = {}
        self.images_by_event: Dict[str, List[Image]] = {}
        self._load_all()

    def _parse_date(self, date_str: str) -> date:
        if not date_str:
            return None
        return date.fromisoformat(date_str)

    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        if not value or value.strip() == "":
            return None
        return Decimal(value.strip())

    def _parse_int(self, value: str) -> Optional[int]:
        if not value or value.strip() == "":
            return None
        return int(value.strip())

    def _split_categories(self, value: str) -> List[str]:
        if not value:
            return []
        return [c.strip() for c in value.split(",") if c.strip()]

    def _load_profiles(self):
        path = self.dataset_path / "financial_profiles.csv"
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                profile = FinancialProfile(
                    user_id=row["user_id"],
                    current_balance=self._parse_decimal(row["current_balance"]),
                    minimum_balance_to_keep=self._parse_decimal(row["minimum_balance_to_keep"]),
                    home_currency=row["home_currency"],
                    financial_priorities=self._split_categories(row["financial_priorities"]),
                    protected_categories=self._split_categories(row["protected_categories"]),
                    reducible_categories=self._split_categories(row["reducible_categories"]),
                    stoppable_categories=self._split_categories(row["stoppable_categories"]),
                    payment_methods_user_will_consider=self._split_categories(row["payment_methods_user_will_consider"]),
                    max_installment_months=self._parse_int(row["max_installment_months"]),
                )
                self.profiles[profile.user_id] = profile

    def _load_events(self):
        path = self.dataset_path / "financial_events.csv"
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                event = FinancialEvent(
                    event_id=row["event_id"],
                    user_id=row["user_id"],
                    event_date=self._parse_date(row["event_date"]),
                    event_type=row["event_type"],
                    amount=self._parse_decimal(row["amount"]),
                    currency=row["currency"],
                    status=row["status"],
                    recurring_frequency=row["recurring_frequency"] if row["recurring_frequency"] else None,
                    recurring_day_of_month=self._parse_int(row["recurring_day_of_month"]),
                    linked_event_id=row["linked_event_id"] if row["linked_event_id"] else None,
                    description=row["description"],
                )
                self.events[event.event_id] = event
                if event.user_id not in self.events_by_user:
                    self.events_by_user[event.user_id] = []
                self.events_by_user[event.user_id].append(event)

    def _load_exchange_rates(self):
        path = self.dataset_path / "exchange_rates.csv"
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rate = ExchangeRate(
                    rate_date=self._parse_date(row["rate_date"]),
                    from_currency=row["from_currency"],
                    to_currency=row["to_currency"],
                    rate=self._parse_decimal(row["rate"]),
                )
                key = (rate.rate_date, rate.from_currency, rate.to_currency)
                self.exchange_rates[key] = rate

    def _load_payment_options(self):
        path = self.dataset_path / "request_payment_options.csv"
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                option = RequestPaymentOption(
                    payment_option_id=row["payment_option_id"],
                    request_id=row["request_id"],
                    payment_method=row["payment_method"],
                    number_of_payments=int(row["number_of_payments"]),
                    first_payment_date=self._parse_date(row["first_payment_date"]),
                    recurring_interval_days=int(row["recurring_interval_days"]),
                    financing_fee=self._parse_decimal(row["financing_fee"]),
                    total_payable_amount=self._parse_decimal(row["total_payable_amount"]),
                )
                if option.request_id not in self.payment_options:
                    self.payment_options[option.request_id] = []
                self.payment_options[option.request_id].append(option)

    def _load_requests(self):
        path = self.dataset_path / "requests.csv"
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                req = Request(
                    request_id=row["request_id"],
                    user_id=row["user_id"],
                    request_date=self._parse_date(row["request_date"]),
                    request_type=row["request_type"],
                    requested_amount=self._parse_decimal(row["requested_amount"]),
                    desired_completion_date=self._parse_date(row["desired_completion_date"]),
                    allows_partial_payment=row["allows_partial_payment"].lower() == "true",
                    request_text=row["request_text"],
                )
                self.requests.append(req)

    def _load_messages(self):
        path = self.dataset_path / "messages.csv"
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                msg = Message(
                    message_id=row["message_id"],
                    user_id=row["user_id"],
                    request_id=row["request_id"] if row["request_id"] else None,
                    related_event_id=row["related_event_id"] if row["related_event_id"] else None,
                    message_date=self._parse_date(row["message_date"]),
                    message_text=row["message_text"],
                )
                self.messages.append(msg)
                if msg.user_id not in self.messages_by_user:
                    self.messages_by_user[msg.user_id] = []
                self.messages_by_user[msg.user_id].append(msg)
                if msg.request_id:
                    if msg.request_id not in self.messages_by_request:
                        self.messages_by_request[msg.request_id] = []
                    self.messages_by_request[msg.request_id].append(msg)
                if msg.related_event_id:
                    if msg.related_event_id not in self.messages_by_event:
                        self.messages_by_event[msg.related_event_id] = []
                    self.messages_by_event[msg.related_event_id].append(msg)

    def _load_images(self):
        path = self.dataset_path / "images.csv"
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                img = Image(
                    image_id=row["image_id"],
                    user_id=row["user_id"],
                    request_id=row["request_id"] if row["request_id"] else None,
                    related_event_id=row["related_event_id"] if row["related_event_id"] else None,
                    image_description=row["image_description"],
                )
                self.images.append(img)
                if img.user_id not in self.images_by_user:
                    self.images_by_user[img.user_id] = []
                self.images_by_user[img.user_id].append(img)
                if img.request_id:
                    if img.request_id not in self.images_by_request:
                        self.images_by_request[img.request_id] = []
                    self.images_by_request[img.request_id].append(img)
                if img.related_event_id:
                    if img.related_event_id not in self.images_by_event:
                        self.images_by_event[img.related_event_id] = []
                    self.images_by_event[img.related_event_id].append(img)

    def _load_all(self):
        self._load_profiles()
        self._load_events()
        self._load_exchange_rates()
        self._load_payment_options()
        self._load_requests()
        self._load_messages()
        self._load_images()

    def get_profile(self, user_id: str) -> Optional[FinancialProfile]:
        return self.profiles.get(user_id)

    def get_events_for_user(self, user_id: str) -> List[FinancialEvent]:
        return self.events_by_user.get(user_id, [])

    def get_event(self, event_id: str) -> Optional[FinancialEvent]:
        return self.events.get(event_id)

    def get_exchange_rate(self, rate_date: date, from_currency: str, to_currency: str) -> Optional[Decimal]:
        if from_currency == to_currency:
            return Decimal("1")
        key = (rate_date, from_currency, to_currency)
        rate = self.exchange_rates.get(key)
        if rate:
            return rate.rate
        # Find closest rate on or before the date
        candidates = [
            r for (d, fc, tc), r in self.exchange_rates.items()
            if fc == from_currency and tc == to_currency and d <= rate_date
        ]
        if candidates:
            return max(candidates, key=lambda r: self.exchange_rates[
                next((k for k, v in self.exchange_rates.items() if v == r), (None, None, None))
            ].rate_date).rate
        return None

    def get_payment_options(self, request_id: str) -> List[RequestPaymentOption]:
        return self.payment_options.get(request_id, [])

    def get_request(self, request_id: str) -> Optional[Request]:
        for req in self.requests:
            if req.request_id == request_id:
                return req
        return None

    def get_messages_for_user(self, user_id: str) -> List[Message]:
        return self.messages_by_user.get(user_id, [])

    def get_messages_for_request(self, request_id: str) -> List[Message]:
        return self.messages_by_request.get(request_id, [])

    def get_messages_for_event(self, event_id: str) -> List[Message]:
        return self.messages_by_event.get(event_id, [])

    def get_images_for_user(self, user_id: str) -> List[Image]:
        return self.images_by_user.get(user_id, [])

    def get_images_for_request(self, request_id: str) -> List[Image]:
        return self.images_by_request.get(request_id, [])

    def get_images_for_event(self, event_id: str) -> List[Image]:
        return self.images_by_event.get(event_id, [])

    def get_all_requests(self) -> List[Request]:
        return self.requests


def load_data(dataset_path: str) -> DataLoader:
    return DataLoader(dataset_path)