import logging

from ltd_invoice.bookkepping import Bookkeper
from ltd_invoice.celeryapp import app
from ltd_invoice.gmail import GmailService
from ltd_invoice.pdf_parse import extract_invoice
from ltd_invoice.tracker import Tracker


@app.task
def process_invoices() -> None:
    logging.info("Starting process_invoices")

    gmail = GmailService()
    tracker = Tracker()
    bookkeper = Bookkeper()

    try:
        for email_message in gmail.get_emails(
            tracker.last_email_processed_date
        ):
            if email_message.id in tracker.processed_emails:
                logging.info(
                    "Skipping id=%s, email=%s",
                    email_message.id,
                    email_message.date,
                )
                continue

            invoice = extract_invoice(email_message.attachment)
            bookkeper.register_invoice(invoice)
            tracker.update(email_message)
            logging.info(
                "Processed email=%s, invoice=%s, timeshee=%s",
                email_message.date,
                invoice.invoice_date,
                invoice.timesheet_id,
            )
            invoice.save()
    finally:
        del bookkeper
