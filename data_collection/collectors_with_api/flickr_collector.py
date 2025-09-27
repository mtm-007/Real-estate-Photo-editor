from .base_collector import RealEstatePhotoCollector
import logging, time

logger = logging.getLogger(__name__)

class FlickrCollector(RealEstatePhotoCollector):
    def __init__(self, api_key: str, output_dir: str = "real_estate_dataset"):
        super().__init__(output_dir)
        self.api_key = api_key
        self.base_url = "https://api.flickr.com/services/rest/"

    def search_photos(self, tags: str, per_page: int = 100, pages: int = 5):
        downloaded = 0
        for page in range(1, pages + 1):
            try:
                params = {
                    'method': 'flickr.photos.search',
                    'api_key': self.api_key,
                    'tags': tags,
                    'media': 'photos',
                    'per_page': per_page,
                    'page': page,
                    'format': 'json',
                    'nojsoncallback': 1,
                    'extras': 'url_c,url_b'
                }
                resp = self.session.get(self.base_url, params=params)
                resp.raise_for_status()
                for photo in resp.json()['photos']['photo']:
                    img_url = photo.get('url_b') or photo.get('url_c')
                    if img_url and img_url not in self.collected_urls:
                        filename = self.generate_filename(img_url, 'flickr')
                        if self.download_image(img_url, filename):
                            self.collected_urls.add(img_url)
                            downloaded += 1
                            self.metadata.append({
                                'filename': filename,
                                'source_url': img_url,
                                'flickr_id': photo['id'],
                                'title': photo.get('title', ''),
                                'source': 'flickr',
                                'downloaded_at': time.time()
                            })
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error searching Flickr: {e}")
        return downloaded
