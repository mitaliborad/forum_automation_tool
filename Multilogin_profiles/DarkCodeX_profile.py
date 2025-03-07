import requests
import time
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging

# --- MultiLogin Configuration ---
MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER_V1 = "https://launcher.mlx.yt:45001/api/v1"  # Updated endpoint
LOCALHOST = "http://127.0.0.1"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

USERNAME = "armanmishra1115@gmail.com"  # Replace with your MultiLogin username
PASSWORD = "Nik&291411"  # Replace with your MultiLogin password
FOLDER_ID = "fedd6c4d-f3d0-4bcd-8b25-e6ce25559ea8"
PROFILE_ID = "d949ef43-c834-44b4-9628-f60bb0c33b77"

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
        logger.info(f"Starting profile {PROFILE_ID}...")
        response = requests.get(
            f"{MLX_LAUNCHER_V1}/profile/f/{FOLDER_ID}/p/{PROFILE_ID}/start?automation_type=selenium",
            headers={"Authorization": f"Bearer {token}", **HEADERS},
            verify=False  # Disable SSL verification for testing
        )

        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.json()}")  # Log the full response

        if response.status_code != 200:
            logger.error(f"Error while starting profile: {response.text}")
            return None

        # Handle the new response format
        response_data = response.json()
        if "status" in response_data and "message" in response_data["status"]:
            selenium_port = response_data["status"]["message"]
            logger.info(f"Extracted port from response: {selenium_port}")
        else:
            logger.error(f"Unexpected response format: {response_data}")
            return None

        # Start the WebDriver
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
    """Attempts to stop the MultiLogin profile using the correct endpoint."""
    try:
        logger.info(f"Attempting to stop MultiLogin profile: {PROFILE_ID}...")

        # Stop the profile using the correct endpoint
        response = requests.get(
            f"{MLX_LAUNCHER_V1}/profile/stop/p/{PROFILE_ID}",
            headers={"Authorization": f"Bearer {token}", **HEADERS},
            verify=False  # Disable SSL verification for testing
        )

        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")

        if response.status_code == 200:
            logger.info(f"Profile {PROFILE_ID} stopped successfully.")
        elif response.status_code == 404:
            logger.warning(f"Profile {PROFILE_ID} not found. It might already be stopped.")
        else:
            logger.error(f"Failed to stop profile: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error while stopping profile: {e}")
"""
# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    token = signin(logger)
    if token:
        driver = start_profile(token, logger)
        if driver:
            # Perform your automation tasks here
            time.sleep(10)  # Example delay

            # Close the browser
            driver.quit()
            logger.info("Browser closed successfully.")

            # Add a small delay before stopping the profile
            time.sleep(5)  # Wait for processes to clean up

            # Stop the profile
            stop_profile(token, logger)
"""