import os
import time
import logging
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from Quoted_replies_config import setup_logger  
from Quoted_replies_manager import PROFILES, configure_logger, start_profile, stop_profile, signin, refresh_token
from gemini_api import GeminiHandler
from Quoted_replies_config import (LOG_DIRECTORY)
from Quoted_replies_function import (
    sanitize_filename,
    setup_folders,
    get_quoted_comments,
    extract_details_and_save,
    generate_api_comment,
    reply_to_comment,
    get_thread_title,
    extract_post_content,
    clear_memory
)

# --- Configuration ---
BASE_URL = "https://www.blackhatworld.com/"
QUOTED_REPLIES_FOLDER = "quoted_replies"
API_GENERATED_REPLIES_FOLDER = "API Generated Replies"
PROMPT_FILE = "prompt.txt"
ALERT_BUTTON_LOCATOR = (By.XPATH, "//div//a[@data-xf-click='menu'][@title='Alerts']")
SHOW_ALL_LINK_TEXT = (By.LINK_TEXT,"Show all")
PROFILE = "PixelPirate99"
REPLY_BUTTON_LOCATOR = (By.XPATH, "//article//blockquote[@data-quote='BinaryGhost']//ancestor::article//footer//div//a[@data-xf-click='quote']")
COMMENT_TEXTAREA_LOCATOR = (By.XPATH,"//form[@method='post']//div//span[text()='Write your reply...']")
POST_REPLY_BUTTON_LOCATOR = (By.XPATH,"//span[contains(text(),'Post reply')]")
SCROLL_AMOUNT = 500



def main():
    """Main function to orchestrate the automation."""

    # Setup basic logging in case configure_logger fails early
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - MAIN - %(levelname)s - %(message)s")
    logging.info("--- Automation Script Starting ---")

    setup_folders() # Ensure folders exist
    logging.info("Checked/Created necessary directories.")

    for profile_name, profile_config in PROFILES.items():
        profile_logger = configure_logger(profile_name)
        token, expiration_time = None, None
        driver = None   
        
        try:

            # Initialize logger *outside* the loop, for the profile itself
            profile_logger, profile_log_file = setup_logger(LOG_DIRECTORY, profile_name)
            profile_logger.info(f"Starting automation for profile: {profile_name}")

            thread_content_dir = "Thread-Details/Thread Content"
            if not os.path.exists(thread_content_dir):
                logging.info(f"Created directory: {thread_content_dir}")
                os.makedirs(thread_content_dir)
            
            # Sign In
            token, expiration_time = signin(profile_name, profile_config, profile_logger)
            if not token:
                profile_logger.error(f"Profile {profile_name}: Failed to sign in. Skipping.")
                continue
                
            # Start Profile
            driver = start_profile(profile_name, profile_config, token, profile_logger)
            if not driver:
                profile_logger.error(f"Profile {profile_name}: Failed to start profile. Skipping.")
                continue
            
            driver.get(BASE_URL)
            profile_logger.info(f"Profile {profile_name}: Navigated to {BASE_URL}")
            profile_logger.debug(f"Profile {profile_name}: Navigated to {BASE_URL}")
            time.sleep(random.uniform(3,4))

            # perform_random_action(driver, profile_logger, profile_name) # Add random human-like actions

            # Get Quoted Comments 
            quoted_comments = get_quoted_comments(driver, profile_logger, profile_name)
            if not quoted_comments:
                profile_logger.info(f"Profile {profile_name}: No quoted comments found. Skipping.")
                profile_logger.debug(f"Profile {profile_name}: No quoted comments found. Skipping.")
                continue
            time.sleep(random.uniform(3,4))
                
            # Select a random quoted comment
            selected_comment = random.choice(quoted_comments)
            profile_logger.info(f"Profile {profile_name}: Selected comment - {selected_comment['thread_title']}")
            profile_logger.debug(f"Profile {profile_name}: Selected comment - {selected_comment['thread_title']}")
            time.sleep(random.uniform(3,4))

            # Extract Details and Save
            reply_context_filepath = extract_details_and_save(driver, profile_logger, profile_name, selected_comment)
            if not reply_context_filepath:
                profile_logger.error(f"Profile {profile_name}: Failed to extract reply details. Skipping comment.")
                continue

            # save thread content
            thread_title = get_thread_title(profile_logger, driver) 
            profile_logger.info("thread title found")
            profile_logger.debug("thread title found")
            thread_content_file = os.path.join(
                thread_content_dir, f"{thread_title}.txt"
            )

            extract_post_content(profile_logger, driver, thread_content_file) 
            profile_logger.info(f"Post content extracted and saved to {thread_content_file}") 
            profile_logger.debug(f"Post content extracted and saved to {thread_content_file}") 
               
            # Generate API Comment
            gemini_handler = GeminiHandler()
            time.sleep(random.uniform(3,4))
            api_comment_filepath = generate_api_comment(profile_logger,reply_context_filepath,thread_content_file, gemini_handler)
            if not api_comment_filepath:
                profile_logger.error(f"Profile {profile_name}: Failed to generate API comment. Skipping.")
                continue

            time.sleep(random.uniform(3,4))

            # Reply to Comment
            reply_to_comment(driver, profile_logger, profile_name, api_comment_filepath)
            time.sleep(random.uniform(3,4))

        except Exception as e:
            profile_logger.error(f"Profile {profile_name}: An unexpected error occurred: {e}", exc_info=True)
            
            
        finally:
            # Stop Profile
            if driver:
                stop_profile(profile_name, profile_config, token, profile_logger, driver)
            profile_logger.info(f"Profile {profile_name}: Finished processing.")
            profile_logger.debug(f"Profile {profile_name}: Finished processing.")
            clear_memory(profile_logger)

if __name__ == "__main__":
    main()