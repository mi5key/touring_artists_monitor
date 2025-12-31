import subprocess
import sys

def send_imessage(phone_number, message):
    apple_script = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{phone_number}" of targetService
        send "{message}" to targetBuddy
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', apple_script], check=True)
        print(f"Message sent to {phone_number}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to send message: {e}")

if __name__ == "__main__":
    print("Attempting to send a test message...")
    send_imessage("323-973-3509", "Test message from Buckethead Monitor")
