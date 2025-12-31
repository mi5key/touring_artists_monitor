use anyhow::{Result, Ok};
use chrono::Local;
use headless_chrome::{Browser, LaunchOptions};
use std::process::Command;
use std::thread;
use std::time::Duration;

fn main() -> Result<()> {
    // Print timestamp first thing (log format)
    let now = Local::now();
    // Use slightly different format to match "date +%Y-%m-%d-%H%M" from wrapper script if we want consistency
    // User asked for "2025-12-30-1600 - "
    print!("{} - ", now.format("%Y-%m-%d-%H:%M"));

    let opts = LaunchOptions {
        headless: true,
        ..Default::default()
    };
    
    // Launch browser
    let browser = Browser::new(opts)?;
    let tab = browser.new_tab()?;
    
    // Navigate
    tab.navigate_to("https://bucketheadtour.us/")?;
    
    // Wait for selector (playwright equivalent)
    // There isn't a direct "wait_for_selector" with high level convenience in basic example,
    // but find_elements will retry for a bit or we can wait.
    // simpler: search for element with retry.
    
    let element_found = tab.wait_for_element("a.div-link");
    
    if element_found.is_err() {
        println!("No matching tour dates found in Oregon or Washington.");
        return Ok(());
    }

    // Get all elements
    let elements = tab.find_elements("a.div-link")?;
    
    let mut matches = Vec::new();

    for elem in elements {
        // Get inner text
        // inner_text might need to be fetched via JS or attributes
        if let std::result::Result::Ok(text) = elem.get_inner_text() {
             // Parse lines
             let lines: Vec<&str> = text.split('\n').map(|s| s.trim()).collect();
             
             // Python logic:
             // Line 0: Day
             // Line 1: Date
             // ...
             // Line 3 (index 3) or 4 (index 4) is location.
             // "Fri", "Jan 23", "6:30 PM", "Buckethead", "Ace of Spades..."
             
             if lines.len() < 4 {
                 continue;
             }
             
             let date_str = format!("{} {}", lines[0], lines[1]);
             let location_str = if lines.len() > 4 {
                 lines[4]
             } else {
                 lines[lines.len() - 2] // Fallback
             };
             
             let parts: Vec<&str> = location_str.split(',').map(|s| s.trim()).collect();
             if parts.len() < 3 {
                 continue; 
             }
             
             let state = parts.last().unwrap_or(&"");
             let _city = parts.get(parts.len() - 2).unwrap_or(&"");
             let venue = parts[..parts.len() - 2].join(", ");

             // Filter logic: OR or WA (or AZ for testing if requested, sticking to OR/WA for now)
             if *state == "OR" || *state == "WA" {
                 matches.push(format!("{} - {}, {}, {}", date_str, venue, _city, state));
             }
        }
    }

    if !matches.is_empty() {
        let summary = format!("Buckethead Tour Matches Found: {}", matches.join("; "));
        println!("{}", summary);
        
        // SMS
        let sms_body = format!("Buckethead Tour Matches Found:\n{}", matches.join("\n"));
        // send_imessage logic
        send_imessage("323-973-3509", &sms_body)?;
    } else {
        println!("No matching tour dates found in Oregon or Washington.");
    }

    Ok(())
}

fn send_imessage(phone: &str, message: &str) -> Result<()> {
    let script = format!(
        "tell application \"Messages\"\n\
        set targetService to 1st account whose service type = iMessage\n\
        set targetBuddy to participant \"{}\" of targetService\n\
        send \"{}\" to targetBuddy\n\
        end tell",
        phone, message
    );

    Command::new("osascript")
        .arg("-e")
        .arg(script)
        .output()?;
    Ok(())
}
