from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import random

# Path to your ChromeDriver
chrome_driver_path = "/path/to/your/chromedriver"  # Update this path

# Set up Chrome options
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-blink-features=AutomationControlled")

# Initialize the WebDriver
#service = Service(executable_path=chrome_driver_path)
service = Service()
driver = webdriver.Chrome(service=service, options=options)

# Navigate to the job search page
job_url = "https://www.linkedin.com/jobs/search?keywords=Data%2BScientist&location=India&trk=public_jobs_jobs-search-bar_search-submit&currentJobId=3983495628&position=1&pageNum=0&original_referer=https%3A%2F%2Fwww.linkedin.com%2Fjobs%2Fsearch%3Fkeywords%3DData%252BScientist%26location%3DIndia%26trk%3Dpublic_jobs_jobs-search-bar_search-submit%26currentJobId%3D3975347333%26position%3D2%26pageNum%3D0"
driver.get(job_url)

# Function to simulate human-like scrolling behavior
def slow_human_like_scroll():
    current_scroll_position = 0
    scroll_increment = random.randint(200, 400)  # Scroll a random distance between 200 and 400 pixels

    while True:
        # Scroll by small increments
        driver.execute_script(f"window.scrollTo(0, {current_scroll_position});")
        current_scroll_position += scroll_increment
        
        # Random pauses to mimic human scrolling behavior
        time.sleep(random.uniform(0.05, 0.5))  # Wait between 1.5 and 3 seconds

        # Try to click the "See more jobs" button if it exists
        try:
            see_more_button = driver.find_element(By.XPATH, "//button[contains(@class, 'infinite-scroller__show-more-button')]")
            if see_more_button.is_displayed():
                see_more_button.click()
                print("Clicked 'See more jobs' button.")
                time.sleep(random.uniform(12, 14))  # Wait for new jobs to load after clicking
        except Exception as e:
            print("No 'See more jobs' button found or error occurred:", e)
            # wait for loading of new jobs
            time.sleep(random.uniform(12, 24))

        # Break the loop if we've reached the bottom of the page
        new_scroll_height = driver.execute_script("return document.body.scrollHeight")
        if current_scroll_position >= new_scroll_height:
            time.sleep(random.uniform(12, 24))
            new_scroll_height = driver.execute_script("return document.body.scrollHeight")
            if current_scroll_position >= new_scroll_height:
                print("Reached the bottom of the page.")
                break

# Run the slow scrolling function
slow_human_like_scroll()

# Save the final page as an HTML file
with open("linkedin_jobs_page.html", "w", encoding="utf-8") as file:
    file.write(driver.page_source)
    print("Saved the page as 'linkedin_jobs_page.html'")

# Close the WebDriver
driver.quit()
