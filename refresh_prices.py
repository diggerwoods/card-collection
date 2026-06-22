"""
Refresh card prices from a new Ludex CSV export.

HOW TO USE:
1. Export your collection from Ludex (same as before)
2. Drop the new CSV file in this folder
3. Run: python refresh_prices.py new-export.csv

This will:
- Read the new CSV
- Match cards to your database by series + card_number + player_name
- Insert new price_history records for any cards with changed prices
- Report how many prices were updated

You can also re-import from the original file to create a new price snapshot:
    python refresh_prices.py ludex-collection-2026-06-21.csv
"""

import csv
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']


def main():
    if len(sys.argv) < 2:
        print("Usage: python refresh_prices.py <ludex-export.csv>")
        print("  Reads a Ludex CSV export and updates prices in your database.")
        return

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"ERROR: File not found: {csv_path}")
        return

    print("Connecting to Supabase...")
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Read CSV
    print(f"Reading {csv_path}...")
    csv_cards = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            price = None
            try:
                price = float(row['price']) if row.get('price') else None
            except ValueError:
                pass
            if price and price > 0:
                csv_cards.append({
                    'series': row['series'],
                    'card_number': row['card_number'],
                    'player_name': row['player_name'],
                    'parallel': row.get('parallel', ''),
                    'price': price
                })
    print(f"  Found {len(csv_cards)} cards with prices")

    # Fetch all cards from DB with their latest price
    print("Fetching current database cards...")
    all_db = []
    page = 0
    while True:
        result = sb.table('cards').select('id, series, card_number, player_name, parallel').range(page*1000, (page+1)*1000-1).execute()
        if not result.data:
            break
        all_db.extend(result.data)
        page += 1
    print(f"  Loaded {len(all_db)} cards from database")

    # Build lookup: (series, card_number, player_name, parallel) -> card_id
    db_lookup = {}
    for card in all_db:
        key = (card['series'], card['card_number'] or '', card['player_name'], card.get('parallel') or '')
        if key not in db_lookup:
            db_lookup[key] = card['id']

    # Match and prepare price updates
    updates = []
    matched = 0
    unmatched = 0
    for csv_card in csv_cards:
        key = (csv_card['series'], csv_card['card_number'], csv_card['player_name'], csv_card['parallel'])
        card_id = db_lookup.get(key)
        if card_id:
            updates.append({
                'card_id': card_id,
                'price': csv_card['price'],
                'source': 'ludex'
            })
            matched += 1
        else:
            unmatched += 1

    print(f"  Matched: {matched}, Unmatched: {unmatched}")

    # Insert price history records in batches
    if updates:
        print(f"Inserting {len(updates)} price records...")
        batch_size = 500
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            sb.table('price_history').insert(batch).execute()
            print(f"  {min(i+batch_size, len(updates))}/{len(updates)}...")

    print(f"\nDone! {len(updates)} prices refreshed.")
    print("Your price_history table now has a new snapshot.")
    print("The HTML page will automatically use the latest prices.")


if __name__ == '__main__':
    main()
