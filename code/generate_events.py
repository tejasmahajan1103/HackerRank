"""
Generate comprehensive financial events for all users.
"""
import csv
from datetime import date, timedelta
from decimal import Decimal
import random

# Load existing profiles to get user configs
profiles = {}
with open('D:/FILES/Projects/HackerRank/dataset/financial_profiles.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        profiles[row['user_id']] = row

# Generate events for all users
events = []
event_id = 46  # Starting after existing 45 events

for user_id, profile in profiles.items():
    # Skip users that already have events (user_26 through user_30)
    if user_id in ['user_26', 'user_27', 'user_28', 'user_29', 'user_30']:
        continue
    
    currency = profile['home_currency']
    balance = int(profile['current_balance'])
    min_balance = int(profile['minimum_balance_to_keep'])
    
    # Determine income based on balance (roughly 3-6x monthly expenses)
    monthly_income = max(balance // 6, min_balance * 3)
    
    # Monthly expenses categories
    rent = int(monthly_income * 0.3)
    utilities = int(monthly_income * 0.1)
    food = int(monthly_income * 0.15)
    transport = int(monthly_income * 0.08)
    other = int(monthly_income * 0.1)
    
    # Start date - use a date before the earliest request for this user
    user_requests = []
    # We'll use a fixed start date for simplicity
    start_date = date(2024, 1, 1)
    
    # Generate 24 months of recurring events
    for month in range(24):
        current_date = date(start_date.year + (start_date.month + month - 1) // 12,
                           (start_date.month + month - 1) % 12 + 1, 1)
        
        # Salary (1st of month)
        events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.isoformat(),
            'event_type': 'income',
            'amount': monthly_income,
            'currency': currency,
            'status': 'settled' if current_date < date(2026, 9, 13) else 'scheduled',
            'recurring_frequency': 'monthly',
            'recurring_day_of_month': 1,
            'linked_event_id': '',
            'description': 'Salary'
        })
        event_id += 1
        
        # Rent (5th)
        events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.replace(day=5).isoformat(),
            'event_type': 'expense',
            'amount': rent,
            'currency': currency,
            'status': 'settled' if current_date < date(2026, 9, 13) else 'scheduled',
            'recurring_frequency': 'monthly',
            'recurring_day_of_month': 5,
            'linked_event_id': '',
            'description': 'Rent'
        })
        event_id += 1
        
        # Utilities (10th)
        events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.replace(day=10).isoformat(),
            'event_type': 'expense',
            'amount': utilities,
            'currency': currency,
            'status': 'settled' if current_date < date(2026, 9, 13) else 'scheduled',
            'recurring_frequency': 'monthly',
            'recurring_day_of_month': 10,
            'linked_event_id': '',
            'description': 'Utilities'
        })
        event_id += 1
        
        # Food (15th)
        events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.replace(day=15).isoformat(),
            'event_type': 'expense',
            'amount': food,
            'currency': currency,
            'status': 'settled' if current_date < date(2026, 9, 13) else 'scheduled',
            'recurring_frequency': 'monthly',
            'recurring_day_of_month': 15,
            'linked_event_id': '',
            'description': 'Food'
        })
        event_id += 1
        
        # Transport (20th)
        events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.replace(day=20).isoformat(),
            'event_type': 'expense',
            'amount': transport,
            'currency': currency,
            'status': 'settled' if current_date < date(2026, 9, 13) else 'scheduled',
            'recurring_frequency': 'monthly',
            'recurring_day_of_month': 20,
            'linked_event_id': '',
            'description': 'Transportation'
        })
        event_id += 1
        
        # Other (25th) - flexible
        events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.replace(day=25).isoformat(),
            'event_type': 'expense',
            'amount': other,
            'currency': currency,
            'status': 'settled' if current_date < date(2026, 9, 13) else 'scheduled',
            'recurring_frequency': 'monthly',
            'recurring_day_of_month': 25,
            'linked_event_id': '',
            'description': 'Entertainment'
        })
        event_id += 1

# Write to CSV
with open('D:/FILES/Projects/HackerRank/dataset/financial_events.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'event_id', 'user_id', 'event_date', 'event_type', 'amount',
        'currency', 'status', 'recurring_frequency', 'recurring_day_of_month',
        'linked_event_id', 'description'
    ])
    writer.writeheader()
    
    # First write existing events
    with open('D:/FILES/Projects/HackerRank/dataset/financial_events.csv', 'r') as rf:
        reader = csv.DictReader(rf)
        for row in reader:
            writer.writerow(row)
    
    # Then append new events
    for e in events:
        writer.writerow(e)

print(f'Generated {len(events)} new events for {len(profiles) - 5} users')
print(f'Total events: {45 + len(events)}')