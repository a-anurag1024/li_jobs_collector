from pathlib import Path
import json

from job_post_collector.collector_old import JobPostsCollector, CollectorConfig
from job_post_collector.db import DB, DB_Creds

account_name = "adityaanurag75@gmail.com"

accounts_detail_filepath = Path("./secrets/li_accounts.json")
with open(accounts_detail_filepath, 'r') as file:
    accounts_detail = json.load(file)


def main():
    creds = DB_Creds(
        host = "localhost",
        port = '3306',
        user = "local",
        password = "local",
        database = "jobs_data"
    )
    
    db = DB(creds)
    
    config = CollectorConfig(
        account_name=account_name,
        account_cookie=accounts_detail[account_name],
        query='data-science-jobs',
    )
    
    collector = JobPostsCollector(config, db)
    
    collector.launch_scrapper()
    
if __name__ == "__main__":
    main()