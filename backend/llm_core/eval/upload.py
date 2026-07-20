"""データセットをLangSmithにアップロードするスクリプト。"""

import json
from pathlib import Path

from langsmith import Client

DATASETS_DIR = Path(__file__).parent / "datasets"


def upload_classify_dataset():
    client = Client()
    dataset_name = "tabioto-classify"

    dataset = client.create_dataset(dataset_name=dataset_name)

    with open(DATASETS_DIR / "classify.json") as f:
        examples = json.load(f)

    for example in examples:
        client.create_example(
            inputs={"message": example["input"]},
            outputs={"is_urgent": example["expected"]},
            dataset_id=dataset.id,
        )
    print(f"Uploaded {len(examples)} examples to '{dataset_name}'")


def upload_reply_dataset():
    client = Client()
    dataset_name = "tabioto-reply"

    dataset = client.create_dataset(dataset_name=dataset_name)

    with open(DATASETS_DIR / "reply.json") as f:
        examples = json.load(f)

    for example in examples:
        client.create_example(
            inputs=example["input"],
            outputs={},
            dataset_id=dataset.id,
        )
    print(f"Uploaded {len(examples)} examples to '{dataset_name}'")


if __name__ == "__main__":
    upload_classify_dataset()
    upload_reply_dataset()
