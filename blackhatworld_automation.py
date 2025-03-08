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

from blackhatworld_config import setup_logger  # Import logger setup
from Multilogin_manager import PROFILES, signin, start_profile, stop_profile  # Import Multilogin functions
from blackhatworld_functions import (
    get_subforum_list,
    load_visited_threads,
    save_visited_thread,
    scroll_random_times,
    find_random_thread_link_from_subforum,
    get_thread_title,
    like_random_posts,
    extract_post_content,
    extract_main_post_content,
    generate_and_save_comments,
    read_thread_content,
    post_comment,
    navigate_home,
    clear_memory
) # Import functions from Blackhatworld-functions.py

# Import configuration variables
from blackhatworld_config import (
    LOG_DIRECTORY,
    AUTOMATION_WAIT_TIME,
    start_time,
    run_duration
)

# --- Main Execution Function (for each profile) ---
def process_profile(profile_name, profile_config):
    # Initialize logger *outside* the loop, for the profile itself
    profile_logger, profile_log_file = setup_logger(LOG_DIRECTORY, profile_name)
    profile_logger.info(f"Starting automation for profile: {profile_name}")

    token = None
    driver = None

    try:
        # 1. MultiLogin Authentication and Profile Start
        token = signin(profile_name, profile_config, profile_logger)
        if not token:
            profile_logger.error(f"Failed to sign in to MultiLogin profile: {profile_name}. Skipping.")
            return  # Exit the function, which will stop the thread

        driver = start_profile(profile_name, profile_config, token, profile_logger)
        if not driver:
            profile_logger.error(f"Failed to start MultiLogin profile: {profile_name}. Skipping.")
            return  # Exit the function, which will stop the thread

        # *** MAIN AUTOMATION LOGIC HERE ***
        while True:
            
            if datetime.now() - start_time > run_duration:
                task_logger.info("Automation has reached the time limit. Stopping execution.")
                break

            # ---- NEW LOGGER FOR EACH TASK ----
            automation_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            task_logger, task_log_file = setup_logger(LOG_DIRECTORY, profile_name, automation_timestamp)  # New logger
            task_logger.info(f"Starting new automation task. Log file created at: {task_log_file}") # Use task logger


            try:
                subforum_urls = get_subforum_list(task_logger) # Use task logger
                if not subforum_urls:
                    task_logger.critical("No subforum URLs found in the file. Exiting.") # Use task logger
                    break  # Exit the loop, effectively stopping the profile's automation

                visited_threads = load_visited_threads(task_logger)  # Load visited threads at the start  # Use task logger
                if visited_threads:
                    task_logger.info(f"Successfully loaded links that was already visited!")   # Use task logger

                scroll_random_times(task_logger, driver) # Use task logger

                # Select and navigate a random thread to specific subforum
                subforum_url = random.choice(subforum_urls)
                scroll_random_times(task_logger, driver) # Use task logger
                thread_link = find_random_thread_link_from_subforum(task_logger,driver, subforum_url,visited_threads)  # Use task logger

                if thread_link:
                    time.sleep(random.uniform(2, 3))
                    driver.get(thread_link)
                    time.sleep(random.uniform(2, 3))
                    task_logger.info(f"Navigated to random thread: {thread_link}") # Use task logger
                    visited_threads.add(thread_link)
                    save_visited_thread(task_logger, thread_link)  # Use task logger
                else:
                    task_logger.warning(
                        "Skipping thread processing due to no thread link being found in subforum."
                    ) # Use task logger
                    continue  # Skip to next subforum

                # Extract thread title
                thread_title = get_thread_title(task_logger, driver) # Use task logger

                scroll_random_times(task_logger, driver, min_scrolls=2, max_scrolls=4, scroll_delay=2) # Use task logger
                time.sleep(random.uniform(2, 3))

                like_random_posts(
                    task_logger, driver,
                    min_likes=1,
                    max_likes=4,
                    min_scrolls_posts=1,
                    max_scrolls_posts=4,
                    scroll_delay=3,
                ) # Use task logger

                scroll_random_times(task_logger, driver, min_scrolls=3, max_scrolls=7, scroll_delay=3) # Use task logger
                time.sleep(random.uniform(2, 3))

                # save thread content
                thread_content_dir = "Thread-Details/Thread Content"  # Moved inside try block
                thread_content_file = os.path.join(
                    thread_content_dir, f"{thread_title}.txt"
                )
                extract_post_content(task_logger, driver, thread_content_file) # Use task logger
                task_logger.info(f"Post content extracted and saved to {thread_content_file}") # Use task logger
                time.sleep(random.uniform(2, 3))

                main_post_content = extract_main_post_content(task_logger, driver) # Use task logger
                time.sleep(random.uniform(2, 3))

                # generate and save comment
                if main_post_content:
                    api_comments_dir = "Thread-Details/API Comments" # Moved inside try block
                    comment = generate_and_save_comments(task_logger,
                        main_post_content,
                        os.path.join(api_comments_dir, "temp_comment.txt"),
                    ) # Use task logger
                    if comment:
                        sanitized_comment = re.sub(r'[\\/*?:"<>|]', "", comment[:50])
                        api_comment_file = os.path.join(
                            api_comments_dir, f"{thread_title}_{sanitized_comment}.txt"
                        )
                        try:
                            os.rename(
                                os.path.join(api_comments_dir, "temp_comment.txt"),
                                api_comment_file,
                            )
                        except Exception as e:
                            task_logger.warning(
                                f"rename Error: {e}", exc_info=True
                            ) # Use task logger
                            task_logger.info(f"API comment generated and saved to {api_comment_file}") # Use task logger
                    else:
                        task_logger.warning("Failed to generate comment, skipping saving.")  # Use task logger

                # Read the generated comment
                comment_file = os.path.join(
                    api_comments_dir, f"{thread_title}_{sanitized_comment}.txt"
                )
                comment = read_thread_content(task_logger, comment_file) # Use task logger
                time.sleep(random.uniform(2, 3))

                if comment:
                    post_comment(task_logger, driver, comment, write_delay=3) # Use task logger
                    task_logger.info("Comment posted successfully.")  # Use task logger
                else:
                    task_logger.warning("No comment available to post.")  # Use task logger

                task_logger.info("Task Completed!!") # Use task logger
                # 1.5) Added code to go back to HOME

                # navigate back to home after automation
                navigate_home(task_logger, driver) # Use task logger

            except Exception as e:
                task_logger.error(f"An error occurred: {e}", exc_info=True) # Use task logger

            
                # clear the memory and wait from next automation
            clear_memory(task_logger)  # Use task logger
            task_logger.info(f"Waiting for {AUTOMATION_WAIT_TIME} seconds before next execution.")  # Use task logger
            time.sleep(AUTOMATION_WAIT_TIME)
            # -- Remove handler to log in new files --
            for handler in task_logger.handlers[:]:
                task_logger.removeHandler(handler)
                handler.close()

    except Exception as e:
        profile_logger.critical(f"An error occurred with profile {profile_name}: {e}", exc_info=True)

    finally:
        # 3. MultiLogin Profile Stop
        if driver:
            try:
                profile_logger.info(f"Stopping browser for profile: {profile_name}...")
                stop_profile(profile_name, profile_config, token, profile_logger, driver)  # Pass driver to stop_profile
                profile_logger.info(f"Browser stopped successfully for profile: {profile_name}.")

            except Exception as e:
                profile_logger.warning(f"Error stopping profile for {profile_name}: {e}", exc_info=True)

# --- Main Execution Loop (with Threading) ---
if __name__ == "__main__":
    # find directories

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    threads = []  # List to store the threads

    # Create and start a thread for each profile
    for profile_name, profile_config in PROFILES.items():
        thread = threading.Thread(target=process_profile, args=(profile_name, profile_config))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("Automation completed for all profiles.")