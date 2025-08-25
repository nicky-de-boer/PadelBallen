import requests
from bs4 import BeautifulSoup
import json
from datetime import date

DECATHLON_URL = "https://www.decathlon.nl/search?Ntt=padelballen"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/114.0.0.0 Safari/537.36",
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.decathlon.nl/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
}

def scrape_decathlon():
    session = requests.Session()
    session.headers.update(HEADERS)

    response = session.get("https://www.decathlon.nl")
    # Dan pas de zoekpagina ophalen
    response = session.get(DECATHLON_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    producten = []

    for item in soup.select("a.css-1kb1x2t"):  # Product link selector
        try:
            title = item.select_one("span.css-7b41t7").get_text(strip=True)
            link = "https://www.decathlon.nl" + item["href"]

            # Prijs staat in een apart blok binnen de parent container
            prijs_tag = item.select_one("span[data-testid='price-value']")
            prijs = float(prijs_tag.get_text(strip=True).replace("€", "").replace(",", "."))

            # Merk als eerste woord
            merk = title.split()[0]
            model = " ".join(title.split()[1:])

            # Simpele inschatting van aantal ballen
            if "12" in title:
                aantal = 12
            elif "6" in title:
                aantal = 6
            elif "4" in title:
                aantal = 4
            elif "3" in title:
                aantal = 3
            else:
                aantal = 3  # fallback

            producten.append({
                "merk": merk,
                "model": model,
                "aantal_per_verpakking": aantal,
                "prijs": prijs,
                "winkel": "Decathlon",
                "link": link,
                "laatste_update": str(date.today())
            })

        except Exception as e:
            print("Fout bij product:", e)
            continue

    return producten

if __name__ == "__main__":
    padelballen = scrape_decathlon()

    with open("data/padelballen_decathlon.json", "w") as f:
        json.dump(padelballen, f, indent=2)

    print(f"{len(padelballen)} padelballen van Decathlon opgeslagen.")
