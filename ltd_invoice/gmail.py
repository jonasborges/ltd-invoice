import base64
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Generator, Union

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build


@dataclass(frozen=True)
class EmailMessage:
    id: str
    thread_id: str
    subject: str
    body: str = field(repr=False)
    attachment: bytes = field(repr=False)
    sender: str
    receiver: str
    date: datetime

    def __post_init__(self) -> None:
        attributes_to_format = (
            (
                "date",
                datetime.strptime(
                    self.date,
                    os.environ["EMAIL_DATE_FORMAT"],
                ),
            ),
        )

        for attr, value in attributes_to_format:
            super().__setattr__(attr, value)


class GmailService:
    def __init__(self) -> None:
        logging.info("Creating GmailService")
        self.service = self.build()
        self.from_email_filter = os.environ["FROM_EMAIL_FILTER"]
        logging.info("GmailService created!")

    @staticmethod
    def build_query(query_data) -> str:
        return " ".join(
            f"{field}:{value}"
            for field, value in query_data.items()
            if value is not None
        )

    def get_raw_messages(
        self, last_email_processed: Union[datetime, None]
    ) -> Generator[Dict[str, Any], None, None]:

        try:
            after_date = last_email_processed.date().isoformat()
        except AttributeError:
            after_date = None

        query_data = {
            "after": after_date,
            "from": os.environ["FROM_EMAIL_FILTER"],
        }

        message_response = (
            self.service.users()
            .messages()
            .list(
                userId=os.environ["GMAIL_USER_ID"],
                labelIds=[os.environ["GMAIL_LABEL_4_INVOICES"]],
                q=self.build_query(query_data),
            )
            .execute()
        )

        for msg in message_response.get("messages", []):
            raw_message = (
                self.service.users()
                .messages()
                .get(
                    id=msg["id"],
                    userId=os.environ["GMAIL_USER_ID"],
                )
                .execute()
            )

            if (
                os.environ["MESSAGE_SNIPPET_FILTER"]
                not in raw_message["snippet"]
            ):
                continue

            yield raw_message

    def get_attachment(self, attachment_id: str, message_id: str) -> bytes:
        raw_attachment = (
            self.service.users()
            .messages()
            .attachments()
            .get(
                userId=os.environ["GMAIL_USER_ID"],
                messageId=message_id,
                id=attachment_id,
            )
            .execute()
        )
        return base64.urlsafe_b64decode(raw_attachment["data"])

    def get_emails(
        self, last_email_processed_date
    ) -> Generator[EmailMessage, None, None]:
        logging.info("Retrieving emails since %s", last_email_processed_date)
        yield from sorted(
            (
                EmailMessage(
                    body=raw_message["payload"]["body"],
                    id=raw_message["id"],
                    thread_id=raw_message["threadId"],
                    attachment=self.get_attachment(
                        attachment_id=self.get_attachment_id(raw_message),
                        message_id=raw_message["id"],
                    ),
                    subject=self.get_attribute_from_header(
                        attribute="subject", message=raw_message
                    ),
                    sender=self.get_attribute_from_header(
                        attribute="from", message=raw_message
                    ),
                    receiver=self.get_attribute_from_header(
                        attribute="to", message=raw_message
                    ),
                    date=self.get_attribute_from_header(
                        attribute="date", message=raw_message
                    ),
                )
                for raw_message in self.get_raw_messages(
                    last_email_processed_date
                )
            ),
            key=lambda x: x.date,
        )

    @staticmethod
    def get_attribute_from_header(
        attribute: str, message: Dict[str, Any]
    ) -> str:
        attr = attribute.lower()
        for header in message["payload"]["headers"]:
            if header["name"].lower() == attr:
                return str(header["value"])
        raise ValueError(f"{attribute} is not present")

    @staticmethod
    def get_attachment_id(message: Dict[str, Any]) -> str:
        for part in message["payload"]["parts"]:
            if part["mimeType"] == "application/pdf":
                return str(part["body"]["attachmentId"])
        raise ValueError("Message has no pdf attached")

    @classmethod
    @lru_cache(maxsize=1)
    def build(cls) -> Resource:
        # Call the Gmail API
        return build("gmail", "v1", credentials=cls.get_credentials())

    @classmethod
    def get_credentials(cls):
        # If modifying these scopes, delete the file token.json.
        scopes = [os.environ["GOOGLE_API_SCOPE"]]

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", scopes)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds = cls.refresh_creds(creds, scopes)
            else:
                creds = cls.generate_creds(scopes)

        return creds

    @classmethod
    def refresh_creds(cls, creds, scopes):
        try:
            creds.refresh(Request())
        except RefreshError:
            os.unlink("token.json")
            creds = cls.generate_creds(scopes)
        return creds

    @classmethod
    def generate_creds(cls, scopes):
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", scopes
        )
        creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
        return creds
