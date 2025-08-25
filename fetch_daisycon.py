import requests
import json
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_daisycon_feed(url):
    response = requests.get(url, verify=False)
    response.raise_for_status()
    try:
        data = response.json()
        print("Raw JSON response:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print("Error parsing JSON:", e)
        print("Raw text response:")
        print(response.text)
    return response

def fetch_daisycon_products(url):
    response = requests.get(url, verify=False)
    response.raise_for_status()
    data = response.json()
    # If data is a dict, try to find the product list
    if isinstance(data, dict):
        # Try common keys
        for key in ['products', 'items', 'data', 'result']:
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
        else:
            # If no known key, try to flatten dict values
            data = [v for v in data.values() if isinstance(v, dict) or isinstance(v, list)]
            # If still not a list, abort
            if not data or not isinstance(data[0], dict):
                return []
    # If data is not a list, abort
    if not isinstance(data, list):
        return []
    products = []
    products_list = data[0]['programs'][0]['products']
    # Only match padel balls, not rackets or other products
    padel_ball_patterns = [
        r'\bpadelbal\b', r'\bpadelballen\b', r'\bpadel ball\b', r'\bpadel ballen\b', r'\bpadel-bal\b', r'\bpadel-ballen\b', r'\bpadel balls\b', r'\bpadelballs\b'
    ]
    exclude_patterns = [
        r'\bracket\b', r'\brackets\b', r'\bpadelracket\b', r'\bpadelrackets\b', r'\bracket', r'\brackets', r'\btennisbal\b', r'\btennisballen\b', r'\bsquashbal\b', r'\bvoetbal\b', r'\bbasketbal\b', r'\brugbybal\b', r'\bhonkbal\b', r'\bgolfbal\b'
    ]
    # Search for specific product by title
    target_title = "drop shot training padelballen 3 st"
    found_products = []
    for item in products_list:
        if not isinstance(item, dict):
            continue
        info = item.get('product_info', {})
        # Only include products that are in stock and have a price
        if not info.get('in_stock') or not info.get('price'):
            continue
        text_fields = (info.get('category', ''), info.get('title', ''), info.get('description', ''))
        combined_text = ' '.join(text_fields).lower()
        # Only add if a padel ball pattern matches and no exclude pattern matches
        if not any(re.search(pattern, combined_text) for pattern in padel_ball_patterns):
            continue
        if any(re.search(pattern, combined_text) for pattern in exclude_patterns):
            continue
        # Check for the specific product title
        if info.get('title', '').strip().lower() == target_title:
            found_products.append(item)
        # Get image url
        img_url = None
        images = info.get('images', [])
        for img in images:
            if img.get('size') == 'large':
                img_url = img.get('location')
                break
        if not img_url and images:
            img_url = images[0].get('location')
        # Calculate prijs_per_stuk
        num_balls = extract_num_balls(' '.join(text_fields))
        prijs = info.get('price')
        if not num_balls:
            # If no pattern matched, fallback to 3 only if it's a padelballen product
            if any(re.search(pattern, ' '.join(text_fields).lower()) for pattern in padel_ball_patterns):
                num_balls = 3
        if num_balls and prijs:
            try:
                prijs_per_stuk = float(prijs) / num_balls
            except Exception:
                prijs_per_stuk = prijs
        else:
            prijs_per_stuk = prijs
        products.append({
            'img': img_url,
            'merk': info.get('brand', '').strip() or 'Onbekend',
            'model': info.get('title', '').strip(),
            'prijs': prijs,
            'prijs_per_stuk': prijs_per_stuk,
            'winkel': 'PadelDiscount',
            'link': info.get('link'),
            'description': info.get('description', ''),
            'category': info.get('category', ''),
        })
    # Print found products for debugging
    if found_products:
        print("Found product(s) with title 'Drop Shot Training Padelballen 3 St':")
        for prod in found_products:
            print(json.dumps(prod, indent=2))
    else:
        print("No product found with title 'Drop Shot Training Padelballen 3 St'.")
    return products

def extract_num_balls(text):
    """
    Extract the total number of balls from product text (title, description, category).
    Returns int or None if not found.
    Handles cases like '24 x 3 ballen', '24 kokers à 3 ballen', '(3)', '(3 st)', '(72 ballen totaal)', '24 kokers padelballen van 3 stuks per koker'.
    """
    text = text.lower()
    # 0. Patterns like '(72 ballen totaal)', '(72 stuks totaal)', '(72 totaal)'
    match = re.search(r'\((\d+)\s*(ballen|stuks|bal|stuk)?\s*totaal\)', text)
    if match:
        return int(match.group(1))
    # 1. Patterns like '24 x 3 ballen', '24 × 3 ballen', '24x3 ballen'
    match = re.search(r'(\d+)\s*[x×]\s*(\d+)\s*(ballen|bal|st|stuks|pack)', text)
    if match:
        return int(match.group(1)) * int(match.group(2))
    # 2. Patterns like '24 kokers à 3 ballen', '24 tubes met 3 ballen'
    match = re.search(r'(\d+)\s*(kokers|tubes|koker|tube)[^\d]*(\d+)\s*(ballen|bal)', text)
    if match:
        num_tubes = int(match.group(1))
        balls_per_tube = int(match.group(3))
        return num_tubes * balls_per_tube
    # 3. Patterns like '1 koker met 3 ballen'
    match = re.search(r'(\d+)\s*(koker|tube)[^\d]*(\d+)\s*(ballen|bal)', text)
    if match:
        num_tubes = int(match.group(1))
        balls_per_tube = int(match.group(3))
        return num_tubes * balls_per_tube
    # 4. Patterns like '24 kokers padelballen van 3 stuks per koker'
    match = re.search(r'(\d+)\s*(kokers|tubes|koker|tube)[^\d]*(\d+)\s*stuks?\s*per\s*(koker|tube)', text)
    if match:
        num_tubes = int(match.group(1))
        balls_per_tube = int(match.group(3))
        return num_tubes * balls_per_tube
    # 5. Patterns like 'van 3 stuks per koker' (if tube count is found earlier)
    match = re.search(r'van\s*(\d+)\s*stuks?\s*per\s*(koker|tube)', text)
    if match:
        balls_per_tube = int(match.group(1))
        # Try to find tube count earlier in the string
        tube_match = re.search(r'(\d+)\s*(kokers|tubes|koker|tube)', text)
        if tube_match:
            num_tubes = int(tube_match.group(1))
            return num_tubes * balls_per_tube
    # 6. Patterns like '(3)', '(3 st)', '(3-pack)'
    match = re.search(r'\((\d+)\s*(ballen|bal|st|stuks|pack)?\)', text)
    if match:
        return int(match.group(1))
    # 7. Direct number of balls: '6 ballen', '3 st', '3 stuks', '3-pack'
    match = re.search(r'(\d+)\s*(ballen|bal|st|stuks|pack)', text)
    if match:
        return int(match.group(1))
    return None

if __name__ == "__main__":
    FEED_URL = "https://daisycon.io/datafeed/?media_id=410302&standard_id=1&language_code=nl&locale_id=1&type=JSON&program_id=19068&html_transform=none&rawdata=false&encoding=utf8&general=false"
    fetch_daisycon_feed(FEED_URL)
    products = fetch_daisycon_products(FEED_URL)
    print(products[:3])
