import time
import logging
from datetime import datetime
import os
import re
import random
import threading
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


from blackhatworld_config import setup_logger  
from Multilogin_manager import PROFILES, signin, refresh_token, start_profile, stop_profile, perform_random_action   
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
) 

# Import configuration variables
from blackhatworld_config import (
    LOG_DIRECTORY,
    AUTOMATION_WAIT_TIME,
    start_time,
    run_duration
)

# --- Main Execution Function (for each profile) ---
def process_profile(profile_name, profile_config, manager_logger, start_time, run_duration):
    # Initialize logger *outside* the loop, for the profile itself
    profile_logger, profile_log_file = setup_logger(LOG_DIRECTORY, profile_name)
    profile_logger.info(f"Starting automation for profile: {profile_name}")

    token = None
    token_expiration_time = 0
    driver = None

    try:
        # 1. MultiLogin Authentication and Profile Start
        token, token_expiration_time = signin(profile_name, profile_config, profile_logger)
        if not token:
            profile_logger.error(f"Failed to sign in to MultiLogin profile: {profile_name}. Skipping.")
            return  # Exit the function, which will stop the thread

        driver = start_profile(profile_name, profile_config, token, profile_logger)
        if not driver:
            profile_logger.error(f"Failed to start MultiLogin profile: {profile_name}. Skipping.")
            return  # Exit the function, which will stop the thread

        # *** MAIN AUTOMATION LOGIC HERE ***
        automation_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        api_comments_dir = "Thread-Details/API Comments"
        thread_content_dir = "Thread-Details/Thread Content"
        visited_threads = load_visited_threads(profile_logger)  # Load visited threads at the start  # Use task logger
        if visited_threads:
            profile_logger.info(f"Successfully loaded links that was already visited!")   # Use task logger

        while True:

            profile_logger, profile_log_file = setup_logger(LOG_DIRECTORY, profile_name)

            if datetime.now() - start_time > run_duration:
                profile_logger.info("Automation has reached the time limit. Stopping execution.")
                break

            try:
                current_time = time.time()
                profile_logger.info(f"Current time: {current_time}")

                # is_expired = current_time >= token_expiration_time - 60
                # profile_logger.info(f"Token expiration check: {is_expired}")

                # if time.time() >= token_expiration_time - 60:
                #     # Log token refresh attempt
                #     profile_logger.info("Token is near expiration. Refreshing token...")

                #     # Attempt to refresh the token
                #     token, token_expiration_time = signin(profile_name, profile_config, profile_logger)  # Refresh Token!
                #     if not token:
                #         profile_logger.error("Failed to refresh token.  Exiting...")
                #         break  # Exit if refresh fails

                #     # Log the successful token refresh
                #     profile_logger.info("Token refreshed successfully.")

                if current_time >= token_expiration_time - 60:
                    profile_logger.info("Token is about to expire. Refreshing...")
                    token, token_expiration_time = refresh_token(profile_name, profile_config, profile_logger)
                    if not token:
                        profile_logger.error("Failed to refresh token. Exiting...")
                        break
                    profile_logger.info("Token refreshed successfully.")
                    profile_logger.info(f"New token expiration time: {token_expiration_time}")

                profile_logger.info(f"Token expiration time: {token_expiration_time}")

                # Log token expiration time
                profile_logger.info(f"Token expiration time: {token_expiration_time}")

                # PERFORM RANDOM ACTION
                perform_random_action(driver, profile_logger, profile_name)
                profile_logger.info("performing random action")

                subforum_urls = get_subforum_list(profile_logger) # Use task logger
                if not subforum_urls:
                    profile_logger.critical("No subforum URLs found in the file. Exiting.") # Use task logger
                    break  # Exit the loop, effectively stopping the profile's automation

                # PERFORM RANDOM ACTION
                #perform_random_action(driver, profile_logger, profile_name)

                scroll_random_times(profile_logger, driver) # Use task logger

                # Select and navigate a random thread to specific subforum
                subforum_url = random.choice(subforum_urls)
                scroll_random_times(profile_logger, driver) # Use task logger
                thread_link = find_random_thread_link_from_subforum(profile_logger,driver, subforum_url,visited_threads)  # Use task logger

                # PERFORM RANDOM ACTION
                perform_random_action(driver, profile_logger, profile_name)
                profile_logger.info("performing random action")

                if thread_link:
                    time.sleep(random.uniform(2, 3))
                    driver.get(thread_link)
                    time.sleep(random.uniform(2, 3))
                    profile_logger.info(f"Navigated to random thread: {thread_link}") # Use task logger
                    visited_threads.add(thread_link)
                    save_visited_thread(profile_logger, thread_link)  # Use task logger
                else:
                    profile_logger.warning(
                        "Skipping thread processing due to no thread link being found in subforum."
                    ) # Use task logger
                    continue  # Skip to next subforum

                # Extract thread title
                thread_title = get_thread_title(profile_logger, driver) # Use task logger

                # PERFORM RANDOM ACTION
                #perform_random_action(driver, profile_logger, profile_name)

                scroll_random_times(profile_logger, driver, min_scrolls=2, max_scrolls=4, scroll_delay=2) # Use task logger
                time.sleep(random.uniform(2, 3))

                like_random_posts(
                    profile_logger, driver,
                    min_likes=1,
                    max_likes=4,
                    min_scrolls_posts=1,
                    max_scrolls_posts=4,
                    scroll_delay=3,
                ) # Use task logger

                time.sleep(random.uniform(2,3))

                # PERFORM RANDOM ACTION
                perform_random_action(driver, profile_logger, profile_name)
                profile_logger.info("performing random action")

                scroll_random_times(profile_logger, driver, min_scrolls=3, max_scrolls=7, scroll_delay=3) # Use task logger
                time.sleep(random.uniform(2, 3))


                # save thread content
                thread_content_file = os.path.join(
                    thread_content_dir, f"{thread_title}.txt"
                )
                extract_post_content(profile_logger, driver, thread_content_file) # Use task logger
                profile_logger.info(f"Post content extracted and saved to {thread_content_file}") # Use task logger
                time.sleep(random.uniform(2, 3))

                # PERFORM RANDOM ACTION
                #perform_random_action(driver, profile_logger, profile_name)

                main_post_content = extract_main_post_content(profile_logger, driver) # Use task logger
                time.sleep(random.uniform(2, 3))

                # generate and save comment
                if main_post_content:
                    comment = generate_and_save_comments(profile_logger,
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
                            profile_logger.warning(
                                f"rename Error: {e}", exc_info=True
                            ) # Use task logger
                            profile_logger.info(f"API comment generated and saved to {api_comment_file}") # Use task logger
                    else:
                        profile_logger.warning("Failed to generate comment, skipping saving.")  # Use task logger

                # Read the generated comment
                comment_file = os.path.join(
                    api_comments_dir, f"{thread_title}_{sanitized_comment}.txt"
                )
                comment = read_thread_content(profile_logger, comment_file) # Use task logger
                time.sleep(random.uniform(2, 3))

                # PERFORM RANDOM ACTION
                perform_random_action(driver, profile_logger, profile_name)
                profile_logger.info("performing random action")

                if comment:
                    post_comment(profile_logger, driver, comment, write_delay=3) # Use task logger
                    profile_logger.info("Comment posted successfully.")  # Use task logger
                else:
                    profile_logger.warning("No comment available to post.")  # Use task logger

                profile_logger.info("Task Completed!!") # Use task logger
                # 1.5) Added code to go back to HOME

                # navigate back to home after automation
                navigate_home(profile_logger, driver) # Use task logger

            except Exception as e:
                try:
                    profile_logger.error(f"An error occurred: {e}", exc_info=True) # Use task logger
                except NameError:
                    profile_logger.error(f"A task error occurred before task_logger was initialized: {e}", exc_info=True)

                # clear the memory and wait from next automation
            clear_memory(profile_logger)  # Use task logger
            profile_logger.info(f"Waiting for {AUTOMATION_WAIT_TIME} seconds before next execution.")  # Use task logger
            time.sleep(AUTOMATION_WAIT_TIME)

            print("\n\n\n\n")

    except Exception as e:
        profile_logger.critical(f"An error occurred with profile {profile_name}: {e}", exc_info=True)

    finally:
        # 3. MultiLogin Profile Stop
        if driver:
            try:
                profile_logger.info(f"Stopping browser for profile: {profile_name}...")

                # *** REFRESH TOKEN IMMEDIATELY BEFORE STOPPING ***
                profile_logger.info("Refreshing token before stopping profile...")
                token, token_expiration_time = refresh_token(profile_name, profile_config, profile_logger)
                if not token:
                    profile_logger.error("Failed to refresh token before stopping.  Attempting to stop anyway...")
                else:
                    profile_logger.info("Token refreshed successfully before stopping.")

                stop_profile(profile_name, profile_config, token, profile_logger, driver, max_retries=3, retry_delay=2)  # Pass driver to stop_profile
                profile_logger.info(f"Browser stopped successfully for profile: {profile_name}.")

            except Exception as e:
                profile_logger.warning(f"Error stopping profile for {profile_name}: {e}", exc_info=True)

        else:
            profile_logger.warning(f"Driver was not initialized for {profile_name}.  Skipping stop_profile.")

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
    manager_logger = logging.getLogger("Manager")
    manager_logger.setLevel(logging.INFO)  # Set level for manager logger
    manager_logger.addHandler(console_handler)  # Add console handler

    # Create and start a thread for each profile
    profile_names = list(PROFILES.keys())
    start_time = datetime.now()

    for i, profile_name in enumerate(profile_names):
        profile_config = PROFILES[profile_name]

        # Stagger the start times
        if i > 0:
            delay_minutes = random.uniform(1, 3)  # Use values from `Multilogin_manager.py` or define them here
            delay_seconds = delay_minutes * 60
            manager_logger.info(f"Waiting {delay_minutes:.2f} minutes before starting profile {profile_name}...")
            time.sleep(delay_seconds)

        thread = threading.Thread(target=process_profile, args=(profile_name, profile_config, manager_logger, start_time, run_duration))
        threads.append(thread)
        thread.start()


    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("Automation completed for all profiles.")