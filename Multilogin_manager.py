import requests
import time
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import threading

# --- MultiLogin Configuration ---
MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER_V1 = "https://launcher.mlx.yt:45001/api/v1"  # Updated endpoint
LOCALHOST = "http://127.0.0.1"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

# --- Profile Configuration (moved out of class - Manager Style) ---
PROFILES = {
    "DarkCodeX": {
        "username": "armanmishra1115@gmail.com",
        "password": "Nik&291411",
        "folder_id": "fedd6c4d-f3d0-4bcd-8b25-e6ce25559ea8",
        "profile_id": "d949ef43-c834-44b4-9628-f60bb0c33b77",
        "launcher_url": "https://launcher.mlx.yt:45001/api/v1"
    },
    "Emmaxx": {
        "username": "armanmishra1115@gmail.com",
        "password": "Nik&291411",
        "folder_id": "2895cd9a-0e5f-44bc-a1f5-344a8d81baaa",
        "profile_id": "ece3d7b0-6dd3-4189-94c7-20c2dfa82943",
        "launcher_url": "https://launcher.mlx.yt:45001/api/v1"
    },
    # Add more profiles as needed
}


# --- Helper Functions (No Class - Manager Logic) ---
def signin(profile_name, profile_config, logger):
    """Signs in using profile config."""
    password_hash = hashlib.md5(profile_config["password"].encode()).hexdigest()
    payload = {
        "email": profile_config["username"],
        "password": password_hash,
    }
    try:
        response = requests.post(f"{MLX_BASE}/user/signin", json=payload)

        if response.status_code != 200:
            logger.error(f"Profile {profile_name}: Error during login: {response.text}")
            return None

        data = response.json().get("data", {})
        token = data.get("token")

        if not token:
            logger.error(f"Profile {profile_name}: Authentication failed.")
            return None

        logger.info(f"Profile {profile_name}: Successfully logged in.")
        return token

    except requests.exceptions.RequestException as e:
        logger.error(f"Profile {profile_name}: Connection error during login: {e}")
        return None


def start_profile(profile_name, profile_config, token, logger):
    """Starts profile using its config and token."""
    try:
        logger.info(f"Profile {profile_name}: Starting profile {profile_config['profile_id']}...")
        response = requests.get(
            f"{profile_config['launcher_url']}/profile/f/{profile_config['folder_id']}/p/{profile_config['profile_id']}/start?automation_type=selenium",
            headers={"Authorization": f"Bearer {token}", **HEADERS},
            verify=False  # Disable SSL verification for testing
        )

        if response.status_code != 200:
            logger.error(f"Profile {profile_name}: Error starting profile: {response.text}")
            return None

        response_data = response.json()
        if "status" in response_data and "message" in response_data["status"]:
            selenium_port = response_data["status"]["message"]
            logger.info(f"Profile {profile_name}: Extracted port: {selenium_port}")
        else:
            logger.error(f"Profile {profile_name}: Unexpected response format: {response_data}")
            return None

        driver = webdriver.Remote(
            command_executor=f"{LOCALHOST}:{selenium_port}",
            options=Options()
        )
        logger.info(f"Profile {profile_name}: Started on port {selenium_port}.")
        return driver

    except requests.exceptions.RequestException as e:
        logger.error(f"Profile {profile_name}: Connection error starting profile: {e}")
        return None
    except Exception as e:
        logger.error(f"Profile {profile_name}: Error creating WebDriver instance: {e}", exc_info=True)
        return None


def stop_profile(profile_name, profile_config, token, logger, driver):
    """Stops profile, closing browser and stopping MultiLogin."""
    try:
        logger.info(f"Profile {profile_name}: Attempting to stop...")

        if driver:
            try:
                driver.quit()
                logger.info(f"Profile {profile_name}: Browser closed successfully.")
            except Exception as e:
                logger.error(f"Profile {profile_name}: Error closing browser: {e}")

        response = requests.get(
            f"{profile_config['launcher_url']}/profile/stop/p/{profile_config['profile_id']}",
            headers={"Authorization": f"Bearer {token}", **HEADERS},
            verify=False #Disable SSL verification for testing
        )

        if response.status_code == 200:
            logger.info(f"Profile {profile_name}: Stopped successfully.")
        elif response.status_code == 404:
            logger.warning(f"Profile {profile_name}: Not found, may already be stopped.")
        else:
            logger.error(f"Profile {profile_name}: Failed to stop: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Profile {profile_name}: Connection error stopping profile: {e}")


def configure_logger(profile_name):
    """Configures a logger for the given profile name."""
    logger = logging.getLogger(profile_name)
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

# --- Main Execution Logic (Manager) ---
def manage_profile(profile_name, profile_config):
    """Manages a single profile: sign in, start, run tasks, stop."""
    logger = configure_logger(profile_name)
    token = signin(profile_name, profile_config, logger)

    if token:
        driver = start_profile(profile_name, profile_config, token, logger)
        if driver:
            try:
                # Perform your automation tasks here using the 'driver'
                logger.info(f"Profile {profile_name}: Running automation tasks...")
                time.sleep(5)  # Example task: Wait for 5 seconds
                logger.info(f"Profile {profile_name}: Automation tasks completed.")

            except Exception as e:
                logger.error(f"Profile {profile_name}: Error during automation: {e}")

            finally:
                stop_profile(profile_name, profile_config, token, logger, driver) # Pass the driver here
        else:
            logger.error(f"Profile {profile_name}: Failed to start.")
    else:
        logger.error(f"Profile {profile_name}: Failed to sign in.")

def manage_all_profiles():
    """Manages all profiles concurrently using threads."""
    threads = []
    for profile_name, profile_config in PROFILES.items():
        thread = threading.Thread(target=manage_profile, args=(profile_name, profile_config))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()  # Wait for all threads to finish
    print("All profiles managed.")

# --- Entry Point ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    manage_all_profiles()
