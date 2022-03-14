from dotenv import load_dotenv

from ltd_invoice.bookkepping import Bookkeper
from ltd_invoice.gmail import GmailService
from ltd_invoice.pdf_parse import extract_invoice


def main() -> None:
    bookkeper = Bookkeper()
    for email_message in GmailService().get_emails():
        invoice = extract_invoice(email_message.attachment)
        bookkeper.register_invoice(invoice)
        invoice.save()
        print(email_message, "\n\t", invoice)


if __name__ == "__main__":
    load_dotenv()
    main()
