from .base_collector import RealEstatePhotoCollector
import logging, time

logger = logging.getLogger(__name__)

class UnsplashCollector(RealEstatePhotoCollector):
    def __init__(self, api_key: str, output_dir: str = "real_estate_dataset"):
        super().__init__(output_dir)
        self.api_key = api_key
        self.base_url = "https://api.unsplash.com"

    def search_photos(self, query: str, per_page: int = 30, pages: int = 5):
        downloaded = 0
        for page in range(1, pages + 1):
            try:
                resp = self.session.get(f"{self.base_url}/search/photos",
                                        params={'query': query, 'per_page': per_page, 'page': page, 'client_id': self.api_key})
                resp.raise_for_status()
                for photo in resp.json().get('results', []):
                    img_url = photo['urls']['regular']
                    if img_url not in self.collected_urls:
                        filename = self.generate_filename(img_url, 'unsplash')
                        if self.download_image(img_url, filename):
                            self.collected_urls.add(img_url)
                            downloaded += 1
                            self.metadata.append({
                                'filename': filename,
                                'source_url': img_url,
                                'unsplash_id': photo['id'],
                                'description': photo.get('description', ''),
                                'source': 'unsplash',
                                'downloaded_at': time.time()
                            })
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error searching Unsplash: {e}")
        return downloaded
