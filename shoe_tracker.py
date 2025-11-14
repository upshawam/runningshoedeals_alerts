import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://www.runningshoedeals.com/shoes/adidas-adizero-adios-pro-4?category=Women&size=6.5"
PRICE_FILE = "last_price.txt"
HISTORY_FILE = "price_history.json"
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

    # Load price history
    try:
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    except:
        history = []

    now_utc = datetime.utcnow()
    now_iso = now_utc.isoformat() + "Z"

    # Check if price changed
    if last_price is None:
        send_alert(f"📢 Tracker initialized. Baseline price: ${price}\n{URL}")
        history.append({"timestamp": now_iso, "price": price, "change": "initialized"})
    elif price < last_price:
        send_alert(f"🔥 Price drop detected: ${last_price} → ${price}\n{URL}")
        history.append({"timestamp": now_iso, "price": price, "change": "down"})
    elif price > last_price:
        print(f"📈 Price increased: ${last_price} → ${price}")
        history.append({"timestamp": now_iso, "price": price, "change": "up"})
    else:
        print("ℹ️ No price change.")

    # Always update the current price
    with open(PRICE_FILE, "w") as f:
        f.write(str(price))

    # Save history (keep last 50 entries)
    history = history[-50:]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    # Build price history HTML
    history_html = ""
    if history:
        history_html = "<h2>Price History</h2><table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>"
        history_html += "<tr><th>Date/Time (CST)</th><th>Price</th><th>Change</th></tr>"
        for entry in reversed(history[-10:]):  # Show last 10 entries, newest first
            timestamp = entry['timestamp']
            entry_price = entry['price']
            change = entry['change']
            change_icon = "🔥" if change == "down" else ("📈" if change == "up" else "ℹ️")
            history_html += f"<tr><td><span class='history-time' data-utc='{timestamp}'></span></td><td>${entry_price}</td><td>{change_icon} {change}</td></tr>"
        history_html += "</table>"

    with open(HTML_FILE, "w") as f:
        f.write(f"""
        <html>
        <head>
            <title>Shoe Tracker Status</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ margin-top: 10px; }}
                th {{ background-color: #f0f0f0; }}
            </style>
        </head>
        <body>
            <h1>Shoe Tracker Status</h1>
            <p>Last run: <span id="timestamp" data-utc="{now_iso}">Loading...</span></p>
            <p><strong>Current price: ${price}</strong></p>
            <p>URL: <a href="{URL}">{URL}</a></p>
            {history_html}
            <script>
                function formatTime(utcTime) {{
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
                    
                    return timeStr + ' (' + timeAgo + ')';
                }}
                
                function updateAllTimes() {{
                    // Update main timestamp
                    const span = document.getElementById('timestamp');
                    if (span) {{
                        const utcTime = new Date(span.getAttribute('data-utc'));
                        span.textContent = formatTime(utcTime);
                    }}
                    
                    // Update history timestamps
                    const historySpans = document.querySelectorAll('.history-time');
                    historySpans.forEach(span => {{
                        const utcTime = new Date(span.getAttribute('data-utc'));
                        span.textContent = utcTime.toLocaleString('en-US', {{
                            timeZone: 'America/Chicago',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit',
                            hour12: true
                        }});
                    }});
                }}
                
                updateAllTimes();
                setInterval(updateAllTimes, 60000); // Update every minute
            </script>
        </body>
        </html>
        """)

if __name__ == "__main__":
    check_price()
