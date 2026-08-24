import os
import json
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def authenticate():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json", SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def get_header(headers, name):
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return ""


def get_body(payload):
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode(
                        "utf-8",
                        errors="ignore"
                    )

    if payload.get("mimeType") == "text/plain":
        data = payload["body"].get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode(
                "utf-8",
                errors="ignore"
            )

    return ""


def fetch_emails(service, limit=20):
    response = service.users().messages().list(
        userId="me",
        maxResults=limit
    ).execute()

    messages = response.get("messages", [])

    emails = []

    for message in messages:
        msg = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="full"
        ).execute()

        payload = msg["payload"]

        email = {
            "id": msg["id"],
            "thread_id": msg["threadId"],
            "sender": get_header(
                payload.get("headers", []), "From"
            ),
            "recipients": get_header(
                payload.get("headers", []), "To"
            ),
            "subject": get_header(
                payload.get("headers", []), "Subject"
            ),
            "date": get_header(
                payload.get("headers", []), "Date"
            ),
            "body": get_body(payload)
        }

        emails.append(email)

    return emails


def main():
    creds = authenticate()

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    emails = fetch_emails(service, limit=20)

    with open("emails.json", "w", encoding="utf-8") as f:
        json.dump(
            emails,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Fetched {len(emails)} emails.")
    print("Saved to emails.json")


if __name__ == "__main__":
    main()