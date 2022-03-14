import pytest

from ltd_invoice.gmail import GmailService


@pytest.mark.parametrize(
    "raw_message_header_only",
    [
        {
            "payload": {
                "headers": [
                    {
                        "name": "Date",
                        "value": "Tue, 8 Mar 2022 11:53:45 +0000 (GMT)",
                    },
                    {"name": "From", "value": "google@google.com"},
                    {"name": "To", "value": "myself@gmail.com"},
                    {
                        "name": "Subject",
                        "value": "Invoices From Google",
                    },
                    {"name": "X-Mimecast-Originator", "value": "google.com"},
                ],
            }
        }
    ],
)
@pytest.mark.parametrize(
    "attribute,expected_value",
    [
        ("date", "Tue, 8 Mar 2022 11:53:45 +0000 (GMT)"),
        ("Date", "Tue, 8 Mar 2022 11:53:45 +0000 (GMT)"),
        ("DATE", "Tue, 8 Mar 2022 11:53:45 +0000 (GMT)"),
        ("from", "google@google.com"),
        ("From", "google@google.com"),
        ("FROM", "google@google.com"),
        ("subject", "Invoices From Google"),
        ("Subject", "Invoices From Google"),
        ("SUBJECT", "Invoices From Google"),
        ("x-mimecast-originator", "google.com"),
        ("X-Mimecast-Originator", "google.com"),
        ("X-MIMECAST-ORIGINATOR", "google.com"),
        ("to", "myself@gmail.com"),
        ("To", "myself@gmail.com"),
        ("TO", "myself@gmail.com"),
    ],
)
def test_get_attribute_from_header(
    attribute, expected_value, raw_message_header_only
):
    assert (
        GmailService.get_attribute_from_header(
            attribute=attribute, message=raw_message_header_only
        )
        == expected_value
    )


@pytest.mark.parametrize(
    "raw_message_header_only",
    [
        {
            "payload": {
                "headers": [
                    {
                        "name": "Subject",
                        "value": "Invoices From Google",
                    },
                ],
            }
        }
    ],
)
@pytest.mark.parametrize(
    "attribute", ["subj&ct", "too", "froomm", ".subject."]
)
def test_attempt_to_get_invalid_attribute_from_header(
    attribute, raw_message_header_only
):
    with pytest.raises(ValueError):
        GmailService.get_attribute_from_header(
            attribute=attribute, message=raw_message_header_only
        )


@pytest.mark.parametrize(
    "raw_message",
    [
        pytest.param(
            {
                "payload": {
                    "parts": [
                        {
                            "partId": "0",
                            "mimeType": "application/pdf",
                            "filename": "invoice.pdf",
                            "body": {
                                "attachmentId": "this-is-the-attachment-id",
                            },
                        },
                    ],
                }
            },
            id="single payload part",
        ),
        pytest.param(
            {
                "payload": {
                    "parts": [
                        {
                            "partId": "0",
                            "mimeType": "text/html",
                        },
                        {
                            "partId": "1",
                            "mimeType": "application/pdf",
                            "filename": "invoice.pdf",
                            "body": {
                                "attachmentId": "this-is-the-attachment-id",
                            },
                        },
                    ],
                }
            },
            id="multiple payload parts",
        ),
    ],
)
def test_get_attachment_id(raw_message):
    expected_value = "this-is-the-attachment-id"
    GmailService.get_attachment_id(message=raw_message) == expected_value
