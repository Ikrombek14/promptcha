# Promptcha — serverga oʻrnatish (Ubuntu 24.04, bitta VPS)

> **Jonli deploy (2026-09-15):** Robbit serveri `169.58.130.201`, Caddy orqali TLS, portlar 8010/3010,
> `deploy/robbit/` fayllari, `git push origin main` → GitHub Actions → `scripts/ci-deploy.sh`.
> Tafsilot CLAUDE.md «Deploy» boʻlimida. Quyidagi yoʻriqnoma — Nginx'li alohida server uchun umumiy variant.

Xavfsizlik modeli: API (`:8000`) va Next (`:3000`) faqat `127.0.0.1` da; tashqaridan faqat Nginx (443).
API har soʻrovda Nginx qoʻshgan maxfiy `X-Internal-Key`ni, brauzerning `Origin`ini va `X-Requested-With`ni tekshiradi;
guest limitlari bazada (`usage_log`), daqiqalik limitlar IP boʻyicha. Sirlar faqat `.env`da (chmod 600).

## 1. Server tayyorlash

```bash
apt update && apt upgrade -y
apt install -y nginx certbot python3-certbot-nginx postgresql-16 ufw fail2ban git curl
# Python 3.12 + uv, Node 22 (NodeSource) oʻrnatiladi
curl -LsSf https://astral.sh/uv/install.sh | sh

ufw default deny incoming && ufw default allow outgoing
ufw allow OpenSSH && ufw allow 'Nginx Full' && ufw enable
systemctl enable --now fail2ban

# SSH: faqat kalit bilan
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config && systemctl restart ssh

adduser --system --group --home /srv/promptcha promptcha
```

PostgreSQL faqat lokal tinglaydi (default). Baza va kuchli parol:

```bash
sudo -u postgres psql -c "CREATE USER promptcha WITH PASSWORD '$(openssl rand -base64 24)';"   # parolni saqlang
sudo -u postgres psql -c "CREATE DATABASE promptcha OWNER promptcha;"
```

## 2. Kod va sirlar

```bash
cd /srv/promptcha && git clone <repo> . && chown -R promptcha:promptcha /srv/promptcha
cp api/.env.example api/.env && chmod 600 api/.env
```

`api/.env` da majburiy (aks holda API ishga tushmaydi — `Settings.production_problems`):

| Kalit | Qiymat |
|---|---|
| `APP_ENV` | `production` |
| `APP_SECRET`, `JWT_SECRET`, `INTERNAL_API_KEY` | `openssl rand -hex 32` (uchtasi har xil) |
| `TRUST_PROXY` | `true` |
| `FRONTEND_URL`, `CORS_ORIGINS` | `https://promptcha.uz` |
| `DATABASE_URL` | `postgresql+asyncpg://promptcha:<parol>@localhost:5432/promptcha` |
| AI kalitlari | `GROQ_API_KEY`, `GEMINI_API_KEY` … (pullik tarif tavsiya etiladi) |

`deploy/nginx.conf` ichidagi `X-Internal-Key` qiymatini `INTERNAL_API_KEY` bilan **bir xil** qiling.

## 3. Build va migratsiya

```bash
cd /srv/promptcha/api && sudo -u promptcha uv sync --no-dev && sudo -u promptcha uv run alembic upgrade head
cd /srv/promptcha/web && sudo -u promptcha npm ci && sudo -u promptcha npm run build
```

## 4. Xizmatlar va Nginx

```bash
cp deploy/promptcha-api.service deploy/promptcha-web.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now promptcha-api promptcha-web
cp deploy/nginx.conf /etc/nginx/sites-available/promptcha.uz
ln -s /etc/nginx/sites-available/promptcha.uz /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
certbot --nginx -d promptcha.uz -d www.promptcha.uz
```

Cloudflare DNS: A yozuv → VPS IP, proxy yoqilgan boʻlsa SSL rejimi «Full (strict)».

## 5. Tekshirish

```bash
curl -s https://promptcha.uz/api/health                       # {"status":"ok"}
curl -s -o /dev/null -w "%{http_code}\n" https://promptcha.uz/api/docs     # 404
curl -s -X POST https://promptcha.uz/api/prompts/analyze -H "Content-Type: application/json" -d '{"text":"salom dunyo"}'
# → 403 "Soʻrov rad etildi" (sayt sarlavhalarisiz kirib boʻlmaydi)
curl -s -o /dev/null -w "%{http_code}\n" http://<VPS-IP>:8000/api/health  # ulanmaydi (faqat lokal)
```

## Har deploy

```bash
cd /srv/promptcha && sudo -u promptcha git pull
cd api && sudo -u promptcha uv sync --no-dev && sudo -u promptcha uv run alembic upgrade head && cd ..
cd web && sudo -u promptcha npm ci && sudo -u promptcha npm run build && cd ..
systemctl restart promptcha-api promptcha-web
```

Deploy'dan oldin: `uv run pytest`, `npm run lint && npm test`, `.env.example` yangi, migratsiya bor.

## Zaxira

```bash
sudo -u postgres pg_dump promptcha | gzip > /var/backups/promptcha-$(date +%F).sql.gz   # cron: har kuni 03:00
```
