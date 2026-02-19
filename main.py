import os
import requests
import asyncio
from google import genai
from playwright.async_api import async_playwright

# Configuration
# Note: Ensure NOTIFY_WEBHOOK_URL in GitHub Secrets is the full URL:
# https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<ID>
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
        # Standard timeout for modern JS-heavy venue sites
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
    - User is located in Salem, Oregon.
    - Known Gap: March 14 (Santa Cruz, CA) to April 14 (Tucson, AZ).
    
    Task:
    1. Check for Oregon dates (Portland, Salem, Eugene).
    2. Analyze the 30-day gap. Identify if any listed venues have open dates in late March/early April.
    3. Estimate the probability of an Oregon show being added based on geographic proximity to the California/Arizona route.
    
    Provide a direct, data-driven report.
    """
    
    # Using Gemini 2.0 Flash for current compatibility
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt
    )
    return response.text

def send_telegram_notification(message):
    if not TELEGRAM_URL:
        print("Error: TELEGRAM_URL not configured.")
        return
        
    # Append message to the base sendMessage URL
    encoded_msg = requests.utils.quote(message)
    url = f"{TELEGRAM_URL}&text={encoded_msg}"
    
    try:
        response = requests.get(url)
        print(f"Telegram Notification Sent. Status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

async def run_agent():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        aggregated_data = ""
        for name, url in VENUES.items():
            print(f"Scraping {name}...")
            content = await get_page_content(browser, url)
            aggregated_data += f"\n--- {name} ---\n{content}\n"
        
        # State Check
        last_state = ""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                last_state = f.read()

        if aggregated_data.strip() != last_state.strip():
            print("Changes detected. Analyzing...")
            analysis = await analyze_with_gemini(aggregated_data)
            
            report = f"🤖 Buckethead Tour Report\n\n{analysis}"
            send_telegram_notification(report)
            
            with open(STATE_FILE, "w") as f:
                f.write(aggregated_data)
        else:
            print("No new data found since last check.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_agent())
