import logging

from ltd_invoice.bookkepping import Bookkeper
from ltd_invoice.gmail import GmailService
from ltd_invoice.pdf_parse import extract_invoice
from ltd_invoice.tasks import process_invoices
from ltd_invoice.tracker import Tracker


def main() -> None:
    process_invoices()


if __name__ == "__main__":
    main()
