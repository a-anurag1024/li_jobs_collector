from dataclasses import dataclass, field 
from typing import List
import os
from pathlib import Path

import logging
from logging.handlers import RotatingFileHandler

from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.linkedin_scraper import Config
from linkedin_jobs_scraper.events import Events, EventData, EventMetrics
from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
from linkedin_jobs_scraper.filters import RelevanceFilters, TimeFilters, TypeFilters, ExperienceLevelFilters, OnSiteOrRemoteFilters, SalaryBaseFilters
    
from job_post_collector.db import DB
    
@dataclass
class CollectorConfig:
    
    account_name: str
    account_cookie: str
    query: str
    
    # Default Scrapper parameters
    max_workers: int = 1
    slow_mo: float = 1
    page_load_timeout: int = 400    # Page load timeout (in seconds)
    
    # Default QueryOptions
    locations: List[str] = field(default_factory=lambda: ['india'])
    apply_link: bool = True
    skip_promoted_jobs: bool = False
    page_offset: int = 0
    limit: int = 50
    query_filters: QueryFilters = None  # Check the py-linkedin-jobs-scraper documentation for more details
    
    
    
class JobPostsCollector:
    def __init__(self, 
                 config: CollectorConfig,
                 db: DB):
        
        self.config = config
        self.db = db
        
        # logger
        fh = RotatingFileHandler(Path(f'./mount/logs/{self.config.query}.log'), maxBytes=10*1024*1024, backupCount=5e10)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        
        self.data_logger = logging.getLogger('data')
        self.data_logger.setLevel(logging.INFO)
        self.data_logger.addHandler(fh)
        
        self.error_logger = logging.getLogger('error')
        self.error_logger.setLevel(logging.ERROR)
        self.error_logger.addHandler(fh)        
        
        # log account name
        self.data_logger.info(f"====Scrapper started for {self.config.account_name}====")
        
        # initialize scrapper
        self.scrapper = None
        self.cookie_num = 0
        self._initialize_scrapper()
        
        # Add event listeners
        self.scraper.on(Events.DATA, self.on_data)
        self.scraper.on(Events.ERROR, self.on_error)
        self.scraper.on(Events.END, self.on_end)
        
        self.queries = [
            Query(
                query=self.config.query,
                options=QueryOptions(
                    locations=self.config.locations,
                    apply_link=self.config.apply_link,  # Try to extract apply link (easy applies are skipped). If set to True, scraping is slower because an additional page must be navigated. Default to False.
                    skip_promoted_jobs=self.config.skip_promoted_jobs,  # Skip promoted jobs. Default to False.
                    page_offset=self.config.page_offset,  # How many pages to skip
                    limit=self.config.limit
                )
            ),
        ]
    
    
    def _initialize_scrapper(self):
        
        # set account cookie
        if self.config.account_cookie[self.cookie_num % len(self.config.account_cookie)]: 
            os.environ['LI_AT_COOKIE'] = self.config.account_cookie[self.cookie_num % len(self.config.account_cookie)]
            self.cookie_num += 1
            Config.LI_AT_COOKIE = os.environ['LI_AT_COOKIE']
            self.data_logger.info(f"Using cookie: {os.environ['LI_AT_COOKIE']}")
        
        self.scraper = LinkedinScraper(
            chrome_executable_path=None,  # Custom Chrome executable path (e.g. /foo/bar/bin/chromedriver)
            chrome_binary_location=None,  # Custom path to Chrome/Chromium binary (e.g. /foo/bar/chrome-mac/Chromium.app/Contents/MacOS/Chromium)
            chrome_options=None,  # Custom Chrome options here
            headless=True,  # Overrides headless mode only if chrome_options is None
            max_workers=self.config.max_workers,  # How many threads will be spawned to run queries concurrently (one Chrome driver for each thread)
            slow_mo=self.config.slow_mo,  # Slow down the scraper to avoid 'Too many requests 429' errors (in seconds)
            page_load_timeout=self.config.page_load_timeout  # Page load timeout (in seconds)    
        )
        
        
    def on_data(self, data: EventData):
        entry = {
            'query': data.query,
            'query_location': data.location,
            'job_id': data.job_id,
            'link': data.link,
            'apply_link': data.apply_link,
            'title': data.title,
            'company': data.company,
            'company_link': data.company_link,
            'company_img_link': data.company_img_link,
            'place': data.place,
            'description': data.description,
            'description_html': data.description_html,
            'date': data.date,
            'insights': "||".join(data.insights) if data.insights else None,
            'skills': "||".join(data.skills) if data.skills else None
        }
        self.db.insert_job(entry)
        self.data_logger.info(f"job_title: {data.title}, company: {data.company}, location: {data.place}, description_len: {len(data.description)}")
        
        
    def on_error(self, error):
        self.error_logger.error(error)
        
        
    def on_end(self):
        self.data_logger.info("====Scrapper ended====")
        

    def launch_scrapper(self):
        
        while True:
            returns = self.scraper.run(self.queries)
            try:
                page_offset = int(returns[-1]['page_offset'])
                self.error_logger.error(f"Error: Session Invalidated... Restarting from offset: {page_offset}")
            except:
                page_offset = self.config.page_offset + 1
                self.config.page_offset = page_offset
                self.data_logger.info(f"Session ended... Restarting from offset: {page_offset}")
        
            self.data_logger.info(f"Session ended... Restarting from offset: {page_offset}")
            self._initialize_scrapper()             
            self.queries = [
                Query(
                    query=self.config.query,
                    options=QueryOptions(
                        locations=self.config.locations,
                        apply_link=self.config.apply_link,  # Try to extract apply link (easy applies are skipped). If set to True, scraping is slower because an additional page must be navigated. Default to False.
                        skip_promoted_jobs=self.config.skip_promoted_jobs,  # Skip promoted jobs. Default to False.
                        page_offset=page_offset,  # How many pages to skip
                        limit=self.config.limit
                    )
                ),
            ]