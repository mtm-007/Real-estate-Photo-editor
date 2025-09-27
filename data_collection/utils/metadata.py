import json
from pathlib import Path
from collectors.base_collector import logger

def save_metadata(collectors):
    all_metadata = []
    for collector in collectors:
        all_metadata.extend(collector.metadata)

    metadata_file = Path("real_estate_photos/logs/metadata.json")
    with open(metadata_file, "w") as f:
        json.dump(all_metadata, f, indent=2)

    logger.info(f"Saved metadata for {len(all_metadata)} images")

    sources = {}
    for item in all_metadata:
        source = item.get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1
    for s, c in sources.items():
        logger.info(f"{s}: {c} images")

    return all_metadata
