"""Repository implementation using pandas for persistence."""

import json
import logging
from dataclasses import asdict
from typing import List

import pandas as pd

from src.models.offer import OfferItem


class PandasOfferRepository:
    """Repository implementation using pandas for persistence."""

    def save_csv(self, items: List[OfferItem], path: str) -> None:
        """Save offers to CSV file."""
        if not items:
            logging.warning("No items to save to CSV")
            return

        data = []
        for item in items:
            item_dict = asdict(item)
            # Add special columns for images
            item_dict["images"] = ",".join(item.images) if item.images else ""
            item_dict["images_json"] = json.dumps(item.images)
            data.append(item_dict)

        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
        logging.info(f"Saved {len(items)} items to {path}")

    def save_jsonl(self, items: List[OfferItem], path: str) -> None:
        """Save offers to JSONL file."""
        if not items:
            logging.warning("No items to save to JSONL")
            return

        with open(path, "w", encoding="utf-8") as f:
            for item in items:
                json.dump(asdict(item), f, ensure_ascii=False)
                f.write("\n")

        logging.info(f"Saved {len(items)} items to {path}")
