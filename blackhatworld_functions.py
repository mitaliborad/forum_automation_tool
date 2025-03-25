import time
import logging
import re
import gc
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from blackhatworld_config import (  # Corrected import
    SUB_FORUM_LIST_FILE,
    VISITED_THREADS_FILE,
    MIN_SCROLLS,
    MAX_SCROLLS,
    SCROLL_AMOUNT,
    SCROLL_DELAY,
    MIN_LIKES,
    MAX_LIKES,
    MIN_SCROLLS_POSTS,
    MAX_SCROLLS_POSTS,
    SCROLL_DELAY_LIKES,
    WRITE_DELAY,
    MouseMovement # Import MouseMovement class
) # Import configuration variables
from gemini_api import GeminiHandler  # import gemini

# Helper functions

def get_subforum_list(logger, file_path=SUB_FORUM_LIST_FILE):
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


def load_visited_threads(logger, file_path=VISITED_THREADS_FILE):
    """Loads the list of visited threads from the specified file."""
    try:
        with open(file_path, "r") as f:
            visited_threads = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(visited_threads)} visited threads from {file_path}")
        return set(visited_threads)  # Use a set for faster lookups
    except FileNotFoundError:
        logger.info(
            f"Visited threads file '{file_path}' not found. Starting with an empty list."
        )
        return set()
    except Exception as e:
        logger.error(f"Error reading visited threads file: {e}", exc_info=True)
        return set()


def save_visited_thread(logger, thread_url, file_path=VISITED_THREADS_FILE):
    """Appends a thread URL to the list of visited threads."""
    try:
        with open(file_path, "a") as f:
            f.write(thread_url + "\n")
        logger.info(f"Saved thread URL '{thread_url}' to visited threads file '{file_path}'.")
    except Exception as e:
        logger.error(f"Error saving thread URL to visited threads file: {e}", exc_info=True)


def scroll_page(logger, driver, scroll_amount=SCROLL_AMOUNT, min_delay=1, max_delay=2.0):
    logger.debug(f"Scrolling page by {scroll_amount} pixels.")
    try:
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    except Exception as e:
        logger.warning(f"Scrolling failed: {e}")
    time.sleep(random.uniform(min_delay, max_delay))
    logger.debug("Page scrolled.")


def scroll_random_times(logger, driver, min_scrolls=MIN_SCROLLS, max_scrolls=MAX_SCROLLS, scroll_amount=SCROLL_AMOUNT, scroll_delay=SCROLL_DELAY):
    num_scrolls = random.randint(min_scrolls, max_scrolls)
    logger.debug(f"Scrolling page {num_scrolls} times.")
    for _ in range(num_scrolls):
        scroll_page(logger, driver, scroll_amount)
        time.sleep(scroll_delay)
    logger.debug("Random scrolls complete.")


def click_element(logger, driver, locator):
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
            logger.error(
                f"Failed to click element after attempting ActionChains: {locator}. Error: {e}",
                exc_info=True,
            )


def find_element_with_scroll(logger, driver, locator, max_scrolls=5):
    logger.debug(f"Attempting to find element with locator: {locator}")
    for i in range(max_scrolls):
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(locator)
            )
            logger.info(f"Element found after {i + 1} scrolls: {locator}")
            return element
        except:
            logger.debug(
                f"Element not found, scrolling page (attempt {i + 1}/{max_scrolls})."
            )
            scroll_page(logger, driver, scroll_amount=400)
    logger.warning(f"Element not found after {max_scrolls} scrolls: {locator}")
    return None


def find_like_buttons(logger, driver):
    try:
        like_buttons = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//bdi[contains(text(), 'Like')]"))
        )
        logger.debug(f"Found {len(like_buttons)} like buttons.")
        likes_length = len(like_buttons)
        return like_buttons, likes_length
    except Exception as e:
        logger.warning(f"Error finding like buttons: {e}", exc_info=True)
        return [], 0  # Return an empty list and 0 if no buttons found


def click_like_button(logger, driver, button, scroll_delay=2):
    try:
        driver.execute_script("arguments[0].scrollIntoView();", button)
        time.sleep(random.uniform(0.5, 1))
        logger.debug(
            "Scrolling like button into view and attempting to click using JavaScript."
        )
        driver.execute_script("arguments[0].click();", button)
        logger.info("Like button clicked successfully using JavaScript.")
        return True
    except Exception as e:
        logger.warning(
            f"JavaScript click failed: {e}, attempting ActionChains.", exc_info=True
        )
        try:
            ActionChains(driver).move_to_element(button).click().perform()
            logger.info("Like button clicked successfully using ActionChains.")
            return True
        except Exception as e:
            logger.error(
                f"Failed to click like button after attempting ActionChains: {e}",
                exc_info=True,
            )
            return False

def like_random_posts(logger, driver, min_likes=MIN_LIKES, max_likes=MAX_LIKES, min_scrolls_posts=MIN_SCROLLS_POSTS, max_scrolls_posts=MAX_SCROLLS_POSTS, scroll_delay=SCROLL_DELAY_LIKES):
    """Likes a random number of posts, avoiding duplicates."""
    try:
        scroll_random_times(
            logger, driver,
            min_scrolls_posts,
            max_scrolls_posts,
            scroll_amount=500,
            scroll_delay=scroll_delay,
        )
        like_buttons, likes_length = find_like_buttons(logger, driver)

        if not like_buttons:
            logger.info("No like buttons found, skipping like_random_posts function...")
            return

        total_likes = random.randint(min_likes, max_likes)
        total_likes = min(total_likes, likes_length)

        liked_buttons = set() #To avoid Duplicates
        successful_likes = 0  # Counter for the number of successful likes

        time.sleep(scroll_delay)
        logger.info(
            f"Attempting to like {total_likes} posts. There are {likes_length} available."
        )

        current_index = 0
        while successful_likes < total_likes and current_index < likes_length:
            button = like_buttons[current_index]

            if button not in liked_buttons: #Cheeck for duplicates

                if click_like_button(logger, driver, button, scroll_delay):
                   liked_buttons.add(button)
                   successful_likes += 1
                   logger.debug(f"Liked post number {successful_likes} of {total_likes}.")
                   time.sleep(random.uniform(4, 5))

                else:
                   logger.warning(f"Failed to like post at index {current_index}.")

            else:
                 logger.info(f"Skipping already liked post at index {current_index}")

            current_index+=1 # increase the index

        logger.info(f"Liked {successful_likes} posts successfully.")
    except Exception as e:
        logger.error(f"Unexpected error in like_random_posts: {e}", exc_info=True)

    logger.info(f"Liked {successful_likes} posts successfully.")

# count comments
def count_main_post_comments(logger, driver):
    try:
        # Locate the first post container
        first_post = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//article[@data-author][1]"))
        )

        # Find all reply buttons inside the first post only
        reply_buttons = first_post.find_elements(
            By.XPATH, ".//footer//a[contains(@class, 'actionBar-action--reply')]"
        )

        # Count the number of reply buttons
        total_comments = len(reply_buttons)

        print(f"Total comments on the first post: {total_comments}")
        return total_comments

    except Exception as e:
        print(f"Error counting comments: {e}")
        return 0


# extract element text
def extract_element_text(logger, element, xpath):
    try:
        element = WebDriverWait(element, 3).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        text = element.text.strip()
        logging.debug(f"Extracted text '{text}' from element with XPath: {xpath}")
        return text
    except Exception as e:
        logging.warning(
            f"Could not extract text from element with XPath: {xpath}. Error: {e}",
            exc_info=True,
        )
        return "No text found"


# extract main post content
def extract_main_post_content(logger, driver):
    try:
        main_post_locator = (
            By.XPATH,
            '//div[@data-lb-id and contains(@data-lb-id, "post-")]',
        )
        logger.debug(
            f"Attempting to locate main post element with locator: {main_post_locator}"
        )
        main_post_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(main_post_locator)
        )
        main_post_text = main_post_element.text.strip()
        logger.debug(f"Extracted main post content: {main_post_text}")
        return main_post_text
    except Exception as e:
        logger.warning(
            f"Could not extract main post content. Error: {e}", exc_info=True
        )
        return None


# extract post content
def extract_post_content(logger, driver, output_file):
    try:
        posts_locator = (By.CSS_SELECTOR, "article[data-author]")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(posts_locator))
        all_posts_elements = driver.find_elements(*posts_locator)

        with open(output_file, "w", encoding="utf-8") as file:
            try:
                #for main post title
                main_post_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//h1"))
                )
                main_post = main_post_element.text.strip()
                file.write(f"--- Main Post Title ---\n{main_post}\n\n")
                logging.debug(f"Main Post Title: {main_post}")
            except Exception as e:
                file.write(f"--- Main Post Title ---\nNo main post title found\n\n")
                logging.warning(
                    f"No main post title found. Error: {e}", exc_info=True
                )

            try:
                #for all comments in the page
                all_comments = driver.find_elements(
                    By.XPATH, "//footer//a[contains(@class, 'actionBar-action--reply')]"
                )
                total_comments = len(all_comments)
                logger.debug(f"Total comments in the thread: {total_comments}")
                file.write(f"Total comments in the thread: {total_comments}\n\n")
            except Exception as e:
                logger.warning(
                    f"Could not count total comments: {e}", exc_info=True
                )
                file.write("Total comments: 0\n\n")

            first_post = True

            # select one post among all posts
            for post_element in all_posts_elements:
                try:
                    link_element = post_element.find_element(By.XPATH, ".//div[@data-lb-id]")
                    post_id = link_element.get_attribute("data-lb-id")
                    logging.info(f"Processing post with ID: {post_id}")
                except Exception as e:
                    post_id = "No ID Found"
                    logging.error(f"Could not extract post ID. Error: {e}", exc_info=True)

                # Username
                topic_username = extract_element_text(logger, post_element, ".//h4//a//span")
                file.write(f"Topic User: {topic_username}\n")
                logging.debug(f"Topic User: {topic_username}")

                # thread content
                topic_locator = ".//div[@class='message-content js-messageContent']"
                topic = extract_element_text(logger, post_element, topic_locator)
                file.write(f"Topic: {topic}\n")
                logging.debug(f"Topic: {topic}")

                try:
                    # likes
                    like_user_locator = ".//a[@data-xf-click='overlay'][@data-cache='false'][@rel='nofollow']"
                    like_element = WebDriverWait(post_element, 10).until(
                         EC.presence_of_element_located((By.XPATH, like_user_locator)))
                    # )
                    # like_user_text = like_user_elements.text.strip()

                    # parts = re.split(r", | and ", like_user_text)
                    # other_count = 0
                    # if parts and "others" in parts[-1]:
                    #     try:
                    #         other_count = int(re.search(r'(\d+)', parts[-1]).group(1))
                    #         parts = parts[:-1]
                    #     except:
                    #         other_count = 0

                    # like_users = [user.strip() for user in parts if user.strip()]
                    # if "You and" in like_text:
                    #     like_users.append("You")
                    #     other_likes = like_element.find_elements(By.XPATH,".//bdi")
                    #     for other_like in other_likes:
                    #         like_users.append(other_like.text.strip())

                    # like_count = len(like_users) + other_count
                    #like_element = post_element.find_element(By.XPATH, like_user_locator)

                    like_text = like_element.text.strip()
                    like_users = []

                    if "You and" in like_text:  # Check if "You and" is present
                        like_users.append("You")  # Add "You" to the list
                        other_likes = like_element.find_elements(By.XPATH, ".//bdi")  # Find other users
                        for other_like in other_likes:
                            like_users.append(other_like.text.strip())  # Add other user names

                    elif "You" in like_text:  # If only "You" has liked
                         like_users.append("You")
                    else:
                         other_likes = like_element.find_elements(By.XPATH, ".//bdi")  # Find other users
                         for other_like in other_likes:
                             like_users.append(other_like.text.strip())  # Add other user names


                    like_count = len(like_users)  # Count all users who liked
                    like_user_text = ", ".join(like_users) 

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
def read_thread_content(logger, file_path):
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
def generate_and_save_comments(logger, thread_content, output_file):
    try:
        gemini_handler = GeminiHandler()
        comments = gemini_handler.get_comments(thread_content, prompt_file="prompt.txt")

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
def post_comment(logger, driver, comment, write_delay=WRITE_DELAY):
    if not comment:
        logger.warning("No comment to post.")
        return False

    try:
        write_comment_locator = (
            By.XPATH,
            "//span[contains(text(), 'Write your reply...')]",
        )
        logger.debug(f"Searching for text box with locator: {write_comment_locator}")
        write_comment = find_element_with_scroll(logger, driver, write_comment_locator)

        post_reply = driver.find_element(By.XPATH, "//span[contains(text(),'Post reply')]")
        if write_comment:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(write_comment_locator)
                )
                logger.debug(
                    f"Text box is clickable using element_to_be_clickable with locator : {write_comment_locator}"
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                logger.debug("Text box scrolled into view")
                time.sleep(random.uniform(0.5, 1))

                logger.debug("Initializing actionchains")
                actions = ActionChains(driver)

                location = post_reply.location
                size = post_reply.size
                logger.debug(f"Post reply Element location: {location}, size: {size}")

                target_x = location["x"] + size["width"] // 2
                target_y = location["y"] + size["height"] // 2
                logger.debug(f"Target click coordinates: ({target_x}, {target_y})")

                mouse_movement = MouseMovement() #Initialize mouse Movement
                mouse_movement.move_mouse_with_curve(target_x, target_y) #Access with class

                logger.debug("Moved mouse to target location using bezier curve.")

                actions.move_to_element(element)
                logger.debug("Moving mouse to text box element.")

                actions.click()
                logger.debug(f"Clicking on the text box.")

                actions.send_keys(comment)
                logger.debug(f"Sending keys with content: {comment}")

                time.sleep(random.uniform(2, 3))
                time.sleep(write_delay)
                actions.click(post_reply)
                logger.debug(f"Clicking on post reply button.")

                actions.perform()
                logger.debug("Performed Actionchains")
                logger.info(
                    "Successfully wrote into text box using ActionChains and click."
                )

                time.sleep(4)

            except Exception as e:
                logger.error(f"Error posting comment: {e}", exc_info=True)
                return False

    except Exception as e:
        logger.error("if comment closed then you should close the browser")
        try:
            block_comment_locator = (
                By.XPATH,
                '//div//dl[@class="blockStatus"]//dd',
            )
            logger.debug(f"Searching for text with locator: {block_comment_locator}")
            block_comment = find_element_with_scroll(logger, driver, block_comment_locator)
            if block_comment:
                driver.quit()
            else:
                print("no driver found")
        except Exception as e:
            print(e)


# extract thread title
def get_thread_title(logger, driver):
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div//h1'))
        )
        thread_title = title_element.text.strip()
        thread_title = re.sub(r'[\\/*?:"<>|]', "", thread_title)
        logger.info(f"Extracted thread title: {thread_title}")
        return thread_title

    except Exception as e:
        logger.warning(
            f"Could not extract thread title. Error: {e}", exc_info=True
        )
        return "Untitled Thread"


# clear memory after automation
def clear_memory(logger):
    logger.info("Attempting to clear memory and resources.")
    gc.collect()
    logger.info("Garbage collection completed.")


# find random thread link from Sub-Forum-link
# find random thread link from Sub-Forum-link
def find_random_thread_link_from_subforum(logger, driver, subforum_url, visited_threads):
    """Navigates to a subforum and finds a random thread link, avoiding deleted threads."""
    deleted_thread_xpath = "//a[contains(@href, '/seo/deleted.') and normalize-space(text())='deleted']"  # Define the XPath here

    try:
        driver.get(subforum_url)
        logger.info(f"Navigated to subforum: {subforum_url}")

        wait = WebDriverWait(driver, 10)
        wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'structItem')]"))
        )
        all_threads = driver.find_elements(By.XPATH, "//div[contains(@class, 'structItem')]")
        unvisited_threads = []

        for thread in all_threads:
            try:
                sticky_span = thread.find_elements(
                    By.XPATH, ".//span[contains(@class, 'sticky-thread--hightlighted')]"
                )

                # Skip if the span exists, indicating it's a sticky thread
                if sticky_span:
                    continue

                title_elements = thread.find_elements(
                    By.XPATH, ".//div[contains(@class, 'structItem-title')]//a"
                )

                if title_elements:
                    href = title_elements[0].get_attribute("href")
                    if href not in visited_threads:
                         # *NEW: Check if the thread is a "deleted" thread*
                         try:
                             deleted_elements = thread.find_elements(By.XPATH, deleted_thread_xpath)
                             if not deleted_elements:  # If no "deleted" elements are found
                                 unvisited_threads.append(title_elements[0])  # Append unvisited and NOT deleted thread

                             else:
                                 logger.warning(f"Skipping deleted thread: {href}")

                         except Exception as e:
                              logger.warning(f"Error checking if thread is deleted: {e}, assuming not deleted.")
                              unvisited_threads.append(title_elements[0]) # If any error happens consider it not deleted

            except Exception as e:
                logger.warning(f"Skipping a thread due to error: {e}")

        if not unvisited_threads:
            logger.warning(
                f"No unvisited, non-deleted thread links found in subforum: {subforum_url}"
            )
            return None

        random_link = random.choice(unvisited_threads)
        href = random_link.get_attribute("href")
        logger.info(f"Selected random thread link: {href}")
        return href

    except Exception as e:
        logger.error(
            f"Error finding random thread link in subforum: {e}", exc_info=True
        )
        return None



# after automation it navigate home page
def navigate_home(logger, driver):
    """Navigates the driver back to the main BHW homepage."""
    try:
        driver.get("https://www.blackhatworld.com/")
        logger.info("Navigated back to the homepage.")
        time.sleep(random.uniform(2, 3))  # Short delay to ensure page load
    except Exception as e:
        logger.error(f"Failed to navigate back to the homepage: {e}", exc_info=True)