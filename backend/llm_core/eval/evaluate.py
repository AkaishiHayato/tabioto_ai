"""LangSmith上でevalを実行するスクリプト。"""

from langsmith import evaluate

from llm_core.client import classify_message, generate_reply


def classify_target(inputs: dict) -> dict:
    """分類のeval対象関数。"""
    is_urgent = classify_message(inputs["message"])
    return {"is_urgent": is_urgent}


def classify_accuracy(run, example) -> dict:
    """分類の正解率を評価する。"""
    predicted = run.outputs["is_urgent"]
    expected = example.outputs["is_urgent"]
    return {"key": "accuracy", "score": int(predicted == expected)}


def reply_target(inputs: dict) -> dict:
    """返信文生成のeval対象関数。"""
    reply = generate_reply(inputs["message"], inputs["listing_info"])
    return {"reply": reply}


def run_classify_eval():
    results = evaluate(
        classify_target,
        data="tabioto-classify",
        evaluators=[classify_accuracy],
        experiment_prefix="classify",
    )
    print("Classification eval complete")
    return results


def run_reply_eval():
    results = evaluate(
        reply_target,
        data="tabioto-reply",
        experiment_prefix="reply",
    )
    print("Reply eval complete (check LangSmith UI for results)")
    return results


if __name__ == "__main__":
    run_classify_eval()
    run_reply_eval()
