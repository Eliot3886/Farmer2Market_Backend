import threading
import time
import requests
import os

def start_pinger():
    # Only run in production (if DEBUG is False)
    if os.environ.get('DEBUG', 'False').lower() == 'true':
        print("Pinger: Debug mode active, skipping pinger.")
        return

    def ping():
        url = os.environ.get('RENDER_EXTERNAL_URL')
        if not url:
            print("Pinger: RENDER_EXTERNAL_URL not set, skipping.")
            return

        ping_url = f"{url.rstrip('/')}/api/ping/"
        print(f"Pinger: Starting pinger for {ping_url}")
        
        while True:
            try:
                response = requests.get(ping_url)
                print(f"Pinger: Pinged {ping_url} - Status: {response.status_code}")
            except Exception as e:
                print(f"Pinger: Error pinging {ping_url}: {e}")
            
            # Ping every 10 minutes (Render sleeps after 15 mins)
            time.sleep(600)

    # Start as a daemon thread so it doesn't block exit
    thread = threading.Thread(target=ping, daemon=True)
    thread.start()
