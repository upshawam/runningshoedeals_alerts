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

    now_utc = datetime.utcnow()
    now_iso = now_utc.isoformat() + "Z"
    with open(HTML_FILE, "w") as f:
        f.write(f"""
        <html>
        <head>
            <title>Shoe Tracker Status</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <h1>Shoe Tracker Status</h1>
            <p>Last run: <span id="timestamp" data-utc="{now_iso}">Loading...</span></p>
            <p>Current price: ${price}</p>
            <p>URL: <a href="{URL}">{URL}</a></p>
            <script>
                function updateTime() {{
                    const span = document.getElementById('timestamp');
                    const utcTime = new Date(span.getAttribute('data-utc'));
                    
                    // Convert to CST using proper timezone conversion
                    const timeStr = utcTime.toLocaleString('en-US', {{
                        timeZone: 'America/Chicago',
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: true
                    }}) + ' CST';
                    
                    // Calculate minutes ago
                    const now = new Date();
                    const diffMs = now - utcTime;
                    const diffMins = Math.floor(diffMs / (1000 * 60));
                    
                    let timeAgo;
                    if (diffMins < 1) {{
                        timeAgo = 'just now';
                    }} else if (diffMins === 1) {{
                        timeAgo = '1 minute ago';
                    }} else if (diffMins < 60) {{
                        timeAgo = diffMins + ' minutes ago';
                    }} else if (diffMins < 1440) {{
                        const diffHours = Math.floor(diffMins / 60);
                        const remainMins = diffMins % 60;
                        if (diffHours === 1) {{
                            timeAgo = remainMins > 0 ? '1 hour ' + remainMins + ' minutes ago' : '1 hour ago';
                        }} else {{
                            timeAgo = remainMins > 0 ? diffHours + ' hours ' + remainMins + ' minutes ago' : diffHours + ' hours ago';
                        }}
                    }} else {{
                        const diffDays = Math.floor(diffMins / 1440);
                        timeAgo = diffDays === 1 ? '1 day ago' : diffDays + ' days ago';
                    }}
                    
                    span.textContent = timeStr + ' (' + timeAgo + ')';
                }}
                
                updateTime();
                setInterval(updateTime, 60000); // Update every minute
            </script>
        </body>
        </html>
        """)

if __name__ == "__main__":
    check_price()
