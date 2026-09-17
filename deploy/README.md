# Azure VM deployment runbook

This runbook deploys Career Platform on an Ubuntu Azure VM. Nginx is the only
public web server: Uvicorn listens exclusively on `127.0.0.1:8000`. The SQLite
database and backups stay outside the Git checkout under protected directories.
Replace `YOUR_*` placeholders before running commands.

## 1. Create and restrict the VM

From a workstation with the Azure CLI signed in, create an Ubuntu VM and allow
only SSH, HTTP, and HTTPS in its network security group. Do not create a rule
for port 8000.

```bash
az group create --name career-platform-rg --location eastus
az vm create \
  --resource-group career-platform-rg \
  --name career-platform-vm \
  --image Ubuntu2404 \
  --admin-username YOUR_ADMIN_USER \
  --generate-ssh-keys \
  --public-ip-sku Standard \
  --nsg-rule SSH
az vm open-port --resource-group career-platform-rg --name career-platform-vm --port 80
az vm open-port --resource-group career-platform-rg --name career-platform-vm --port 443
```

SSH to the public IP reported by Azure. Confirm the NSG contains no inbound
rule for `8000`; that port must never be exposed publicly.

## 2. Install system dependencies and uv

```bash
sudo apt-get update
sudo apt-get install -y git nginx sqlite3 certbot python3 python3-venv curl
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo install -m 755 "$HOME/.local/bin/uv" /usr/local/bin/uv
```

Create the dedicated non-root service account and protected persistent
directories:

```bash
sudo useradd --system --create-home --home-dir /home/career-platform \
  --user-group --shell /usr/sbin/nologin career-platform
sudo install -d -m 700 -o career-platform -g career-platform /var/lib/career-platform
sudo install -d -m 700 -o career-platform -g career-platform /var/backups/career-platform
```

## 3. Clone and configure the application

```bash
sudo install -d -m 755 /srv
sudo -u career-platform git clone YOUR_REPOSITORY_URL /srv/career-platform
sudo install -d -m 750 -o root -g career-platform /etc/career-platform
sudo tee /etc/career-platform/environment >/dev/null <<'EOF'
DATABASE_URL=sqlite:////var/lib/career-platform/resume.db
EOF
sudo chown root:career-platform /etc/career-platform/environment
sudo chmod 640 /etc/career-platform/environment
```

The absolute `DATABASE_URL` deliberately points outside `/srv/career-platform`;
do not put a production database in the checkout or commit an environment file.
Install the locked production dependencies, migrate, and seed under the service
account:

```bash
sudo -u career-platform bash -c '
  cd /srv/career-platform
  DATABASE_URL=sqlite:////var/lib/career-platform/resume.db /usr/local/bin/uv sync --locked --no-dev
  DATABASE_URL=sqlite:////var/lib/career-platform/resume.db /usr/local/bin/uv run alembic upgrade head
  DATABASE_URL=sqlite:////var/lib/career-platform/resume.db /usr/local/bin/uv run python -m app.seed
'
```

## 4. Install systemd and Nginx

Install the systemd unit, then issue the TLS certificate before enabling the
TLS Nginx site. Certbot's standalone mode needs port 80 temporarily, so stop
the default Nginx service first.

```bash
sudo install -m 644 /srv/career-platform/deploy/systemd/career-platform.service \
  /etc/systemd/system/career-platform.service
sudo systemctl daemon-reload
sudo systemctl enable --now career-platform

sudo systemctl stop nginx
sudo certbot certonly --standalone -d YOUR_DOMAIN --email YOUR_EMAIL --agree-tos --no-eff-email
```

Edit both `server_name` values and the two Let’s Encrypt path components in
`deploy/nginx/career-platform.conf` from `your-domain.example` to `YOUR_DOMAIN`,
then enable it:

```bash
sudo install -m 644 /srv/career-platform/deploy/nginx/career-platform.conf \
  /etc/nginx/sites-available/career-platform
sudo ln -s /etc/nginx/sites-available/career-platform /etc/nginx/sites-enabled/career-platform
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

No certificate or private key belongs in this repository. Certbot renewals use
the installed system timer; verify it with `sudo systemctl status certbot.timer`.

## 5. Deploy updates safely

Before every deployment or schema migration, create a verified SQLite backup.
The deployment script refuses to continue if the backup, migration, or seed
step fails. After updating the checkout to the intended revision, run:

```bash
sudo -u career-platform bash -c '
  cd /srv/career-platform
  DATABASE_URL=sqlite:////var/lib/career-platform/resume.db \
    ./deploy/scripts/deploy.sh \
    /var/lib/career-platform/resume.db \
    /var/backups/career-platform
'
sudo systemctl restart career-platform
```

Verify the private upstream and the public HTTPS endpoint:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail --location https://YOUR_DOMAIN/health
sudo systemctl status career-platform --no-pager
```

## 6. Practice a restore without replacing production

Stop the service before any real recovery. For a safe restore drill, restore
the latest backup to a new file, check it, then remove the drill file:

```bash
BACKUP_FILE="$(find /var/backups/career-platform -maxdepth 1 -type f -name '*.db' -print -quit)"
test -n "$BACKUP_FILE"
sudo -u career-platform /srv/career-platform/deploy/scripts/restore-sqlite.sh \
  "$BACKUP_FILE" /var/lib/career-platform/restore-drill.db
sqlite3 /var/lib/career-platform/restore-drill.db "PRAGMA integrity_check;"
sudo rm /var/lib/career-platform/restore-drill.db
```

For a real restore, stop `career-platform`, keep the current database as an
additional backup, restore to a new target, atomically arrange the approved
cutover, and start the service. The restore script intentionally never
overwrites an existing database.
