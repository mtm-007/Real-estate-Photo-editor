import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import tempfile
from .base_collector import SimplePhotoCollector, logger

def collect_from_pexels(headless: bool = True, max_images_per_term: int = 10):
    collector = SimplePhotoCollector()

    # Setup headless Selenium
    # chrome_options = Options()
    # if headless:
    #     chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--disable-gpu")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")   # use new headless mode
    chrome_options.add_argument("--no-sandbox")     # required in Codespaces / Docker
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--remote-debugging-port=9222")  # needed in cloud environments


    # Add this to solve "user data directory is already in use"
    tmp_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={tmp_dir}")

    driver = webdriver.Chrome(options=chrome_options)

    search_terms = ["living room tv", "fireplace interior", "modern living room"]
    total_downloaded = 0

    for term in search_terms:
        try:
            search_url = f"https://www.pexels.com/search/{term.replace(' ', '%20')}/"
            logger.info(f"Searching Pexels for: {term}")

            driver.get(search_url)
            time.sleep(3)  # wait for page to load

            # Scroll a few times to load more images
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
                time.sleep(2)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            img_elements = soup.find_all('img', {'class': lambda x: x and 'photo-item' in str(x)})[:max_images_per_term]

            downloaded = 0
            for img in img_elements:
                src = img.get("src") or img.get("data-src")
                if not src or src in collector.downloaded_urls:
                    continue

                filename = collector.generate_filename(src, f"pexels_{term.replace(' ', '_')}")
                if collector.download_image(src, filename):
                    collector.downloaded_urls.add(src)
                    collector.metadata.append({
                        "filename": filename,
                        "source_url": src,
                        "source": "pexels",
                        "search_term": term
                    })
                    downloaded += 1
                    total_downloaded += 1

                time.sleep(1)  # rate limiting

            logger.info(f"Downloaded {downloaded} images for term '{term}'")
        except Exception as e:
            logger.error(f"Error collecting from Pexels for term '{term}': {e}")

    driver.quit()
    logger.info(f"Total downloaded images from Pexels: {total_downloaded}")
    return collector
