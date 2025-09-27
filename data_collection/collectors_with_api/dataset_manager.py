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
