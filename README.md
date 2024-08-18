# li_jobs_collector
A slow but reliable way of collecting job postings from the LinkedIN's publicly available Job postings search portal. Doesn't require any authentication

## Modus Operandi 

- This collection has been broken down to a two step process :- 
- **Step-1** : Getting the job post header details and the Job description link by scrolling through the LinkedIn's Job search portal using the different search queries. The scrolling is done slowly to limit the requests sent to linked-in. 
- **Step-2** : From the job posts info obtained from the scrolling, each job post description is obtained by scraping the individual's Job post page. Some additional tags are also collected.
- Note: The project started as a trial to automate job collection using an already existing python package [py-linkedin-jobs-scrapper](https://github.com/spinlud/py-linkedin-jobs-scraper). But this package required authentication (which is the supported way for that package). But even with authentication, the script used to keep on breaking repeatedly due to linkedin's crawling detection and invalidation of the session cookie required for crawling. The current method, although slower and two step, is more reliable.

## Setup

- run the `folder_setup.py` to setup the folder structure
- The required python packages are mentioned in `requirements.txt` file. Run it with pip command
```pip install -r requirements.txt```
- All the data is stored in a locally built MySQL DB. Use the docker compose setup to create the local mysql container. Change the paths to environment file and the mysql_data folder as required. 
- After setting up the docker-compose.yml file, initiate the docker containers

## Data Collection

- Once the setup is complete and the MySQL container is running, **for step-1**, review and/or change the search configs that you want to use (stored at `search_configs`) and run the python file `collect_by_scrolling_jobs.py`

- **For step-2**, simply run the python file `collect_jds.py`