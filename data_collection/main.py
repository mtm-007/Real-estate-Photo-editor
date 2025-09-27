import time
from collectors.open_datasets import collect_from_open_datasets
from collectors.pexels_dataset_with_Selenium import collect_from_pexels
from collectors.coco_dataset import collect_sample_coco_tv #collect_from_coco_tv #create_coco_tv_subset #
from utils.metadata import save_metadata
from collectors.base_collector import logger

def main():
    logger.info("=== Starting Real Estate Photo Collection ===")
    collectors = []
    try:
        #collectors.append(collect_from_open_datasets()); time.sleep(2)
        #collectors.append(collect_from_pexels()); time.sleep(2)
        # COCO_PATH = "/workspaces/Real-estate-Photo-editor/data_collection/real_estate_photos/images/coco_data"
        # collectors.append(collect_from_coco_tv(COCO_PATH))
        collectors.append(collect_sample_coco_tv())
    except Exception as e:
        logger.error(f"Collection error: {e}")

    if collectors:
        metadata = save_metadata(collectors)
        logger.info(f"Total images collected: {len(metadata)}")
        logger.info("Images saved in real_estate_photos/images/")
        logger.info("Metadata saved in real_estate_photos/logs/metadata.json")

if __name__ == "__main__":
    main()
