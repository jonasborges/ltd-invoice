import base64
from importlib.resources import Resource
import os
from dataclasses import dataclass
from typing import Dict, Generator, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = [os.environ["GOOGLE_API_SCOPE"]]


@dataclass
class EmailMessage:
    id: str
    thread_id: str
    subject: str
    body: str
    attachment: bytes


class GmailService:
    def __init__(self, service: Resource) -> None:
        self.service = service

    def get_invoice_messages(self) -> Generator[Dict, None, None]:
        message_response = (
            self.service.users()
            .messages()
            .list(
                userId=os.environ["GMAIL_USER_ID"],
                labelIds=[os.environ["GMAIL_LABEL_4_INVOICES"]],
            )
            .execute()
        )

        try:
            messages = message_response["messages"]
        except KeyError:
            print("FAILED!")

        for msg in messages:
            raw_message = (
                self.service.users()
                .messages()
                .get(id=msg["id"], userId=os.environ["GMAIL_USER_ID"])
                .execute()
            )

            if (
                os.environ["MESSAGE_SNIPPET_FILTER"]
                not in raw_message["snippet"]
            ):
                continue

            yield raw_message

    def get_invoice_attachments(self) -> Generator[EmailMessage, None, None]:
        for raw_message in self.service.get_invoice_messages():
            try:
                attachment = (
                    self.service.users()
                    .messages()
                    .attachments()
                    .get(
                        userId=os.environ["GMAIL_USER_ID"],
                        messageId=raw_message["id"],
                        id=self.get_attachement_id(raw_message),
                    )
                    .execute()
                )
            except Exception as exc:
                print(exc)
            else:
                yield EmailMessage(
                    id=raw_message["id"],
                    thread_id=raw_message["threadId"],
                    subject=self.get_subject(raw_message),
                    body=raw_message["payload"]["body"],
                    attachment=base64.urlsafe_b64decode(attachment["data"]),
                )

    @staticmethod
    def get_subject(message: Dict) -> str:
        for header in message["payload"]["headers"]:
            if header["name"] == "subject":
                return str(header["value"])
        raise ValueError("Subject is not present")

    @staticmethod
    def get_attachement_id(message: Dict) -> str:
        return str(message["payload"]["parts"][1]["body"]["attachmentId"])


def get_gmail_service() -> GmailService:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Call the Gmail API
    return GmailService(service=build("gmail", "v1", credentials=creds))
