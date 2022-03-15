import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from io import BytesIO

from pdfminer.high_level import extract_text


class InvoicePattern:
    _DATE_REGEX = r"[0-3]?[0-9]/[0-3]?[0-9]/(?:[0-9]{2})?[0-9]{2}"
    CLIENT_NAME = r"SELF BILL INVOICE\n\n([A-Za-z ]+)"
    GROSS_VALUE = r"Gross.(\d{0,3}[,]?\d{0,6}.\d{2})"
    HOUR_RATE = r"STD..(\d+.\d{2})..SELF BILL INVOICE Number"
    HOURS_WORKED = r".(\d{0,2}:\d{2}).hrs"
    INVOICE_DATE = rf"Date:.({_DATE_REGEX})"
    INVOICE_NUMBER = r"SELF BILL INVOICE Number: (\w+-\w+)"
    NET_VALUE = r"Net.(\d{0,3}[,]?\d{0,6}.\d{2})"
    PAYMENT_DUE_DATE = rf"Amount is due by ({_DATE_REGEX})"
    TIMESHEET_ID = r"Sheet:.(TS_\d+)"
    VAT_RATE = r"Rate.(\d{0,3}[,]?\d{0,6}.\d{2})"
    VAT_VALUE = r"VAT.(\d{0,3}[,]?\d{0,6}.\d{2})"


@dataclass(frozen=True)
class Invoice:
    raw_pdf: bytes = field(
        repr=False,
    )
    client_name: str
    gross_value: str
    hour_rate: str
    hours_worked: str
    invoice_date: str
    invoice_number: str
    net_value: str
    payment_due_date: str
    timesheet_id: str
    vat_rate: str
    vat_value: str
    REGEX_MAPPING = dict(
        client_name=InvoicePattern.CLIENT_NAME,
        gross_value=InvoicePattern.GROSS_VALUE,
        hour_rate=InvoicePattern.HOUR_RATE,
        hours_worked=InvoicePattern.HOURS_WORKED,
        invoice_date=InvoicePattern.INVOICE_DATE,
        invoice_number=InvoicePattern.INVOICE_NUMBER,
        net_value=InvoicePattern.NET_VALUE,
        payment_due_date=InvoicePattern.PAYMENT_DUE_DATE,
        timesheet_id=InvoicePattern.TIMESHEET_ID,
        vat_rate=InvoicePattern.VAT_RATE,
        vat_value=InvoicePattern.VAT_VALUE,
    )

    def __post_init__(self) -> None:
        attributes_to_format = (
            ("hours_worked", str(float(self.hours_worked.replace(":", ".")))),
            ("vat_rate", str(int(float(self.vat_rate)))),
            (
                "invoice_date",
                datetime.strptime(
                    self.invoice_date, os.environ["PDF_INVOICE_DATE_FORMAT"]
                ).strftime(os.environ["BOOKKEPPING_DATE_FORMAT"]),
            ),
            (
                "payment_due_date",
                datetime.strptime(
                    self.payment_due_date,
                    os.environ["PDF_INVOICE_DATE_FORMAT"],
                ).strftime(os.environ["BOOKKEPPING_DATE_FORMAT"]),
            ),
        )

        for attr, value in attributes_to_format:
            super().__setattr__(attr, value)

    @cached_property
    def internal_note(self) -> str:
        return (
            str(self)
            .replace("Invoice(", "")
            .replace(",", "\n")
            .replace("'", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("_", " ")
            .replace("=", " = ")
            .title()
        )

    def save(self) -> None:
        """Save to filesystem"""
        with open(
            os.path.join(
                os.environ["INVOICE_DIR"], f"invoice-{self.invoice_number}.pdf"
            ),
            "wb+",
        ) as f:
            f.write(self.raw_pdf)


def extract_invoice(attachment: bytes) -> Invoice:
    pdf_text = extract_text(BytesIO(attachment))

    return Invoice(
        raw_pdf=attachment,
        **{
            field_name: re.findall(regex_pattern, pdf_text, flags=re.DOTALL)[0]
            for field_name, regex_pattern in Invoice.REGEX_MAPPING.items()
        },
    )
