from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import random
import time
import logging
from datetime import datetime
import os
from pynput.mouse import Button, Controller
import numpy as np

# --- Configure Logging ---
def setup_logger(log_dir):
    """Sets up logging to a file and console."""
    os.makedirs(log_dir, exist_ok=True) # Creates the log directory if it doesn't exist
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # Creates a timestamp for the log file name
    log_file = os.path.join(log_dir, f"script_log_{timestamp}.log") # Creates the log file path

    logger = logging.getLogger(__name__) # Gets the logger object
    logger.setLevel(logging.DEBUG) # Sets the logging level to DEBUG

    file_handler = logging.FileHandler(log_file) # Creates a file handler to write logs to file
    file_handler.setLevel(logging.DEBUG) # Sets file handler level to DEBUG

    console_handler = logging.StreamHandler() # Creates a console handler to print logs to console
    console_handler.setLevel(logging.INFO) # Sets console handler level to INFO

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s') # Creates a log formatter
    file_handler.setFormatter(formatter) # Sets formatter for file handler
    console_handler.setFormatter(formatter) # Sets formatter for console handler

    logger.addHandler(file_handler) # Adds file handler to the logger
    logger.addHandler(console_handler) # Adds console handler to the logger

    return logger, log_file


log_directory = "selenium_logs1" # Sets log directory name
logger, log_file = setup_logger(log_directory) # Sets up logger and retrieves logger object and log file path
logger.info(f"Log file created at: {log_file}") # Logs the log file path

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
options = Options() #Creates Chrome Options object
options.add_argument('disable-infobars') # Disables info bars
options.add_experimental_option("excludeSwitches", ["enable-automation"]) #Excludes 'enable-automation' switch
options.add_experimental_option('useAutomationExtension', False) #Disables automation extension

user_data = r"C:\Users\DELL\AppData\Local\Google\Chrome\User Data" #Path for chrome user data
profile_name = "Profile 37" #Profile Name

options.add_argument(f"user-data-dir={user_data}") #Adds user-data-dir argument to options
logger.info(f"Starting Chrome with user data from: {user_data}") #Logs starting chrome with user data
driver = webdriver.Chrome(options=options) #Initiates the Chrome Driver
driver.get("https://www.blackhatworld.com/") #Navigates to URL
logger.info("Navigated to https://www.blackhatworld.com/") #Logs navigation

# --- Selenium Actions ---
try:

    # --- Human-like Scrolling Function ---
    def scroll(driver):
        """Scrolls the page down by a fixed amount a number of times"""
        logger.debug("Starting scrolling function...") # Logs starting scrolling
        for i in range(0,1): # Scrolls the page once
            logger.debug(f"Scrolling iteration: {i+1}") #Logs the scrolling iteration
            driver.execute_script("window.scrollBy(0,400);") #Scrolls the window
            time.sleep(random.uniform(1.5, 2)) #Pauses the execution for a random time
        logger.debug("Scrolling function completed.") #Logs when scrolling is done

    scroll(driver) #Runs the scroll method
    logger.info("Scrolling completed.") #Logs that the scroll is completed

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
    link.click() #Clicks the element using selenium
    logger.info("Clicked 'Social Networking' link using Selenium click.") #Logs that the click is completed

    # --- Human-like Scrolling Function ---
    def scroll_down(driver):
        """Scrolls down the page multiple times with delays"""
        logger.debug("Starting scrolling function...") #Logs scroll start
        time.sleep(random.uniform(2,3)) #Pauses the execution
        for i in range(-1,9): #Loops to scroll the page
            logger.debug(f"Scrolling iteration: {i+1}") #Logs scroll iteration
            driver.execute_script("window.scrollBy(0,700);") #Scrolls the page by the given amount
            time.sleep(random.uniform(1.5, 2)) #Pauses the execution
        logger.debug("Scrolling function completed.") #Logs scroll completion

    scroll_down(driver) #Runs the scroll_down method
    logger.info("Scrolling completed.") #Logs completion

    time.sleep(2) #Pauses execution
    logger.debug("Pausing 4 seconds before quitting driver...") #Logs pause before driver quit
    driver.quit() #Quits the driver
    logger.info("Driver quit successfully.") #Logs quit

except Exception as e:
    logger.error(f"An error occurred: {e}", exc_info=True) #Logs an error with exception details
    if 'driver' in locals():
        driver.quit() #Quits the driver in case of an exception