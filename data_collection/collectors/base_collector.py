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
