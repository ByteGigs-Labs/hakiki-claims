#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu 22.04/24.04 server. Run as root:
#   DEPLOY_PUBKEY="ssh-ed25519 AAAA... deploy@ci" ./provision.sh
set -euo pipefail

DEPLOY_USER="${DEPLOY_USER:-deploy}"
APP_DIR="${APP_DIR:-/opt/hakiki}"

[[ $EUID -eq 0 ]] || { echo "run as root" >&2; exit 1; }
[[ -n "${DEPLOY_PUBKEY:-}" ]] || { echo "set DEPLOY_PUBKEY to the public key CI will deploy with" >&2; exit 1; }

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl ufw fail2ban unattended-upgrades

if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi

id -u "$DEPLOY_USER" >/dev/null 2>&1 || adduser --disabled-password --gecos "" "$DEPLOY_USER"
usermod -aG docker "$DEPLOY_USER"
install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"
echo "$DEPLOY_PUBKEY" > "/home/$DEPLOY_USER/.ssh/authorized_keys"
chown "$DEPLOY_USER:$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh/authorized_keys"
chmod 600 "/home/$DEPLOY_USER/.ssh/authorized_keys"

install -d -m 750 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "$APP_DIR" "$APP_DIR/infra" "$APP_DIR/backups"

cat > /etc/ssh/sshd_config.d/99-hakiki.conf <<'CONF'
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
X11Forwarding no
MaxAuthTries 3
CONF
sshd -t

ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

systemctl enable --now fail2ban
dpkg-reconfigure -f noninteractive unattended-upgrades

systemctl reload ssh || systemctl reload sshd
echo "Done. Test 'ssh $DEPLOY_USER@<host>' in a second terminal before closing this session."
