"""Gmail OAuth2 token olusturucu.

Ilk kullanim oncesinde bir kez calistir:
    py scripts/setup_gmail.py

Tarayici acilacak, Google hesabina giris yap, izin ver.
token.json olusturulacak, bir daha calistirmana gerek yok.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.integrations.gmail_client import get_gmail_service

if __name__ == "__main__":
    print("Gmail OAuth2 kurulumu baslatiliyor...")
    service = get_gmail_service()
    profile = service.users().getProfile(userId="me").execute()
    print(f"Basarili! Gmail hesabi: {profile.get('emailAddress')}")
    print("token.json olusturuldu, artik mail gonderebilirsiniz.")
