import os
import requests
import asyncio
import urllib.parse
from google import genai
from playwright.async_api import async_playwright

# --- Configuration ---
TELEGRAM_URL = os.getenv("NOTIFY_WEBHOOK_URL")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Expanded venue list for the I-5 Corridor
VENUES = {
    "Official Site": "https://www.bucketheadtour.us/",
    "Roseland Theater": "https://roselandpdx.com/",
    "Crystal Ballroom": "https://www.mcmenamins.com/events",
    "McDonald Theatre": "https://mcdonaldtheatre.com/events",
    "Showbox Seattle": "https://www.showboxpresents.com/events",
    "Cascades Ridgefield": "https://www.cascadesamphitheater.com/shows",
    "Elsinore Salem": "https://elsinoretheatre.com/events/",
    "Neptune Seattle": "https://www.stgpresents.org/neptune/events"
}

STATE_FILE = "last_seen_dates.txt"
client = genai.Client(api_key=GEMINI_KEY)

async def get_page_content(browser, url):
    page = await browser.new_page()
    try:
        # networkidle is used for JS-heavy venue calendars
        await page.goto(url, wait_until="networkidle", timeout=60000)
        return await page.inner_text("body")
    except Exception as e:
        print(f"Scrape Error {url}: {e}")
        return ""
    finally:
        await page.close()

async def analyze_with_gemini(all_data):
    prompt = f"""
    Analyze the following concert data for Buckethead (Brian Carroll).
    
    Data: {all_data}
    
    Context:
    - User location: Salem, Oregon.
    - If there are no shows scheduled near the User location, do not send anything.
    
    Task:
    1. Identify any shows in Oregon (Portland, Salem, Eugene) or Washington (Seattle, Ridgefield).
    2. Analyze the 30-day gap. List any open dates for the PNW venues.
    3. Calculate the probability of a PNW addition based on travel distance from the Mar 14 CA date.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt
    )
    return response.text

def send_telegram_notification(message):
    if not TELEGRAM_URL:
        print("ERROR: NOTIFY_WEBHOOK_URL not found.")
        return
        
    encoded_msg = urllib.parse.quote(message)
    url = f"{TELEGRAM_URL}&text={encoded_msg}"
    
    try:
        response = requests.get(url, timeout=20)
        print(f"Telegram Response: {response.status_code}")
    except Exception as e:
        print(f"Telegram Connection Failed: {e}")

async def run_agent():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        aggregated_data = ""
        
        for name, url in VENUES.items():
            print(f"Scanning {name}...")
            content = await get_page_content(browser, url)
            aggregated_data += f"\n--- {name} ---\n{content}\n"
        
        last_state = ""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                last_state = f.read()

        # Logic: Only process if the website content actually changed
        if aggregated_data.strip() != last_state.strip():
            print("Changes detected. Analyzing...")
            analysis = await analyze_with_gemini(aggregated_data)
            
            # Local keyword filter to suppress non-PNW alerts
            pnw_keywords = [
                "oregon", "portland", "salem", "eugene", "washington", 
                "seattle", "ridgefield", "roseland", "crystal ballroom", 
                "mcdonald", "showbox", "elsinore", "cascades"
            ]
            
            if any(key in analysis.lower() for key in pnw_keywords):
                report = f"🌲 PNW BUCKETHEAD ALERT\n\n{analysis}"
                send_telegram_notification(report)
                # Save state so we don't alert again for the same data
                with open(STATE_FILE, "w") as f:
                    f.write(aggregated_data)
            else:
                print("Changes found but no PNW dates confirmed.")
        else:
            print("No changes. Silent mode active.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_agent())
