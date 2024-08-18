from pathlib import Path
import json
from datetime import datetime

from job_post_collector.job_scroller import SearchConfig, JobScroller
from job_post_collector.db import DB, DB_Creds


search_config_file = Path("./mount/search_configs/config_1_monthly.json")

def main():
    creds = DB_Creds(
        host = "localhost",
        port = '3306',
        user = "local",
        password = "local",
        database = "jobs_data"
    )
    
    db = DB(creds)
    
    with open(search_config_file, 'r') as f:
        search_config = json.load(f)
        
    for config in search_config["searches"]:
        
        search_term = config["search_term"]
        location = config["location"]
        last_how_many_days = config["last_how_many_days"]
        print(f" ||>> Running search for {search_term} in {location} for the last {last_how_many_days} days")
    
        config = SearchConfig(
            search_id=f"{search_term}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}",
            Keywords=search_term.replace(" ", "+"),
            Location=location,
            Time=last_how_many_days*86400
        )
    
        Scroller = JobScroller(config, db)
        
        Scroller.run()
    
if __name__ == "__main__":
    main()