import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://www.runningshoedeals.com/shoes/adidas-adizero-adios-pro-4?category=Women&size=6.5"
PRICE_FILE = "last_price.txt"
HTML_FILE = "index.html"

def send_alert(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message}
    )

def check_price():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    element = soup.find("p", {"class": "chakra-text css-itvw0n"})
    if not element:
        return None

    text = element.get_text()
    match = re.search(r"\$(\d+\.\d+)", text)
    if not match:
        return None

    price = float(match.group(1))

    # Load last price
    try:
        with open(PRICE_FILE) as f:
            last_price = float(f.read().strip())
    except:
        last_price = None

    # Compare
    if last_price is None or price < last_price:
        send_alert(f"🔥 Price drop detected: ${price}\n{URL}")

    # Save current price
    with open(PRICE_FILE, "w") as f:
        f.write(str(price))

    # Write HTML status page
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(HTML_FILE, "w") as f:
        f.write(f"""
        <html>
        <head><title>Shoe Tracker Status</title></head>
        <body>
            <h1>Shoe Tracker Status</h1>
            <p>Last run: {now}</p>
            <p>Current price: ${price}</p>
            <p>URL: <a href="{URL}">{URL}</a></p>
        </body>
        </html>
        """)

if __name__ == "__main__":
    check_price()
