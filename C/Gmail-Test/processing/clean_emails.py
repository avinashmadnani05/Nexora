import json
import re
from html import unescape


def clean_email_body(body):
    if not body:
        return ""

    # HTML entities
    body = unescape(body)

    # Remove URLs
    body = re.sub(r"https?://\S+", "", body)

    # Remove common email footer sections
    footer_patterns = [
        r"\n\s*unsubscribe.*",
        r"\n\s*manage email settings.*",
        r"\n\s*privacy policy.*",
        r"\n\s*terms.*",
        r"\n\s*help centre.*",
        r"\n\s*help center.*",
    ]

    for pattern in footer_patterns:
        body = re.sub(pattern, "", body, flags=re.IGNORECASE | re.DOTALL)

    # Remove excessive whitespace
    body = re.sub(r"\n\s*\n+", "\n\n", body)
    body = re.sub(r"[ \t]+", " ", body)

    return body.strip()


def clean_emails(input_file="emails.json", output_file="cleaned_emails.json"):

    with open(input_file, "r", encoding="utf-8") as f:
        emails = json.load(f)

    cleaned = []

    for email in emails:

        cleaned_email = {
            "id": email.get("id"),
            "thread_id": email.get("thread_id"),
            "sender": email.get("sender"),
            "recipients": email.get("recipients"),
            "subject": email.get("subject"),
            "date": email.get("date"),
            "body": clean_email_body(email.get("body", ""))
        }

        # Ignore completely empty emails
        if not cleaned_email["subject"] and not cleaned_email["body"]:
            continue

        cleaned.append(cleaned_email)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"Original emails: {len(emails)}")
    print(f"Cleaned emails: {len(cleaned)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    clean_emails()