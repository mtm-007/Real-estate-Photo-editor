import time
import os
from pycocotools.coco import COCO
from .base_collector import SimplePhotoCollector, logger
import random
import requests


def collect_sample_coco_tv(sample_size: int = 1000):
    """Download a small sample of COCO train2017 images with TVs"""
    collector = SimplePhotoCollector()
    downloaded = 0

    # COCO image IDs range from 000000000000.jpg to 000000118287.jpg (train2017)
    # all_ids = list(range(1, 118288))  # total train2017 images
    # sample_ids = random.sample(all_ids, sample_size)

    coco = COCO('instances_train2017.json')
    valid_ids = [img['id'] for img in coco.dataset['images']]
    sample_ids = random.sample(valid_ids, 1000)

    logger.info(f"Downloading {sample_size} sample COCO images...")

    for img_id in sample_ids:
        if downloaded >= sample_size:
            break  # stop when we reach the desired number of images

        img_filename = f"{img_id:012d}.jpg"
        url = f"http://images.cocodataset.org/train2017/{img_filename}"
        filename = collector.generate_filename(url, "coco_sample")

        try:

            if collector.download_image(url, filename):
                collector.metadata.append({
                    "filename": filename,
                    "source_url": url,
                    "source": "coco_dataset",
                    "category": "tv_detection"
                })
                downloaded += 1
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Image not found, skipping: {url}")
            else:
                logger.error(f"HTTP error downloading {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")


        time.sleep(0.5)  # be polite

    logger.info(f"Downloaded {downloaded} COCO sample images")
    return collector


# def collect_from_coco_tv(coco_dataset_path):
#     collector = SimplePhotoCollector()
#     coco = COCO(os.path.join(coco_dataset_path, "annotations/instances_train2017.json"))

#     cat_ids = coco.getCatIds(catNms=['tv'])
#     img_ids = coco.getImgIds(catIds=cat_ids)

#     for img_id in img_ids[:50]:  # limit to 50 for now
#         img_info = coco.loadImgs(img_id)[0]
#         url = img_info['coco_url']
#         filename = collector.generate_filename(url, "coco_tv")
#         if collector.download_image(url, filename):
#             collector.downloaded_urls.add(url)
#             collector.metadata.append({
#                 "filename": filename,
#                 "source_url": url,
#                 "source": "coco",
#                 "coco_id": img_id,
#                 "category": "tv"
#             })
    
#     logger.info(f"Downloaded {len(collector.downloaded_urls)} images from COCO (TV category)")
#     return collector







# def create_coco_tv_subset():
#     coco_tv_urls = [
#         "http://images.cocodataset.org/train2017/000000000009.jpg",
#         "http://images.cocodataset.org/train2017/000000000025.jpg",
#     ]
#     collector = SimplePhotoCollector()
#     downloaded = 0
#     for url in coco_tv_urls:
#         filename = collector.generate_filename(url, "coco_tv")
#         if collector.download_image(url, filename):
#             collector.metadata.append({
#                 "filename": filename,
#                 "source_url": url,
#                 "source": "coco_dataset",
#                 "has_tv": True,
#                 "category": "tv_detection"
#             })
#             downloaded += 1
#         time.sleep(1)
#     logger.info(f"Downloaded {downloaded} COCO TV images")
#     return collector
