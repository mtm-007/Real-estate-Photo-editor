import logging
from collectors.unsplash_collector import UnsplashCollector
from collectors.flickr_collector import FlickrCollector
from dataset_manager import DatasetManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def collect_dataset():
    all_metadata = []

    UNSPLASH_API_KEY = "YOUR_UNSPLASH_API_KEY"
    if UNSPLASH_API_KEY != "YOUR_UNSPLASH_API_KEY":
        unsplash = UnsplashCollector(UNSPLASH_API_KEY)
        queries = ["living room tv", "fireplace interior"]
        for q in queries:
            downloaded = unsplash.search_photos(q, per_page=30, pages=3)
            logger.info(f"Downloaded {downloaded} Unsplash images for '{q}'")
            all_metadata.extend(unsplash.metadata)

    FLICKR_API_KEY = "YOUR_FLICKR_API_KEY"
    if FLICKR_API_KEY != "YOUR_FLICKR_API_KEY":
        flickr = FlickrCollector(FLICKR_API_KEY)
        tags_list = ["living,room,tv", "fireplace,interior,home"]
        for tags in tags_list:
            downloaded = flickr.search_photos(tags, per_page=50, pages=2)
            logger.info(f"Downloaded {downloaded} Flickr images for tags '{tags}'")
            all_metadata.extend(flickr.metadata)

    if all_metadata:
        manager = DatasetManager()
        manager.save_metadata(all_metadata)
        manager.create_annotation_template()
        manager.generate_stats()
        logger.info(f"Dataset collection complete! Total images: {len(all_metadata)}")
    else:
        logger.warning("No images collected. Make sure API keys are set!")

if __name__ == "__main__":
    collect_dataset()
