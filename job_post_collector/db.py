import mysql.connector as mysql
from dataclasses import dataclass 
from datetime import datetime
import json
import os
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import traceback


@dataclass 
class DB_Creds:
    
    host: str
    port: str
    user: str
    password: str
    database: str
    
    
class DB:
    def __init__(self, creds: DB_Creds):
        
        self.db = mysql.connect(
            host = creds.host,
            port = creds.port,
            user = creds.user,
            password = creds.password,
            database = creds.database
        )
        
        #self._create_jobs_old_table()
        self._create_jobs_table()
        self._create_scrolled_jobs_table()
        
    
    def _create_jobs_old_table(self):
        
        cursor = self.db.cursor()
        command = """
        CREATE TABLE IF NOT EXISTS jobs(
            entry_id INT AUTO_INCREMENT PRIMARY KEY,
            entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            query VARCHAR(255),
            query_location VARCHAR(255),
            job_id VARCHAR(255),
            link VARCHAR(2555),
            apply_link VARCHAR(2555),
            title VARCHAR(255),
            company VARCHAR(255),
            company_link VARCHAR(255),
            company_img_link VARCHAR(255),
            place VARCHAR(255),
            description TEXT,
            description_html TEXT,
            date VARCHAR(255),
            insights TEXT,
            skills TEXT
            )
            """
        cursor.execute(command)
        self.db.commit()
        cursor.close()
    
    
    def _create_jobs_table(self):
        
        cursor = self.db.cursor()
        command = """
        CREATE TABLE IF NOT EXISTS jobs(
            entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            job_id VARCHAR(255) PRIMARY KEY,
            job_link VARCHAR(2555),
            job_description TEXT,
            seniority_level VARCHAR(255),
            employment_type VARCHAR(255),
            job_function VARCHAR(255),
            industries VARCHAR(255)
            )
            """
        cursor.execute(command)
        self.db.commit()
        cursor.close()
        
        
    def _create_scrolled_jobs_table(self):
        
        cursor = self.db.cursor()
        command = """
        CREATE TABLE IF NOT EXISTS scrolled_jobs(
            entry_id INT AUTO_INCREMENT PRIMARY KEY,
            entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            job_title VARCHAR(255),
            company VARCHAR(255),
            location VARCHAR(255),
            time_of_posting VARCHAR(255),
            job_link VARCHAR(2555),
            job_id VARCHAR(255),
            search_keyword VARCHAR(255),
            search_location VARCHAR(255)
            )
            """
        cursor.execute(command)
        self.db.commit()
        cursor.close()
        
    
    def insert_scrolled_job(self, entries: dict):
        
        cursor = self.db.cursor()
        entry_tags = list(entries.keys())
        command = f"""INSERT INTO scrolled_jobs ({', '.join(entry_tags)})"""
        command += f" VALUES ({', '.join(['%s' for _ in range(len(entry_tags))])})"
        values = [entries[tag] for tag in entry_tags]
        cursor.execute(command, values)
        self.db.commit()
        cursor.close()
        
        
    def insert_job_old(self, entries: dict):
    
        cursor = self.db.cursor()
        entry_tags = list(entries.keys())
        command = f"""INSERT INTO jobs ({', '.join(entry_tags)})"""
        command += f" VALUES ({', '.join(['%s' for _ in range(len(entry_tags))])})"
        values = [entries[tag] for tag in entry_tags]
        cursor.execute(command, values)
        self.db.commit()
        cursor.close()
        
    
    def get_all_scrolled_jobs(self) -> pd.DataFrame:
        
        cursor = self.db.cursor()
        command = "SELECT job_link, job_id FROM scrolled_jobs"
        cursor.execute(command)
        result = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(result, columns=['job_link', 'job_id'])        
        
    
    def check_if_job_already_scraped(self, job_id: str):
        
        cursor = self.db.cursor()
        command = f"SELECT * FROM jobs WHERE job_id='{job_id}'"
        cursor.execute(command)
        result = cursor.fetchall()
        cursor.close()
        return True if result else False
    
    
    def insert_job(self, entries: dict):
    
        cursor = self.db.cursor()
        entry_tags = list(entries.keys())
        command = f"""INSERT INTO jobs ({', '.join(entry_tags)})"""
        command += f" VALUES ({', '.join(['%s' for _ in range(len(entry_tags))])})"
        values = [entries[tag] for tag in entry_tags]
        cursor.execute(command, values)
        self.db.commit()
        cursor.close()