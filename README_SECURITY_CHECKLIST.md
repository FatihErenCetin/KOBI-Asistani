# GitHub’a Paylaşmadan Önce Güvenlik Kontrolü

Bu dosya, projeyi public GitHub reposuna koymadan önce gizli bilgileri temizlemek için kullanılır.

## Paylaşılmaması Gereken Dosyalar

```text
.env
.env.local
frontend/.env.local
credentials.json
token.json
gmail_token.json
google_token.json
client_secret*.json
ngrok.yml
.venv/
node_modules/
frontend/node_modules/
.next/
frontend/.next/
__pycache__/
*.log
```

## .gitignore İçeriği

```gitignore
.env
.env.*
!.env.example
frontend/.env.local
credentials.json
token.json
gmail_token.json
google_token.json
client_secret*.json
ngrok.yml
.venv/
node_modules/
frontend/node_modules/
.next/
frontend/.next/
__pycache__/
*.pyc
*.log
```

## Git Takibinden Çıkarma

Dosyaları bilgisayardan silmeden Git takibinden çıkarmak için:

```powershell
git rm --cached .env
git rm --cached frontend/.env.local
git rm --cached credentials.json
git rm --cached token.json
git rm --cached gmail_token.json
git rm --cached google_token.json
```

## Gizli Bilgi Arama

```powershell
Select-String -Path .\* -Pattern "GEMINI_API_KEY|GEMINI_API_KEYS|TELEGRAM_BOT_TOKEN|AIza|bot[0-9]|client_secret|token" -Recurse
```

## Kritik Uyarı

Eğer herhangi bir key veya token daha önce GitHub’a pushlandıysa, dosyayı silmek yeterli değildir. O key/token iptal edilmeli ve yenisi oluşturulmalıdır.
