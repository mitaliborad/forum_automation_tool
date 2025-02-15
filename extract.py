# blackhatworld-automation.py
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
import re  # Import the regular expression module

# Import Gemini API handler
from gemini_api import GeminiHandler

# --- Configure Logging ---
def setup_logger(log_dir):
    """Sets up a logger to write to a file and the console."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"script_log_{timestamp}.log")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Set the logger's level to DEBUG to capture all messages

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # File handler level

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) # Console handler level

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

def bezier_curve(p0, p1, p2, t):
    """Calculates a point on a Bezier curve."""
    return (1-t)**2 * p0 + 2*(1-t)*t*p1 + t**2*p2

def generate_bezier_path(start, end, num_points=50):
    """Generates a path of points following a Bezier curve."""
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

def move_mouse_with_curve(target_x, target_y, base_speed=0.001):
    """Moves the mouse along a Bezier curve to the target coordinates."""
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
        logger.debug(f"Moved mouse to ({x}, {y}), delay: {delay:.4f}")  # Log each intermediate position
    logger.info(f"Successfully moved mouse to ({target_x}, {target_y}) using Bezier curve.")

# --- Selenium Setup ---
opt = Options()
opt.add_experimental_option("debuggerAddress","localhost:9222")

driver = webdriver.Chrome(options=opt)
logger.debug("Chrome driver initialized.")
driver.get("https://www.blackhatworld.com/")
logger.debug("Navigating to URL.")
time.sleep(random.uniform(0.5, 1))

logger.info("Navigated to https://www.blackhatworld.com/")

# --- Helper Functions ---
def scroll_page(driver, scroll_amount=500, min_delay=1, max_delay=2.0):
    """Scrolls the page by a specified amount."""
    logger.debug(f"Scrolling page by {scroll_amount} pixels.")
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    time.sleep(random.uniform(min_delay, max_delay))
    logger.debug("Page scrolled.")

def scroll_random_times(driver, min_scrolls=3, max_scrolls=7, scroll_amount=500, scroll_delay=2):
    """Scrolls the page a random number of times within a range."""
    num_scrolls = random.randint(min_scrolls, max_scrolls)
    logger.debug(f"Scrolling page {num_scrolls} times.")
    for _ in range(num_scrolls):
        scroll_page(driver, scroll_amount)
        time.sleep(scroll_delay)
    logger.debug("Random scrolls complete.")

def click_element(driver, locator):
    """Clicks an element using JavaScript and ActionChains as fallback."""
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

def find_element_with_scroll(driver, locator, max_scrolls=5):
    """Finds an element after scrolling the page a maximum number of times."""
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

def find_like_buttons(driver):
    """Finds all 'Like' buttons on the page."""
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

def click_like_button(driver, button, scroll_delay=2):
    """Clicks a like button using JavaScript and ActionChains as fallback."""
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


def like_random_posts(driver, min_likes=1, max_likes=4, min_scrolls_posts=1, max_scrolls_posts=5, scroll_delay=3):
    """Likes a random number of posts after scrolling randomly."""

    scroll_random_times(driver, min_scrolls_posts, max_scrolls_posts, scroll_amount=500, scroll_delay=scroll_delay)
    like_buttons, likes_length = find_like_buttons(driver) # Get the like buttons list and length

    if not like_buttons:
        logger.info("No like buttons found, skipping like_random_posts function...")
        return # Exit if no buttons found

    total_likes = random.randint(min_likes, max_likes)

    # Ensure we dont try to like more than available
    total_likes = min(total_likes, likes_length)

    liked_buttons = set()  # Tracks which buttons have already been liked (to avoid duplicates)
    time.sleep(scroll_delay)
    logger.info(f"Attempting to like {total_likes} posts. There are {likes_length} available.")

    while len(liked_buttons) < total_likes:
        skip_interval = random.randint(2, 5) # Randomly skip some buttons
        current_index = 0

        while current_index < len(like_buttons) and len(liked_buttons) < total_likes:
            button = like_buttons[current_index]
            if button not in liked_buttons and click_like_button(driver, button, scroll_delay):
                liked_buttons.add(button)
                logger.debug(f"Liked post number {len(liked_buttons)} of {total_likes}.")
                time.sleep(random.uniform(4, 5))
            current_index += skip_interval

    logger.info(f"Liked {len(liked_buttons)} posts successfully.")

def extract_element_text(element, xpath):
    """Extracts text from an element, handling potential exceptions."""
    try:
        element = WebDriverWait(element, 3).until(EC.presence_of_element_located((By.XPATH, xpath)))
        text = element.text.strip()
        logging.debug(f"Extracted text '{text}' from element with XPath: {xpath}") #Log all elements with debug
        return text
    except Exception as e:
        logging.warning(f"Could not extract text from element with XPath: {xpath}. Error: {e}", exc_info=True) #Added exc_info
        return "No text found"

def extract_main_post_content(driver):
    """Extracts only the main post content from the thread."""
    try:
        # Locate the main post element.
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

def extract_post_content(driver, output_file):
    """Extracts, processes, and saves post content and replies to a file."""
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


            for post_element in all_posts_elements:
                try:
                    # Find the <a> tag with the data-lb-id attribute within the post_element
                    link_element = post_element.find_element(By.XPATH, ".//div[@data-lb-id]")
                    post_id = link_element.get_attribute("data-lb-id")
                    logging.info(f"Processing post with ID: {post_id}") #Log the post Id's as they proccess
                    # print(f"Processing post with ID: {post_id} - Error: {e}")
                except Exception as e:
                    post_id = "No ID Found"
                    logging.error(f"Could not extract post ID. Error: {e}", exc_info=True) #Added exc_info
                    # print(f"Processing post with ID: {post_id} - Error: {e}")

                # --- Topic Username ---
                topic_username = extract_element_text(post_element, ".//h4//a//span")
                file.write(f"Topic User: {topic_username}\n")
                logging.debug(f"Topic User: {topic_username}")

                # --- Topic Text ---
                #New Locator
                topic_locator = ".//div[@class='message-content js-messageContent']"
                topic = extract_element_text(post_element, topic_locator)
                file.write(f"Topic: {topic}\n")
                logging.debug(f"Topic: {topic}")
                 # ---likes count---
                try:
                    #New Locator
                    like_user_locator = ".//a[@data-xf-click='overlay'][bdi]"
                    like_user_element = WebDriverWait(post_element, 3).until(EC.presence_of_element_located((By.XPATH, like_user_locator)))
                    like_user_text = like_user_element.text.strip()

                    # Split by commas and "and" to separate usernames and the "and X others" part.
                    parts = re.split(r", | and ", like_user_text)

                    # Extract the number of "others" if it exists
                    other_count = 0
                    if parts and "others" in parts[-1]:
                        try:
                            other_count = int(re.search(r'(\d+)', parts[-1]).group(1))
                            parts = parts[:-1]  # Remove the "and X others" part
                        except:
                            other_count = 0  # Handle the case where the number is not an integer

                    # Clean up the usernames by stripping whitespace and removing empty strings
                    like_users = [user.strip() for user in parts if user.strip()]

                    # Calculate the total like count
                    like_count = len(like_users) + other_count

                    file.write(f"Liked by: {like_user_text}\n")
                    file.write(f"Number of likes: {like_count}\n")
                    logging.debug(f"Liked by: {like_user_text}")
                    logging.debug(f"Number of likes: {like_count}")
                except Exception as e:
                    file.write("Liked by: No user likes\n")
                    file.write("Number of likes: 0\n")
                    logging.debug(f"No user likes were found: {e}", exc_info=True) #Added exception


                # --- Extract Number of comments ONLY for Main Post & Structure Replies ---
                if post_id == driver.find_element(By.XPATH, "//div[@data-lb-id and contains(@data-lb-id, 'post-')]").get_attribute("data-lb-id"):
                    try:
                        comments_elements = post_element.find_elements(By.XPATH, ".//a[text()='Click to expand...']")
                        num_comments = len(comments_elements)

                        file.write(f"Number of comments: {num_comments}\n")
                        logging.debug(f"Number of comments: {num_comments}")

                    except Exception as e:
                        file.write("Number of comments: 0\n")
                        logging.debug(f"No reply was found: {e}", exc_info=True)
                else:
                  file.write("Number of comments: 0 (Reply Post)\n")  # Indicate it's a reply post
                  logging.debug("Number of comments: 0 (Reply Post)")

                # Structure Replies
                file.write("-----\n\n")
                file.write("Replies:\n\n\n")



    except Exception as e:
        logging.critical(f"General error in extract_post_content: {e}", exc_info=True)  #Critical Error

def read_thread_content(file_path):
    """Reads thread content from a text file."""
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

def generate_and_save_comments(thread_content, output_file):
    """Generates comments using the Gemini API and saves them to a text file."""
    try:
        gemini_handler = GeminiHandler()
        # Generate comments to one comment only.
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
        logger.error(f"An error occurred while generating comment: {e}", exc_info=True)
        return None

def post_comment(driver, comment,write_delay=3):
    """Posts the comment to the BHW thread."""
    if not comment:
        logger.warning("No comment to post.")
        return False


    try:
        # 1. Find the comment input box.
        write_comment_locator = (By.XPATH,"//span[contains(text(), 'Write your reply...')]")
        logger.debug(f"Searching for text box with locator: {write_comment_locator}")
        write_comment = find_element_with_scroll(driver,write_comment_locator)

        # 2. find post_reply button
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

                 # Get the location and size of the post_reply button
                location = post_reply.location
                size = post_reply.size
                logger.debug(f"Post reply Element location: {location}, size: {size}")

                # Calculate center coordinates of the button
                target_x = location['x'] + size['width'] // 2
                target_y = location['y'] + size['height'] // 2
                logger.debug(f"Target click coordinates: ({target_x}, {target_y})")

                 # Move the mouse using move_mouse_with_curve
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
           logger.error(f"Error interacting with the text box: {e}")

def find_random_thread_link(driver):
    """Finds a random thread link on the current page."""
    try:
        # Adjust this XPath to find relevant thread links on BHW
        thread_links = driver.find_elements(By.XPATH, '//div[@class="structItemContainer"]//div[@class="structItem-title"]//a[@href]')  # Generic thread link

        if not thread_links:
            logger.warning("No thread links found on the page.")
            return None

        random_link = random.choice(thread_links)
        href = random_link.get_attribute("href")

        # Get the location and size of the element
        location = random_link.location
        size = random_link.size
        logger.debug(f"Element location: {location}, size: {size}")

        # Calculate center coordinates of the link element
        target_x = location['x'] + size['width'] // 2
        target_y = location['y'] + size['height'] // 2
        logger.debug(f"Target click coordinates: ({target_x}, {target_y})")

         # Move the mouse using move_mouse_with_curve
        move_mouse_with_curve(target_x, target_y)
        logger.debug("Moved mouse to target location using bezier curve.")
        
        logger.info(f"Selected random thread link: {href}")
        return href
    except Exception as e:
        logger.error(f"Error finding random thread link: {e}", exc_info=True)
        return None

def get_thread_title(driver):
    """Extracts the thread title from the page."""
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div//h1'))
        )
        thread_title = title_element.text.strip()
        # Sanitize the title to remove invalid characters for filenames
        thread_title = re.sub(r'[\\/*?:"<>|]', "", thread_title)
        logger.info(f"Extracted thread title: {thread_title}")
        return thread_title
    except Exception as e:
        logger.warning(f"Could not extract thread title. Error: {e}", exc_info=True)
        return "Untitled Thread"

# --- Selenium Actions ---
try:

    # 1. Define the base directories
    thread_details_dir = "Thread-Details"
    thread_content_dir = os.path.join(thread_details_dir, "Thread Content")
    api_comments_dir = os.path.join(thread_details_dir, "API Comments")

    # 2. scroll random times
    scroll_random_times(driver)

    # 3. Navigate to a random thread
    thread_link = find_random_thread_link(driver)
    
    if thread_link:
        time.sleep(random.uniform(2, 3))
        driver.get(thread_link)
        time.sleep(random.uniform(2, 3))
        logger.info(f"Navigated to random thread: {thread_link}")
    else:
        logger.warning("Skipping thread processing due to no thread link being found.")
        driver.quit()  # Or handle the situation differently
        exit()  # Stop further execution

    # 4. Extract thread title
    thread_title = get_thread_title(driver)

    # 5. scroll random after click on the link
    scroll_random_times(driver, min_scrolls=2, max_scrolls=4, scroll_delay=2)
    time.sleep(random.uniform(2, 3))

    # 6. like_random posts, random times
    like_random_posts(driver, min_likes=1, max_likes=4, min_scrolls_posts=1, max_scrolls_posts=4, scroll_delay=3)

    scroll_random_times(driver, min_scrolls=3, max_scrolls=7, scroll_delay=3)
    time.sleep(random.uniform(2, 3))

    # 7. Extract post content and save to file
    thread_content_file = os.path.join(thread_content_dir, f"{thread_title}.txt")
    extract_post_content(driver, thread_content_file)
    logger.info(f"Post content extracted and saved to {thread_content_file}")
    time.sleep(random.uniform(2, 3))

    # 8. Extract main post content
    main_post_content = extract_main_post_content(driver)
    time.sleep(random.uniform(2, 3))

    # 9. Generate and save comment
    if main_post_content:
        comment = generate_and_save_comments(main_post_content, os.path.join(api_comments_dir, "temp_comment.txt")) # Save to a temporary file
        if comment:
            # Sanitize the comment for use in the filename
            sanitized_comment = re.sub(r'[\\/*?:"<>|]', "", comment[:50])  # Take the first 50 characters
            api_comment_file = os.path.join(api_comments_dir, f"{thread_title}_{sanitized_comment}.txt")
            os.rename(os.path.join(api_comments_dir, "temp_comment.txt"), api_comment_file)  # Rename the temporary file
            logger.info(f"API comment generated and saved to {api_comment_file}")
        else:
            logger.warning("Failed to generate comment, skipping saving.")
    else:
        logger.warning("Failed to extract main post content, skipping comment generation.")

    # 10. Read the generated comment
    comment_file = os.path.join(api_comments_dir, f"{thread_title}_{sanitized_comment}.txt") # Use the new filename
    comment = read_thread_content(comment_file)
    time.sleep(random.uniform(2, 3))

    # 11. Post the comment (uncomment when ready, and ensure it is working)
    if comment:
        post_comment(driver, comment, write_delay=3)
        logger.info("Comment posted successfully.")
    else:
        logger.warning("No comment available to post.")


    time.sleep(2)
    driver.quit()
    logger.info("Driver quit successfully.")

except Exception as e:
    logger.error(f"An error occurred: {e}", exc_info=True)
    if driver:
        driver.quit()
        logger.info("Driver successfully quit after error.")
