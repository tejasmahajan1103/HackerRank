"""
Dataset import script to populate database from CSV files.
"""
import csv
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.database import init_db, SessionLocal, engine
from database.models import (
    User, FinancialEvent, ExchangeRate, Request,
    RequestPaymentOption, Message, Image,
    EventTypeEnum, EventStatusEnum, RecurringFrequencyEnum,
    RequestTypeEnum
)


def import_dataset(dataset_path: str):
    """Import all dataset CSV files into database."""
    dataset_path = Path(dataset_path)
    db = SessionLocal()
    
    try:
        print("Initializing database...")
        init_db()
        
        # Clear existing data
        print("Clearing existing data...")
        db.query(Image).delete()
        db.query(Message).delete()
        db.query(RequestPaymentOption).delete()
        db.query(Request).delete()
        db.query(ExchangeRate).delete()
        db.query(FinancialEvent).delete()
        db.query(User).delete()
        db.commit()
        
        # Import financial_profiles.csv -> User
        print("Importing users...")
        with open(dataset_path / "financial_profiles.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                user = User(
                    user_id=row["user_id"],
                    current_balance=Decimal(row["current_balance"]),
                    minimum_balance_to_keep=Decimal(row["minimum_balance_to_keep"]),
                    home_currency=row["home_currency"],
                    financial_priorities=row["financial_priorities"],
                    protected_categories=row["protected_categories"],
                    reducible_categories=row["reducible_categories"],
                    stoppable_categories=row["stoppable_categories"],
                    payment_methods_user_will_consider=row["payment_methods_user_will_consider"],
                    max_installment_months=int(row["max_installment_months"]) if row["max_installment_months"] else None,
                )
                db.add(user)
        db.commit()
        print(f"  Imported users")
        
        # Import financial_events.csv -> FinancialEvent
        print("Importing financial events...")
        with open(dataset_path / "financial_events.csv", 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                event = FinancialEvent(
                    event_id=row["event_id"],
                    user_id=row["user_id"],
                    event_date=date.fromisoformat(row["event_date"]),
                    event_type=EventTypeEnum(row["event_type"]),
                    amount=Decimal(row["amount"]) if row["amount"] else None,
                    currency=row["currency"],
                    status=EventStatusEnum(row["status"]),
                    recurring_frequency=RecurringFrequencyEnum(row["recurring_frequency"]) if row["recurring_frequency"] else None,
                    recurring_day_of_month=int(row["recurring_day_of_month"]) if row["recurring_day_of_month"] else None,
                    linked_event_id=row["linked_event_id"] if row["linked_event_id"] else None,
                    description=row["description"],
                )
                db.add(event)
                count += 1
                if count % 1000 == 0:
                    db.commit()
                    print(f"  Imported {count} events...")
        db.commit()
        print(f"  Imported {count} financial events")
        
        # Import exchange_rates.csv -> ExchangeRate
        print("Importing exchange rates...")
        with open(dataset_path / "exchange_rates.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rate = ExchangeRate(
                    rate_date=date.fromisoformat(row["rate_date"]),
                    from_currency=row["from_currency"],
                    to_currency=row["to_currency"],
                    rate=Decimal(row["rate"]),
                )
                db.add(rate)
        db.commit()
        print(f"  Imported exchange rates")
        
        # Import requests.csv -> Request
        print("Importing requests...")
        with open(dataset_path / "requests.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                req = Request(
                    request_id=row["request_id"],
                    user_id=row["user_id"],
                    request_date=date.fromisoformat(row["request_date"]),
                    request_type=RequestTypeEnum(row["request_type"]),
                    requested_amount=Decimal(row["requested_amount"]),
                    desired_completion_date=date.fromisoformat(row["desired_completion_date"]),
                    allows_partial_payment=row["allows_partial_payment"].lower() == "true",
                    request_text=row["request_text"],
                )
                db.add(req)
        db.commit()
        print(f"  Imported requests")
        
        # Import request_payment_options.csv -> RequestPaymentOption
        print("Importing payment options...")
        with open(dataset_path / "request_payment_options.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                opt = RequestPaymentOption(
                    payment_option_id=row["payment_option_id"],
                    request_id=row["request_id"],
                    payment_method=row["payment_method"],
                    number_of_payments=int(row["number_of_payments"]),
                    first_payment_date=date.fromisoformat(row["first_payment_date"]),
                    recurring_interval_days=int(row["recurring_interval_days"]),
                    financing_fee=Decimal(row["financing_fee"]),
                    total_payable_amount=Decimal(row["total_payable_amount"]),
                )
                db.add(opt)
        db.commit()
        print(f"  Imported payment options")
        
        # Import messages.csv -> Message
        print("Importing messages...")
        with open(dataset_path / "messages.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                msg = Message(
                    message_id=row["message_id"],
                    user_id=row["user_id"],
                    request_id=row["request_id"] if row["request_id"] else None,
                    related_event_id=row["related_event_id"] if row["related_event_id"] else None,
                    message_date=date.fromisoformat(row["message_date"]),
                    message_text=row["message_text"],
                )
                db.add(msg)
        db.commit()
        print(f"  Imported messages")
        
        # Import images.csv -> Image
        print("Importing images...")
        with open(dataset_path / "images.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                img = Image(
                    image_id=row["image_id"],
                    user_id=row["user_id"],
                    request_id=row["request_id"] if row["request_id"] else None,
                    related_event_id=row["related_event_id"] if row["related_event_id"] else None,
                    image_description=row["image_description"],
                    image_path=f"media/images/{row['image_id']}.png",
                )
                db.add(img)
        db.commit()
        print(f"  Imported images")
        
        print("Dataset import completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during import: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    dataset_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..', 'dataset')
    import_dataset(dataset_path)