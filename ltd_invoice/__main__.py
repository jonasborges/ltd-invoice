from dotenv import load_dotenv

from ltd_invoice.gmail import GmailService
from ltd_invoice.pdf_parse import extract_invoice


def main() -> None:
    for email_message in GmailService().get_emails():
        invoice = extract_invoice(email_message.attachment)
        print(email_message, "\n\t", invoice)
        invoice.save()


if __name__ == "__main__":
    load_dotenv()
    main()
