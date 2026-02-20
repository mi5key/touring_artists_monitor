import os
import requests
import asyncio
from google import genai
from playwright.async_api import async_playwright

# --- Configuration ---
# Ensure NOTIFY_WEBHOOK_URL is: https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<ID>
# 
TELEGRAM_URL = os.getenv("NOTIFY_WEBHOOK_URL")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

VENUES = {
    "Official Site": "https://www.bucketheadtour.us/",
    "Roseland Theater": "https://roselandpdx.com/",
    "Crystal Ballroom": "https://www.mcmenamins.com/events",
    "McDonald Theatre": "https://mcdonaldtheatre.com/events"
}

STATE_FILE = "last_seen_dates.txt"

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_KEY)

async def get_page_content(browser, url):
    page = await browser.new_page()
    try:
        # 60s timeout for modern JS-heavy venue sites
        await page.goto(url, wait_until="networkidle", timeout=60000)
        content = await page.inner_text("body")
        return content
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""
    finally:
        await page.close()

async def analyze_with_gemini(all_data):
    prompt = f"""
    Analyze the following concert data for Buckethead (Brian Carroll).
    
    Data:
    {all_data}
    
    Context:
    - User location: Salem, Oregon.
    - Focus Window: March 14 (Santa Cruz, CA) to April 14 (Tucson, AZ).
    
    Task:
    1. Search for Oregon dates (Portland, Salem, Eugene).
    2. Analyze the 30-day gap. List any open dates for the target venues.
    3. Calculate probability of an Oregon addition based on geographic routing.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt
    )
    return response.text

def send_telegram_notification(message):
    if not TELEGRAM_URL:
        print("CRITICAL: NOTIFY_WEBHOOK_URL is None")
        return
        
    # Proper URL encoding is mandatory for automated agents
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    url = f"{TELEGRAM_URL}&text={encoded_message}"
    
    print(f"DEBUG: Dispatching request to Telegram...")
    try:
        response = requests.get(url, timeout=20)
        # THIS LINE REVEALS THE TRUTH:
        print(f"DEBUG Response Code: {response.status_code}")
        print(f"DEBUG Full JSON Response: {response.text}")
        
        if response.status_code != 200:
            print(f"ERROR: Telegram API rejected the request: {response.text}")
    except Exception as e:
        print(f"ERROR: Connection to Telegram failed: {e}")
        
async def run_agent():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        aggregated_data = ""
        for name, url in VENUES.items():
            print(f"Checking {name}...")
            content = await get_page_content(browser, url)
            aggregated_data += f"\n--- {name} ---\n{content}\n"
        
        # State Management
        last_state = ""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                last_state = f.read()

        # Comparison Logic
        if aggregated_data.strip() != last_state.strip():
            print("Changes detected. Analyzing...")
            analysis = await analyze_with_gemini(aggregated_data)
            
            report = f"🤖 Buckethead Tour Report\n\n{analysis}"
            send_telegram_notification(report)
            
            with open(STATE_FILE, "w") as f:
                f.write(aggregated_data)
        else:
            # Heartbeat Notification
            print("No changes. Sending heartbeat...")
            heartbeat = "✅ Heartbeat: No changes detected on venue sites. Monitoring active."
            send_telegram_notification(heartbeat)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_agent())
