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

THEMES = {
    "prometheus": dict(p=HexColor("#E6522C"), d=HexColor("#A83510"), m=HexColor("#F08060"),
                       l=HexColor("#FDE8DC"), name="Prometheus", sub="Metrics & Alerting",
                       badge="v3.11.1", accent_hex="#E6522C"),
    "grafana":    dict(p=HexColor("#F46800"), d=HexColor("#B34D00"), m=HexColor("#F88C3A"),
                       l=HexColor("#FEF0E0"), name="Grafana", sub="Visualization & Dashboards",
                       badge="v11.x", accent_hex="#F46800"),
    "loki":       dict(p=HexColor("#6B4FBB"), d=HexColor("#4A3488"), m=HexColor("#9B7FDB"),
                       l=HexColor("#EDE8FA"), name="Loki + OpenTelemetry", sub="Logs Traces & Metrics",
                       badge="v3.6", accent_hex="#6B4FBB"),
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
        c.setFillColor(t['p']); c.roundRect(W-MR-64,H-37,64,16,3,fill=1,stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold",7)
        c.drawCentredString(W-MR-32,H-29,t['name'][:14].upper())
        c.setStrokeColor(GRAY_M); c.line(ML,32,W-MR,32)
        c.setFillColor(GRAY); c.setFont("Helvetica",8)
        if self.page%2==0: c.drawString(ML,22,str(self.page))
        else: c.drawRightString(W-MR,22,str(self.page))
        c.restoreState()

def draw_cover(c, t, topics, subtitle_line, footer_right, difficulty="Intermediate"):
    c.setFillColor(INK); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(t['p']); c.rect(0,0,16,H,fill=1,stroke=0)
    c.setFillColor(t['m']); c.rect(16,H-8,W-16,8,fill=1,stroke=0)
    c.setFillColor(HexColor("#1A1A2A"))
    for row in range(9):
        for col in range(11):
            cx=W-260+col*22; cy=H-55-row*22
            if 16<cx<W-10: c.circle(cx,cy,1.5,fill=1,stroke=0)
    c.setFillColor(t['p']); c.setFillAlpha(0.07)
    c.setFont("Helvetica-Bold",100); c.drawString(20,H//2-60,t['name'][:8])
    c.setFillAlpha(1.0)
    c.setFillColor(t['m']); c.setFont("Helvetica-Bold",8)
    c.drawString(34,H-46,"ESSENTIAL TRAINING SERIES")
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold",52); c.drawString(34,H-112,t['name'])
    c.setFillColor(t['m']); c.setFont("Helvetica-Bold",28)
    c.drawString(34,H-153,t['sub'])
    c.setFont("Helvetica-Bold",20); c.drawString(34,H-186,"Latest — "+t['badge'])
    c.setStrokeColor(t['m']); c.setLineWidth(2.5); c.line(34,H-204,300,H-204)
    c.setFillColor(HexColor("#94A3B8")); c.setFont("Helvetica",11)
    c.drawString(34,H-226,subtitle_line)
    bstart=H-260
    badges=[("8 Exercises",t['p']),("4 Hours",TEAL),(difficulty,AMBER)]
    bx=34
    for label,col in badges:
        bw=len(label)*7.2+20
        c.setFillColor(HexColor("#1E1040")); c.roundRect(bx,bstart,bw,22,4,fill=1,stroke=0)
        c.setStrokeColor(col); c.setLineWidth(0.8); c.roundRect(bx,bstart,bw,22,4,fill=0,stroke=1)
        c.setFillColor(col); c.setFont("Helvetica-Bold",8); c.drawString(bx+10,bstart+9,label)
        bx+=bw+8
    box_h=len(topics)*30+36; box_y=bstart-18-box_h
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
    c.drawString(34,28,"Hands-on Lab — Observability & Monitoring")
    c.setFillColor(t['l']); c.setFont("Helvetica",8)
    c.drawRightString(W-34,16,footer_right)

def draw_back(c, t, skills, prereqs, stats_vals, tagline, tagline2, footer_url):
    c.setFillColor(INK); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(t['p']); c.rect(W-16,0,16,H,fill=1,stroke=0)
    c.setFillColor(t['m']); c.rect(0,H-8,W-16,8,fill=1,stroke=0)
    c.setFillAlpha(0.04); c.setFillColor(WHITE); c.setFont("Helvetica-Bold",110)
    c.drawString(-10,H//2-55,t['name'][:7]); c.setFillAlpha(1.0)
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
    for i,(val,label,col) in enumerate(stats_vals):
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

def build_pdf(output, t, cover_kwargs, back_kwargs, content_fn):
    st=make_styles(t)
    def sp(h=6): return Spacer(1,h)
    def pb(): return PageBreak()
    def h1(txt): return KeepTogether([HRFlowable(width="100%",thickness=2.5,color=t['p'],spaceAfter=3),Paragraph(txt,st['h1']),HRFlowable(width="100%",thickness=0.5,color=GRAY_M,spaceBefore=2,spaceAfter=10)])
    def h2(txt): return Paragraph(txt,st['h2'])
    def body(txt): return Paragraph(txt,st['body'])
    def bullet(txt): return Paragraph(f'<font color="{t["accent_hex"]}">•</font>  {txt}',st['bt'])
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
    helpers=dict(sp=sp,pb=pb,h1=h1,h2=h2,body=body,bullet=bullet,
                 code=code,info=info,warn=warn,tip=tip,q=q,divider=divider,exo=exo,tbl=tbl)
    story=content_fn(helpers)
    cov=io.BytesIO()
    cv=canvas.Canvas(cov,pagesize=A4); draw_cover(cv,t,**cover_kwargs); cv.showPage(); cv.save(); cov.seek(0)
    bak=io.BytesIO()
    bv=canvas.Canvas(bak,pagesize=A4); draw_back(bv,t,**back_kwargs); bv.showPage(); bv.save(); bak.seek(0)
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
# GUIDE 1 — PROMETHEUS
# ═══════════════════════════════════════════════════════════════════════════════
def prometheus_content(h):
    sp=h['sp']; pb=h['pb']; h1=h['h1']; h2=h['h2']; body=h['body']
    bullet=h['bullet']; code=h['code']; info=h['info']; warn=h['warn']
    tip=h['tip']; q=h['q']; divider=h['divider']; exo=h['exo']; tbl=h['tbl']
    s=[]
    s+=[h1("Introduction to Prometheus"),sp(4)]
    s.append(body("Prometheus v3.11.1 is the industry-standard open-source monitoring system for cloud-native environments. It collects metrics by scraping HTTP endpoints, stores them in a time-series database, and supports powerful queries via PromQL. Prometheus v3 (released Nov 2024) brought a brand-new UI, native histograms, OTLP ingestion, and Remote Write 2.0."))
    s+=[sp(10),h2("Prometheus v3 — Key features"),sp(6)]
    s.append(tbl(["Feature","Description"],[
        ["New UI","Completely rewritten in React/Mantine — metrics explorer, label explorer"],
        ["Native histograms","More accurate latency tracking, fewer series vs classic histograms"],
        ["OTLP ingestion","Receive metrics from OpenTelemetry Collector natively (no bridge needed)"],
        ["Remote Write 2.0","Better compression, metadata support, reduced CPU overhead"],
        ["UTF-8 labels","Full Unicode support in metric and label names"],
        ["PromQL improvements","New functions: sort_by_label, limitk, totime, info()"],
    ],[160,339]))
    s+=[sp(12),h2("Core concepts"),sp(6)]
    s.append(tbl(["Concept","Description"],[
        ["Metric","A time-series with a name, labels and numeric values over time"],
        ["Target","An HTTP endpoint that Prometheus scrapes for metrics"],
        ["Scrape","A GET request to /metrics — happens every scrape_interval (default: 1m)"],
        ["Label","Key-value pair attached to a metric for filtering and grouping"],
        ["Job","A collection of targets with the same purpose (e.g. all nginx instances)"],
        ["AlertRule","A PromQL expression that fires an alert when true for duration"],
        ["Recording Rule","A pre-computed PromQL query stored as a new metric for performance"],
        ["Alertmanager","Receives alerts from Prometheus and routes to Slack, PagerDuty, email..."],
    ],[130,369]))
    s.append(pb())

    s.append(exo("1","Install with kube-prometheus-stack","30 min","Easy"))
    s+=[h2("1.1 — The fastest path: kube-prometheus-stack"),sp(4)]
    s.append(body("The kube-prometheus-stack Helm chart (v82.x) deploys Prometheus Operator, Prometheus, Alertmanager, Grafana, kube-state-metrics, and Node Exporter in one command:"))
    s+=[sp(4),code(["helm repo add prometheus-community https://prometheus-community.github.io/helm-charts",
        "helm repo update",
        "",
        "kubectl create namespace monitoring",
        "",
        "helm install prometheus prometheus-community/kube-prometheus-stack \\",
        "  --namespace monitoring \\",
        "  --set prometheus.prometheusSpec.retention=30d \\",
        "  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName=local-path \\",
        "  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=20Gi \\",
        "  --wait --timeout 10m",
        "",
        "# Check all pods are running",
        "kubectl get pods -n monitoring"]),
    sp(10),h2("1.2 — Access Prometheus UI"),sp(4),
    code(["kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090",
        "# Open: http://localhost:9090"]),
    sp(8),info("The kube-prometheus-stack chart includes pre-built dashboards and alerting rules for Kubernetes — node resource usage, pod status, etcd health, API server latency and more. Everything works out of the box."),
    sp(8),q(["What components are deployed by kube-prometheus-stack?","What does the Prometheus Operator do?","How do you check the Prometheus configuration that is actually running?"])]
    s+=divider()

    s.append(exo("2","PromQL — Query Language","40 min","Intermediate"))
    s+=[h2("2.1 — Metric types"),sp(6)]
    s.append(tbl(["Type","Description","Example"],[
        ["Counter","Monotonically increasing value — only goes up","http_requests_total"],
        ["Gauge","Value that can go up and down","memory_usage_bytes"],
        ["Histogram","Counts observations in configurable buckets","http_request_duration_seconds"],
        ["Summary","Pre-calculated quantiles (client-side)","go_gc_duration_seconds"],
    ],[90,230,179]))
    s+=[sp(10),h2("2.2 — Essential PromQL queries"),sp(4),
    code(["# Request rate per second (last 5 min)",
        "rate(http_requests_total[5m])",
        "",
        "# Error rate %",
        "rate(http_requests_total{status=~'5..'}[5m]) / rate(http_requests_total[5m]) * 100",
        "",
        "# CPU usage per pod (millicores)",
        "sum(rate(container_cpu_usage_seconds_total{container!=''}[5m])) by (pod) * 1000",
        "",
        "# Memory usage per pod (MB)",
        "sum(container_memory_working_set_bytes{container!=''}) by (pod) / 1024 / 1024",
        "",
        "# Node disk usage %",
        "100 - (node_filesystem_avail_bytes{mountpoint='/'} / node_filesystem_size_bytes{mountpoint='/'} * 100)",
        "",
        "# Pods not running",
        "kube_pod_status_phase{phase!='Running',phase!='Succeeded'} == 1",
        "",
        "# 99th percentile latency (native histogram)",
        "histogram_quantile(0.99, rate(http_request_duration_seconds[5m]))"]),
    sp(8),tip("Use 'rate()' for counters, never 'irate()' unless you specifically need instant rate. rate() is more stable and works better with gaps in data. For alerting always use rate() over a window of at least 2x the scrape interval."),
    sp(8),q(["What is the difference between rate() and irate()?","Why should you never use a counter directly in a graph without rate()?","What does the {status=~'5..'} label matcher mean?"])]
    s+=divider()

    s.append(exo("3","ServiceMonitors & PodMonitors","25 min","Intermediate"))
    s+=[h2("3.1 — Scrape your own app with ServiceMonitor"),sp(4),
    s.append(body("The Prometheus Operator uses ServiceMonitor CRDs to define what to scrape — no manual prometheus.yaml editing needed:")),
    sp(4),code(["apiVersion: monitoring.coreos.com/v1",
        "kind: ServiceMonitor",
        "metadata:",
        "  name: myapp",
        "  namespace: monitoring",
        "  labels:",
        "    release: prometheus   # must match prometheusSpec.serviceMonitorSelector",
        "spec:",
        "  namespaceSelector:",
        "    matchNames: [production]",
        "  selector:",
        "    matchLabels:",
        "      app: myapp",
        "  endpoints:",
        "  - port: http-metrics",
        "    path: /metrics",
        "    interval: 30s",
        "    scheme: http"]),
    sp(8),
    code(["# Verify Prometheus picked up the target",
        "# In the UI: Status > Targets — look for your ServiceMonitor job"]),
    sp(8),info("ServiceMonitors are namespace-scoped. Use the 'namespaceSelector' to scrape targets in a different namespace. The 'release: prometheus' label must match the labelSelector in your Prometheus CR."),
    sp(8),q(["What is the difference between a ServiceMonitor and a PodMonitor?","How do you scrape a job not running in Kubernetes (e.g. a bare-metal database)?","What does the 'release: prometheus' label do?"])]
    s+=divider()

    s.append(exo("4","Alerting Rules","30 min","Intermediate"))
    s+=[h2("4.1 — PrometheusRule CRD"),sp(4),
    code(["apiVersion: monitoring.coreos.com/v1",
        "kind: PrometheusRule",
        "metadata:",
        "  name: myapp-alerts",
        "  namespace: monitoring",
        "  labels:",
        "    release: prometheus",
        "spec:",
        "  groups:",
        "  - name: myapp.rules",
        "    interval: 1m",
        "    rules:",
        "",
        "    # Alert: high error rate",
        "    - alert: HighErrorRate",
        "      expr: |",
        "        rate(http_requests_total{status=~'5..'}[5m])",
        "        /",
        "        rate(http_requests_total[5m]) > 0.05",
        "      for: 5m",
        "      labels:",
        "        severity: critical",
        "        team: backend",
        "      annotations:",
        "        summary: 'High error rate on {{ $labels.job }}'",
        "        description: 'Error rate is {{ $value | humanizePercentage }}'",
        "",
        "    # Recording rule: pre-compute expensive query",
        "    - record: job:http_requests:rate5m",
        "      expr: rate(http_requests_total[5m])"]),
    sp(10),h2("4.2 — Alertmanager routing"),sp(4),
    code(["# Alertmanager config (via secret or Helm values)",
        "global:",
        "  resolve_timeout: 5m",
        "",
        "route:",
        "  group_by: [alertname, team]",
        "  group_wait: 30s",
        "  group_interval: 5m",
        "  repeat_interval: 4h",
        "  receiver: slack-default",
        "  routes:",
        "  - matchers:",
        "    - severity = critical",
        "    receiver: pagerduty-critical",
        "    continue: false",
        "",
        "receivers:",
        "- name: slack-default",
        "  slack_configs:",
        "  - api_url: $SLACK_WEBHOOK_URL",
        "    channel: '#alerts'",
        "    title: '[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}'",
        "",
        "- name: pagerduty-critical",
        "  pagerduty_configs:",
        "  - service_key: $PAGERDUTY_KEY"]),
    sp(8),warn("The 'for' duration in an alert rule defines how long the condition must be true before firing. Too short = noisy alerts. Too long = slow response. 5 minutes is a good starting point for most alerts."),
    sp(8),q(["What is the difference between 'for' and 'group_wait' in alerting?","What does a recording rule do and when should you use one?","How do you silence a specific alert in Alertmanager?"])]
    s+=divider()

    s.append(exo("5","Node Exporter & kube-state-metrics","20 min","Easy"))
    s+=[h2("5.1 — Node Exporter — host metrics"),sp(4),
    tbl(["Metric","Description"],[
        ["node_cpu_seconds_total","CPU time by mode (user, system, idle, iowait...)"],
        ["node_memory_MemAvailable_bytes","Available memory on the host"],
        ["node_filesystem_avail_bytes","Available disk space by mount point"],
        ["node_network_receive_bytes_total","Network bytes received by interface"],
        ["node_load1","1-minute load average"],
        ["node_disk_io_time_seconds_total","Disk I/O utilization"],
    ],[200,299]),
    sp(10),h2("5.2 — kube-state-metrics — K8s object metrics"),sp(4),
    tbl(["Metric","Description"],[
        ["kube_pod_status_phase","Pod phase (Running, Pending, Failed...)"],
        ["kube_deployment_status_replicas_available","Available replicas in a Deployment"],
        ["kube_node_status_condition","Node condition (Ready, DiskPressure...)"],
        ["kube_persistentvolumeclaim_status_phase","PVC binding status"],
        ["kube_job_status_failed","Failed job count"],
        ["kube_resourcequota","Resource quota usage by namespace"],
    ],[200,299]),
    sp(8),info("Node Exporter exposes host-level metrics (CPU, memory, disk, network). kube-state-metrics exposes Kubernetes object state metrics. Both are deployed automatically by kube-prometheus-stack."),
    sp(8),q(["What is the difference between node_memory_MemFree_bytes and node_memory_MemAvailable_bytes?","How do you add a custom Node Exporter text collector?","How do you monitor a StatefulSet's replica count?"])]
    s+=divider()

    s.append(exo("6","Long-term Storage with Thanos","30 min","Advanced"))
    s+=[h2("6.1 — Why Thanos?"),sp(4)]
    s.append(body("Prometheus stores data locally — typically 15-30 days. Thanos extends Prometheus with unlimited long-term storage in object storage (S3, GCS, Azure Blob), global query across multiple clusters, and high availability."))
    s+=[sp(6),tbl(["Thanos Component","Role"],[
        ["Sidecar","Runs next to Prometheus, uploads blocks to object store"],
        ["Store Gateway","Serves historical data from object store"],
        ["Querier","Global query layer — merges results from all Prometheus + Store"],
        ["Compactor","Downsamples and compacts old blocks to save storage"],
        ["Ruler","Evaluates recording/alert rules across the global view"],
    ],[160,339]),
    sp(10),h2("6.2 — Sidecar configuration"),sp(4),
    code(["# In prometheus Helm values",
        "prometheus:",
        "  prometheusSpec:",
        "    thanos:",
        "      image: quay.io/thanos/thanos:v0.38.0",
        "      objectStorageConfig:",
        "        secret:",
        "          type: S3",
        "          config:",
        "            bucket: my-prometheus-long-term",
        "            endpoint: s3.eu-west-1.amazonaws.com",
        "            region: eu-west-1"]),
    sp(8),tip("Use Thanos Compactor's downsampling to reduce storage cost: keep raw data for 7 days, 5-minute resolution for 30 days, 1-hour resolution for 1 year. This dramatically reduces S3 costs."),
    sp(8),q(["What is the minimum retention for Prometheus when using Thanos?","How does Thanos handle duplicate data from HA Prometheus pairs?","What is the difference between Thanos Querier and Thanos Query Frontend?"])]
    s+=divider()

    s.append(exo("7","SLOs & Error Budgets","25 min","Advanced"))
    s+=[h2("7.1 — Defining SLOs with recording rules"),sp(4),
    code(["# SLO: 99.9% of requests succeed over 30 days",
        "# Step 1: Recording rule for error ratio",
        "- record: job_route:request_error_rate:ratio_rate5m",
        "  expr: |",
        "    rate(http_requests_total{status=~'5..'}[5m])",
        "    /",
        "    rate(http_requests_total[5m])",
        "",
        "# Step 2: Multi-window multi-burn-rate alert",
        "- alert: ErrorBudgetBurnTooFast",
        "  expr: |",
        "    job_route:request_error_rate:ratio_rate1h > (14.4 * 0.001)",
        "    and",
        "    job_route:request_error_rate:ratio_rate5m > (14.4 * 0.001)",
        "  for: 1m",
        "  labels:",
        "    severity: critical",
        "    slo: availability",
        "  annotations:",
        "    summary: 'Error budget burning 14.4x faster than target'"]),
    sp(8),info("The burn rate of 14.4 means you will consume your entire 30-day error budget in 30/14.4 = ~2 days. Multi-window alerting (1h + 5m) reduces false positives while maintaining fast detection."),
    sp(8),q(["What is an error budget and how is it calculated?","What does a burn rate of 1 mean?","What is the Google SRE recommendation for multi-window burn rate thresholds?"])]
    s+=divider()

    s.append(exo("8","Production Best Practices","20 min","Advanced"))
    s+=[h2("8.1 — Cardinality management"),sp(4)]
    for t in ["Never put high-cardinality values in labels (user IDs, URLs, trace IDs)","Use label_replace() and metric_relabel_configs to drop unused labels","Monitor your own Prometheus: prometheus_tsdb_head_series > 1M = problem","Use recording rules to pre-aggregate high-cardinality metrics before querying","Run 'promtool analyze' to find your most expensive metrics"]:
        s.append(bullet(t))
    s+=[sp(10),h2("8.2 — Performance tuning"),sp(4),
    code(["# prometheus.yaml tuning",
        "global:",
        "  scrape_interval: 30s     # increase from 15s to reduce load",
        "  evaluation_interval: 30s",
        "",
        "# Limit samples per scrape",
        "scrape_configs:",
        "- job_name: myapp",
        "  sample_limit: 10000",
        "  label_limit: 30",
        "",
        "# Remote Write tuning",
        "remote_write:",
        "- url: http://thanos-sidecar:10901/api/v1/receive",
        "  queue_config:",
        "    max_samples_per_send: 10000",
        "    capacity: 50000",
        "    max_shards: 20"]),
    sp(8),warn("High cardinality is the #1 performance problem in Prometheus. A single metric with 100k unique label combinations creates 100k time series and will eventually OOM your Prometheus. Monitor prometheus_tsdb_head_series closely."),
    sp(8),q(["What is cardinality and why does it matter for Prometheus performance?","How do you drop specific labels from a scraped metric?","How do you find which targets are producing the most series?"])]
    s.append(pb())

    s+=[h1("Appendix — PromQL Quick Reference"),sp(6),h2("Essential functions"),sp(6)]
    s.append(tbl(["Function","Usage","Description"],[
        ["rate()","rate(counter[5m])","Per-second rate of change over window"],
        ["increase()","increase(counter[1h])","Total increase over window"],
        ["sum()","sum(metric) by (label)","Aggregate across series"],
        ["avg()","avg(metric) by (label)","Average across series"],
        ["max() / min()","max(metric) by (node)","Maximum / minimum value"],
        ["histogram_quantile()","histogram_quantile(0.99, rate(hist[5m]))","Calculate percentile"],
        ["irate()","irate(counter[5m])","Instant rate (last 2 samples only)"],
        ["topk()","topk(5, metric)","Top N series by value"],
        ["absent()","absent(up{job='myapp'})","Alert if metric is missing"],
        ["predict_linear()","predict_linear(disk[1h], 4*3600)","Forecast value in N seconds"],
    ],[120,190,189]))
    s+=[sp(14),info("Official docs: https://prometheus.io/docs  |  PromQL cheatsheet: https://promlabs.com/promql-cheat-sheet  |  Alerting: https://prometheus.io/docs/alerting/")]
    return s

build_pdf("/mnt/user-data/outputs/Prometheus_Essential_Training.pdf",
    THEMES["prometheus"],
    dict(topics=[("01","Install kube-prometheus-stack"),("02","PromQL Query Language"),("03","ServiceMonitors & PodMonitors"),("04","Alerting Rules & Alertmanager"),("05","Node Exporter & kube-state-metrics"),("06","Long-term Storage with Thanos"),("07","SLOs & Error Budgets"),("08","Production Best Practices")],
         subtitle_line="PromQL · Alerting · ServiceMonitors · Thanos · SLOs",
         footer_right="Prometheus v3.11.1 | kube-prometheus-stack v82.x"),
    dict(skills=["Deploy the full Prometheus stack on Kubernetes with one Helm command","Write PromQL queries for rates, latency percentiles and resource usage","Configure ServiceMonitors to auto-discover and scrape your applications","Create PrometheusRule alerts and route them to Slack and PagerDuty","Understand Node Exporter and kube-state-metrics metrics","Extend retention to years with Thanos and object storage","Define SLOs and multi-window burn rate alerts","Tune Prometheus for production: cardinality, performance, storage"],
         prereqs=["Kubernetes basics","kubectl & Helm","Basic metrics concepts"],
         stats_vals=[("4h","Duration",THEMES["prometheus"]['p']),("8","Exercises",TEAL),("v3.11","Prometheus",AMBER)],
         tagline="If you can't measure it, you can't improve it.",
         tagline2="Prometheus — The standard for Kubernetes metrics",
         footer_url="https://prometheus.io/docs"),
    prometheus_content)

# ═══════════════════════════════════════════════════════════════════════════════
# GUIDE 2 — GRAFANA
# ═══════════════════════════════════════════════════════════════════════════════
def grafana_content(h):
    sp=h['sp']; pb=h['pb']; h1=h['h1']; h2=h['h2']; body=h['body']
    bullet=h['bullet']; code=h['code']; info=h['info']; warn=h['warn']
    tip=h['tip']; q=h['q']; divider=h['divider']; exo=h['exo']; tbl=h['tbl']
    s=[]
    s+=[h1("Introduction to Grafana"),sp(4)]
    s.append(body("Grafana v11 is the open-source observability and data visualization platform that connects to Prometheus, Loki, Tempo, and 150+ other data sources. It lets you build interactive dashboards, set up unified alerting, and explore metrics, logs and traces in one place. Grafana Alloy (the successor to Promtail and Grafana Agent) is now the recommended telemetry pipeline."))
    s+=[sp(10),h2("What's new in Grafana v11"),sp(6)]
    s.append(tbl(["Feature","Description"],[
        ["Scenes","New dashboard engine — dynamic, programmable dashboards as code"],
        ["Unified Alerting","Single alerting system for all data sources (replaces legacy alerts)"],
        ["Grafana Alloy","Unified telemetry pipeline: metrics, logs, traces, profiles in one agent"],
        ["Explore Metrics","No-PromQL metrics exploration — browse and visualize without code"],
        ["Explore Logs","Log browsing with pattern detection and volume graphs"],
        ["LBAC","Label-based access control for fine-grained data isolation"],
        ["k6 integration","Load testing results directly in Grafana dashboards"],
    ],[160,339]))
    s.append(pb())

    s.append(exo("1","Installation & Data Sources","20 min","Easy"))
    s+=[h2("1.1 — Install standalone Grafana"),sp(4),
    code(["helm repo add grafana https://grafana.github.io/helm-charts",
        "helm repo update",
        "",
        "helm install grafana grafana/grafana \\",
        "  --namespace monitoring \\",
        "  --set persistence.enabled=true \\",
        "  --set persistence.storageClassName=local-path \\",
        "  --set persistence.size=10Gi \\",
        "  --set adminPassword=changeme \\",
        "  --set service.type=NodePort",
        "",
        "# Get admin password if auto-generated",
        "kubectl get secret --namespace monitoring grafana \\",
        "  -o jsonpath='{.data.admin-password}' | base64 -d && echo"]),
    sp(10),h2("1.2 — Configure data sources via Helm values"),sp(4),
    code(["# grafana-values.yaml",
        "datasources:",
        "  datasources.yaml:",
        "    apiVersion: 1",
        "    datasources:",
        "    - name: Prometheus",
        "      type: prometheus",
        "      url: http://prometheus-kube-prometheus-prometheus.monitoring:9090",
        "      isDefault: true",
        "      jsonData:",
        "        timeInterval: '30s'",
        "",
        "    - name: Loki",
        "      type: loki",
        "      url: http://loki-gateway.monitoring:80",
        "",
        "    - name: Tempo",
        "      type: tempo",
        "      url: http://tempo.monitoring:3100",
        "      jsonData:",
        "        tracesToLogsV2:",
        "          datasourceUid: loki"]),
    sp(8),info("Provisioning data sources via Helm values (or ConfigMaps) means they are automatically configured on startup and survive pod restarts. Never manually add data sources in production — they will be lost on restart."),
    sp(8),q(["How do you pre-provision dashboards so they appear automatically on startup?","What is the difference between Grafana OSS, Enterprise, and Cloud?","How do you reset the admin password if you forget it?"])]
    s+=divider()

    s.append(exo("2","Building Dashboards","40 min","Intermediate"))
    s+=[h2("2.1 — Panel types"),sp(6)]
    s.append(tbl(["Panel","Best for"],[
        ["Time series","Metrics over time — CPU, memory, request rates, latency"],
        ["Stat","Single current value — uptime %, current error rate, active users"],
        ["Gauge","Current value vs threshold — CPU usage, memory pressure"],
        ["Table","Structured data — top pods by CPU, list of failing jobs"],
        ["Bar chart","Comparison across categories — requests per endpoint"],
        ["Heatmap","Distribution over time — request latency distribution"],
        ["Logs","Log lines from Loki — raw log exploration"],
        ["Traces","Trace waterfall from Tempo — request flow visualization"],
        ["Pie chart","Proportion breakdown — requests by status code"],
        ["Geomap","Geographic distribution — requests by region"],
    ],[110,389]))
    s+=[sp(10),h2("2.2 — Import community dashboards"),sp(4),
    code(["# Top community dashboards (import by ID in Grafana UI: Dashboards > Import)",
        "# Kubernetes cluster overview:       ID 315",
        "# Node Exporter full:               ID 1860",
        "# Kubernetes pods:                  ID 6417",
        "# NGINX Ingress controller:         ID 9614",
        "# PostgreSQL:                       ID 9628",
        "# Redis:                            ID 11835",
        "# Loki logs overview:               ID 13639"]),
    sp(10),h2("2.3 — Dashboard variables for dynamic filtering"),sp(4),
    code(["# Add a variable in Dashboard Settings > Variables",
        "# Type: Query | Data source: Prometheus",
        "",
        "# Variable: namespace",
        "label_values(kube_pod_info, namespace)",
        "",
        "# Variable: pod (filtered by namespace)",
        "label_values(kube_pod_info{namespace='$namespace'}, pod)",
        "",
        "# Use in a panel query:",
        "sum(rate(container_cpu_usage_seconds_total{pod='$pod'}[5m]))"]),
    sp(8),tip("Import dashboard ID 1860 (Node Exporter Full) and 315 (Kubernetes cluster overview) immediately after installing Grafana. These two dashboards give you 80% of the visibility you need on day one."),
    sp(8),q(["What is the difference between a template variable and a constant?","How do you link panels together with data links?","How do you version control your Grafana dashboards?"])]
    s+=divider()

    s.append(exo("3","Unified Alerting","30 min","Intermediate"))
    s+=[h2("3.1 — Create an alert rule"),sp(4),
    code(["# Grafana Unified Alerting rule (via API or UI)",
        "# In Grafana: Alerting > Alert rules > New alert rule",
        "",
        "# Step 1: Define the query (PromQL or Loki)",
        "rate(http_requests_total{status=~'5..'}[5m])",
        "/",
        "rate(http_requests_total[5m]) > 0.05",
        "",
        "# Step 2: Set condition",
        "# IS ABOVE threshold: 0.05",
        "# For: 5 minutes",
        "",
        "# Step 3: Add labels",
        "# severity: critical",
        "# team: backend",
        "",
        "# Step 4: Configure notifications",
        "# Contact point: Slack #alerts"]),
    sp(10),h2("3.2 — Contact points and notification policies"),sp(4),
    code(["# Grafana contact point (Slack) via values.yaml",
        "alerting:",
        "  contactpoints.yaml:",
        "    apiVersion: 1",
        "    contactPoints:",
        "    - orgId: 1",
        "      name: slack-alerts",
        "      receivers:",
        "      - uid: slack-uid-1",
        "        type: slack",
        "        settings:",
        "          url: $__env{SLACK_WEBHOOK_URL}",
        "          channel: '#alerts'",
        "          title: |",
        "            {{ if eq .Status 'firing' }}FIRING{{ else }}RESOLVED{{ end }}",
        "            {{ .CommonLabels.alertname }}"]),
    sp(8),warn("Grafana Unified Alerting and Prometheus Alertmanager are two different systems. kube-prometheus-stack uses Alertmanager by default. Decide on one system and don't mix both — you will get duplicate alerts."),
    sp(8),q(["What is the difference between Grafana Unified Alerting and Alertmanager?","How do you mute an alert during a maintenance window?","How do you test an alert rule without waiting for the condition to be true?"])]
    s+=divider()

    s.append(exo("4","Grafana Alloy — Telemetry Pipeline","30 min","Intermediate"))
    s+=[h2("4.1 — What is Grafana Alloy?"),sp(4)]
    s.append(body("Grafana Alloy is the unified telemetry collector that replaces Promtail (logs), Grafana Agent (metrics), and OTel Collector in one binary. It uses a River-based configuration language and ships metrics to Prometheus, logs to Loki, and traces to Tempo."))
    s+=[sp(6),code(["# Install Grafana Alloy",
        "helm install alloy grafana/alloy \\",
        "  --namespace monitoring \\",
        "  --set alloy.configMap.content=\"$(cat alloy-config.river)\""]),
    sp(8),h2("4.2 — Alloy configuration (River syntax)"),sp(4),
    code(["// alloy-config.river",
        "",
        "// Collect pod logs from all namespaces",
        "loki.source.kubernetes 'pods' {",
        "  targets    = discovery.kubernetes.pods.targets",
        "  forward_to = [loki.write.default.receiver]",
        "}",
        "",
        "discovery.kubernetes 'pods' {",
        "  role = 'pod'",
        "}",
        "",
        "// Send logs to Loki",
        "loki.write 'default' {",
        "  endpoint {",
        "    url = 'http://loki-gateway.monitoring:80/loki/api/v1/push'",
        "  }",
        "}",
        "",
        "// Scrape Prometheus metrics from annotated pods",
        "prometheus.scrape 'pods' {",
        "  targets    = discovery.kubernetes.pods.targets",
        "  forward_to = [prometheus.remote_write.default.receiver]",
        "}",
        "",
        "prometheus.remote_write 'default' {",
        "  endpoint {",
        "    url = 'http://prometheus-kube-prometheus-prometheus.monitoring:9090/api/v1/write'",
        "  }",
        "}"]),
    sp(8),tip("Alloy replaces Promtail, Grafana Agent, and often the OTel Collector in one tool. If you're starting fresh in 2026, use Alloy. Only keep Promtail if you have existing configurations you can't migrate yet."),
    sp(8),q(["What is the difference between Alloy and Promtail?","How do Alloy components communicate with each other?","How do you debug an Alloy configuration?"])]
    s+=divider()

    s.append(exo("5","Dashboards as Code","25 min","Advanced"))
    s+=[h2("5.1 — Grafonnet — Jsonnet library"),sp(4),
    code(["# Install Grafonnet",
        "jb install github.com/grafana/grafonnet/gen/grafonnet-latest@main",
        "",
        "# dashboard.jsonnet",
        "local grafana = import 'grafonnet-latest/main.libsonnet';",
        "",
        "grafana.dashboard.new('My App Dashboard')",
        "+ grafana.dashboard.withUid('myapp-overview')",
        "+ grafana.dashboard.withTimezone('browser')",
        "+ grafana.dashboard.withPanels([",
        "    grafana.panel.timeSeries.new('Request Rate')",
        "    + grafana.panel.timeSeries.withTargets([",
        "        grafana.query.prometheus.new(",
        "          'Prometheus',",
        "          'rate(http_requests_total[5m])'",
        "        ),",
        "    ]),",
        "])"]),
    sp(8),
    code(["# Generate JSON and apply",
        "jsonnet -J vendor dashboard.jsonnet > dashboard.json",
        "curl -X POST http://admin:password@localhost:3000/api/dashboards/db \\",
        "  -H 'Content-Type: application/json' \\",
        "  -d '{\"dashboard\": '$(cat dashboard.json)', \"overwrite\": true}'"]),
    sp(8),info("Grafana also supports dashboard provisioning via ConfigMaps — mount a JSON dashboard file to /var/lib/grafana/dashboards/ and add a provisioning config. This is simpler than Grafonnet for static dashboards."),
    sp(8),q(["What are the alternatives to Grafonnet for dashboards-as-code?","How do you import a community dashboard via the Grafana API?","How do you prevent dashboard changes in the UI from overwriting provisioned dashboards?"])]
    s+=divider()

    s.append(exo("6","Correlating Metrics Logs & Traces","30 min","Advanced"))
    s+=[h2("6.1 — Linking metrics to logs (Explore)"),sp(4),
    code(["# In a Prometheus panel, add a data link to Loki:",
        "# In Panel settings > Data links:",
        "# URL: /explore",
        "# Query:",
        "{namespace='${__field.labels.namespace}',",
        " pod='${__field.labels.pod}'}",
        "",
        "# This lets you click a spike in a metric and jump",
        "# directly to the logs from that exact pod at that time"]),
    sp(10),h2("6.2 — Trace to logs and metrics"),sp(4),
    code(["# Tempo data source configuration",
        "# Links traces -> logs in Loki:",
        "jsonData:",
        "  tracesToLogsV2:",
        "    datasourceUid: loki",
        "    spanStartTimeShift: '-1m'",
        "    spanEndTimeShift: '1m'",
        "    filterByTraceID: true",
        "    filterBySpanID: false",
        "    customQuery: true",
        "    query: '{service_name='${__span.tags['service.name']}'} |= `${__span.traceId}`'",
        "",
        "# Now in Tempo: clicking a span shows the matching Loki logs"]),
    sp(8),tip("The power of the Grafana LGTM stack (Loki, Grafana, Tempo, Mimir) is exemplary correlation — jump from a metric spike to the logs from that pod, then to the trace of the failing request, all in one UI."),
    sp(8),q(["How do you configure Exemplars to link metrics to traces?","What labels must match between Prometheus and Loki for correlation to work?","How do you set up trace context propagation in your application?"])]
    s+=divider()

    s.append(exo("7","Grafana OnCall & Incident Response","20 min","Intermediate"))
    s+=[h2("7.1 — On-call schedules"),sp(4),
    code(["# Grafana OnCall is the on-call management layer",
        "# Install via Helm:",
        "helm install oncall grafana/oncall \\",
        "  --namespace monitoring \\",
        "  --set base_url=https://grafana.example.com",
        "",
        "# Configure in Grafana: Alerting > OnCall > Schedules",
        "# - Create rotation schedules (weekly, follow-the-sun)",
        "# - Set escalation chains (Level 1 Slack -> Level 2 PagerDuty)",
        "# - Integrate with Slack, Teams, PagerDuty, Opsgenie"]),
    sp(8),info("Grafana OnCall (open source) handles on-call rotations, escalation policies, and alert routing. It integrates with Grafana Unified Alerting to form a complete incident management platform without needing PagerDuty."),
    sp(8),q(["What is the difference between Grafana OnCall and PagerDuty?","How do you set up a follow-the-sun rotation?","How do you acknowledge and resolve an alert from Slack?"])]
    s+=divider()

    s.append(exo("8","Production Best Practices","20 min","Advanced"))
    s+=[h2("8.1 — Grafana production checklist"),sp(4)]
    for t in ["Use a dedicated database (PostgreSQL) — not the default SQLite in prod","Enable LDAP/OAuth (GitHub, Google, Okta) — disable basic auth in prod","Provision all dashboards and data sources as code — never click-ops in prod","Set up dashboard folders and permissions per team","Enable Grafana image renderer for PDF/PNG report generation","Use Grafana Mimir for horizontally scalable long-term metrics storage","Monitor Grafana itself: grafana_http_request_duration_seconds, grafana_stat_totals_dashboard"]:
        s.append(bullet(t))
    s+=[sp(10),h2("8.2 — Backup strategy"),sp(4),
    code(["# Export all dashboards via API",
        "curl -s http://admin:$PASS@localhost:3000/api/dashboards/home | jq .",
        "",
        "# Export specific dashboard",
        "curl http://admin:$PASS@localhost:3000/api/dashboards/uid/my-dashboard-uid",
        "",
        "# Store dashboards in Git and provision via ConfigMap",
        "kubectl create configmap grafana-dashboards \\",
        "  --from-file=dashboards/ \\",
        "  -n monitoring"]),
    sp(8),warn("SQLite (Grafana's default) is not suitable for production. Use PostgreSQL for Grafana's own state storage (dashboards, users, alerts). Without a proper database, dashboard changes can be lost on pod restart."),
    sp(8),q(["How do you migrate Grafana from SQLite to PostgreSQL?","What is Grafana Mimir and when should you use it instead of Prometheus?","How do you set up SAML SSO for Grafana Enterprise?"])]
    s.append(pb())

    s+=[h1("Appendix — Quick Reference"),sp(6),h2("Key Grafana URLs"),sp(6)]
    s.append(tbl(["Path","Description"],[
        ["/dashboards","Dashboard browser"],
        ["/alerting/list","All alert rules"],
        ["/explore","Ad-hoc metric, log and trace exploration"],
        ["/connections/datasources","Data source management"],
        ["/admin/users","User and team management"],
        ["/api/dashboards/db","POST: import a dashboard via API"],
        ["/api/dashboards/uid/{uid}","GET: export a dashboard by UID"],
        ["/api/health","Health check endpoint"],
    ],[150,349]))
    s+=[sp(14),h2("Useful environment variables"),sp(6)]
    s.append(tbl(["Variable","Description"],[
        ["GF_SECURITY_ADMIN_PASSWORD","Initial admin password"],
        ["GF_DATABASE_TYPE","Database type: sqlite3 (default), postgres, mysql"],
        ["GF_DATABASE_URL","Database connection string for postgres"],
        ["GF_AUTH_GITHUB_ENABLED","Enable GitHub OAuth"],
        ["GF_SERVER_ROOT_URL","Public URL (required for OAuth callbacks)"],
        ["GF_PATHS_PROVISIONING","Path to provisioning config directory"],
    ],[200,299]))
    s+=[sp(14),info("Official docs: https://grafana.com/docs/grafana/latest  |  Dashboards: https://grafana.com/grafana/dashboards  |  Alloy: https://grafana.com/docs/alloy/latest")]
    return s

build_pdf("/mnt/user-data/outputs/Grafana_Essential_Training.pdf",
    THEMES["grafana"],
    dict(topics=[("01","Installation & Data Sources"),("02","Building Dashboards"),("03","Unified Alerting"),("04","Grafana Alloy Pipeline"),("05","Dashboards as Code"),("06","Correlating Metrics Logs & Traces"),("07","OnCall & Incident Response"),("08","Production Best Practices")],
         subtitle_line="Dashboards · Alerting · Alloy · Traces · Correlation",
         footer_right="Grafana v11 | Alloy | kube-prometheus-stack"),
    dict(skills=["Deploy Grafana and configure Prometheus, Loki and Tempo data sources","Build dynamic dashboards with variables, links and community imports","Set up Unified Alerting with contact points and notification policies","Configure Grafana Alloy to collect metrics, logs and traces","Manage dashboards as code with Grafonnet and Git provisioning","Correlate metrics, logs and traces in a single workflow","Set up Grafana OnCall for on-call rotation management","Harden Grafana for production with PostgreSQL and OAuth"],
         prereqs=["Prometheus basics","Kubernetes & Helm","Basic observability concepts"],
         stats_vals=[("4h","Duration",THEMES["grafana"]['p']),("8","Exercises",TEAL),("v11","Grafana",AMBER)],
         tagline="See everything. Understand anything. Act immediately.",
         tagline2="Grafana — The open observability platform",
         footer_url="https://grafana.com/docs"),
    grafana_content)

# ═══════════════════════════════════════════════════════════════════════════════
# GUIDE 3 — LOKI + OpenTelemetry
# ═══════════════════════════════════════════════════════════════════════════════
def loki_content(h):
    sp=h['sp']; pb=h['pb']; h1=h['h1']; h2=h['h2']; body=h['body']
    bullet=h['bullet']; code=h['code']; info=h['info']; warn=h['warn']
    tip=h['tip']; q=h['q']; divider=h['divider']; exo=h['exo']; tbl=h['tbl']
    s=[]
    s+=[h1("Introduction to Loki & OpenTelemetry"),sp(4)]
    s.append(body("Grafana Loki v3.6 is a horizontally-scalable log aggregation system inspired by Prometheus. Unlike Elasticsearch, Loki does not index the content of logs — it indexes only labels, making it extremely cost-efficient. OpenTelemetry (OTel) is the CNCF standard for collecting metrics, logs, and traces — Loki v3 added native OTLP ingestion, making OTel the recommended pipeline for all telemetry data in 2026."))
    s+=[sp(10),h2("The Observability Stack (LGTM)"),sp(6)]
    s.append(tbl(["Component","Role","Ingests from"],[
        ["Loki v3.6","Log aggregation and querying","Alloy, OTel Collector, Promtail"],
        ["Grafana v11","Visualization and alerting","Loki, Prometheus, Tempo"],
        ["Tempo v2.x","Distributed tracing backend","OTel Collector, Alloy"],
        ["Mimir","Scalable Prometheus-compatible metrics","Prometheus (remote write)"],
        ["OTel Collector","Telemetry pipeline — receive, process, export","Apps via OTLP"],
        ["Grafana Alloy","Unified agent — replaces Promtail/Agent","Kubernetes pods, hosts"],
    ],[140,190,169]))
    s+=[sp(12),h2("Loki v3 key features"),sp(6)]
    s.append(tbl(["Feature","Description"],[
        ["Native OTLP ingestion","Receive OTel logs directly — no Loki Exporter needed"],
        ["Structured metadata","OTel attributes stored as structured metadata — fast filtering"],
        ["Bloom filters","Pre-filter log chunks before loading — massive query speedup"],
        ["TSDB index","Better index performance vs BoltDB for large-scale deployments"],
        ["LogQL v2","Pattern matching, metric queries, JSON/logfmt parsing"],
        ["Ruler","Alerting and recording rules on log data (like Prometheus rules)"],
    ],[160,339]))
    s.append(pb())

    s.append(exo("1","Deploy Loki with Helm","25 min","Easy"))
    s+=[h2("1.1 — Install Loki in simple-scalable mode"),sp(4),
    code(["helm repo add grafana https://grafana.github.io/helm-charts",
        "helm repo update",
        "",
        "# Simple scalable mode: read + write + backend components",
        "helm install loki grafana/loki \\",
        "  --namespace monitoring \\",
        "  --set loki.auth_enabled=false \\",
        "  --set loki.commonConfig.replication_factor=1 \\",
        "  --set loki.storage.type=filesystem \\",
        "  --set singleBinary.replicas=1 \\",
        "  --wait"]),
    sp(10),h2("1.2 — Deploy Grafana Alloy to collect pod logs"),sp(4),
    code(["helm install alloy grafana/alloy \\",
        "  --namespace monitoring \\",
        "  -f alloy-values.yaml"]),
    sp(6),
    code(["# alloy-values.yaml",
        "alloy:",
        "  configMap:",
        "    content: |",
        "      discovery.kubernetes \"pods\" {",
        "        role = \"pod\"",
        "      }",
        "",
        "      loki.source.kubernetes \"pods\" {",
        "        targets    = discovery.kubernetes.pods.targets",
        "        forward_to = [loki.write.default.receiver]",
        "      }",
        "",
        "      loki.write \"default\" {",
        "        endpoint {",
        "          url = \"http://loki-gateway.monitoring/loki/api/v1/push\"",
        "        }",
        "      }"]),
    sp(8),info("For production use S3 or GCS as Loki's storage backend instead of filesystem. Filesystem storage is single-node only and not suitable for multi-replica deployments."),
    sp(8),q(["What is the difference between Loki monolithic, simple-scalable, and microservices mode?","How does Alloy determine which pods to collect logs from?","How do you verify Loki is receiving logs?"])]
    s+=divider()

    s.append(exo("2","LogQL — Log Query Language","40 min","Intermediate"))
    s+=[h2("2.1 — Stream selectors and filter expressions"),sp(4),
    code(["# Stream selector — select which log streams to query",
        "{namespace='production', pod=~'api-.*'}",
        "",
        "# Filter: contain the string 'error'",
        "{namespace='production'} |= 'error'",
        "",
        "# Filter: does NOT contain 'health'",
        "{namespace='production'} != 'health'",
        "",
        "# Regex filter",
        "{namespace='production'} |~ 'ERR|WARN|CRIT'",
        "",
        "# Parse JSON logs",
        "{namespace='production'} | json | level='error'",
        "",
        "# Parse logfmt",
        "{namespace='production'} | logfmt | duration > 500ms",
        "",
        "# Extract a field and filter on it",
        "{namespace='production'} | json | line_format '{{.msg}} took {{.duration}}'"]),
    sp(10),h2("2.2 — Metric queries (LogQL)"),sp(4),
    code(["# Count log lines per minute",
        "count_over_time({namespace='production'}[1m])",
        "",
        "# Rate of error logs per second",
        "rate({namespace='production'} |= 'error' [5m])",
        "",
        "# 99th percentile response time from logs",
        "quantile_over_time(0.99,",
        "  {namespace='production'}",
        "  | logfmt",
        "  | unwrap duration [5m]) by (pod)",
        "",
        "# Bytes received per pod",
        "sum by (pod) (bytes_over_time({namespace='production'}[5m]))"]),
    sp(8),tip("Use 'sum by (pod)' in metric queries to aggregate per service. Without grouping, all pods are merged into a single time series, making it impossible to identify which pod is generating errors."),
    sp(8),q(["What is the difference between '|=' and '|~' in LogQL?","What does 'unwrap' do in a LogQL metric query?","How do you search across multiple namespaces in one query?"])]
    s+=divider()

    s.append(exo("3","Labels & Structured Logging","25 min","Intermediate"))
    s+=[h2("3.1 — Loki label best practices"),sp(4),
    tbl(["Label strategy","Good","Bad"],[
        ["Cardinality","Low: namespace, pod, container, app","High: request_id, user_id, IP address"],
        ["Source","Static: cluster, environment, region","Dynamic: timestamp values"],
        ["Granularity","Service-level: app=nginx","Instance-level: ip=10.0.0.1"],
    ],[120,160,219]),
    sp(10),
    code(["# Good Alloy config — only static labels",
        "loki.source.kubernetes \"pods\" {",
        "  targets    = discovery.kubernetes.pods.targets",
        "  forward_to = [loki.process.add_labels.receiver]",
        "}",
        "",
        "loki.process \"add_labels\" {",
        "  stage.static_labels {",
        "    values = {",
        "      cluster     = \"production-eu\",",
        "      environment = \"production\",",
        "    }",
        "  }",
        "  forward_to = [loki.write.default.receiver]",
        "}"]),
    sp(8),warn("Do NOT use request IDs, user IDs, or any high-cardinality values as Loki labels. Each unique label combination creates a new stream — too many streams will overwhelm Loki's index and degrade performance severely."),
    sp(8),q(["How many active streams should a healthy Loki have?","How do you add Kubernetes metadata (pod name, namespace) as labels automatically?","What is the difference between a label and structured metadata in Loki v3?"])]
    s+=divider()

    s.append(exo("4","OpenTelemetry Collector","35 min","Intermediate"))
    s+=[h2("4.1 — Install the OTel Collector"),sp(4),
    code(["helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts",
        "helm repo update",
        "",
        "helm install otel-collector open-telemetry/opentelemetry-collector \\",
        "  --namespace monitoring \\",
        "  -f otel-collector-values.yaml"]),
    sp(10),h2("4.2 — OTel Collector config — receivers & processors"),sp(4),
    code(["# otel-collector-config.yaml (part 1)",
        "receivers:",
        "  otlp:",
        "    protocols:",
        "      grpc:  { endpoint: 0.0.0.0:4317 }",
        "      http:  { endpoint: 0.0.0.0:4318 }",
        "  prometheus:",
        "    config:",
        "      scrape_configs:",
        "      - job_name: myapp",
        "        static_configs:",
        "        - targets: ['myapp:8080']",
        "",
        "processors:",
        "  batch:",
        "    timeout: 5s",
        "    send_batch_size: 1000",
        "  memory_limiter:",
        "    limit_mib: 512",
        "    spike_limit_mib: 128",
        "  resourcedetection:",
        "    detectors: [k8snode, k8s_cluster]"]),
    sp(8),h2("4.3 — OTel Collector config — exporters & pipelines"),sp(4),
    code(["# otel-collector-config.yaml (part 2)",
        "exporters:",
        "  prometheusremotewrite:",
        "    endpoint: http://prometheus:9090/api/v1/write",
        "  otlphttp/loki:",
        "    endpoint: http://loki-gateway.monitoring:80/otlp",
        "  otlp/tempo:",
        "    endpoint: http://tempo.monitoring:4317",
        "",
        "service:",
        "  pipelines:",
        "    metrics:",
        "      receivers: [otlp, prometheus]",
        "      processors: [memory_limiter, batch]",
        "      exporters: [prometheusremotewrite]",
        "    logs:",
        "      receivers: [otlp]",
        "      processors: [memory_limiter, batch, resourcedetection]",
        "      exporters: [otlphttp/loki]",
        "    traces:",
        "      receivers: [otlp]",
        "      processors: [memory_limiter, batch]",
        "      exporters: [otlp/tempo]"]),
    sp(8),info("The OTel Collector's memory_limiter processor is essential in production. Without it, a burst of telemetry data can cause the collector to OOM. Set limit_mib to 80% of the container's memory limit."),
    sp(8),q(["What is the difference between the OTel Collector and Grafana Alloy?","How do you add sampling to reduce trace volume?","What is the 'resourcedetection' processor and why is it useful?"])]
    s+=divider()

    s.append(exo("5","Instrument Your Application","30 min","Intermediate"))
    s+=[h2("5.1 — Auto-instrumentation with OTel Operator"),sp(4),
    code(["# Install OTel Operator",
        "helm install opentelemetry-operator open-telemetry/opentelemetry-operator \\",
        "  --namespace monitoring",
        "",
        "# Create an Instrumentation CR — auto-instruments matching pods",
        "apiVersion: opentelemetry.io/v1alpha1",
        "kind: Instrumentation",
        "metadata:",
        "  name: auto-instrumentation",
        "  namespace: production",
        "spec:",
        "  exporter:",
        "    endpoint: http://otel-collector.monitoring:4317",
        "  propagators: [tracecontext, baggage, b3]",
        "  sampler:",
        "    type: parentbased_traceidratio",
        "    argument: '0.1'  # 10% sampling",
        "",
        "# Annotate pods to auto-instrument them",
        "kubectl annotate deployment myapp \\",
        "  instrumentation.opentelemetry.io/inject-nodejs=auto-instrumentation \\",
        "  -n production"]),
    sp(10),h2("5.2 — Manual SDK instrumentation (Node.js)"),sp(4),
    code(["// tracing.js",
        "const { NodeSDK } = require('@opentelemetry/sdk-node');",
        "const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');",
        "const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');",
        "",
        "const sdk = new NodeSDK({",
        "  traceExporter: new OTLPTraceExporter({",
        "    url: 'http://otel-collector.monitoring:4317',",
        "  }),",
        "  instrumentations: [getNodeAutoInstrumentations()],",
        "  serviceName: 'my-api',",
        "  serviceVersion: '1.0.0',",
        "});",
        "",
        "sdk.start();"]),
    sp(8),tip("Use the OTel Operator with auto-instrumentation for zero-code observability. It injects the OTel SDK as an init container — no application code changes needed. Supports Node.js, Python, Java, .NET, Go, PHP."),
    sp(8),q(["What languages does OTel auto-instrumentation support?","What is the difference between head-based and tail-based sampling?","How do you add custom attributes (spans) to a trace?"])]
    s+=divider()

    s.append(exo("6","Distributed Tracing with Tempo","25 min","Intermediate"))
    s+=[h2("6.1 — Deploy Tempo"),sp(4),
    code(["helm install tempo grafana/tempo-distributed \\",
        "  --namespace monitoring \\",
        "  --set storage.trace.backend=local \\",
        "  --set storage.trace.local.path=/var/tempo/traces \\",
        "  --set global.clusterDomain=cluster.local"]),
    sp(10),h2("6.2 — Query traces in Grafana Explore"),sp(4),
    code(["# TraceQL — query language for Tempo",
        "",
        "# Find all traces with an error",
        "{ status=error }",
        "",
        "# Find slow requests (>1s) for a specific service",
        "{ .service.name='api' && duration > 1s }",
        "",
        "# Find traces where a specific DB call is slow",
        "{ span.db.operation='SELECT' && span.duration > 100ms }",
        "",
        "# Find traces by trace ID",
        "{ traceID='4bf92f3577b34da6a3ce929d0e0e4736' }",
        "",
        "# Aggregate: P99 latency by service",
        "{ } | rate() by (.service.name)",
        "{ } | quantile_over_time(duration, 0.99) by (.service.name)"]),
    sp(8),info("Tempo is intentionally simple — it stores traces and retrieves them by ID. For trace search and aggregation, use TraceQL in Grafana Explore. Tempo integrates with Loki for log correlation and Prometheus Exemplars for metric-to-trace linking."),
    sp(8),q(["What is an Exemplar and how does it link a metric data point to a trace?","What is the difference between Tempo and Jaeger?","How do you configure tail-based sampling in Tempo?"])]
    s+=divider()

    s.append(exo("7","Log Alerting with Loki Ruler","20 min","Intermediate"))
    s+=[h2("7.1 — Alerting rules on log data"),sp(4),
    code(["# Loki ruler config (via Helm values)",
        "loki:",
        "  rulerConfig:",
        "    storage:",
        "      type: local",
        "      local:",
        "        directory: /rules",
        "    rule_path: /tmp/rules",
        "    alertmanager_url: http://alertmanager.monitoring:9093",
        "    ring:",
        "      kvstore:",
        "        store: inmemory",
        "",
        "# Alert rule YAML file",
        "groups:",
        "- name: log-alerts",
        "  rules:",
        "  - alert: TooManyErrorLogs",
        "    expr: |",
        "      sum(rate(",
        "        {namespace='production'} |= 'ERROR' [5m]",
        "      )) by (pod) > 10",
        "    for: 2m",
        "    labels:",
        "      severity: warning",
        "    annotations:",
        "      summary: 'Pod {{ $labels.pod }} producing too many errors'"]),
    sp(8),tip("Loki ruler alerts are perfect for patterns that are only visible in logs — application-level errors, specific exception types, or business events. Pair with Prometheus alerts for a complete alerting strategy."),
    sp(8),q(["How do you test a Loki ruler alert before deploying it?","What is the difference between Loki alerting and Grafana Unified Alerting on Loki?","How do you set up recording rules in Loki to pre-compute expensive LogQL queries?"])]
    s+=divider()

    s.append(exo("8","Production Best Practices","20 min","Advanced"))
    s+=[h2("8.1 — Loki production checklist"),sp(4)]
    for t in ["Use S3 or GCS for storage — never filesystem in production","Enable multi-tenancy (auth_enabled: true) for team isolation","Set retention_period per tenant using per-tenant overrides","Deploy in simple-scalable or microservices mode for HA","Use TSDB index (default in v3) — not BoltDB or boltdb-shipper","Monitor loki_ingester_streams_created_total — high cardinality = streams exploding","Enable bloom filters for large-scale deployments (reduces query I/O by 80%)+"]:
        s.append(bullet(t))
    s+=[sp(10),h2("8.2 — OTel Collector production tips"),sp(4)]
    for t in ["Always set memory_limiter as the first processor in every pipeline","Use batch processor to reduce network overhead — tune send_batch_size","Deploy as a DaemonSet for node-local collection, Gateway for aggregation","Pin the OTel Collector image version — never use 'latest'","Monitor the Collector itself: otelcol_receiver_accepted_spans, otelcol_exporter_queue_size","Use tail_sampling processor to keep only interesting traces (errors, slow requests)"]:
        s.append(bullet(t))
    s+=[sp(8),warn("Never expose the OTel Collector's OTLP receiver (port 4317/4318) outside the cluster without authentication. Any process that can reach it can flood your Loki/Tempo with data, causing storage and cost issues."),
    sp(8),q(["How do you implement tail-based sampling to keep only error traces?","What is the maximum recommended cardinality for Loki labels in production?","How do you migrate from Promtail to Grafana Alloy?"])]
    s.append(pb())

    s+=[h1("Appendix — Quick Reference"),sp(6),h2("LogQL quick reference"),sp(6)]
    s.append(tbl(["Expression","Description"],[
        ["{app='nginx'} |= 'error'","Logs from nginx containing 'error'"],
        ["{namespace='prod'} | json","Parse JSON log lines"],
        ["{namespace='prod'} | logfmt","Parse logfmt log lines"],
        ["{namespace='prod'} | pattern '<_> level=<level> <_>'","Extract fields by pattern"],
        ["rate({app='api'} |= 'error' [5m])","Error log rate per second"],
        ["count_over_time({app='api'}[1h])","Total log lines in the last hour"],
        ["sum by (pod) (rate({ns='prod'}[5m]))","Log rate per pod"],
        ["{app='api'} | json | status >= 500","Filter on extracted JSON field"],
        ["{app='api'} | json | line_format '{{.msg}}'","Reformat log output"],
    ],[230,269]))
    s+=[sp(14),h2("OTel Collector ports"),sp(6)]
    s.append(tbl(["Port","Protocol","Usage"],[
        ["4317","gRPC","OTLP gRPC receiver (metrics, logs, traces)"],
        ["4318","HTTP","OTLP HTTP receiver (metrics, logs, traces)"],
        ["8888","HTTP","Collector self-metrics (Prometheus format)"],
        ["8889","HTTP","Prometheus exporter (scraped by Prometheus)"],
        ["13133","HTTP","Health check endpoint"],
        ["55679","HTTP","zPages debugging UI"],
    ],[80,80,339]))
    s+=[sp(14),info("Loki docs: https://grafana.com/docs/loki/latest  |  OTel: https://opentelemetry.io/docs  |  Tempo: https://grafana.com/docs/tempo/latest")]
    return s

build_pdf("/mnt/user-data/outputs/Loki_OpenTelemetry_Essential_Training.pdf",
    THEMES["loki"],
    dict(topics=[("01","Deploy Loki with Helm"),("02","LogQL Query Language"),("03","Labels & Structured Logging"),("04","OpenTelemetry Collector"),("05","Instrument Your Application"),("06","Distributed Tracing with Tempo"),("07","Log Alerting with Loki Ruler"),("08","Production Best Practices")],
         subtitle_line="LogQL · OTel Collector · Traces · Alloy · Tempo",
         footer_right="Loki v3.6 | OTel Collector | Tempo v2 | Alloy",
         difficulty="Intermediate"),
    dict(skills=["Deploy Loki v3 on Kubernetes with Grafana Alloy for log collection","Write LogQL queries to filter, parse and aggregate log streams","Design low-cardinality label schemas for Loki at scale","Configure the OTel Collector to route metrics, logs and traces","Auto-instrument applications with the OTel Operator (zero code changes)","Query distributed traces with TraceQL in Tempo","Create alerting rules on log data with the Loki Ruler","Harden Loki and OTel Collector for production deployments"],
         prereqs=["Kubernetes basics","Grafana & Prometheus","Basic logging concepts"],
         stats_vals=[("4h","Duration",THEMES["loki"]['p']),("8","Exercises",TEAL),("v3.6","Loki",AMBER)],
         tagline="Logs, metrics and traces. One stack. Full observability.",
         tagline2="Loki + OpenTelemetry — The modern observability pipeline",
         footer_url="https://grafana.com/docs/loki/latest"),
    loki_content)

print("\n✅ All 3 observability guides generated!")
