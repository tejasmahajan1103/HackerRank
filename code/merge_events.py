"""
Merge original events with generated events.
"""
import csv

# Read original events
original_events = []
with open('D:/FILES/Projects/HackerRank/dataset/financial_events_original.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        original_events.append(row)

# Read generated events (skip header)
generated_events = []
with open('D:/FILES/Projects/HackerRank/dataset/financial_events.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Skip users 26-30 (they're in original)
        if row['user_id'] not in ['user_26', 'user_27', 'user_28', 'user_29', 'user_30']:
            generated_events.append(row)

# Write merged
with open('D:/FILES/Projects/HackerRank/dataset/financial_events.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'event_id', 'user_id', 'event_date', 'event_type', 'amount',
        'currency', 'status', 'recurring_frequency', 'recurring_day_of_month',
        'linked_event_id', 'description'
    ])
    writer.writeheader()
    for e in original_events:
        writer.writerow(e)
    for e in generated_events:
        writer.writerow(e)

print(f'Merged: {len(original_events)} original + {len(generated_events)} generated = {len(original_events) + len(generated_events)} total')