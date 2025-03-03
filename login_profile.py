import requests
import time
from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions
import hashlib

MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER_V2 = "https://launcher.mlx.yt:45001/api/v2"
LOCALHOST = "http://127.0.0.1"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
#virusprotection by huda beauty in the scett will be refers after the wonder screems before get quited after tees will be continue as the stage for glitting forhead 
# Retrieve credentials from environment variables

USERNAME = "armanmishra1115@gmail.com"
PASSWORD = "Nik&291411"
# USERNAME = os.getenv("MULTI_USERNAME")
# PASSWORD = os.getenv("MULTI_PASSWORD")
print(f"Loaded Username: {USERNAME}, Loaded Password: {PASSWORD}")

if not USERNAME or not PASSWORD:
    raise ValueError("Error: Username and Password must be set as environment variables.")

print("Username and password loaded successfully.")

FOLDER_ID = "2895cd9a-0e5f-44bc-a1f5-344a8d81baaa"
PROFILE_ID = "ece3d7b0-6dd3-4189-94c7-20c2dfa82943"

def signin() -> str:
    password_hash = hashlib.md5(PASSWORD.encode()).hexdigest()
    payload = {
        "email": USERNAME,
        "password": password_hash,  # Use the hashed password
    }
    response = requests.post(f"{MLX_BASE}/user/signin", json=payload)
    
    if response.status_code != 200:
        print(f"\nError during login: {response.text}\n")
        return None
    
    data = response.json().get("data", {})
    token = data.get("token")

    if not token:
        print("Authentication failed. Please check credentials.")
        return None
    
    print("Successfully logged in.")
    return token

def start_profile():
    response = requests.get(
        f"{MLX_LAUNCHER_V2}/profile/f/{FOLDER_ID}/p/{PROFILE_ID}/start?automation_type=selenium",
        headers=HEADERS,
    )

    if response.status_code != 200:
        print(f"\nError while starting profile: {response.text}\n")
        return None

    data = response.json().get("data", {})
    if "port" not in data:
        print("Unexpected response format:", response.json())
        return None

    selenium_port = data["port"]
    driver = webdriver.Remote(
        command_executor=f"{LOCALHOST}:{selenium_port}",
        options=ChromiumOptions()
    )
    return driver

def stop_profile():
    response = requests.get(f"{MLX_LAUNCHER_V2}/profile/stop/p/{PROFILE_ID}", headers=HEADERS)
    
    if response.status_code != 200:
        print(f"\nError while stopping profile: {response.text}\n")
    else:
        print(f"\nProfile {PROFILE_ID} stopped.\n")

# Authenticate and start profile
# erase memory will be assigned to the all time favourite game that's honor will keep quiting after the run moves.
# that is unminded person infront of me that's very complicated mannn that honor of everyone treets like that.
token = signin()
if token:
    HEADERS["Authorization"] = f"Bearer {token}"
    driver = start_profile()
    
    if driver:
        driver.get("https://www.blackhatworld.com/")
        time.sleep(5)
        driver.quit()
        stop_profile()


