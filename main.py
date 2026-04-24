#!/usr/bin/env python3
"""
Property24 Email Collator
Connects to an IMAP mailbox, finds Property24 enquiry emails,
and exports them as CSV, Excel, and/or HTML.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from imap_client import connect, fetch_property24_emails
from parser import parse_email
from output import to_csv, to_excel, to_html

load_dotenv()
console = Console()


def get_env(key: str, prompt: str, secret: bool = False) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        if secret:
            import getpass
            value = getpass.getpass(f"{prompt}: ")
        else:
            value = input(f"{prompt}: ").strip()
    return value


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collate Property24 enquiry emails from an IMAP mailbox."
    )
    parser.add_argument("--host", default="", help="IMAP server hostname (e.g. imap.gmail.com)")
    parser.add_argument("--port", type=int, default=0, help="IMAP port (default: 993 for SSL, 143 otherwise)")
    parser.add_argument("--no-ssl", action="store_true", help="Disable SSL (not recommended)")
    parser.add_argument("--username", default="", help="Email address / IMAP username")
    parser.add_argument("--password", default="", help="IMAP password (or app password)")
    parser.add_argument("--mailbox", default="INBOX", help="Mailbox folder to search (default: INBOX)")
    parser.add_argument("--out-dir", default=".", help="Directory to write output files (default: current dir)")
    parser.add_argument("--csv", action="store_true", help="Export to CSV")
    parser.add_argument("--excel", action="store_true", help="Export to Excel (.xlsx)")
    parser.add_argument("--html", action="store_true", help="Export to HTML report")
    parser.add_argument("--preview", action="store_true", help="Print a summary table to the terminal")
    return parser.parse_args()


def main() -> None:
    args = build_args()

    use_ssl = not args.no_ssl

    host = args.host or get_env("IMAP_HOST", "IMAP server (e.g. imap.gmail.com)")
    port = args.port or int(os.environ.get("IMAP_PORT", "993" if use_ssl else "143"))
    username = args.username or get_env("IMAP_USERNAME", "Email address")
    password = args.password or get_env("IMAP_PASSWORD", "Password / App password", secret=True)

    # Default to all three outputs if none specified
    do_csv = args.csv
    do_excel = args.excel
    do_html = args.html
    do_preview = args.preview
    if not any([do_csv, do_excel, do_html, do_preview]):
        do_csv = do_excel = do_html = True

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold blue]Property24 Email Collator[/bold blue]")
    console.print(f"Connecting to [cyan]{host}:{port}[/cyan] as [cyan]{username}[/cyan]...\n")

    try:
        conn = connect(host, port, username, password, use_ssl=use_ssl)
    except Exception as exc:
        console.print(f"[red]Connection failed:[/red] {exc}")
        sys.exit(1)

    enquiries = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Fetching emails from mailbox...", total=None)
        try:
            for raw in fetch_property24_emails(conn, mailbox=args.mailbox):
                progress.update(task, description=f"Parsing email: {raw.get('subject', '')[:60]}")
                parsed = parse_email(raw)
                enquiries.append(parsed)
        except Exception as exc:
            console.print(f"[red]Error fetching emails:[/red] {exc}")
            sys.exit(1)
        finally:
            conn.logout()

    if not enquiries:
        console.print("[yellow]No Property24 enquiry emails found.[/yellow]")
        sys.exit(0)

    # Sort newest first
    enquiries.sort(key=lambda e: e.get("date", ""), reverse=True)

    console.print(f"\nFound [bold green]{len(enquiries)}[/bold green] enquiries.\n")

    if do_preview:
        table = Table(title="Property24 Enquiries", show_lines=True)
        for header in ["Date", "Web Ref", "Enquirer", "Contact", "Email", "Price", "Address"]:
            table.add_column(header, overflow="fold")
        for e in enquiries:
            table.add_row(
                e.get("date", ""),
                e.get("web_ref", ""),
                e.get("enquirer_name", ""),
                e.get("contact_number", ""),
                e.get("enquirer_email", ""),
                e.get("price", ""),
                e.get("address", ""),
            )
        console.print(table)

    if do_csv:
        path = out_dir / "property24_enquiries.csv"
        to_csv(enquiries, str(path))
        console.print(f"[green]CSV saved:[/green]   {path}")

    if do_excel:
        path = out_dir / "property24_enquiries.xlsx"
        to_excel(enquiries, str(path))
        console.print(f"[green]Excel saved:[/green] {path}")

    if do_html:
        path = out_dir / "property24_enquiries.html"
        to_html(enquiries, str(path))
        console.print(f"[green]HTML saved:[/green]  {path}")

    console.print()


if __name__ == "__main__":
    main()
