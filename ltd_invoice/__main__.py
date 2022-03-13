import sys

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    from ltd_invoice.gmail import GmailService
    from ltd_invoice.invoice import Invoice

    steps = (
        "get_invoice_attachments",
        "parse_invoice_content",
        "update_bookkeping_app",
        "persist_invoice",
    )

    for step in steps:
        try:
            step.execute()
        except Exception as exc:
            print(f"Failed {str(exc)}")
            sys.exit(1)

    # gmail_service = get_gmail_service()
    # for num, email_message in enumerate(gmail_service.get_invoice_attachments()):
    #     invoice = Invoice(email_message.attachment)


if __name__ == "__main__":
    main()
