from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from datetime import date

def scrape_decathlon_selenium():
    options = Options()
    options.headless = False  # Browser opent niet zichtbaar
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)

    driver.get("https://www.decathlon.nl/sporten/padel/padelballen")

    time.sleep(3)  # Wacht tot de pagina volledig geladen is
    try:
        consent_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.didomi-continue-without-agreeing"))
        )
        consent_button.click()
        print("Popup weggeklikt")
    except:
        print("Geen popup gevonden of al weggeklikt")

    time.sleep(3)

    producten = []

    # Alle li elementen met producten
    product_elements = driver.find_elements(By.CSS_SELECTOR, "li.grid__item-span-2")

    print(f"Aantal producten gevonden: {len(product_elements)}")

    for prod in product_elements:
        try:
            # Titel en link
            a_tag = prod.find_element(By.CSS_SELECTOR, "h2 a")
            titel = a_tag.get_attribute("aria-label")
            link = a_tag.get_attribute("href")
            if link.startswith("/"):
                link = urljoin(base_url, link)

            # Prijs totaal
            prijs_totaal_elem = prod.find_element(By.CSS_SELECTOR, "span.price-base__current-price")
            prijs_totaal_str = prijs_totaal_elem.text.replace("€", "").replace(",", ".").strip()
            prijs_totaal = float(prijs_totaal_str)

            # Prijs per stuk
            prijs_per_stuk_elem = prod.find_element(By.CSS_SELECTOR, "span.price-base__secondary-price")
            prijs_per_stuk_str = prijs_per_stuk_elem.text.replace("€", "").replace("/stuk", "").replace(",",
                                                                                                        ".").strip()
            prijs_per_stuk = float(prijs_per_stuk_str)



            # Merk en model uit titel (merk = eerste woord, model = rest)
            woorden = titel.split()
            merk = woorden[0]
            model = " ".join(woorden[1:])

            # Aantal ballen: proberen te vinden in titel (e.g. "koker van 3 ballen")
            aantal = 3  # default
            import re
            match = re.search(r"(\d+)\s*ballen", titel.lower())
            if match:
                aantal = int(match.group(1))

            # Haal de afbeelding op
            img_elem = prod.find_element(By.CSS_SELECTOR, "img")
            img_url = img_elem.get_attribute("src")

            product = {
                "merk": merk,
                "model": model,
                "aantal_per_verpakking": aantal,
                "prijs": prijs_totaal,
                "prijs_per_stuk": prijs_per_stuk,
                "winkel": "Decathlon",
                "link": link,
                "img": img_url,
                "laatste_update": str(date.today())
            }
            producten.append(product)
        except Exception as e:
            print(f"Fout bij product: {e}")
            continue

    driver.quit()
    return producten


if __name__ == "__main__":
    padelballen = scrape_decathlon_selenium()

    print(f"Gevonden producten: {len(padelballen)}")
    for p in padelballen:
        print(p)

    with open("data/padelballen.json", "w") as f:
        json.dump(padelballen, f, indent=2)
