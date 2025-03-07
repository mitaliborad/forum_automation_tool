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

from gemini_api import GeminiHandler
from Multilogin_profiles import DarkCodeX_profile

# --- Automation Configuration ---  (Keep only Automation Configuration here)
LOG_DIRECTORY = "DarkCodeX_Logs"
AUTOMATION_WAIT_TIME = 1680
MIN_SCROLLS = 3
MAX_SCROLLS = 7
SCROLL_AMOUNT = 500
SCROLL_DELAY = 2
MIN_LIKES = 1
MAX_LIKES = 5
MIN_SCROLLS_POSTS = 1
MAX_SCROLLS_POSTS = 5
SCROLL_DELAY_LIKES = 3
WRITE_DELAY = 3
BASE_SPEED = 0.001
SUB_FORUM_LIST_FILE = "Sub-Forum-List.txt"
VISITED_THREADS_FILE = "Thread_links.txt"
start_time = datetime.now()
run_duration = timedelta(hours=2) 


# logger setup
def setup_logger(log_dir, timestamp=None):
    """Sets up a logger with a unique file for each automation run."""
    os.makedirs(log_dir, exist_ok=True)

    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    log_file = os.path.join(log_dir, f"script_log_{timestamp}.log")
    
    logger = logging.getLogger(f"automation_{timestamp}")  # Unique logger per run
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

# Initialize the logger at the module level
#logger, log_file = setup_logger(LOG_DIRECTORY)

# --- Mouse Movement Functions ---

mouse = Controller()

def bezier_curve(p0, p1, p2, t):
    return (1-t)**2 * p0 + 2*(1-t)*t*p1 + t**2*p2

def generate_bezier_path(start, end, num_points=50):
    logger.debug(f"Generating Bezier path from {start} to {end} with {num_points} points.")
    control_point = (
        start[0] + random.randint(-100, 100),
        start[1] + random.randint(-100, 100)
    )
    logger.debug(f"Control point: {control_point}")
    path = []
    for i in range(num_points):
        t = i / (num_points - 1)
        point = bezier_curve(np.array(start), np.array(control_point), np.array(end), t)
        path.append((int(point[0]), int(point[1])))
    logger.debug(f"Generated Bezier path with {len(path)} points.")
    return path

def move_mouse_with_curve(target_x, target_y, base_speed=BASE_SPEED):
    current_x, current_y = mouse.position
    logger.debug(f"Moving mouse from ({current_x}, {current_y}) to ({target_x}, {target_y}).")
    path = generate_bezier_path((current_x, current_y), (target_x, target_y))
    for x, y in path:
        speed = base_speed * random.uniform(0.8, 1.5)
        distance = np.sqrt((current_x - x)**2 + (current_y - y)**2)
        delay = speed * (distance **0.75)
        time.sleep(delay)
        mouse.position = (x, y)
        current_x, current_y = x, y
        logger.debug(f"Moved mouse to ({x}, {y}), delay: {delay:.4f}")
    logger.info(f"Successfully moved mouse to ({target_x}, {target_y}) using Bezier curve.")

# --- Helper Functions ---

#for import Sub-Forum-List.txt file
def get_subforum_list(file_path=SUB_FORUM_LIST_FILE):
    """Reads subforum URLs from the specified file."""
    try:
        with open(file_path, "r") as f:
            subforum_urls = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(subforum_urls)} subforum URLs from {file_path}")
        return subforum_urls
    except FileNotFoundError:
        logger.error(f"Subforum list file '{file_path}' not found.")
        return []
    except Exception as e:
        logger.error(f"Error reading subforum list file: {e}", exc_info=True)
        return []

# check visited thread from thread_links.txt
def load_visited_threads(file_path=VISITED_THREADS_FILE):
    """Loads the list of visited threads from the specified file."""
    try:
        with open(file_path, "r") as f:
            visited_threads = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(visited_threads)} visited threads from {file_path}")
        return set(visited_threads)  # Use a set for faster lookups
    except FileNotFoundError:
        logger.info(f"Visited threads file '{file_path}' not found. Starting with an empty list.")
        return set()
    except Exception as e:
        logger.error(f"Error reading visited threads file: {e}", exc_info=True)
        return set()

# save visited threads in Thread_links.txt
def save_visited_thread(thread_url, file_path=VISITED_THREADS_FILE):
    """Appends a thread URL to the list of visited threads."""
    try:
        with open(file_path, "a") as f:
            f.write(thread_url + "\n")
        logger.info(f"Saved thread URL '{thread_url}' to visited threads file '{file_path}'.")
    except Exception as e:
        logger.error(f"Error saving thread URL to visited threads file: {e}", exc_info=True)

# page scroll
def scroll_page(driver, scroll_amount=SCROLL_AMOUNT, min_delay=1, max_delay=2.0):
    logger.debug(f"Scrolling page by {scroll_amount} pixels.")
    try:
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    except Exception as e:
        logger.warning(f"Scrolling failed: {e}")
    time.sleep(random.uniform(min_delay, max_delay))
    logger.debug("Page scrolled.")

#page scroll for random times
def scroll_random_times(driver, min_scrolls=MIN_SCROLLS, max_scrolls=MAX_SCROLLS, scroll_amount=SCROLL_AMOUNT, scroll_delay=SCROLL_DELAY):
    num_scrolls = random.randint(min_scrolls, max_scrolls)
    logger.debug(f"Scrolling page {num_scrolls} times.")
    for _ in range(num_scrolls):
        scroll_page(driver, scroll_amount)
        time.sleep(scroll_delay)
    logger.debug("Random scrolls complete.")

#click on element using javascript and actionchains
def click_element(driver, locator):
    try:
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(locator))
        logger.debug(f"Element found, attempting to click using JavaScript: {locator}")
        driver.execute_script("arguments[0].focus();", element)
        driver.execute_script("arguments[0].click();", element)
        logger.info(f"Element clicked successfully using JavaScript: {locator}")
    except Exception as e:
        logger.warning(f"JavaScript click failed, attempting ActionChains: {e}")
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(locator))
            actions = ActionChains(driver)
            actions.move_to_element(element).click().perform()
            logger.info(f"Element clicked successfully using ActionChains: {locator}")
        except Exception as e:
            logger.error(f"Failed to click element after attempting ActionChains: {locator}. Error: {e}", exc_info=True)

#find element with scrolling the page
def find_element_with_scroll(driver, locator, max_scrolls=5):
    logger.debug(f"Attempting to find element with locator: {locator}")
    for i in range(max_scrolls):
        try:
            element = WebDriverWait(driver, 5).until(EC.presence_of_element_located(locator))
            logger.info(f"Element found after {i + 1} scrolls: {locator}")
            return element
        except:
            logger.debug(f"Element not found, scrolling page (attempt {i + 1}/{max_scrolls}).")
            scroll_page(driver, scroll_amount=400)
    logger.warning(f"Element not found after {max_scrolls} scrolls: {locator}")
    return None

#find like button, numbers of like buttons
def find_like_buttons(driver):
    try:
        like_buttons = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//bdi[contains(text(), 'Like')]"))
        )
        logger.debug(f"Found {len(like_buttons)} like buttons.")
        likes_length = len(like_buttons)
        return like_buttons, likes_length
    except Exception as e:
        logger.warning(f"Error finding like buttons: {e}", exc_info=True)
        return []

#click on like button
def click_like_button(driver, button, scroll_delay=2):
    try:
        driver.execute_script("arguments[0].scrollIntoView();", button)
        time.sleep(random.uniform(0.5, 1))
        logger.debug("Scrolling like button into view and attempting to click using JavaScript.")
        driver.execute_script("arguments[0].click();", button)
        logger.info("Like button clicked successfully using JavaScript.")
        return True
    except Exception as e:
        logger.warning(f"JavaScript click failed: {e}, attempting ActionChains.", exc_info=True)
        try:
            ActionChains(driver).move_to_element(button).click().perform()
            logger.info("Like button clicked successfully using ActionChains.")
            return True
        except Exception as e:
            logger.error(f"Failed to click like button after attempting ActionChains: {e}", exc_info=True)
            return False

# like random amount of post, at random time, like on random posts
def like_random_posts(driver, min_likes=MIN_LIKES, max_likes=MAX_LIKES, min_scrolls_posts=MIN_SCROLLS_POSTS, max_scrolls_posts=MAX_SCROLLS_POSTS, scroll_delay=SCROLL_DELAY_LIKES):
    try:
        scroll_random_times(driver, min_scrolls_posts, max_scrolls_posts, scroll_amount=500, scroll_delay=scroll_delay)
        like_buttons, likes_length = find_like_buttons(driver)

        if not like_buttons:
            logger.info("No like buttons found, skipping like_random_posts function...")
            return

        total_likes = random.randint(min_likes, max_likes)
        total_likes = min(total_likes, likes_length)

        liked_buttons = set()
        time.sleep(scroll_delay)
        logger.info(f"Attempting to like {total_likes} posts. There are {likes_length} available.")

        while len(liked_buttons) < total_likes:
            skip_interval = random.randint(2, 5)
            current_index = 0

            while current_index < len(like_buttons) and len(liked_buttons) < total_likes:
                try:
                    button = like_buttons[current_index]
                    if button not in liked_buttons and click_like_button(driver, button, scroll_delay):
                        liked_buttons.add(button)
                        logger.debug(f"Liked post number {len(liked_buttons)} of {total_likes}.")
                        time.sleep(random.uniform(4, 5))
                    current_index += skip_interval
                except Exception as e:
                    logger.error(f"Error clicking like button: {e}", exc_info=True)
                    break  # Prevent infinite loop

        logger.info(f"Liked {len(liked_buttons)} posts successfully.")
    except Exception as e:
        logger.error(f"Unexpected error in like_random_posts: {e}", exc_info=True)

    logger.info(f"Liked {len(liked_buttons)} posts successfully.")

# count comments
def count_main_post_comments(driver):
    try:
        # Locate the first post container
        first_post = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//article[@data-author][1]"))
        )

        # Find all reply buttons inside the first post only
        reply_buttons = first_post.find_elements(By.XPATH, ".//footer//a[contains(@class, 'actionBar-action--reply')]")

        # Count the number of reply buttons
        total_comments = len(reply_buttons)
        
        print(f"Total comments on the first post: {total_comments}")
        return total_comments

    except Exception as e:
        print(f"Error counting comments: {e}")
        return 0


# extract element text
def extract_element_text(element, xpath):
    try:
        element = WebDriverWait(element, 3).until(EC.presence_of_element_located((By.XPATH, xpath)))
        text = element.text.strip()
        logging.debug(f"Extracted text '{text}' from element with XPath: {xpath}")
        return text
    except Exception as e:
        logging.warning(f"Could not extract text from element with XPath: {xpath}. Error: {e}", exc_info=True)
        return "No text found"

# extract main post content
def extract_main_post_content(driver):
    try:
        main_post_locator = (By.XPATH, '//div[@data-lb-id and contains(@data-lb-id, "post-")]')
        logger.debug(f"Attempting to locate main post element with locator: {main_post_locator}")
        main_post_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(main_post_locator)
        )
        main_post_text = main_post_element.text.strip()
        logger.debug(f"Extracted main post content: {main_post_text}")
        return main_post_text
    except Exception as e:
        logger.warning(f"Could not extract main post content. Error: {e}", exc_info=True)
        return None

# extract post content
def extract_post_content(driver, output_file):
    try:
        posts_locator = (By.CSS_SELECTOR, 'article[data-author]')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(posts_locator))
        all_posts_elements = driver.find_elements(*posts_locator)

        with open(output_file, 'w', encoding='utf-8') as file:
            try:
                main_post_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//h1'))
                )
                main_post = main_post_element.text.strip()
                file.write(f"--- Main Post Title ---\n{main_post}\n\n")
                logging.debug(f"Main Post Title: {main_post}")
            except Exception as e:
                file.write(f"--- Main Post Title ---\nNo main post title found\n\n")
                logging.warning(f"No main post title found. Error: {e}", exc_info=True)
            
            try:
                all_comments = driver.find_elements(By.XPATH, "//footer//a[contains(@class, 'actionBar-action--reply')]")
                total_comments = len(all_comments)
                logger.debug(f"Total comments in the thread: {total_comments}")
                file.write(f"Total comments in the thread: {total_comments}\n\n")
            except Exception as e:
                logger.warning(f"Could not count total comments: {e}", exc_info=True)
                file.write("Total comments: 0\n\n")

            first_post = True

            for post_element in all_posts_elements:
                try:
                    link_element = post_element.find_element(By.XPATH, ".//div[@data-lb-id]")
                    post_id = link_element.get_attribute("data-lb-id")
                    logging.info(f"Processing post with ID: {post_id}")
                except Exception as e:
                    post_id = "No ID Found"
                    logging.error(f"Could not extract post ID. Error: {e}", exc_info=True)

                topic_username = extract_element_text(post_element, ".//h4//a//span")
                file.write(f"Topic User: {topic_username}\n")
                logging.debug(f"Topic User: {topic_username}")

                topic_locator = ".//div[@class='message-content js-messageContent']"
                topic = extract_element_text(post_element, topic_locator)
                file.write(f"Topic: {topic}\n")
                logging.debug(f"Topic: {topic}")

                try:
                    like_user_locator = ".//a[@data-xf-click='overlay'][bdi]"
                    like_user_element = WebDriverWait(post_element, 3).until(EC.presence_of_element_located((By.XPATH, like_user_locator)))
                    like_user_text = like_user_element.text.strip()

                    parts = re.split(r", | and ", like_user_text)
                    other_count = 0
                    if parts and "others" in parts[-1]:
                        try:
                            other_count = int(re.search(r'(\d+)', parts[-1]).group(1))
                            parts = parts[:-1]
                        except:
                            other_count = 0

                    like_users = [user.strip() for user in parts if user.strip()]
                    like_count = len(like_users) + other_count

                    file.write(f"Liked by: {like_user_text}\n")
                    file.write(f"Number of likes: {like_count}\n")
                    logging.debug(f"Liked by: {like_user_text}")
                    logging.debug(f"Number of likes: {like_count}")
                except Exception as e:
                    file.write("Liked by: No user likes\n")
                    file.write("Number of likes: 0\n")
                    logging.debug(f"No user likes were found: {e}", exc_info=True)

                file.write("-----\n\n")  # Separator after each post                
                file.write("Replies:\n\n\n")

    except Exception as e:
        logging.critical(f"General error in extract_post_content: {e}", exc_info=True)


# read thread content 
def read_thread_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        logger.error(f"Thread content file '{file_path}' not found.")
        return None
    except Exception as e:
        logger.error(f"Error reading thread content file: {e}", exc_info=True)
        return None

# API generates and save comments in txt file
def generate_and_save_comments(thread_content, output_file):
    try:
        gemini_handler = GeminiHandler()
        comments = gemini_handler.get_comments(thread_content,prompt_file="prompt.txt")

        if comments:
            logger.info("Successfully generated comments using Gemini API.")
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(comments)
                logger.info(f"Comment saved to '{output_file}'.")
                return comments
            
            except Exception as e:
                logger.error(f"Error saving comment to file: {e}", exc_info=True)
                return None
        else:
            logger.warning("Failed to generate comment using Gemini API.")
            return None

    except Exception as e:
        logger.error(f"Error occurred while generating comment: {e}", exc_info=True)
        return None

# write and post comment
def post_comment(driver, comment,write_delay=WRITE_DELAY):
    if not comment:
        logger.warning("No comment to post.")
        return False

    try:
        write_comment_locator = (By.XPATH,"//span[contains(text(), 'Write your reply...')]")
        logger.debug(f"Searching for text box with locator: {write_comment_locator}")
        write_comment = find_element_with_scroll(driver,write_comment_locator)

        post_reply = driver.find_element(By.XPATH,"//span[contains(text(),'Post reply')]")
        if write_comment:

            try:
                element = WebDriverWait(driver,10).until(EC.element_to_be_clickable(write_comment_locator))
                logger.debug(f"Text box is clickable using element_to_be_clickable with locator : {write_comment_locator}")
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                logger.debug("Text box scrolled into view")
                time.sleep(random.uniform(0.5,1))

                logger.debug("Initializing actionchains")
                actions = ActionChains(driver)

                location = post_reply.location
                size = post_reply.size
                logger.debug(f"Post reply Element location: {location}, size: {size}")

                target_x = location['x'] + size['width'] // 2
                target_y = location['y'] + size['height'] // 2
                logger.debug(f"Target click coordinates: ({target_x}, {target_y})")

                move_mouse_with_curve(target_x, target_y)
                logger.debug("Moved mouse to target location using bezier curve.")

                actions.move_to_element(element)
                logger.debug("Moving mouse to text box element.")

                actions.click()
                logger.debug("Clicking on the text box.")

                actions.send_keys(comment)
                logger.debug(f"Sending keys with content: {comment}")

                time.sleep(random.uniform(2,3))
                time.sleep(write_delay)
                actions.click(post_reply)
                logger.debug(f"Clicking on post reply button.")

                actions.perform()
                logger.debug("Performed Actionchains")
                logger.info("Successfully wrote into text box using ActionChains and click.")

                time.sleep(4)

            except Exception as e:
                logger.error(f"Error posting comment: {e}", exc_info=True)
                return False
            
    except Exception as e:
            logger.error("if comment closed then you should close the browser")
            try:
                block_comment_locator = (By.XPATH,'//div//dl[@class="blockStatus"]//dd')
                logger.debug(f"Searching for text with locator: {block_comment_locator}")
                block_comment = find_element_with_scroll(driver,block_comment_locator)
                if block_comment:
                   driver.quit()
                else:
                    print("no driver found")
            except Exception as e:
                print(e)

# extract thread title
def get_thread_title(driver):

    try:
        title_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div//h1')))
        thread_title = title_element.text.strip()
        thread_title = re.sub(r'[\\/*?:"<>|]', "", thread_title)
        logger.info(f"Extracted thread title: {thread_title}")
        return thread_title
    
    except Exception as e:
        logger.warning(f"Could not extract thread title. Error: {e}", exc_info=True)
        return "Untitled Thread"

# clear memory after automation
def clear_memory():
    logger.info("Attempting to clear memory and resources.")
    gc.collect()
    logger.info("Garbage collection completed.")

# find random thread link from Sub-Forum-link
def find_random_thread_link_from_subforum(driver, subforum_url,visited_threads):
    """Navigates to a subforum and finds a random thread link."""
    try:
        driver.get(subforum_url)
        logger.info(f"Navigated to subforum: {subforum_url}")

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'structItem')]")))
        all_threads = driver.find_elements(By.XPATH, "//div[contains(@class, 'structItem')]")
        unvisited_threads = []
        for thread in all_threads:
            try:
                
                sticky_span = thread.find_elements(By.XPATH, ".//span[contains(@class, 'sticky-thread--hightlighted')]")

                # Skip if the span exists, indicating it's a sticky thread
                if sticky_span:
                    continue

                title_elements = thread.find_elements(By.XPATH, ".//div[contains(@class, 'structItem-title')]//a")
                
                if title_elements:
                    href = title_elements[0].get_attribute("href")
                    if href not in visited_threads:
                        unvisited_threads.append(title_elements[0])

            except Exception as e:
                print(f"Skipping a thread due to error: {e}")

        if not unvisited_threads:
            logger.warning(f"No unvisited thread links found in subforum: {subforum_url}")
            return None

        random_link = random.choice(unvisited_threads)
        href = random_link.get_attribute("href")
        logger.info(f"Selected random thread link: {href}")
        return href

    except Exception as e:
        logger.error(f"Error finding random thread link in subforum: {e}", exc_info=True)
        return None

    
# after automation it navigate home page 
def navigate_home(driver):
    """Navigates the driver back to the main BHW homepage."""
    try:
         driver.get("https://www.blackhatworld.com/")
         logger.info("Navigated back to the homepage.")
         time.sleep(random.uniform(2, 3))  # Short delay to ensure page load
    except Exception as e:
         logger.error(f"Failed to navigate back to the homepage: {e}", exc_info=True)


# --- Main Execution Loop ---

if __name__ == "__main__":

    logger, log_file = setup_logger(LOG_DIRECTORY)

    #find directories
    thread_details_dir = "Thread-Details"
    thread_content_dir = os.path.join(thread_details_dir, "Thread Content")
    api_comments_dir = os.path.join(thread_details_dir, "API Comments")

    token = None  # Initialize token outside the loop
    driver = None
    is_profile_active = False # Add a status flag
    
    try:
        # MultiLogin Authentication and Profile Start (DO THIS ONLY ONCE!)
        token = DarkCodeX_profile.signin(logger)  # Pass logger
        if not token:
            logger.critical("Failed to sign in to MultiLogin.  Exiting.")
            exit()  # Exit completely if login fails

        driver = DarkCodeX_profile.start_profile(token, logger)  # Pass logger
        if not driver:
            logger.critical("Failed to start MultiLogin profile. Exiting.")
            exit()  # Exit completely if starting profile fails

        is_profile_active = True  # Set flag

        while True:
            # Set up new log location for each task
            if datetime.now() - start_time > run_duration:
                logger.info("Automation has reached the time limit. Stopping execution.")
                break            
             # Generate a new timestamp for each automation run
            automation_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            #logger, log_file = setup_logger(LOG_DIRECTORY, automation_timestamp)
            logger.info(f"Starting new automation task. Log file created at: {log_file}")


            try:

                subforum_urls = get_subforum_list()
                if not subforum_urls:
                    logger.critical("No subforum URLs found in the file. Exiting.")
                    exit()
                
                visited_threads = load_visited_threads()  # Load visited threads at the start
                if visited_threads:
                    logger.info(f"Successfully loaded links that was already visited!")

                scroll_random_times(driver)

                # Select and navigate a random thread to specific subforum
                subforum_url = random.choice(subforum_urls)
                scroll_random_times(driver)
                thread_link = find_random_thread_link_from_subforum(driver, subforum_url,visited_threads)

                if thread_link:
                    time.sleep(random.uniform(2, 3))
                    driver.get(thread_link)
                    time.sleep(random.uniform(2, 3))
                    logger.info(f"Navigated to random thread: {thread_link}")
                    visited_threads.add(thread_link)
                    save_visited_thread(thread_link)
                else:
                    logger.warning("Skipping thread processing due to no thread link being found in subforum.")
                    continue #Skip to next subforum

                # Extract thread title
                thread_title = get_thread_title(driver)

                scroll_random_times(driver, min_scrolls=2, max_scrolls=4, scroll_delay=2)
                time.sleep(random.uniform(2, 3))

                like_random_posts(driver, min_likes=1, max_likes=4, min_scrolls_posts=1, max_scrolls_posts=4, scroll_delay=3)

                scroll_random_times(driver, min_scrolls=3, max_scrolls=7, scroll_delay=3)
                time.sleep(random.uniform(2, 3))

                # save thread content
                thread_content_file = os.path.join(thread_content_dir, f"{thread_title}.txt")
                extract_post_content(driver, thread_content_file)
                logger.info(f"Post content extracted and saved to {thread_content_file}")
                time.sleep(random.uniform(2, 3))

                main_post_content = extract_main_post_content(driver)
                time.sleep(random.uniform(2, 3))

                #generate and save comment
                if main_post_content:
                    comment = generate_and_save_comments(main_post_content, os.path.join(api_comments_dir, "temp_comment.txt"))
                    if comment:
                        sanitized_comment = re.sub(r'[\\/*?:"<>|]', "", comment[:50])
                        api_comment_file = os.path.join(api_comments_dir, f"{thread_title}_{sanitized_comment}.txt")
                        try:
                            os.rename(os.path.join(api_comments_dir, "temp_comment.txt"), api_comment_file)
                        except Exception as e:
                            logger.warning(f"rename Error: {e}", exc_info=True)
                        logger.info(f"API comment generated and saved to {api_comment_file}")
                    else:
                        logger.warning("Failed to generate comment, skipping saving.")

                # Read the generated comment
                comment_file = os.path.join(api_comments_dir, f"{thread_title}_{sanitized_comment}.txt")
                comment = read_thread_content(comment_file)
                time.sleep(random.uniform(2, 3))

                if comment:
                    post_comment(driver, comment, write_delay=3)
                    logger.info("Comment posted successfully.")
                else:
                    logger.warning("No comment available to post.")

                logger.info("Task Completed!!")
                # 1.5) Added code to go back to HOME

                # navigate back to home after automation
                navigate_home(driver)

            except Exception as e:
                logger.error(f"An error occurred: {e}", exc_info=True)

            # clear the memory and wait from next automation
            clear_memory()
            logger.info(f"Waiting for {AUTOMATION_WAIT_TIME} seconds before next execution.")
            time.sleep(AUTOMATION_WAIT_TIME)

    except Exception as e:
            logger.critical(f"An unrecoverable error occurred: {e}", exc_info=True)

    finally:  
        if driver:
            try:
                logger.info("Quitting browser driver...")
                driver.quit()
                time.sleep(5)  # Ensure the browser fully closes
                logger.info("Browser closed successfully.")
            except Exception as e:
                logger.warning(f"Error while quitting driver: {e}", exc_info=True)

        if token and is_profile_active:  # Check if the profile is active.
            try:
                logger.info("Stopping MultiLogin profile...")
                time.sleep(3)  # Add a short delay before stopping profile
                DarkCodeX_profile.stop_profile(token, logger)
                is_profile_active = False # Reset the Flag
            except Exception as e:
                logger.warning(f"Error while stopping MultiLogin profile: {e}", exc_info=True)