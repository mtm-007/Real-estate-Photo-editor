"""
Real Estate Photo Data Collection System for AutoHDR Portfolio Project
Collects interior photos with TVs and fireplaces for object detection training
"""

import requests
import json
import os
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import hashlib
from typing import List, Dict, Optional
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import cv2
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealEstatePhotoCollector:
    def __init__(self, output_dir: str = "real_estate_dataset"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
        (self.output_dir / "annotations").mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.collected_urls = set()
        self.metadata = []
        
    def setup_selenium(self, headless: bool = True):
        """Setup Selenium WebDriver for dynamic content"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def download_image(self, url: str, filename: str) -> bool:
        """Download and save image with validation"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Validate image
            if len(response.content) < 1024:  # Too small
                return False
                
            # Check if it's actually an image
            img_array = np.frombuffer(response.content, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                return False
                
            # Check minimum dimensions
            height, width = img.shape[:2]
            if width < 300 or height < 300:
                return False
            
            # Save image
            filepath = self.output_dir / "images" / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
                
            logger.info(f"Downloaded: {filename} ({width}x{height})")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False
    
    def generate_filename(self, url: str, source: str) -> str:
        """Generate unique filename from URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        extension = url.split('.')[-1].lower()
        if extension not in ['jpg', 'jpeg', 'png', 'webp']:
            extension = 'jpg'
        return f"{source}_{url_hash}.{extension}"

class ZillowCollector(RealEstatePhotoCollector):
    """Collect photos from Zillow property listings"""
    
    def __init__(self, output_dir: str = "real_estate_dataset"):
        super().__init__(output_dir)
        self.base_url = "https://www.zillow.com"
        
    def search_properties(self, location: str, pages: int = 5) -> List[str]:
        """Search for property listings and return URLs"""
        property_urls = []
        
        try:
            self.setup_selenium()
            
            # Search URL format
            search_url = f"{self.base_url}/homes/{location.replace(' ', '-').replace(',', '')}_rb/"
            
            for page in range(1, pages + 1):
                logger.info(f"Searching page {page} for {location}")
                
                page_url = f"{search_url}{page}_p/"
                self.driver.get(page_url)
                time.sleep(3)
                
                # Find property links
                property_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-test="property-card-link"]')
                
                for element in property_elements:
                    href = element.get_attribute('href')
                    if href and '/homedetails/' in href:
                        property_urls.append(href)
                
                time.sleep(2)  # Be respectful
                
            self.driver.quit()
            logger.info(f"Found {len(property_urls)} properties")
            return property_urls
            
        except Exception as e:
            logger.error(f"Error searching Zillow: {e}")
            if hasattr(self, 'driver'):
                self.driver.quit()
            return []
    
    def collect_property_photos(self, property_url: str, max_photos: int = 10) -> int:
        """Collect photos from a single property listing"""
        try:
            self.setup_selenium()
            self.driver.get(property_url)
            time.sleep(3)
            
            # Find photo gallery
            photo_elements = self.driver.find_elements(By.CSS_SELECTOR, 'img[class*="photo"]')
            
            downloaded = 0
            for i, img_element in enumerate(photo_elements[:max_photos]):
                if downloaded >= max_photos:
                    break
                    
                img_url = img_element.get_attribute('src')
                if not img_url or img_url in self.collected_urls:
                    continue
                
                # Filter for interior photos (heuristic)
                if any(keyword in img_url.lower() for keyword in ['living', 'room', 'interior', 'kitchen']):
                    filename = self.generate_filename(img_url, 'zillow')
                    
                    if self.download_image(img_url, filename):
                        self.collected_urls.add(img_url)
                        self.metadata.append({
                            'filename': filename,
                            'source_url': img_url,
                            'property_url': property_url,
                            'source': 'zillow',
                            'downloaded_at': time.time()
                        })
                        downloaded += 1
                
                time.sleep(1)  # Rate limiting
            
            self.driver.quit()
            return downloaded
            
        except Exception as e:
            logger.error(f"Error collecting from {property_url}: {e}")
            if hasattr(self, 'driver'):
                self.driver.quit()
            return 0

class UnsplashCollector(RealEstatePhotoCollector):
    """Collect interior photos from Unsplash API"""
    
    def __init__(self, api_key: str, output_dir: str = "real_estate_dataset"):
        super().__init__(output_dir)
        self.api_key = api_key
        self.base_url = "https://api.unsplash.com"
    
    def search_photos(self, query: str, per_page: int = 30, pages: int = 5) -> int:
        """Search and download photos from Unsplash"""
        downloaded = 0
        
        for page in range(1, pages + 1):
            try:
                url = f"{self.base_url}/search/photos"
                params = {
                    'query': query,
                    'per_page': per_page,
                    'page': page,
                    'client_id': self.api_key
                }
                
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for photo in data.get('results', []):
                    img_url = photo['urls']['regular']
                    if img_url in self.collected_urls:
                        continue
                    
                    filename = self.generate_filename(img_url, 'unsplash')
                    
                    if self.download_image(img_url, filename):
                        self.collected_urls.add(img_url)
                        self.metadata.append({
                            'filename': filename,
                            'source_url': img_url,
                            'unsplash_id': photo['id'],
                            'description': photo.get('description', ''),
                            'source': 'unsplash',
                            'downloaded_at': time.time()
                        })
                        downloaded += 1
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error searching Unsplash: {e}")
                break
        
        return downloaded

class FlickrCollector(RealEstatePhotoCollector):
    """Collect interior photos from Flickr API"""
    
    def __init__(self, api_key: str, output_dir: str = "real_estate_dataset"):
        super().__init__(output_dir)
        self.api_key = api_key
        self.base_url = "https://api.flickr.com/services/rest/"
    
    def search_photos(self, tags: str, per_page: int = 100, pages: int = 5) -> int:
        """Search and download photos from Flickr"""
        downloaded = 0
        
        for page in range(1, pages + 1):
            try:
                params = {
                    'method': 'flickr.photos.search',
                    'api_key': self.api_key,
                    'tags': tags,
                    'tag_mode': 'any',
                    'media': 'photos',
                    'per_page': per_page,
                    'page': page,
                    'format': 'json',
                    'nojsoncallback': 1,
                    'extras': 'url_c,url_b'  # Medium and large sizes
                }
                
                response = self.session.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for photo in data['photos']['photo']:
                    # Try different size URLs
                    img_url = photo.get('url_b') or photo.get('url_c')
                    if not img_url or img_url in self.collected_urls:
                        continue
                    
                    filename = self.generate_filename(img_url, 'flickr')
                    
                    if self.download_image(img_url, filename):
                        self.collected_urls.add(img_url)
                        self.metadata.append({
                            'filename': filename,
                            'source_url': img_url,
                            'flickr_id': photo['id'],
                            'title': photo.get('title', ''),
                            'source': 'flickr',
                            'downloaded_at': time.time()
                        })
                        downloaded += 1
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error searching Flickr: {e}")
                break
        
        return downloaded

class DatasetManager:
    """Manage the collected dataset"""
    
    def __init__(self, dataset_dir: str = "real_estate_dataset"):
        self.dataset_dir = Path(dataset_dir)
    
    def save_metadata(self, metadata: List[Dict]):
        """Save metadata to CSV"""
        df = pd.DataFrame(metadata)
        df.to_csv(self.dataset_dir / "metadata" / "dataset_metadata.csv", index=False)
        logger.info(f"Saved metadata for {len(metadata)} images")
    
    def filter_by_keywords(self, keywords: List[str]) -> List[str]:
        """Filter images that likely contain TVs/fireplaces"""
        metadata_file = self.dataset_dir / "metadata" / "dataset_metadata.csv"
        if not metadata_file.exists():
            return []
        
        df = pd.read_csv(metadata_file)
        filtered_files = []
        
        for _, row in df.iterrows():
            filename = row['filename']
            description = str(row.get('description', '') + ' ' + row.get('title', '')).lower()
            
            if any(keyword in description for keyword in keywords):
                filtered_files.append(filename)
        
        return filtered_files
    
    def create_annotation_template(self):
        """Create template for manual annotation"""
        template = {
            'filename': '',
            'tv_present': False,
            'fireplace_present': False,
            'tv_bbox': '',  # x,y,w,h
            'fireplace_bbox': '',  # x,y,w,h
            'room_type': '',  # living_room, bedroom, etc.
            'quality_score': 0  # 1-5 rating
        }
        
        template_df = pd.DataFrame([template])
        template_df.to_csv(self.dataset_dir / "annotations" / "annotation_template.csv", index=False)
        logger.info("Created annotation template")
    
    def generate_stats(self):
        """Generate dataset statistics"""
        images_dir = self.dataset_dir / "images"
        if not images_dir.exists():
            return
        
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
        
        stats = {
            'total_images': len(image_files),
            'size_gb': sum(f.stat().st_size for f in image_files) / (1024**3),
            'sources': {},
        }
        
        # Count by source
        for img_file in image_files:
            source = img_file.name.split('_')[0]
            stats['sources'][source] = stats['sources'].get(source, 0) + 1
        
        logger.info(f"Dataset Stats: {stats}")
        return stats

# Main execution functions
def collect_dataset():
    """Main function to collect the dataset"""
    
    # Initialize collectors
    collector = RealEstatePhotoCollector()
    
    # Collect from multiple sources
    all_metadata = []
    
    # 1. Unsplash (requires API key)
    UNSPLASH_API_KEY = "YOUR_UNSPLASH_API_KEY"  # Get from https://unsplash.com/developers
    if UNSPLASH_API_KEY != "YOUR_UNSPLASH_API_KEY":
        unsplash = UnsplashCollector(UNSPLASH_API_KEY)
        
        # Search for relevant interior photos
        queries = [
            "living room tv",
            "fireplace interior",
            "modern living room",
            "home theater",
            "cozy living room fireplace"
        ]
        
        for query in queries:
            logger.info(f"Searching Unsplash for: {query}")
            downloaded = unsplash.search_photos(query, per_page=30, pages=3)
            logger.info(f"Downloaded {downloaded} images for '{query}'")
            all_metadata.extend(unsplash.metadata)
            time.sleep(2)
    
    # 2. Flickr (requires API key)
    FLICKR_API_KEY = "YOUR_FLICKR_API_KEY"  # Get from https://www.flickr.com/services/apps/create/
    if FLICKR_API_KEY != "YOUR_FLICKR_API_KEY":
        flickr = FlickrCollector(FLICKR_API_KEY)
        
        # Search with tags
        tag_sets = [
            "living,room,tv,television",
            "fireplace,interior,home",
            "family,room,entertainment",
            "home,theater,tv,wall"
        ]
        
        for tags in tag_sets:
            logger.info(f"Searching Flickr for tags: {tags}")
            downloaded = flickr.search_photos(tags, per_page=50, pages=2)
            logger.info(f"Downloaded {downloaded} images for tags '{tags}'")
            all_metadata.extend(flickr.metadata)
            time.sleep(2)
    
    # Save metadata
    if all_metadata:
        manager = DatasetManager()
        manager.save_metadata(all_metadata)
        manager.create_annotation_template()
        manager.generate_stats()
        
        logger.info(f"Dataset collection complete! Total images: {len(all_metadata)}")
    else:
        logger.warning("No images collected. Make sure to set API keys!")

if __name__ == "__main__":
    collect_dataset()