from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
time.sleep(random.uniform(0.5,1))

logger.info("Navigated to https://www.blackhatworld.com/")

# --- Helper Functions ---

# To mimic human-like scrolling behavior by scrolling a set amount and having a short delay before continuing.
def scroll_page(driver, scroll_amount=500, min_delay=1, max_delay=2.0):
  """Scrolls the page a single time with a random delay for simulating user-like behavior."""
  logger.debug(f"scroll_page: Scrolling by {scroll_amount} pixels.")
  driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
  delay = random.uniform(min_delay, max_delay)
  time.sleep(delay)
  logger.debug(f"scroll_page: Scrolled page by {scroll_amount}, Delay: {delay:.2f} seconds.")

#for random scrolling , emulating human browsing behavior
def scroll_random_times(driver, min_scrolls=3, max_scrolls=7, scroll_amount=500, scroll_delay=2):
    """Scrolls the page a random number of times."""
    num_scrolls = random.randint(min_scrolls, max_scrolls)
    logger.debug(f"scroll_random_times: Scrolling page {num_scrolls} times.")
    for _ in range(num_scrolls):
        scroll_page(driver, scroll_amount)
        time.sleep(scroll_delay)
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


#for page scroll with find element and count how many scrolls
def find_element_with_scroll(driver, locator, max_scrolls=5):
    """Find an element after random scrolls, or returns None if not found."""
    logger.debug(f"find_element_with_scroll: Searching for element with locator: {locator}")
    for i in range(max_scrolls):
        try:
            element = WebDriverWait(driver, 5).until(EC.presence_of_element_located(locator))
            logger.info(f"find_element_with_scroll: Element found after {i + 1} scrolls.")
            return element
        except:
             scroll_page(driver, scroll_amount=400)
    logger.warning(f"find_element_with_scroll: Element not found after {max_scrolls} scrolls.")
    return None

# for locate like buttons that are currently visible on a webpage.
def find_like_buttons(driver):
    """Finds all like buttons currently visible on the page using more specific CSS."""
    
    try:
        like_buttons = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//bdi[contains(text(), 'Like')]"))
        )
        logger.debug(f"find_like_buttons: Found {len(like_buttons)} like buttons.")
        return like_buttons
    except Exception as e:
         logger.warning(f"find_like_buttons: Error finding like buttons: {e}")
         return []

#  for clicking a specific "Like" button element on a web page.
def click_like_button(driver,button, scroll_delay=2):
    """Clicks the given like button using JavaScript first, then ActionChains as a backup."""
    try:
        driver.execute_script("arguments[0].scrollIntoView();", button)
        time.sleep(random.uniform(0.5, 1))
        time.sleep(scroll_delay)
        driver.execute_script("arguments[0].click();", button)
        logger.info("Liked a post using JavaScript.")
        return True
    except:
        try:
            ActionChains(driver).move_to_element(button).click().perform()
            logger.info("Liked a post using ActionChains.")
            return True
        except:
            logger.warning("Failed to click like button.")
            return False

#The like_random_posts function simulates a user scrolling through a page and liking a random number of posts. It handles finding like buttons, scrolling between posts, and ensuring posts are only liked once.
def like_random_posts(driver, min_likes=2, max_likes=6, min_scrolls_posts=1, max_scrolls_posts=4, scroll_delay=2):
    """Scrolls and likes a random number of posts."""
    liked_buttons = set()
    total_likes = random.randint(min_likes,max_likes)
    time.sleep(scroll_delay)
    logger.info(f"Attempting to like {total_likes} posts.")

    while len(liked_buttons) < total_likes:
        scroll_random_times(driver, min_scrolls_posts, max_scrolls_posts, scroll_amount=500,scroll_delay=scroll_delay)
        like_buttons = find_like_buttons(driver)

        if not like_buttons:
            logger.info("No like buttons found, scrolling again...")
            continue

        # Randomly select a subset of posts
        num_buttons = len(like_buttons)
        if num_buttons == 0:
            continue  # Skip if no like buttons are found

        
        skip_interval = random.randint(2, 5)  # Random interval to skip
        current_index = 0

        while current_index < num_buttons and len(liked_buttons) < total_likes:
             button = like_buttons[current_index]
             
             if button not in liked_buttons and click_like_button(driver,button,scroll_delay):
                  liked_buttons.add(button)
                  time.sleep(random.uniform(4,5))  # Random delay between likes
             current_index+=skip_interval

    logger.debug("Completed like_random_post function.")


# --- Selenium Actions ---
try:
    # Initial Scroll
    logger.debug("Starting initial random scrolls...")
    scroll_random_times(driver)
    logger.info("Initial random scroll completed.")

    # Locate the "Social Networking" Link
    link_locator = (By.LINK_TEXT, "Social Networking")
    logger.debug(f"Locating 'Social Networking' Link with locator: {link_locator}")
    
    #Scroll the element into view
    element = WebDriverWait(driver,10).until(EC.presence_of_element_located(link_locator))
    logger.debug("Element located with EC.presence_of_element_located()")
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
    logger.debug("Moved mouse to target location using bezier curve.")

    # Click the link using Selenium's click method
    time.sleep(random.uniform(0.1, 0.3))
    logger.debug("pause before click")
    
    #Click the element
    click_element(driver, link_locator)
    logger.info("Clicked 'Social Networking' link")
    time.sleep(random.uniform(1.5, 2))
    logger.debug("pause before find instagram link")

    # Find Instagram Link after scrolling
    instagram_locator = (By.LINK_TEXT, "Instagram")
    logger.debug(f"Searching for Instagram link with locator: {instagram_locator}")
    instagram_link = find_element_with_scroll(driver, instagram_locator)

    if instagram_link:
        # Get the location and size of the element
        location = instagram_link.location
        size = instagram_link.size
        logger.debug(f"Instagram element location: {location}, size: {size}")

        # Calculate center coordinates of the link element
        target_x = location['x'] + size['width'] // 2
        target_y = location['y'] + size['height'] // 2
        logger.debug(f"Target click coordinates for Instagram link: ({target_x}, {target_y})")

        # Move mouse and click Instagram link
        move_mouse_with_curve(target_x, target_y)
        logger.debug("Moved mouse to Instagram link location using bezier curve")
        time.sleep(random.uniform(0.1, 0.3))
        logger.debug("pause after mouse movement and then click on instagram link")
        click_element(driver,instagram_locator)
        logger.info("Clicked on Instagram Link")

    else:
        logger.warning("Instagram link not found, skipping click.")
    time.sleep(random.uniform(2,3))
    logger.debug("pause before scroll (like read)")

    
    
    # Scroll and Find the Question "AI model for Instagram"
    logger.debug("Scrolling to find the question...")
    scroll_random_times(driver, min_scrolls=1, max_scrolls=4)
    time.sleep(random.uniform(1.5,2))
    logger.debug("pause before click and after scroll")
    question_locator = (By.XPATH, "//a[contains(text(), 'AI model for Instagram')]")
    logger.debug(f"Searching for the question with locator : {question_locator}")
    question_link = find_element_with_scroll(driver,question_locator)
    
        
    time.sleep(random.uniform(2,3))
    logger.debug("pause before click")    
    click_element(driver, question_locator)
    logger.info("Clicked on the Question Link")
    time.sleep(random.uniform(2.5,3))
    logger.debug("pause before scroll(like read)")
    
    # like random posts
    time.sleep(random.uniform(2,3))
    like_random_posts(driver, min_likes=2, max_likes=6, min_scrolls_posts=1, max_scrolls_posts=3, scroll_delay=2)
    
    time.sleep(4)
    logger.debug("Pausing before quitting driver...")
    driver.quit()
    logger.info("Driver quit successfully.")
except Exception as e:
    logger.error(f"An error occurred: {e}")