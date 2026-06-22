# -*- coding: utf-8 -*-
"""
Sync your database with a new Ludex CSV export.

This is your primary workflow for keeping the database updated:
1. Scan new cards in Ludex
2. Export your full collection as CSV
3. Run this script

WHAT IT DOES:
- Compares the CSV to what's already in the database
- Adds any NEW cards (cards in the CSV that aren't in the DB yet)
- Preserves duplicates correctly (if you own 3 copies of a card, all 3 stay)
- Updates prices for existing cards
- Never deletes anything
- Never overwrites your images, notes, or custom data

WHAT IT DOES NOT DO:
- Remove cards from the database (even if you sold/traded them)
- Merge duplicates together
- Overwrite any images or notes you've added

USAGE:
    python sync_from_ludex.py <path-to-new-ludex-export.csv>

EXAMPLE:
    python sync_from_ludex.py "C:/Users/digge/Downloads/ludex-collection-2026-07-01.csv"
"""

import csv
import sys
import os
from collections import Counter
from supabase import create_client

SUPABASE_URL = "https://fokpdeenvnulmbthyjph.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZva3BkZWVudm51bG1idGh5anBoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MjExMTY4NSwiZXhwIjoyMDk3Njg3Njg1fQ.B7ZEHhIqXUOvXgObenbskj_Ob-YpfMYsxmYdRLwND3Y"


def card_fingerprint(row):
    """
    Create a fingerprint for matching cards.
    Two rows with the same fingerprint represent the same physical card type.
    Duplicates = multiple rows with the same fingerprint.
    """
    return (
        row.get('series', ''),
        row.get('card_number', ''),
        row.get('player_name', ''),
        row.get('parallel', '') or '',
        row.get('grader', '') or '',
        row.get('grade_value', '') or ''
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python sync_from_ludex.py <ludex-export.csv>")
        print("\nThis compares your Ludex export to the database and adds only new cards.")
        return

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"ERROR: File not found: {csv_path}")
        return

    print("Connecting to Supabase...")
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Step 1: Read the new CSV
    print(f"Reading {csv_path}...")
    csv_rows = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_rows.append(row)
    print(f"  CSV contains {len(csv_rows)} cards")

    # Step 2: Count fingerprints in CSV
    csv_counts = Counter()
    for row in csv_rows:
        csv_counts[card_fingerprint(row)] += 1

    # Step 3: Fetch all cards from database and count fingerprints
    print("Fetching current database...")
    db_cards = []
    page = 0
    while True:
        result = sb.table('cards').select('id, series, card_number, player_name, parallel, grader, grade_value').range(page*1000, (page+1)*1000-1).execute()
        if not result.data:
            break
        db_cards.extend(result.data)
        page += 1
    print(f"  Database contains {len(db_cards)} cards")

    db_counts = Counter()
    for card in db_cards:
        fp = (
            card.get('series', ''),
            card.get('card_number', ''),
            card.get('player_name', ''),
            card.get('parallel', '') or '',
            card.get('grader', '') or '',
            card.get('grade_value', '') or ''
        )
        db_counts[fp] += 1

    # Step 4: Find cards that need to be added
    # For each fingerprint: if CSV has more copies than DB, add the difference
    to_add = []
    for row in csv_rows:
        fp = card_fingerprint(row)
        if csv_counts[fp] > db_counts[fp]:
            # This fingerprint has more copies in CSV than DB - add one
            db_counts[fp] += 1  # Increment so we don't add too many
            to_add.append(row)

    print(f"\n  New cards to add: {len(to_add)}")
    if not to_add:
        print("  Database is already up to date!")
        # Still update prices
        print("\nUpdating prices...")
        update_prices(sb, csv_rows, db_cards)
        return

    # Step 5: Insert new cards
    print(f"Inserting {len(to_add)} new cards...")
    batch_size = 500
    new_ids = []
    for i in range(0, len(to_add), batch_size):
        batch = to_add[i:i+batch_size]
        rows = []
        for c in batch:
            price = None
            try:
                price = float(c['price']) if c.get('price') else None
            except ValueError:
                pass
            purchase_price = None
            try:
                purchase_price = float(c['purchase_price']) if c.get('purchase_price') else None
            except ValueError:
                pass

            rows.append({
                'year': int(c['year']) if c.get('year') else None,
                'classification': c.get('classification', 'unknown'),
                'series': c.get('series', 'Unknown'),
                'set_name': c.get('set', 'Base Set'),
                'card_name': c.get('card_name'),
                'player_name': c.get('player_name', 'Unknown'),
                'team_name': c.get('team_name'),
                'card_number': c.get('card_number'),
                'parallel': c.get('parallel') or None,
                'grader': c.get('grader') or None,
                'grade_value': c.get('grade_value') or None,
                'condition': c.get('condition') or None,
                'notes': c.get('user_notes') or None,
                'purchased_at': c.get('purchased_at') if c.get('purchased_at') else None,
                'purchase_price': purchase_price,
                'current_price': price,
            })

        result = sb.table('cards').insert(rows).execute()
        new_ids.extend([r['id'] for r in result.data])
        print(f"  {min(i+batch_size, len(to_add))}/{len(to_add)}...")

    # Step 6: Add price history for new cards
    print("Adding price history for new cards...")
    price_rows = []
    for i, row in enumerate(to_add):
        if i < len(new_ids):
            price = None
            try:
                price = float(row['price']) if row.get('price') else None
            except ValueError:
                pass
            if price and price > 0:
                price_rows.append({
                    'card_id': new_ids[i],
                    'price': price,
                    'source': 'ludex'
                })

    for i in range(0, len(price_rows), batch_size):
        sb.table('price_history').insert(price_rows[i:i+batch_size]).execute()

    # Step 7: Update prices for existing cards
    print("\nUpdating prices for existing cards...")
    update_prices(sb, csv_rows, db_cards)

    print(f"\nDone!")
    print(f"  Added: {len(to_add)} new cards")
    print(f"  Total in database: {len(db_cards) + len(to_add)}")


def update_prices(sb, csv_rows, db_cards):
    """Update current_price on existing cards using bulk SQL function."""
    # Build lookup from DB: fingerprint -> list of IDs
    db_by_fp = {}
    for card in db_cards:
        fp = (
            card.get('series', ''),
            card.get('card_number', ''),
            card.get('player_name', ''),
            card.get('parallel', '') or '',
            card.get('grader', '') or '',
            card.get('grade_value', '') or ''
        )
        if fp not in db_by_fp:
            db_by_fp[fp] = []
        db_by_fp[fp].append(card['id'])

    # Match CSV prices to DB cards
    updates = []
    seen_fps = Counter()
    for row in csv_rows:
        fp = card_fingerprint(row)
        price = None
        try:
            price = float(row['price']) if row.get('price') else None
        except ValueError:
            pass
        if price and fp in db_by_fp:
            idx = seen_fps[fp]
            seen_fps[fp] += 1
            if idx < len(db_by_fp[fp]):
                updates.append({'id': db_by_fp[fp][idx], 'price': price})

    print(f"  {len(updates)} cards to update prices...")
    # Use bulk_update_prices SQL function - sends 500 at a time in one call
    batch_size = 500
    updated = 0
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        ids = [u['id'] for u in batch]
        prices = [float(u['price']) for u in batch]
        sb.rpc('bulk_update_prices', {'ids': ids, 'prices': prices}).execute()
        updated += len(batch)
        print(f"  Updated {updated}/{len(updates)} prices...")

    print(f"  Prices updated: {updated}")


if __name__ == '__main__':
    main()
