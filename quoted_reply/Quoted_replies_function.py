import os
import time
import logging
import random
import re
import gc
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementNotInteractableException  # <-- Import it here
)

from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from Quoted_replies_config import MouseMovement
from Quoted_replies_manager import configure_logger, start_profile, stop_profile, signin, refresh_token
from gemini_api import GeminiHandler


# --- Configuration ---
BASE_URL = "https://www.blackhatworld.com/"
QUOTED_REPLIES_FOLDER = "quoted_replies"
API_GENERATED_REPLIES_FOLDER = "API_Generated_Replies"
PROMPT_FILE = "prompt.txt"
ALERT_BUTTON_LOCATOR = (By.XPATH, "//div//a[@data-xf-click='menu'][@title='Alerts']")
SHOW_ALL_LINK_TEXT = (By.LINK_TEXT,"Show all")
PROFILE = "PixelPirate99" 
COMMENT_EDITOR_LOCATOR = (By.XPATH,"//form[@method='post']//div[@contenteditable='true' and @aria-disabled='false' and @spellcheck='true']")
POST_REPLY_BUTTON_LOCATOR = (By.XPATH,"//span[contains(text(),'Post reply')]")
SCROLL_AMOUNT = 500

# --- Functions ---

def sanitize_filename(filename):
    """
    Sanitizes a filename by removing or replacing invalid characters.
    """
    # Replace invalid characters with underscores
    filename = re.sub(r'[<>:"/\\|?*\n]', "_", filename)
    # Remove leading/trailing whitespace
    filename = filename.strip()
    # Truncate if too long (adjust the length as needed)
    max_length = 255  # Maximum filename length for most systems
    if len(filename) > max_length:
        filename = filename[:max_length]
    return filename


def setup_folders():
    """Creates the necessary folders if they don't exist."""
    if not os.path.exists(QUOTED_REPLIES_FOLDER):
        os.makedirs(QUOTED_REPLIES_FOLDER)
    if not os.path.exists(API_GENERATED_REPLIES_FOLDER):
        os.makedirs(API_GENERATED_REPLIES_FOLDER)


def get_quoted_comments(driver, profile_logger, profile_name):
    """Finds all unique quoted comments and saves their details."""

    quoted_comments = []
    processed_links = set()  
    try:
        # Click on the alert button
        try:
            alert_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(ALERT_BUTTON_LOCATOR)
            )
            alert_button.click()
            profile_logger.info(f"Profile {profile_name}: Clicked on alert button.")
            profile_logger.debug(f"Profile {profile_name}: Clicked on alert button.")
            time.sleep(random.uniform(1, 2)) 
        except (TimeoutException, NoSuchElementException) as e:
            profile_logger.error(f"Profile {profile_name}: Alert button not found or not clickable: {e}")
            return quoted_comments 

        # Click on "Show all" link
        try:
            show_all_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Show all"))
            )
            show_all_link.click()
            profile_logger.info(f"Profile {profile_name}: Clicked on 'Show all' link.")
            profile_logger.debug(f"Profile {profile_name}: Clicked on 'Show all' link.")
            time.sleep(random.uniform(1, 2)) # Short pause after click
        except (TimeoutException, NoSuchElementException) as e:
            profile_logger.error(f"Profile {profile_name}: 'Show all' link not found or not clickable: {e}")
            profile_logger.warning(f"Profile {profile_name}: Could not click 'Show all', proceeding with visible alerts.")
            

        # Scroll and find quoted comments
        scroll_pause_time = 1.5 
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 15 

        while scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1
            profile_logger.debug(f"Scrolling attempt {scroll_attempts}/{max_scroll_attempts}")

            # --- REVISED ELEMENT FINDING AND PROCESSING ---
            try:
                # Find the list items containing the alerts first
                alert_list_items = driver.find_elements(By.XPATH, "//li[contains(@class, 'alert') and .//text()[contains(., 'quoted your post in the thread')]]")
                profile_logger.debug(f"Found {len(alert_list_items)} potential alert list items on this view.")

                new_items_found_this_scroll = 0
                for item in alert_list_items:
                    try:
                        # Find the link *within* this specific list item
                        link_element = item.find_element(By.XPATH, ".//a[contains(@href, '/posts/')]") # More specific link find within item

                        profile_link = link_element.get_attribute("href")
                        thread_title = link_element.text.strip()

                        # Check if link is valid and not already processed
                        if profile_link and profile_link not in processed_links:
                            if not thread_title: 
                                thread_title = "Title Not Found"
                                profile_logger.warning(f"Profile {profile_name}: Empty thread title for link {profile_link}")

                            profile_logger.debug(f"Found quote alert: Title='{thread_title}', Link='{profile_link}'")
                            quoted_comments.append({"thread_title": thread_title, "profile_link": profile_link})
                            processed_links.add(profile_link) # Add link to the set
                            new_items_found_this_scroll += 1

                    except (StaleElementReferenceException, NoSuchElementException) as e:
                        profile_logger.warning(f"Profile {profile_name}: Error processing an alert item: {e}. Skipping item.")
                        continue # Skip this specific item if error occurs

                profile_logger.info(f"Added {new_items_found_this_scroll} new unique quote alerts in this scroll.")
                profile_logger.debug(f"Added {new_items_found_this_scroll} new unique quote alerts in this scroll.")

            except NoSuchElementException:
                profile_logger.info(f"Profile {profile_name}: No alert list items found matching the criteria on this view.")
                profile_logger.debug(f"Profile {profile_name}: No alert list items found matching the criteria on this view.")
            # --- END REVISED ELEMENT FINDING ---

            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                profile_logger.info(f"Profile {profile_name}: Reached end of scroll (height didn't change).")
                profile_logger.debug(f"Profile {profile_name}: Reached end of scroll (height didn't change).")
                break # Exit scroll loop
            last_height = new_height
        else: # Runs if loop finished due to max_scroll_attempts
             profile_logger.warning(f"Profile {profile_name}: Reached maximum scroll attempts ({max_scroll_attempts}).")


        # Save the *unique* quoted comments to a file
        if quoted_comments:
            output_file = f"{profile_name}_quoted_reply_list.txt"
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    for comment in quoted_comments:
                        f.write(f"Thread Title: {comment['thread_title']}\n")
                        f.write(f"Profile Link: {comment['profile_link']}\n")
                        f.write("-" * 40 + "\n")
                profile_logger.info(f"Profile {profile_name}: Saved {len(quoted_comments)} unique quoted comments to {output_file}")
                profile_logger.debug(f"Profile {profile_name}: Saved {len(quoted_comments)} unique quoted comments to {output_file}")
            except IOError as e:
                profile_logger.error(f"Profile {profile_name}: Failed to write quoted comments to file {output_file}: {e}")
        else:
            profile_logger.info(f"Profile {profile_name}: No unique quoted comments found to save.")
            profile_logger.debug(f"Profile {profile_name}: No unique quoted comments found to save.")


        return quoted_comments

    except Exception as e:
        profile_logger.error(f"Profile {profile_name}: An unexpected error occurred in get_quoted_comments: {e}", exc_info=True)
        return [] # Return empty list on major error

def extract_details_and_save(driver, profile_logger, profile_name, quoted_comment):
    """Extracts thread details, quoted comment, and saves to a file."""
    try:
        
        selected_post = quoted_comment['profile_link'] 
        driver.get(selected_post)
        time.sleep(random.uniform(2, 5))    

        # Extract Thread Title (again, for confirmation)
        try:
            thread_title = driver.find_element(By.XPATH, "//div//h1").text.strip()
        except NoSuchElementException:
            profile_logger.error(f"Profile {profile_name}: Could not find thread title on the thread page.")
            return None
        
        # Extract Original Main Thread Content
        try:
            original_main_thread_content = driver.find_element(By.XPATH, ".//article//div[@data-lb-id]//article//div//div").text.strip()
        except NoSuchElementException:
            profile_logger.warning(f"Profile {profile_name}: Could not find original thread content.")
            original_main_thread_content = "Not Found"
            
        # Find "my previous comment" 
        try:
            my_previous_comment_locator = driver.find_element(By.XPATH,f"//article[@data-author='{PROFILE}']")
            my_previous_comment_element = my_previous_comment_locator.find_element(By.XPATH,".//div[@itemprop='text']//div[text()]")
            my_previous_comment = my_previous_comment_element.text.strip()
        except NoSuchElementException:
            profile_logger.warning(f"Profile {profile_name}: Could not find my previous comment.")
            my_previous_comment = "Not Found"

        # Find "quoted comment" help with beautifulsoup        
        try:
            wrapper_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//blockquote[@data-quote='{PROFILE}']/parent::div[contains(@class, 'bbWrapper')]"))
            )
            
            # Get the full HTML inside bbWrapper
            wrapper_html = wrapper_element.get_attribute("outerHTML")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(wrapper_html, "html.parser")

            # Remove the <blockquote> so we get only the comment text
            if soup.blockquote:
                soup.blockquote.decompose()

            # Get clean text of the remaining comment
            quoted_comment_text = soup.get_text(separator=" ", strip=True)
            profile_logger.info(f"Quoted comment extracted: {quoted_comment_text}")
        except Exception as e:
            profile_logger.warning(f"Profile {profile_name}: Could not find quoted comment. Error: {e}")
            quoted_comment_text = "Not Found"


        # Save extracted details to file
        filename = f"{sanitize_filename(thread_title)}_reply.txt"
        filepath = os.path.join(QUOTED_REPLIES_FOLDER, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"\n\n** Thread Title : ** \n {thread_title}\n")
            f.write(f"\n\n** Original Thread Content: ** \n {original_main_thread_content}\n")
            f.write(f"\n\n** My Previous Comment: ** \n {my_previous_comment}\n")
            f.write(f"\n\n** Quoted Comment: ** \n {quoted_comment_text}\n")

        profile_logger.info(f"Profile {profile_name}: Extracted details saved to {filepath}")
        profile_logger.debug(f"Profile {profile_name}: Extracted details saved to {filepath}")
        return filepath
    except Exception as e:
        profile_logger.error(f"Profile {profile_name}: Error extracting details: {e}", exc_info=True)
        return None

# extract element text
def extract_element_text(profile_logger, element, xpath):
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

def extract_post_content(profile_logger, driver, output_file):
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
                profile_logger.debug(f"Total comments in the thread: {total_comments}")
                file.write(f"Total comments in the thread: {total_comments}\n\n")
            except Exception as e:
                profile_logger.warning(
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
                    logging.debug(f"Processing post with ID: {post_id}")
                except Exception as e:
                    post_id = "No ID Found"
                    logging.error(f"Could not extract post ID. Error: {e}", exc_info=True)
                    logging.debug(f"Could not extract post ID. Error: {e}", exc_info=True)

                # Username
                topic_username = extract_element_text(profile_logger, post_element, ".//h4//a//span")
                file.write(f"Topic User: {topic_username}\n")
                logging.debug(f"Topic User: {topic_username}")

                # thread content
                topic_locator = ".//div[@class='message-content js-messageContent']"
                topic = extract_element_text(profile_logger, post_element, topic_locator)
                file.write(f"Topic: {topic}\n")
                logging.debug(f"Topic: {topic}")

                try:
                    # likes
                    like_user_locator = ".//a[@data-xf-click='overlay'][@data-cache='false'][@rel='nofollow']"
                    like_element = WebDriverWait(post_element, 10).until(
                         EC.presence_of_element_located((By.XPATH, like_user_locator)))

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

# extract thread title
def get_thread_title(profile_logger, driver):
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div//h1'))
        )
        thread_title = title_element.text.strip()
        thread_title = re.sub(r'[\\/*?:"<>|]', "", thread_title)
        profile_logger.info(f"Extracted thread title: {thread_title}")
        profile_logger.debug(f"Extracted thread title: {thread_title}")
        return thread_title

    except Exception as e:
        profile_logger.warning(
            f"Could not extract thread title. Error: {e}", exc_info=True
        )
        return "Untitled Thread"

def generate_api_comment(profile_logger, reply_context_filepath, thread_content_filepath, gemini_handler): # Add thread_content_filepath
    """Generates comment using Gemini API, considering full thread context."""
    try:
        # --- Pass BOTH filepaths to the handler ---
        comments = gemini_handler.get_comments(reply_context_filepath, thread_content_filepath, prompt_file=PROMPT_FILE)

        if comments:
             # Sanitize the comment for use in the filename *prefix*
             safe_comment_prefix = sanitize_filename(comments[:50])  

             
             # Extract thread title safely from the reply context filename
             base_reply_filename = os.path.basename(reply_context_filepath)
             thread_title_match = re.match(r"^(.*?)_reply\.txt$", base_reply_filename)
             thread_title = thread_title_match.group(1) if thread_title_match else "unknown_thread"

             safe_filename = sanitize_filename(f"{thread_title}_{safe_comment_prefix}")
             base_filename = os.path.join(API_GENERATED_REPLIES_FOLDER, safe_filename)

             # Add a counter to avoid overwriting files.
             counter = 1
             api_comment_filepath = f"{base_filename}.txt" # initial path
             while os.path.exists(api_comment_filepath):
                 api_comment_filepath = f"{base_filename}_{counter}.txt"  # create new path
                 counter += 1

             # Save API generated comment to file
             try:
                 with open(api_comment_filepath, "w", encoding="utf-8") as f:
                     f.write(comments)
                 profile_logger.info(f"API Generated Reply: {comments}")
                 profile_logger.debug(f"API Generated Reply: {comments}")
                 profile_logger.info(f"API generated comment saved to {api_comment_filepath}")
                 profile_logger.debug(f"API generated comment saved to {api_comment_filepath}")

                 return api_comment_filepath
             except OSError as e:
                 profile_logger.error(f"Error saving API comment: {e}")
                 return None
        else:
             profile_logger.error(f"Failed to generate comment using Gemini API.")
             return None
    except Exception as e:
         profile_logger.error(f"Error generating API comment: {e}", exc_info=True)
         return None

def reply_to_comment(driver, profile_logger, profile_name, api_comment_filepath):
    """Finds the quoted comment, clicks reply, inserts API comment *after* the quote using precise JS, and posts."""
    try:
        # Load API Generated Reply
        try:
            with open(api_comment_filepath, "r", encoding="utf-8") as f:
                api_generated_reply = f.read().strip()
                if not api_generated_reply:
                    profile_logger.error(f"Profile {profile_name}: API Generated Reply file is empty.")
                    return False
        except FileNotFoundError:
            profile_logger.error(f"Profile {profile_name}: API Generated Reply file not found at {api_comment_filepath}.")
            return False
        except Exception as e:
            profile_logger.error(f"Profile {profile_name}: Error reading API Generated Reply file: {e}", exc_info=True)
            return False

        # --- Find the specific post containing the quote ---
        # Using PROFILE constant which should hold the *exact* username as used in data-quote attribute
        quoted_post_article_locator = (By.XPATH, f"//article[.//blockquote[@data-quote='{PROFILE}']]")
        try:
            quoted_post_article = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(quoted_post_article_locator)
            )
            profile_logger.info(f"Found the article containing the quoted comment for '{PROFILE}'.")
            profile_logger.debug(f"Found the article containing the quoted comment for '{PROFILE}'.")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", quoted_post_article)
            time.sleep(random.uniform(0.5, 1.0))
        except TimeoutException:
            profile_logger.error(f"Profile {profile_name}: Could not find the article containing the quote for '{PROFILE}'. Ensure PROFILE constant ('{PROFILE}') matches the data-quote attribute exactly.")
            return False
        except Exception as e:
            profile_logger.error(f"Profile {profile_name}: Error finding or scrolling to the quoted post article: {e}", exc_info=True)
            return False

        # --- Find and Click the Reply/Quote button *within that specific article* ---
        reply_button_locator = (By.XPATH, ".//footer//a[contains(@class, 'actionBar-action--reply') or contains(@class, 'actionBar-action--quote') or @data-xf-click='quote']")
        reply_button = None

        try:
            # Ensure we are looking *within* the specific article we found
            reply_button = WebDriverWait(quoted_post_article, 10).until(
                EC.element_to_be_clickable(reply_button_locator)
            )
            profile_logger.info(f"Profile {profile_name}: Found reply/quote button within the specific post.")
            profile_logger.debug(f"Profile {profile_name}: Found reply/quote button within the specific post.")
            driver.execute_script("arguments[0].click();", reply_button)
            profile_logger.info(f"Profile {profile_name}: Clicked reply/quote button using JavaScript.")
            profile_logger.debug(f"Profile {profile_name}: Clicked reply/quote button using JavaScript.")
            time.sleep(random.uniform(2.5, 4.5)) # Wait for editor to load quote

        except TimeoutException:
            profile_logger.error(f"Profile {profile_name}: Reply/Quote button within the specific article not found or clickable.")
            # Attempt to find a more general reply button as a fallback? Maybe not ideal.
            return False
        
        except ElementNotInteractableException:
             profile_logger.warning(f"Profile {profile_name}: Reply/Quote button found but not interactable. Trying JS click again.")
             try:
                 driver.execute_script("arguments[0].click();", reply_button)
                 profile_logger.info(f"Profile {profile_name}: Clicked reply/quote button using JavaScript (second attempt).")
                 profile_logger.debug(f"Profile {profile_name}: Clicked reply/quote button using JavaScript (second attempt).")
                 time.sleep(random.uniform(2.5, 4.5))
             except Exception as js_e:
                  profile_logger.error(f"Profile {profile_name}: Error clicking reply/quote button even with JS: {js_e}", exc_info=True)
                  return False
        except Exception as e:
            profile_logger.error(f"Profile {profile_name}: Error finding or clicking reply/quote button: {e}", exc_info=True)
            return False

        # --- Wait for the comment editor to be ready and contain the quote ---
        try:
            profile_logger.debug(f"Waiting for comment editor ({COMMENT_EDITOR_LOCATOR})...")
            comment_editor_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(COMMENT_EDITOR_LOCATOR)
            )
            # Specifically wait for the blockquote *inside* the editor to ensure quote is loaded
            blockquote_in_editor_locator = (By.XPATH, ".//blockquote")
            WebDriverWait(comment_editor_element, 15).until(
                EC.presence_of_element_located(blockquote_in_editor_locator)
            )
            profile_logger.info("Comment editor is present and contains a blockquote.")
            profile_logger.debug("Comment editor is present and contains a blockquote.")
            time.sleep(random.uniform(1, 2)) # Short delay before interacting

        except TimeoutException:
            profile_logger.error(f"Comment editor or blockquote within it did not become present within timeout.", exc_info=True)
            return False
        except Exception as e:
             profile_logger.error(f"Unexpected error waiting for comment editor/quote: {e}", exc_info=True)
             return False

        # --- Prepare reply text and Insert AFTER the quote using JavaScript insertAdjacentHTML ---
        try:
            # Ensure the editor is scrolled into view
            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", comment_editor_element)
            time.sleep(0.5)

            profile_logger.info("Attempting to insert reply using JavaScript insertAdjacentHTML.")
            profile_logger.debug("Attempting to insert reply using JavaScript insertAdjacentHTML.")
            escaped_reply_for_html = api_generated_reply.replace('\\', '\\\\') \
                                                       .replace('"', '\\"') \
                                                       .replace('\n', '<br>') \
                                                       .replace('\r', '') # Remove carriage returns just in case

            # Construct the HTML to insert:
            # - Start with <p><br></p> to create a clear paragraph break after the quote.
            # - Wrap the actual reply in its own <p> tag.
            html_to_insert = f'<p><br></p><p>{escaped_reply_for_html}</p>'

            # Find the blockquote element *within* the editor element we already found
            blockquote_element = comment_editor_element.find_element(By.XPATH, ".//blockquote")

            # Execute JS to insert the prepared HTML *after* the blockquote element
            driver.execute_script("arguments[0].insertAdjacentHTML('afterend', arguments[1]);",
                                  blockquote_element,
                                  html_to_insert)

            profile_logger.info("Inserted API generated reply using JavaScript after the blockquote.")
            profile_logger.debug("Inserted API generated reply using JavaScript after the blockquote.")
            time.sleep(random.uniform(1.5, 2.5)) # Pause after JS manipulation

        except NoSuchElementException:
             profile_logger.error(f"Failed to find blockquote *inside* the editor element right before insertion.")
             return False
        except Exception as e:
             profile_logger.error(f"Failed to insert reply using JavaScript insertAdjacentHTML: {e}", exc_info=True)
             return False

        # --- Find and Click the "Post reply" Button ---
        try:
            post_reply_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(POST_REPLY_BUTTON_LOCATOR)
            )
            element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(COMMENT_EDITOR_LOCATOR)
                )
            actions = ActionChains(driver)
            location = post_reply_button.location
            size = post_reply_button.size
            profile_logger.debug(f"Post reply Element location: {location}, size: {size}")

            target_x = location["x"] + size["width"] // 2
            target_y = location["y"] + size["height"] // 2
            profile_logger.debug(f"Target click coordinates: ({target_x}, {target_y})")

            mouse_movement = MouseMovement()  # Create an instance if not already done
            mouse_movement.move_mouse_with_curve(target_x, target_y)

            profile_logger.debug("Moved mouse to target location using bezier curve.")

            actions.move_to_element(element)
            profile_logger.debug("Moving mouse to text box element.")


            profile_logger.info("Found 'Post reply' button.")
            profile_logger.debug("Found 'Post reply' button.")

            # Scroll into view just before clicking
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_reply_button)
            time.sleep(random.uniform(0.5, 1.0))
            # Use JS click for reliability
            driver.execute_script("arguments[0].click();", post_reply_button)
            profile_logger.info("Clicked 'Post reply' button using JavaScript.")
            profile_logger.debug("Clicked 'Post reply' button using JavaScript.")

            # --- Wait for confirmation (Example: check if editor disappears) ---
            try:
                WebDriverWait(driver, 25).until(
                    EC.staleness_of(comment_editor_element)
                )
                profile_logger.info("Reply posted successfully (editor became stale).")
                profile_logger.debug("Reply posted successfully (editor became stale).")
            except TimeoutException:
                 profile_logger.warning("Editor did not become stale. Reply might have posted, but confirmation failed. Check the thread manually.")
                 # Could add alternative checks here if needed (e.g., wait for URL change, look for the new post text)

            time.sleep(random.uniform(3, 5)) # Pause after posting
            return True # Indicate success

        except TimeoutException:
            profile_logger.error(f"'Post reply' button not found or not clickable within timeout.")
            return False
        except Exception as e:
            profile_logger.error(f"Unexpected error clicking 'Post reply' or waiting for success: {e}", exc_info=True)
            return False

    except Exception as e:
        profile_logger.error(f"Profile {profile_name}: A critical error occurred during the reply process: {e}", exc_info=True)
        return False # Indicate failure

    finally:
        # Navigate back to homepage
        try:
            if driver: # Check if driver exists before using it
                driver.get(BASE_URL) # Make sure BASE_URL is defined globally or passed in
                profile_logger.info(f"Profile {profile_name}: Navigated back to homepage.")
                profile_logger.debug(f"Profile {profile_name}: Navigated back to homepage.")
                time.sleep(random.uniform(2, 4))
        except Exception as nav_e:
            profile_logger.error(f"Profile {profile_name}: Failed to navigate back to homepage: {nav_e}")


# clear memory after automation
def clear_memory(profile_logger):
    profile_logger.info("Attempting to clear memory and resources.")
    profile_logger.debug("Attempting to clear memory and resources.")
    gc.collect()
    profile_logger.info("Garbage collection completed.")
    profile_logger.debug("Garbage collection completed.")