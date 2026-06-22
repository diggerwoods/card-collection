"""
Import your Ludex CSV export into your Supabase database.

BEFORE RUNNING:
1. Create your Supabase project at supabase.com
2. Run schema.sql in the SQL Editor (Supabase dashboard > SQL Editor > paste & run)
3. Fill in your SUPABASE_URL and SUPABASE_KEY below
4. Install the supabase client: pip install supabase

USAGE:
    python import_to_supabase.py

This will:
- Read your Ludex CSV
- Insert all cards into the 'cards' table
- Create an initial price_history entry for each card that has a price
- Populate sets_metadata with known set sizes
"""

import csv
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ludex-collection-2026-06-21.csv")

# ============================================================
# Known set sizes (same as in our HTML page)
# ============================================================
KNOWN_SET_SIZES = {
    ('1952 Topps','baseball'):407,('1962 Topps','baseball'):598,('1968 Topps','baseball'):598,
    ('1969 Topps','baseball'):664,('1973 Topps','baseball'):660,('1974 Topps','baseball'):660,
    ('1975 Topps','baseball'):660,('1976 Topps','baseball'):660,('1977 Topps','baseball'):660,
    ('1978 Topps','baseball'):726,('1979 Topps','baseball'):726,('1980 Topps','baseball'):726,
    ('1981 Topps','baseball'):726,('1981 Donruss','baseball'):600,('1981 Fleer','baseball'):660,
    ('1982 Topps','baseball'):792,('1982 Donruss','baseball'):660,('1982 Fleer','baseball'):660,
    ('1983 Topps','baseball'):792,('1983 Donruss','baseball'):660,('1983 Fleer','baseball'):660,
    ('1984 Topps','baseball'):792,('1984 Fleer','baseball'):660,('1985 Topps','baseball'):792,
    ('1985 Donruss','baseball'):660,('1986 Topps','baseball'):792,('1986 Donruss','baseball'):660,
    ('1986 Fleer','baseball'):660,('1987 Topps','baseball'):792,('1987 Donruss','baseball'):660,
    ('1987 Fleer','baseball'):660,('1988 Topps','baseball'):792,('1988 Donruss','baseball'):660,
    ('1988 Fleer','baseball'):660,('1988 Score','baseball'):660,('1989 Topps','baseball'):792,
    ('1989 Donruss','baseball'):660,('1989 Fleer','baseball'):660,('1989 Score','baseball'):660,
    ('1989 Upper Deck','baseball'):800,('1990 Topps','baseball'):792,('1990 Donruss','baseball'):716,
    ('1990 Fleer','baseball'):660,('1990 Score','baseball'):704,('1990 Upper Deck','baseball'):800,
    ('1991 Topps','baseball'):792,('1991 Donruss','baseball'):770,('1991 Fleer','baseball'):720,
    ('1991 Upper Deck','baseball'):800,('1991 Score','baseball'):900,('1992 Topps','baseball'):792,
    ('1992 Donruss','baseball'):784,('1992 Fleer','baseball'):720,('1992 Upper Deck','baseball'):800,
    ('1992 Score','baseball'):893,('1992 Stadium Club','baseball'):900,('1992 Ultra','baseball'):600,
    ('1993 Topps','baseball'):825,('1993 Fleer','baseball'):720,('1993 Upper Deck','baseball'):840,
    ('1990 SkyBox','basketball'):423,('2004 Fleer Tradition','baseball'):500,
    ('2004 Ultra','baseball'):250,('2005 Topps','baseball'):733,
    ('2005 Topps Turkey Red','baseball'):350,('2005 Topps Total','baseball'):990,
    ('2006 Topps','baseball'):659,('2006 Topps Turkey Red','baseball'):530,
    ('2006 Upper Deck','baseball'):1000,('2006 Ultra','baseball'):250,
    ('2008 Topps','baseball'):660,('2008 Topps Allen & Ginter','baseball'):350,
    ('2012 Topps','baseball'):661,('2023 Topps','baseball'):660,
    ('2025 Topps','baseball'):350,('2025 Topps Heritage','baseball'):500,
    ('2025 Topps Holiday','baseball'):200,('2025 Topps Stadium Club','baseball'):300,
    ('2026 Topps','baseball'):350,('2026 Topps Heritage','baseball'):500,
    ('1984 Topps','football'):396,('1985 Topps','football'):396,
}


def main():
    if "YOUR_SUPABASE" in SUPABASE_URL:
        print("ERROR: Please edit this file and fill in your SUPABASE_URL and SUPABASE_KEY.")
        print("Find them at: Supabase Dashboard > Settings > API")
        return

    print("Connecting to Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Read CSV
    print(f"Reading {CSV_PATH}...")
    cards = []
    with open(CSV_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cards.append(row)
    print(f"  Found {len(cards)} cards")

    # Insert cards in batches of 500 (Supabase limit)
    print("Inserting cards...")
    batch_size = 500
    inserted = 0
    for i in range(0, len(cards), batch_size):
        batch = cards[i:i+batch_size]
        rows = []
        for c in batch:
            price = None
            try:
                price = float(c['price']) if c['price'] else None
            except (ValueError, KeyError):
                pass

            purchase_price = None
            try:
                purchase_price = float(c['purchase_price']) if c.get('purchase_price') else None
            except (ValueError, KeyError):
                pass

            rows.append({
                'year': int(c['year']) if c['year'] else None,
                'classification': c['classification'] or 'unknown',
                'series': c['series'] or 'Unknown',
                'set_name': c['set'] or 'Base Set',
                'card_name': c['card_name'] or None,
                'player_name': c['player_name'] or 'Unknown',
                'team_name': c['team_name'] or None,
                'card_number': c['card_number'] or None,
                'parallel': c['parallel'] or None,
                'grader': c['grader'] or None,
                'grade_value': c['grade_value'] or None,
                'condition': c['condition'] or None,
                'notes': c['user_notes'] or None,
                'purchased_at': c['purchased_at'] if c.get('purchased_at') else None,
                'purchase_price': purchase_price,
            })

        result = supabase.table('cards').insert(rows).execute()
        inserted += len(batch)
        print(f"  Inserted {inserted}/{len(cards)} cards...")

    # Now create initial price history from Ludex prices
    print("Creating initial price history...")
    # Fetch all card IDs
    all_db_cards = []
    page = 0
    while True:
        result = supabase.table('cards').select('id,card_name,player_name,series,card_number').range(page*1000, (page+1)*1000-1).execute()
        if not result.data:
            break
        all_db_cards.extend(result.data)
        page += 1
    print(f"  Fetched {len(all_db_cards)} card IDs from database")

    # Match prices from CSV to database IDs (by index since order is preserved)
    price_rows = []
    for i, c in enumerate(cards):
        if i < len(all_db_cards):
            price = None
            try:
                price = float(c['price']) if c['price'] else None
            except (ValueError, KeyError):
                pass
            if price and price > 0:
                price_rows.append({
                    'card_id': all_db_cards[i]['id'],
                    'price': price,
                    'source': 'ludex',
                })

    # Insert price history in batches
    print(f"  Inserting {len(price_rows)} price records...")
    for i in range(0, len(price_rows), batch_size):
        batch = price_rows[i:i+batch_size]
        supabase.table('price_history').insert(batch).execute()

    # Insert known set sizes
    print("Inserting set metadata...")
    set_rows = [{'series': k[0], 'classification': k[1], 'total_cards': v, 'year': int(k[0][:4])}
                for k, v in KNOWN_SET_SIZES.items()]
    for i in range(0, len(set_rows), batch_size):
        batch = set_rows[i:i+batch_size]
        supabase.table('sets_metadata').insert(batch).execute()

    print(f"\nDone! {len(cards)} cards imported successfully.")
    print("You can now view them in your Supabase dashboard under Table Editor.")


if __name__ == '__main__':
    main()
