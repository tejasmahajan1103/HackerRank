"""
Generate comprehensive financial events for all users - FIXED VERSION.
Only the first occurrence of each recurring series is marked as recurring.
"""
import csv
from datetime import date, timedelta
from decimal import Decimal
import random

# Load existing profiles
profiles = {}
with open('D:/FILES/Projects/HackerRank/dataset/financial_profiles.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        profiles[row['user_id']] = row

# Read existing events to preserve them
existing_events = []
with open('D:/FILES/Projects/HackerRank/dataset/financial_events.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        existing_events.append(row)

# Find max event_id
max_id = 0
for e in existing_events:
    if e['event_id'].startswith('event_'):
        num = int(e['event_id'].split('_')[1])
        max_id = max(max_id, num)

event_id = max_id + 1

new_events = []

for user_id, profile in profiles.items():
    # Skip users that already have events
    if user_id in ['user_26', 'user_27', 'user_28', 'user_29', 'user_30']:
        continue
    
    currency = profile['home_currency']
    balance = int(profile['current_balance'])
    min_balance = int(profile['minimum_balance_to_keep'])
    
    # Monthly income - make it realistic
    monthly_income = max(balance // 6, min_balance * 3)
    
    # Monthly expenses
    rent = int(monthly_income * 0.3)
    utilities = int(monthly_income * 0.1)
    food = int(monthly_income * 0.15)
    transport = int(monthly_income * 0.08)
    other = int(monthly_income * 0.1)
    
    # Generate 24 months of INDIVIDUAL events (not recurring)
    # Only the FIRST month events are marked as recurring
    start_date = date(2024, 1, 1)
    
    for month in range(24):
        current_date = date(start_date.year + (start_date.month + month - 1) // 12,
                           (start_date.month + month - 1) % 12 + 1, 1)
        
        is_first_month = (month == 0)
        status = 'settled' if current_date < date(2026, 9, 13) else 'scheduled'
        
        # Salary (1st of month)
        new_events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.isoformat(),
            'event_type': 'income',
            'amount': monthly_income,
            'currency': currency,
            'status': status,
            'recurring_frequency': 'monthly' if is_first_month else '',
            'recurring_day_of_month': 1 if is_first_month else '',
            'linked_event_id': '',
            'description': 'Salary'
        })
        event_id += 1
        
        # Rent (5th)
        new_events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.replace(day=5).isoformat(),
            'event_type': 'expense',
            'amount': rent,
            'currency': currency,
            'status': status,
            'recurring_frequency': 'monthly' if is_first_month else '',
            'recurring_day_of_month': 5 if is_first_month else '',
            'linked_event_id': '',
            'description': 'Rent'
        })
        event_id += 1
        
        # Utilities (10th)
        new_events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.replace(day=10).isoformat(),
            'event_type': 'expense',
            'amount': utilities,
            'currency': currency,
            'status': status,
            'recurring_frequency': 'monthly' if is_first_month else '',
            'recurring_day_of_month': 10 if is_first_month else '',
            'linked_event_id': '',
            'description': 'Utilities'
        })
        event_id += 1
        
        # Food (15th)
        new_events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.replace(day=15).isoformat(),
            'event_type': 'expense',
            'amount': food,
            'currency': currency,
            'status': status,
            'recurring_frequency': 'monthly' if is_first_month else '',
            'recurring_day_of_month': 15 if is_first_month else '',
            'linked_event_id': '',
            'description': 'Food'
        })
        event_id += 1
        
        # Transport (20th)
        new_events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.replace(day=20).isoformat(),
            'event_type': 'expense',
            'amount': transport,
            'currency': currency,
            'status': status,
            'recurring_frequency': 'monthly' if is_first_month else '',
            'recurring_day_of_month': 20 if is_first_month else '',
            'linked_event_id': '',
            'description': 'Transportation'
        })
        event_id += 1
        
        # Other (25th) - flexible
        new_events.append({
            'event_id': f'event_{event_id}',
            'user_id': user_id,
            'event_date': current_date.replace(day=25).isoformat(),
            'event_type': 'expense',
            'amount': other,
            'currency': currency,
            'status': status,
            'recurring_frequency': 'monthly' if is_first_month else '',
            'recurring_day_of_month': 25 if is_first_month else '',
            'linked_event_id': '',
            'description': 'Entertainment'
        })
        event_id += 1

# Write to CSV - overwrite with existing + new
with open('D:/FILES/Projects/HackerRank/dataset/financial_events.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'event_id', 'user_id', 'event_date', 'event_type', 'amount',
        'currency', 'status', 'recurring_frequency', 'recurring_day_of_month',
        'linked_event_id', 'description'
    ])
    writer.writeheader()
    for e in existing_events:
        writer.writerow(e)
    for e in new_events:
        writer.writerow(e)

print(f'Generated {len(new_events)} new events for {len(profiles) - 5} users')
print(f'Total events: {len(existing_events) + len(new_events)}')