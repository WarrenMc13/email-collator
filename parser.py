import re
from typing import Optional
from bs4 import BeautifulSoup


def _extract_between(text: str, label: str, next_labels: list[str]) -> Optional[str]:
    """Extract text that follows a label, stopping at the next label."""
    pattern = rf"{re.escape(label)}\s*:?\s*\n(.*?)(?={'|'.join(re.escape(l) for l in next_labels)}|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _clean(text: str) -> str:
    # Remove link reference markers like [1], [2]
    text = re.sub(r"\s*\[\d+\]", "", text)
    return " ".join(text.split())


def parse_plain_text(body: str) -> dict:
    result = {}

    # Web reference (P24-XXXXXXXXX)
    web_ref_match = re.search(r"(P24-\d+)", body)
    result["web_ref"] = web_ref_match.group(1) if web_ref_match else ""

    # Price
    price_match = re.search(r"(R\s[\d\s]+)", body)
    result["price"] = _clean(price_match.group(1)) if price_match else ""

    # Property type — line with "Bedroom" or "Studio" etc before the location block
    prop_type_match = re.search(r"([\w\s/]+(?:Bedroom|Studio|Bachelor|Duplex|Penthouse)[^\n]*)", body, re.IGNORECASE)
    result["property_type"] = _clean(prop_type_match.group(1)) if prop_type_match else ""

    # Address
    address_block = _extract_between(body, "Address", ["Web ref", "Enquiry by", "Contact Number", "Email Address", "Message"])
    result["address"] = _clean(address_block) if address_block else ""

    # Enquiry by (name)
    enquiry_block = _extract_between(body, "Enquiry by", ["Contact Number", "Email Address", "Message", "Kind Regards"])
    result["enquirer_name"] = _clean(enquiry_block) if enquiry_block else ""

    # Contact number — grab the phone number itself
    contact_block = _extract_between(body, "Contact Number", ["Email Address", "Message", "Kind Regards"])
    if contact_block:
        phone_match = re.search(r"([\d\s]{7,})", contact_block)
        result["contact_number"] = phone_match.group(1).strip() if phone_match else _clean(contact_block)
    else:
        result["contact_number"] = ""

    # WhatsApp link from the raw body
    wa_match = re.search(r"https://wa\.me/(\d+)", body)
    result["whatsapp_number"] = wa_match.group(1) if wa_match else ""

    # Email address
    email_block = _extract_between(body, "Email Address", ["Message", "Kind Regards", "Need help"])
    if email_block:
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", email_block, re.IGNORECASE)
        result["enquirer_email"] = email_match.group(0) if email_match else _clean(email_block)
    else:
        # Fall back to Reply-To header (set by caller)
        result["enquirer_email"] = ""

    # Message
    message_block = _extract_between(body, "Message", ["Kind Regards", "Need help", "Property24"])
    result["message"] = _clean(message_block) if message_block else ""

    # Property URL
    url_match = re.search(r"(https://www\.property24\.com/for-sale/[^\s\]]+)", body)
    result["property_url"] = url_match.group(1) if url_match else ""

    return result


def parse_html(html_body: str) -> dict:
    soup = BeautifulSoup(html_body, "lxml")
    text = soup.get_text(separator="\n")
    return parse_plain_text(text)


def parse_email(raw: dict) -> dict:
    """Parse a raw email dict (from imap_client) into structured enquiry data."""
    body = raw.get("plain_body", "")
    html = raw.get("html_body", "")

    # Prefer plain text; fall back to stripping HTML
    if body.strip():
        data = parse_plain_text(body)
    elif html.strip():
        data = parse_html(html)
    else:
        data = {}

    # Fill gaps from email headers
    data["date"] = raw.get("date").strftime("%Y-%m-%d %H:%M") if raw.get("date") else ""
    data["subject"] = raw.get("subject", "")

    # Enquirer email from Reply-To header if parser missed it
    if not data.get("enquirer_email"):
        reply_to = raw.get("reply_to", "")
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", reply_to, re.IGNORECASE)
        data["enquirer_email"] = email_match.group(0) if email_match else ""

    # Enquirer name from Reply-To header if parser missed it
    if not data.get("enquirer_name"):
        name_match = re.match(r"^([^<]+)<", raw.get("reply_to", ""))
        data["enquirer_name"] = name_match.group(1).strip() if name_match else ""

    return data
