from selenium import webdriver 
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument('disable-infobars')
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
options.add_experimental_option('useAutomationExtension', False)

user_data = r"C:\Users\DELL\AppData\Local\Google\Chrome\User Data"  # profile path using raw string
profile_name = "Profile 37"  #profile name

options.add_argument(f"user-data-dir={user_data}")  #instructs selenium to start chrome with user_data path.
#options.add_argument(f"profile-directory={profile}")  #instructs selenium to tell chrome to use the Profile 37 in user_data path.

driver = webdriver.Chrome(options=options)
driver.get("https://www.blackhatworld.com/forums/content-copywriting.194/")

scroll_duration = 3  # shows total time spending on scrolling
start_time = time.time() #records the current time when the scrolling starts.

while(time.time() - start_time) < scroll_duration: # The while loop control the duration of scrolling
#The current time will notice from the time scrolling starts which should not be more than 3 seconds
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)# this line finds the body by tag name selector and pressing the END key to the page to scroll down
    time.sleep(2) #makes the program wait for 2 seconds before continuing the loop.

time.sleep(3)
driver.close()
