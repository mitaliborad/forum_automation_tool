from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import random
import time
import logging  # Import the logging module
from datetime import datetime  # Import datetime for unique filenames
import os  # Import os for directory management

# --- Configure Logging ---
def setup_logger(log_dir):
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Get timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"script_log_{timestamp}.log")

    # Configure the logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Log everything including DEBUG messages

    # Create a file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Log everything to file

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Log info and above to console

    # Create formatters and add to handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger, log_file


log_directory = "selenium_logs"  # Directory for log files
logger, log_file = setup_logger(log_directory)
logger.info(f"Log file created at: {log_file}")


# --- Selenium Setup ---
options = Options()
options.add_argument('disable-infobars')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

user_data = r"C:\Users\DELL\AppData\Local\Google\Chrome\User Data"
profile_name = "Profile 37"

options.add_argument(f"user-data-dir={user_data}")
logger.info(f"Starting Chrome with user data from: {user_data}")
driver = webdriver.Chrome(options=options)
driver.get("https://www.blackhatworld.com/")
logger.info("Navigated to https://www.blackhatworld.com/")

# --- Selenium Actions ---
try:

    # --- Human-like Scrolling Function ---
    def scroll(driver):
        logger.debug("Starting scrolling function...")
        for i in range(0,1):
            logger.debug(f"Scrolling iteration: {i+1}")
            driver.execute_script("window.scrollBy(0,400);")
            time.sleep(random.uniform(1.5, 2))
        logger.debug("Scrolling function completed.")

    scroll(driver)
    logger.info("Scrolling completed.")

    link = driver.find_element(By.LINK_TEXT, "Main Forum List")
    logger.debug("Found 'Main Forum List' link.")
    time.sleep(random.uniform(0.5, 2))
    logger.debug("Pausing for random delay before clicking link...")
    link.click()
    logger.info("Clicked 'Main Forum List' link.")

    # --- Human-like Scrolling Function ---
    def scroll_down(driver):
        logger.debug("Starting scrolling function...")
        for i in range(0,13):
            logger.debug(f"Scrolling iteration: {i+1}")
            driver.execute_script("window.scrollBy(0,700);")
            time.sleep(random.uniform(1.5, 2))
        logger.debug("Scrolling function completed.")

    scroll_down(driver)
    logger.info("Scrolling completed.")

    time.sleep(4)
    logger.debug("Pausing 4 seconds before quitting driver...")
    driver.quit()
    logger.info("Driver quit successfully.")

except Exception as e:
    logger.error(f"An error occurred: {e}", exc_info=True) #exc_info=True logs the traceback
    if 'driver' in locals(): # If driver was initialised and failed in middle.
        driver.quit()