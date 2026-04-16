from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, HRFlowable, Flowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
import io

W, H = A4
M_LEFT, M_RIGHT, M_TOP, M_BOTTOM = 48, 48, 58, 44
CONTENT_W = W - M_LEFT - M_RIGHT

# Docker brand palette
INK     = HexColor("#0D1B2A")
BLUE    = HexColor("#1D63ED")   # Docker blue
BLUE_D  = HexColor("#0E3FA8")
BLUE_L  = HexColor("#D6E6FF")
BLUE_M  = HexColor("#4A7FEE")
TEAL    = HexColor("#0E7C72")
TEAL_L  = HexColor("#D1F0EC")
AMBER   = HexColor("#C97A0A")
AMBER_L = HexColor("#FFF3D0")
RED_L   = HexColor("#FEECEC")
RED     = HexColor("#C0392B")
GRAY    = HexColor("#6B7280")
GRAY_L  = HexColor("#F1F5F9")
GRAY_M  = HexColor("#E2E8F0")
STRIPE  = HexColor("#F8FAFC")
CODEBG  = HexColor("#F1F5F9")
CODEFG  = HexColor("#1E3A5F")
WHITE   = white

OUTPUT = "/mnt/user-data/outputs/Docker_Essential_Training.pdf"

# ── Custom Flowables ──────────────────────────────────────────────────────────
class ExerciseHeader(Flowable):
    def __init__(self, num, title, duration, difficulty):
        Flowable.__init__(self)
        self.num = num; self.title = title
        self.duration = duration; self.difficulty = difficulty
        self.width = CONTENT_W; self.height = 48

    def draw(self):
        c = self.canv; w = self.width
        diff_colors = {"Easy": TEAL, "Intermediate": BLUE, "Advanced": AMBER}
        dc = diff_colors.get(self.difficulty, BLUE)
        c.setFillColor(BLUE_D); c.rect(0, 0, 72, self.height, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(36, self.height - 16, "EXERCISE")
        c.setFont("Helvetica-Bold", 20); c.drawCentredString(36, 8, self.num)
        c.setFillColor(BLUE); c.rect(72, 0, w - 72 - 80 - 80, self.height, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 14)
        c.drawString(72 + 12, self.height / 2 - 6, self.title)
        c.setFillColor(BLUE_M); c.rect(w - 160, 0, 80, self.height, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w - 120, self.height / 2 + 2, self.duration)
        c.setFont("Helvetica", 8); c.drawCentredString(w - 120, self.height / 2 - 10, "duration")
        c.setFillColor(dc); c.rect(w - 80, 0, 80, self.height, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w - 40, self.height / 2 + 2, self.difficulty)
        c.setFont("Helvetica", 8); c.drawCentredString(w - 40, self.height / 2 - 10, "level")


class CodeBlock(Flowable):
    def __init__(self, lines, width=CONTENT_W):
        Flowable.__init__(self)
        self.lines = lines; self.width = width
        self.font_size = 9; self.line_h = 14
        self.pad_x = 12; self.pad_y = 10
        self.height = len(lines) * self.line_h + self.pad_y * 2

    def draw(self):
        c = self.canv
        c.setFillColor(CODEBG); c.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        c.setFillColor(BLUE_M); c.rect(0, 0, 3, self.height, fill=1, stroke=0)
        c.setFont("Courier", self.font_size)
        for i, line in enumerate(self.lines):
            y = self.height - self.pad_y - (i + 1) * self.line_h + 3
            c.setFillColor(GRAY if line.strip().startswith("#") else CODEFG)
            c.drawString(self.pad_x + 4, y, line)


class InfoBox(Flowable):
    def __init__(self, kind, title, lines, width=CONTENT_W):
        Flowable.__init__(self)
        self.kind = kind; self.title = title
        self.raw_lines = lines if isinstance(lines, list) else [lines]
        self.width = width; self.pad_x = 16; self.pad_y = 11
        self.fs = 9.5; self.lh = 15
        self.max_text_w = width - self.pad_x * 2 - 6
        configs = {
            "info":     (BLUE_L,  BLUE_M, BLUE,  "Helvetica-Bold"),
            "warn":     (AMBER_L, AMBER,  AMBER, "Helvetica-Bold"),
            "tip":      (TEAL_L,  TEAL,   TEAL,  "Helvetica-Bold"),
            "question": (RED_L,   RED,    RED,   "Helvetica-Bold"),
        }
        self.bg, self.border, self.title_color, self.title_font = configs.get(kind, configs["info"])
        from reportlab.pdfbase.pdfmetrics import stringWidth
        self.display_lines = []
        for raw in self.raw_lines:
            words = raw.split(); cur = ""
            for w in words:
                test = (cur + " " + w).strip()
                if stringWidth(test, "Helvetica", self.fs) <= self.max_text_w:
                    cur = test
                else:
                    if cur: self.display_lines.append(cur)
                    cur = w
            if cur: self.display_lines.append(cur)
        self.height = 20 + len(self.display_lines) * self.lh + self.pad_y * 2

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg); c.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=0)
        c.setStrokeColor(self.border); c.setLineWidth(1)
        c.roundRect(0, 0, self.width, self.height, 5, fill=0, stroke=1)
        c.setFillColor(self.border); c.rect(0, 0, 4, self.height, fill=1, stroke=0)
        y = self.height - self.pad_y - 12
        c.setFillColor(self.title_color); c.setFont(self.title_font, 9.5)
        c.drawString(self.pad_x + 4, y, self.title.upper())
        y -= 18; c.setFont("Helvetica", self.fs); c.setFillColor(INK)
        for line in self.display_lines:
            c.drawString(self.pad_x + 4, y, line); y -= self.lh


class MyDoc(SimpleDocTemplate):
    def afterPage(self):
        pg = self.page
        if pg <= 1: return
        c = self.canv; c.saveState()
        c.setStrokeColor(GRAY_M); c.setLineWidth(0.5)
        c.line(M_LEFT, H - 36, W - M_RIGHT, H - 36)
        c.setFillColor(GRAY); c.setFont("Helvetica-Oblique", 7.5)
        c.drawString(M_LEFT, H - 29, "Docker Essential Training — Engine v29 Hands-on Lab")
        c.setFillColor(BLUE); c.roundRect(W - M_RIGHT - 58, H - 37, 58, 16, 3, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(W - M_RIGHT - 29, H - 29, "DOCKER GUIDE")
        c.setStrokeColor(GRAY_M); c.line(M_LEFT, 32, W - M_RIGHT, 32)
        c.setFillColor(GRAY); c.setFont("Helvetica", 8)
        if pg % 2 == 0: c.drawString(M_LEFT, 22, str(pg))
        else: c.drawRightString(W - M_RIGHT, 22, str(pg))
        c.restoreState()


def draw_cover(c):
    c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(BLUE); c.rect(0, 0, 16, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#1D63ED")); c.rect(16, H - 8, W - 16, 8, fill=1, stroke=0)
    # Grid dots
    c.setFillColor(HexColor("#1A3A6C"))
    for row in range(9):
        for col in range(11):
            cx = W - 260 + col * 22; cy = H - 55 - row * 22
            if 16 < cx < W - 10: c.circle(cx, cy, 1.5, fill=1, stroke=0)
    # BG circles
    c.setFillColor(HexColor("#0F2640")); c.circle(W - 80, H // 2 + 40, 230, fill=1, stroke=0)
    c.setFillColor(HexColor("#0A1929")); c.circle(W - 60, H // 2 + 60, 150, fill=1, stroke=0)
    # Ghost whale
    c.setFillColor(HexColor("#1D63ED")); c.setFillAlpha(0.06)
    c.setFont("Helvetica-Bold", 130); c.drawString(20, H // 2 - 70, "Docker")
    c.setFillAlpha(1.0)
    # Labels
    c.setFillColor(HexColor("#1D63ED")); c.setFont("Helvetica-Bold", 8)
    c.drawString(34, H - 46, "ESSENTIAL TRAINING SERIES")
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 72); c.drawString(34, H - 130, "Docker")
    c.setFillColor(BLUE_M); c.setFont("Helvetica-Bold", 34)
    c.drawString(34, H - 178, "Engine v29 Hands-on Lab")
    c.setFont("Helvetica-Bold", 24); c.drawString(34, H - 212, "Images · Containers · Networks · Volumes")
    c.setStrokeColor(HexColor("#1D63ED")); c.setLineWidth(2.5); c.line(34, H - 230, 300, H - 230)
    c.setFillColor(HexColor("#94A3B8")); c.setFont("Helvetica", 12)
    c.drawString(34, H - 253, "Install · Images · Containers · Networks · Volumes · Compose")
    # Badges
    badges = [("8 Exercises", BLUE), ("4 Hours", TEAL), ("Beginner+", AMBER)]
    bx = 34
    for label, col in badges:
        bw = len(label) * 7.2 + 20
        c.setFillColor(HexColor("#1E3A5F")); c.roundRect(bx, H - 292, bw, 22, 4, fill=1, stroke=0)
        c.setStrokeColor(col); c.setLineWidth(0.8); c.roundRect(bx, H - 292, bw, 22, 4, fill=0, stroke=1)
        c.setFillColor(col); c.setFont("Helvetica-Bold", 8); c.drawString(bx + 10, H - 283, label)
        bx += bw + 8
    # Chapter list
    topics = [
        ("01","Docker Installation & Setup"),
        ("02","Images — Build & Manage"),
        ("03","Containers — Run & Inspect"),
        ("04","Networking"),
        ("05","Volumes & Persistent Storage"),
        ("06","Dockerfile Best Practices"),
        ("07","Docker Compose"),
        ("08","Production & Security"),
    ]
    box_h = len(topics) * 30 + 36
    box_y = H - 292 - 18 - box_h
    c.setFillColor(HexColor("#0D2137")); c.roundRect(34, box_y, W - 68, box_h, 6, fill=1, stroke=0)
    c.setFillColor(HexColor("#1D63ED")); c.setFont("Helvetica-Bold", 8)
    c.drawString(52, box_y + box_h - 20, "COURSE CONTENTS")
    c.setStrokeColor(HexColor("#1A3A5C")); c.setLineWidth(0.5)
    c.line(52, box_y + box_h - 26, W - 52, box_y + box_h - 26)
    for i, (num, title) in enumerate(topics):
        y = box_y + box_h - 50 - i * 30
        c.setFillColor(BLUE_D); c.roundRect(52, y + 2, 26, 16, 3, fill=1, stroke=0)
        c.setFillColor(BLUE_L); c.setFont("Helvetica-Bold", 8); c.drawCentredString(65, y + 8, num)
        c.setFillColor(HexColor("#CBD5E1")); c.setFont("Helvetica", 11); c.drawString(88, y + 6, title)
        if i < len(topics) - 1:
            c.setStrokeColor(HexColor("#1A3A5C")); c.setLineWidth(0.3); c.line(52, y, W - 52, y)
    c.setFillColor(BLUE); c.rect(0, 0, W, 46, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 10)
    c.drawString(34, 28, "Docker Essential Training — Engine v29 Hands-on Lab")
    c.setFillColor(BLUE_L); c.setFont("Helvetica", 8)
    c.drawRightString(W - 34, 16, "Docker Engine v29 | Compose v2 | BuildKit")


def draw_back_cover(c):
    c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(BLUE); c.rect(W - 16, 0, 16, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#1D63ED")); c.rect(0, H - 8, W - 16, 8, fill=1, stroke=0)
    c.setFillAlpha(0.04); c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 160)
    c.drawString(-10, H // 2 - 80, "Docker"); c.setFillAlpha(1.0)
    # What you'll learn
    c.setFillColor(HexColor("#0D2137")); c.roundRect(34, H - 340, W - 84, 290, 8, fill=1, stroke=0)
    c.setFillColor(HexColor("#1D63ED")); c.setFont("Helvetica-Bold", 10)
    c.drawString(52, H - 76, "WHAT YOU WILL LEARN")
    c.setStrokeColor(HexColor("#1D63ED")); c.setLineWidth(1.5); c.line(52, H - 85, 228, H - 85)
    skills = [
        "Install Docker Engine v29 and configure the daemon",
        "Build optimized images with Dockerfile and BuildKit",
        "Run, inspect, and manage containers efficiently",
        "Set up bridge, host, and custom overlay networks",
        "Persist data with named volumes and bind mounts",
        "Write production-grade multi-stage Dockerfiles",
        "Orchestrate multi-container apps with Docker Compose",
        "Harden containers with security best practices",
    ]
    for i, skill in enumerate(skills):
        y = H - 115 - i * 26
        c.setFillColor(HexColor("#1D63ED")); c.circle(62, y + 5, 4, fill=1, stroke=0)
        c.setFillColor(HexColor("#CBD5E1")); c.setFont("Helvetica", 9.5); c.drawString(76, y, skill)
    # Prerequisites
    c.setFillColor(HexColor("#0D2137")); c.roundRect(34, H - 430, W - 84, 72, 8, fill=1, stroke=0)
    c.setFillColor(AMBER); c.setFont("Helvetica-Bold", 9); c.drawString(52, H - 374, "PREREQUISITES")
    c.setStrokeColor(AMBER); c.setLineWidth(0.8); c.line(52, H - 383, 165, H - 383)
    for i, p in enumerate(["Linux basics", "Command line", "Basic networking"]):
        c.setFillColor(AMBER_L); c.setFont("Helvetica", 9); c.drawString(52 + i * 155, H - 402, "• " + p)
    # Stats
    stats_y = H - 510
    for i, (val, label, col) in enumerate([("4h","Duration",BLUE),("8","Exercises",TEAL),("v29","Engine",AMBER)]):
        sx = 52 + i * 150
        c.setFillColor(col); c.roundRect(sx, stats_y, 130, 70, 8, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 34); c.drawCentredString(sx + 65, stats_y + 42, val)
        c.setFillColor(HexColor("#D6E9FA") if col == BLUE else WHITE)
        c.setFont("Helvetica", 9); c.drawCentredString(sx + 65, stats_y + 24, label)
    # Tagline
    c.setFillColor(HexColor("#1A3A5C")); c.roundRect(34, 90, W - 84, 80, 6, fill=1, stroke=0)
    c.setFillColor(HexColor("#1D63ED")); c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W // 2 - 9, 152, '"Learn by doing. One command at a time."')
    c.setFillColor(HexColor("#94A3B8")); c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(W // 2 - 9, 133, "Docker Essential Training — Engine v29 Hands-on Lab")
    # Footer
    c.setFillColor(BLUE); c.rect(0, 0, W - 16, 46, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 10); c.drawString(34, 28, "Docker Essential Training")
    c.setFillColor(BLUE_L); c.setFont("Helvetica", 8); c.drawRightString(W - 34, 16, "https://docs.docker.com")


# ── Styles ────────────────────────────────────────────────────────────────────
def S(name, **kw): return ParagraphStyle(name, **kw)
BODY = S('body', fontName='Helvetica', fontSize=10.5, leading=16, textColor=INK, spaceBefore=3, spaceAfter=3, alignment=TA_JUSTIFY)
H1   = S('h1',  fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=BLUE_D, spaceBefore=20, spaceAfter=8)
H2   = S('h2',  fontName='Helvetica-Bold', fontSize=13.5, leading=17, textColor=INK, spaceBefore=14, spaceAfter=5)
H3   = S('h3',  fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=BLUE, spaceBefore=10, spaceAfter=4)
BTEXT= S('bt',  fontName='Helvetica', fontSize=10.5, leading=15, textColor=INK, leftIndent=18, spaceBefore=3, spaceAfter=3)
NTEXT= S('nt',  fontName='Helvetica', fontSize=10.5, leading=15, textColor=INK, leftIndent=22, firstLineIndent=-14, spaceBefore=4, spaceAfter=4)

def sp(h=6):   return Spacer(1, h)
def pb():      return PageBreak()
def h1(text):  return KeepTogether([HRFlowable(width="100%", thickness=2.5, color=BLUE, spaceAfter=3), Paragraph(text, H1), HRFlowable(width="100%", thickness=0.5, color=GRAY_M, spaceBefore=2, spaceAfter=10)])
def h2(text):  return Paragraph(text, H2)
def body(text):return Paragraph(text, BODY)
def bullet(t): return Paragraph(f'<font color="#1D63ED">•</font>  {t}', BTEXT)
def numbered(n, t): return Paragraph(f'<b>{n}.</b>  {t}', NTEXT)
def code(lines):    return CodeBlock(lines, width=CONTENT_W)
def info(text):     return InfoBox("info",     "ℹ  Info",     [text])
def warn(text):     return InfoBox("warn",     "⚠  Warning",  [text])
def tip(text):      return InfoBox("tip",      "✓  Tip",      [text])
def questions(items): return InfoBox("question","?  Questions",[f"{i+1}.  {q}" for i,q in enumerate(items)])
def divider():  return [sp(20), HRFlowable(width="100%", thickness=1.5, color=BLUE_M, spaceBefore=10, spaceAfter=10)]

def tbl(headers, rows, col_widths):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths)
    style = [
        ('BACKGROUND',(0,0),(-1,0),BLUE),('TEXTCOLOR',(0,0),(-1,0),WHITE),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
        ('ALIGN',(0,0),(-1,0),'CENTER'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),
        ('TEXTCOLOR',(0,1),(-1,-1),INK),('LEFTPADDING',(0,0),(-1,-1),8),
        ('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),
        ('BOTTOMPADDING',(0,0),(-1,-1),7),('GRID',(0,0),(-1,-1),0.4,GRAY_M),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0: style.append(('BACKGROUND',(0,i),(-1,i),STRIPE))
    t.setStyle(TableStyle(style)); return t

def exo(num, title, duration, difficulty):
    return KeepTogether([ExerciseHeader(num, title, duration, difficulty), sp(12)])


# ── Content ───────────────────────────────────────────────────────────────────
def content():
    s = []

    # ── Introduction
    s += [h1("Introduction to Docker"), sp(4)]
    s.append(body("Docker is the industry-standard platform for building, shipping, and running containerized applications. Docker Engine v29, the latest stable release (March 2026), brings containerd as the default image store, experimental nftables support, and significant performance improvements for image pull and push operations."))
    s += [sp(10), h2("Why Docker?"), sp(4)]
    for t in [
        "Package applications and all dependencies into a portable image",
        "Run consistently across development, staging and production",
        "Isolate processes — no more 'it works on my machine'",
        "Start containers in milliseconds vs minutes for VMs",
        "Huge ecosystem: Docker Hub hosts 10M+ public images",
        "Foundation for Kubernetes, K3s and all container orchestration",
    ]: s.append(bullet(t))
    s += [sp(12), h2("Docker Engine v29 — What's new"), sp(6)]
    s.append(tbl(
        ["Feature", "Details"],
        [["Containerd image store","Now the default for all fresh installs (was opt-in)"],
         ["nftables support","Experimental — replaces legacy iptables rules"],
         ["Min API version","Raised to 1.44 (Docker < v25 is now EOL)"],
         ["BuildKit","Default builder — faster, cache-efficient builds"],
         ["Containerd runtime","v2.2.2 — improved performance & OCI compliance"],
         ["Go runtime","Updated to Go 1.25 for security & perf gains"]],
        [160, 339]
    ))
    s += [sp(12), h2("Core concepts"), sp(6)]
    s.append(tbl(
        ["Concept", "Description"],
        [["Image","Read-only template — your app + its dependencies, layered"],
         ["Container","A running instance of an image — isolated process"],
         ["Dockerfile","Script of instructions to build an image"],
         ["Registry","Storage for images (Docker Hub, GHCR, private)"],
         ["Volume","Persistent storage that outlives a container"],
         ["Network","Virtual network connecting containers together"],
         ["Compose","Tool to define & run multi-container applications"]],
        [100, 399]
    ))
    s.append(pb())

    # ── Exercise 1
    s.append(exo("1", "Installation & Setup", "30 min", "Easy"))
    s += [h2("Context"), sp(4)]
    s.append(body("You have a Linux machine (Ubuntu 22.04 or Debian 12). You will install Docker Engine v29 using the official apt repository, configure the daemon, and run your first container."))
    s += [sp(10), h2("1.1 — Install Docker Engine v29"), sp(4)]
    s.append(numbered(1, "Remove any old versions:"))
    s += [sp(4), code([
        "for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do",
        "  sudo apt-get remove -y $pkg 2>/dev/null; done",
    ]), sp(8)]
    s.append(numbered(2, "Add Docker's official apt repository:"))
    s += [sp(4), code([
        "sudo apt-get update && sudo apt-get install -y ca-certificates curl",
        "sudo install -m 0755 -d /etc/apt/keyrings",
        "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \\",
        "  -o /etc/apt/keyrings/docker.asc",
        "sudo chmod a+r /etc/apt/keyrings/docker.asc",
        "",
        'echo "deb [arch=$(dpkg --print-architecture) \\',
        '  signed-by=/etc/apt/keyrings/docker.asc] \\',
        '  https://download.docker.com/linux/ubuntu \\',
        '  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \\',
        '  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',
    ]), sp(8)]
    s.append(numbered(3, "Install the latest Docker Engine v29:"))
    s += [sp(4), code([
        "sudo apt-get update",
        "sudo apt-get install -y docker-ce docker-ce-cli containerd.io \\",
        "  docker-buildx-plugin docker-compose-plugin",
    ]), sp(8)]
    s.append(numbered(4, "Add your user to the docker group (no more sudo):"))
    s += [sp(4), code([
        "sudo usermod -aG docker $USER",
        "newgrp docker",
    ]), sp(10)]
    s += [h2("1.2 — Verify the installation"), sp(4),
    code([
        "docker --version          # Docker version 29.x.x",
        "docker info               # Engine details, storage driver",
        "docker run hello-world    # Pull & run your first container",
    ]), sp(10),
    info("Docker Engine v29 uses containerd as the default image store. Run 'docker info | grep -i storage' — you should see 'overlayfs' (containerd snapshotter) on fresh installs."),
    sp(8),
    questions([
        "What storage driver is reported by 'docker info'?",
        "What is the difference between docker-ce and docker-ce-cli?",
        "Why add your user to the docker group? What are the security implications?",
        "What happens step by step when you run 'docker run hello-world'?",
    ])]
    s += divider()

    # ── Exercise 2
    s.append(exo("2", "Images — Build & Manage", "30 min", "Easy"))
    s += [h2("Context"), sp(4)]
    s.append(body("Images are the foundation of Docker. You will pull images from Docker Hub, inspect their layers, tag and push to a registry, and understand how the layer cache works."))
    s += [sp(10), h2("2.1 — Pull and inspect images"), sp(4),
    code([
        "# Pull specific versions (always pin tags in production!)",
        "docker pull nginx:1.27-alpine",
        "docker pull node:22-alpine",
        "docker pull postgres:17-alpine",
        "",
        "# List local images",
        "docker images",
        "",
        "# Inspect image layers and metadata",
        "docker inspect nginx:1.27-alpine",
        "docker history nginx:1.27-alpine",
    ]), sp(10), h2("2.2 — Build a custom image"), sp(4),
    s.append(body("Create a simple Node.js app and build an image:")),
    sp(4), code([
        "# app.js",
        'const http = require("http");',
        'http.createServer((req, res) => {',
        '  res.end("Hello from Docker v29!\\n");',
        '}).listen(3000);',
    ]), sp(6), code([
        "# Dockerfile",
        "FROM node:22-alpine",
        "WORKDIR /app",
        "COPY app.js .",
        'CMD ["node", "app.js"]',
    ]), sp(6), code([
        "docker build -t my-app:1.0 .",
        "docker images my-app",
    ]), sp(10), h2("2.3 — Tag and push to Docker Hub"), sp(4),
    code([
        "docker login",
        "docker tag my-app:1.0 <your-username>/my-app:1.0",
        "docker push <your-username>/my-app:1.0",
        "",
        "# Remove local image and pull it back",
        "docker rmi <your-username>/my-app:1.0",
        "docker pull <your-username>/my-app:1.0",
    ]), sp(8),
    tip("Always use specific tags (nginx:1.27-alpine) instead of 'latest' in production. The 'latest' tag is just a convention — it is not automatically the newest version and can change unexpectedly."),
    sp(8),
    questions([
        "What is an image layer? Why does Docker use a layered filesystem?",
        "What is the build cache and when does Docker invalidate it?",
        "What is the difference between CMD and ENTRYPOINT in a Dockerfile?",
    ])]
    s += divider()

    # ── Exercise 3
    s.append(exo("3", "Containers — Run & Inspect", "30 min", "Easy"))
    s += [h2("3.1 — Run containers"), sp(4),
    code([
        "# Run in foreground (Ctrl+C to stop)",
        "docker run nginx:1.27-alpine",
        "",
        "# Run detached, name it, map port 8080 -> 80",
        "docker run -d --name web -p 8080:80 nginx:1.27-alpine",
        "",
        "# Run with environment variables",
        "docker run -d --name db \\",
        "  -e POSTGRES_PASSWORD=secret \\",
        "  -e POSTGRES_DB=myapp \\",
        "  postgres:17-alpine",
        "# Note: no --network here — DNS by name tested in Exercise 4",
        "",
        "# Run interactively",
        "docker run -it --rm alpine:3.21 sh",
    ]), sp(10), h2("3.2 — Inspect and debug"), sp(4),
    code([
        "# List running containers",
        "docker ps",
        "",
        "# List all containers (including stopped)",
        "docker ps -a",
        "",
        "# Stream logs",
        "docker logs -f web",
        "",
        "# Execute a command inside a running container",
        "docker exec -it web sh",
        "",
        "# Inspect container details (IP, mounts, env vars...)",
        "docker inspect web",
        "",
        "# Live resource usage",
        "docker stats",
    ]), sp(10), h2("3.3 — Lifecycle management"), sp(4),
    code([
        "docker stop web          # Graceful stop (SIGTERM then SIGKILL)",
        "docker start web         # Restart a stopped container",
        "docker restart web       # Stop + start",
        "docker rm web            # Remove stopped container",
        "docker rm -f web         # Force remove running container",
        "",
        "# Clean up everything unused",
        "docker system prune -a",
    ]), sp(8),
    warn("'docker system prune -a' removes ALL unused images, containers, networks and build cache. Use with caution in shared environments — it cannot be undone."),
    sp(8),
    questions([
        "What is the difference between 'docker stop' and 'docker kill'?",
        "What does --rm do in 'docker run --rm'? When should you use it?",
        "How do you copy a file from a running container to the host?",
    ]),
    warn("CLEANUP before Exercise 4 — remove containers created in this exercise to avoid name conflicts: docker rm -f web db")]
    s += divider()

    # ── Exercise 4
    s.append(exo("4", "Networking", "30 min", "Intermediate"))
    s += [h2("Context"), sp(4)]
    s.append(body("Docker provides isolated virtual networks so containers can communicate securely. You will create custom networks, connect containers, and understand DNS-based service discovery."))
    s += [sp(10), h2("4.1 — Network types"), sp(6)]
    s.append(tbl(
        ["Driver", "Use case", "Container DNS"],
        [["bridge","Default — isolated network on one host","By container name"],
         ["host","Container shares host network stack","N/A"],
         ["none","No networking — fully isolated","N/A"],
         ["overlay","Multi-host (Swarm / Kubernetes)","By service name"],
         ["macvlan","Container gets its own MAC/IP","Depends on setup"]],
        [70, 240, 149]
    ))
    s += [sp(10), h2("4.2 — Create and use a custom network"), sp(4),
    code([
        "# Create an isolated bridge network",
        "docker network create my-net",
        "",
        "# Run containers on the same network",
        "docker run -d --name app --network my-net nginx:1.27-alpine",
        "docker run -d --name db  --network my-net postgres:17-alpine \\",
        "  -e POSTGRES_PASSWORD=secret",
        "",
        "# Containers can reach each other by name!",
        "docker exec -it app sh -c 'wget -qO- http://app'",
        "docker exec -it app sh -c 'nc -zv db 5432 && echo connected'",
        "",
        "# Inspect the network",
        "docker network inspect my-net",
    ]), sp(10), h2("4.3 — Port publishing"), sp(4),
    code([
        "# Publish a specific port",
        "docker run -d -p 8080:80 nginx:1.27-alpine",
        "",
        "# Publish to a specific host interface only",
        "docker run -d -p 127.0.0.1:8080:80 nginx:1.27-alpine",
        "",
        "# List all port mappings",
        "docker port <container>",
    ]), sp(8),
    tip("Always use user-defined bridge networks instead of the default bridge. The default bridge does not support DNS resolution by container name — your containers cannot find each other by name without a custom network."),
    sp(8),
    questions([
        "Why can containers on the same custom network resolve each other by name?",
        "What is the difference between -p 80:80 and -p 127.0.0.1:80:80?",
        "How do you connect an already-running container to an additional network?",
    ]),
    warn("CLEANUP before Exercise 5 — remove containers created in this exercise: docker rm -f app db")]
    s += divider()

    # ── Exercise 5
    s.append(exo("5", "Volumes & Persistent Storage", "30 min", "Intermediate"))
    s += [h2("Context"), sp(4)]
    s.append(body("Containers are ephemeral — data written inside a container is lost when it is removed. Volumes and bind mounts allow you to persist data and share it between containers and the host."))
    s += [sp(10), h2("5.1 — Storage types"), sp(6)]
    s.append(tbl(
        ["Type", "Location", "Best for"],
        [["Named volume","Docker-managed (/var/lib/docker/volumes/)","Databases, app data"],
         ["Bind mount","Any host path","Source code, configs"],
         ["tmpfs mount","Host memory only","Secrets, temp data"]],
        [100, 210, 189]
    ))
    s += [sp(10), h2("5.2 — Named volumes"), sp(4),
    code([
        "# Create a named volume",
        "docker volume create pgdata",
        "",
        "# Run PostgreSQL with the volume (on my-net for DNS access)",
        "docker run -d --name db \\",
        "  --network my-net \\",
        "  -v pgdata:/var/lib/postgresql/data \\",
        "  -e POSTGRES_PASSWORD=secret \\",
        "  postgres:17-alpine",
        "",
        "# Insert data, remove container, verify data persists",
        "docker exec -it db psql -U postgres -c 'CREATE DATABASE testdb;'",
        "docker rm -f db",
        "",
        "# Start a new container with the same volume",
        "docker run -d --name db2 --network my-net -v pgdata:/var/lib/postgresql/data \\",
        "  -e POSTGRES_PASSWORD=secret postgres:17-alpine",
        "docker exec -it db2 psql -U postgres -c '\\l'  # testdb still there!",
    ]), sp(10), h2("5.3 — Bind mounts for development"), sp(4),
    body("A bind mount replaces the container's /app directory with your host folder — it OVERRIDES what was COPYed in the image. Your host folder must already have app.js or the container will crash immediately."),
    sp(6),
    code([
        "# Step 1: make sure app.js exists in your current host directory",
        "ls app.js",
        "",
        "# If not, create it:",
        "cat > app.js << 'EOF'",
        'const http = require("http");',
        'http.createServer((req, res) => {',
        '  res.end("Hello from bind mount!\\n");',
        "}).listen(3000);",
        "EOF",
        "",
        "# Step 2: run with bind mount (quote pwd — handles spaces in path!)",
        "# Remove any existing dev container first (stop does not remove it!)",
        "docker rm -f dev 2>/dev/null || true",
        "docker run -d --name dev \\",
        '  -v "$(pwd)":/app \\',
        "  -p 3000:3000 \\",
        "  node:22-alpine node /app/app.js",
        "",
        "# Step 3: verify the container is running",
        "docker ps",
        "curl http://localhost:3000",
        "",
        "# Step 4: verify the file is visible inside the container",
        "docker exec dev cat /app/app.js",
        "",
        "# Step 5: edit app.js on the HOST — change is instant inside!",
        'echo "// updated on host" >> app.js',
        "docker exec dev cat /app/app.js   # shows the update immediately",
    ]), sp(8),
    info("The bind mount (-v) shadows whatever was COPYed into the image. The image's /app is replaced by your host directory at runtime. This is why you can edit files on your machine and see changes instantly inside the container — no rebuild needed."),
    sp(8),
    warn("Never use bind mounts in production for application code — use COPY in your Dockerfile instead. Bind mounts are for development workflows and configuration injection only."),
    sp(8),
    questions([
        "What is the difference between a named volume and a bind mount?",
        "Where are named volume files stored on the host? How do you find out?",
        "How do you back up a Docker volume?",
    ]),
    warn("CLEANUP before Exercise 6 — remove containers created in this exercise: docker rm -f db db2 dev")]
    s += divider()

    # ── Exercise 6
    s.append(exo("6", "Dockerfile Best Practices", "35 min", "Intermediate"))
    s += [h2("Context"), sp(4)]
    s.append(body("A well-written Dockerfile produces smaller, faster, and more secure images. In this exercise you will create all the files from scratch, build two versions of the same image (normal vs multi-stage), compare their sizes, and understand exactly what each step does."))
    s += [sp(10), h2("6.1 — Files you need to create"), sp(4)]
    s.append(body("You need 4 files in your working directory. Create them one by one:"))
    s += [sp(6), code([
        "# First make a clean folder for this exercise",
        "mkdir -p ~/docker-ex6 && cd ~/docker-ex6",
    ]), sp(8), h2("File 1 — app.js (your application)"), sp(4),
    code([
        "cat > app.js << 'EOF'",
        'const http = require("http");',
        'http.createServer((req, res) => {',
        '  res.writeHead(200, {"Content-Type": "text/plain"});',
        '  res.end("Hello from multi-stage build!\\n");',
        "}).listen(3000);",
        'console.log("Server running on port 3000");',
        "EOF",
    ]), sp(8), h2("File 2 — package.json (app dependencies)"), sp(4),
    code([
        "cat > package.json << 'EOF'",
        "{",
        '  "name": "myapp",',
        '  "version": "1.0.0",',
        '  "main": "app.js",',
        '  "scripts": { "start": "node app.js" }',
        "}",
        "EOF",
    ]), sp(8), h2("File 3 — .dockerignore (what NOT to copy into the image)"), sp(4),
    code([
        "cat > .dockerignore << 'EOF'",
        "node_modules",
        ".git",
        "*.log",
        ".env",
        "EOF",
    ]), sp(6),
    info(".dockerignore works exactly like .gitignore — it tells Docker which files to EXCLUDE from the build context. Without it, node_modules (often 200MB+) gets sent to the Docker daemon on every build, making builds very slow."),
    sp(10), h2("6.2 — What is a multi-stage build and WHY?"), sp(4)]
    s.append(body("A normal Dockerfile copies everything into one image — including build tools you don't need at runtime. A multi-stage build uses TWO stages: the first stage installs/builds everything, the second stage copies ONLY the final files. The result is a much smaller, more secure image."))
    s += [sp(6), info("Our app.js uses only Node's built-in 'http' module — no external packages needed, so no node_modules to copy. In a real app with dependencies (express, lodash...) you would add 'RUN npm install' in stage 1 and 'COPY --from=builder /app/node_modules ./node_modules' in stage 2."),
    sp(8), code([
        "# Without multi-stage: one big image with everything",
        "FROM node:22-alpine",
        "WORKDIR /app",
        "COPY package*.json .",
        "RUN npm install          # installs into the image",
        "COPY . .",
        'CMD ["node", "app.js"]   # image contains npm, build tools, etc.',
    ]), sp(8), h2("File 4 — Dockerfile (multi-stage version)"), sp(4),
    code([
        "cat > Dockerfile << 'EOF'",
        "# ── Stage 1: Builder ──────────────────────────────────────",
        "# This stage prepares files — it is THROWN AWAY after",
        "FROM node:22-alpine AS builder",
        "WORKDIR /app",
        "# Copy package.json first (good habit — cache layer)",
        "COPY package*.json .",
        "# Copy the app source code",
        "COPY . .",
        "",
        "# ── Stage 2: Runtime ──────────────────────────────────────",
        "# This is the FINAL image — only what we actually need",
        "FROM node:22-alpine",
        "WORKDIR /app",
        "# Copy ONLY the app source from the builder stage",
        "# (no node_modules needed — app uses built-in http module only)",
        "COPY --from=builder /app/app.js .",
        "COPY --from=builder /app/package.json .",
        "# Security: never run as root in production",
        "RUN addgroup -S appgroup && adduser -S appuser -G appgroup",
        "USER appuser",
        'CMD ["node", "app.js"]',
        "EOF",
    ]), sp(10), h2("6.3 — Build, compare sizes and run"), sp(4),
    code([
        "# Build the multi-stage image",
        "docker build -t myapp:multistage .",
        "",
        "# See all your images and their sizes",
        "docker images myapp",
        "",
        "# Run it",
        "docker run -d --name api -p 3000:3000 myapp:multistage",
        "",
        "# Test it",
        "curl http://localhost:3000",
        "# Expected: Hello from multi-stage build!",
        "",
        "# Check who the process runs as (should NOT be root)",
        "docker exec api whoami",
        "# Expected: appuser",
    ]), sp(8),
    tip("Run 'docker history myapp:multistage' to see every layer and its size. You will see that the builder stage layers are NOT present in the final image — only the COPY --from=builder layers appear."),
    sp(10), h2("6.4 — Layer cache in action"), sp(4),
    code([
        "# Edit app.js (simulate a code change)",
        "echo '// new feature' >> app.js",
        "",
        "# Rebuild — watch which steps say 'CACHED'",
        "docker build -t myapp:multistage .",
        "",
        "# You will see:",
        "# Step: COPY package*.json .  --> CACHED (package.json unchanged)",
        "# Step: COPY . .              --> not cached (app.js changed)",
        "",
        "# This is WHY we copy package.json BEFORE the rest of the code",
        "# When only code changes, package layers stay cached = faster builds",
    ]), sp(8),
    warn("CLEANUP after Exercise 6: docker rm -f api"),
    sp(8),
    questions([
        "How does a multi-stage build reduce the final image size?",
        "Why do we COPY package*.json before COPY . . in the Dockerfile?",
        "What does .dockerignore do and why is it important?",
        "What does 'USER appuser' do and why is it a security best practice?",
    ])]
    s += divider()

    # ── Exercise 7
    s.append(exo("7", "Docker Compose", "30 min", "Intermediate"))
    s += [h2("Context"), sp(4)]
    s.append(body("Docker Compose lets you define and run multi-container applications from a single YAML file. The Compose plugin (v2) is now bundled with Docker Engine — no separate install needed."))
    s += [sp(10), h2("7.0 — Cleanup before starting"), sp(4)]
    s.append(body("Before starting this exercise, stop and remove ALL containers from previous exercises. Port 3000 and container names must be free or Compose will fail to start."))
    s += [sp(6), code([
        "# Stop and remove ALL running containers",
        "docker rm -f $(docker ps -aq) 2>/dev/null || true",
        "",
        "# Verify nothing is running",
        "docker ps",
        "# Expected: empty list (no containers)",
        "",
        "# Also check port 3000 is free",
        "ss -tlnp | grep 3000",
        "# Expected: no output (port is free)",
    ]), sp(8),
    warn("If you skip this step and port 3000 is already used by a container from a previous exercise, docker compose up will fail with 'port is already allocated'. Always clean up between exercises."),
    sp(10), h2("7.1 — A full-stack compose.yaml"), sp(4)]
    s.append(body("Now create a clean folder for this exercise and create the compose.yaml file:"))
    s += [sp(6), code([
        "# Create a clean folder for this exercise",
        "mkdir -p ~/docker-ex7 && cd ~/docker-ex7",
    ]), sp(8), code([
        "cat > compose.yaml << 'EOF'",
        "services:",
        "",
        "  db:",
        "    image: postgres:17-alpine",
        "    environment:",
        "      POSTGRES_DB: myapp",
        "      POSTGRES_USER: user",
        "      POSTGRES_PASSWORD: secret",
        "    volumes:",
        "      - pgdata:/var/lib/postgresql/data",
        "    healthcheck:",
        "      test: ['CMD-SHELL', 'pg_isready -U user -d myapp']",
        "      interval: 10s",
        "      retries: 5",
        "",
        "  api:",
        "    build: .",
        "    ports:",
        "      - '3000:3000'",
        "    environment:",
        "      DATABASE_URL: postgres://user:secret@db:5432/myapp",
        "    depends_on:",
        "      db:",
        "        condition: service_healthy",
        "",
        "volumes:",
        "  pgdata:",
        "EOF",
    ]), sp(8),
    info("The 'api' service uses 'build: .' which means Compose will look for a Dockerfile in the current directory and build it. Copy your app.js, package.json and Dockerfile from ~/docker-ex6 into this folder first."),
    sp(6), code([
        "# Copy the app files from Exercise 6",
        "cp ~/docker-ex6/app.js ~/docker-ex6/package.json ~/docker-ex6/Dockerfile .",
        "",
        "# Verify all files are present",
        "ls -la",
        "# Expected: app.js  compose.yaml  Dockerfile  package.json",
    ]), sp(10), h2("7.2 — Start the stack and verify"), sp(4),
    code([
        "# Start all services detached (builds api image automatically)",
        "docker compose up -d --build",
        "",
        "# Check all services are running",
        "docker compose ps",
        "",
        "# Stream logs to see db healthcheck passing and api starting",
        "docker compose logs -f",
        "# Press Ctrl+C to stop following logs",
        "",
        "# Test the api service",
        "curl http://localhost:3000",
        "",
        "# Connect to the database",
        "docker compose exec db psql -U user myapp -c '\\l'",
    ]), sp(8),
    tip("The 'depends_on: condition: service_healthy' means the api container will NOT start until the db healthcheck passes. Without this, your app would crash trying to connect to a database that isn't ready yet."),
    sp(10), h2("7.3 — Essential Compose commands"), sp(4),
    code([
        "docker compose up -d          # Start all services detached",
        "docker compose up --build     # Rebuild images before starting",
        "docker compose ps             # Status of all services",
        "docker compose logs -f api    # Stream logs from the api service",
        "docker compose exec db psql -U user myapp  # Shell into db",
        "docker compose restart api    # Restart one service only",
        "docker compose stop           # Stop containers (keeps them)",
        "docker compose down           # Stop and remove containers",
        "docker compose down -v        # Also remove volumes (deletes data!)",
    ]), sp(8),
    warn("CLEANUP after Exercise 7: docker compose down -v"),
    sp(8),
    questions([
        "What is the difference between 'docker compose stop' and 'docker compose down'?",
        "How do you scale a service to 3 replicas with Docker Compose?",
        "How do you override compose values for different environments (dev vs prod)?",
    ])]
    s += divider()

    # ── Exercise 8
    s.append(exo("8", "Production & Security", "30 min", "Advanced"))
    s += [h2("8.1 — Resource limits"), sp(4),
    code([
        "# Limit CPU and memory",
        "docker run -d \\",
        "  --memory='512m' \\",
        "  --memory-swap='512m' \\",
        "  --cpus='0.5' \\",
        "  --name api nginx:1.27-alpine",
        "",
        "# In compose.yaml",
        "services:",
        "  api:",
        "    deploy:",
        "      resources:",
        "        limits:",
        "          cpus: '0.5'",
        "          memory: 512M",
    ]), sp(10), h2("8.2 — Health checks"), sp(4),
    code([
        "# In Dockerfile",
        "HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\",
        "  CMD curl -f http://localhost:3000/health || exit 1",
        "",
        "# Check health status",
        "docker inspect --format='{{.State.Health.Status}}' api",
    ]), sp(10), h2("8.3 — Security hardening"), sp(4),
    code([
        "# Read-only root filesystem",
        "docker run --read-only --tmpfs /tmp nginx:1.27-alpine",
        "",
        "# Drop all Linux capabilities, add only what is needed",
        "docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx:1.27-alpine",
        "",
        "# Prevent privilege escalation",
        "docker run --security-opt no-new-privileges nginx:1.27-alpine",
        "",
        "# Scan image for CVEs",
        "docker scout cves nginx:1.27-alpine",
    ]), sp(10), h2("8.4 — Useful production commands"), sp(4),
    code([
        "# View daemon logs",
        "journalctl -u docker -f",
        "",
        "# Configure daemon (restart required)",
        "sudo nano /etc/docker/daemon.json",
        "sudo systemctl restart docker",
        "",
        "# Monitor all containers",
        "docker stats --no-stream",
        "",
        "# Disk usage breakdown",
        "docker system df -v",
    ]), sp(8),
    warn("Always set memory limits in production. A container without limits can consume all host memory and crash the entire machine. Pair memory limits with --memory-swap to prevent swap abuse."),
    sp(8),
    questions([
        "What happens to a container when it exceeds its memory limit?",
        "What is the principle of least privilege and how does --cap-drop enforce it?",
        "How do you configure Docker daemon to use a private registry by default?",
    ])]
    s.append(pb())

    # ── Appendix
    s += [h1("Appendix — Quick Reference"), sp(6), h2("Essential Docker commands"), sp(6)]
    s.append(tbl(
        ["Command", "Description"],
        [["docker build -t name:tag .",     "Build image from Dockerfile in current directory"],
         ["docker pull image:tag",          "Pull an image from a registry"],
         ["docker push image:tag",          "Push an image to a registry"],
         ["docker run -d -p 8080:80 image", "Run container detached, map port"],
         ["docker exec -it name sh",        "Open a shell in a running container"],
         ["docker logs -f name",            "Stream container logs"],
         ["docker stop / rm name",          "Stop and remove a container"],
         ["docker images",                  "List local images"],
         ["docker system prune -a",         "Remove all unused resources"],
         ["docker stats",                   "Live CPU / memory per container"],
         ["docker compose up -d",           "Start all Compose services detached"],
         ["docker compose down -v",         "Stop services and remove volumes"],
         ["docker scout cves image:tag",    "Scan image for known CVEs"]],
        [210, 289]
    ))
    s += [sp(14), h2("Dockerfile instructions"), sp(6)]
    s.append(tbl(
        ["Instruction", "Description"],
        [["FROM image:tag",        "Base image — always the first instruction"],
         ["WORKDIR /path",         "Set working directory for subsequent instructions"],
         ["COPY src dest",         "Copy files from build context into the image"],
         ["RUN command",           "Execute a command during build (creates a new layer)"],
         ["ENV KEY=value",         "Set environment variable in the image"],
         ["EXPOSE port",           "Document which port the container listens on"],
         ["USER name",             "Switch to a non-root user"],
         ["CMD [\"cmd\", \"arg\"]",  "Default command when container starts"],
         ["HEALTHCHECK ...",       "Define a health check command"],
         ["ARG name",              "Build-time variable (not persisted in image)"]],
        [160, 339]
    ))
    s += [sp(14), h2("Key files and directories"), sp(6)]
    s.append(tbl(
        ["Path", "Contents"],
        [["/etc/docker/daemon.json",         "Docker daemon configuration"],
         ["/var/lib/docker/volumes/",        "Named volume data"],
         ["/var/lib/docker/overlay2/",       "Image layer storage (overlayfs)"],
         ["/var/run/docker.sock",            "Docker daemon Unix socket"],
         ["~/.docker/config.json",           "Registry credentials & auth config"],
         ["compose.yaml",                    "Docker Compose application definition"]],
        [230, 269]
    ))
    s += [sp(14), info("Official docs: https://docs.docker.com  |  Docker Hub: https://hub.docker.com  |  GitHub: https://github.com/moby/moby")]
    return s


def build():
    from pypdf import PdfWriter, PdfReader
    cov = io.BytesIO()
    c = canvas.Canvas(cov, pagesize=A4); draw_cover(c); c.showPage(); c.save(); cov.seek(0)
    bak = io.BytesIO()
    c = canvas.Canvas(bak, pagesize=A4); draw_back_cover(c); c.showPage(); c.save(); bak.seek(0)
    inn = io.BytesIO()
    doc = MyDoc(inn, pagesize=A4, leftMargin=M_LEFT, rightMargin=M_RIGHT,
                topMargin=M_TOP, bottomMargin=M_BOTTOM)
    doc.build(content()); inn.seek(0)
    w = PdfWriter()
    for buf in [cov, inn, bak]:
        for pg in PdfReader(buf).pages: w.add_page(pg)
    w.add_metadata({"/Title": "Docker Essential Training",
                    "/Subject": "Engine v29 Hands-on Lab"})
    with open(OUTPUT, "wb") as f: w.write(f)
    print(f"Done -> {OUTPUT}")

build()
