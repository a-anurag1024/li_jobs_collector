import os
from pathlib import Path

if __name__ == "__main__":
    os.makedirs(Path("./mount/logs/jd_getter_logs"), exist_ok=True)
    os.makedirs(Path("./mount/logs/scroller_logs"), exist_ok=True)
    os.makedirs(Path("./mount/mysql_data"), exist_ok=True)
    os.makedirs(Path("./mount/scrape_scroll_saves"), exist_ok=True)