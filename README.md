# Property24 Email Collator

Automatically finds all Property24 enquiry emails in your mailbox and exports them into a spreadsheet and HTML report — no manual downloading required.

## What you need

- Python 3.10 or later
- Your email address and password (see note below on Gmail/Outlook)

## Setup (one time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create your credentials file
cp .env.example .env
# Then open .env in any text editor and fill in your details
```

### Finding your IMAP server

| Email provider | IMAP server |
|---|---|
| Gmail | `imap.gmail.com` |
| Outlook / Hotmail / Office 365 | `outlook.office365.com` |
| Yahoo Mail | `imap.mail.yahoo.com` |
| Other | Check your webmail's Settings → Account → IMAP |

> **Gmail / Outlook with 2-factor authentication:** Your normal password won't work. You need to generate a free **App Password**:
> - Gmail: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
> - Outlook: Settings → Security → Advanced security → App passwords

## Running

```bash
python main.py
```

This will prompt for any credentials not already in your `.env` file, then produce three files in the current folder:

| File | Contents |
|---|---|
| `property24_enquiries.xlsx` | Excel spreadsheet (clickable links) |
| `property24_enquiries.csv` | Plain CSV for any spreadsheet app |
| `property24_enquiries.html` | Formatted report — open in any browser |

### Options

```bash
# Preview results in the terminal without saving files
python main.py --preview

# Save to a specific folder
python main.py --out-dir ~/Desktop/enquiries

# Only produce one format
python main.py --csv
python main.py --excel
python main.py --html

# Search a folder other than INBOX (e.g. if you filtered emails there)
python main.py --mailbox "Property24"
```
