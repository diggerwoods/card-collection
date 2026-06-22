"""
Upload a card image to Supabase Storage and link it to a card.

USAGE:
    python upload_image.py <card_id> <image_path>

EXAMPLE:
    python upload_image.py 12345 "C:/Users/digge/Pictures/nolan-ryan-1973.jpg"

This will:
1. Upload the image to your 'card-images' storage bucket
2. Update the card's image_url field in the database
3. The image will be publicly accessible and show in the HTML page

FINDING CARD IDs:
Run this in Supabase SQL Editor to find a card's ID:
    SELECT id, player_name, year, series, card_number
    FROM cards WHERE player_name ILIKE '%nolan ryan%';

SUPPORTED FORMATS: jpg, jpeg, png, webp
"""

import sys
import os
from supabase import create_client

SUPABASE_URL = "https://fokpdeenvnulmbthyjph.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZva3BkZWVudm51bG1idGh5anBoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIxMTE2ODUsImV4cCI6MjA5NzY4NzY4NX0.G1YYPlAy3s4dKcgKvdplrsukZOqXiJZgS_ePI8NeBfg"
BUCKET = "card-images"


def main():
    if len(sys.argv) < 3:
        print("Usage: python upload_image.py <card_id> <image_path>")
        print("Example: python upload_image.py 12345 my-card-photo.jpg")
        return

    card_id = int(sys.argv[1])
    image_path = sys.argv[2]

    if not os.path.exists(image_path):
        print(f"ERROR: File not found: {image_path}")
        return

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        print(f"ERROR: Unsupported format {ext}. Use jpg, png, or webp.")
        return

    content_type = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}[ext]

    print("Connecting to Supabase...")
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Generate storage path
    filename = f"card-{card_id}{ext}"

    # Upload to storage
    print(f"Uploading {image_path} as {filename}...")
    with open(image_path, 'rb') as f:
        file_data = f.read()

    result = sb.storage.from_(BUCKET).upload(
        filename,
        file_data,
        file_options={"content-type": content_type, "upsert": "true"}
    )

    # Get public URL
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}"

    # Update card record
    print(f"Linking image to card {card_id}...")
    sb.table('cards').update({'image_url': public_url}).eq('id', card_id).execute()

    print(f"\nDone!")
    print(f"Image URL: {public_url}")
    print(f"Card {card_id} now has this image linked.")


if __name__ == '__main__':
    main()
