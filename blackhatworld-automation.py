from selenium import webdriver 
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random #import random module for generating random numbers.
import time

options = Options()
options.add_argument('disable-infobars')
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
options.add_experimental_option('useAutomationExtension', False)

user_data = r"C:\Users\DELL\AppData\Local\Google\Chrome\User Data"  # profile path using raw string
profile_name = "Profile 37"  #profile name

options.add_argument(f"user-data-dir={user_data}")  #instructs selenium to start chrome with user_data path.
driver = webdriver.Chrome(options=options)
driver.get("https://www.blackhatworld.com/")

#Randomized Delays and Pauses:
link = driver.find_element(By.LINK_TEXT, "Main Forum List")
time.sleep(random.uniform(0.5, 2)) #Adding random pauses makes automated script appear more natural
#random.uniform():a function from the random module used to generate a random floating-point number between two given values.
link.click() #clicking on the element

#Human-like Scrolling
def scroll_down(driver):
 for _ in range(13): # Scroll  times for this example
  driver.execute_script("window.scrollBy(0,600);")
  time.sleep(random.uniform(1.5,2))
scroll_down(driver)

time.sleep(4)
driver.quit()
