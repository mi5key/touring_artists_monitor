import re
import sys
import subprocess
from playwright.sync_api import sync_playwright, TimeoutError

def send_imessage(message):
    phone_number = "323-973-3509"
    apple_script = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{phone_number}" of targetService
        send "{message}" to targetBuddy
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', apple_script], check=True)
        #print(f"SMS notification sent to {phone_number}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to send SMS: {e}")


def scrape_tour_dates():
    url = "https://bucketheadtour.us/"
    dates_found = []

    with sync_playwright() as p:
        browser = None
        for attempt in range(3):
            try:
                browser = p.chromium.launch(headless=True)
                break
            except TimeoutError:
                print(f"Browser launch attempt {attempt+1} failed with timeout.")
                if attempt == 2:
                    print("Failed to launch browser after 3 attempts.")
                    return []
            except Exception as e:
                print(f"Browser launch attempt {attempt+1} failed with error: {e}")
                if attempt == 2:
                    return []

        if not browser:
            return []
        page = browser.new_page()
        # print(f"Loading {url}...")
        page.goto(url)

        # Wait for the tour date links to appear
        try:
            page.wait_for_selector("a.div-link", timeout=10000)
        except Exception:
            print("No tour dates found (selector 'a.div-link' not visible within timeout).")
            browser.close()
            return []

        # Get all tour date elements
        tour_elements = page.query_selector_all("a.div-link")
        
        # print(f"Found {len(tour_elements)} potential tour dates. Analyzing...")

        for el in tour_elements:
            # The structure based on browser investigation:
            # 2nd div -> span is date text (Month Day)
            # 3rd div -> span is location (Venue, City, State)
            
            # Using inner_text to get the full text and parse it might be easier
            text_content = el.inner_text()
            # Expected format roughly: "Fri Jan 23\n6:30 PM\nBuckethead\nAce of Spades, Sacramento, CA\nGet Tickets"
            
            lines = text_content.split('\n')
            if len(lines) < 4:
                continue

            # Attempt to parse date and location
            # Line 0: Day Date (e.g., "Fri Jan 23")
            # Line 1: Time (e.g., "6:30 PM")
            # Line 3: Artist (e.g., "Buckethead")
            # Line 4: Location (e.g., "Ace of Spades, Sacramento, CA")
            
            # print(f"Debug: Lines: {lines}") 
            date_str = f"{lines[0]} {lines[1]}"
            if len(lines) > 4:
                location_str = lines[4].strip()
            else:
                location_str = lines[-2].strip() # Fallback
            
            # print(f"Debug: Analyzing location: '{location_str}'")
            
            # extract city and state from location string "Venue, City, ST"
            parts = [p.strip() for p in location_str.split(',')]
            if len(parts) >= 3:
                state = parts[-1]
                city = parts[-2]
                venue = ", ".join(parts[:-2])
            else:
                # Fallback if structure is weird
                state = "Unknown"
                city = "Unknown"
                venue = location_str

            # Filter logic
            ## Testing
            # if state == "OR" or state == "WA" or state == "AZ":
            ##
            if state == "OR" or state == "WA":
                dates_found.append({
                    "date": date_str,
                    "location": location_str,
                    "city": city,
                    "state": state,
                    "venue": venue
                })

        browser.close()
    
    return dates_found

if __name__ == "__main__":
    # print("Checking for Buckethead tour stops in OR or Southern WA...")
    matches = scrape_tour_dates()
    
    if matches:
        # print("\n!!! FOUND MATCHING TOUR DATES !!!")
        msg_lines = []
        for match in matches:
            line = f"{match['date']} - {match['venue']}, {match['city']}, {match['state']}"
            # print(line)
            msg_lines.append(line)
        
        # Join for single line output in log
        one_line_summary = "Buckethead Tour Matches Found: " + "; ".join(msg_lines)
        print(one_line_summary) # This goes to log (after timestamp)

        # Send SMS
        # For SMS, we might want newlines for readability, but user asked for log output change.
        # Let's keep SMS readable.
        sms_msg = "Buckethead Tour Matches Found:\n" + "\n".join(msg_lines)
        send_imessage(sms_msg)
    else:
        print("No matching tour dates found in Oregon or Washington.")
