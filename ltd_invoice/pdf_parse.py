import re
from dataclasses import dataclass

from pdfminer.high_level import extract_text


@dataclass
class Invoice:
    gross_value: str
    net_value: str
    vat_value: str
    rate_value: str
    invoice_date: str
    payment_due_date: str
    invoice_number: str
    hours_worked: str
    hour_rate: str
    timesheet_number: str

    def save(self) -> None:
        """Save to filesystem"""
        with open(f"invoice-{self.invoice_number}.pdf", "wb+") as f:
            f.write(self.bytes)


class InvoicePattern:
    _DATE_REGEX = r"[0-3]?[0-9]/[0-3]?[0-9]/(?:[0-9]{2})?[0-9]{2}"
    GROSS_VALUE = r"Gross.(\d{0,3}[,]?\d{0,6}.\d{2})"
    HOUR_RATE = r"STD..(\d+.\d{2})..SELF BILL INVOICE Number"
    HOURS_WORKED = r".(\d{0,2}:\d{2}).hrs"
    INVOICE_DATE = rf"Date:.({_DATE_REGEX})"
    INVOICE_NUMBER = r"SELF BILL INVOICE Number: (\w+-\w+)"
    NET_VALUE = r"Net.(\d{0,3}[,]?\d{0,6}.\d{2})"
    PAYMENT_DUE_DATE = rf"Amount is due by ({_DATE_REGEX})"
    RATE_VALUE = r"Rate.(\d{0,3}[,]?\d{0,6}.\d{2})"
    TIMESHEET_ID = r"Sheet:.(TS_\d+)"
    VAT_VALUE = r"VAT.(\d{0,3}[,]?\d{0,6}.\d{2})"


def extract_content(filename: str) -> Invoice:
    pdf_text = extract_text(filename)

    return Invoice(
        gross_value=re.findall(
            InvoicePattern.GROSS_VALUE, pdf_text, flags=re.DOTALL
        )[0],
        hour_rate=re.findall(
            InvoicePattern.HOUR_RATE, pdf_text, flags=re.DOTALL
        )[0],
        hours_worked=re.findall(
            InvoicePattern.HOURS_WORKED, pdf_text, flags=re.DOTALL
        )[0],
        invoice_date=re.findall(
            InvoicePattern.INVOICE_DATE, pdf_text, flags=re.DOTALL
        )[0],
        invoice_number=re.findall(
            InvoicePattern.INVOICE_NUMBER, pdf_text, flags=re.DOTALL
        )[0],
        net_value=re.findall(
            InvoicePattern.NET_VALUE, pdf_text, flags=re.DOTALL
        )[0],
        payment_due_date=re.findall(
            InvoicePattern.PAYMENT_DUE_DATE, pdf_text, flags=re.DOTALL
        )[0],
        rate_value=re.findall(
            InvoicePattern.RATE_VALUE, pdf_text, flags=re.DOTALL
        )[0],
        timesheet_number=re.findall(
            InvoicePattern.TIMESHEET_ID, pdf_text, flags=re.DOTALL
        )[0],
        vat_value=re.findall(
            InvoicePattern.VAT_VALUE, pdf_text, flags=re.DOTALL
        )[0],
    )
