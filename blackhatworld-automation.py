from selenium import webdriver 
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument('disable-infobars')
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
driver.get(url = "https://www.blackhatworld.com/forums/blogging.3/")


scroll_duration = 3  # shows total time spending on scrolling
start_time = time.time() #records the current time when the scrolling starts.
while(time.time() - start_time) < scroll_duration: # The while loop control the duration of scrolling
#The current time will notice from the time scrolling starts which should not be more than 3 seconds
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)# this line finds the body by tag name selector and pressing the END key to the page to scroll down
    time.sleep(2) #makes the program wait for 2 seconds before continuing the loop.

time.sleep(3)
driver.close()