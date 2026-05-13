"""Gmail API ile tedarikci mail entegrasyonu.

Ilk calistirildiginda OAuth2 akisi baslar, token.json olusturulur.
Sonraki calismalarda token.json kullanilir.
"""

import base64
import logging
import os
from email.mime.text import MIMEText
from pathlib import Path


logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token.json")


def get_gmail_service():
    """Gmail API servisini olustur, gerekirse OAuth akisini baslatir."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Gmail entegrasyonu icin su paketleri kurulu olmali: "
            "pip install google-auth-oauthlib google-api-python-client"
        ) from exc

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "credentials.json bulunamadi. "
                    "Google Cloud Console'dan OAuth2 credentials indirin."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_email(to: str, subject: str, body: str, sender: str = "me") -> dict:
    """Gmail API ile mail gonder."""
    service = get_gmail_service()

    message = MIMEText(body, "plain", "utf-8")
    message["to"] = to
    message["subject"] = subject
    message["from"] = sender

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    result = service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()

    logger.info("Email sent to %s, message_id=%s", to, result.get("id"))
    return result


async def send_supplier_email(
    supplier_email: str,
    product_name: str,
    quantity: float,
    unit: str,
    urgency: str = "normal",
    draft_text: str | None = None,
) -> dict:
    """Tedarikci mail gonder. draft_text verilmezse otomatik olusturur."""
    if draft_text:
        body = draft_text
        subject = f"Sipariş Talebi - {product_name}"
    else:
        urgency_str = "ACİL " if urgency == "urgent" else ""
        subject = f"{urgency_str}Sipariş Talebi - {product_name}"
        body = f"""Sayın Tedarikçimiz,

{product_name} ürününden {quantity} {unit} sipariş vermek istiyoruz.

Lütfen en kısa sürede stok durumunu ve teslimat tarihini bildiriniz.

{"Bu talep acildir, lütfen öncelikli değerlendirin." if urgency == "urgent" else ""}

Saygılarımızla,
KOBİ Asistanı Sistemi
"""

    try:
        result = send_email(
            to=supplier_email,
            subject=subject,
            body=body,
        )
        return {
            "success": True,
            "message_id": result.get("id"),
            "to": supplier_email,
            "subject": subject,
        }
    except Exception as e:
        logger.exception("Failed to send supplier email to %s", supplier_email)
        return {"success": False, "error": str(e)}
