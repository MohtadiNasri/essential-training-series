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

# Helm palette — deep purple/violet
INK     = HexColor("#0D1B2A")
PURP    = HexColor("#4F1DB5")   # Helm purple
PURP_D  = HexColor("#31138A")
PURP_L  = HexColor("#EAE4FB")
PURP_M  = HexColor("#7B52D4")
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
CODEFG  = HexColor("#1E1A5F")
WHITE   = white

OUTPUT = "/mnt/user-data/outputs/Helm_Essential_Training.pdf"

class ExerciseHeader(Flowable):
    def __init__(self, num, title, duration, difficulty):
        Flowable.__init__(self)
        self.num = num; self.title = title
        self.duration = duration; self.difficulty = difficulty
        self.width = CONTENT_W; self.height = 48

    def draw(self):
        c = self.canv; w = self.width
        diff_colors = {"Easy": TEAL, "Intermediate": PURP, "Advanced": AMBER}
        dc = diff_colors.get(self.difficulty, PURP)
        c.setFillColor(PURP_D); c.rect(0, 0, 72, self.height, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(36, self.height - 16, "EXERCISE")
        c.setFont("Helvetica-Bold", 20); c.drawCentredString(36, 8, self.num)
        c.setFillColor(PURP); c.rect(72, 0, w - 72 - 80 - 80, self.height, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 14)
        c.drawString(72 + 12, self.height / 2 - 6, self.title)
        c.setFillColor(PURP_M); c.rect(w - 160, 0, 80, self.height, fill=1, stroke=0)
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
        c.setFillColor(PURP_M); c.rect(0, 0, 3, self.height, fill=1, stroke=0)
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
            "info":     (PURP_L,  PURP_M,  PURP,  "Helvetica-Bold"),
            "warn":     (AMBER_L, AMBER,   AMBER, "Helvetica-Bold"),
            "tip":      (TEAL_L,  TEAL,    TEAL,  "Helvetica-Bold"),
            "question": (RED_L,   RED,     RED,   "Helvetica-Bold"),
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
        c.drawString(M_LEFT, H - 29, "Helm Essential Training — The Package Manager for Kubernetes")
        c.setFillColor(PURP); c.roundRect(W - M_RIGHT - 58, H - 37, 58, 16, 3, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(W - M_RIGHT - 29, H - 29, "HELM GUIDE")
        c.setStrokeColor(GRAY_M); c.line(M_LEFT, 32, W - M_RIGHT, 32)
        c.setFillColor(GRAY); c.setFont("Helvetica", 8)
        if pg % 2 == 0: c.drawString(M_LEFT, 22, str(pg))
        else: c.drawRightString(W - M_RIGHT, 22, str(pg))
        c.restoreState()


def draw_cover(c):
    c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(PURP); c.rect(0, 0, 16, H, fill=1, stroke=0)
    c.setFillColor(PURP_M); c.rect(16, H - 8, W - 16, 8, fill=1, stroke=0)
    c.setFillColor(HexColor("#2D1A5C"))
    for row in range(9):
        for col in range(11):
            cx = W - 260 + col * 22; cy = H - 55 - row * 22
            if 16 < cx < W - 10: c.circle(cx, cy, 1.5, fill=1, stroke=0)
    c.setFillColor(HexColor("#2A1060")); c.circle(W - 80, H // 2 + 40, 230, fill=1, stroke=0)
    c.setFillColor(HexColor("#1A0A3A")); c.circle(W - 60, H // 2 + 60, 150, fill=1, stroke=0)
    c.setFillColor(PURP); c.setFillAlpha(0.07)
    c.setFont("Helvetica-Bold", 140); c.drawString(20, H // 2 - 70, "Helm")
    c.setFillAlpha(1.0)
    c.setFillColor(PURP_M); c.setFont("Helvetica-Bold", 8)
    c.drawString(34, H - 46, "ESSENTIAL TRAINING SERIES")
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 72); c.drawString(34, H - 130, "Helm")
    c.setFillColor(PURP_M); c.setFont("Helvetica-Bold", 32)
    c.drawString(34, H - 178, "Package Manager")
    c.setFont("Helvetica-Bold", 26); c.drawString(34, H - 213, "for Kubernetes — v4.1.3")
    c.setStrokeColor(PURP_M); c.setLineWidth(2.5); c.line(34, H - 231, 320, H - 231)
    c.setFillColor(HexColor("#94A3B8")); c.setFont("Helvetica", 12)
    c.drawString(34, H - 254, "Charts · Releases · Repositories · Templating · OCI")
    badges = [("8 Exercises", PURP), ("4 Hours", TEAL), ("Intermediate", AMBER)]
    bx = 34
    for label, col in badges:
        bw = len(label) * 7.2 + 20
        c.setFillColor(HexColor("#1E1040")); c.roundRect(bx, H - 292, bw, 22, 4, fill=1, stroke=0)
        c.setStrokeColor(col); c.setLineWidth(0.8); c.roundRect(bx, H - 292, bw, 22, 4, fill=0, stroke=1)
        c.setFillColor(col); c.setFont("Helvetica-Bold", 8); c.drawString(bx + 10, H - 283, label)
        bx += bw + 8
    topics = [
        ("01","Installation & First Chart"),
        ("02","Chart Structure Deep Dive"),
        ("03","Templating & Values"),
        ("04","Repositories & Artifact Hub"),
        ("05","Releases — Install, Upgrade, Rollback"),
        ("06","Hooks & Tests"),
        ("07","OCI Registries & Chart Packaging"),
        ("08","Production — Security & Best Practices"),
    ]
    box_h = len(topics) * 30 + 36
    box_y = H - 292 - 18 - box_h
    c.setFillColor(HexColor("#140A30")); c.roundRect(34, box_y, W - 68, box_h, 6, fill=1, stroke=0)
    c.setFillColor(PURP_M); c.setFont("Helvetica-Bold", 8)
    c.drawString(52, box_y + box_h - 20, "COURSE CONTENTS")
    c.setStrokeColor(HexColor("#2D1A5C")); c.setLineWidth(0.5)
    c.line(52, box_y + box_h - 26, W - 52, box_y + box_h - 26)
    for i, (num, title) in enumerate(topics):
        y = box_y + box_h - 50 - i * 30
        c.setFillColor(PURP_D); c.roundRect(52, y + 2, 26, 16, 3, fill=1, stroke=0)
        c.setFillColor(PURP_L); c.setFont("Helvetica-Bold", 8); c.drawCentredString(65, y + 8, num)
        c.setFillColor(HexColor("#CBD5E1")); c.setFont("Helvetica", 11); c.drawString(88, y + 6, title)
        if i < len(topics) - 1:
            c.setStrokeColor(HexColor("#2D1A5C")); c.setLineWidth(0.3); c.line(52, y, W - 52, y)
    c.setFillColor(PURP); c.rect(0, 0, W, 46, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 10)
    c.drawString(34, 28, "Hands-on Lab — Kubernetes Application Delivery")
    c.setFillColor(PURP_L); c.setFont("Helvetica", 8)
    c.drawRightString(W - 34, 16, "Helm v4.1.3 | CNCF Graduated Project")


def draw_back_cover(c):
    c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(PURP); c.rect(W - 16, 0, 16, H, fill=1, stroke=0)
    c.setFillColor(PURP_M); c.rect(0, H - 8, W - 16, 8, fill=1, stroke=0)
    c.setFillAlpha(0.04); c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 160)
    c.drawString(-10, H // 2 - 80, "Helm"); c.setFillAlpha(1.0)
    c.setFillColor(HexColor("#140A30")); c.roundRect(34, H - 340, W - 84, 290, 8, fill=1, stroke=0)
    c.setFillColor(PURP_M); c.setFont("Helvetica-Bold", 10)
    c.drawString(52, H - 76, "WHAT YOU WILL LEARN")
    c.setStrokeColor(PURP_M); c.setLineWidth(1.5); c.line(52, H - 85, 228, H - 85)
    skills = [
        "Install Helm v4 and deploy your first chart in minutes",
        "Understand chart structure: templates, values, helpers",
        "Master Go templating, conditionals, loops and pipes",
        "Add and manage public and private chart repositories",
        "Install, upgrade, rollback and uninstall releases",
        "Write chart hooks and automated chart tests",
        "Package and publish charts to OCI registries",
        "Secure and optimize Helm for production clusters",
    ]
    for i, skill in enumerate(skills):
        y = H - 115 - i * 26
        c.setFillColor(PURP_M); c.circle(62, y + 5, 4, fill=1, stroke=0)
        c.setFillColor(HexColor("#CBD5E1")); c.setFont("Helvetica", 9.5); c.drawString(76, y, skill)
    c.setFillColor(HexColor("#140A30")); c.roundRect(34, H - 430, W - 84, 72, 8, fill=1, stroke=0)
    c.setFillColor(AMBER); c.setFont("Helvetica-Bold", 9); c.drawString(52, H - 374, "PREREQUISITES")
    c.setStrokeColor(AMBER); c.setLineWidth(0.8); c.line(52, H - 383, 165, H - 383)
    for i, p in enumerate(["Kubernetes basics", "kubectl installed", "Docker & containers"]):
        c.setFillColor(AMBER_L); c.setFont("Helvetica", 9); c.drawString(52 + i * 155, H - 402, "• " + p)
    stats_y = H - 510
    for i, (val, label, col) in enumerate([("4h","Duration",PURP),("8","Exercises",TEAL),("v4.1","Helm",AMBER)]):
        sx = 52 + i * 150
        c.setFillColor(col); c.roundRect(sx, stats_y, 130, 70, 8, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 34); c.drawCentredString(sx + 65, stats_y + 42, val)
        c.setFillColor(PURP_L if col == PURP else WHITE)
        c.setFont("Helvetica", 9); c.drawCentredString(sx + 65, stats_y + 24, label)
    c.setFillColor(HexColor("#2D1A5C")); c.roundRect(34, 90, W - 84, 80, 6, fill=1, stroke=0)
    c.setFillColor(PURP_M); c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W // 2 - 9, 152, '"Stop copy-pasting YAML. Start shipping charts."')
    c.setFillColor(HexColor("#94A3B8")); c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(W // 2 - 9, 133, "Helm — The standard for Kubernetes application packaging")
    c.setFillColor(PURP); c.rect(0, 0, W - 16, 46, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 10); c.drawString(34, 28, "Helm Essential Training")
    c.setFillColor(PURP_L); c.setFont("Helvetica", 8); c.drawRightString(W - 34, 16, "https://helm.sh/docs")


def S(name, **kw): return ParagraphStyle(name, **kw)
BODY = S('body', fontName='Helvetica', fontSize=10.5, leading=16, textColor=INK, spaceBefore=3, spaceAfter=3, alignment=TA_JUSTIFY)
H1   = S('h1',  fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=PURP_D, spaceBefore=20, spaceAfter=8)
H2   = S('h2',  fontName='Helvetica-Bold', fontSize=13.5, leading=17, textColor=INK, spaceBefore=14, spaceAfter=5)
H3   = S('h3',  fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=PURP, spaceBefore=10, spaceAfter=4)
BTEXT= S('bt',  fontName='Helvetica', fontSize=10.5, leading=15, textColor=INK, leftIndent=18, spaceBefore=3, spaceAfter=3)
NTEXT= S('nt',  fontName='Helvetica', fontSize=10.5, leading=15, textColor=INK, leftIndent=22, firstLineIndent=-14, spaceBefore=4, spaceAfter=4)

def sp(h=6):   return Spacer(1, h)
def pb():      return PageBreak()
def h1(t):     return KeepTogether([HRFlowable(width="100%", thickness=2.5, color=PURP, spaceAfter=3), Paragraph(t, H1), HRFlowable(width="100%", thickness=0.5, color=GRAY_M, spaceBefore=2, spaceAfter=10)])
def h2(t):     return Paragraph(t, H2)
def body(t):   return Paragraph(t, BODY)
def bullet(t): return Paragraph(f'<font color="#4F1DB5">•</font>  {t}', BTEXT)
def numbered(n, t): return Paragraph(f'<b>{n}.</b>  {t}', NTEXT)
def code(lines):    return CodeBlock(lines, width=CONTENT_W)
def info(t):        return InfoBox("info",     "ℹ  Info",      [t])
def warn(t):        return InfoBox("warn",     "⚠  Warning",   [t])
def tip(t):         return InfoBox("tip",      "✓  Tip",       [t])
def questions(items): return InfoBox("question","?  Questions", [f"{i+1}.  {q}" for i,q in enumerate(items)])
def divider():  return [sp(20), HRFlowable(width="100%", thickness=1.5, color=PURP_M, spaceBefore=10, spaceAfter=10)]

def tbl(headers, rows, col_widths):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths)
    style = [
        ('BACKGROUND',(0,0),(-1,0),PURP),('TEXTCOLOR',(0,0),(-1,0),WHITE),
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


def content():
    s = []

    s += [h1("Introduction to Helm"), sp(4)]
    s.append(body("Helm is the package manager for Kubernetes — a CNCF graduated project now on version 4.1.3. It lets you define, install, and upgrade even the most complex Kubernetes applications using reusable packages called charts. Helm v4 is the first major release in 6 years, introducing a redesigned plugin system, OCI-first registry support, local content-based caching, and server-side apply."))
    s += [sp(10), h2("Why Helm?"), sp(4)]
    for t in [
        "Package all Kubernetes manifests (Deployment, Service, Ingress...) into one chart",
        "Parameterize everything with values.yaml — one chart, many environments",
        "One-command install, upgrade and rollback of entire applications",
        "Share and reuse charts via Artifact Hub (15,000+ public charts)",
        "Track release history — know exactly what is running and when it changed",
        "Foundation for GitOps tools like ArgoCD and Flux",
    ]: s.append(bullet(t))
    s += [sp(12), h2("Helm v4 — Key changes from v3"), sp(6)]
    s.append(tbl(
        ["Change", "v3 behavior", "v4 behavior"],
        [["Plugin system","Executable binaries","WebAssembly-based runtime"],
         ["Image store","Client-side 3-way merge","Server-side apply (SSA)"],
         ["Caching","No local caching","Content-based local chart cache"],
         ["Registry login","Full URL required","Domain name only"],
         ["Logging","Custom logger","slog (structured, modern)"],
         ["Chart API","v1 and v2","v1, v2 + experimental v3"],
         ["Min Kubernetes","1.20+","1.28+"]],
        [140, 160, 199]
    ))
    s += [sp(12), h2("Core concepts"), sp(6)]
    s.append(tbl(
        ["Concept", "Description"],
        [["Chart",    "A package of Kubernetes manifests + templates + metadata"],
         ["Release",  "A running instance of a chart installed in a cluster"],
         ["Values",   "Configuration parameters that customize a chart (values.yaml)"],
         ["Template", "A Kubernetes manifest with Go template directives"],
         ["Repository","A collection of charts served over HTTP or OCI"],
         ["Hook",     "A chart action triggered at specific lifecycle events"],
         ["Revision", "A numbered snapshot of a release (used for rollback)"]],
        [90, 409]
    ))
    s.append(pb())

    # ── EXO 1
    s.append(exo("1", "Installation & First Chart", "30 min", "Easy"))
    s += [h2("1.1 — Install Helm v4"), sp(4)]
    s.append(numbered(1, "Install via the official script (recommended):"))
    s += [sp(4), code([
        "curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4 | bash",
        "",
        "# Verify",
        "helm version   # version.BuildInfo{Version:\"v4.1.3\", ...}",
    ]), sp(8)]
    s.append(numbered(2, "Or via apt (Ubuntu/Debian):"))
    s += [sp(4), code([
        "curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | \\",
        "  sudo tee /usr/share/keyrings/helm.gpg > /dev/null",
        'echo "deb [signed-by=/usr/share/keyrings/helm.gpg] \\',
        '  https://baltocdn.com/helm/stable/debian/ all main" | \\',
        "  sudo tee /etc/apt/sources.list.d/helm-stable-debian.list",
        "sudo apt-get update && sudo apt-get install helm",
    ]), sp(10)]
    s += [h2("1.2 — Deploy your first chart"), sp(4)]
    s.append(body("Deploy NGINX from the Bitnami repository in 3 commands:"))
    s += [sp(4), code([
        "# Add the Bitnami chart repository",
        "helm repo add bitnami https://charts.bitnami.com/bitnami",
        "helm repo update",
        "",
        "# Install NGINX as a release named 'my-nginx'",
        "helm install my-nginx bitnami/nginx --namespace default",
        "",
        "# Check the release status",
        "helm status my-nginx",
        "helm list",
    ]), sp(10)]
    s += [h2("1.3 — Explore and clean up"), sp(4), code([
        "# See what Kubernetes resources were created",
        "kubectl get all -l app.kubernetes.io/instance=my-nginx",
        "",
        "# Show release history",
        "helm history my-nginx",
        "",
        "# Uninstall the release",
        "helm uninstall my-nginx",
    ]), sp(8),
    info("Helm stores release metadata as Kubernetes Secrets in the target namespace by default. Run 'kubectl get secrets | grep helm' to see them — each revision gets its own Secret."),
    sp(8),
    questions([
        "What is the difference between a chart and a release?",
        "Where does Helm store release state by default in v4?",
        "What happens to the Kubernetes resources when you run 'helm uninstall'?",
        "How do you list all releases across all namespaces?",
    ])]
    s += divider()

    # ── EXO 2
    s.append(exo("2", "Chart Structure Deep Dive", "30 min", "Easy"))
    s += [h2("2.1 — Create a chart from scratch"), sp(4), code([
        "helm create myapp",
        "tree myapp/",
    ]), sp(6)]
    s.append(tbl(
        ["File / Directory", "Purpose"],
        [["Chart.yaml",              "Chart metadata: name, version, description, appVersion"],
         ["values.yaml",             "Default configuration values for the chart"],
         ["templates/",              "Directory of Kubernetes manifest templates"],
         ["templates/deployment.yaml","Deployment template (most charts start here)"],
         ["templates/service.yaml",  "Service template"],
         ["templates/ingress.yaml",  "Ingress template (disabled by default)"],
         ["templates/_helpers.tpl",  "Named template helpers (reusable snippets)"],
         ["templates/NOTES.txt",     "Post-install instructions shown to the user"],
         ["templates/tests/",        "Chart test pods (run with helm test)"],
         ["charts/",                 "Directory for chart dependencies (subcharts)"],
         [".helmignore",             "Files to exclude when packaging the chart"]],
        [180, 319]
    ))
    s += [sp(10), h2("2.2 — Chart.yaml explained"), sp(4), code([
        "apiVersion: v2             # Helm chart API version (v2 for Helm 3+/4)",
        "name: myapp",
        "description: A sample application chart",
        "type: application          # or 'library' for shared templates",
        "version: 0.1.0             # Chart version (SemVer) — bump on chart changes",
        "appVersion: '1.0.0'        # Version of the app being packaged",
        "dependencies:",
        "  - name: postgresql",
        "    version: '~15.0'",
        "    repository: https://charts.bitnami.com/bitnami",
        "    condition: postgresql.enabled",
    ]), sp(8),
    tip("Always use SemVer for your chart version. The chart version and appVersion are independent — bump chart version when templates change, appVersion when the application changes."),
    sp(8),
    questions([
        "What is the difference between 'version' and 'appVersion' in Chart.yaml?",
        "What is a library chart and when would you use one?",
        "What does the 'condition' field in a dependency do?",
    ])]
    s += divider()

    # ── EXO 3
    s.append(exo("3", "Templating & Values", "45 min", "Intermediate"))
    s += [h2("3.1 — Values and overrides"), sp(4), code([
        "# values.yaml (defaults)",
        "replicaCount: 1",
        "image:",
        "  repository: nginx",
        "  tag: '1.27-alpine'",
        "  pullPolicy: IfNotPresent",
        "service:",
        "  type: ClusterIP",
        "  port: 80",
        "resources:",
        "  limits:",
        "    cpu: 100m",
        "    memory: 128Mi",
    ]), sp(8)]
    s.append(body("Override values at install time — multiple methods:"))
    s += [sp(4), code([
        "# Override a single value",
        "helm install myapp ./myapp --set replicaCount=3",
        "",
        "# Override with a custom values file",
        "helm install myapp ./myapp -f values-prod.yaml",
        "",
        "# Combine: file overrides first, --set overrides second",
        "helm install myapp ./myapp -f values-prod.yaml --set image.tag=2.0.0",
        "",
        "# Preview rendered templates without installing",
        "helm template myapp ./myapp -f values-prod.yaml",
    ]), sp(10), h2("3.2 — Template syntax"), sp(4), code([
        "# templates/deployment.yaml",
        "apiVersion: apps/v1",
        "kind: Deployment",
        "metadata:",
        "  name: {{ include \"myapp.fullname\" . }}",
        "  labels:",
        "    {{- include \"myapp.labels\" . | nindent 4 }}",
        "spec:",
        "  replicas: {{ .Values.replicaCount }}",
        "  template:",
        "    spec:",
        "      containers:",
        "      - name: {{ .Chart.Name }}",
        "        image: \"{{ .Values.image.repository }}:{{ .Values.image.tag }}\"",
        "        {{- if .Values.resources }}",
        "        resources:",
        "          {{- toYaml .Values.resources | nindent 10 }}",
        "        {{- end }}",
    ]), sp(10), h2("3.3 — Named templates in _helpers.tpl"), sp(4), code([
        "{{/* Generate a full name for the app */}}",
        "{{- define \"myapp.fullname\" -}}",
        "{{- printf \"%s-%s\" .Release.Name .Chart.Name | trunc 63 | trimSuffix \"-\" }}",
        "{{- end }}",
        "",
        "{{/* Common labels */}}",
        "{{- define \"myapp.labels\" -}}",
        "helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}",
        "app.kubernetes.io/name: {{ .Chart.Name }}",
        "app.kubernetes.io/instance: {{ .Release.Name }}",
        "app.kubernetes.io/version: {{ .Chart.AppVersion }}",
        "{{- end }}",
    ]), sp(8),
    warn("Never use 'helm template' output directly in production by piping to kubectl apply. Use 'helm install' or 'helm upgrade' so Helm can track the release state and enable rollbacks."),
    sp(8),
    questions([
        "What does the '-' in '{{- ' and ' -}}' do in a template?",
        "What is the difference between .Values, .Release, and .Chart objects?",
        "How do you set a default value in a template when the value might be empty?",
    ])]
    s += divider()

    # ── EXO 4
    s.append(exo("4", "Repositories & Artifact Hub", "20 min", "Easy"))
    s += [h2("4.1 — Manage repositories"), sp(4), code([
        "# Add popular repositories",
        "helm repo add bitnami    https://charts.bitnami.com/bitnami",
        "helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx",
        "helm repo add cert-manager https://charts.jetstack.io",
        "helm repo add prometheus  https://prometheus-community.github.io/helm-charts",
        "",
        "# Update all repo indexes",
        "helm repo update",
        "",
        "# List configured repos",
        "helm repo list",
        "",
        "# Search for a chart",
        "helm search repo nginx",
        "helm search repo nginx --versions   # show all available versions",
    ]), sp(10), h2("4.2 — Inspect before installing"), sp(4), code([
        "# Show chart info and README",
        "helm show chart bitnami/nginx",
        "helm show readme bitnami/nginx",
        "",
        "# Show all default values",
        "helm show values bitnami/nginx",
        "",
        "# Save values to a file for customization",
        "helm show values bitnami/nginx > my-nginx-values.yaml",
        "",
        "# Preview what will be installed",
        "helm template my-nginx bitnami/nginx -f my-nginx-values.yaml",
    ]), sp(8),
    tip("Always run 'helm show values' before installing a chart and save a copy of the values you intend to override. This documents your configuration and makes future upgrades much easier."),
    sp(8),
    questions([
        "What does 'helm repo update' do and why is it important to run it regularly?",
        "How do you search Artifact Hub from the command line?",
        "What is the difference between 'helm search repo' and 'helm search hub'?",
    ])]
    s += divider()

    # ── EXO 5
    s.append(exo("5", "Releases — Install, Upgrade, Rollback", "30 min", "Intermediate"))
    s += [h2("5.1 — Install with options"), sp(4), code([
        "# Install into a specific namespace (create if missing)",
        "helm install myapp ./myapp \\",
        "  --namespace production \\",
        "  --create-namespace \\",
        "  -f values-prod.yaml \\",
        "  --wait \\",
        "  --timeout 5m",
        "",
        "# Dry-run: validate without installing",
        "helm install myapp ./myapp --dry-run --debug",
    ]), sp(10), h2("5.2 — Upgrade a release"), sp(4), code([
        "# Upgrade with new values",
        "helm upgrade myapp ./myapp \\",
        "  -f values-prod.yaml \\",
        "  --set image.tag=2.1.0 \\",
        "  --namespace production",
        "",
        "# Install if not exists, upgrade if it does",
        "helm upgrade --install myapp ./myapp -f values-prod.yaml",
        "",
        "# View release history",
        "helm history myapp -n production",
    ]), sp(10), h2("5.3 — Rollback"), sp(4), code([
        "# Roll back to the previous revision",
        "helm rollback myapp -n production",
        "",
        "# Roll back to a specific revision",
        "helm rollback myapp 2 -n production",
        "",
        "# Uninstall but keep release history",
        "helm uninstall myapp -n production --keep-history",
        "",
        "# Get manifest of a specific revision",
        "helm get manifest myapp --revision 2 -n production",
    ]), sp(8),
    tip("Always use '--wait' in CI/CD pipelines so Helm waits for all pods to be Ready before marking the release successful. Combine with '--atomic' to auto-rollback on failure."),
    sp(8),
    questions([
        "What does '--atomic' do during a helm upgrade?",
        "How many revisions does Helm keep by default? How do you change this?",
        "What is the difference between 'helm rollback' and re-running 'helm upgrade'?",
    ])]
    s += divider()

    # ── EXO 6
    s.append(exo("6", "Hooks & Chart Tests", "30 min", "Intermediate"))
    s += [h2("6.1 — Lifecycle hooks"), sp(4)]
    s.append(body("Hooks are Kubernetes Jobs or Pods that run at specific points in the release lifecycle. They are defined with the 'helm.sh/hook' annotation."))
    s += [sp(4), code([
        "# templates/hooks/db-migrate.yaml",
        "apiVersion: batch/v1",
        "kind: Job",
        "metadata:",
        "  name: {{ .Release.Name }}-db-migrate",
        "  annotations:",
        '    "helm.sh/hook": pre-upgrade,pre-install',
        '    "helm.sh/hook-weight": "-5"',
        '    "helm.sh/hook-delete-policy": hook-succeeded',
        "spec:",
        "  template:",
        "    spec:",
        "      restartPolicy: Never",
        "      containers:",
        "      - name: migrate",
        "        image: myapp:{{ .Values.image.tag }}",
        '        command: ["python", "manage.py", "migrate"]',
    ]), sp(10)]
    s.append(tbl(
        ["Hook", "When it runs"],
        [["pre-install",   "Before any resources are installed"],
         ["post-install",  "After all resources are installed"],
         ["pre-upgrade",   "Before an upgrade begins"],
         ["post-upgrade",  "After the upgrade completes"],
         ["pre-rollback",  "Before a rollback begins"],
         ["post-rollback", "After the rollback completes"],
         ["pre-delete",    "Before 'helm uninstall' deletes resources"],
         ["post-delete",   "After 'helm uninstall' completes"]],
        [120, 379]
    ))
    s += [sp(10), h2("6.2 — Chart tests"), sp(4), code([
        "# templates/tests/test-connection.yaml",
        "apiVersion: v1",
        "kind: Pod",
        "metadata:",
        "  name: {{ .Release.Name }}-test-connection",
        "  annotations:",
        '    "helm.sh/hook": test',
        "spec:",
        "  restartPolicy: Never",
        "  containers:",
        "  - name: wget",
        "    image: busybox",
        "    command: ['wget']",
        "    args: ['{{ .Release.Name }}-myapp:{{ .Values.service.port }}']",
        "",
        "# Run chart tests",
        "helm test myapp -n production",
    ]), sp(8),
    info("Hook weights control execution order — lower weights run first. Use 'hook-delete-policy: hook-succeeded' to automatically clean up hook pods after they complete successfully."),
    sp(8),
    questions([
        "What happens if a pre-install hook fails?",
        "What is the difference between hook-weight and hook-delete-policy?",
        "How do chart tests differ from regular pods?",
    ])]
    s += divider()

    # ── EXO 7
    s.append(exo("7", "OCI Registries & Chart Packaging", "30 min", "Intermediate"))
    s += [h2("Context"), sp(4)]
    s.append(body("Helm v4 is OCI-first — charts can be stored in any OCI-compliant registry (Docker Hub, GHCR, ECR, ACR). This replaces the legacy HTTP chart repository model for new projects."))
    s += [sp(10), h2("7.1 — Package a chart"), sp(4), code([
        "# Lint the chart first",
        "helm lint ./myapp",
        "",
        "# Package into a .tgz archive",
        "helm package ./myapp",
        "# Creates: myapp-0.1.0.tgz",
        "",
        "# Package with a specific version",
        "helm package ./myapp --version 1.2.0 --app-version 2.0.0",
    ]), sp(10), h2("7.2 — Push to an OCI registry"), sp(4), code([
        "# Login to the registry (domain only in Helm v4)",
        "helm registry login ghcr.io",
        "",
        "# Push chart to GitHub Container Registry",
        "helm push myapp-0.1.0.tgz oci://ghcr.io/my-org/charts",
        "",
        "# Install directly from OCI registry",
        "helm install myapp oci://ghcr.io/my-org/charts/myapp --version 0.1.0",
        "",
        "# Pull and inspect without installing",
        "helm pull oci://ghcr.io/my-org/charts/myapp --version 0.1.0",
        "helm show chart oci://ghcr.io/my-org/charts/myapp",
    ]), sp(10), h2("7.3 — Manage dependencies"), sp(4), code([
        "# Add dependency to Chart.yaml, then download it",
        "helm dependency update ./myapp",
        "",
        "# List dependencies",
        "helm dependency list ./myapp",
        "",
        "# Install with all dependencies",
        "helm install myapp ./myapp",
    ]), sp(8),
    tip("Use OCI registries for new projects — they support versioning, authentication, and access control out of the box. Docker Hub, GHCR, ECR and ACR all support Helm charts as OCI artifacts."),
    sp(8),
    questions([
        "What is the difference between 'helm push' and 'helm repo push'?",
        "How do you list charts available in an OCI registry?",
        "What does 'helm dependency update' do and when do you need to run it?",
    ])]
    s += divider()

    # ── EXO 8
    s.append(exo("8", "Production & Best Practices", "30 min", "Advanced"))
    s += [h2("8.1 — Values management across environments"), sp(4), code([
        "# Directory structure for multi-env",
        "myapp/",
        "  values.yaml           # defaults (all envs)",
        "  values-dev.yaml       # dev overrides",
        "  values-staging.yaml   # staging overrides",
        "  values-prod.yaml      # production overrides",
        "",
        "# Deploy to production",
        "helm upgrade --install myapp ./myapp \\",
        "  -f values.yaml \\",
        "  -f values-prod.yaml \\",
        "  --namespace production --create-namespace",
    ]), sp(10), h2("8.2 — Security best practices"), sp(4)]
    for t in [
        "Never store secrets in values.yaml — use external-secrets or Vault instead",
        "Use 'helm lint --strict' in CI to catch template errors before deploy",
        "Pin chart versions explicitly — avoid floating versions like '~1.0'",
        "Use '--atomic' in CI/CD to auto-rollback failed upgrades",
        "Scan charts with 'helm plugin install https://github.com/aquasecurity/helm-snyk'",
        "Set resource limits in your values — never deploy without CPU/memory limits",
    ]: s.append(bullet(t))
    s += [sp(10), h2("8.3 — Useful debugging commands"), sp(4), code([
        "# Render templates locally without a cluster",
        "helm template myapp ./myapp -f values-prod.yaml",
        "",
        "# Debug with verbose output",
        "helm install myapp ./myapp --debug --dry-run",
        "",
        "# Get all resources managed by a release",
        "helm get all myapp -n production",
        "",
        "# Get just the values used for a release",
        "helm get values myapp -n production",
        "",
        "# Check if chart can be upgraded (diff plugin)",
        "helm plugin install https://github.com/databus23/helm-diff",
        "helm diff upgrade myapp ./myapp -f values-prod.yaml",
    ]), sp(8),
    warn("Avoid 'helm upgrade --force' — it deletes and recreates resources, causing downtime. Use it only as a last resort. For stuck releases, use 'helm rollback' or fix the underlying issue first."),
    sp(8),
    questions([
        "What does 'helm get values --all' show vs 'helm get values'?",
        "How do you manage Helm secrets without storing them in values.yaml?",
        "What is the helm-diff plugin and why is it essential for production workflows?",
    ])]
    s.append(pb())

    # ── Appendix
    s += [h1("Appendix — Quick Reference"), sp(6), h2("Essential Helm commands"), sp(6)]
    s.append(tbl(
        ["Command", "Description"],
        [["helm repo add name url",          "Add a chart repository"],
         ["helm repo update",                "Refresh all repository indexes"],
         ["helm search repo <term>",         "Search charts in configured repos"],
         ["helm show values repo/chart",     "Show all default values for a chart"],
         ["helm install name chart",         "Install a chart as a new release"],
         ["helm upgrade --install name chart","Install or upgrade a release"],
         ["helm list -A",                    "List all releases in all namespaces"],
         ["helm status name",                "Show release status and notes"],
         ["helm history name",               "Show revision history of a release"],
         ["helm rollback name [revision]",   "Roll back to a previous revision"],
         ["helm uninstall name",             "Remove a release"],
         ["helm template name chart",        "Render templates locally (no install)"],
         ["helm lint ./chart",               "Check chart for errors"],
         ["helm package ./chart",            "Package chart into a .tgz file"],
         ["helm test name",                  "Run chart tests"],
         ["helm diff upgrade name chart",    "Preview changes before upgrade (plugin)"]],
        [210, 289]
    ))
    s += [sp(14), h2("Template objects quick reference"), sp(6)]
    s.append(tbl(
        ["Object", "Example", "Description"],
        [[".Values",   ".Values.image.tag",        "User-supplied values from values.yaml"],
         [".Release",  ".Release.Name",             "Release metadata (Name, Namespace, Revision)"],
         [".Chart",    ".Chart.Name",               "Chart metadata (Name, Version, AppVersion)"],
         [".Files",    ".Files.Get 'config.ini'",   "Access non-template files in the chart"],
         [".Capabilities",".Capabilities.KubeVersion","Kubernetes cluster capabilities"],
         [".Template", ".Template.Name",            "Current template file path"]],
        [100, 165, 234]
    ))
    s += [sp(14), h2("Common template functions"), sp(6)]
    s.append(tbl(
        ["Function", "Example", "Output"],
        [["toYaml",    "{{ toYaml .Values.resources | nindent 10 }}","Converts value to YAML string"],
         ["include",   "{{ include \"app.labels\" . }}",              "Renders a named template"],
         ["quote",     "{{ .Values.name | quote }}",                  "Wraps value in double quotes"],
         ["default",   "{{ .Values.port | default 8080 }}",          "Returns default if value is empty"],
         ["required",  "{{ required \"need it\" .Values.host }}",    "Fails if value is missing"],
         ["trunc",     "{{ .Release.Name | trunc 63 }}",             "Truncates string to N chars"],
         ["printf",    "{{ printf \"%s-%s\" .Release.Name .Chart.Name }}","String formatting"]],
        [80, 195, 224]
    ))
    s += [sp(14), info("Official docs: https://helm.sh/docs  |  Artifact Hub: https://artifacthub.io  |  GitHub: https://github.com/helm/helm")]
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
    w.add_metadata({"/Title": "Helm Essential Training",
                    "/Subject": "The Package Manager for Kubernetes — v4.1.3"})
    with open(OUTPUT, "wb") as f: w.write(f)
    print(f"Done -> {OUTPUT}")

build()
