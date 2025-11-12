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
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ BOT_TOKEN or CHAT_ID not set in environment")
        return

    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message}
    )
    print("➡️ Telegram request:", r.request.url)
    print("➡️ Telegram payload:", r.request.body)
    print("➡️ Telegram response:", r.status_code, r.text)

def check_price():
    try:
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except Exception as e:
        print("❌ Error fetching page:", e)
        return

    soup = BeautifulSoup(r.text, "html.parser")
    element = soup.find("p", {"class": "chakra-text css-itvw0n"})
    if not element:
        print("❌ Could not find price element")
        return

    text = element.get_text()
    match = re.search(r"\$(\d+\.\d+)", text)
    if not match:
        print("❌ Could not parse price from:", text)
        return

    price = float(match.group(1))
    print("✅ Current price:", price)

    try:
        with open(PRICE_FILE) as f:
            last_price = float(f.read().strip())
    except:
        last_price = None

    print("📂 Last recorded price:", last_price)

    if last_price is None:
        send_alert(f"📢 Tracker initialized. Baseline price: ${price}\n{URL}")
    elif price < last_price:
        send_alert(f"🔥 Price drop detected: {last_price} → {price}\n{URL}")
    else:
        print("ℹ️ No price drop detected.")

    with open(PRICE_FILE, "w") as f:
        f.write(str(price))

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
