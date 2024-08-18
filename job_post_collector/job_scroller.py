from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import random
import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import pandas as pd

from job_post_collector.db import DB



@dataclass
class SearchConfig:
    
    search_id: str
    
    Keywords: str = "Data Scientist"
    Location: str = "India"
    Time: int = "86400" # last how many seconds results to search (default 1 day (86400 seconds))
    max_jobs: int = 400 # Maximum number of jobs to collect
    
    base_url: str = "https://www.linkedin.com/jobs/search?"
    
    save_every: int = 10 # Save the results every 10 scroll iterations
    base_save_dir: str = "./mount/scrape_scroll_saves"
    
    @property
    def get_url(self):
        return f"{self.base_url}keywords={self.Keywords}&location={self.Location}&f_TPR=r{self.Time}"
    
    @property
    def save_file(self) -> Path: 
        return Path(os.path.join(self.base_save_dir, f"{self.search_id}.html"))
    
    
    
class JobScroller:
    def __init__(self, 
                 config: SearchConfig,
                 db: DB):
        
        self.config = config
        self.db = db
        self.added_jobs_ids = []
        
        # setup the chrome driver
        self.driver = self._get_chrome_driver()
        
        # setup the logger
        fh = logging.FileHandler(Path(f'./mount/logs/scroller_logs/{self.config.search_id}.log'))
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger = logging.getLogger('job_scroller')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fh)
        
        self.logger.info(f"Job Scroller initialized for search_id: {self.config.search_id}")
        
        
    def _get_chrome_driver(self):
        options = Options()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        
        return driver
    
    
    def save_results(self):
        with open(self.config.save_file, "w", encoding="utf-8") as file:
            file.write(self.driver.page_source)
        self.logger.info(f"Results saved to {self.config.save_file}")
            
    
    def slow_human_like_scroll(self):
        current_scroll_position = 0
        scroll_increment = random.randint(200, 400)  # Scroll a random distance between 200 and 400 pixels
        scroll_no = 0
        
        while True:
            # Scroll by small increments
            self.driver.execute_script(f"window.scrollTo(0, {current_scroll_position});")
            current_scroll_position += scroll_increment
            
            # Random pauses to mimic human scrolling behavior
            time.sleep(random.uniform(0.05, 0.5))  # Wait between 1.5 and 3 seconds

            # Try to click the "See more jobs" button if it exists
            try:
                see_more_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'infinite-scroller__show-more-button')]")
                if see_more_button.is_displayed():
                    see_more_button.click()
                    self.logger.info("Clicked 'See more jobs' button.")
                    time.sleep(random.uniform(12, 14))  # Wait for new jobs to load after clicking
            except Exception as e:
                self.logger.warning("No 'See more jobs' button found or error occurred:", e)
                raise e
                # wait for loading of new jobs
                time.sleep(random.uniform(12, 24))

            # Break the loop if we've reached the bottom of the page
            new_scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            if current_scroll_position >= new_scroll_height:
                time.sleep(random.uniform(12, 24))
                new_scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                if current_scroll_position >= new_scroll_height:
                    self.logger.warning("Reached the bottom of the page.")
                    break
            
            # Break the loop if max number of jobs collected
            if len(self.added_jobs_ids) >= self.config.max_jobs:
                self.logger.warning("Max number of jobs collected. Stopping the scroller.")
                break
            
            # Save the results every n scroll iterations
            scroll_no += 1
            if scroll_no % self.config.save_every == 0:
                self.save_results()
                jobs_df = self.scrape_job_info_from_html()
                self.save_to_db(jobs_df)
                
                
    def scrape_job_info_from_html(self) -> pd.DataFrame:
        
        with open(self.config.save_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, 'html.parser')
            
        # Lists to store job data
        job_titles = []
        companies = []
        locations = []
        post_times = []
        links = []
        job_ids = []

        # Attempting to find all job listings by targeting the appropriate divs
        job_cards = soup.find_all("div", class_="base-card")

        # Extract information from each job card
        for card in job_cards:
            # Extract job title
            title_tag = card.find("h3", class_="base-search-card__title")
            title = title_tag.text.strip() if title_tag else "N/A"
            
            # Extract company name
            company_tag = card.find("h4", class_="base-search-card__subtitle")
            company = company_tag.text.strip() if company_tag else "N/A"
            
            # Extract job location
            location_tag = card.find("span", class_="job-search-card__location")
            location = location_tag.text.strip() if location_tag else "N/A"
            
            # Extract time of posting
            post_time_tag = card.find("time")
            post_time = post_time_tag.text.strip() if post_time_tag else "N/A"
            
            # Extract job link
            link_tag = card.find("a", class_="base-card__full-link")
            link = link_tag['href'].strip() if link_tag else "N/A"
            
            # Append data to lists
            job_titles.append(title)
            companies.append(company)
            locations.append(location)
            post_times.append(post_time)
            links.append(link)
            job_ids.append(link.split("https://in.linkedin.com/jobs/view/")[-1].split("?")[0])

        # Create a DataFrame
        jobs_df = pd.DataFrame({
            "job_title": job_titles,
            "company": companies,
            "location": locations,
            "time_of_posting": post_times,
            "job_link": links,
            "job_id": job_ids,
            "search_keyword": self.config.Keywords,
            "search_location": self.config.Location
        })
                    
        self.logger.info(f"Scraped {len(job_cards)} job listings in total till now.")
        
        return jobs_df
    
    
    def save_to_db(self, jobs_df: pd.DataFrame):
        for _, row in jobs_df.iterrows():
            if row['job_id'] in self.added_jobs_ids:
                continue
            self.db.insert_scrolled_job(row.to_dict())
            self.added_jobs_ids.append(row['job_id'])
            
        self.logger.info(f"Scraped job listings saved to database.")
        
        
    def run(self):
        
        while True:
            try:
                self.logger.info(f"Starting the job scroller for search_id: {self.config.search_id} and url: {self.config.get_url}")
                self.driver.get(self.config.get_url)
                self.slow_human_like_scroll()
                
                self.save_results()
                jobs_df = self.scrape_job_info_from_html()
                self.save_to_db(jobs_df)
                self.logger.info(f"Job Scroller ended for search_id: {self.config.search_id}. Added {len(self.added_jobs_ids)} jobs.")
                break
            except Exception as e:
                self.logger.error(f"Error occurred during scroller run: {e}")
                self.driver = self._get_chrome_driver()
            