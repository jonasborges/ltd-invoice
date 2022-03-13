import re
from dataclasses import dataclass
from io import BytesIO

from pdfminer.high_level import extract_text


class InvoicePattern:
    _DATE_REGEX = r"[0-3]?[0-9]/[0-3]?[0-9]/(?:[0-9]{2})?[0-9]{2}"
    GROSS_VALUE = r"Gross.(\d{0,3}[,]?\d{0,6}.\d{2})"
    HOUR_RATE = r"STD..(\d+.\d{2})..SELF BILL INVOICE Number"
    HOURS_WORKED = r".(\d{0,2}:\d{2}).hrs"
    INVOICE_DATE = rf"Date:.({_DATE_REGEX})"
    INVOICE_NUMBER = r"SELF BILL INVOICE Number: (\w+-\w+)"
    NET_VALUE = r"Net.(\d{0,3}[,]?\d{0,6}.\d{2})"
    PAYMENT_DUE_DATE = rf"Amount is due by ({_DATE_REGEX})"
    VAT_RATE = r"Rate.(\d{0,3}[,]?\d{0,6}.\d{2})"
    TIMESHEET_ID = r"Sheet:.(TS_\d+)"
    VAT_VALUE = r"VAT.(\d{0,3}[,]?\d{0,6}.\d{2})"


@dataclass
class Invoice:
    gross_value: str
    net_value: str
    vat_value: str
    vat_rate: str
    invoice_date: str
    payment_due_date: str
    invoice_number: str
    hours_worked: str
    hour_rate: str
    timesheet_id: str
    REGEX_MAPPING = dict(
        gross_value=InvoicePattern.GROSS_VALUE,
        net_value=InvoicePattern.NET_VALUE,
        vat_value=InvoicePattern.VAT_VALUE,
        vat_rate=InvoicePattern.VAT_RATE,
        invoice_date=InvoicePattern.INVOICE_DATE,
        payment_due_date=InvoicePattern.PAYMENT_DUE_DATE,
        invoice_number=InvoicePattern.INVOICE_NUMBER,
        hours_worked=InvoicePattern.HOURS_WORKED,
        hour_rate=InvoicePattern.HOUR_RATE,
        timesheet_id=InvoicePattern.TIMESHEET_ID,
    )

    def save(self) -> None:
        """Save to filesystem"""
        with open(f"invoice-{self.invoice_number}.pdf", "wb+") as f:
            f.write(self.bytes)


def extract_invoice(attachment: bytes) -> Invoice:
    pdf_text = extract_text(BytesIO(attachment))

    return Invoice(
        **{
            field_name: re.findall(regex_pattern, pdf_text, flags=re.DOTALL)[0]
            for field_name, regex_pattern in Invoice.REGEX_MAPPING.items()
        }
    )
