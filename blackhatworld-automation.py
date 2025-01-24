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
    logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Console logs are still INFO level

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
    result = (1-t)**2 * p0 + 2*(1-t)*t*p1 + t**2*p2
    logger.debug(f"bezier_curve: t={t}, p0={p0}, p1={p1}, p2={p2}, result={result}")
    return result

def generate_bezier_path(start, end, num_points=50):
    """Generates a path of points based on a random Bezier curve."""
    logger.debug(f"generate_bezier_path: start={start}, end={end}, num_points={num_points}")
    
    control_point = (
        start[0] + random.randint(-100, 100),
        start[1] + random.randint(-100, 100)
    )
    logger.debug(f"generate_bezier_path: control_point={control_point}")
    path = []
    for i in range(num_points):
        t = i / (num_points - 1)
        point = bezier_curve(np.array(start),np.array(control_point), np.array(end), t)
        path.append((int(point[0]),int(point[1])))
        logger.debug(f"generate_bezier_path: step {i}, t={t}, point={point}, path_point={path[-1]}")
    logger.debug(f"generate_bezier_path: Generated path with {len(path)} points.")
    return path

def move_mouse_with_curve(target_x, target_y, smoothing_factor=10, base_speed=0.001):
    """Moves the mouse cursor along a path of random bezier curve with varying speed."""
    logger.debug(f"move_mouse_with_curve: Starting mouse movement to ({target_x}, {target_y}).")
    current_x, current_y = mouse.position
    logger.debug(f"move_mouse_with_curve: Current mouse position: ({current_x}, {current_y}).")

    # Generate the path
    path = generate_bezier_path((current_x, current_y), (target_x, target_y))
    logger.debug(f"move_mouse_with_curve: Generated path with {len(path)} points.")

    for i, (x, y) in enumerate(path):
        # Random Speed
        speed = base_speed * random.uniform(0.8, 1.5)
        logger.debug(f"move_mouse_with_curve: Step {i}, speed={speed:.2f}")

        # Calculate a delay based on the distance, longer distance == longer delay
        distance = np.sqrt((current_x - x)**2 + (current_y - y)**2)
        delay = speed * (distance **0.75)
        logger.debug(f"move_mouse_with_curve: Step {i}, distance={distance:.2f}, delay={delay:.5f}")
        time.sleep(delay)

        mouse.position = (x,y)
        current_x, current_y = x,y
        logger.debug(f"move_mouse_with_curve: Step {i}, moved mouse to ({x}, {y}).")

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
  logger.debug(f"scroll_page: Scrolling by {scroll_amount} pixels.")
  driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
  delay = random.uniform(min_delay, max_delay)
  time.sleep(delay)
  logger.debug(f"scroll_page: Scrolled page by {scroll_amount}, Delay: {delay:.2f} seconds.")

#for random scrolling , emulating human browsing behavior
def scroll_random_times(driver, min_scrolls=3, max_scrolls=7, scroll_amount=500):
    """Scrolls the page a random number of times."""
    num_scrolls = random.randint(min_scrolls, max_scrolls)
    logger.debug(f"scroll_random_times: Scrolling page {num_scrolls} times.")
    for _ in range(num_scrolls):
        scroll_page(driver, scroll_amount)
    logger.debug("scroll_random_times: Scrolling Completed")

#To ensure reliable clicks using JavaScript as the main method and ActionChains as a fallback.
def click_element(driver, locator):
    """Clicks element using JavaScript click, and ActionChains as fallback"""
    logger.debug(f"click_element: Attempting to click element with locator: {locator}")
    try:
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(locator))
        logger.debug("click_element: Element located successfully. Attempting to click using Javascript")
        driver.execute_script("arguments[0].focus();", element) #Focus the element
        driver.execute_script("arguments[0].click();", element)
        logger.info("click_element: Element clicked using JavaScript click.")
    except Exception as e:
        logger.warning(f"click_element: JavaScript click failed: {e}. Attempting ActionChains click.")
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(locator))
            actions = ActionChains(driver)
            actions.move_to_element(element).click().perform()
            logger.info("click_element: Element clicked using ActionChains click.")
        except Exception as e:
            logger.error(f"click_element: ActionChains click failed: {e}", exc_info=True)


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
    link = driver.find_element(By.LINK_TEXT, "Social Networking")
    logger.debug("Found 'Social Networking' link.")

    # Get the location and size of the element
    location = link.location
    size = link.size
    logger.debug(f"Element location: {location}, size: {size}")

    # Calculate center coordinates of the link element
    target_x = location['x'] + size['width'] // 2
    target_y = location['y'] + size['height'] // 2
    logger.debug(f"Target click coordinates: ({target_x}, {target_y})")

     # Move the mouse using move_mouse_with_curve
    move_mouse_with_curve(target_x, target_y)

    # Click the link using Selenium's click method
    time.sleep(random.uniform(0.1, 0.3))
    
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