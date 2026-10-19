# Deployment

One server runs everything behind Caddy, which gets and renews the HTTPS certificate on its own. Only ports 22, 80 and 443 are open. Postgres, Redis, the API and the dashboard sit on an internal Docker network and are never published.

## One-time setup

1. Create an Ubuntu 22.04 or 24.04 server and point a DNS `A` record for your domain at it.
2. Generate a deploy key on your machine: `ssh-keygen -t ed25519 -f hakiki_deploy -C deploy@ci`.
3. Copy `infra/provision.sh` to the server and run it as root with the public key:
   `DEPLOY_PUBKEY="$(cat hakiki_deploy.pub)" ./provision.sh`. It installs Docker, opens the firewall, turns off password and root SSH login and enables fail2ban. Test `ssh deploy@<host>` in a second terminal before closing the first.
4. On the server, as `deploy`, copy `infra/.env.prod.example` to `/opt/hakiki/.env`, fill in every value (generate secrets with `openssl rand`), and `chmod 600` it.
5. Add these GitHub repository secrets under an environment called `production`:

   | Secret | Value |
   |---|---|
   | `DEPLOY_HOST` | server IP or hostname |
   | `DEPLOY_USER` | `deploy` |
   | `DEPLOY_SSH_KEY` | contents of the private key `hakiki_deploy` |
   | `DEPLOY_KNOWN_HOSTS` | output of `ssh-keyscan -t ed25519 <host>` |
   | `DEPLOY_DOMAIN` | the domain, for example `hakiki.example.com` |
   | `SMOKE_EMAIL`, `SMOKE_PASSWORD` | the demo login created by the seed script |

6. After the first deploy, create the demo data once:
   `docker compose -f docker-compose.prod.yml exec api python -m scripts.seed`.
7. Install the nightly backup: `(crontab -l; echo "17 2 * * * /opt/hakiki/infra/backup.sh") | crontab -`.

## Every deploy

Merging to `main` runs CI. When CI passes, the Deploy workflow builds the API and dashboard images, pushes them to GHCR, copies the compose file to the server, pulls and restarts, then runs `infra/smoke.sh` against the live URL (login, check, history, audit chain). Secrets live in GitHub and on the server, never in the repository.

## Roll back

`ssh deploy@<host>`, edit `API_IMAGE` and `DASHBOARD_IMAGE` in `/opt/hakiki/.env` to a previous commit tag, then `docker compose -f docker-compose.prod.yml up -d`.

## Check it locally first

`DOMAIN=localhost` makes Caddy issue an internal certificate, so the whole stack can be exercised on a laptop with `infra/smoke.sh https://localhost --insecure`.
