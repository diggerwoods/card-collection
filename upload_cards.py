"""Upload front and back images for specific cards."""
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']
BUCKET = "card-images"

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image(card_id, image_path, side):
    """Upload an image and return the public URL."""
    ext = os.path.splitext(image_path)[1].lower()
    filename = f"card-{card_id}-{side}{ext}"
    content_type = 'image/jpeg' if ext in ['.jpg','.jpeg'] else 'image/png'
    
    with open(image_path, 'rb') as f:
        file_data = f.read()
    
    # Upload (upsert in case it already exists)
    sb.storage.from_(BUCKET).upload(filename, file_data, file_options={"content-type": content_type, "upsert": "true"})
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}"
    return public_url

def find_and_upload(player, year, series, front_path, back_path):
    """Find card by player/year/series, upload images, update record."""
    print(f"\nSearching for: {player} - {year} {series}...")
    result = sb.table('cards').select('id, player_name, year, series, card_number').eq('player_name', player).eq('year', year).eq('series', series).execute()
    
    if not result.data:
        print(f"  ERROR: Card not found!")
        return
    
    card = result.data[0]
    card_id = card['id']
    print(f"  Found card ID: {card_id} (#{card['card_number']})")
    
    # Upload front
    print(f"  Uploading front image...")
    front_url = upload_image(card_id, front_path, 'front')
    print(f"    URL: {front_url}")
    
    # Upload back
    print(f"  Uploading back image...")
    back_url = upload_image(card_id, back_path, 'back')
    print(f"    URL: {back_url}")
    
    # Update database
    sb.table('cards').update({'image_url': front_url, 'image_back_url': back_url}).eq('id', card_id).execute()
    print(f"  Done! Card {card_id} updated with both images.")

# ============================================================
# UPLOAD YOUR CARDS
# ============================================================

find_and_upload(
    player="Michael Jordan",
    year=1988,
    series="1988 Fleer",
    front_path=r"C:\Users\digge\OneDrive\Desktop\Card images\1988Michael JordanChicago Bulls1988 FleerBase Set_Front.jpeg",
    back_path=r"C:\Users\digge\OneDrive\Desktop\Card images\1988Michael JordanChicago Bulls1988 FleerBase Set_Back.jpeg"
)
