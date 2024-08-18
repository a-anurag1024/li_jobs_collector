from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

# Setup ChromeDriver path and options
chrome_driver_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"  # Change this to your chromedriver path
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-blink-features")
options.add_argument("--disable-blink-features=AutomationControlled")

service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# LinkedIn Job Search URL
base_url = "https://www.linkedin.com/jobs/search?keywords=Data%2BScientist&location=India&trk=public_jobs_jobs-search-bar_search-submit&currentJobId=3983495628&position=1&pageNum=0&original_referer=https%3A%2F%2Fwww.linkedin.com%2Fjobs%2Fsearch%3Fkeywords%3DData%252BScientist%26location%3DIndia%26trk%3Dpublic_jobs_jobs-search-bar_search-submit%26currentJobId%3D3970018098%26position%3D3%26pageNum%3D2"

# Function to scrape job listings
def scrape_linkedin_jobs():
    driver.get(base_url)
    time.sleep(2)  # Allow the page to load
    
    jobs = []
    while True:
        job_cards = driver.find_elements(By.CLASS_NAME, "result-card__contents")
        for card in job_cards:
            try:
                title = card.find_element(By.CLASS_NAME, "result-card__title").text
                company = card.find_element(By.CLASS_NAME, "result-card__subtitle").text
                location = card.find_element(By.CLASS_NAME, "job-result-card__location").text
                link = card.find_element(By.CSS_SELECTOR, "a.result-card__full-card-link").get_attribute('href')
                
                job_info = {
                    "Title": title,
                    "Company": company,
                    "Location": location,
                    "Link": link
                }
                
                jobs.append(job_info)
                print(f"Scraped: {title} at {company}, {location}")

            except Exception as e:
                print(f"Error extracting job card: {e}")
        
        # Move to the next page
        try:
            next_button = driver.find_element(By.CLASS_NAME, "artdeco-pagination__button--next")
            if "disabled" in next_button.get_attribute("class"):
                break  # Exit if no more pages
            next_button.click()
            time.sleep(2)  # Wait for the next page to load
        except Exception as e:
            print(f"Error navigating to the next page: {e}")
            break

    driver.quit()
    return jobs

# Run the scraper
jobs_list = scrape_linkedin_jobs()
print(f"Extracted {len(jobs_list)} job listings")

# Save to CSV
df = pd.DataFrame(jobs_list)
df.to_csv('linkedin_jobs.csv', index=False)

print("Job listings saved to linkedin_jobs.csv")
