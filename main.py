import os
import requests
import asyncio
from google import genai
from playwright.async_api import async_playwright

# --- Configuration ---
# Ensure NOTIFY_WEBHOOK_URL is: https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<ID>
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
    print(f"DEBUG: Attempting to send message. URL length: {len(TELEGRAM_URL) if TELEGRAM_URL else 0}")
    if not TELEGRAM_URL:
        print("DEBUG ERROR: TELEGRAM_URL is None")
        return
        
    url = f"{TELEGRAM_URL}&text={requests.utils.quote(message)}"
    try:
        response = requests.get(url, timeout=15)
        # This will print the actual error from Telegram (e.g., {"ok":false,"error_code":400...})
        print(f"DEBUG Telegram API Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"DEBUG Connection Error: {e}")
        
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
