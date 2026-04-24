import os
import tempfile
from datetime import date, timedelta

import streamlit as st

from imap_client import connect, fetch_property24_emails
from parser import parse_email
from output import to_csv, to_excel, to_html

st.set_page_config(page_title="Property24 Email Collator", page_icon="🏠", layout="centered")

st.title("🏠 Property24 Email Collator")
st.caption("Connect to your webmail, pull Property24 enquiries, download as Excel / CSV / HTML.")

with st.form("credentials"):
    st.subheader("Mail server")
    col_host, col_port = st.columns([3, 1])
    host = col_host.text_input("IMAP host", placeholder="mail.yourdomain.com")
    port = col_port.number_input("Port", value=993, min_value=1, max_value=65535)
    use_ssl = st.checkbox("Use SSL", value=True)

    st.subheader("Login")
    username = st.text_input("Email address", placeholder="you@yourdomain.com")
    password = st.text_input("Password", type="password")
    mailbox = st.text_input("Mailbox folder", value="INBOX")

    st.subheader("Sender filter")
    sender = st.text_input("From address", value="no-reply@property24.com")

    st.subheader("Date range")
    col_from, col_to = st.columns(2)
    date_from = col_from.date_input("From", value=date.today() - timedelta(days=30))
    date_to = col_to.date_input("To", value=date.today())

    submitted = st.form_submit_button("Fetch enquiries", use_container_width=True)

if submitted:
    if not host or not username or not password:
        st.error("IMAP host, email address and password are required.")
        st.stop()

    if date_from > date_to:
        st.error("'From' date must be before 'To' date.")
        st.stop()

    with st.spinner(f"Connecting to {host}:{port}..."):
        try:
            conn = connect(host, int(port), username, password, use_ssl=use_ssl)
        except Exception as e:
            st.error(f"Connection failed: {e}")
            st.stop()

    enquiries = []
    progress = st.progress(0, text="Fetching emails...")
    try:
        emails = list(fetch_property24_emails(
            conn,
            mailbox=mailbox,
            sender=sender,
            date_from=date_from,
            date_to=date_to,
        ))
        total = len(emails)
        if total == 0:
            st.warning("No matching emails found in that date range.")
            st.stop()
        for i, raw in enumerate(emails):
            progress.progress((i + 1) / total, text=f"Parsing {i + 1}/{total}: {raw.get('subject', '')[:60]}")
            enquiries.append(parse_email(raw))
    except Exception as e:
        st.error(f"Error fetching emails: {e}")
        st.stop()
    finally:
        conn.logout()

    enquiries.sort(key=lambda e: e.get("date", ""), reverse=True)
    progress.empty()

    st.success(f"Found **{len(enquiries)}** enquiries.")

    st.dataframe(
        [{
            "Date": e.get("date", ""),
            "Web Ref": e.get("web_ref", ""),
            "Name": e.get("enquirer_name", ""),
            "Contact": e.get("contact_number", ""),
            "Email": e.get("enquirer_email", ""),
            "Price": e.get("price", ""),
            "Address": e.get("address", ""),
        } for e in enquiries],
        use_container_width=True,
    )

    st.subheader("Download")
    col1, col2, col3 = st.columns(3)

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "enquiries.csv")
        xlsx_path = os.path.join(tmpdir, "enquiries.xlsx")
        html_path = os.path.join(tmpdir, "enquiries.html")

        to_csv(enquiries, csv_path)
        to_excel(enquiries, xlsx_path)
        to_html(enquiries, html_path)

        with open(csv_path, "rb") as f:
            col1.download_button("⬇ CSV", f.read(), "property24_enquiries.csv", "text/csv", use_container_width=True)
        with open(xlsx_path, "rb") as f:
            col2.download_button("⬇ Excel", f.read(), "property24_enquiries.xlsx",
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 use_container_width=True)
        with open(html_path, "rb") as f:
            col3.download_button("⬇ HTML", f.read(), "property24_enquiries.html", "text/html", use_container_width=True)
