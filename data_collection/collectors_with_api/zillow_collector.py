from .base_collector import RealEstatePhotoCollector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import logging

logger = logging.getLogger(__name__)

class ZillowCollector(RealEstatePhotoCollector):
    def __init__(self, output_dir: str = "real_estate_dataset"):
        super().__init__(output_dir)
        self.base_url = "https://www.zillow.com"

    def setup_selenium(self, headless: bool = True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        return webdriver.Chrome(options=chrome_options)

    def search_properties(self, location: str, pages: int = 5):
        property_urls = []
        try:
            driver = self.setup_selenium()
            search_url = f"{self.base_url}/homes/{location.replace(' ', '-')}_rb/"
            for page in range(1, pages + 1):
                driver.get(f"{search_url}{page}_p/")
                time.sleep(3)
                elems = driver.find_elements(By.CSS_SELECTOR, 'a[data-test="property-card-link"]')
                for e in elems:
                    href = e.get_attribute('href')
                    if href and '/homedetails/' in href:
                        property_urls.append(href)
                time.sleep(2)
            driver.quit()
            logger.info(f"Found {len(property_urls)} properties")
            return property_urls
        except Exception as e:
            logger.error(f"Error searching Zillow: {e}")
            return []

    def collect_property_photos(self, property_url: str, max_photos: int = 10):
        downloaded = 0
        try:
            driver = self.setup_selenium()
            driver.get(property_url)
            time.sleep(3)
            photo_elements = driver.find_elements(By.CSS_SELECTOR, 'img[class*="photo"]')
            for img_element in photo_elements[:max_photos]:
                img_url = img_element.get_attribute('src')
                if img_url and img_url not in self.collected_urls:
                    filename = self.generate_filename(img_url, 'zillow')
                    if self.download_image(img_url, filename):
                        self.collected_urls.add(img_url)
                        downloaded += 1
                        self.metadata.append({
                            'filename': filename,
                            'source_url': img_url,
                            'property_url': property_url,
                            'source': 'zillow',
                            'downloaded_at': time.time()
                        })
                time.sleep(1)
            driver.quit()
            return downloaded
        except Exception as e:
            logger.error(f"Error collecting from {property_url}: {e}")
            return downloaded
