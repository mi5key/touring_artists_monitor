# Buckethead Tour Monitor (will soon update to monitor additional/other artists)

This tool monitors [bucketheadtour.us](https://bucketheadtour.us/) for new tour dates in Oregon (OR) or Washington (WA). When matches are found, it logs them and sends an iMessage notification.

## Prerequisites

- **macOS**: Required for iMessage support (via AppleScript).
- **Python 3**: Ensure Python 3 is installed.
- **Playwright**: Used for scraping the dynamic content of the tour site.

## Installation

1.  **Clone or Download** the repository to your local machine.
2.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install Playwright Browsers**:
    ```bash
    playwright install chromium
    ```

## Configuration

> [!IMPORTANT]
> You must update the hardcoded paths and phone numbers in the scripts to match your environment.

1.  **Update Paths**:
    - **`run_monitor.sh`**: Edit line 4 to point to your project directory.
      ```bash
      cd /absolute/path/to/touring_artists_monitor
      ```
    - **`com.mike.davis.buckethead.monitor.plist`**: Update the paths for `ProgramArguments`, `StandardOutPath`, and `StandardErrorPath` to matches your file locations.

2.  **Update Phone Number**:
    - **`monitor_buckethead.py`**: Edit the `send_imessage` function (around line 7) to use your target phone number.
      ```python
      phone_number = "555-123-4567"
      ```

## Usage

### Manual Run
You can run the monitor manually to check for dates immediately:

```bash
python3 monitor_buckethead.py
```

Check `monitor.log` for output.

### Test SMS
To verify iMessage functionality works:

```bash
python3 test_sms.py
```

## Automation (Launchd)

To run the script automatically every hour:

1.  **Copy the plist** to your LaunchAgents folder:
    ```bash
    cp com.mike.davis.buckethead.monitor.plist ~/Library/LaunchAgents/
    ```
2.  **Load the Job**:
    ```bash
    launchctl load ~/Library/LaunchAgents/com.mike.davis.buckethead.monitor.plist
    ```

To stop the automation:
```bash
launchctl unload ~/Library/LaunchAgents/com.mike.davis.buckethead.monitor.plist
```
