import json
import logging
from datetime import datetime
from typing import List


class Tracker:
    TRACKER_FILE = ".tracker"
    PROCESSED_EMAILS_FILE = ".processed_emails"

    def __init__(self) -> None:
        logging.info("Creating Tracker")
        try:
            with open(self.TRACKER_FILE, "r+") as f:
                last_email_processed_date = datetime.fromisoformat(f.read())
        except (FileNotFoundError, ValueError):
            last_email_processed_date = None

        self.last_email_processed_date = last_email_processed_date
        self.processed_emails = self.load_processed_emails()
        logging.info("Tracker created!")

    def update(self, email_message) -> None:
        self.processed_emails.append(email_message.id)
        self.save_processed_emails()
        with open(self.TRACKER_FILE, "w") as f:
            f.write(email_message.date.date().isoformat())

    def load_processed_emails(self) -> List[str]:
        with open(self.PROCESSED_EMAILS_FILE, "r+") as f:
            return list(set(json.loads(f.read())))

    def save_processed_emails(self) -> None:
        with open(self.PROCESSED_EMAILS_FILE, "w+") as f:
            f.write(json.dumps(list(set(self.processed_emails)), indent=4))
