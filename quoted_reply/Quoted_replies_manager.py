import requests
import time
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import random
from pynput.keyboard import Key, Controller
from pynput.mouse import Controller as MouseController
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- MultiLogin Configuration ---
MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER_V1 = "https://launcher.mlx.yt:45001/api/v2"  # Updated endpoint
LOCALHOST = "http://127.0.0.1"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

# --- Profile Configuration (moved out of class - Manager Style) ---
PROFILES = {    
    "Emaxx": {
        "username": "armanmishra1115@gmail.com",
        "password": "Nik&291411",
        "folder_id": "2895cd9a-0e5f-44bc-a1f5-344a8d81baaa",
        "profile_id": "ece3d7b0-6dd3-4189-94c7-20c2dfa82943",
        "launcher_url": "https://launcher.mlx.yt:45001/api/v1"
    },
    "DarkCodeX": {
        "username": "armanmishra1115@gmail.com",
        "password": "Nik&291411",
        "folder_id": "fedd6c4d-f3d0-4bcd-8b25-e6ce25559ea8",
        "profile_id": "d949ef43-c834-44b4-9628-f60bb0c33b77",
        "launcher_url": "https://launcher.mlx.yt:45001/api/v1"
    },
    "ZeroDayHunter":{
        "username": "armanmishra1115@gmail.com",
        "password": "Nik&291411",
        "folder_id": "2895cd9a-0e5f-44bc-a1f5-344a8d81baaa",
        "profile_id": "e70a0144-441c-40ec-92fc-84a43bc03e6a",
        "launcher_url": "https://launcher.mlx.yt:45001/api/v1"
    },
    "BinaryGhost":{
        "username": "armanmishra1115@gmail.com",
        "password": "Nik&291411",
        "folder_id": "2895cd9a-0e5f-44bc-a1f5-344a8d81baaa",
        "profile_id": "8bede9f0-d352-4430-acd5-fd8df8f4a8cb",
        "launcher_url": "https://launcher.mlx.yt:45001/api/v1"
    },
    "NullBytee":{
        "username": "armanmishra1115@gmail.com",
        "password": "Nik&291411",
        "folder_id": "2895cd9a-0e5f-44bc-a1f5-344a8d81baaa",
        "profile_id": "33096624-f91e-4137-b999-8508a489375e",
        "launcher_url": "https://launcher.mlx.yt:45001/api/v1"
    },
    "PhantomRoot":{
        "username": "armanmishra1115@gmail.com",
        "password": "Nik&291411",
        "folder_id": "2895cd9a-0e5f-44bc-a1f5-344a8d81baaa",
        "profile_id": "8c98d4bf-a650-472e-ada8-4f3ae5d61152",
        "launcher_url": "https://launcher.mlx.yt:45001/api/v1"
    },
    "DataPhreak":{
        "username": "armanmishra1115@gmail.com",
        "password": "Nik&291411",
        "folder_id": "2895cd9a-0e5f-44bc-a1f5-344a8d81baaa",
        "profile_id": "54a81ba0-2713-4c85-bdc6-78e91dee21ab",
        "launcher_url": "https://launcher.mlx.yt:45001/api/v1"
    },
    "PixelPirate99":{
        "username": "armanmishra1115@gmail.com",
        "password": "Nik&291411",
        "folder_id": "2895cd9a-0e5f-44bc-a1f5-344a8d81baaa",
        "profile_id": "1038850a-a71c-4c6e-9f86-19b7937ee408",
        "launcher_url": "https://launcher.mlx.yt:45001/api/v1"
    }
}

# --- Configuration Constants ---
STAGGER_DELAY_MINUTES_MIN = 0
STAGGER_DELAY_MINUTES_MAX = 1
RANDOM_ACTION_CHANCE = 0.5  # Probability of performing a random action
RANDOM_PAUSE_MIN = 30       # Minimum pause duration in seconds
RANDOM_PAUSE_MAX = 50      # Maximum pause duration in seconds
NEW_TAB_URL = "https://www.google.com"  # Example URL for the new tab
RANDOM_WEBSITES = ["https://www.canva.com/en_in/", "https://www.adobe.com/in/products/photoshop.html", "https://www.w3schools.com/", "https://github.com/", "https://www.teejh.com/", "https://letshyphen.com/", "https://www.netflix.com/in/"]
MINIMIZE_DELAY_MIN = 15  # Minimum minimize duration in seconds
MINIMIZE_DELAY_MAX = 30 # Maximum minimize duration in seconds
SCROLL_PAUSE_TIME = 0.9

LOG_FOLDER = "Selenium_Logs"


# --- Absolute Path for Log Folder ---
try:
    # Get the directory where *this* script (Quoted_replies_manager.py) is located
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    LOG_FOLDER = os.path.join(_script_dir, "Selenium_Logs")
    print(f"[INFO] Log directory target: {LOG_FOLDER}") # Print target location
except NameError:
    # Fallback if __file__ is not defined (e.g., interactive session)
    LOG_FOLDER = os.path.join(os.getcwd(), "Selenium_Logs")
    print(f"[WARN] Could not determine script directory, using CWD for logs: {LOG_FOLDER}")

# --- Logger Configuration Function ---
def configure_logger(profile_name):
    """Configures a dedicated logger for a specific profile."""
    logger = logging.getLogger(profile_name) # Use profile_name as logger name

    # Prevent adding handlers multiple times
    if logger.hasHandlers():
        # print(f"Logger for {profile_name} already configured. Clearing existing handlers.") # Optional debug print
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG) # Set logger base level to DEBUG to allow handlers to capture everything

    # Create the log directory using the absolute path
    try:
        os.makedirs(LOG_FOLDER, exist_ok=True) # exist_ok=True prevents error if folder exists
        # print(f"[DEBUG] Ensured log directory exists: {LOG_FOLDER}") # Optional debug
    except OSError as e:
        print(f"[ERROR] Critical error creating log directory {LOG_FOLDER}: {e}. File logging disabled.")
        # Setup console-only logging as fallback
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s] - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.propagate = False
        return logger # Return the console-only logger

    log_file_path = os.path.join(LOG_FOLDER, f"{profile_name}.log")

    # --- Add diagnostic print ---
    print(f"[INFO] Logger {profile_name}: Attempting to configure file logging to: {log_file_path}")

    # File Handler
    try:
        # Use 'a' mode to append if file exists, 'w' to overwrite each run
        fh = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        fh.setLevel(logging.DEBUG) # Capture DEBUG level and above in the file
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        # print(f"[DEBUG] Logging for {profile_name} configured to file: {log_file_path}") # Optional debug print
    except Exception as e:
        print(f"[ERROR] Error setting up file handler for {profile_name} at {log_file_path}: {e}")
        # Continue to setup console handler even if file handler fails

    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO) # Show INFO level and above on console
    ch_formatter = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s] - %(message)s') # Slightly different format for console
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)

    # Prevent log messages from propagating to the root logger
    logger.propagate = False

    logger.info(f"Logger configured for {profile_name}. Logging to Console (INFO+) and File (DEBUG+): {log_file_path}")
    return logger


# --- Global Controller Instances for Pynput ---
try:
    keyboard_controller = Controller()
    mouse_controller = MouseController()
except Exception as e:
    # Use root logger or print if controllers fail early
    logging.basicConfig(level=logging.ERROR) # Basic config for early errors
    logging.error(f"Failed to initialize pynput controllers: {e}", exc_info=True)
    print("[ERROR] Failed to initialize pynput controllers. Minimize/Restore actions may fail.")
    keyboard_controller = None
    mouse_controller = None


# --- Helper Functions (No Class - Manager Logic) ---
def signin(profile_name, profile_config, profile_logger):
    """Signs in using profile config."""
    password_hash = hashlib.md5(profile_config["password"].encode()).hexdigest()
    payload = {
        "email": profile_config["username"],
        "password": password_hash,
    }
    profile_logger.debug(f"Signin payload (excluding password hash): { {'email': payload['email']} }") 
    try:
        response = requests.post(f"{MLX_BASE}/user/signin", json=payload)
        profile_logger.debug(f"Signin response status code: {response.status_code}")

        if response.status_code != 200:
            profile_logger.error(f"Profile {profile_name}: Error during login: {response.text}")
            return None

        data = response.json().get("data", {})
        token = data.get("token")
        expires_in = data.get("expires_in", 10800)  # Default to 1 hour if not provided
        profile_logger.info(f"Received expires_in from MultiLogin: {expires_in}")
        profile_logger.debug(f"Received 'expires_in': {expires_in} seconds from MultiLogin API.")
        expiration_time = time.time() + expires_in
        profile_logger.info(f"Calculated token expiration time: {expiration_time}")
        profile_logger.debug(f"Calculated token expiration time: {expiration_time}")

        if not token:
            profile_logger.error(f"Profile {profile_name}: Authentication failed.")
            return None, None

        profile_logger.info(f"Profile {profile_name}: Successfully logged in.")
        profile_logger.debug(f"Profile {profile_name}: Successfully logged in.")
        return token, expiration_time

    except requests.exceptions.RequestException as e:
        profile_logger.error(f"Profile {profile_name}: Connection error during login: {e}")
        return None, None
    
def refresh_token(profile_name, profile_config, profile_logger):
    """Refreshes the token when it expires."""
    profile_logger.info(f"Refreshing token for {profile_name}...")
    profile_logger.debug(f"Refreshing token for {profile_name}...")
    return signin(profile_name, profile_config, profile_logger)

def start_profile(profile_name, profile_config, token, profile_logger):
    """Starts profile using its config and token."""
    try:
        profile_logger.info(f"Profile {profile_name}: Starting profile {profile_config['profile_id']}...")
        profile_logger.debug(f"Attempting to start profile via URL: {profile_config['launcher_url']}/profile/f/{profile_config['folder_id']}/p/{profile_config['profile_id']}/start?automation_type=selenium")
        response = requests.get(
            f"{profile_config['launcher_url']}/profile/f/{profile_config['folder_id']}/p/{profile_config['profile_id']}/start?automation_type=selenium",
            headers={"Authorization": f"Bearer {token}", **HEADERS},
            verify=False  # Disable SSL verification for testing
        )

        if response.status_code != 200:
            profile_logger.error(f"Profile {profile_name}: Error starting profile: {response.text}")
            return None

        response_data = response.json()
        if "status" in response_data and "message" in response_data["status"]:
            selenium_port = response_data["status"]["message"]
            profile_logger.info(f"Profile {profile_name}: Extracted port: {selenium_port}")
            profile_logger.debug(f"Profile {profile_name}: Extracted port: {selenium_port}")
        else:
            profile_logger.error(f"Profile {profile_name}: Unexpected response format: {response_data}")
            return None

        driver = webdriver.Remote(
            command_executor=f"{LOCALHOST}:{selenium_port}",
            options=Options()
        )
        profile_logger.info(f"Profile {profile_name}: Started on port {selenium_port}.")
        profile_logger.debug(f"Profile {profile_name}: Started on port {selenium_port}.")
        return driver

    except requests.exceptions.RequestException as e:
        profile_logger.error(f"Profile {profile_name}: Connection error starting profile: {e}")
        return None
    except Exception as e:
        profile_logger.error(f"Profile {profile_name}: Error creating WebDriver instance: {e}", exc_info=True)
        return None


def stop_profile(profile_name, profile_config, token, profile_logger, driver, max_retries=3, retry_delay=2):
    """Stops profile, closing browser and stopping MultiLogin."""
    for attempt in range(max_retries):
        try:
            profile_logger.info(f"Profile {profile_name}: Attempting to stop (Attempt {attempt + 1}/{max_retries})...")
            profile_logger.debug(f"Profile {profile_name}: Attempting to stop (Attempt {attempt + 1}/{max_retries})...")

            if driver:
                try:
                    start_time = time.time()
                    driver.quit()
                    end_time = time.time()
                    profile_logger.info(f"Profile {profile_name}: Browser closed successfully in {end_time - start_time:.2f} seconds.")
                    profile_logger.debug(f"Profile {profile_name}: Browser closed successfully in {end_time - start_time:.2f} seconds.")
                except Exception as e:
                    profile_logger.error(f"Profile {profile_name}: Error closing browser: {e}", exc_info=True)

            start_time = time.time()
            response = requests.get(
                f"{profile_config['launcher_url']}/profile/stop/p/{profile_config['profile_id']}",
                headers={"Authorization": f"Bearer {token}", **HEADERS},
                verify=False #Disable SSL verification for testing
            )
            end_time = time.time()  # Time after the API call

            profile_logger.info(f"Profile {profile_name}: API call took {end_time - start_time:.2f} seconds.")
            profile_logger.debug(f"Profile {profile_name}: API call took {end_time - start_time:.2f} seconds.")

            if response.status_code == 200:
                profile_logger.info(f"Profile {profile_name}: Stopped successfully.")
                profile_logger.debug(f"Profile {profile_name}: Stopped successfully.")
                return
            elif response.status_code == 404:
                profile_logger.warning(f"Profile {profile_name}: Not found, may already be stopped.")
                return
            else:
                profile_logger.error(f"Profile {profile_name}: Failed to stop: {response.text}")

        except requests.exceptions.RequestException as e:
            profile_logger.error(f"Profile {profile_name}: Connection error stopping profile: {e}")
        except Exception as e:
            profile_logger.error(f"Profile {profile_name}: Unexpected error stopping profile: {e}", exc_info=True)

        if attempt < max_retries - 1:
            delay = random.uniform(retry_delay, retry_delay * 2)  # Jittered delay
            profile_logger.info(f"Profile {profile_name}: Retrying in {delay:.2f} seconds...")
            profile_logger.debug(f"Profile {profile_name}: Retrying in {delay:.2f} seconds...")
            time.sleep(delay)

    profile_logger.error(f"Profile {profile_name}: Failed to stop after {max_retries} attempts.")


def configure_logger(profile_name):
    """Configures a profile_logger for the given profile name."""
    profile_logger = logging.getLogger(profile_name)
    profile_logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    profile_logger.addHandler(ch)
    return profile_logger

def random_pause(profile_logger, profile_name):
    """Pauses execution for a random duration."""
    pause_duration = random.uniform(RANDOM_PAUSE_MIN, RANDOM_PAUSE_MAX)
    profile_logger.info(f"Profile {profile_name}: Pausing for {pause_duration:.2f} seconds...")
    profile_logger.debug(f"Profile {profile_name}: Pausing for {pause_duration:.2f} seconds...")
    time.sleep(pause_duration)
    profile_logger.info(f"Profile {profile_name}: Resuming...")
    profile_logger.debug(f"Profile {profile_name}: Resuming...")

def open_new_tab_default(driver, profile_logger, profile_name, url=NEW_TAB_URL):
    """Opens a new tab with the default URL."""
    try:
        profile_logger.info(f"Profile {profile_name}: Opening default URL: {url}")
        profile_logger.debug(f"Profile {profile_name}: Opening default URL: {url}")
        driver.execute_script(f"window.open('{url}', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        simulate_scrolling(driver, profile_logger, profile_name)
        driver.switch_to.window(driver.window_handles[0])  # Switch back to original tab
        profile_logger.info(f"Profile {profile_name}: Switched back to original tab.")
        profile_logger.debug(f"Profile {profile_name}: Switched back to original tab.")

    except Exception as e:
        profile_logger.error(f"Profile {profile_name}: Error opening new tab: {e}")

def open_new_tab_random(driver, profile_logger, profile_name):
    """Opens a new tab with a random website from the list."""
    try:
        url = random.choice(RANDOM_WEBSITES)
        profile_logger.info(f"Profile {profile_name}: Opening random website: {url}")
        profile_logger.debug(f"Profile {profile_name}: Opening random website: {url}")
        driver.execute_script(f"window.open('{url}', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        simulate_scrolling(driver, profile_logger, profile_name)
        driver.switch_to.window(driver.window_handles[0])  # Switch back to original tab
        profile_logger.info(f"Profile {profile_name}: Switched back to original tab.")
        profile_logger.debug(f"Profile {profile_name}: Switched back to original tab.")

    except Exception as e:
        profile_logger.error(f"Profile {profile_name}: Error opening random website: {e}")

def simulate_scrolling(driver, profile_logger, profile_name):
    """Simulates scrolling in the current tab."""
    profile_logger.info(f"({profile_name}) Simulating scrolling...")
    try:
        scroll_count = random.randint(3, 7)  # Scroll a few times
        profile_logger.debug(f"({profile_name}) Will perform {scroll_count} scroll actions.")
        for i in range(scroll_count):
            scroll_amount = random.randint(150, 400)
            driver.execute_script("window.scrollBy(0, 200);")  # Scroll down a bit
            profile_logger.debug(f"({profile_name}) Scrolled down by {scroll_amount} pixels (Action {i+1}/{scroll_count}).")
            time.sleep(SCROLL_PAUSE_TIME)
        random_pause(profile_logger, profile_name)  # Pause after scrolling

    except Exception as e:
        profile_logger.error(f"Profile {profile_name}: Error simulating scrolling: {e}")

def minimize_window(profile_logger, profile_name):
    """Minimizes the current window."""
    try:
        profile_logger.info(f"Profile {profile_name}: Minimizing window...")
        keyboard_controller.press(Key.cmd)  # Press Windows key
        keyboard_controller.press('m')  # Press M key
        keyboard_controller.release('m')  # Release M key
        keyboard_controller.release(Key.cmd)  # Release Windows key
        pause_duration = random.uniform(MINIMIZE_DELAY_MIN, MINIMIZE_DELAY_MAX)
        profile_logger.info(f"Profile {profile_name}: Window minimized. Pausing for {pause_duration:.2f} seconds...")
        profile_logger.debug(f"Profile {profile_name}: Window minimized. Pausing for {pause_duration:.2f} seconds...")
        time.sleep(pause_duration)
        profile_logger.info(f"Profile {profile_name}: Resuming after minimize...")
        profile_logger.debug(f"Profile {profile_name}: Resuming after minimize...")
    except Exception as e:
        profile_logger.error(f"Profile {profile_name}: Error minimizing window: {e}")

def restore_window(profile_logger, profile_name):
    """Restores the minimized window."""
    try:
        profile_logger.info(f"Profile {profile_name}: Restoring window...")
        profile_logger.debug(f"Profile {profile_name}: Restoring window...")
        keyboard_controller.press(Key.alt)  # Press Alt key
        keyboard_controller.press(Key.tab)  # Press Tab key
        keyboard_controller.release(Key.tab)  # Release Tab key
        keyboard_controller.release(Key.alt)  # Release Alt key
        time.sleep(2) # Short delay for window to restore
    except Exception as e:
        profile_logger.error(f"Profile {profile_name}: Error restoring window: {e}")

def perform_random_action(driver, profile_logger, profile_name):
    """Randomly performs a pause, opens a new tab, minimizes, or restores."""
    if random.random() < RANDOM_ACTION_CHANCE:
        actions = ["pause", "new_tab_default", "new_tab_random", "minimize", "restore"]  # Corrected typo here
        action = random.choice(actions)

        if action == "pause":
            random_pause(profile_logger, profile_name)
        elif action == "new_tab_default":
            open_new_tab_default(driver, profile_logger, profile_name)
        elif action == "new_tab_random":
            open_new_tab_random(driver, profile_logger, profile_name)
        elif action == "minimize":
            minimize_window(profile_logger, profile_name)
        elif action == "restore":
            restore_window(profile_logger, profile_name)
    else:
         profile_logger.debug(f"({profile_name}) Random action skipped (chance not met).")