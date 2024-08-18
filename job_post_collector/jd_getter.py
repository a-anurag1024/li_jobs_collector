from dataclasses import dataclass, field 
import requests
import re
import os
import time
from pathlib import Path
from bs4 import BeautifulSoup
import logging
from tqdm import tqdm

from job_post_collector.db import DB


@dataclass 
class JD_GetterConfig:
    
    wait_time: int = 1  # Wait time between each job post collection
    
    # retry parameters
    max_retries: int = 3
    retry_wait_time: int = 5
    
    log_dir: str = "./mount/logs/jd_getter_logs"
    

class JD_Getter:
    def __init__(self, 
                 config: JD_GetterConfig,
                 db: DB):
        
        self.config = config
        self.db = db
        
        # setup loggers
        for agent in ['info', 'error']:
            logger = logging.getLogger(agent)
            logger.setLevel(logging.INFO if agent == 'info' else logging.WARNING)
            fh = logging.FileHandler(Path(os.path.join(self.config.log_dir, f"jd_getter_{agent}.log")))
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(fh)
            if agent == 'info':
                self.info_logger = logger
            else:
                self.error_logger = logger
            
        
    
    def extract_job_tags(self, soup: BeautifulSoup):
        details = {}
        
        # Look for specific labels
        labels_to_find = ["Seniority level", "Employment type", "Job function", "Industries"]
        
        for label in labels_to_find:
            # Find the label in the section
            label_element = soup.find("h3", string=re.compile(label))
            if label_element:
                # Find the next sibling containing the relevant data
                value_element = label_element.find_next("span")
                details[label] = value_element.get_text(strip=True) if value_element else "Not Found"
                if details[label] == "Not Found":
                    self.error_logger.warning(f"Value not found for {label} for {soup.find('link', rel='canonical')['href']}")

        return details


    def get_job_posts(self, job_url: str):
        
        response = requests.get(job_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        section = soup.find("div", class_="show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden")
        
        if section:
            # Extract heading-tagged content
            
            job_description = section.get_text()

            # Extract job-related details
            job_details = self.extract_job_tags(soup)
            
            return {"job_description": job_description, **job_details}
        else:
            self.error_logger.error(f"Job post not found at {job_url}")
            raise ValueError(f"Job post not found at {job_url}")
        
        
    def run(self):
        while True:
            self.info_logger.info("Starting job post collection")
            jobs_db = self.db.get_all_scrolled_jobs()
            for job_link, job_id in tqdm(jobs_db.values):
                retries = 0
                while not self.db.check_if_job_already_scraped(job_id) and retries < self.config.max_retries:
                    try:
                        job_data_ret = self.get_job_posts(job_link)
                        job_data = {"job_id": job_id, "job_link": job_link}
                        job_data['job_description'] = job_data_ret['job_description']
                        job_data['seniority_level'] = job_data_ret.get('Seniority level', 'Not Found')
                        job_data['employment_type'] = job_data_ret.get('Employment type', 'Not Found')
                        job_data['job_function'] = job_data_ret.get('Job function', 'Not Found')
                        job_data['industries'] = job_data_ret.get('Industries', 'Not Found')
                        self.db.insert_job(job_data)
                        self.info_logger.info(f"Job post collected for {job_id}")
                    except Exception as e:
                        retries += 1
                        error_tag = e if isinstance(e, str) else str(e)
                        time.sleep(self.config.retry_wait_time)
                        
                if retries >= self.config.max_retries:    
                    self.error_logger.error(f"Error collecting job post for {job_id}: {error_tag}")
                        
                else:
                    continue
                    
                time.sleep(self.config.wait_time)
            else:
                self.info_logger.info("All job posts collected")
                break