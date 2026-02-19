import os
import requests
import asyncio
from google import genai
from playwright.async_api import async_playwright

# Configuration
VENUES = {
    "Official Site": "https://www.bucketheadtour.us/",
    "Roseland Theater": "https://roselandpdx.com/",
    "Crystal Ballroom": "https://www.mcmenamins.com/events",
    "McDonald Theatre": "https://mcdonaldtheatre.com/events"
}
STATE_FILE = "last_seen_dates.txt"
# This URL should be in the format: 
# https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>
TELEGRAM_URL = os.getenv("NOTIFY_WEBHOOK_URL")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def get_page_content(browser, url):
    page = await browser.new_page()
    try:
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
    You are a technical advisor analyzing concert tour data for Buckethead.
    
    Data from multiple sites:
    {all_data}
    
    Current Target: Salem, Oregon.
    Task:
    1. Identify any direct matches for 'Buckethead' or 'Brian Carroll' in Oregon.
    2. Analyze the March 14 (Santa Cruz, CA) to April 14 (Tucson, AZ) gap. 
    3. Determine if the current venue calendars for Roseland, Crystal Ballroom, or McDonald Theatre have unassigned dates in that window.
    4. Provide a probability (Low/Med/High) of an impending Oregon announcement based on geographic flow.
    
    Return a high-density, professional report for a technical user.
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text

async def send_notification(message):
    # Appends the message to the text parameter for Telegram
    url = f"{TELEGRAM_URL}&text={requests.utils.quote(message)}"
    response = requests.get(url)
    return response.status_code

async def run_agent():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        aggregated_data = ""
        for name, url in VENUES.items():
            content = await get_page_content(browser, url)
            aggregated_data += f"\n--- SOURCE: {name} ---\n{content}\n"
        
        # Load previous state to avoid duplicate notifications
        last_state = ""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                last_state = f.read()

        # Execute only if the data has changed
        if aggregated_data != last_state:
            analysis = await analyze_with_gemini(aggregated_data)
            await send_notification(f"🤖 Buckethead Agent Report\n\n{analysis}")
            
            with open(STATE_FILE, "w") as f:
                f.write(aggregated_data)
        else:
            print("No changes detected since last scan.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_agent())
