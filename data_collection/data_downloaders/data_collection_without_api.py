"""
Simple Real Estate Photo Collector - No API Keys Required
Quick start data collection for AutoHDR portfolio project
"""

import requests
import os
import time
import json
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import logging
from bs4 import BeautifulSoup
import cv2
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplePhotoCollector:
    def __init__(self, output_dir="real_estate_photos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.downloaded_urls = set()
        self.metadata = []
        
    def validate_image(self, image_content):
        """Validate image quality and content"""
        try:
            # Check file size
            if len(image_content) < 5000:  # Too small
                return False, "File too small"
            
            # Decode image
            img_array = np.frombuffer(image_content, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                return False, "Invalid image format"
            
            # Check dimensions
            height, width = img.shape[:2]
            if width < 400 or height < 300:
                return False, f"Image too small: {width}x{height}"
            
            # Check aspect ratio (avoid banners/weird formats)
            aspect_ratio = width / height
            if aspect_ratio > 3 or aspect_ratio < 0.3:
                return False, f"Invalid aspect ratio: {aspect_ratio:.2f}"
            
            return True, f"Valid image: {width}x{height}"
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def download_image(self, url, filename):
        """Download and save image with validation"""
        try:
            logger.info(f"Downloading: {url}")
            response = self.session.get(url, timeout=15, stream=True)
            response.raise_for_status()
            
            # Get content
            content = response.content
            
            # Validate image
            is_valid, message = self.validate_image(content)
            if not is_valid:
                logger.warning(f"Skipping {filename}: {message}")
                return False
            
            # Save image
            filepath = self.output_dir / "images" / filename
            with open(filepath, 'wb') as f:
                f.write(content)
            
            logger.info(f"✓ Saved: {filename} - {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False
    
    def generate_filename(self, url, prefix="img"):
        """Generate unique filename"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Get extension from URL
        parsed = urlparse(url)
        ext = parsed.path.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'webp']:
            ext = 'jpg'
        
        return f"{prefix}_{url_hash}.{ext}"

def collect_from_open_datasets():
    """Collect from publicly available datasets and sources"""
    collector = SimplePhotoCollector()
    
    # 1. Open Images Dataset - Sample URLs
    logger.info("=== Collecting from sample datasets ===")
    
    # These are sample interior photos with TVs/fireplaces from various sources
    sample_urls = [
        # Living room with TV samples
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        
        # Fireplace samples  
        "https://images.unsplash.com/photo-1513584684374-8bab748fbf90?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        
        # More living room interiors
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    ]
    
    downloaded = 0
    for i, url in enumerate(sample_urls):
        if url not in collector.downloaded_urls:
            filename = collector.generate_filename(url, f"sample_{i:03d}")
            
            if collector.download_image(url, filename):
                collector.downloaded_urls.add(url)
                collector.metadata.append({
                    'filename': filename,
                    'source_url': url,
                    'source': 'sample_dataset',
                    'category': 'living_room'
                })
                downloaded += 1
            
            time.sleep(1)  # Be respectful
    
    logger.info(f"Downloaded {downloaded} sample images")
    return collector

def collect_from_pexels():
    """Collect from Pexels (no API key needed for basic scraping)"""
    collector = SimplePhotoCollector()
    
    # Pexels search URLs (publicly accessible)
    search_terms = [
        "living room tv",
        "fireplace interior", 
        "modern living room",
        "home entertainment"
    ]
    
    downloaded = 0
    
    for term in search_terms:
        try:
            logger.info(f"Searching Pexels for: {term}")
            
            # Pexels search URL
            search_url = f"https://www.pexels.com/search/{term.replace(' ', '%20')}/"
            
            response = collector.session.get(search_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find image elements (Pexels structure)
            img_elements = soup.find_all('img', {'class': lambda x: x and 'photo-item' in str(x)})[:10]
            
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if not src or src in collector.downloaded_urls:
                    continue
                
                # Convert to higher quality URL
                if 'pexels.com' in src and '?w=' in src:
                    src = src.replace('?w=280&h=390', '?w=800&h=600')
                
                filename = collector.generate_filename(src, f"pexels_{term.replace(' ', '_')}")
                
                if collector.download_image(src, filename):
                    collector.downloaded_urls.add(src)
                    collector.metadata.append({
                        'filename': filename,
                        'source_url': src,
                        'source': 'pexels',
                        'search_term': term
                    })
                    downloaded += 1
                
                time.sleep(2)  # Be very respectful
            
        except Exception as e:
            logger.error(f"Error collecting from Pexels: {e}")
    
    logger.info(f"Downloaded {downloaded} images from Pexels")
    return collector

def create_coco_tv_subset():
    """Download TV images from COCO dataset"""
    
    logger.info("=== Getting COCO TV annotations ===")
    
    # COCO TV category URLs (these are publicly available)
    coco_tv_urls = [
        # Sample COCO images with TVs - these are examples
        "http://images.cocodataset.org/train2017/000000000009.jpg",
        "http://images.cocodataset.org/train2017/000000000025.jpg", 
        "http://images.cocodataset.org/train2017/000000000030.jpg",
        "http://images.cocodataset.org/train2017/000000000034.jpg",
        "http://images.cocodataset.org/train2017/000000000042.jpg",
    ]
    
    collector = SimplePhotoCollector()
    downloaded = 0
    
    for url in coco_tv_urls:
        try:
            filename = collector.generate_filename(url, "coco_tv")
            
            if collector.download_image(url, filename):
                collector.metadata.append({
                    'filename': filename,
                    'source_url': url,
                    'source': 'coco_dataset',
                    'has_tv': True,
                    'category': 'tv_detection'
                })
                downloaded += 1
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error downloading COCO image: {e}")
    
    logger.info(f"Downloaded {downloaded} COCO TV images")
    return collector

def save_metadata(collectors):
    """Save all metadata to JSON file"""
    all_metadata = []
    for collector in collectors:
        all_metadata.extend(collector.metadata)
    
    metadata_file = Path("real_estate_photos/logs/metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    logger.info(f"Saved metadata for {len(all_metadata)} images")
    
    # Create summary
    sources = {}
    for item in all_metadata:
        source = item.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    
    logger.info("=== Collection Summary ===")
    for source, count in sources.items():
        logger.info(f"{source}: {count} images")
    
    return all_metadata

def main():
    """Main collection function"""
    logger.info("Starting data collection for AutoHDR portfolio...")
    
    collectors = []
    
    # Collect from multiple sources
    try:
        # 1. Sample dataset
        collectors.append(collect_from_open_datasets())
        time.sleep(2)
        
        # 2. Pexels scraping  
        collectors.append(collect_from_pexels())
        time.sleep(2)
        
        # 3. COCO subset
        collectors.append(create_coco_tv_subset())
        
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
    except Exception as e:
        logger.error(f"Collection error: {e}")
    
    # Save all metadata
    if collectors:
        metadata = save_metadata(collectors)
        
        # Final stats
        total_images = len(metadata)
        logger.info(f"=== COLLECTION COMPLETE ===")
        logger.info(f"Total images collected: {total_images}")
        logger.info(f"Images saved to: real_estate_photos/images/")
        logger.info(f"Metadata saved to: real_estate_photos/logs/metadata.json")
        
        if total_images > 0:
            logger.info("\nNext steps:")
            logger.info("1. Review images in real_estate_photos/images/")
            logger.info("2. Manually annotate TVs/fireplaces using LabelImg or similar")
            logger.info("3. Split into train/validation sets")
            logger.info("4. Train YOLOv8 model")
    else:
        logger.warning("No images collected!")

if __name__ == "__main__":
    main()