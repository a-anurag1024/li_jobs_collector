from pathlib import Path
import json
from datetime import datetime

from job_post_collector.jd_getter import JD_GetterConfig, JD_Getter
from job_post_collector.db import DB, DB_Creds


def main():
    creds = DB_Creds(
        host = "localhost",
        port = '3306',
        user = "local",
        password = "local",
        database = "jobs_data"
    )
    
    db = DB(creds)
        
    
    config = JD_GetterConfig()
    
    jd_getter = JD_Getter(config, db)
        
    jd_getter.run()
    
if __name__ == "__main__":
    main()