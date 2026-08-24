import json
from transformers import pipeline

INPUT_FILE = "cleaned_emails.json"
OUTPUT_FILE = "classified_emails.json"

CATEGORIES = [
    "job related",
    "direct HR or recruiter message",
    "newsletter",
    "notification",
    "personal",
    "other"
]

classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/DeBERTa-v3-base-mnli"
)


def classify_email(email):

    text = f"""
Subject: {email.get("subject", "")}

Sender: {email.get("sender", "")}

Email:
{email.get("body", "")[:4000]}
"""

    result = classifier(
        text,
        candidate_labels=CATEGORIES,
        multi_label=False
    )

    return {
        "category": result["labels"][0],
        "confidence": round(float(result["scores"][0]), 4)
    }


def main():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        emails = json.load(f)

    classified = []

    for i, email in enumerate(emails, 1):

        print(f"Processing {i}/{len(emails)}")

        classification = classify_email(email)

        classified.append({
            **email,
            "classification": classification
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            classified,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\nDone.")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()