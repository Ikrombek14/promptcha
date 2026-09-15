#!/usr/bin/env bash
# Serverda (root) ishlaydi: GitHub Actions `ssh -n ... bash scripts/ci-deploy.sh <sha>` bilan chaqiradi.
# Repo allaqachon origin/main ga yangilangan. Qadamlar: zaxira → API → migratsiya → web build → restart → tekshiruv.
set -euo pipefail
SHA="${1:-$(git rev-parse HEAD)}"
APP=/opt/promptcha/app
export PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin
UV=/root/.local/bin/uv

step() { echo; echo "=== $*"; }

step "commit $SHA"
git config --global --add safe.directory "$APP" >/dev/null 2>&1 || true
[ "$(git -C "$APP" rev-parse HEAD)" = "$SHA" ] || { echo "HEAD mos emas: $(git -C "$APP" rev-parse HEAD)"; exit 1; }
echo "$SHA" > "$APP/COMMIT"

step "zaxira (migratsiyadan oldin)"
mkdir -p /opt/promptcha/backups
BK="/opt/promptcha/backups/pre-migrate-$(date +%Y%m%d-%H%M%S).sql.gz"
sudo -u postgres pg_dump promptcha | gzip > "$BK"
[ -s "$BK" ] || { echo "zaxira olinmadi — toʻxtadi"; exit 1; }
ls -1t /opt/promptcha/backups/pre-migrate-*.sql.gz | tail -n +31 | xargs -r rm -f
echo "$BK"

step "api"
cd "$APP/api"
$UV sync --no-dev --python 3.12 -q
./.venv/bin/python -c "import app.main"
./.venv/bin/alembic upgrade head 2>&1 | tail -3

step "web"
cd "$APP/web"
rm -f .env.local
npm ci --no-audit --no-fund --loglevel=error
npm run build 2>&1 | grep -E "Compiled|error|Error" | head -5

step "systemd"
cp "$APP/deploy/robbit/promptcha-api.service" /etc/systemd/system/promptcha-api.service
cp "$APP/deploy/robbit/promptcha-web.service" /etc/systemd/system/promptcha-web.service
chown -R promptcha:promptcha /opt/promptcha/app /opt/promptcha/backups
systemctl daemon-reload
systemctl restart promptcha-api promptcha-web
sleep 6
systemctl is-active promptcha-api promptcha-web

step "tekshiruv"
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s -m 5 http://127.0.0.1:8010/api/health | grep -q "\"status\": *\"ok\""; then break; fi
  sleep 2
done
curl -s -m 10 http://127.0.0.1:8010/api/health; echo
curl -s -m 15 -o /dev/null -w "web /uz/app: %{http_code}\n" http://127.0.0.1:3010/uz/app
echo "DEPLOY OK"
