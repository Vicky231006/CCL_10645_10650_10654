"""Generate high-resolution draw.io styled diagrams for Resumo.

Generates:
  - docs/figures/figure_3_1_aws_architecture.png (2400x1520 high-res PNG)
  - docs/figures/figure_3_2_ingestion_pipeline.png (2200x620 high-res PNG)
  - docs/figures/figure_3_3_bedrock_pipeline.png (2000x820 high-res PNG)
  - docs/figures/resumo_aws_architecture.drawio (Native Draw.io XML)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FIGURES_DIR = ROOT / "docs" / "figures"
OUT_PNG_3_1 = FIGURES_DIR / "figure_3_1_aws_architecture.png"
OUT_PNG_3_2 = FIGURES_DIR / "figure_3_2_ingestion_pipeline.png"
OUT_PNG_3_3 = FIGURES_DIR / "figure_3_3_bedrock_pipeline.png"
OUT_DRAWIO = FIGURES_DIR / "resumo_aws_architecture.drawio"

W = 2400
H = 1520

# Colors (Draw.io / Modern Cloud Architecture Palette)
BG_COLOR = (248, 250, 252)          # Slate-50
WHITE = (255, 255, 255)

# Tiers / Boundaries
VPC_BG = (241, 245, 249)            # Slate-100
VPC_BORDER = (37, 99, 235)          # Blue-600
VPC_HEADER = (30, 64, 175)          # Blue-800

PUB_SUBNET_BG = (255, 251, 235)     # Amber-50
PUB_SUBNET_BORDER = (217, 119, 6)   # Amber-600

PRIV_SUBNET_BG = (240, 253, 244)    # Emerald-50
PRIV_SUBNET_BORDER = (16, 185, 129) # Emerald-500

# Service Colors
EC2_ORANGE = (234, 88, 12)          # Orange-600
NGINX_GREEN = (22, 163, 74)         # Green-600
FASTAPI_BLUE = (37, 99, 235)        # Blue-600
RDS_BLUE = (2, 132, 199)            # Sky-600
S3_GREEN = (22, 163, 74)            # Green-600
BEDROCK_PURPLE = (124, 58, 237)     # Violet-600
SSM_TEAL = (13, 148, 136)           # Teal-600
SQS_PINK = (219, 39, 119)           # Pink-600
CLOUDFRONT_PURPLE = (126, 34, 206)  # Purple-700
GOV_ORANGE = (194, 65, 12)          # Orange-700

# Text Colors
TEXT_DARK = (15, 23, 42)            # Slate-900
TEXT_MUTED = (71, 85, 105)          # Slate-600
TEXT_LIGHT = (100, 116, 139)        # Slate-500
BORDER_LIGHT = (203, 213, 225)      # Slate-300


def get_font(name: str, size: int):
    font_paths = [
        f"C:/Windows/Fonts/{name}.ttf",
        f"C:/Windows/Fonts/{name.lower()}.ttf",
        f"C:/Windows/Fonts/segoeui.ttf",
        f"C:/Windows/Fonts/arial.ttf",
    ]
    for p in font_paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_rounded_rect(draw, bbox, radius, fill, outline, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=int(width))


def draw_card(draw, bbox, header_text, header_color, body_fill, border_color, radius=10, width=2, header_h=34, f_head=None):
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(bbox, radius=radius, fill=body_fill, outline=border_color, width=int(width))
    draw.rounded_rectangle((x0, y0, x1, y0 + header_h), radius=radius, fill=header_color, outline=None)
    draw.rectangle((x0, y0 + header_h - radius, x1, y0 + header_h), fill=header_color)
    draw.line([(x0, y0 + header_h), (x1, y0 + header_h)], fill=border_color, width=int(width))
    if f_head:
        draw.text((x0 + 16, y0 + (header_h - 20) // 2), header_text, font=f_head, fill=WHITE)


def draw_arrow(draw, start, end, label="", color=(71, 85, 105), width=2, f_label=None, label_side="top"):
    x0, y0 = start
    x1, y1 = end
    draw.line([start, end], fill=color, width=int(width))
    
    size = 9
    import math
    angle = math.atan2(y1 - y0, x1 - x0)
    p1 = (x1 - size * math.cos(angle - math.pi / 6), y1 - size * math.sin(angle - math.pi / 6))
    p2 = (x1 - size * math.cos(angle + math.pi / 6), y1 - size * math.sin(angle + math.pi / 6))
    draw.polygon([end, p1, p2], fill=color)

    if label and f_label:
        mx = (x0 + x1) / 2
        my = (y0 + y1) / 2
        bbox = draw.textbbox((0, 0), label, font=f_label)
        lw = bbox[2] - bbox[0] + 12
        lh = bbox[3] - bbox[1] + 6
        lx = mx - lw / 2
        ly = my - lh / 2 - (14 if label_side == "top" else -14)
        draw.rounded_rectangle((lx, ly, lx + lw, ly + lh), radius=4, fill=(255, 255, 255, 230), outline=color, width=1)
        draw.text((lx + 6, ly + 2), label, font=f_label, fill=color)


def generate_png_3_1():
    img = Image.new("RGBA", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    f_title = get_font("segoeuib", 32)
    f_subtitle = get_font("segoeui", 17)
    f_h2 = get_font("segoeuib", 16)
    f_h3 = get_font("segoeuib", 14)
    f_body = get_font("segoeui", 14)
    f_body_b = get_font("segoeuib", 14)
    f_sub = get_font("segoeui", 12)
    f_label = get_font("segoeuib", 12)

    # 1. Title Banner
    draw_rounded_rect(draw, (50, 30, W - 50, 115), 10, fill=WHITE, outline=BORDER_LIGHT, width=1)
    draw.rounded_rectangle((50, 30, 62, 115), radius=4, fill=FASTAPI_BLUE)
    draw.text((80, 42), "Resumo — Cloud-Native Multi-Tier AWS Architecture (Path B Deployment)", font=f_title, fill=TEXT_DARK)
    draw.text((82, 82), "Decoupled N-Services on Amazon Web Services (ap-south-1 Mumbai): VPC Tier Isolation, Amazon Bedrock GenAI & Zero-Secret Governance", font=f_subtitle, fill=TEXT_MUTED)

    # 2. Ingress & Client Tier
    draw_card(draw, (80, 140, 520, 245), "Client Web Browser (Desktop / Mobile)", (71, 85, 105), WHITE, (148, 163, 184), radius=8, header_h=32, f_head=f_h3)
    draw.text((100, 182), "• React 18 TypeScript Single-Page Application (SPA)", font=f_body, fill=TEXT_DARK)
    draw.text((100, 204), "• Cookie Session (httpOnly) + CSRF Double-Submit Token", font=f_body, fill=TEXT_DARK)
    draw.text((100, 224), "• Accessible UI (360px+ responsive, WCAG 2.2 AA standards)", font=f_sub, fill=TEXT_MUTED)

    draw_arrow(draw, (300, 245), (300, 300), label="HTTPS (Port 443 / TLS 1.3)", color=CLOUDFRONT_PURPLE, width=2, f_label=f_label)

    draw_card(draw, (80, 300, 520, 430), "Amazon CloudFront CDN (Global Edge Network)", CLOUDFRONT_PURPLE, (250, 245, 255), CLOUDFRONT_PURPLE, radius=8, header_h=32, f_head=f_h3)
    draw.text((100, 340), "• Edge Caching for Static SPA Assets (JS, CSS, Media)", font=f_body, fill=TEXT_DARK)
    draw.text((100, 362), "• Free Wildcard SSL/TLS Termination (*.cloudfront.net)", font=f_body, fill=TEXT_DARK)
    draw.text((100, 384), "• Low-Latency Global Edge Ingress & DDoS Protection", font=f_body, fill=TEXT_DARK)
    draw.text((100, 404), "• Dynamic /api/* Path Routed Directly to EC2 Origin", font=f_sub, fill=CLOUDFRONT_PURPLE)

    draw_arrow(draw, (300, 430), (300, 500), label="HTTP (Port 80 Ingress Proxy)", color=EC2_ORANGE, width=2, f_label=f_label)

    # 3. Amazon VPC Container
    vpc_box = (60, 490, 1600, 1260)
    draw_rounded_rect(draw, vpc_box, radius=14, fill=VPC_BG, outline=VPC_BORDER, width=2)
    draw.rounded_rectangle((60, 490, 850, 532), radius=12, fill=VPC_HEADER)
    draw.text((80, 500), "Amazon Virtual Private Cloud (VPC) — Region: ap-south-1 (Mumbai) | CIDR: 10.0.0.0/16", font=f_h2, fill=WHITE)

    # 3A. Public Subnet
    pub_box = (85, 550, 810, 1230)
    draw_rounded_rect(draw, pub_box, radius=12, fill=PUB_SUBNET_BG, outline=PUB_SUBNET_BORDER, width=2)
    draw.rounded_rectangle((85, 550, 590, 586), radius=10, fill=PUB_SUBNET_BORDER)
    draw.text((100, 558), "Public Subnet (CIDR: 10.0.1.0/24) — Internet Gateway (IGW)", font=f_h3, fill=WHITE)

    ec2_box = (110, 600, 785, 1205)
    draw_card(draw, ec2_box, "Amazon EC2 Compute Instance (t3.micro / t4g.micro) — resumo-web", EC2_ORANGE, WHITE, EC2_ORANGE, radius=10, header_h=36, f_head=f_h2)
    draw.rounded_rectangle((125, 645, 770, 675), radius=6, fill=(255, 237, 213), outline=EC2_ORANGE, width=1)
    draw.text((135, 652), "Elastic IP Attached  |  IAM Role: resumo-ec2-role  |  Security Group: resumo-web-sg (:80, :443, :22)", font=f_sub, fill=EC2_ORANGE)

    # Nginx Container
    nginx_box = (130, 690, 765, 825)
    draw_card(draw, nginx_box, "Docker Container 1: resumo-frontend (Nginx :80)", NGINX_GREEN, (240, 253, 244), NGINX_GREEN, radius=8, header_h=30, f_head=f_h3)
    draw.text((148, 728), "• Serves Compiled Production React 18 SPA at root /", font=f_body, fill=TEXT_DARK)
    draw.text((148, 750), "• Reverse-proxies /api/ requests to FastAPI backend on port 8000", font=f_body, fill=TEXT_DARK)
    draw.text((148, 772), "• Single-Origin configuration: httpOnly session & CSRF cookies preserved", font=f_body, fill=TEXT_DARK)
    draw.text((148, 796), "• Health endpoint proxy (/api/v1/health -> 200 OK)", font=f_sub, fill=NGINX_GREEN)

    draw_arrow(draw, (450, 825), (450, 875), label="Internal Docker Network Proxy (Port 8000)", color=FASTAPI_BLUE, width=2, f_label=f_label)

    # FastAPI Container
    fastapi_box = (130, 875, 765, 1180)
    draw_card(draw, fastapi_box, "Docker Container 2: resumo-backend (FastAPI / Python 3.13 :8000)", FASTAPI_BLUE, (239, 246, 255), FASTAPI_BLUE, radius=8, header_h=32, f_head=f_h2)
    draw.text((148, 915), "• Universal Parsing Registry (PDF, DOCX, TXT, MD, RTF, ODT, HTML, Images)", font=f_body, fill=TEXT_DARK)
    draw.text((148, 938), "• Deterministic Quality Scoring Engine (6 Weighted Categories, 0–10 Scale)", font=f_body, fill=TEXT_DARK)
    draw.text((148, 961), "• Evidence-Based Job Description Matcher (Semantic Cosine + Exact Overlap)", font=f_body, fill=TEXT_DARK)
    draw.text((148, 984), "• Truth-Preserving AI Orchestrator (Subset Fact Verification Guardrails)", font=f_body, fill=TEXT_DARK)
    draw.text((148, 1007), "• Career Gap & Roadmap Coach (Milestones & Actionable Project Briefs)", font=f_body, fill=TEXT_DARK)
    draw.text((148, 1030), "• Document Export Engine: PDF (ReportLab), DOCX, LaTeX, TXT with Hyperlinks", font=f_body, fill=TEXT_DARK)
    draw.text((148, 1053), "• Database Migration Manager (Alembic Head Auto-Executed on Boot)", font=f_body, fill=TEXT_DARK)
    draw.text((148, 1076), "• Boto3 AWS SDK Clients: S3 Storage, Bedrock Runtime, SQS Queue, SSM Store", font=f_body, fill=FASTAPI_BLUE)
    draw.text((148, 1102), "• Security: PBKDF2-HMAC-SHA256, SSRF IP-Guard, Rate Limiter, Magic-Bytes", font=f_sub, fill=TEXT_MUTED)
    draw.text((148, 1124), "• Graceful Fallback: Deterministic core operates 100% offline if AI disabled", font=f_sub, fill=FASTAPI_BLUE)

    # 3B. Private Subnet
    priv_box = (840, 550, 1570, 1230)
    draw_rounded_rect(draw, priv_box, radius=12, fill=PRIV_SUBNET_BG, outline=PRIV_SUBNET_BORDER, width=2)
    draw.rounded_rectangle((840, 550, 1430, 586), radius=10, fill=PRIV_SUBNET_BORDER)
    draw.text((855, 558), "Private Subnet (CIDR: 10.0.2.0/24) — Completely Isolated (Zero Internet Routes)", font=f_h3, fill=WHITE)

    rds_box = (865, 610, 1545, 1190)
    draw_card(draw, rds_box, "Amazon RDS for PostgreSQL 16 (db.t3.micro) — resumo-db", RDS_BLUE, WHITE, RDS_BLUE, radius=10, header_h=36, f_head=f_h2)
    
    draw.rounded_rectangle((885, 655, 1525, 715), radius=6, fill=(238, 242, 255), outline=RDS_BLUE, width=1)
    draw.text((900, 665), "FIREWALL RULE: Security Group 'resumo-db-sg' Inbound Port 5432 RESTRICTED", font=f_body_b, fill=(30, 64, 175))
    draw.text((900, 688), "ALLOWED SOURCE: Strictly 'resumo-web-sg' (EC2 Private IP)  |  PUBLIC ACCESS: NO (0.0.0.0/0 BLOCKED)", font=f_sub, fill=RDS_BLUE)

    draw.text((885, 735), "Key Managed Relational Features & Architecture:", font=f_h3, fill=TEXT_DARK)
    draw.text((905, 765), "• Fully Managed Engine: Automated Minor Version Upgrades & Maintenance", font=f_body, fill=TEXT_DARK)
    draw.text((905, 790), "• 20 GiB gp3 SSD Storage (Autoscaling Disabled to Avoid Uncontrolled Costs)", font=f_body, fill=TEXT_DARK)
    draw.text((905, 815), "• Automated Daily Database Snapshots & Point-in-Time Recovery (PITR)", font=f_body, fill=TEXT_DARK)
    draw.text((905, 840), "• High-Performance psycopg3 Binary Connection Pooling via SQLAlchemy 2.0", font=f_body, fill=TEXT_DARK)
    draw.text((905, 865), "• Relational Data Integrity with Enforced Tenant Ownership on All Tables", font=f_body, fill=TEXT_DARK)

    draw.rounded_rectangle((885, 905, 1525, 1165), radius=8, fill=(248, 250, 252), outline=BORDER_LIGHT, width=1)
    draw.text((900, 918), "Persisted Core Relational Tables & Entities:", font=f_h3, fill=TEXT_DARK)
    entities = [
        "1. Users & Credentials (Salted PBKDF2-SHA256)",
        "2. Candidate Profiles & Onboarding State",
        "3. Resumes, Sections & Version Snapshots",
        "4. Quality Analyses (6-Category Scores & Excerpts)",
        "5. Job Descriptions & Extracted Requirements",
        "6. Match Reports & Keyword Evidence Matrix",
        "7. Career Roadmaps & Milestone Schedules",
        "8. Project Plans, Evidence Proofs & Assets",
        "9. Published Portfolio Pages & Slugs",
        "10. Job Applications Pipeline (5 Stages)",
        "11. Tailor Suggestions & Verification Audit",
        "12. Uploaded File Metadata & S3 Object Keys"
    ]
    for idx, ent in enumerate(entities):
        col = idx // 6
        row = idx % 6
        ex = 905 + col * 310
        ey = 948 + row * 34
        draw.text((ex, ey), f"• {ent}", font=f_sub, fill=TEXT_DARK)

    draw_arrow(draw, (765, 960), (865, 960), label="SQLAlchemy (Port 5432)", color=RDS_BLUE, width=3, f_label=f_label, label_side="top")

    # 4. Right Side: External Managed AWS Cloud Services
    rx0, rx1 = 1640, 2340

    # S3
    s3_box = (rx0, 140, rx1, 395)
    draw_card(draw, s3_box, "Amazon S3 Bucket (resumo-files-<accountid>)", S3_GREEN, (240, 253, 244), S3_GREEN, radius=10, header_h=34, f_head=f_h2)
    draw.text((rx0 + 20, 185), "• Persistent Binary Object Storage for Candidate Data", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 210), "• Uploaded Raw Documents (PDF, DOCX, TXT, Images)", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 235), "• Rendered Export Artifacts (PDF, DOCX, LaTeX, TXT)", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 260), "• Automated PostgreSQL Daily Gzipped Database Dumps", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 285), "• Security: Server-Side Encryption (SSE-S3 Enabled)", font=f_body_b, fill=S3_GREEN)
    draw.text((rx0 + 20, 310), "• Block All Public Access: ON (Private Bucket Security)", font=f_body_b, fill=S3_GREEN)
    draw.text((rx0 + 20, 335), "• Access Mode: Streamed via Authenticated API Routes", font=f_sub, fill=TEXT_MUTED)
    draw.text((rx0 + 20, 355), "• Key Scheme: Cryptographic Server-Side UUID Key Derivation", font=f_sub, fill=TEXT_MUTED)

    # Bedrock
    bedrock_box = (rx0, 420, rx1, 680)
    draw_card(draw, bedrock_box, "Amazon Bedrock (Serverless Foundation Models)", BEDROCK_PURPLE, (250, 245, 255), BEDROCK_PURPLE, radius=10, header_h=34, f_head=f_h2)
    draw.text((rx0 + 20, 465), "• Foundation Models: Claude 3.5 Sonnet / Amazon Titan Express", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 490), "• Native Boto3 Bedrock Runtime Converse API Interface", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 515), "• Authenticated via EC2 IAM Instance Profile (Zero API Keys)", font=f_body_b, fill=BEDROCK_PURPLE)
    draw.text((rx0 + 20, 540), "• Truth-Preservation Guardrail: Mathematical Subset Fact Check", font=f_body_b, fill=BEDROCK_PURPLE)
    draw.text((rx0 + 20, 565), "• Eliminates Hallucinated Metrics, Dates, and Experience", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 590), "• Contextual Résumé Tailoring & High-Impact Bullet Rewriting", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 615), "• Technical Project Brief Synthesis & Interview Prep Roadmaps", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 640), "• Cost Model: 100% Serverless Pay-per-Token (Zero Idle Cost)", font=f_sub, fill=BEDROCK_PURPLE)

    # SSM
    ssm_box = (rx0, 705, rx1, 955)
    draw_card(draw, ssm_box, "AWS Systems Manager (SSM Parameter Store)", SSM_TEAL, (240, 253, 250), SSM_TEAL, radius=10, header_h=34, f_head=f_h2)
    draw.text((rx0 + 20, 750), "• Zero-Secret Governance for Production Credentials", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 775), "• Standard Tier: 100% Free Lifetime Allowance on AWS", font=f_body_b, fill=SSM_TEAL)
    draw.text((rx0 + 20, 800), "• Type: SecureString Encrypted with AWS KMS Keys", font=f_body_b, fill=SSM_TEAL)
    draw.text((rx0 + 20, 825), "• Stores /resumo/SECRET_KEY (Session JWT Signing Key)", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 850), "• Stores /resumo/DATABASE_URL & RDS Database Password", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 875), "• Injected Directly into Process Memory via fetch-secrets.sh", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 900), "• Eliminates Hardcoded Plaintext Secrets from Disk & Git", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 925), "• Access Governed Strictly by EC2 IAM Instance Profile", font=f_sub, fill=SSM_TEAL)

    # SQS
    sqs_box = (rx0, 980, rx1, 1230)
    draw_card(draw, sqs_box, "Amazon SQS (resumo-jobs Message Queue)", SQS_PINK, (253, 242, 248), SQS_PINK, radius=10, header_h=34, f_head=f_h2)
    draw.text((rx0 + 20, 1025), "• Decoupled Asynchronous Processing for Compute Heavy Jobs", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 1050), "• Multi-Page PDF Text Extraction, Link Mapping & OCR", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 1075), "• Batch Job Description Semantic Matching & Tailoring", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 1100), "• Worker Long-Polling (WaitTimeSeconds: 20s) Eliminates CPU Spin", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 1125), "• Configured with Dead-Letter Queue (DLQ) for Failed Runs", font=f_body_b, fill=SQS_PINK)
    draw.text((rx0 + 20, 1150), "• Visibility Timeout: 60s with Exponential Backoff Strategy", font=f_body, fill=TEXT_DARK)
    draw.text((rx0 + 20, 1175), "• HTTP API returns 202 Accepted + Polling Job Status URL", font=f_sub, fill=SQS_PINK)

    draw_arrow(draw, (765, 915), (rx0, 270), label="Boto3 Client (S3 Put/Get)", color=S3_GREEN, width=2, f_label=f_label, label_side="top")
    draw_arrow(draw, (765, 980), (rx0, 550), label="Boto3 Converse API", color=BEDROCK_PURPLE, width=2, f_label=f_label, label_side="top")
    draw_arrow(draw, (765, 1045), (rx0, 830), label="IAM Session (ssm:GetParameter)", color=SSM_TEAL, width=2, f_label=f_label, label_side="top")
    draw_arrow(draw, (765, 1110), (rx0, 1105), label="Boto3 SQS (Send/Receive)", color=SQS_PINK, width=2, f_label=f_label, label_side="bottom")

    # 5. Bottom Banner
    gov_box = (60, 1285, W - 60, 1485)
    draw_card(draw, gov_box, "Security, Observability & Cost Governance (Cross-Cutting Cloud Foundations)", GOV_ORANGE, (255, 247, 237), GOV_ORANGE, radius=12, header_h=34, f_head=f_h2)

    col_w = (W - 120 - 60) // 4
    pillars = [
        ("AWS IAM Least-Privilege Profile", EC2_ORANGE, [
            "• EC2 Instance Profile: resumo-ec2-role",
            "• Zero Static Access Keys on Server Disk",
            "• s3:PutObject, s3:GetObject, s3:DeleteObject",
            "• ssm:GetParameter on /resumo/* only",
            "• bedrock:InvokeModel on Foundation Models",
            "• sqs:SendMessage, Receive, Delete on Queue"
        ]),
        ("Amazon CloudWatch Logs & Metrics", (2, 132, 199), [
            "• Docker stdout/stderr Shipped to CloudWatch",
            "• Metric Alarms: EC2 System & Instance Checks",
            "• RDS Memory, CPU Utilization, and Connections",
            "• Centralized Searchable Audit Logs",
            "• Log Retention: 7 Days to Minimize Storage",
            "• Zero PII Logged (GDPR/Privacy Compliant)"
        ]),
        ("Amazon SNS Real-Time Alerting", (194, 65, 12), [
            "• SNS Alert Topic: resumo-alerts",
            "• Subscribed to CloudWatch Metric Alarms",
            "• Instant Email Alert on Health Check Failure",
            "• Automated Outage Notification (< 5 min)",
            "• Monitors Unexpected DB Disconnects",
            "• Zero Cost inside Free Tier Allotment"
        ]),
        ("AWS Budgets & Credit Control ($1.00)", (22, 163, 74), [
            "• AWS Promotional Credit Tracking ($100–$200)",
            "• Hard Budget Alert Threshold at $1.00",
            "• Avoids NAT Gateways (~$32/mo) via Public Subnet",
            "• Disables RDS Storage Autoscaling",
            "• Teardown Checklist Eliminates Unused Disks",
            "• Guaranteed $0 Surprise Bills for Students"
        ])
    ]

    for c_idx, (col_title, col_color, col_bullets) in enumerate(pillars):
        cx0 = 80 + c_idx * (col_w + 20)
        cx1 = cx0 + col_w
        cy0 = 1330
        cy1 = 1465
        draw.rounded_rectangle((cx0, cy0, cx1, cy1), radius=8, fill=WHITE, outline=col_color, width=1)
        draw.rounded_rectangle((cx0, cy0, cx1, cy0 + 26), radius=8, fill=col_color)
        draw.text((cx0 + 10, cy0 + 5), col_title, font=f_h3, fill=WHITE)
        for b_idx, bullet in enumerate(col_bullets):
            draw.text((cx0 + 10, cy0 + 32 + b_idx * 17), bullet, font=f_sub, fill=TEXT_DARK)

    OUT_PNG_3_1.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(OUT_PNG_3_1), "PNG", dpi=(300, 300))
    print(f"Generated Figure 3.1 PNG: {OUT_PNG_3_1} ({OUT_PNG_3_1.stat().st_size} bytes)")


def generate_png_3_2():
    # Figure 3.2: Résumé Upload, Parsing, and Cloud Storage Pipeline (2200 x 580)
    w, h = 2200, 580
    img = Image.new("RGBA", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    f_title = get_font("segoeuib", 22)
    f_h3 = get_font("segoeuib", 14)
    f_body = get_font("segoeui", 13)
    f_sub = get_font("segoeui", 11)

    # Title
    draw_rounded_rect(draw, (40, 20, w - 40, 75), 8, fill=WHITE, outline=BORDER_LIGHT, width=1)
    draw.rounded_rectangle((40, 20, 50, 75), radius=4, fill=FASTAPI_BLUE)
    draw.text((65, 33), "Resumo — End-to-End Résumé Upload, Parsing, Quality Evaluation & Cloud Storage Pipeline", font=f_title, fill=TEXT_DARK)

    # 8 Pipeline Stages arranged in 2 rows of 4 cards
    stages = [
        # Row 1
        ("1. Multi-Format Upload", FASTAPI_BLUE, [
            "• Client uploads PDF, DOCX, TXT or Image",
            "• Validated by magic-byte signature check",
            "• Size cap: 10 MB | Page cap: 10 pages"
        ]),
        ("2. S3 Cloud Storage", S3_GREEN, [
            "• Binary streamed to Amazon S3 (Private)",
            "• Key: resumes/{user_id}/{uuid}.pdf",
            "• Server-Side Encryption: SSE-S3 enabled"
        ]),
        ("3. Parser Registry Extraction", (109, 40, 217), [
            "• Format registry dispatches pypdf / docx",
            "• Link annotations extracted from PDF URI",
            "• Character glyph repair pass applied"
        ]),
        ("4. Structuring Engine", (2, 132, 199), [
            "• _split_entries boundary detection",
            "• _build_bullets merges wrapped lines",
            "• Structured model with confidence score"
        ]),
        # Row 2
        ("5. Deterministic Quality Engine", (217, 119, 6), [
            "• 6 categories evaluated deterministically",
            "• Scored 0–10 with exact excerpt citations",
            "• Actionable fix recommendations surfaced"
        ]),
        ("6. Job Description Matcher", (13, 148, 136), [
            "• Mandatory & preferred skills extracted",
            "• Semantic cosine & exact keyword overlap",
            "• Status: Evidenced / Weak / Missing"
        ]),
        ("7. Bedrock AI Tailoring", BEDROCK_PURPLE, [
            "• Claude 3.5 Sonnet Converse API invocation",
            "• Governed by Truth-Preserving Engine",
            "• Enforces strict subset of candidate facts"
        ]),
        ("8. Multi-Format Export", EC2_ORANGE, [
            "• Renders PDF, DOCX, LaTeX, TXT",
            "• Real clickable hyperlink annotations",
            "• Download streamed from Amazon S3"
        ]),
    ]

    card_w = (w - 80 - 60) // 4
    card_h = 200

    for idx, (s_title, s_color, s_bullets) in enumerate(stages):
        row = idx // 4
        col = idx % 4
        cx0 = 40 + col * (card_w + 20)
        cx1 = cx0 + card_w
        cy0 = 100 + row * (card_h + 35)
        cy1 = cy0 + card_h

        draw_card(draw, (cx0, cy0, cx1, cy1), s_title, s_color, WHITE, s_color, radius=8, width=2, header_h=30, f_head=f_h3)
        for b_idx, bullet in enumerate(s_bullets):
            draw.text((cx0 + 12, cy0 + 40 + b_idx * 26), bullet, font=f_body, fill=TEXT_DARK)

        # Arrow to next step
        if col < 3:
            draw_arrow(draw, (cx1, cy0 + card_h // 2), (cx1 + 20, cy0 + card_h // 2), color=(71, 85, 105), width=2)
        elif row == 0 and col == 3:
            # Turn around arrow from end of row 1 to start of row 2
            pass

    OUT_PNG_3_2.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(OUT_PNG_3_2), "PNG", dpi=(300, 300))
    print(f"Generated Figure 3.2 PNG: {OUT_PNG_3_2} ({OUT_PNG_3_2.stat().st_size} bytes)")


def generate_png_3_3():
    # Figure 3.3: Amazon Bedrock Truth-Preserving AI Pipeline (2000 x 780)
    w, h = 2000, 780
    img = Image.new("RGBA", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    f_title = get_font("segoeuib", 22)
    f_h2 = get_font("segoeuib", 16)
    f_h3 = get_font("segoeuib", 14)
    f_body = get_font("segoeui", 14)
    f_body_b = get_font("segoeuib", 14)
    f_sub = get_font("segoeui", 12)
    f_label = get_font("segoeuib", 12)

    # Title
    draw_rounded_rect(draw, (40, 20, w - 40, 75), 8, fill=WHITE, outline=BORDER_LIGHT, width=1)
    draw.rounded_rectangle((40, 20, 50, 75), radius=4, fill=BEDROCK_PURPLE)
    draw.text((65, 33), "Resumo — Amazon Bedrock Truth-Preserving AI Verification Architecture", font=f_title, fill=TEXT_DARK)

    # Left: Step 1 Source Facts
    b1 = (60, 120, 520, 290)
    draw_card(draw, b1, "1. Source Résumé Fact Extraction", FASTAPI_BLUE, WHITE, FASTAPI_BLUE, radius=8, header_h=30, f_head=f_h3)
    draw.text((80, 165), "• Extract Candidate Ground-Truth Facts F_source", font=f_body, fill=TEXT_DARK)
    draw.text((80, 195), "• Numerical Metrics (e.g., 40%, 15ms, 100K users)", font=f_body, fill=TEXT_DARK)
    draw.text((80, 225), "• Date Ranges & Employment Chronology", font=f_body, fill=TEXT_DARK)
    draw.text((80, 255), "• Named Organizations, Degrees & Technologies", font=f_body, fill=TEXT_DARK)

    # Step 2: Strict Prompt
    b2 = (580, 120, 1040, 290)
    draw_card(draw, b2, "2. Strict Prompt Construction", (109, 40, 217), WHITE, (109, 40, 217), radius=8, header_h=30, f_head=f_h3)
    draw.text((600, 165), "• Candidate Résumé Context + Targeted Job Criteria", font=f_body, fill=TEXT_DARK)
    draw.text((600, 195), "• Injected Content Formally Flagged as UNTRUSTED", font=f_body, fill=TEXT_DARK)
    draw.text((600, 225), "• System Prompt Constrains AI to Source Truth Only", font=f_body, fill=TEXT_DARK)
    draw.text((600, 255), "• Temperature: 0.2 (Deterministic Low-Variance Output)", font=f_sub, fill=TEXT_MUTED)

    # Step 3: Bedrock
    b3 = (1100, 120, 1560, 290)
    draw_card(draw, b3, "3. Amazon Bedrock Runtime", BEDROCK_PURPLE, (250, 245, 255), BEDROCK_PURPLE, radius=8, header_h=30, f_head=f_h3)
    draw.text((1120, 165), "• Anthropic Claude 3.5 Sonnet / Amazon Titan", font=f_body, fill=TEXT_DARK)
    draw.text((1120, 195), "• Boto3 Converse API via EC2 IAM Instance Profile", font=f_body, fill=TEXT_DARK)
    draw.text((1120, 225), "• Generates Tailored Bullet Drafts & Project Plans", font=f_body, fill=TEXT_DARK)
    draw.text((1120, 255), "• Output Candidate Suggestion: s", font=f_body_b, fill=BEDROCK_PURPLE)

    draw_arrow(draw, (520, 205), (580, 205), color=(71, 85, 105), width=2)
    draw_arrow(draw, (1040, 205), (1100, 205), color=(71, 85, 105), width=2)
    draw_arrow(draw, (1330, 290), (1330, 360), color=(71, 85, 105), width=2)

    # Step 4: Decision Engine Card (Central Decision Box)
    b4 = (800, 360, 1660, 520)
    draw_card(draw, b4, "4. Mathematical Subset Fact Verification Guardrail", (2, 132, 199), (239, 246, 255), (2, 132, 199), radius=10, header_h=34, f_head=f_h2)
    draw.text((830, 410), "FORMAL CRITERIA:   Admissible(s)  <==>  ( Facts(s) ⊆ Facts(Resume) )", font=f_h3, fill=(30, 64, 175))
    draw.text((830, 440), "• Test A: Does suggestion s introduce any technology not in source résumé?", font=f_body, fill=TEXT_DARK)
    draw.text((830, 465), "• Test B: Does suggestion s fabricate or alter any numerical metric or date?", font=f_body, fill=TEXT_DARK)
    draw.text((830, 490), "• Test C: Does suggestion s name an organization or degree not in candidate profile?", font=f_body, fill=TEXT_DARK)

    # Two Outcome Branches (Left = Approved / Green, Right = Rejected / Red)
    draw_arrow(draw, (1000, 520), (500, 580), label="PASS: All Assertions Verified (YES)", color=S3_GREEN, width=3, f_label=f_label, label_side="top")
    draw_arrow(draw, (1460, 520), (1500, 580), label="FAIL: Hallucinated Fact Detected (NO)", color=(220, 38, 38), width=3, f_label=f_label, label_side="top")

    # Approved Outcome Card
    b_yes = (100, 580, 900, 740)
    draw_card(draw, b_yes, "OUTCOME A: Suggestion Approved & Admitted", S3_GREEN, (240, 253, 244), S3_GREEN, radius=8, header_h=30, f_head=f_h3)
    draw.text((120, 625), "• Suggestion tagged with verification status 'verified'", font=f_body, fill=TEXT_DARK)
    draw.text((120, 652), "• Presented to candidate interface as a reviewable edit", font=f_body, fill=TEXT_DARK)
    draw.text((120, 679), "• Applied ONLY upon explicit human approval; audit event logged", font=f_body, fill=TEXT_DARK)
    draw.text((120, 706), "• Candidate credibility fully preserved for technical interviews", font=f_sub, fill=S3_GREEN)

    # Rejected Outcome Card
    b_no = (1100, 580, 1900, 740)
    draw_card(draw, b_no, "OUTCOME B: Suggestion Rejected (Hallucination Blocked)", (220, 38, 38), (254, 242, 242), (220, 38, 38), radius=8, header_h=30, f_head=f_h3)
    draw.text((1120, 625), "• Discards fabricated content instantly without exposing to candidate", font=f_body, fill=TEXT_DARK)
    draw.text((1120, 652), "• Fallback to deterministic rule-based bullet rewording engine", font=f_body, fill=TEXT_DARK)
    draw.text((1120, 679), "• Never fabricates accomplishments to falsely inflate match scores", font=f_body, fill=TEXT_DARK)
    draw.text((1120, 706), "• Anomaly telemetry logged to CloudWatch for prompt tuning", font=f_sub, fill=(220, 38, 38))

    OUT_PNG_3_3.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(OUT_PNG_3_3), "PNG", dpi=(300, 300))
    print(f"Generated Figure 3.3 PNG: {OUT_PNG_3_3} ({OUT_PNG_3_3.stat().st_size} bytes)")


if __name__ == "__main__":
    generate_png_3_1()
    generate_png_3_2()
    generate_png_3_3()
