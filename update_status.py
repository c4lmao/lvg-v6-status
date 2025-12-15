import json
import os
import sys
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GitHub Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')  # format: "username/repo"
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH', 'main')

# File to update
STATUS_FILE = "status.json"
WEBHOOK_URL = "https://discord.com/api/webhooks/1449898428199862454/2F4gI-8tC70_t-fQWVBZzHJQkpfP_5UQNgGKxO3zHUwvsVTPlUD5VmENPacvib7kJnrb"

def get_current_status():
    """Get current status from GitHub"""
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{STATUS_FILE}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def update_status(new_status, reason="", message=""):
    """Update status on GitHub"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("❌ ERROR: GitHub token or repo not configured")
        return False
    
    # Get current status or create new
    current = get_current_status() or {
        "status": "on",
        "reason": "",
        "last_updated": "",
        "version": "v6.0",
        "maintenance": False,
        "message": ""
    }
    
    # Update fields
    current["status"] = new_status
    current["reason"] = reason
    current["last_updated"] = datetime.now(timezone.utc).isoformat()
    current["maintenance"] = (new_status == "off")
    if message:
        current["message"] = message
    
    # Prepare API request
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{STATUS_FILE}"
    
    # Get current file SHA (needed for update)
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # First, get current file info to get SHA
    response = requests.get(url, headers=headers)
    sha = None
    if response.status_code == 200:
        sha = response.json()["sha"]
    
    # Prepare data
    data = {
        "message": f"Update status to {new_status.upper()}",
        "content": json.dumps(current, indent=2).encode("utf-8").decode("unicode_escape"),
        "branch": GITHUB_BRANCH
    }
    
    if sha:
        data["sha"] = sha
    
    # Make request
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✅ Status updated to '{new_status}' on GitHub")
        
        # Send Discord notification
        send_discord_notification(new_status, reason)
        
        return True
    else:
        print(f"❌ Failed to update: {response.status_code} - {response.text}")
        return False

def send_discord_notification(status, reason=""):
    """Send notification to Discord webhook"""
    try:
        if status.lower() == "on":
            color = 0x00FF00
            title = "✅ DDOS V6 Status: ONLINE"
            description = "The application is now operational."
        else:
            color = 0xFF0000
            title = "⛔ DDOS V6 Status: OFFLINE"
            description = "The application has been taken offline."
        
        if reason:
            description += f"\n\n**Reason:** {reason}"
        
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "fields": [
                {"name": "Source", "value": "GitHub Status System", "inline": True},
                {"name": "Updated", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
            ],
            "footer": {"text": "Automated status update"}
        }
        
        requests.post(WEBHOOK_URL, json={"embeds": [embed]}, timeout=5)
        print("📨 Discord notification sent")
        
    except Exception as e:
        print(f"⚠️ Failed to send Discord notification: {e}")

def main():
    """Command line interface"""
    if len(sys.argv) < 2:
        print("Usage: python update_status.py <on|off> [reason] [message]")
        print("Example: python update_status.py off 'Maintenance' 'Scheduled update'")
        return
    
    new_status = sys.argv[1].lower()
    if new_status not in ["on", "off"]:
        print("❌ Status must be 'on' or 'off'")
        return
    
    reason = sys.argv[2] if len(sys.argv) > 2 else ""
    message = sys.argv[3] if len(sys.argv) > 3 else ""
    
    if update_status(new_status, reason, message):
        print("🎉 Status update successful!")
    else:
        print("💥 Status update failed!")

if __name__ == "__main__":
    main()
