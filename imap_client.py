import imaplib
import email
import socket
from email.header import decode_header
from datetime import datetime
from typing import Generator

CONNECT_TIMEOUT = 30   # seconds to establish connection
FETCH_TIMEOUT   = 120  # seconds to wait for a single FETCH response
BATCH_SIZE      = 200  # emails fetched per IMAP FETCH command


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
    # Set a socket-level timeout so the initial TCP connect cannot hang forever.
    socket.setdefaulttimeout(CONNECT_TIMEOUT)
    if use_ssl:
        conn = imaplib.IMAP4_SSL(host, port)
    else:
        conn = imaplib.IMAP4(host, port)
    # Switch to a longer timeout for data operations after login.
    conn.sock.settimeout(FETCH_TIMEOUT)
    conn.login(username, password)
    return conn


def _parse_message(msg: email.message.Message) -> dict:
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

    return {
        "subject": subject,
        "date": date,
        "reply_to": reply_to,
        "plain_body": plain_body,
        "html_body": html_body,
    }


def fetch_property24_emails(conn: imaplib.IMAP4, mailbox: str = "INBOX") -> Generator[dict, None, None]:
    conn.select(mailbox, readonly=True)

    _, message_ids = conn.search(None, 'FROM "no-reply@property24.com"')

    ids = message_ids[0].split()
    if not ids:
        return

    # Fetch in batches to reduce round-trips and avoid per-email timeouts.
    for i in range(0, len(ids), BATCH_SIZE):
        batch = ids[i : i + BATCH_SIZE]
        id_set = b",".join(batch)
        _, msg_data = conn.fetch(id_set, "(RFC822)")

        # imaplib returns a flat list: [(b'N (RFC822 {size}', raw_bytes), b')', ...]
        for item in msg_data:
            if not isinstance(item, tuple):
                continue
            raw = item[1]
            if not isinstance(raw, bytes):
                continue
            msg = email.message_from_bytes(raw)
            yield _parse_message(msg)
