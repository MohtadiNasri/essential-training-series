from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, HRFlowable, Flowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
import io
from pypdf import PdfWriter, PdfReader

W, H = A4
ML, MR, MT, MB = 48, 48, 58, 44
CW = W - ML - MR

INK=HexColor("#0D1B2A"); WHITE=white; GRAY=HexColor("#6B7280"); GRAY_M=HexColor("#E2E8F0")
STRIPE=HexColor("#F8FAFC"); CODEBG=HexColor("#F1F5F9"); CODEFG=HexColor("#1E1A5F")
TEAL=HexColor("#0E7C72"); TEAL_L=HexColor("#D1F0EC")
AMBER=HexColor("#C97A0A"); AMBER_L=HexColor("#FFF3D0")
RED=HexColor("#C0392B"); RED_L=HexColor("#FEECEC")

# ── Themes ────────────────────────────────────────────────────────────────────
THEMES = {
    "k8s":    dict(p=HexColor("#326CE5"), d=HexColor("#1A4DB8"), m=HexColor("#5C8FEF"), l=HexColor("#D6E6FF"), name="Kubernetes", sub="Full Cluster Administration", badge="v1.35", accent_hex="#326CE5"),
    "compose":dict(p=HexColor("#0A5EB8"), d=HexColor("#064A91"), m=HexColor("#3A8FD4"), l=HexColor("#D6E9FA"), name="Docker Compose", sub="Multi-Container Applications", badge="v2.x", accent_hex="#0A5EB8"),
    "actions":dict(p=HexColor("#1F883D"), d=HexColor("#116329"), m=HexColor("#3DAB5C"), l=HexColor("#D4F5DC"), name="GitHub Actions", sub="CI/CD Pipelines", badge="2026", accent_hex="#1F883D"),
    "argocd": dict(p=HexColor("#EF7B4D"), d=HexColor("#B85C30"), m=HexColor("#F4A27A"), l=HexColor("#FDE8DC"), name="ArgoCD", sub="GitOps for Kubernetes", badge="v3.3.6", accent_hex="#EF7B4D"),
}

class ExoHeader(Flowable):
    def __init__(self, num, title, dur, diff, t):
        Flowable.__init__(self); self.num=num; self.title=title; self.dur=dur
        self.diff=diff; self.t=t; self.width=CW; self.height=48
    def draw(self):
        c=self.canv; w=self.width; t=self.t
        dm={"Easy":TEAL,"Intermediate":t['p'],"Advanced":AMBER}
        dc=dm.get(self.diff,t['p'])
        c.setFillColor(t['d']); c.rect(0,0,72,self.height,fill=1,stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold",9)
        c.drawCentredString(36,self.height-16,"EXERCISE")
        c.setFont("Helvetica-Bold",20); c.drawCentredString(36,8,self.num)
        c.setFillColor(t['p']); c.rect(72,0,w-72-80-80,self.height,fill=1,stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold",14)
        c.drawString(72+12,self.height/2-6,self.title)
        c.setFillColor(t['m']); c.rect(w-160,0,80,self.height,fill=1,stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold",10)
        c.drawCentredString(w-120,self.height/2+2,self.dur)
        c.setFont("Helvetica",8); c.drawCentredString(w-120,self.height/2-10,"duration")
        c.setFillColor(dc); c.rect(w-80,0,80,self.height,fill=1,stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold",10)
        c.drawCentredString(w-40,self.height/2+2,self.diff)
        c.setFont("Helvetica",8); c.drawCentredString(w-40,self.height/2-10,"level")

class CB(Flowable):
    def __init__(self, lines, t):
        Flowable.__init__(self); self.lines=lines; self.t=t; self.width=CW
        self.lh=14; self.px=12; self.py=10; self.height=len(lines)*self.lh+self.py*2
    def draw(self):
        c=self.canv
        c.setFillColor(CODEBG); c.roundRect(0,0,self.width,self.height,4,fill=1,stroke=0)
        c.setFillColor(self.t['m']); c.rect(0,0,3,self.height,fill=1,stroke=0)
        c.setFont("Courier",9)
        for i,line in enumerate(self.lines):
            y=self.height-self.py-(i+1)*self.lh+3
            c.setFillColor(GRAY if line.strip().startswith("#") else CODEFG)
            c.drawString(self.px+4,y,line)

class IB(Flowable):
    def __init__(self, kind, ttl, lines, t):
        Flowable.__init__(self); self.kind=kind; self.ttl=ttl
        self.raw=lines if isinstance(lines,list) else [lines]
        self.t=t; self.px=16; self.py=11; self.fs=9.5; self.lh=15
        self.mw=CW-self.px*2-6
        cfgs={"info":(t['l'],t['m'],t['p']),"warn":(AMBER_L,AMBER,AMBER),"tip":(TEAL_L,TEAL,TEAL),"question":(RED_L,RED,RED)}
        self.bg,self.border,self.tc=cfgs.get(kind,cfgs["info"])
        from reportlab.pdfbase.pdfmetrics import stringWidth
        self.dl=[]
        for raw in self.raw:
            words=raw.split(); cur=""
            for w in words:
                test=(cur+" "+w).strip()
                if stringWidth(test,"Helvetica",self.fs)<=self.mw: cur=test
                else:
                    if cur: self.dl.append(cur)
                    cur=w
            if cur: self.dl.append(cur)
        self.height=20+len(self.dl)*self.lh+self.py*2
    def draw(self):
        c=self.canv
        c.setFillColor(self.bg); c.roundRect(0,0,CW,self.height,5,fill=1,stroke=0)
        c.setStrokeColor(self.border); c.setLineWidth(1)
        c.roundRect(0,0,CW,self.height,5,fill=0,stroke=1)
        c.setFillColor(self.border); c.rect(0,0,4,self.height,fill=1,stroke=0)
        y=self.height-self.py-12
        c.setFillColor(self.tc); c.setFont("Helvetica-Bold",9.5)
        c.drawString(self.px+4,y,self.ttl.upper())
        y-=18; c.setFont("Helvetica",self.fs); c.setFillColor(INK)
        for line in self.dl:
            c.drawString(self.px+4,y,line); y-=self.lh

class MyDoc(SimpleDocTemplate):
    def __init__(self,*a,theme=None,**k):
        super().__init__(*a,**k); self.t=theme
    def afterPage(self):
        if self.page<=1: return
        t=self.t; c=self.canv; c.saveState()
        c.setStrokeColor(GRAY_M); c.setLineWidth(0.5)
        c.line(ML,H-36,W-MR,H-36)
        c.setFillColor(GRAY); c.setFont("Helvetica-Oblique",7.5)
        c.drawString(ML,H-29,f"{t['name']} Essential Training — {t['sub']}")
        c.setFillColor(t['p']); c.roundRect(W-MR-62,H-37,62,16,3,fill=1,stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold",7)
        c.drawCentredString(W-MR-31,H-29,t['name'].upper()[:12])
        c.setStrokeColor(GRAY_M); c.line(ML,32,W-MR,32)
        c.setFillColor(GRAY); c.setFont("Helvetica",8)
        if self.page%2==0: c.drawString(ML,22,str(self.page))
        else: c.drawRightString(W-MR,22,str(self.page))
        c.restoreState()

def draw_cover(c, t, topics, subtitle_lines, footer_right):
    c.setFillColor(INK); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(t['p']); c.rect(0,0,16,H,fill=1,stroke=0)
    c.setFillColor(t['m']); c.rect(16,H-8,W-16,8,fill=1,stroke=0)
    c.setFillColor(HexColor("#1A2A40"))
    for row in range(9):
        for col in range(11):
            cx=W-260+col*22; cy=H-55-row*22
            if 16<cx<W-10: c.circle(cx,cy,1.5,fill=1,stroke=0)
    c.setFillColor(t['p']); c.setFillAlpha(0.07)
    c.setFont("Helvetica-Bold",100); c.drawString(20,H//2-60,t['name'][:6])
    c.setFillAlpha(1.0)
    c.setFillColor(t['m']); c.setFont("Helvetica-Bold",8)
    c.drawString(34,H-46,"ESSENTIAL TRAINING SERIES")
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold",58); c.drawString(34,H-120,t['name'])
    c.setFillColor(t['m']); c.setFont("Helvetica-Bold",26)
    c.drawString(34,H-163,t['sub'])
    c.setFont("Helvetica-Bold",20)
    c.drawString(34,H-196,"Latest — "+t['badge'])
    c.setStrokeColor(t['m']); c.setLineWidth(2.5); c.line(34,H-214,300,H-214)
    c.setFillColor(HexColor("#94A3B8")); c.setFont("Helvetica",11)
    for i,sl in enumerate(subtitle_lines):
        c.drawString(34,H-234-i*18,sl)
    bstart=H-234-len(subtitle_lines)*18-20
    badges=[("8 Exercises",t['p']),("4 Hours",TEAL),("Intermediate",AMBER)]
    bx=34
    for label,col in badges:
        bw=len(label)*7.2+20
        c.setFillColor(HexColor("#1E1040")); c.roundRect(bx,bstart,bw,22,4,fill=1,stroke=0)
        c.setStrokeColor(col); c.setLineWidth(0.8); c.roundRect(bx,bstart,bw,22,4,fill=0,stroke=1)
        c.setFillColor(col); c.setFont("Helvetica-Bold",8); c.drawString(bx+10,bstart+9,label)
        bx+=bw+8
    box_h=len(topics)*30+36; box_y=bstart-18-box_h
    if box_y<108: box_y=108
    c.setFillColor(HexColor("#0D2137")); c.roundRect(34,box_y,W-68,box_h,6,fill=1,stroke=0)
    c.setFillColor(t['m']); c.setFont("Helvetica-Bold",8)
    c.drawString(52,box_y+box_h-20,"COURSE CONTENTS")
    c.setStrokeColor(HexColor("#1A3A5C")); c.setLineWidth(0.5)
    c.line(52,box_y+box_h-26,W-52,box_y+box_h-26)
    for i,(num,title) in enumerate(topics):
        y=box_y+box_h-50-i*30
        c.setFillColor(t['d']); c.roundRect(52,y+2,26,16,3,fill=1,stroke=0)
        c.setFillColor(t['l']); c.setFont("Helvetica-Bold",8); c.drawCentredString(65,y+8,num)
        c.setFillColor(HexColor("#CBD5E1")); c.setFont("Helvetica",11); c.drawString(88,y+6,title)
        if i<len(topics)-1:
            c.setStrokeColor(HexColor("#1A3A5C")); c.setLineWidth(0.3); c.line(52,y,W-52,y)
    c.setFillColor(t['p']); c.rect(0,0,W,46,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold",10)
    c.drawString(34,28,"Hands-on Lab — "+t['sub'])
    c.setFillColor(t['l']); c.setFont("Helvetica",8)
    c.drawRightString(W-34,16,footer_right)

def draw_back(c, t, skills, prereqs, stats, tagline, tagline2, footer_url):
    c.setFillColor(INK); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(t['p']); c.rect(W-16,0,16,H,fill=1,stroke=0)
    c.setFillColor(t['m']); c.rect(0,H-8,W-16,8,fill=1,stroke=0)
    c.setFillAlpha(0.04); c.setFillColor(WHITE); c.setFont("Helvetica-Bold",120)
    c.drawString(-10,H//2-60,t['name'][:6]); c.setFillAlpha(1.0)
    c.setFillColor(HexColor("#0D2137")); c.roundRect(34,H-340,W-84,290,8,fill=1,stroke=0)
    c.setFillColor(t['m']); c.setFont("Helvetica-Bold",10)
    c.drawString(52,H-76,"WHAT YOU WILL LEARN")
    c.setStrokeColor(t['m']); c.setLineWidth(1.5); c.line(52,H-85,228,H-85)
    for i,skill in enumerate(skills):
        y=H-115-i*26
        c.setFillColor(t['m']); c.circle(62,y+5,4,fill=1,stroke=0)
        c.setFillColor(HexColor("#CBD5E1")); c.setFont("Helvetica",9.5); c.drawString(76,y,skill)
    c.setFillColor(HexColor("#0D2137")); c.roundRect(34,H-430,W-84,72,8,fill=1,stroke=0)
    c.setFillColor(AMBER); c.setFont("Helvetica-Bold",9); c.drawString(52,H-374,"PREREQUISITES")
    c.setStrokeColor(AMBER); c.setLineWidth(0.8); c.line(52,H-383,165,H-383)
    for i,p in enumerate(prereqs):
        c.setFillColor(AMBER_L); c.setFont("Helvetica",9); c.drawString(52+i*155,H-402,"• "+p)
    sy=H-510
    for i,(val,label,col) in enumerate(stats):
        sx=52+i*150
        c.setFillColor(col); c.roundRect(sx,sy,130,70,8,fill=1,stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold",32); c.drawCentredString(sx+65,sy+42,val)
        c.setFillColor(t['l'] if col==t['p'] else WHITE)
        c.setFont("Helvetica",9); c.drawCentredString(sx+65,sy+24,label)
    c.setFillColor(HexColor("#1A2A40")); c.roundRect(34,90,W-84,80,6,fill=1,stroke=0)
    c.setFillColor(t['m']); c.setFont("Helvetica-Bold",10)
    c.drawCentredString(W//2-9,152,f'"{tagline}"')
    c.setFillColor(HexColor("#94A3B8")); c.setFont("Helvetica-Oblique",9)
    c.drawCentredString(W//2-9,133,tagline2)
    c.setFillColor(t['p']); c.rect(0,0,W-16,46,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold",10)
    c.drawString(34,28,t['name']+" Essential Training")
    c.setFillColor(t['l']); c.setFont("Helvetica",8); c.drawRightString(W-34,16,footer_url)

def S(name,**kw): return ParagraphStyle(name,**kw)
def make_styles(t):
    return dict(
        body=S('body',fontName='Helvetica',fontSize=10.5,leading=16,textColor=INK,spaceBefore=3,spaceAfter=3,alignment=TA_JUSTIFY),
        h1=S('h1',fontName='Helvetica-Bold',fontSize=20,leading=24,textColor=t['d'],spaceBefore=20,spaceAfter=8),
        h2=S('h2',fontName='Helvetica-Bold',fontSize=13.5,leading=17,textColor=INK,spaceBefore=14,spaceAfter=5),
        bt=S('bt',fontName='Helvetica',fontSize=10.5,leading=15,textColor=INK,leftIndent=18,spaceBefore=3,spaceAfter=3),
        nt=S('nt',fontName='Helvetica',fontSize=10.5,leading=15,textColor=INK,leftIndent=22,firstLineIndent=-14,spaceBefore=4,spaceAfter=4),
    )

def build_pdf(output, t, cover_args, back_args, content_fn):
    st=make_styles(t)
    def sp(h=6): return Spacer(1,h)
    def pb(): return PageBreak()
    def h1(txt): return KeepTogether([HRFlowable(width="100%",thickness=2.5,color=t['p'],spaceAfter=3),Paragraph(txt,st['h1']),HRFlowable(width="100%",thickness=0.5,color=GRAY_M,spaceBefore=2,spaceAfter=10)])
    def h2(txt): return Paragraph(txt,st['h2'])
    def body(txt): return Paragraph(txt,st['body'])
    def bullet(txt): return Paragraph(f'<font color="{t["accent_hex"]}">•</font>  {txt}',st['bt'])
    def num(n,txt): return Paragraph(f'<b>{n}.</b>  {txt}',st['nt'])
    def code(lines): return CB(lines,t)
    def info(txt): return IB("info","ℹ  Info",[txt],t)
    def warn(txt): return IB("warn","⚠  Warning",[txt],t)
    def tip(txt): return IB("tip","✓  Tip",[txt],t)
    def q(items): return IB("question","?  Questions",[f"{i+1}.  {x}" for i,x in enumerate(items)],t)
    def divider(): return [sp(20),HRFlowable(width="100%",thickness=1.5,color=t['m'],spaceBefore=10,spaceAfter=10)]
    def exo(n,title,dur,diff): return KeepTogether([ExoHeader(n,title,dur,diff,t),sp(12)])
    def tbl(headers,rows,widths):
        data=[headers]+rows; tab=Table(data,colWidths=widths)
        style=[('BACKGROUND',(0,0),(-1,0),t['p']),('TEXTCOLOR',(0,0),(-1,0),WHITE),
               ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
               ('ALIGN',(0,0),(-1,0),'CENTER'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),
               ('TEXTCOLOR',(0,1),(-1,-1),INK),('LEFTPADDING',(0,0),(-1,-1),8),
               ('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),
               ('BOTTOMPADDING',(0,0),(-1,-1),7),('GRID',(0,0),(-1,-1),0.4,GRAY_M),
               ('VALIGN',(0,0),(-1,-1),'MIDDLE')]
        for i in range(1,len(data)):
            if i%2==0: style.append(('BACKGROUND',(0,i),(-1,i),STRIPE))
        tab.setStyle(TableStyle(style)); return tab

    helpers=dict(sp=sp,pb=pb,h1=h1,h2=h2,body=body,bullet=bullet,num=num,
                 code=code,info=info,warn=warn,tip=tip,q=q,divider=divider,exo=exo,tbl=tbl)
    story=content_fn(helpers)

    cov=io.BytesIO()
    cv=canvas.Canvas(cov,pagesize=A4); draw_cover(cv,t,**cover_args); cv.showPage(); cv.save(); cov.seek(0)
    bak=io.BytesIO()
    bv=canvas.Canvas(bak,pagesize=A4); draw_back(bv,t,**back_args); bv.showPage(); bv.save(); bak.seek(0)
    inn=io.BytesIO()
    doc=MyDoc(inn,pagesize=A4,leftMargin=ML,rightMargin=MR,topMargin=MT,bottomMargin=MB,theme=t)
    doc.build(story); inn.seek(0)
    w=PdfWriter()
    for buf in [cov,inn,bak]:
        for pg in PdfReader(buf).pages: w.add_page(pg)
    w.add_metadata({"/Title":t['name']+" Essential Training"})
    with open(output,"wb") as f: w.write(f)
    print(f"✓ {output}")

# ═══════════════════════════════════════════════════════════════════════════════
# GUIDE 1 — Kubernetes (kubeadm)
# ═══════════════════════════════════════════════════════════════════════════════
def k8s_content(h):
    sp=h['sp']; pb=h['pb']; h1=h['h1']; h2=h['h2']; body=h['body']
    bullet=h['bullet']; num=h['num']; code=h['code']
    info=h['info']; warn=h['warn']; tip=h['tip']; q=h['q']
    divider=h['divider']; exo=h['exo']; tbl=h['tbl']
    s=[]
    s+=[h1("Introduction to Kubernetes"),sp(4)]
    s.append(body("Kubernetes (K8s) is the industry-standard container orchestration platform. While K3s is great for edge and development, production-grade clusters are often built with kubeadm — the official bootstrapping tool that gives you full control over every component. This guide covers K8s v1.35 with kubeadm on Ubuntu 22.04."))
    s+=[sp(10),h2("K8s vs K3s — when to use each"),sp(6)]
    s.append(tbl(["Feature","K3s","Kubernetes (kubeadm)"],[
        ["Use case","Edge, IoT, dev, homelab","Enterprise, cloud, full prod"],
        ["Control","Opinionated defaults","Full configuration control"],
        ["etcd","SQLite default","etcd required"],
        ["CRI","containerd","containerd or others"],
        ["Ingress","Traefik built-in","Install separately"],
        ["Overhead","~512 MB RAM","~2 GB RAM per node"],
        ["CNI","Flannel built-in","Choose your own (Calico, Cilium...)"],
    ],[150,150,199]))
    s+=[sp(12),h2("Control plane components"),sp(6)]
    s.append(tbl(["Component","Role","Port"],[
        ["kube-apiserver","REST API — heart of the cluster","6443/tcp"],
        ["etcd","Distributed key-value state store","2379-2380/tcp"],
        ["kube-scheduler","Assigns pods to nodes","—"],
        ["kube-controller-manager","Runs controllers (replica, node, job...)","—"],
        ["cloud-controller-manager","Cloud provider integration (optional)","—"],
    ],[170,250,79]))
    s.append(pb())

    s.append(exo("1","Cluster Bootstrap with kubeadm","45 min","Intermediate"))
    s+=[h2("1.1 — Prerequisites on all nodes"),sp(4),
    code(["# Disable swap (required by kubelet)",
          "sudo swapoff -a",
          "sudo sed -i '/ swap / s/^/#/' /etc/fstab",
          "",
          "# Enable kernel modules",
          "cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf",
          "overlay",
          "br_netfilter",
          "EOF",
          "sudo modprobe overlay && sudo modprobe br_netfilter",
          "",
          "# Sysctl settings",
          "cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf",
          "net.bridge.bridge-nf-call-iptables  = 1",
          "net.bridge.bridge-nf-call-ip6tables = 1",
          "net.ipv4.ip_forward                 = 1",
          "EOF",
          "sudo sysctl --system"]),
    sp(10),h2("1.2 — Install containerd + kubeadm"),sp(4),
    code(["# Install containerd",
          "sudo apt-get update && sudo apt-get install -y containerd.io",
          "sudo mkdir -p /etc/containerd",
          "containerd config default | sudo tee /etc/containerd/config.toml",
          "# Enable SystemdCgroup",
          "sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml",
          "sudo systemctl restart containerd",
          "",
          "# Install kubeadm, kubelet, kubectl (v1.35)",
          "curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key | \\",
          "  sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg",
          'echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] \\',
          "  https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /\" | \\",
          "  sudo tee /etc/apt/sources.list.d/kubernetes.list",
          "sudo apt-get update",
          "sudo apt-get install -y kubelet=1.35.* kubeadm=1.35.* kubectl=1.35.*",
          "sudo apt-mark hold kubelet kubeadm kubectl"]),
    sp(10),h2("1.3 — Initialize the control plane"),sp(4),
    code(["# On the master node only",
          "sudo kubeadm init \\",
          "  --pod-network-cidr=10.244.0.0/16 \\",
          "  --kubernetes-version=v1.35.3",
          "",
          "# Setup kubeconfig",
          "mkdir -p $HOME/.kube",
          "sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config",
          "sudo chown $(id -u):$(id -g) $HOME/.kube/config",
          "",
          "# Install Calico CNI",
          "kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml",
          "",
          "# Join worker nodes (use token from kubeadm init output)",
          "sudo kubeadm join <MASTER_IP>:6443 --token <TOKEN> \\",
          "  --discovery-token-ca-cert-hash sha256:<HASH>"]),
    sp(8),
    info("Save the 'kubeadm join' command from the init output! If you lose it, regenerate with: kubeadm token create --print-join-command"),
    sp(8),q(["What happens if you don't disable swap before running kubeadm?","What is the role of the CNI plugin and why isn't one included by default?","How do you generate a new bootstrap token to add nodes later?"])]
    s+=divider()

    s.append(exo("2","Namespaces & RBAC","30 min","Intermediate"))
    s+=[h2("2.1 — Namespaces"),sp(4),
    code(["# Create namespaces for environments",
          "kubectl create namespace development",
          "kubectl create namespace staging",
          "kubectl create namespace production",
          "",
          "# Set a default namespace for your session",
          "kubectl config set-context --current --namespace=development",
          "",
          "# List all resources in a namespace",
          "kubectl get all -n production"]),
    sp(10),h2("2.2 — RBAC — Role-Based Access Control"),sp(4),
    code(["# Create a Role (namespace-scoped)",
          "kubectl apply -f - <<EOF",
          "apiVersion: rbac.authorization.k8s.io/v1",
          "kind: Role",
          "metadata:",
          "  namespace: development",
          "  name: pod-reader",
          "rules:",
          "- apiGroups: ['']",
          "  resources: ['pods', 'pods/log']",
          "  verbs: ['get', 'list', 'watch']",
          "EOF",
          "",
          "# Bind the role to a user",
          "kubectl create rolebinding dev-reader \\",
          "  --role=pod-reader --user=alice -n development",
          "",
          "# Verify permissions",
          "kubectl auth can-i list pods --namespace=development --as=alice"]),
    sp(8),
    warn("Never grant cluster-admin to application service accounts. Follow the principle of least privilege — grant only the exact verbs and resources the workload needs."),
    sp(8),q(["What is the difference between a Role and a ClusterRole?","How do you check what permissions a service account has?","What is the default service account and what can it do?"])]
    s+=divider()

    s.append(exo("3","Deployments & Services","30 min","Easy"))
    s+=[h2("3.1 — Production-grade Deployment"),sp(4),
    code(["apiVersion: apps/v1",
          "kind: Deployment",
          "metadata:",
          "  name: api",
          "  namespace: production",
          "spec:",
          "  replicas: 3",
          "  strategy:",
          "    type: RollingUpdate",
          "    rollingUpdate:",
          "      maxSurge: 1",
          "      maxUnavailable: 0",
          "  selector:",
          "    matchLabels:",
          "      app: api",
          "  template:",
          "    metadata:",
          "      labels:",
          "        app: api",
          "    spec:",
          "      containers:",
          "      - name: api",
          "        image: myapp:1.0.0",
          "        ports:",
          "        - containerPort: 8080",
          "        resources:",
          "          requests: { cpu: 100m, memory: 128Mi }",
          "          limits:   { cpu: 500m, memory: 256Mi }",
          "        readinessProbe:",
          "          httpGet: { path: /health, port: 8080 }",
          "          initialDelaySeconds: 5",
          "          periodSeconds: 10",
          "        livenessProbe:",
          "          httpGet: { path: /health, port: 8080 }",
          "          initialDelaySeconds: 15"]),
    sp(8),tip("maxUnavailable: 0 ensures zero-downtime deployments — no pod is removed before a new one is Ready. Pair this with a proper readinessProbe to prevent routing traffic to unready pods."),
    sp(8),q(["What is the difference between a readinessProbe and a livenessProbe?","What happens during a RollingUpdate if maxSurge=1 and maxUnavailable=0?","How do you pause and resume a rollout?"])]
    s+=divider()

    s.append(exo("4","ConfigMaps, Secrets & Storage","30 min","Intermediate"))
    s+=[h2("4.1 — ConfigMap"),sp(4),
    code(["kubectl create configmap app-config \\",
          "  --from-literal=LOG_LEVEL=info \\",
          "  --from-file=config.yaml \\",
          "  -n production"]),
    sp(10),h2("4.2 — Secrets (external-secrets recommended)"),sp(4),
    code(["# Native secret (base64 encoded — not encrypted at rest by default!)",
          "kubectl create secret generic db-creds \\",
          "  --from-literal=username=admin \\",
          "  --from-literal=password=supersecret \\",
          "  -n production",
          "",
          "# Enable encryption at rest in kube-apiserver",
          "# /etc/kubernetes/manifests/kube-apiserver.yaml:",
          "# --encryption-provider-config=/etc/kubernetes/enc/config.yaml"]),
    sp(10),h2("4.3 — PersistentVolume with StorageClass"),sp(4),
    code(["apiVersion: storage.k8s.io/v1",
          "kind: StorageClass",
          "metadata:",
          "  name: fast-ssd",
          "provisioner: kubernetes.io/no-provisioner",
          "volumeBindingMode: WaitForFirstConsumer",
          "---",
          "apiVersion: v1",
          "kind: PersistentVolumeClaim",
          "metadata:",
          "  name: db-data",
          "  namespace: production",
          "spec:",
          "  storageClassName: fast-ssd",
          "  accessModes: [ReadWriteOnce]",
          "  resources:",
          "    requests:",
          "      storage: 20Gi"]),
    sp(8),warn("Kubernetes Secrets are base64-encoded, not encrypted. Enable EncryptionConfiguration at rest, or use Sealed Secrets / External Secrets Operator in production."),
    sp(8),q(["How do you enable encryption at rest for Secrets in kubeadm clusters?","What is the difference between ReadWriteOnce, ReadOnlyMany and ReadWriteMany?","What does WaitForFirstConsumer volumeBindingMode do?"])]
    s+=divider()

    s.append(exo("5","Ingress & Network Policies","30 min","Intermediate"))
    s+=[h2("5.1 — Install NGINX Ingress Controller"),sp(4),
    code(["kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.0/deploy/static/provider/baremetal/deploy.yaml",
          "",
          "# Verify",
          "kubectl get pods -n ingress-nginx",
          "kubectl get svc -n ingress-nginx"]),
    sp(10),h2("5.2 — Ingress resource"),sp(4),
    code(["apiVersion: networking.k8s.io/v1",
          "kind: Ingress",
          "metadata:",
          "  name: api-ingress",
          "  namespace: production",
          "  annotations:",
          "    nginx.ingress.kubernetes.io/rewrite-target: /",
          "spec:",
          "  ingressClassName: nginx",
          "  rules:",
          "  - host: api.example.com",
          "    http:",
          "      paths:",
          "      - path: /",
          "        pathType: Prefix",
          "        backend:",
          "          service:",
          "            name: api",
          "            port:",
          "              number: 8080"]),
    sp(10),h2("5.3 — Network Policy (default deny)"),sp(4),
    code(["# Deny all ingress by default in a namespace",
          "apiVersion: networking.k8s.io/v1",
          "kind: NetworkPolicy",
          "metadata:",
          "  name: default-deny-ingress",
          "  namespace: production",
          "spec:",
          "  podSelector: {}",
          "  policyTypes: [Ingress]"]),
    sp(8),tip("Start with a default-deny NetworkPolicy and add explicit allow rules. This is the zero-trust approach — no pod can receive traffic unless explicitly permitted."),
    sp(8),q(["What is the difference between Ingress and a LoadBalancer service?","Do NetworkPolicies work without a CNI that supports them?","How do you allow traffic between two specific namespaces?"])]
    s+=divider()

    s.append(exo("6","Horizontal Pod Autoscaler","20 min","Intermediate"))
    s+=[h2("6.1 — Install Metrics Server"),sp(4),
    code(["kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml",
          "",
          "# Verify (wait ~1 min)",
          "kubectl top nodes",
          "kubectl top pods -n production"]),
    sp(10),h2("6.2 — Create an HPA"),sp(4),
    code(["# HPA based on CPU",
          "kubectl autoscale deployment api \\",
          "  --cpu-percent=70 \\",
          "  --min=2 --max=10 \\",
          "  -n production",
          "",
          "# Or declaratively",
          "apiVersion: autoscaling/v2",
          "kind: HorizontalPodAutoscaler",
          "metadata:",
          "  name: api-hpa",
          "  namespace: production",
          "spec:",
          "  scaleTargetRef:",
          "    apiVersion: apps/v1",
          "    kind: Deployment",
          "    name: api",
          "  minReplicas: 2",
          "  maxReplicas: 10",
          "  metrics:",
          "  - type: Resource",
          "    resource:",
          "      name: cpu",
          "      target:",
          "        type: Utilization",
          "        averageUtilization: 70",
          "",
          "kubectl get hpa -n production -w"]),
    sp(8),info("HPA requires resource requests to be set on the container. Without requests, the HPA cannot calculate utilization percentage and will not scale."),
    sp(8),q(["What metrics can HPA scale on besides CPU?","What is the difference between HPA and VPA (Vertical Pod Autoscaler)?","How do you test HPA scaling manually?"])]
    s+=divider()

    s.append(exo("7","Cluster Upgrades","30 min","Advanced"))
    s+=[h2("7.1 — Upgrade the control plane"),sp(4),
    code(["# Check available versions",
          "apt-cache madison kubeadm | head -5",
          "",
          "# Upgrade kubeadm first",
          "sudo apt-get update",
          "sudo apt-get install -y kubeadm=1.35.*",
          "",
          "# Verify upgrade plan",
          "sudo kubeadm upgrade plan",
          "",
          "# Apply the upgrade",
          "sudo kubeadm upgrade apply v1.35.3",
          "",
          "# Upgrade kubelet and kubectl on the master",
          "sudo apt-get install -y kubelet=1.35.* kubectl=1.35.*",
          "sudo systemctl daemon-reload && sudo systemctl restart kubelet"]),
    sp(10),h2("7.2 — Upgrade worker nodes (one at a time)"),sp(4),
    code(["# Drain the node (evicts pods gracefully)",
          "kubectl drain node-1 --ignore-daemonsets --delete-emptydir-data",
          "",
          "# On the worker node: upgrade kubeadm, kubelet, kubectl",
          "sudo apt-get install -y kubeadm=1.35.* kubelet=1.35.* kubectl=1.35.*",
          "sudo kubeadm upgrade node",
          "sudo systemctl daemon-reload && sudo systemctl restart kubelet",
          "",
          "# Back on master: uncordon the node",
          "kubectl uncordon node-1"]),
    sp(8),warn("Never skip minor versions during upgrades. Go v1.33 -> v1.34 -> v1.35. Skipping versions is unsupported and can corrupt the cluster state."),
    sp(8),q(["What does 'kubectl drain' do to DaemonSet pods?","What is the difference between 'kubeadm upgrade apply' and 'kubeadm upgrade node'?","How do you verify a node upgraded successfully?"])]
    s+=divider()

    s.append(exo("8","Troubleshooting & Production Tips","30 min","Advanced"))
    s+=[h2("8.1 — Cluster health checks"),sp(4),
    code(["# Component status",
          "kubectl get componentstatuses",
          "kubectl get nodes -o wide",
          "",
          "# etcd health",
          "sudo etcdctl --cacert /etc/kubernetes/pki/etcd/ca.crt \\",
          "  --cert /etc/kubernetes/pki/etcd/healthcheck-client.crt \\",
          "  --key /etc/kubernetes/pki/etcd/healthcheck-client.key \\",
          "  endpoint health",
          "",
          "# API server logs",
          "sudo journalctl -u kubelet -f",
          "kubectl logs -n kube-system kube-apiserver-<node>"]),
    sp(10),h2("8.2 — etcd backup & restore"),sp(4),
    code(["# Backup etcd",
          "ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%Y%m%d).db \\",
          "  --cacert=/etc/kubernetes/pki/etcd/ca.crt \\",
          "  --cert=/etc/kubernetes/pki/etcd/server.crt \\",
          "  --key=/etc/kubernetes/pki/etcd/server.key",
          "",
          "# Verify snapshot",
          "ETCDCTL_API=3 etcdctl snapshot status /backup/etcd-$(date +%Y%m%d).db"]),
    sp(8),tip("Automate etcd backups with a CronJob. Store snapshots in object storage (S3, GCS). Test restore procedures regularly — a backup you never tested is not a backup."),
    sp(8),q(["How do you check why a pod is stuck in Pending?","What does it mean when a node shows NotReady?","How do you restore an etcd snapshot?"])]
    s.append(pb())

    s+=[h1("Appendix — Quick Reference"),sp(6),h2("Essential kubectl commands"),sp(6)]
    s.append(tbl(["Command","Description"],[
        ["kubectl get pods -A","All pods in all namespaces"],
        ["kubectl describe node <n>","Node details, conditions, capacity"],
        ["kubectl drain <node>","Evict pods before maintenance"],
        ["kubectl uncordon <node>","Re-enable scheduling on a node"],
        ["kubectl top nodes","CPU / RAM per node"],
        ["kubectl auth can-i <verb> <res>","Check your own permissions"],
        ["kubectl rollout history deploy/<n>","Show deployment revisions"],
        ["kubectl rollout undo deploy/<n>","Revert to previous revision"],
        ["kubectl apply --dry-run=server -f f.yaml","Server-side validation"],
        ["kubectl diff -f file.yaml","Show what would change"],
    ],[220,279]))
    s+=[sp(14),info("Official docs: https://kubernetes.io/docs  |  kubeadm: https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/")]
    return s

build_pdf("/mnt/user-data/outputs/Kubernetes_Essential_Training.pdf",
    THEMES["k8s"],
    dict(topics=[("01","Cluster Bootstrap with kubeadm"),("02","Namespaces & RBAC"),("03","Deployments & Services"),("04","ConfigMaps, Secrets & Storage"),("05","Ingress & Network Policies"),("06","Horizontal Pod Autoscaler"),("07","Cluster Upgrades"),("08","Troubleshooting & Production")],
         subtitle_lines=["kubeadm · RBAC · Networking · Storage · HPA · Upgrades"],
         footer_right="Kubernetes v1.35 | kubeadm | Calico CNI"),
    dict(skills=["Bootstrap a production cluster with kubeadm on Ubuntu","Configure RBAC roles, bindings and service accounts","Deploy apps with zero-downtime rolling update strategy","Manage Namespaces, ConfigMaps, Secrets and PVCs","Install NGINX Ingress and configure Network Policies","Set up Horizontal Pod Autoscaler with metrics-server","Perform safe in-place cluster upgrades without downtime","Backup and restore etcd for disaster recovery"],
         prereqs=["Linux & networking","kubectl basics","Docker/containers"],
         stats=[("4h","Duration",THEMES["k8s"]['p']),("8","Exercises",TEAL),("v1.35","K8s",AMBER)],
         tagline="Full control. Full power. Full Kubernetes.",
         tagline2="Kubernetes — The production-grade orchestration platform",
         footer_url="https://kubernetes.io/docs"),
    k8s_content)

# ═══════════════════════════════════════════════════════════════════════════════
# GUIDE 2 — Docker Compose
# ═══════════════════════════════════════════════════════════════════════════════
def compose_content(h):
    sp=h['sp']; pb=h['pb']; h1=h['h1']; h2=h['h2']; body=h['body']
    bullet=h['bullet']; num=h['num']; code=h['code']
    info=h['info']; warn=h['warn']; tip=h['tip']; q=h['q']
    divider=h['divider']; exo=h['exo']; tbl=h['tbl']
    s=[]
    s+=[h1("Introduction to Docker Compose"),sp(4)]
    s.append(body("Docker Compose is the tool for defining and running multi-container applications. With a single compose.yaml file you describe your entire stack — services, networks, volumes, and environment — and bring it up with one command. The Compose plugin (v2) ships with Docker Engine v29 and replaces the legacy standalone docker-compose binary."))
    s+=[sp(10),h2("Compose v1 vs v2"),sp(6)]
    s.append(tbl(["Aspect","Compose v1 (legacy)","Compose v2 (current)"],[
        ["Binary","docker-compose (Python)","docker compose (Go plugin)"],
        ["Install","Separate pip install","Bundled with Docker Engine v29"],
        ["Command","docker-compose up","docker compose up"],
        ["File name","docker-compose.yml","compose.yaml (preferred)"],
        ["Speed","Slower startup","Significantly faster"],
        ["Profile support","Limited","Full --profile support"],
        ["Status","End of life (July 2023)","Active, use this"],
    ],[150,170,179]))
    s+=[sp(12),h2("Core concepts"),sp(6)]
    s.append(tbl(["Concept","Description"],[
        ["Service","A container definition — image, ports, env, volumes"],
        ["Network","Virtual network connecting services (automatic by default)"],
        ["Volume","Persistent storage attached to one or more services"],
        ["Profile","Named group of services — activate with --profile"],
        ["Dependency","depends_on controls startup order between services"],
        ["Health check","Condition to wait for before starting dependent services"],
        ["Override","compose.override.yaml merges automatically for dev/prod split"],
    ],[120,379]))
    s.append(pb())

    s.append(exo("1","Your First Stack","20 min","Easy"))
    s+=[h2("1.1 — A minimal compose.yaml"),sp(4),
    code(["# compose.yaml",
          "services:",
          "  web:",
          "    image: nginx:1.27-alpine",
          "    ports:",
          "      - '8080:80'",
          "    volumes:",
          "      - ./html:/usr/share/nginx/html:ro",
          "",
          "  db:",
          "    image: postgres:17-alpine",
          "    environment:",
          "      POSTGRES_PASSWORD: secret",
          "      POSTGRES_DB: myapp",
          "    volumes:",
          "      - pgdata:/var/lib/postgresql/data",
          "",
          "volumes:",
          "  pgdata:"]),
    sp(8),
    code(["docker compose up -d       # Start detached",
          "docker compose ps          # Check status",
          "docker compose logs -f     # Stream all logs",
          "docker compose down        # Stop & remove containers"]),
    sp(8),info("Compose automatically creates a network named <project>_default and connects all services to it. Services can reach each other by service name — 'web' can connect to 'db' on port 5432."),
    sp(8),q(["How does Compose determine the project name?","What is the difference between 'docker compose stop' and 'docker compose down'?","How do you run a one-off command in a service container?"])]
    s+=divider()

    s.append(exo("2","Build & Development Workflow","30 min","Easy"))
    s+=[h2("2.1 — Build from Dockerfile"),sp(4),
    code(["services:",
          "  api:",
          "    build:",
          "      context: ./api",
          "      dockerfile: Dockerfile",
          "      args:",
          "        NODE_ENV: development",
          "    ports:",
          "      - '3000:3000'",
          "    volumes:",
          "      - ./api:/app         # bind mount for live reload",
          "      - /app/node_modules  # anonymous volume — keep container's node_modules",
          "    environment:",
          "      NODE_ENV: development",
          "    command: npm run dev"]),
    sp(8),
    code(["# Build and start",
          "docker compose up --build",
          "",
          "# Rebuild a specific service only",
          "docker compose build api",
          "",
          "# Build without cache",
          "docker compose build --no-cache api"]),
    sp(10),h2("2.2 — Dev vs prod split with override files"),sp(4),
    code(["# compose.yaml — base (shared between envs)",
          "services:",
          "  api:",
          "    image: myregistry/api:${TAG:-latest}",
          "    environment:",
          "      DB_HOST: db",
          "",
          "# compose.override.yaml — auto-loaded in dev",
          "services:",
          "  api:",
          "    build: ./api",
          "    volumes:",
          "      - ./api:/app",
          "    environment:",
          "      NODE_ENV: development",
          "",
          "# compose.prod.yaml — explicit in prod",
          "# docker compose -f compose.yaml -f compose.prod.yaml up -d"]),
    sp(8),tip("The compose.override.yaml file is loaded automatically when you run 'docker compose up'. This makes it perfect for local dev overrides without modifying the base file that goes to production."),
    sp(8),q(["What is the order of precedence for environment variables in Compose?","How do anonymous volumes (- /app/node_modules) work?","How do you pass a .env file to Docker Compose?"])]
    s+=divider()

    s.append(exo("3","Networks & Service Discovery","25 min","Intermediate"))
    s+=[h2("3.1 — Custom networks"),sp(4),
    code(["services:",
          "  api:",
          "    networks: [frontend, backend]",
          "",
          "  db:",
          "    networks: [backend]         # not reachable from frontend!",
          "",
          "  nginx:",
          "    networks: [frontend]",
          "    ports:",
          "      - '80:80'",
          "",
          "networks:",
          "  frontend:",
          "  backend:",
          "    internal: true              # no external internet access"]),
    sp(8),info("'internal: true' on a network prevents containers from reaching the internet — perfect for database networks that should never have outbound access."),
    sp(8),q(["Can a container be on multiple networks simultaneously?","How do you give a service a custom hostname on the network?","What does 'network_mode: host' do and when would you use it?"])]
    s+=divider()

    s.append(exo("4","Volumes & Data Management","25 min","Intermediate"))
    s+=[h2("4.1 — Volume types"),sp(4),
    tbl(["Type","Syntax","Best for"],[
        ["Named volume","- pgdata:/var/lib/postgresql/data","Databases, persistent app data"],
        ["Bind mount","- ./src:/app","Source code, config files in dev"],
        ["Anonymous volume","- /app/node_modules","Temp data, overriding bind mounts"],
        ["tmpfs","tmpfs: /tmp","Secrets, temp files (memory only)"],
    ],[120,210,169]),
    sp(10),
    code(["services:",
          "  db:",
          "    image: postgres:17-alpine",
          "    volumes:",
          "      - pgdata:/var/lib/postgresql/data",
          "    tmpfs:",
          "      - /tmp",
          "",
          "volumes:",
          "  pgdata:",
          "    driver: local",
          "    driver_opts:",
          "      type: none",
          "      o: bind",
          "      device: /mnt/ssd/pgdata   # store on fast SSD"]),
    sp(8),
    code(["# Inspect a volume",
          "docker volume inspect myproject_pgdata",
          "",
          "# Backup a volume",
          "docker run --rm -v myproject_pgdata:/data -v $(pwd):/backup \\",
          "  alpine tar czf /backup/pgdata-backup.tar.gz /data"]),
    sp(8),q(["How do you share a volume between multiple services?","What happens to named volumes when you run 'docker compose down'?","How do you migrate data from one volume to another?"])]
    s+=divider()

    s.append(exo("5","Health Checks & Dependency Order","25 min","Intermediate"))
    s+=[h2("5.1 — Health checks and service_healthy"),sp(4),
    code(["services:",
          "  db:",
          "    image: postgres:17-alpine",
          "    environment:",
          "      POSTGRES_PASSWORD: secret",
          "    healthcheck:",
          "      test: ['CMD-SHELL', 'pg_isready -U postgres']",
          "      interval: 10s",
          "      timeout: 5s",
          "      retries: 5",
          "      start_period: 30s",
          "",
          "  api:",
          "    build: ./api",
          "    depends_on:",
          "      db:",
          "        condition: service_healthy   # wait for DB to be ready!",
          "      redis:",
          "        condition: service_started   # just wait for container start"]),
    sp(8),warn("Without 'condition: service_healthy', depends_on only waits for the container to start — not for the service inside to be ready. Always use service_healthy for databases."),
    sp(8),q(["What are the four conditions available in depends_on?","What is the 'start_period' option in a healthcheck?","How do you check the health status of a service?"])]
    s+=divider()

    s.append(exo("6","Profiles & Environment Management","25 min","Intermediate"))
    s+=[h2("6.1 — Profiles for optional services"),sp(4),
    code(["services:",
          "  api:",
          "    build: ./api        # always started",
          "",
          "  db:",
          "    image: postgres:17-alpine",
          "    profiles: [backend]  # only when --profile backend",
          "",
          "  adminer:",
          "    image: adminer",
          "    profiles: [tools]   # only when --profile tools",
          "    ports:",
          "      - '8081:8080'",
          "",
          "# Start core + backend only",
          "# docker compose --profile backend up -d",
          "",
          "# Start everything",
          "# docker compose --profile backend --profile tools up -d"]),
    sp(10),h2("6.2 — Environment variables and .env"),sp(4),
    code(["# .env file (auto-loaded)",
          "POSTGRES_PASSWORD=mypassword",
          "API_IMAGE_TAG=1.2.0",
          "NODE_ENV=production",
          "",
          "# compose.yaml references .env variables",
          "services:",
          "  api:",
          "    image: myapi:${API_IMAGE_TAG}",
          "    environment:",
          "      - NODE_ENV=${NODE_ENV}",
          "      - DB_PASS=${POSTGRES_PASSWORD}"]),
    sp(8),tip("Never commit .env files with real secrets to Git. Add .env to .gitignore and provide a .env.example with placeholder values for documentation."),
    sp(8),q(["How do you use different .env files for different environments?","What is the difference between 'environment' and 'env_file' in a service?","How do you prevent a variable from being expanded in compose.yaml?"])]
    s+=divider()

    s.append(exo("7","Scaling & Production Deployment","30 min","Advanced"))
    s+=[h2("7.1 — Scale services"),sp(4),
    code(["# Scale api to 3 replicas",
          "docker compose up -d --scale api=3",
          "",
          "# Note: scaled services cannot have fixed port mappings",
          "# Use a load balancer service instead:",
          "services:",
          "  api:",
          "    build: ./api",
          "    # No 'ports' here — accessed via nginx",
          "    deploy:",
          "      replicas: 3",
          "      resources:",
          "        limits:",
          "          cpus: '0.5'",
          "          memory: 256M",
          "",
          "  nginx:",
          "    image: nginx:1.27-alpine",
          "    ports:",
          "      - '80:80'",
          "    depends_on: [api]"]),
    sp(10),h2("7.2 — Production checklist"),sp(4)]
    for t in ["Use specific image tags — never :latest in production","Set memory and CPU limits on every service","Use healthchecks with service_healthy in depends_on","Store secrets in a secrets manager, not compose.yaml","Use --env-file for environment-specific config","Enable restart: unless-stopped for all services","Use named volumes, never bind mounts for prod data"]:
        s.append(bullet(t))
    s+=[sp(8),q(["How do you do zero-downtime deployments with Compose?","What is the difference between 'restart: always' and 'restart: unless-stopped'?","How do you use Docker secrets in Compose (Swarm mode)?"])]
    s+=divider()

    s.append(exo("8","Monitoring & Debugging","20 min","Easy"))
    s+=[h2("8.1 — Essential Compose commands"),sp(4),
    code(["docker compose ps                    # Status of all services",
          "docker compose logs -f api           # Stream logs from api",
          "docker compose logs --tail=50 db     # Last 50 lines from db",
          "docker compose exec api sh           # Shell in running api container",
          "docker compose run --rm api pytest   # One-off command",
          "docker compose top                   # Running processes in containers",
          "docker compose events                # Live event stream",
          "docker compose config                # Print merged config (debug)",
          "docker compose images                # Images used by services"]),
    sp(8),info("'docker compose config' is invaluable for debugging — it shows the final merged configuration after all overrides and variable substitutions have been applied."),
    sp(8),q(["How do you restart a single service without affecting others?","How do you view the diff between running config and new config?","How do you force-recreate a container without stopping the whole stack?"])]
    s.append(pb())

    s+=[h1("Appendix — Quick Reference"),sp(6),h2("Essential Compose commands"),sp(6)]
    s.append(tbl(["Command","Description"],[
        ["docker compose up -d","Start all services detached"],
        ["docker compose up --build","Rebuild images before starting"],
        ["docker compose down","Stop and remove containers + networks"],
        ["docker compose down -v","Also remove named volumes"],
        ["docker compose ps","Service status"],
        ["docker compose logs -f <svc>","Stream service logs"],
        ["docker compose exec <svc> sh","Open shell in running service"],
        ["docker compose run --rm <svc> cmd","Run one-off command"],
        ["docker compose --profile X up","Start with optional profile X"],
        ["docker compose config","Show merged final configuration"],
        ["docker compose pull","Pull latest images for all services"],
        ["docker compose restart <svc>","Restart a specific service"],
    ],[210,289]))
    s+=[sp(14),info("Official docs: https://docs.docker.com/compose  |  Compose Spec: https://compose-spec.io")]
    return s

build_pdf("/mnt/user-data/outputs/DockerCompose_Essential_Training.pdf",
    THEMES["compose"],
    dict(topics=[("01","Your First Stack"),("02","Build & Dev Workflow"),("03","Networks & Service Discovery"),("04","Volumes & Data Management"),("05","Health Checks & Dependencies"),("06","Profiles & Environment Mgmt"),("07","Scaling & Production"),("08","Monitoring & Debugging")],
         subtitle_lines=["Services · Networks · Volumes · Profiles · Production"],
         footer_right="Docker Compose v2 | Docker Engine v29"),
    dict(skills=["Write compose.yaml to define multi-container stacks","Build images and mount source for live reload in dev","Set up isolated frontend/backend networks","Manage named volumes, bind mounts and backups","Use healthchecks to guarantee correct startup order","Split dev/prod config with override files and profiles","Scale services and set resource limits for production","Debug stacks with logs, exec and compose config"],
         prereqs=["Docker basics","Command line","Basic networking"],
         stats=[("4h","Duration",THEMES["compose"]['p']),("8","Exercises",TEAL),("v2","Compose",AMBER)],
         tagline="One file. Your entire stack. One command.",
         tagline2="Docker Compose — Multi-container apps made simple",
         footer_url="https://docs.docker.com/compose"),
    compose_content)

# ═══════════════════════════════════════════════════════════════════════════════
# GUIDE 3 — GitHub Actions
# ═══════════════════════════════════════════════════════════════════════════════
def actions_content(h):
    sp=h['sp']; pb=h['pb']; h1=h['h1']; h2=h['h2']; body=h['body']
    bullet=h['bullet']; num=h['num']; code=h['code']
    info=h['info']; warn=h['warn']; tip=h['tip']; q=h['q']
    divider=h['divider']; exo=h['exo']; tbl=h['tbl']
    s=[]
    s+=[h1("Introduction to GitHub Actions"),sp(4)]
    s.append(body("GitHub Actions is GitHub's built-in CI/CD platform, running 71 million jobs per day in 2026. Workflows are YAML files in .github/workflows/ that trigger on events (push, PR, schedule) and run jobs on GitHub-hosted or self-hosted runners. The 2026 security roadmap introduces dependency locking, egress firewalls and centralized policy controls."))
    s+=[sp(10),h2("Key concepts"),sp(6)]
    s.append(tbl(["Concept","Description"],[
        ["Workflow","A YAML file in .github/workflows/ — defines automation"],
        ["Event","Trigger for a workflow (push, pull_request, schedule, workflow_dispatch...)"],
        ["Job","A group of steps running on the same runner"],
        ["Step","An individual task — shell command or Action"],
        ["Action","A reusable unit of automation (from Marketplace or your repo)"],
        ["Runner","The machine that executes jobs (ubuntu-latest, macos-26, windows-2025)"],
        ["Secret","Encrypted variable stored in repo/org settings"],
        ["Environment","Named deployment target with protection rules and secrets"],
        ["Matrix","Run the same job with multiple combinations of variables"],
        ["Artifact","Files produced by a job and shared between jobs or downloaded"],
    ],[120,379]))
    s.append(pb())

    s.append(exo("1","Your First Workflow","20 min","Easy"))
    s+=[h2("1.1 — Hello World workflow"),sp(4),
    code(["# .github/workflows/hello.yaml",
          "name: Hello World",
          "",
          "on:",
          "  push:",
          "    branches: [main]",
          "  pull_request:",
          "    branches: [main]",
          "  workflow_dispatch:   # manual trigger button in GitHub UI",
          "",
          "jobs:",
          "  greet:",
          "    runs-on: ubuntu-latest",
          "    steps:",
          "      - name: Checkout code",
          "        uses: actions/checkout@v4",
          "",
          "      - name: Say hello",
          "        run: echo 'Hello from GitHub Actions 2026!'",
          "",
          "      - name: Show runner info",
          "        run: |",
          "          echo 'OS: ${{ runner.os }}'",
          "          echo 'Workspace: ${{ github.workspace }}'",
          "          docker --version"]),
    sp(8),info("ubuntu-latest maps to Ubuntu 24.04 in 2026. Always pin to a specific version (ubuntu-24.04) in production workflows to avoid unexpected runner image changes breaking your builds."),
    sp(8),q(["What is the difference between 'uses' and 'run' in a step?","What events can trigger a GitHub Actions workflow?","How do you manually trigger a workflow from the GitHub UI?"])]
    s+=divider()

    s.append(exo("2","CI — Build, Test & Lint","30 min","Easy"))
    s+=[h2("2.1 — Node.js CI pipeline"),sp(4),
    code(["name: CI",
          "",
          "on:",
          "  push:",
          "    branches: [main, develop]",
          "  pull_request:",
          "    branches: [main]",
          "",
          "jobs:",
          "  lint-and-test:",
          "    runs-on: ubuntu-24.04",
          "    strategy:",
          "      matrix:",
          "        node-version: ['20', '22']  # test on 2 versions",
          "",
          "    steps:",
          "      - uses: actions/checkout@v4",
          "",
          "      - name: Setup Node.js ${{ matrix.node-version }}",
          "        uses: actions/setup-node@v4",
          "        with:",
          "          node-version: ${{ matrix.node-version }}",
          "          cache: npm",
          "",
          "      - name: Install dependencies",
          "        run: npm ci",
          "",
          "      - name: Lint",
          "        run: npm run lint",
          "",
          "      - name: Run tests",
          "        run: npm test -- --coverage",
          "",
          "      - name: Upload coverage",
          "        uses: actions/upload-artifact@v4",
          "        with:",
          "          name: coverage-node${{ matrix.node-version }}",
          "          path: coverage/"]),
    sp(8),tip("Use 'npm ci' instead of 'npm install' in CI — it installs exactly what's in package-lock.json, is faster, and fails if the lock file is out of sync."),
    sp(8),q(["What does the matrix strategy do and how many jobs does the example create?","What is the difference between upload-artifact and cache in Actions?","How do you skip CI for a commit (e.g. docs-only changes)?"])]
    s+=divider()

    s.append(exo("3","Docker Build & Push","30 min","Intermediate"))
    s+=[h2("3.1 — Build and push to GHCR"),sp(4),
    code(["name: Build & Push Image",
          "",
          "on:",
          "  push:",
          "    branches: [main]",
          "    tags: ['v*.*.*']",
          "",
          "env:",
          "  REGISTRY: ghcr.io",
          "  IMAGE_NAME: ${{ github.repository }}",
          "",
          "jobs:",
          "  build:",
          "    runs-on: ubuntu-24.04",
          "    permissions:",
          "      contents: read",
          "      packages: write",
          "",
          "    steps:",
          "      - uses: actions/checkout@v4",
          "",
          "      - name: Log in to GHCR",
          "        uses: docker/login-action@v3",
          "        with:",
          "          registry: ${{ env.REGISTRY }}",
          "          username: ${{ github.actor }}",
          "          password: ${{ secrets.GITHUB_TOKEN }}",
          "",
          "      - name: Extract metadata",
          "        id: meta",
          "        uses: docker/metadata-action@v5",
          "        with:",
          "          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}",
          "          tags: |",
          "            type=semver,pattern={{version}}",
          "            type=sha,prefix=sha-",
          "",
          "      - name: Set up BuildKit",
          "        uses: docker/setup-buildx-action@v3",
          "",
          "      - name: Build and push",
          "        uses: docker/build-push-action@v6",
          "        with:",
          "          context: .",
          "          push: true",
          "          tags: ${{ steps.meta.outputs.tags }}",
          "          cache-from: type=gha",
          "          cache-to: type=gha,mode=max"]),
    sp(8),warn("Always pin Actions to a commit SHA in production (e.g. actions/checkout@11bd71901...) not a tag. Tags are mutable — this is the #1 supply chain attack vector in CI/CD."),
    sp(8),q(["What does 'cache-from: type=gha' do?","Why does the job need 'packages: write' permission?","How do you build multi-platform images (amd64 + arm64) in Actions?"])]
    s+=divider()

    s.append(exo("4","Secrets & Environments","25 min","Intermediate"))
    s+=[h2("4.1 — Using secrets securely"),sp(4),
    code(["# Set secrets in: Settings > Secrets and variables > Actions",
          "",
          "jobs:",
          "  deploy:",
          "    runs-on: ubuntu-24.04",
          "    environment: production  # requires approval if configured",
          "",
          "    steps:",
          "      - name: Deploy with secret",
          "        env:",
          "          API_KEY: ${{ secrets.PROD_API_KEY }}",
          "          DB_URL:  ${{ secrets.PROD_DB_URL }}",
          "        run: |",
          "          echo 'Deploying...'",
          "          ./scripts/deploy.sh",
          "",
          "      # OIDC — no long-lived secrets needed!",
          "      - name: Configure AWS via OIDC",
          "        uses: aws-actions/configure-aws-credentials@v4",
          "        with:",
          "          role-to-assume: arn:aws:iam::123456789:role/GitHubActions",
          "          aws-region: eu-west-1"]),
    sp(8),info("OIDC (OpenID Connect) lets GitHub Actions authenticate to cloud providers (AWS, GCP, Azure) without storing long-lived credentials as secrets. This is the recommended approach in 2026."),
    sp(8),q(["What is the difference between repository secrets and environment secrets?","How do you prevent a secret from being printed in logs?","What is OIDC and why is it better than long-lived API keys?"])]
    s+=divider()

    s.append(exo("5","Reusable Workflows & Composite Actions","30 min","Intermediate"))
    s+=[h2("5.1 — Reusable workflow (called from other workflows)"),sp(4),
    code(["# .github/workflows/reusable-deploy.yaml",
          "name: Reusable Deploy",
          "",
          "on:",
          "  workflow_call:",
          "    inputs:",
          "      environment:",
          "        required: true",
          "        type: string",
          "      image-tag:",
          "        required: true",
          "        type: string",
          "    secrets:",
          "      KUBE_CONFIG:",
          "        required: true",
          "",
          "jobs:",
          "  deploy:",
          "    runs-on: ubuntu-24.04",
          "    environment: ${{ inputs.environment }}",
          "    steps:",
          "      - name: Deploy to K8s",
          "        env:",
          "          KUBECONFIG_DATA: ${{ secrets.KUBE_CONFIG }}",
          "        run: |",
          "          echo \"$KUBECONFIG_DATA\" | base64 -d > kubeconfig",
          "          kubectl set image deploy/api api=${{ inputs.image-tag }}"]),
    sp(8),
    code(["# Calling the reusable workflow",
          "jobs:",
          "  deploy-staging:",
          "    uses: ./.github/workflows/reusable-deploy.yaml",
          "    with:",
          "      environment: staging",
          "      image-tag: ghcr.io/myorg/api:sha-abc123",
          "    secrets:",
          "      KUBE_CONFIG: ${{ secrets.STAGING_KUBE_CONFIG }}"]),
    sp(8),tip("Reusable workflows are the best way to share CI/CD logic across repositories. They run as a separate job — unlike composite actions which run as steps in the calling job."),
    sp(8),q(["What is the difference between a reusable workflow and a composite action?","How do you pass outputs from a reusable workflow to the caller?","Can a reusable workflow call another reusable workflow?"])]
    s+=divider()

    s.append(exo("6","Full CI/CD Pipeline","35 min","Advanced"))
    s+=[h2("6.1 — End-to-end pipeline: test → build → deploy"),sp(4)]
    s.append(body("Part 1 — Test and Build jobs:"))
    s+=[sp(4),code(["name: Full CI/CD Pipeline",
          "on:",
          "  push:",
          "    branches: [main]",
          "",
          "jobs:",
          "  test:",
          "    runs-on: ubuntu-24.04",
          "    steps:",
          "      - uses: actions/checkout@v4",
          "      - uses: actions/setup-node@v4",
          "        with: { node-version: '22', cache: npm }",
          "      - run: npm ci && npm test",
          "",
          "  build:",
          "    needs: test",
          "    runs-on: ubuntu-24.04",
          "    outputs:",
          "      image-tag: ${{ steps.meta.outputs.version }}",
          "    steps:",
          "      - uses: actions/checkout@v4",
          "      - uses: docker/setup-buildx-action@v3",
          "      - uses: docker/login-action@v3",
          "        with:",
          "          registry: ghcr.io",
          "          username: ${{ github.actor }}",
          "          password: ${{ secrets.GITHUB_TOKEN }}",
          "      - id: meta",
          "        uses: docker/metadata-action@v5",
          "        with:",
          "          images: ghcr.io/${{ github.repository }}",
          "      - uses: docker/build-push-action@v6",
          "        with:",
          "          push: true",
          "          tags: ${{ steps.meta.outputs.tags }}",
          "          cache-from: type=gha",
          "          cache-to: type=gha,mode=max"]),
    sp(8)]
    s.append(body("Part 2 — Deploy jobs (staging then production with approval gate):"))
    s+=[sp(4),code(["  deploy-staging:",
          "    needs: build",
          "    uses: ./.github/workflows/reusable-deploy.yaml",
          "    with:",
          "      environment: staging",
          "      image-tag: ghcr.io/${{ github.repository }}:${{ needs.build.outputs.image-tag }}",
          "    secrets: inherit",
          "",
          "  deploy-production:",
          "    needs: deploy-staging",
          "    uses: ./.github/workflows/reusable-deploy.yaml",
          "    with:",
          "      environment: production    # requires manual approval!",
          "      image-tag: ghcr.io/${{ github.repository }}:${{ needs.build.outputs.image-tag }}",
          "    secrets: inherit"]),
    sp(8),q(["What does 'needs' do and how does it affect parallel execution?","How do you pass data between jobs using outputs?","How do you add a manual approval gate before the production deploy?"])]
    s+=divider()

    s.append(exo("7","Caching & Performance","20 min","Intermediate"))
    s+=[h2("7.1 — Dependency caching"),sp(4),
    code(["# Cache node_modules across runs",
          "- uses: actions/cache@v4",
          "  with:",
          "    path: ~/.npm",
          "    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}",
          "    restore-keys: |",
          "      ${{ runner.os }}-npm-",
          "",
          "# Built-in cache in setup actions (easier)",
          "- uses: actions/setup-node@v4",
          "  with:",
          "    node-version: '22'",
          "    cache: npm       # or: pip, gradle, maven"]),
    sp(8),tip("Use 'hashFiles' to key caches on lock files. When the lock file changes (new deps), the cache is busted automatically. This is faster than always running npm install from scratch."),
    sp(8),q(["What is the cache eviction policy in GitHub Actions?","How do you force-invalidate a cache?","What is the maximum cache size per repository?"])]
    s+=divider()

    s.append(exo("8","Security Best Practices (2026)","25 min","Advanced"))
    s+=[h2("8.1 — 2026 security hardening"),sp(4)]
    for t in ["Pin all Actions to commit SHAs, not tags (use Dependabot to update them)","Set 'permissions' explicitly on every job — default to read-only","Use OIDC for cloud auth — eliminate long-lived secrets entirely","Enable 'pull_request_target' with caution — it runs with write permissions","Add 'timeout-minutes' to every job to prevent runaway billing","Use environments with required reviewers for production deployments","Enable CodeQL scanning as a required status check on main"]:
        s.append(bullet(t))
    s+=[sp(8),code(["# Minimal permissions — principle of least privilege",
          "jobs:",
          "  build:",
          "    runs-on: ubuntu-24.04",
          "    permissions:",
          "      contents: read       # checkout only",
          "      packages: write      # push to GHCR",
          "      id-token: write      # OIDC token for cloud auth",
          "    timeout-minutes: 15"]),
    sp(8),warn("Never use 'permissions: write-all' in production workflows. Each job should declare only the permissions it actually needs — the 2026 security roadmap enforces this through policy controls."),
    sp(8),q(["What is the GITHUB_TOKEN and how does it differ from a PAT?","How do you prevent secrets from being exfiltrated via a compromised action?","What is the 'pull_request_target' event and why is it dangerous?"])]
    s.append(pb())

    s+=[h1("Appendix — Quick Reference"),sp(6),h2("Common workflow triggers"),sp(6)]
    s.append(tbl(["Trigger","Syntax","Use case"],[
        ["Push to branch","on: push: branches: [main]","CI on every commit"],
        ["Pull request","on: pull_request: branches: [main]","PR checks before merge"],
        ["Tag push","on: push: tags: ['v*.*.*']","Release pipeline on tag"],
        ["Manual","on: workflow_dispatch:","Deploy on demand"],
        ["Schedule","on: schedule: - cron: '0 2 * * *'","Nightly jobs (UTC)"],
        ["Another workflow","on: workflow_call:","Reusable workflow"],
        ["Release published","on: release: types: [published]","Publish to package registry"],
    ],[130,190,179]))
    s+=[sp(14),h2("Useful context variables"),sp(6)]
    s.append(tbl(["Variable","Description"],[
        ["github.sha","Full commit SHA of the trigger"],
        ["github.ref","Branch or tag ref (refs/heads/main)"],
        ["github.actor","Username that triggered the workflow"],
        ["github.repository","owner/repo"],
        ["github.event_name","Event that triggered the workflow"],
        ["runner.os","Runner OS (Linux, macOS, Windows)"],
        ["secrets.GITHUB_TOKEN","Auto-generated token for the repo"],
    ],[170,329]))
    s+=[sp(14),info("Official docs: https://docs.github.com/actions  |  Actions Marketplace: https://github.com/marketplace?type=actions")]
    return s

build_pdf("/mnt/user-data/outputs/GitHubActions_Essential_Training.pdf",
    THEMES["actions"],
    dict(topics=[("01","Your First Workflow"),("02","CI — Build, Test & Lint"),("03","Docker Build & Push"),("04","Secrets & Environments"),("05","Reusable Workflows"),("06","Full CI/CD Pipeline"),("07","Caching & Performance"),("08","Security Best Practices")],
         subtitle_lines=["Workflows · CI/CD · Docker · OIDC · Security 2026"],
         footer_right="GitHub Actions 2026 | ubuntu-24.04 runners"),
    dict(skills=["Write YAML workflows triggered by push, PR, schedule and dispatch","Build CI pipelines with matrix strategy across multiple versions","Build and push Docker images to GHCR with BuildKit cache","Manage secrets, environments and manual approval gates","Create reusable workflows and composite actions","Build a full CI/CD pipeline from test to production deploy","Speed up workflows with dependency caching strategies","Harden pipelines against supply chain attacks (2026 roadmap)"],
         prereqs=["Git & GitHub basics","Docker basics","Basic shell scripting"],
         stats=[("4h","Duration",THEMES["actions"]['p']),("8","Exercises",TEAL),("2026","Platform",AMBER)],
         tagline="Push code. Ship to prod. Automatically.",
         tagline2="GitHub Actions — CI/CD built into every repository",
         footer_url="https://docs.github.com/actions"),
    actions_content)

# ═══════════════════════════════════════════════════════════════════════════════
# GUIDE 4 — ArgoCD
# ═══════════════════════════════════════════════════════════════════════════════
def argocd_content(h):
    sp=h['sp']; pb=h['pb']; h1=h['h1']; h2=h['h2']; body=h['body']
    bullet=h['bullet']; num=h['num']; code=h['code']
    info=h['info']; warn=h['warn']; tip=h['tip']; q=h['q']
    divider=h['divider']; exo=h['exo']; tbl=h['tbl']
    s=[]
    s+=[h1("Introduction to ArgoCD"),sp(4)]
    s.append(body("ArgoCD is a declarative, GitOps continuous delivery tool for Kubernetes. It continuously monitors your Git repository and automatically syncs your cluster to match the desired state defined in code. ArgoCD v3.3.6 (the latest stable release) brought a complete v3 architectural overhaul with fine-grained RBAC, server-side apply, and a redesigned UI."))
    s+=[sp(10),h2("GitOps vs traditional CI/CD"),sp(6)]
    s.append(tbl(["Aspect","Traditional CI/CD","GitOps with ArgoCD"],[
        ["Source of truth","CI pipeline scripts","Git repository"],
        ["Deployment trigger","Pipeline runs kubectl","ArgoCD watches Git"],
        ["Cluster credentials","Stored in CI secrets","ArgoCD runs in-cluster"],
        ["Rollback","Re-run old pipeline","git revert + auto-sync"],
        ["Drift detection","None","Continuous, auto-heals"],
        ["Audit trail","CI logs","Git history (full audit)"],
        ["Multi-cluster","Complex scripting","Native multi-cluster support"],
    ],[140,160,199]))
    s+=[sp(12),h2("ArgoCD v3 — Key changes from v2"),sp(6)]
    s.append(tbl(["Change","Details"],[
        ["Fine-grained RBAC","update/delete no longer applies to sub-resources by default"],
        ["Server-side apply","Default for all syncs — better conflict resolution"],
        ["argocd-cm repos","Removed — all repos now managed as Secrets"],
        ["Legacy metrics","argocd_app_sync_status etc. removed — use argocd_app_info labels"],
        ["New UI","Redesigned dashboard with better ApplicationSet visibility"],
    ],[150,349]))
    s.append(pb())

    s.append(exo("1","Install ArgoCD v3","30 min","Easy"))
    s+=[h2("1.1 — Install ArgoCD"),sp(4),
    code(["# Create namespace and install ArgoCD v3.3.6",
          "kubectl create namespace argocd",
          "kubectl apply -n argocd --server-side --force-conflicts \\",
          "  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml",
          "",
          "# Wait for all pods to be ready",
          "kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s",
          "",
          "# Get the initial admin password",
          "kubectl get secret argocd-initial-admin-secret -n argocd \\",
          "  -o jsonpath='{.data.password}' | base64 -d && echo"]),
    sp(10),h2("1.2 — Access the UI"),sp(4),
    code(["# Port-forward the ArgoCD server",
          "kubectl port-forward svc/argocd-server -n argocd 8080:443",
          "",
          "# Open: https://localhost:8080",
          "# Username: admin",
          "# Password: <from above>",
          "",
          "# Install the CLI",
          "curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64",
          "chmod +x argocd && sudo mv argocd /usr/local/bin/",
          "",
          "# Login via CLI",
          "argocd login localhost:8080 --username admin --insecure",
          "",
          "# Change the admin password immediately!",
          "argocd account update-password"]),
    sp(8),warn("Change the initial admin password immediately after installation. Consider disabling the admin account entirely and using SSO (Dex, GitHub OAuth) for production clusters."),
    sp(8),q(["What does '--server-side --force-conflicts' do during installation?","What is the difference between argocd-server and argocd-repo-server?","How do you expose ArgoCD with a LoadBalancer instead of port-forward?"])]
    s+=divider()

    s.append(exo("2","Your First Application","25 min","Easy"))
    s+=[h2("2.1 — Deploy from a Git repository"),sp(4),
    code(["# Add a repository (HTTPS)",
          "argocd repo add https://github.com/myorg/myapp \\",
          "  --username myuser \\",
          "  --password $GITHUB_TOKEN",
          "",
          "# Create an Application",
          "argocd app create myapp \\",
          "  --repo https://github.com/myorg/myapp \\",
          "  --path k8s/ \\",
          "  --dest-server https://kubernetes.default.svc \\",
          "  --dest-namespace production \\",
          "  --sync-policy automated \\",
          "  --auto-prune \\",
          "  --self-heal"]),
    sp(8),
    code(["# Or declaratively (preferred!)",
          "apiVersion: argoproj.io/v1alpha1",
          "kind: Application",
          "metadata:",
          "  name: myapp",
          "  namespace: argocd",
          "spec:",
          "  project: default",
          "  source:",
          "    repoURL: https://github.com/myorg/myapp",
          "    targetRevision: main",
          "    path: k8s/",
          "  destination:",
          "    server: https://kubernetes.default.svc",
          "    namespace: production",
          "  syncPolicy:",
          "    automated:",
          "      prune: true",
          "      selfHeal: true",
          "    syncOptions:",
          "      - CreateNamespace=true"]),
    sp(8),info("'selfHeal: true' means ArgoCD will revert any manual changes made directly to the cluster (drift). This is the core GitOps principle — Git is the only source of truth."),
    sp(8),q(["What is the difference between OutOfSync and Degraded in ArgoCD?","What does 'prune: true' do when resources are removed from Git?","What does selfHeal do and when might you want to disable it?"])]
    s+=divider()

    s.append(exo("3","Helm Charts with ArgoCD","30 min","Intermediate"))
    s+=[h2("3.1 — Deploy a Helm chart"),sp(4),
    code(["apiVersion: argoproj.io/v1alpha1",
          "kind: Application",
          "metadata:",
          "  name: nginx",
          "  namespace: argocd",
          "spec:",
          "  project: default",
          "  source:",
          "    repoURL: https://charts.bitnami.com/bitnami",
          "    chart: nginx",
          "    targetRevision: '18.x'",
          "    helm:",
          "      releaseName: nginx",
          "      values: |",
          "        replicaCount: 2",
          "        service:",
          "          type: ClusterIP",
          "      valueFiles:",
          "        - values-prod.yaml",
          "  destination:",
          "    server: https://kubernetes.default.svc",
          "    namespace: web"]),
    sp(10),h2("3.2 — Multiple sources (values from Git + chart from OCI)"),sp(4),
    code(["spec:",
          "  sources:",
          "    - repoURL: oci://ghcr.io/myorg/charts",
          "      chart: myapp",
          "      targetRevision: '1.2.0'",
          "      helm:",
          "        valueFiles:",
          "          - $values/environments/prod/values.yaml",
          "    - repoURL: https://github.com/myorg/gitops",
          "      targetRevision: main",
          "      ref: values   # reference name for the values repo"]),
    sp(8),tip("Use multiple sources to separate your Helm chart (versioned in OCI) from your values files (in a Git repo). This lets you upgrade chart versions and environment values independently."),
    sp(8),q(["How do you override Helm values with environment-specific files in ArgoCD?","How do you force ArgoCD to use a specific Helm chart version?","What is the 'ref' field in multiple sources?"])]
    s+=divider()

    s.append(exo("4","Projects & RBAC","30 min","Intermediate"))
    s+=[h2("4.1 — AppProjects for multi-team isolation"),sp(4),
    code(["apiVersion: argoproj.io/v1alpha1",
          "kind: AppProject",
          "metadata:",
          "  name: team-backend",
          "  namespace: argocd",
          "spec:",
          "  description: Backend team applications",
          "  sourceRepos:",
          "    - 'https://github.com/myorg/backend-*'",
          "  destinations:",
          "    - namespace: 'backend-*'",
          "      server: https://kubernetes.default.svc",
          "  clusterResourceWhitelist:",
          "    - group: ''",
          "      kind: Namespace",
          "  namespaceResourceBlacklist:",
          "    - group: ''",
          "      kind: ResourceQuota",
          "  roles:",
          "    - name: developer",
          "      description: Can sync but not delete",
          "      policies:",
          "        - p, proj:team-backend:developer, applications, sync, team-backend/*, allow",
          "        - p, proj:team-backend:developer, applications, get, team-backend/*, allow",
          "      groups:",
          "        - backend-engineers"]),
    sp(8),info("AppProjects are the ArgoCD multi-tenancy boundary. Each team gets a project that restricts which repos they can deploy from, which namespaces they can deploy to, and what Kubernetes resources they can manage."),
    sp(8),q(["What is the difference between a clusterResourceWhitelist and namespaceResourceBlacklist?","How do you add GitHub team SSO to ArgoCD RBAC?","What happens if an Application tries to deploy outside its Project's allowed destinations?"])]
    s+=divider()

    s.append(exo("5","Sync Policies & Waves","25 min","Intermediate"))
    s+=[h2("5.1 — Sync options"),sp(4),
    code(["syncPolicy:",
          "  automated:",
          "    prune: true",
          "    selfHeal: true",
          "    allowEmpty: false   # don't prune everything if source is empty",
          "  syncOptions:",
          "    - CreateNamespace=true",
          "    - ServerSideApply=true",
          "    - PrunePropagationPolicy=foreground",
          "    - RespectIgnoreDifferences=true",
          "  retry:",
          "    limit: 5",
          "    backoff:",
          "      duration: 5s",
          "      factor: 2",
          "      maxDuration: 3m"]),
    sp(10),h2("5.2 — Sync waves for ordered deployment"),sp(4),
    code(["# Deploy resources in order using sync waves",
          "# Lower wave number = deployed first",
          "",
          "# 1. Namespace (wave -2)",
          "metadata:",
          "  annotations:",
          "    argocd.argoproj.io/sync-wave: '-2'",
          "",
          "# 2. Database (wave -1) — wait for namespace",
          "metadata:",
          "  annotations:",
          "    argocd.argoproj.io/sync-wave: '-1'",
          "",
          "# 3. Application (wave 0 — default)",
          "",
          "# 4. Ingress (wave 1) — after app is running",
          "metadata:",
          "  annotations:",
          "    argocd.argoproj.io/sync-wave: '1'"]),
    sp(8),tip("Combine sync waves with resource health checks. ArgoCD won't move to the next wave until all resources in the current wave are Healthy — this gives you ordered, safe deployments."),
    sp(8),q(["What is the difference between sync-wave and sync-phase?","How do you force a manual sync when automated sync is enabled?","What does 'allowEmpty: false' protect against?"])]
    s+=divider()

    s.append(exo("6","ApplicationSets — Multi-Cluster","30 min","Advanced"))
    s+=[h2("6.1 — Deploy to multiple clusters with one ApplicationSet"),sp(4),
    code(["apiVersion: argoproj.io/v1alpha1",
          "kind: ApplicationSet",
          "metadata:",
          "  name: myapp-all-clusters",
          "  namespace: argocd",
          "spec:",
          "  generators:",
          "    - clusters:",
          "        selector:",
          "          matchLabels:",
          "            environment: production",
          "  template:",
          "    metadata:",
          "      name: 'myapp-{{name}}'",
          "    spec:",
          "      project: default",
          "      source:",
          "        repoURL: https://github.com/myorg/myapp",
          "        targetRevision: main",
          "        path: 'k8s/overlays/{{metadata.labels.region}}'",
          "      destination:",
          "        server: '{{server}}'",
          "        namespace: production",
          "      syncPolicy:",
          "        automated:",
          "          prune: true",
          "          selfHeal: true"]),
    sp(8),info("ApplicationSets automatically create, update and delete ArgoCD Applications based on generators. The clusters generator creates one Application per registered cluster matching the label selector."),
    sp(8),q(["What other generators does ApplicationSet support besides clusters?","How do you register an external cluster with ArgoCD?","What happens to an Application when its cluster label no longer matches the selector?"])]
    s+=divider()

    s.append(exo("7","Notifications & Monitoring","20 min","Intermediate"))
    s+=[h2("7.1 — ArgoCD Notifications"),sp(4),
    code(["# Install notifications controller",
          "kubectl apply -n argocd \\",
          "  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/notifications_catalog/install.yaml",
          "",
          "# Configure Slack notifications",
          "kubectl patch cm argocd-notifications-cm -n argocd --patch '{",
          '  "data": {',
          '    "service.slack": "| token: $slack-token"',
          "  }",
          "}'",
          "",
          "# Add annotation to Application",
          "kubectl annotate app myapp -n argocd \\",
          "  notifications.argoproj.io/subscribe.on-sync-failed.slack=deployments \\",
          "  notifications.argoproj.io/subscribe.on-health-degraded.slack=alerts"]),
    sp(10),h2("7.2 — Key metrics to monitor"),sp(4),
    tbl(["Metric","Description"],[
        ["argocd_app_info","App health and sync status (primary metric)"],
        ["argocd_app_sync_total","Total sync operations by result"],
        ["argocd_cluster_api_resource_objects","Resource count per cluster"],
        ["argocd_repo_pending_requests_total","Repo server queue depth"],
    ],[200,299]),
    sp(8),tip("Use the argocd_app_info metric with labels (health_status, sync_status) in Prometheus/Grafana to build an ArgoCD dashboard. The legacy argocd_app_sync_status metric was removed in v3."),
    sp(8),q(["How do you send notifications on successful deploys vs failures?","Which Prometheus metrics were removed in ArgoCD v3?","How do you configure webhook notifications for GitHub?"])]
    s+=divider()

    s.append(exo("8","Production Best Practices","25 min","Advanced"))
    s+=[h2("8.1 — Production hardening checklist"),sp(4)]
    for t in ["Use AppProjects to isolate teams — never use the default project in prod","Enable automated sync with selfHeal and prune on all production Apps","Set resource limits on ArgoCD components (repo-server is most memory-hungry)","Use SSO (GitHub OAuth, Okta, Google) — disable the admin account","Pin ArgoCD version in manifests — don't use 'stable' channel in prod","Back up ArgoCD state: all Applications, Projects, Secrets (git-managed is best)","Use ApplicationSets for any app deployed to more than 2 clusters","Enable audit logging to track who triggered syncs and changed configs"]:
        s.append(bullet(t))
    s+=[sp(10),h2("8.2 — High Availability install"),sp(4),
    code(["# HA mode: multiple replicas of each component",
          "kubectl apply -n argocd --server-side --force-conflicts \\",
          "  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/ha/install.yaml",
          "",
          "# HA requires at least 3 nodes for proper anti-affinity rules"]),
    sp(8),warn("The standard (non-HA) install is a single point of failure. Use HA mode for production clusters managing critical workloads. HA requires 3+ nodes to respect pod anti-affinity rules."),
    sp(8),q(["What is the difference between the standard and HA install manifests?","How do you backup and restore ArgoCD state?","How do you manage ArgoCD itself with ArgoCD (App of Apps pattern)?"])]
    s.append(pb())

    s+=[h1("Appendix — Quick Reference"),sp(6),h2("Essential argocd CLI commands"),sp(6)]
    s.append(tbl(["Command","Description"],[
        ["argocd app list","List all applications"],
        ["argocd app get myapp","Show app status and sync details"],
        ["argocd app sync myapp","Manually trigger a sync"],
        ["argocd app sync myapp --dry-run","Preview changes without applying"],
        ["argocd app diff myapp","Show diff between Git and cluster"],
        ["argocd app rollback myapp 3","Rollback to revision 3"],
        ["argocd app history myapp","Show deployment history"],
        ["argocd app delete myapp","Delete the app (and resources if --cascade)"],
        ["argocd repo list","List configured repositories"],
        ["argocd cluster list","List registered clusters"],
        ["argocd proj list","List AppProjects"],
        ["argocd admin export > backup.yaml","Export all ArgoCD config"],
    ],[220,279]))
    s+=[sp(14),h2("Application health statuses"),sp(6)]
    s.append(tbl(["Status","Meaning"],[
        ["Healthy","All resources are running and ready"],
        ["Progressing","Resources are being updated (rollout in progress)"],
        ["Degraded","One or more resources are not healthy"],
        ["Suspended","Application or resource is intentionally paused"],
        ["Missing","Resource exists in Git but not in cluster"],
        ["Unknown","Health cannot be determined"],
        ["Synced","Cluster matches Git state"],
        ["OutOfSync","Cluster differs from Git (drift detected)"],
    ],[100,399]))
    s+=[sp(14),info("Official docs: https://argo-cd.readthedocs.io  |  GitHub: https://github.com/argoproj/argo-cd  |  CNCF: https://www.cncf.io/projects/argo/")]
    return s

build_pdf("/mnt/user-data/outputs/ArgoCD_Essential_Training.pdf",
    THEMES["argocd"],
    dict(topics=[("01","Install ArgoCD v3"),("02","Your First Application"),("03","Helm Charts with ArgoCD"),("04","Projects & RBAC"),("05","Sync Policies & Waves"),("06","ApplicationSets — Multi-Cluster"),("07","Notifications & Monitoring"),("08","Production Best Practices")],
         subtitle_lines=["GitOps · Applications · Helm · RBAC · ApplicationSets"],
         footer_right="ArgoCD v3.3.6 | CNCF Graduated"),
    dict(skills=["Install ArgoCD v3 and access the UI and CLI","Deploy applications from Git with automated sync","Deploy Helm charts with environment-specific values","Set up AppProjects for team isolation and RBAC","Configure sync policies, waves and ordered deployments","Deploy to multiple clusters with ApplicationSets","Set up Slack and webhook notifications for sync events","Harden ArgoCD for production with HA and SSO"],
         prereqs=["Kubernetes basics","kubectl","Git & GitHub"],
         stats=[("4h","Duration",THEMES["argocd"]['p']),("8","Exercises",TEAL),("v3.3","ArgoCD",AMBER)],
         tagline="Git is your source of truth. ArgoCD does the rest.",
         tagline2="ArgoCD — Declarative GitOps for Kubernetes",
         footer_url="https://argo-cd.readthedocs.io"),
    argocd_content)

print("\n✅ All 4 guides generated!")
