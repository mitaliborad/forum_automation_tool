import time
import logging
from datetime import datetime
import numpy as np
import os
import re
import gc
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from pynput.mouse import Button, Controller
import threading


# --- Automation Configuration ---
LOG_DIRECTORY = "Selenium-Logs"
AUTOMATION_WAIT_TIME = 100
MIN_SCROLLS = 3
MAX_SCROLLS = 7
SCROLL_AMOUNT = 500
SCROLL_DELAY = 2
MIN_LIKES = 1
MAX_LIKES = 3
MIN_SCROLLS_POSTS = 1
MAX_SCROLLS_POSTS = 5
SCROLL_DELAY_LIKES = 3
WRITE_DELAY = 3
BASE_SPEED = 0.001
SUB_FORUM_LIST_FILE = "Sub-Forum-List.txt"
VISITED_THREADS_FILE = "Thread_links.txt"
start_time = datetime.now()
run_duration = timedelta(hours=2) 


# Logger setup
def setup_logger(log_dir, profile_name, timestamp=None):
    """Sets up a logger with a unique file for each automation run and profile."""
    os.makedirs(log_dir, exist_ok=True)

    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    log_file = os.path.join(log_dir, f"{profile_name}_script_log_{timestamp}.log")

    logger = logging.getLogger(f"automation_{profile_name}_{timestamp}")  # Unique logger per run and profile
    logger.setLevel(logging.DEBUG)

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


# --- Mouse Movement Functions ---
class MouseMovement:
    def __init__(self):
        self.mouse = Controller()
        self.BASE_SPEED = 0.001

    def bezier_curve(self, p0, p1, p2, t):
        return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2

    def generate_bezier_path(self, start, end, num_points=50):
        #logger.debug(f"Generating Bezier path from {start} to {end} with {num_points} points.")
        control_point = (
            start[0] + random.randint(-100, 100),
            start[1] + random.randint(-100, 100),
        )
        #logger.debug(f"Control point: {control_point}")
        path = []
        for i in range(num_points):
            t = i / (num_points - 1)
            point = self.bezier_curve(
                np.array(start), np.array(control_point), np.array(end), t
            )
            path.append((int(point[0]), int(point[1])))
        #logger.debug(f"Generated Bezier path with {len(path)} points.")
        return path

    def move_mouse_with_curve(self, target_x, target_y, base_speed=0.001):
        #current_x, current_y = self.mouse.position
        #logger.debug(f"Moving mouse from ({current_x}, {current_y}) to ({target_x}, {target_y}).")
        path = self.generate_bezier_path((0, 0), (target_x, target_y))
        for x, y in path:
            speed = base_speed * random.uniform(0.8, 1.5)
            distance = np.sqrt((0 - x) ** 2 + (0 - y) ** 2)
            delay = speed * (distance ** 0.75)
            time.sleep(delay)
            self.mouse.position = (x, y)
            #current_x, current_y = x, y
            #logger.debug(f"Moved mouse to ({x}, {y}), delay: {delay:.4f}")
        #logger.info(
            #f"Successfully moved mouse to ({target_x}, {target_y}) using Bezier curve."
        