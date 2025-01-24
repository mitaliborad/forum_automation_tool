from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from pynput.mouse import Button, Controller
import random
import time
import logging
from datetime import datetime
import numpy as np
import os

# --- Configure Logging ---
# To track what the script is doing
def setup_logger(log_dir):
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"script_log_{timestamp}.log")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)  # Set to INFO for cleaner console output

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger, log_file

log_directory = "Selenium-Logs"
logger, log_file = setup_logger(log_directory)
logger.info(f"Log file created at: {log_file}")

# --- Mouse Movement Functions ---
mouse = Controller()
# ----- Curve Generation (Bezier Curve) -----

def bezier_curve(p0, p1, p2, t):
    """Calculates a point on a Bezier curve using 3 control points."""
    return (1-t)**2 * p0 + 2*(1-t)*t*p1 + t**2*p2

def generate_bezier_path(start, end, num_points=50):
    """Generates a path of points based on a random Bezier curve."""

    control_point = ( #Generates a random control point for the curve
        start[0] + random.randint(-100, 100),
        start[1] + random.randint(-100, 100)
    )
    path = []
    for i in range(num_points):
        t = i / (num_points - 1) #Calculates the position along the curve
        point = bezier_curve(np.array(start),np.array(control_point), np.array(end), t) #Calculate point on curve
        path.append((int(point[0]),int(point[1]))) #Adds the new point in the curve path
    return path

def move_mouse_with_curve(target_x, target_y, smoothing_factor=10, base_speed=0.001):
    """Moves the mouse cursor along a path of random bezier curve with varying speed."""
    logger.debug(f"Starting mouse movement to ({target_x}, {target_y}).") #Logs that mouse movement has started
    current_x, current_y = mouse.position #Gets the current mouse position

    # Generate the path
    path = generate_bezier_path((current_x, current_y), (target_x, target_y)) #Generates a curve path to the target

    for i, (x, y) in enumerate(path):
        # Random Speed
        speed = base_speed * random.uniform(0.8, 1.5)  # Vary the base speed slightly

        # Calculate a delay based on the distance, longer distance == longer delay
        distance = np.sqrt((current_x - x)**2 + (current_y - y)**2)
        delay = speed * (distance **0.75)
        time.sleep(delay) #Pauses the execution for the calculated delay

        mouse.position = (x,y) # Moves the mouse to the new point
        current_x, current_y = x,y #Updates the current mouse position
        logger.debug(f"Moved mouse to ({x}, {y}) with a delay of {delay:.5f} seconds.") #Logs mouse movement details

# --- Selenium Setup ---
# for reduce websites detection mechanisms
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

# --- Helper Functions ---
# To mimic human-like scrolling behavior by scrolling a set amount and having a short delay before continuing.
def scroll_page(driver, scroll_amount=500, min_delay=0.5, max_delay=1.0):
  """Scrolls the page a single time with a random delay for simulating user-like behavior."""
  driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
  delay = random.uniform(min_delay, max_delay)
  time.sleep(delay)
  logger.debug(f"Scrolled page by {scroll_amount}, Delay: {delay:.2f} seconds.")

#for random scrolling , emulating human browsing behavior
def scroll_random_times(driver, min_scrolls=3, max_scrolls=7, scroll_amount=500):
    """Scrolls the page a random number of times."""
    num_scrolls = random.randint(min_scrolls, max_scrolls)
    logger.debug(f"Scrolling page {num_scrolls} times.")
    for _ in range(num_scrolls):
        scroll_page(driver, scroll_amount)
    logger.debug("Scrolling Completed")

#To ensure reliable clicks using JavaScript as the main method and ActionChains as a fallback.
def click_element(driver, locator):
    """Clicks element using JavaScript click, and ActionChains as fallback"""
    try:
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(locator))
        logger.debug("Element located successfully. Attempting to click using Javascript")
        driver.execute_script("arguments[0].focus();", element) #Focus the element
        driver.execute_script("arguments[0].click();", element) #Click using JS click
        logger.info("Element clicked using JavaScript click.")
    except Exception as e:
        logger.warning(f"JavaScript click failed: {e}. Attempting ActionChains click.")
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(locator)) # Locates element again
            actions = ActionChains(driver)
            actions.move_to_element(element).click().perform()
            logger.info("Element clicked using ActionChains click.")
        except Exception as e:
            logger.error(f"ActionChains click failed: {e}", exc_info=True)


# --- Selenium Actions ---
try:
    # Initial Scroll
    scroll_random_times(driver)
    logger.info("Initial random scroll completed.")

    # Locate the "Social Networking" Link
    link_locator = (By.LINK_TEXT, "Social Networking")
    logger.debug("Locating 'Social Networking' Link.")
    
    #Scroll the element into view
    element = WebDriverWait(driver,10).until(EC.presence_of_element_located(link_locator))
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    logger.debug("Scrolled the element into view.")

    # Find the "Social Networking" link
    link = driver.find_element(By.LINK_TEXT, "Social Networking") #Finds the link using link text
    logger.debug("Found 'Social Networking' link.") #Logs that the link is found

    # Get the location and size of the element
    location = link.location #Gets the location of the element
    size = link.size #Gets the size of the element

    # Calculate center coordinates of the link element
    target_x = location['x'] + size['width'] // 2 #Calculate the x coordinate of the center of the element
    target_y = location['y'] + size['height'] // 2 #Calculate the y coordinate of the center of the element

     # Move the mouse using move_mouse_with_curve
    move_mouse_with_curve(target_x, target_y) #Moves the mouse using a curve

    # Click the link using Selenium's click method
    time.sleep(random.uniform(0.1, 0.3)) #Pauses the execution before the click
    
    #Click the element
    click_element(driver, link_locator)
    time.sleep(random.uniform(1.5, 2))

    # Scroll down after click
    scroll_random_times(driver, min_scrolls=9, max_scrolls=10)
    logger.info("Scrolling completed after click.")

    time.sleep(2)
    logger.debug("Pausing before quitting driver...")
    driver.quit()
    logger.info("Driver quit successfully.")
except Exception as e:
    logger.error(f"An error occurred: {e}", exc_info=True)
    if 'driver' in locals():
        driver.quit()