from flask import Flask, render_template, request
import json
from datetime import datetime
from urllib.parse import urlencode
from fetch_daisycon import fetch_daisycon_products

def update_query(args, **new_params):
    # Maak een dict van huidige args
    q = dict(args)
    # Update met nieuwe params
    for k, v in new_params.items():
        q[k] = v
    # Maak querystring
    return urlencode(q)


app = Flask(__name__)
app.jinja_env.globals.update(update_query=update_query)

@app.route("/")
def index():
    with open("data/padelballen.json") as f:
        padelballen = json.load(f)
    # Fetch Daisycon products
    FEED_URL = "https://daisycon.io/datafeed/?media_id=410302&standard_id=1&language_code=nl&locale_id=1&type=JSON&program_id=19068&html_transform=none&rawdata=false&encoding=utf8&general=false"
    daisycon_products = fetch_daisycon_products(FEED_URL)
    # Merge products
    all_products = padelballen + daisycon_products
    # Sort the data by 'prijs_per_stuk'
    sorted_products = sorted(all_products, key=lambda x: x.get('prijs_per_stuk', x.get('prijs', 99999)))
    # Alle unieke merken
    alle_merken = sorted({b["merk"] for b in sorted_products})
    # Filter
    geselecteerde_merken = request.args.getlist("merken")
    if geselecteerde_merken:
        sorted_products = [b for b in sorted_products if b["merk"] in geselecteerde_merken]
    return render_template("index.html",
                           padelballen=sorted_products,
                           merken=alle_merken,
                           geselecteerde_merk=geselecteerde_merken,
                           current_year=datetime.now().year
                           )

    # with open("data/padelballen.json") as f:
    #     padelballen = json.load(f)
    #
    # # Alle unieke merken ophalen (case-insensitive, maar originele hoofdletters bewaren)
    # merken_set = set()
    # for bal in padelballen:
    #     merken_set.add(bal["merk"])
    # merken = sorted(merken_set, key=lambda x: x.lower())
    #
    # # Filter op 1 merk (case-insensitive)
    # geselecteerd_merk = request.args.get("merk", "").strip()
    # if geselecteerd_merk:
    #     padelballen = [b for b in padelballen if b["merk"].lower() == geselecteerd_merk.lower()]
    #
    # # Sorteer op prijs_per_stuk
    # padelballen.sort(key=lambda x: x["prijs_per_stuk"])
    #
    # return render_template(
    #     "index.html",
    #     padelballen=padelballen,
    #     merken=merken,
    #     merk_filter=geselecteerd_merk,
    #     current_year=datetime.now().year
    # )

if __name__ == "__main__":
    app.run(debug=True)
