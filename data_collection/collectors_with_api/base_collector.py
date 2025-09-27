import requests
from pathlib import Path
import hashlib
import logging
import time
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class RealEstatePhotoCollector:
    def __init__(self, output_dir: str = "real_estate_dataset"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
        (self.output_dir / "annotations").mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        self.collected_urls = set()
        self.metadata = []

    def download_image(self, url: str, filename: str) -> bool:
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            if len(response.content) < 1024:
                return False
            img_array = np.frombuffer(response.content, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is None or img.shape[0] < 300 or img.shape[1] < 300:
                return False
            filepath = self.output_dir / "images" / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded: {filename} ({img.shape[1]}x{img.shape[0]})")
            return True
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False

    def generate_filename(self, url: str, source: str) -> str:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        extension = url.split('.')[-1].lower()
        if extension not in ['jpg', 'jpeg', 'png', 'webp']:
            extension = 'jpg'
        return f"{source}_{url_hash}.{extension}"
