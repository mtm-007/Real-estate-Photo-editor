import time
from bs4 import BeautifulSoup
from .base_collector import SimplePhotoCollector, logger

def collect_from_pexels():
    collector = SimplePhotoCollector()
    search_terms = ["living room tv", "fireplace interior", "modern living room"]

    downloaded = 0
    for term in search_terms:
        try:
            search_url = f"https://www.pexels.com/search/{term.replace(' ', '%20')}/"
            logger.info(f"Searching Pexels for: {term}")
            resp = collector.session.get(search_url)
            soup = BeautifulSoup(resp.content, "html.parser")
            #img_elements = soup.find_all('img')[:10]
            img_elements = soup.find_all('img', {'class': lambda x: x and 'photo-item' in str(x)})[:10]


            for img in img_elements:
                src = img.get("src") or img.get("data-src")
                if not src or src in collector.downloaded_urls:
                    continue

                filename = collector.generate_filename(src, f"pexels_{term.replace(' ', '_')}")
                if collector.download_image(src, filename):
                    collector.downloaded_urls.add(src)
                    collector.metadata.append({
                        "filename": filename,
                        "source_url": src,
                        "source": "pexels",
                        "search_term": term
                    })
                    downloaded += 1
                time.sleep(2)
        except Exception as e:
            logger.error(f"Error collecting from Pexels: {e}")

    logger.info(f"Downloaded {downloaded} images from Pexels")

    response = collector.session.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    print(soup.prettify()[:1000])  # print first 1000 chars of HTML
    return collector
