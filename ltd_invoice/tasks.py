from ltd_invoice.bookkepping import Bookkeper
from ltd_invoice.celeryapp import app
from ltd_invoice.gmail import GmailService
from ltd_invoice.pdf_parse import extract_invoice


@app.task
def process_invoices() -> None:
    bookkeper = Bookkeper()
    gmail = GmailService()
    for email_message in gmail.get_emails():
        invoice = extract_invoice(email_message.attachment)
        bookkeper.register_invoice(invoice)
