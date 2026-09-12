"""
Database models using SQLAlchemy.
"""
from sqlalchemy import (
    Column, String, Numeric, Date, DateTime, Integer, Boolean, Text, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import uuid
import enum

Base = declarative_base()


class RequestTypeEnum(str, enum.Enum):
    PURCHASE = "purchase"
    TRAVEL = "travel"
    EDUCATION = "education"
    FAMILY_TRANSFER = "family_transfer"
    DEBT_REPAYMENT = "debt_repayment"
    INVESTMENT = "investment"
    HOUSING = "housing"
    EMERGENCY_EXPENSE = "emergency_expense"
    OTHER = "other"


class EventTypeEnum(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    REFUND = "refund"
    DEBT_PAYMENT = "debt_payment"
    INVESTMENT_PURCHASE = "investment_purchase"
    INVESTMENT_SALE = "investment_sale"
    INVESTMENT_VALUATION = "investment_valuation"
    TRANSFER = "transfer"
    SUBSCRIPTION = "subscription"


class EventStatusEnum(str, enum.Enum):
    SETTLED = "settled"
    PENDING = "pending"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RecurringFrequencyEnum(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class AffordabilityStatusEnum(str, enum.Enum):
    AFFORDABLE_NOW = "affordable_now"
    AFFORDABLE_WITH_PLAN = "affordable_with_plan"
    AFFORDABLE_LATER = "affordable_later"
    NOT_AFFORDABLE = "not_affordable"


class PaymentMethodEnum(str, enum.Enum):
    FULL_PAYMENT = "full_payment"
    PARTIAL_PAYMENT = "partial_payment"
    INSTALLMENTS = "installments"
    WAIT = "wait"
    NOT_RECOMMENDED = "not_recommended"


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(50), primary_key=True)
    current_balance = Column(Numeric(20, 2), nullable=False)
    minimum_balance_to_keep = Column(Numeric(20, 2), nullable=False)
    home_currency = Column(String(3), nullable=False)
    financial_priorities = Column(Text)  # JSON array
    protected_categories = Column(Text)  # JSON array
    reducible_categories = Column(Text)  # JSON array
    stoppable_categories = Column(Text)  # JSON array
    payment_methods_user_will_consider = Column(Text)  # JSON array
    max_installment_months = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    financial_events = relationship("FinancialEvent", back_populates="user")
    requests = relationship("Request", back_populates="user")
    messages = relationship("Message", back_populates="user")
    images = relationship("Image", back_populates="user")


class FinancialEvent(Base):
    __tablename__ = "financial_events"
    
    event_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    event_date = Column(Date, nullable=False, index=True)
    event_type = Column(SQLEnum(EventTypeEnum), nullable=False)
    amount = Column(Numeric(20, 2))
    currency = Column(String(3), nullable=False)
    status = Column(SQLEnum(EventStatusEnum), nullable=False)
    recurring_frequency = Column(SQLEnum(RecurringFrequencyEnum))
    recurring_day_of_month = Column(Integer)
    linked_event_id = Column(String(50), ForeignKey("financial_events.event_id"), index=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="financial_events")
    linked_event = relationship("FinancialEvent", remote_side=[event_id])
    messages = relationship("Message", back_populates="related_event")
    images = relationship("Image", back_populates="related_event")


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rate_date = Column(Date, nullable=False, index=True)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(20, 8), nullable=False)
    
    __table_args__ = (
        # Unique constraint on date + currency pair
        # Note: In production, you'd want a composite unique index
    )


class Request(Base):
    __tablename__ = "requests"
    
    request_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    request_date = Column(Date, nullable=False)
    request_type = Column(SQLEnum(RequestTypeEnum), nullable=False)
    requested_amount = Column(Numeric(20, 2), nullable=False)
    desired_completion_date = Column(Date, nullable=False)
    allows_partial_payment = Column(Boolean, default=False)
    request_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="requests")
    payment_options = relationship("RequestPaymentOption", back_populates="request")
    messages = relationship("Message", back_populates="request")
    images = relationship("Image", back_populates="request")
    analysis_results = relationship("AnalysisResult", back_populates="request")


class RequestPaymentOption(Base):
    __tablename__ = "request_payment_options"
    
    payment_option_id = Column(String(50), primary_key=True)
    request_id = Column(String(50), ForeignKey("requests.request_id"), nullable=False, index=True)
    payment_method = Column(String(50), nullable=False)
    number_of_payments = Column(Integer, nullable=False)
    first_payment_date = Column(Date, nullable=False)
    recurring_interval_days = Column(Integer, default=0)
    financing_fee = Column(Numeric(20, 2), default=0)
    total_payable_amount = Column(Numeric(20, 2), nullable=False)
    
    # Relationships
    request = relationship("Request", back_populates="payment_options")


class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    request_id = Column(String(50), ForeignKey("requests.request_id"), index=True)
    related_event_id = Column(String(50), ForeignKey("financial_events.event_id"), index=True)
    message_date = Column(Date, nullable=False)
    message_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="messages")
    request = relationship("Request", back_populates="messages")
    related_event = relationship("FinancialEvent", back_populates="messages")


class Image(Base):
    __tablename__ = "images"
    
    image_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    request_id = Column(String(50), ForeignKey("requests.request_id"), index=True)
    related_event_id = Column(String(50), ForeignKey("financial_events.event_id"), index=True)
    image_description = Column(Text)
    image_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="images")
    request = relationship("Request", back_populates="images")
    related_event = relationship("FinancialEvent", back_populates="images")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(50), ForeignKey("requests.request_id"), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    amount_safe_to_pay = Column(Numeric(20, 2), nullable=False)
    affordability_status = Column(SQLEnum(AffordabilityStatusEnum), nullable=False)
    recommended_payment_method = Column(SQLEnum(PaymentMethodEnum), nullable=False)
    payment_plan = Column(Text)  # JSON
    earliest_date_for_full_payment = Column(Date)
    spending_changes_needed = Column(Text)  # JSON
    decision_explanation = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    request = relationship("Request", back_populates="analysis_results")