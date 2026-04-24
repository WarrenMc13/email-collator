import imaplib
import email
from email.header import decode_header
from datetime import datetime
from typing import Generator


def _decode_header_value(value: str) -> str:
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def connect(host: str, port: int, username: str, password: str, use_ssl: bool = True) -> imaplib.IMAP4:
    if use_ssl:
        conn = imaplib.IMAP4_SSL(host, port)
    else:
        conn = imaplib.IMAP4(host, port)
    conn.login(username, password)
    return conn


def fetch_property24_emails(conn: imaplib.IMAP4, mailbox: str = "INBOX") -> Generator[dict, None, None]:
    conn.select(mailbox, readonly=True)

    # Search for emails from Property24's no-reply address
    _, message_ids = conn.search(None, 'FROM "no-reply@property24.com"')

    ids = message_ids[0].split()
    for msg_id in ids:
        _, msg_data = conn.fetch(msg_id, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        subject = _decode_header_value(msg.get("Subject", ""))
        date_str = msg.get("Date", "")
        reply_to = msg.get("Reply-To", "")

        try:
            date = email.utils.parsedate_to_datetime(date_str)
        except Exception:
            date = None

        plain_body = ""
        html_body = ""
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    plain_body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    html_body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")

        yield {
            "subject": subject,
            "date": date,
            "reply_to": reply_to,
            "plain_body": plain_body,
            "html_body": html_body,
        }
