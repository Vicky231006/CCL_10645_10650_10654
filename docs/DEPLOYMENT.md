# Deploying Resumo on AWS — a complete, cost-first, beginner's guide

> Audience: someone who has **never used AWS before**. Every click, every command
> and every value you must type is written out. If a step is optional it is clearly
> marked. Nothing here requires you to already own a domain, and the recommended
> path fits inside the AWS Free Tier / promotional credits so it costs **$0** if you
> follow the teardown instructions when you finish.

Resumo is three things running together:

| Piece | What it is | Runs as |
| --- | --- | --- |
| **API** | FastAPI (Python) service, all business logic | Docker container `resumo-backend` on port `8000` |
| **Web** | React single-page app served by Nginx, proxies `/api` to the API | Docker container `resumo-frontend` on port `80` |
| **Database** | PostgreSQL (SQLite is only for local dev) | Docker container `resumo-db` (Path A) or RDS (Path B) |

Everything is configured through **environment variables**. No secret is baked into
an image. The repository already contains:

- `backend/Dockerfile`, `frontend/Dockerfile` — build recipes
- `docker-compose.yml` — runs all three containers together
- `.env.example` (root) and `backend/.env.example` — templates
- `backend/entrypoint.sh` — optionally runs database migrations on boot
- `docs/ARCHITECTURE.md` — how the app is built

---

## 0. Choose your path (read this first)

There are two ways to deploy. **Both are covered end-to-end** below.

| | **Path A — one small server (recommended)** | **Path B — managed AWS services** |
| --- | --- | --- |
| What runs in AWS | One EC2 instance running Docker Compose (API + Web + Postgres) | EC2 (API) + RDS (Postgres) + S3 (files) + CloudFront (Web) + SSM + CloudWatch |
| Cost | ~$0 (uses credits slowly; can stop the box any time) | Uses credits faster; RDS/CloudFront are billed |
| Setup time | 30–45 minutes | 2–3 hours |
| Difficulty | Easy (copy-paste) | Medium |
| Best for | A college demo/defense, a portfolio site, learning | A "real" production-shaped deployment |
| Risk of surprise bill | Very low | Low if you follow the teardown checklist |

> **If you are unsure, do Path A.** It gives you a working public URL today and you
> can add Path B services later without changing the application code.

### How AWS free-tier works in 2026 (important — this changed)

AWS changed its program on **15 July 2025**. If the account was created on or after
that date, you get:

- **$100 in promotional credits at sign-up**, plus **up to $100 more** by completing
  small activities (e.g. launching an EC2 instance, creating an RDS database).
- These **credits pay for usage**; the account is on the **Free plan**, which is
  auto-closed when the credits run out **or after 6 months**, whichever comes first.
- You are **not billed** on the Free plan unless you deliberately **upgrade to a Paid
  plan**. So the worst case is "the account closes", not "you get a big bill".
- **Always Free** services (30+ of them, available on both plans) include buckets,
  small Lambda usage, CloudWatch basics, DynamoDB, SNS/SQS, etc.
- **Free-tier-eligible EC2 instance types for new accounts** include
  `t3.micro`, `t3.small`, `t4g.micro`, `t4g.small` (and a couple of larger "flex"
  types). We use `t3.micro` (Intel) or `t4g.micro` (ARM/Graviton — slightly cheaper).

> The old "750 hours for 12 months" wording you will find in older tutorials applies
> **only to accounts created before 15 July 2025**. If your account is new, think in
> **credits**, not in months. Always confirm current numbers on the official
> **AWS Free Tier** page before you start.

**What is NOT free (avoid, or use sparingly):**
- NAT Gateway (~$32+/month) — **do not create one**; use a public subnet.
- Application/Network Load Balancer (~$16+/month) — not needed; Caddy/Nginx handles TLS.
- Secrets Manager (~$0.40/secret/month) — use **SSM Parameter Store (Standard)**, free.
- Route 53 hosted zone ($0.50/month) — optional; free alternatives are shown.
- ECS Fargate / App Runner — no meaningful free tier; that is why Path A uses plain EC2.

---

## 1. Create and secure your AWS account

1. Go to <https://aws.amazon.com/free/> and click **Create a free account**.
2. Enter an email and a strong password. Choose the **Free plan** (the one that does
   not bill you). AWS asks for a payment method to verify identity — it is not
   charged while you stay on the Free plan.
3. Pick a **region close to you** and remember it. This guide uses **`ap-south-1`
   (Mumbai)**. Whatever you choose, keep it identical everywhere, because resources
   in one region are invisible to another.
4. Sign in to the **AWS Management Console** (the web dashboard).

### 1.1 Turn on MFA for the root user (do not skip)

1. Top-right menu → **Security credentials** → **Multi-factor authentication (MFA)**
   → **Assign MFA device**. Use a free authenticator app.
2. Never use the root user for daily work. If you ever lose it, recovery is painful.

### 1.2 Create an admin user for yourself

1. In the search bar type **IAM** → open it → **Users** → **Create user**.
2. Name it `resumo-admin`, tick **Provide user access to the AWS Management Console**.
3. Choose **I want to create an IAM user**, set a password.
4. On the permissions step choose **Attach policies directly** →
   `AdministratorAccess` → create. (For a personal learning account this is fine.)
5. Open the new user → **Security credentials** → **Create access key** →
   choose **Command Line Interface (CLI)** → copy the **Access key ID** and
   **Secret access key**. You will paste them in section 2.

---

## 2. Install and configure the tools on your laptop

You need the **AWS CLI** (to run AWS commands) and will use **SSH** (built into
Windows 10/11, macOS and Linux) to reach the server.

### Windows (PowerShell)

```powershell
winget install --id Amazon.AWSCLI
```

Close and reopen PowerShell, then verify:

```powershell
aws --version
```

### macOS

```bash
brew install awscli
aws --version
```

### Linux (Debian/Ubuntu)

```bash
sudo apt-get update && sudo apt-get install -y unzip curl
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscli.zip
unzip awscli.zip && sudo ./aws/install
aws --version
```

### Configure your credentials

```bash
aws configure
# AWS Access Key ID     : <paste the resumo-admin key id>
# AWS Secret Access Key : <paste the resumo-admin secret>
# Default region name   : ap-south-1
# Default output format : json
```

Confirm it works:

```bash
aws sts get-caller-identity
```

You should see your account ID and the `resumo-admin` user. If you see an error,
re-run `aws configure`.

---

## 3. Set a budget and watch your credits (do this before anything else)

This prevents every "surprise bill" story you have ever heard.

### 3.1 A zero-spend budget alert

1. Console search → **Budgets** → **Create budget**.
2. **Use a template** → **Zero spend budget**. Enter your email. Create.
3. Add a second budget: **Monthly cost budget**, amount `1` USD, alert at 80%.

### 3.2 See your credit balance

1. Console search → **Billing and Cost Management** → **Home**.
2. The Free plan widget shows **credits remaining** and the **date the plan ends**.
3. Bookmark this page. Check it weekly.

> Rule of thumb for Path A: a `t3.micro` left running **24/7** costs roughly
> **$7–9/month** of usage. Your $100–$200 of credits therefore covers far more than
> the 6-month window. **Stop the instance when you are not demonstrating it** to
> make the credits last even longer.

---

## 4. Path A — one small server, deployed end-to-end

### 4.1 Create an SSH key pair

An SSH key is how you log into the server without a password.

1. Console search → **EC2** → in the left menu **Network & Security → Key Pairs**
   → **Create key pair**.
2. Name: `resumo-key`. Type: **RSA**. Format: **.pem** (macOS/Linux/Windows
   PowerShell) — use `.ppk` only if you specifically use PuTTY.
3. The file downloads automatically. On Windows move it to
   `C:\Users\<you>\.ssh\resumo-key.pem`.

Lock down the file's permissions (SSH refuses keys that are too open):

```powershell
# Windows PowerShell
icacls "$env:USERPROFILE\.ssh\resumo-key.pem" /inheritance:r /grant:r "$env:USERNAME:(R)"
```

```bash
# macOS / Linux
chmod 400 ~/.ssh/resumo-key.pem
```

### 4.2 Create a firewall rule set (security group)

1. EC2 → **Network & Security → Security Groups → Create security group**.
2. Name `resumo-web`, same VPC as default.
3. Inbound rules — add exactly these four:

| Type | Protocol | Port range | Source | Why |
| --- | --- | --- | --- | --- |
| SSH | TCP | 22 | **My IP** | so only you can log in |
| HTTP | TCP | 80 | 0.0.0.0/0 | the web app / TLS challenge |
| HTTPS | TCP | 443 | 0.0.0.0/0 | secure access |
| Custom TCP | TCP | 8000 | **My IP** | optional: hit the raw API while testing |

> Restricting SSH and `8000` to **My IP** is a simple, effective defence. The app's
> own ports (`80`/`443`) stay public because that is the point of a web app.

### 4.3 Launch the instance

1. EC2 → **Instances → Launch instances**.
2. **Name**: `resumo-app`.
3. **AMI**: **Amazon Linux 2023** (choose the *64-bit (x86)* variant; it is free-tier
   eligible). If you prefer ARM, see the note below.
4. **Instance type**: `t3.micro`. (If the console warns it is not free-tier eligible,
   pick whichever type *is* marked **Free tier eligible** — for new accounts that is
   `t3.micro`, `t3.small`, `t4g.micro` or `t4g.small`.)
5. **Key pair**: select `resumo-key`.
6. **Network settings** → **Select existing security group** → `resumo-web`.
7. **Configure storage**: change size to **20 GiB gp3** (still within the free
   allowance; the default 8 GiB is enough but 20 gives room for images).
8. Leave everything else default. **Launch instance**.

> **ARM note (`t4g.micro`, slightly cheaper):** choose AMI
> *Amazon Linux 2023 (64-bit ARM)* and instance type `t4g.micro`. All four images we
> use (`python:3.13-slim`, `node:22-alpine`, `postgres:16-alpine`, `nginx:1.27-alpine`)
> publish ARM64 builds, so the same `docker-compose.yml` works unchanged.

### 4.4 Connect to the server

1. EC2 → **Instances** → wait until **Instance state = Running** and
   **Status checks = 2/2 passed**.
2. Tick the instance → **Connect** → **SSH client** tab. It shows the exact command.
3. Copy the **Public IPv4 address**.
4. From your laptop:

```bash
ssh -i "C:\Users\<you>\.ssh\resumo-key.pem" ec2-user@<PUBLIC_IP>
# macOS/Linux: ssh -i ~/.ssh/resumo-key.pem ec2-user@<PUBLIC_IP>
```

Type `yes` when asked to trust the host. You are now on the server.

### 4.5 Install Docker and Git

Run these **on the server** (Amazon Linux 2023 uses `dnf`):

```bash
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable --now docker
# let your user run docker without sudo (log out/in for it to apply)
sudo usermod -aG docker ec2-user
newgrp docker

# Docker Compose v2 plugin
sudo mkdir -p /usr/libexec/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m) \
  -o /usr/libexec/docker/cli-plugins/docker-compose
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose

docker --version
docker compose version
```

### 4.6 Get the Resumo code onto the server

Pick whichever is easiest for you:

**Option 1 — Git (if you push the project to GitHub/GitLab):**

```bash
git clone https://github.com/<your-user>/<your-repo>.git resumo
cd resumo
```

**Option 2 — upload from your laptop (no Git hosting needed).** From your **laptop**,
in the project folder:

```bash
scp -i "C:\Users\<you>\.ssh\resumo-key.pem" -r ^
  backend frontend docker-compose.yml .env.example ^
  ec2-user@<PUBLIC_IP>:/home/ec2-user/resumo
```

(On macOS/Linux drop the `^` and use a single line with `\`.) Then on the server:
`cd resumo`.

> The `.git` folder and `node_modules` are not needed on the server; the Docker build
> installs dependencies for you.

### 4.7 Create the production `.env`

On the **server**, in the `resumo` folder:

```bash
cd /home/ec2-user/resumo
cp .env.example .env
```

Generate a strong secret and put it in the file:

```bash
python3 -c "import secrets;print(secrets.token_urlsafe(48))"
# copy the output
nano .env     # or: vi .env
```

Set these values (leave the rest as-is):

```
APP_ENV=production
DEBUG=false
SECRET_KEY=<paste-the-generated-secret>
POSTGRES_USER=resumo
POSTGRES_PASSWORD=<make-up-a-strong-db-password>
POSTGRES_DB=resumo
FRONTEND_ORIGIN=http://<PUBLIC_IP>          # or https://your.domain later
COOKIE_SECURE=false                          # true once you have HTTPS
STORAGE_BACKEND=local                        # Path A keeps files on the instance
LLM_PROVIDER=none                            # see section 4.12 to enable AI
RUN_MIGRATIONS=1
```

Save (`Ctrl-O`, Enter, `Ctrl-X` in nano) and lock the file down:

```bash
chmod 600 .env
```

> `COOKIE_SECURE=false` is correct while you are on plain HTTP. If you later add
> HTTPS (section 4.11), set it to `true` and `FRONTEND_ORIGIN` to your HTTPS URL.
> All browser requests go to one origin (the Web container proxies `/api`), so
> cookies and CSRF keep working.

### 4.8 Build and run

```bash
docker compose up -d --build
```

This builds the backend and frontend images, starts PostgreSQL, waits for it to be
healthy, runs Alembic migrations (because `RUN_MIGRATIONS=1`), then starts the API and
Web containers. First build takes a few minutes.

Watch it come up:

```bash
docker compose ps
docker compose logs -f backend
```

When `backend` logs show `Uvicorn running on http://0.0.0.0:8000`, press `Ctrl-C` to
stop following the logs (the containers keep running).

### 4.9 Verify the deployment

From your laptop (replace the IP):

```bash
curl http://<PUBLIC_IP>/api/v1/health      # expect {"status":"ok", ...}
curl http://<PUBLIC_IP>/api/v1/ready       # checks the database too
```

Then open **`http://<PUBLIC_IP>/`** in a browser. You should see the Resumo landing
page. Click **Sign up**, create an account, and walk the flow: upload a resume →
analyse → paste a job description → match → export. API docs live at
`http://<PUBLIC_IP>/api/docs`.

Optional: seed the demo account so the workspace looks populated:

```bash
docker compose exec backend python scripts/seed_demo.py
# login: demo@resumo.app / demo1234
```

### 4.10 Make the IP stable (Elastic IP)

By default the public IP changes if you stop/start the instance. An **Elastic IP** is
**free while it is attached to a running instance** (you are charged only for an EIP
that is *not* attached).

1. EC2 → **Elastic IPs** → **Allocate Elastic IP address** → Allocate.
2. Select it → **Actions → Associate** → choose `resumo-app` → Associate.
3. Use this new (permanent) IP from now on.

> **Teardown reminder:** release the Elastic IP when you delete the instance, or you
> will be billed for an unused EIP.

### 4.11 Optional — a domain name and free HTTPS

You do **not** need a domain to demo. If you want a nice HTTPS URL:

**Step 1 — get a hostname.** Either buy a cheap domain, or use a **free dynamic-DNS**
hostname such as [DuckDNS](https://www.duckdns.org) or [sslip.io](https://sslip.io)
(e.g. `https://<your-ip>.sslip.io` works with **no** DNS account at all). Point the
hostname at your Elastic IP.

**Step 2 — terminate TLS with Caddy (automatic Let's Encrypt).** Create a second
compose file `docker-compose.prod.yml` on the server:

```yaml
# docker-compose.prod.yml — adds an HTTPS reverse proxy in front of the app
services:
  caddy:
    image: caddy:2
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - frontend

volumes:
  caddy_data:
  caddy_config:
```

And a `Caddyfile` next to it (replace the hostname):

```
resumo.example.com {
    reverse_proxy frontend:80
}
```

Run both files together:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Caddy fetches and renews the certificate automatically. Then update `.env`
(`COOKIE_SECURE=true`, `FRONTEND_ORIGIN=https://your.host`) and re-run
`docker compose ... up -d`.

> Why Caddy and not an ALB? An Application Load Balancer costs ~$16+/month and is not
> in the free tier. Caddy is a container and costs nothing.

### 4.12 Optional — enable a real AI model

Out of the box `LLM_PROVIDER=none` means Resumo runs **fully deterministically**
(parsing, scoring, matching, exports all work; AI buttons show a clear "not
configured" message). To enable a local model **on the same small instance**:

```bash
# on the server — run Ollama as another container
docker run -d --name ollama --restart unless-stopped \
  -v ollama:/root/.ollama -p 11434:11434 ollama/ollama
docker exec -it ollama ollama pull qwen2.5:1.5b
```

Then in `.env` set:

```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:1.5b
```

and restart: `docker compose up -d`. On `t3.micro` the model is slow; long prompts may
hit the 120 s timeout and gracefully fall back to deterministic output (this is by
design, not an error). For faster AI, either use a larger instance or point
`OPENAI_BASE_URL`/`OPENAI_API_KEY` at any OpenAI-compatible endpoint.

> Everything above runs **inside** the instance, so **no new AWS service and no extra
> cost** is involved. 1.5B models need ~2 GB RAM; if the box feels tight, leave AI off
> for the demo.

### 4.13 Persist data and back up

Your data lives in Docker named volumes (`pgdata` for Postgres, `storage` for uploaded
files), which survive container restarts but **not** instance termination.

Quick logical backup (safe to copy to your laptop or S3):

```bash
docker compose exec db pg_dump -U resumo resumo | gzip > ~/resumo-$(date +%F).sql.gz
```

Restore:

```bash
gunzip -c ~/resumo-YYYY-MM-DD.sql.gz | docker compose exec -T db psql -U resumo -d resumo
```

Optionally copy backups to S3 with a **cron** job later (section 5.2 covers S3).

---

## 5. Path B — managed AWS services (optional, add later)

Use this to make the deployment "production-shaped". Each sub-section is independent;
add only what you need. All of these stay inside promotional credits if you keep usage
tiny and tear them down afterwards.

### 5.1 RDS for PostgreSQL

Benefits: automatic backups, patching, no DB container to babysit.

1. Console → **RDS** → **Create database** → **Standard create** → **PostgreSQL 16**.
2. **Templates**: *Free tier*. **DB instance class**: `db.t3.micro` (or `db.t4g.micro`).
3. **Storage**: 20 GiB gp3, **disable** storage autoscaling (avoids growth).
4. **Credentials**: set `resumo` and a strong password. **Public access: No**.
5. **VPC security group**: create new, e.g. `resumo-db-sg`. Allow inbound `5432`
   from the **EC2 instance's security group** (`resumo-web`) only — never `0.0.0.0/0`.
6. **Additional configuration → Initial database name**: `resumo`. Create.
7. When available, copy the **endpoint** (e.g.
   `resumo.abc123.ap-south-1.rds.amazonaws.com`).
8. Allow the EC2 box to reach it: EC2 → the instance's security group → add the
   RDS security group as the **source** of a `5432` inbound rule (done in step 5), and
   put the instance and RDS in the same VPC.
9. On the server, change `.env`:

   ```
   DATABASE_URL=postgresql+psycopg://resumo:<password>@<rds-endpoint>:5432/resumo
   ```

   Remove the local `db` service from the compose file (or just stop it:
   `docker compose stop db`), then:

   ```bash
   docker compose up -d --build      # RUN_MIGRATIONS=1 applies migrations to RDS
   ```

### 5.2 S3 for uploaded files and backups

Buckets are private; the API streams files through ownership-checked routes, so the
bucket never needs to be public.

1. Console → **S3** → **Create bucket**. Name `resumo-files-<accountid>` (globally
   unique), same region.
2. **Block all public access: ON**. **Default encryption: SSE-S3** (free).
3. Create an IAM policy (see 5.3) granting `s3:PutObject`, `s3:GetObject`,
   `s3:DeleteObject` on `arn:aws:s3:::resumo-files-<accountid>/*`.
4. On the server set:

   ```
   STORAGE_BACKEND=s3
   S3_BUCKET=resumo-files-<accountid>
   S3_REGION=ap-south-1
   ```

   and provide credentials via the instance role (5.3) — **not** hardcoded keys.
   Restart: `docker compose up -d`.

### 5.3 IAM role for the EC2 instance (least privilege)

Instead of storing access keys on the server, attach a role:

1. IAM → **Roles → Create role** → **AWS service** → **EC2**.
2. Attach an inline policy allowing only what the app needs:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       { "Effect": "Allow",
         "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
         "Resource": "arn:aws:s3:::resumo-files-<accountid>/*" },
       { "Effect": "Allow",
         "Action": ["ssm:GetParameter", "ssm:GetParametersByPath"],
         "Resource": "arn:aws:ssm:ap-south-1:<accountid>:parameter/resumo/*" },
       { "Effect": "Allow",
         "Action": ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage"],
         "Resource": "arn:aws:sqs:ap-south-1:<accountid>:resumo-jobs" },
       { "Effect": "Allow",
         "Action": ["bedrock:InvokeModel", "bedrock:Converse"],
         "Resource": "arn:aws:bedrock:*::foundation-model/*" }
     ]
   }
   ```

3. Name it `resumo-ec2-role` → create.
4. EC2 → instance → **Actions → Security → Modify IAM role** → attach it.

### 5.4 Secrets in SSM Parameter Store (Standard = free)

1. Console → **Systems Manager → Parameter Store → Create parameter**.
2. Type **SecureString** for `SECRET_KEY` and the DB password; **String** for
   non-secret config. Name them under a path, e.g. `/resumo/SECRET_KEY`.
3. On the server, export them before `docker compose up`, e.g. add a small
   `fetch-secrets.sh`:

   ```bash
   #!/bin/sh
   SECRET_KEY=$(aws ssm get-parameter --name /resumo/SECRET_KEY \
     --with-decryption --query Parameter.Value --output text)
   export SECRET_KEY
   docker compose up -d
   ```

   The instance role from 5.3 grants read access, so no keys live on disk.

### 5.5 CloudFront for the web app

CloudFront gives HTTPS on a `*.cloudfront.net` name (via its default certificate)
**without owning a domain**, and caches static assets at the edge.

1. Console → **CloudFront → Create distribution**.
2. **Origin**: your EC2 public DNS, protocol **HTTP only**, port `80`.
3. **Default behavior**: allow all methods, **forward all cookies** and headers,
   **cache policy CachingDisabled** (the SPA and `/api` are dynamic). For purely
   static builds you can instead set the S3 bucket as origin and cache normally.
4. **Alternate domain + custom cert**: only if you own a domain (use ACM in
   `us-east-1`).
5. Set `FRONTEND_ORIGIN=https://<distribution>.cloudfront.net` in `.env` and, once on
   HTTPS, `COOKIE_SECURE=true`.
6. Because all traffic hits one CloudFront origin, cookies/CSRF keep working.

> Simplest version: keep Nginx serving the SPA and let CloudFront proxy everything.
> A more advanced setup is "API origin = EC2" + "static origin = S3" with ordered
> cache behaviors, exactly as described in `docs/ARCHITECTURE.md`.

### 5.6 CloudWatch logs, metrics and alarms

- The containers already log to stdout; `docker compose logs` shows them. For durable
  logs, install the **CloudWatch agent** on the instance and ship
  `/var/lib/docker/containers`.
- Create an alarm: EC2 → **Status checks failed** for more than 5 minutes → notify
  your email via an SNS topic (both sit inside always-free allowances at this scale).
- Optionally add a **budget alarm** (section 3) for cost, which is the more important
  one.

### 5.7 Amazon Bedrock for Serverless Generative AI (Path B)

Resumo supports Amazon Bedrock (Anthropic Claude 3.5 Sonnet / Amazon Titan Text Express)
for AI resume tailoring, project brief generation, and quality analysis without running
a heavy local GPU or storing API keys on disk.

1. Console -> **Amazon Bedrock** -> **Model access** -> Request access to:
   - Anthropic Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20240620-v1:0`), or
   - Amazon Titan Text Express (`amazon.titan-text-express-v1`).
2. The EC2 instance accesses Bedrock through its attached IAM instance profile
   (`resumo-ec2-role` created in 5.3), so **no API keys are ever stored on disk**.
3. On the server, update `.env`:
   ```
   LLM_PROVIDER=bedrock
   BEDROCK_REGION=ap-south-1
   BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
   ```
4. Restart the backend container: `docker compose up -d backend`.
5. The application automatically interacts with Bedrock via `boto3` Converse API and
   runs all AI suggestions through Resumo's deterministic truth-preservation verifier.

---

## 6. Operations runbook

Run these from the `resumo` folder on the server.

| Task | Command |
| --- | --- |
| See status | `docker compose ps` |
| Follow API logs | `docker compose logs -f backend` |
| Follow web logs | `docker compose logs -f frontend` |
| Restart everything | `docker compose restart` |
| Deploy new code | `git pull && docker compose up -d --build` |
| Stop (keep data) | `docker compose stop` |
| Start again | `docker compose start` |
| Remove containers (keep volumes) | `docker compose down` |
| Remove everything incl. data | `docker compose down -v` |
| Open a DB shell | `docker compose exec db psql -U resumo -d resumo` |
| Run migrations manually | `docker compose exec backend alembic upgrade head` |
| Seed the demo account | `docker compose exec backend python scripts/seed_demo.py` |

Suggested first hardening step after any deploy:

```bash
docker compose exec backend python -m pytest -q   # if test deps are present
```

---

## 7. Cost control and teardown checklist

### While it is running

- [ ] Check **Billing → Home** (credits) and **Budgets** weekly.
- [ ] `aws ec2 describe-instances --query "Reservations[].Instances[].{id:InstanceId,state:State.Name,type:InstanceType}" --output table`
- [ ] Stop the instance when you are not demoing:
      `aws ec2 stop-instances --instance-ids <id>` (data on EBS persists; you are
      billed only for storage while stopped).
- [ ] Never create a NAT Gateway or a load balancer.

### Full teardown (do this when the project is graded)

```bash
# 1. Stop and remove app data on the instance
docker compose down -v

# 2. From your laptop (or console):
aws ec2 terminate-instances --instance-ids <instance-id>          # delete the server
aws ec2 release-address --public-ip <elastic-ip>                   # release the EIP
aws rds delete-db-instance --db-instance-identifier resumo \
  --skip-final-snapshot --delete-automated-backups                 # delete RDS (Path B)
aws s3 rm s3://resumo-files-<accountid> --recursive                # empty S3 (Path B)
aws s3api delete-bucket --bucket resumo-files-<accountid>          # delete bucket
```

Then in the console confirm: **EC2 → Volumes** (delete orphaned volumes),
**RDS → Snapshots** (delete manual ones), **CloudFront → Distributions** (disable then
delete), **SSM Parameter Store** (delete `/resumo/*`).

> Deleting the instance stops compute charges immediately. Unattached Elastic IPs,
> idle RDS and leftover snapshots are the usual causes of a "why am I being charged"
> surprise — clean all four.

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Browser shows the page but `/api` calls fail | Web container cannot reach backend | `docker compose logs frontend backend`; confirm both are `Up` |
| `502 Bad Gateway` from the site | backend not ready yet or crashed | `docker compose logs backend`; check `DATABASE_URL` |
| `curl http://<ip>/api/v1/health` times out | security group missing port 80 | add HTTP inbound rule (4.2) |
| Login seems to "not stick" | cookies dropped | all traffic must go to one origin; set `COOKIE_SECURE` to match http/https |
| Migration error on boot | wrong DB creds or DB not ready | confirm `.env` `POSTGRES_*`; `docker compose logs db` |
| `permission denied` on the `.pem` | key file too open | re-run the `icacls`/`chmod` from 4.1 |
| Out of disk | image layers + storage | `docker system prune -af`; check `df -h` |
| AI buttons say "not configured" | `LLM_PROVIDER=none` | see 4.12 |
| Instance IP changed after restart | no Elastic IP | associate an Elastic IP (4.10) |

Useful diagnostics:

```bash
docker compose ps
docker compose logs --tail=200 backend
df -h && free -m
curl -s localhost/api/v1/health
curl -s localhost/api/v1/ready
```

---

## 9. CLI quick reference

```bash
# identity / region
aws sts get-caller-identity
aws configure

# EC2
aws ec2 describe-instances --query "Reservations[].Instances[].{id:InstanceId,ip:PublicIpAddress,state:State.Name}" --output table
aws ec2 stop-instances  --instance-ids <id>
aws ec2 start-instances --instance-ids <id>
aws ec2 terminate-instances --instance-ids <id>

# security groups
aws ec2 describe-security-groups --group-names resumo-web

# AMIs that are free-tier eligible (new accounts)
aws ec2 describe-instance-types --filters Name=free-tier-eligible,Values=true \
  --query "InstanceTypes[*].InstanceType" --output text | tr '\t' '\n' | sort

# S3
aws s3 ls
aws s3 sync frontend/dist s3://resumo-web-<accountid> --delete

# RDS
aws rds describe-db-instances --query "DBInstances[*].{id:DBInstanceIdentifier,endpoint:Endpoint.Address}" --output table
```

---

## Appendix A — environment variables

| Variable | Purpose | Path A value |
| --- | --- | --- |
| `APP_ENV` | `development` / `production` | `production` |
| `DEBUG` | verbose errors | `false` |
| `SECRET_KEY` | signs session JWTs | random 48+ char string |
| `DATABASE_URL` | SQLAlchemy URL (`postgresql+psycopg://…`) | set by compose to the `db` service |
| `FRONTEND_ORIGIN` | CORS allow-list | your public URL |
| `COOKIE_SECURE` | send cookies only over HTTPS | `false` on HTTP |
| `RUN_MIGRATIONS` | run Alembic on boot | `1` |
| `STORAGE_BACKEND` | `local` or `s3` | `local` |
| `LOCAL_STORAGE_DIR` | where local files go | `/app/storage` (a volume) |
| `S3_BUCKET` / `S3_REGION` | S3 target when `STORAGE_BACKEND=s3` | set in Path B |
| `LLM_PROVIDER` | `none` / `ollama` / `openai` / `bedrock` | `none` |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | local model | `http://host.docker.internal:11434` / `qwen2.5:1.5b` |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | hosted model | empty |
| `LLM_TIMEOUT_SECONDS` | AI request timeout | `120` |
| `MAX_UPLOAD_MB` / `MAX_PDF_PAGES` | upload safety caps | `10` / `10` |
| `JOB_RUNNER` | `inline` / `thread` / `sqs` | `thread` |
| `SQS_QUEUE_URL` | queue when `JOB_RUNNER=sqs` | set in Path B |

Full list with defaults: `backend/.env.example` and `backend/app/core/config.py`.

## Appendix B — architecture

```
                    ┌─────────────────────────── EC2 instance (t3.micro) ───────────────────────────┐
  Browser  ──HTTP(S)──▶  Caddy:80/443 (optional TLS)  ──▶  resumo-frontend (Nginx)  ──/api──▶  resumo-backend (FastAPI)
                    │                                              │                              │
                    │                                              └── static SPA                 ├──▶ resumo-db (Postgres)
                    │                                                                             ├──▶ local volume  (Path A)
                    │                                                                             └──▶ S3 + IAM role (Path B)
                    └────────────────────────────────────────────────────────────────────────────┘
```

Everything the app needs is inside the compose project except optional Path B
services (RDS, S3, CloudFront, SSM, CloudWatch), each of which is introduced
separately above so you can adopt them one at a time without redeploying from scratch.
