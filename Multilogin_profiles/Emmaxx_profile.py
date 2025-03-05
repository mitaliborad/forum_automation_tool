import requests
import time
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging

# --- MultiLogin Configuration ---
MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER_V2 = "https://launcher.mlx.yt:45001/api/v2"
LOCALHOST = "http://127.0.0.1"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

USERNAME = "armanmishra1115@gmail.com"  # Replace with your MultiLogin username
PASSWORD = "Nik&291411"  # Replace with your MultiLogin password
FOLDER_ID = "2895cd9a-0e5f-44bc-a1f5-344a8d81baaa"
PROFILE_ID = "ece3d7b0-6dd3-4189-94c7-20c2dfa82943"

def signin(logger) -> str:
    password_hash = hashlib.md5(PASSWORD.encode()).hexdigest()
    payload = {
        "email": USERNAME,
        "password": password_hash,  # Use the hashed password
    }
    try:
        response = requests.post(f"{MLX_BASE}/user/signin", json=payload)

        if response.status_code != 200:
            logger.error(f"Error during login: {response.text}")
            return None

        data = response.json().get("data", {})
        token = data.get("token")

        if not token:
            logger.error("Authentication failed. Please check credentials.")
            return None

        logger.info("Successfully logged in.")
        return token

    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error during login: {e}")
        return None

def start_profile(token: str, logger) -> webdriver.Remote | None:
    """Starts the MultiLogin profile and returns a Selenium WebDriver instance."""
    try:
        response = requests.get(
            f"{MLX_LAUNCHER_V2}/profile/f/{FOLDER_ID}/p/{PROFILE_ID}/start?automation_type=selenium",
            headers={"Authorization": f"Bearer {token}", **HEADERS},
        )

        if response.status_code != 200:
            logger.error(f"Error while starting profile: {response.text}")
            return None

        data = response.json().get("data", {})
        if "port" not in data:
            logger.error(f"Unexpected response format: {response.json()}")
            return None

        selenium_port = data["port"]
        driver = webdriver.Remote(
            command_executor=f"{LOCALHOST}:{selenium_port}",
            options=Options()
        )
        logger.info(f"MultiLogin profile started on port {selenium_port}.")
        return driver

    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error while starting profile: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating webdriver instance: {e}", exc_info=True)
        return None

def stop_profile(token: str, logger) -> None:
    """Stops the MultiLogin profile."""
    try:
        response = requests.get(f"{MLX_LAUNCHER_V2}/profile/stop/p/{PROFILE_ID}",
                                headers={"Authorization": f"Bearer {token}", **HEADERS})

        if response.status_code != 200:
            logger.error(f"Error while stopping profile: {response.text}")
        else:
            logger.info(f"Profile {PROFILE_ID} stopped.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error while stopping profile: {e}")