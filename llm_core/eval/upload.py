"""データセットをLangSmithにアップロードするスクリプト。"""

import json

from langsmith import Client


def upload_classify_dataset():
    client = Client()
    dataset_name = "tabioto-classify"

    dataset = client.create_dataset(dataset_name=dataset_name)

    with open("datasets/classify.json") as f:
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

    with open("datasets/reply.json") as f:
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
