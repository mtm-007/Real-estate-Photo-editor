import time
from .base_collector import SimplePhotoCollector, logger

def collect_from_open_datasets():
    collector = SimplePhotoCollector()
    sample_urls = [
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7",
        "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c",
        "https://images.unsplash.com/photo-1513584684374-8bab748fbf90",
    ]
    downloaded = 0
    for i, url in enumerate(sample_urls):
        if url not in collector.downloaded_urls:
            filename = collector.generate_filename(url, f"sample_{i:03d}")
            if collector.download_image(url, filename):
                collector.downloaded_urls.add(url)
                collector.metadata.append({
                    "filename": filename,
                    "source_url": url,
                    "source": "sample_dataset",
                    "category": "living_room"
                })
                downloaded += 1
            time.sleep(1)
    logger.info(f"Downloaded {downloaded} sample images")
    return collector
