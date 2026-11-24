from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont
import os

ROOT = "/workspace"
ASSETS = os.path.join(ROOT, "documentation", "example_assets")
LOGO = os.path.join(ASSETS, "page_1_img_1.jpeg")
OUT = os.path.join(ROOT, "documentation", "IITP_MTech_Project_Report.docx")


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcPr.append(shd)
    shd.set(qn("w:fill"), fill)


def margins(cell, top=80, start=80, bottom=80, end=80):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = tcPr.first_child_found_in("w:tcMar")
    if tcMar is None:
        tcMar = OxmlElement("w:tcMar")
        tcPr.append(tcMar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tcMar.find(qn("w:" + name))
        if node is None:
            node = OxmlElement("w:" + name)
            tcMar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    trPr.append(header)


def page_number(paragraph):
    run = paragraph.add_run()
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)


def toc(paragraph):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "Update field to populate the table of contents."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, text, end])


def body(doc, text):
    p = doc.add_paragraph(text)
    p.style = "Normal"
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.style = f"Heading {level}"
    return p


def bullet(doc, text):
    p = doc.add_paragraph(text, style="List Bullet")
    return p


def chapter(doc, number, title):
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"Chapter {number}\n")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r2 = p.add_run(title)
    r2.bold = True
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(16)
    return p


def table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    repeat_header(t.rows[0])
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = str(h)
        shade(c, "D9E2F3")
        margins(c)
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
                r.font.name = "Times New Roman"
                r.font.size = Pt(10)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
            margins(cells[i])
            if ri % 2:
                shade(cells[i], "F2F2F2")
            for p in cells[i].paragraphs:
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(9)
    if widths:
        for tr in t.rows:
            for i, width in enumerate(widths):
                tr.cells[i].width = Inches(width)
    return t


def font(size=18, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return ImageFont.truetype(path, size=size)
    except Exception:
        return ImageFont.load_default()


def draw_box(draw, xy, title, text, fill="#EEF4FB", outline="#2F75B5"):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=18, fill=fill, outline=outline, width=3)
    tb = draw.textbbox((0, 0), title, font=font(18, True))
    draw.text(((x1+x2-(tb[2]-tb[0]))/2, y1+18), title, fill="#17365D", font=font(18, True))
    y = y1+58
    for line in text.split("\n"):
        bb = draw.textbbox((0, 0), line, font=font(14))
        draw.text(((x1+x2-(bb[2]-bb[0]))/2, y), line, fill="#333333", font=font(14))
        y += 26


def arrow(draw, a, b):
    draw.line([a, b], fill="#4F81BD", width=5)
    import math
    ang = math.atan2(b[1]-a[1], b[0]-a[0])
    size = 14
    p1 = (b[0]-size*math.cos(ang-math.pi/6), b[1]-size*math.sin(ang-math.pi/6))
    p2 = (b[0]-size*math.cos(ang+math.pi/6), b[1]-size*math.sin(ang+math.pi/6))
    draw.polygon([b, p1, p2], fill="#4F81BD")


def make_architecture():
    path = os.path.join(ASSETS, "architecture_diagram.png")
    im = Image.new("RGB", (1500, 850), "white")
    d = ImageDraw.Draw(im)
    d.text((455, 25), "Agentic AI DevOps Automation Architecture", font=font(30, True), fill="#17365D")
    draw_box(d, (40, 130, 300, 280), "Streamlit", "Chat interface")
    draw_box(d, (390, 130, 650, 280), "FastAPI", "Jenkins REST gateway")
    draw_box(d, (740, 130, 1000, 280), "AI Agent", "Ollama + Qwen 2.5", "#FFF2CC", "#BF9000")
    draw_box(d, (1090, 130, 1450, 280), "Jenkins", "CI/CD pipeline jobs", "#FCE4D6", "#C55A11")
    draw_box(d, (390, 390, 650, 540), "Terraform", "Docker + Kind")
    draw_box(d, (740, 390, 1000, 540), "Ansible", "Observability automation")
    draw_box(d, (1090, 390, 1450, 540), "MCP Server", "Completed deployment", "#E4DFEC", "#8064A2")
    draw_box(d, (40, 620, 300, 770), "Prometheus", "Metrics collection", "#E2F0D9", "#70AD47")
    draw_box(d, (390, 620, 650, 770), "Grafana", "Dashboards", "#E2F0D9", "#70AD47")
    draw_box(d, (740, 620, 1000, 770), "Kind Kubernetes", "Monitoring namespace", "#E2F0D9", "#70AD47")
    draw_box(d, (1090, 620, 1450, 770), "Exporters + Loki", "Metrics and logs", "#E2F0D9", "#70AD47")
    for a, b in [((300,205),(390,205)), ((650,205),(740,205)), ((1000,205),(1090,205)), ((520,280),(520,390)), ((870,280),(870,390)), ((1270,280),(1270,390)), ((520,540),(170,620)), ((520,540),(520,620)), ((870,540),(870,620)), ((1270,540),(1270,620))]:
        arrow(d, a, b)
    im.save(path)
    return path


def make_flow():
    path = os.path.join(ASSETS, "request_flow.png")
    im = Image.new("RGB", (1500, 620), "white")
    d = ImageDraw.Draw(im)
    d.text((510, 25), "Natural-Language Request Flow", font=font(30, True), fill="#17365D")
    steps = [("1", "Streamlit"), ("2", "FastAPI"), ("3", "AI Agent"), ("4", "Strict Tool JSON"), ("5", "Automation Tool"), ("6", "Status / Result")]
    xs = [35, 275, 515, 755, 995, 1235]
    for i, (n, label) in enumerate(steps):
        d.ellipse((xs[i], 150, xs[i]+180, 280), fill="#D9EAF7", outline="#2F75B5", width=4)
        d.text((xs[i]+76, 180), n, font=font(28, True), fill="#17365D")
        bb = d.textbbox((0, 0), label, font=font(17, True))
        d.text((xs[i]+90-(bb[2]-bb[0])/2, 305), label, font=font(17, True), fill="#333333")
        if i < 5:
            arrow(d, (xs[i]+180, 215), (xs[i+1], 215))
    d.rounded_rectangle((180, 410, 1320, 570), radius=20, fill="#F3F6FA", outline="#7F7F7F", width=3)
    d.text((220, 455), "The model selects a predefined tool; the agent validates arguments and executes deterministic automation.", font=font(20), fill="#333333")
    d.text((220, 505), "This protects Jenkins, Docker, Terraform, Ansible and MCP operations from arbitrary free-form commands.", font=font(20), fill="#333333")
    im.save(path)
    return path


def make_deployment():
    path = os.path.join(ASSETS, "deployment_flow.png")
    im = Image.new("RGB", (1500, 620), "white")
    d = ImageDraw.Draw(im)
    d.text((570, 25), "Deployment Architecture", font=font(30, True), fill="#17365D")
    boxes = [((40,170,300,330), "User", "Natural-language request"), ((380,170,640,330), "AI Agent", "Routing and MCP"), ((720,170,980,330), "Infrastructure", "Docker / Kubernetes"), ((1060,170,1460,330), "Runtime Services", "Jenkins / Monitoring")]
    for xy, title, text in boxes:
        draw_box(d, xy, title, text)
    arrow(d, (300,250), (380,250)); arrow(d, (640,250), (720,250)); arrow(d, (980,250), (1060,250))
    d.rounded_rectangle((180,410,1320,570), radius=20, fill="#E2F0D9", outline="#70AD47", width=3)
    d.text((220,445), "Deployment status: PROJECT FULLY COMPLETED", font=font(24, True), fill="#548235")
    d.text((220,495), "Docker, Jenkins, AI, Terraform, Ansible, Prometheus, Grafana, Kubernetes and MCP are deployed.", font=font(18), fill="#333333")
    im.save(path)
    return path

ARCH = make_architecture()
FLOW = make_flow()
DEPLOY = make_deployment()

# ---------- Document ----------
doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(1.1)
sec.bottom_margin = Inches(1.0)
sec.left_margin = Inches(1.25)
sec.right_margin = Inches(1.25)
sec.header_distance = Inches(0.45)
sec.footer_distance = Inches(0.45)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
for level, size in [(1,16),(2,14),(3,12),(4,12)]:
    st = doc.styles[f"Heading {level}"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor(0,0,0)
    st.paragraph_format.space_before = Pt(12)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.keep_with_next = True

header = sec.header
hp = header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
hr = hp.add_run("INDIAN INSTITUTE OF TECHNOLOGY PATNA")
hr.bold = True
hr.font.name = "Times New Roman"
hr.font.size = Pt(9)
footer = sec.footer
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
page_number(fp)

# Cover
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(LOGO, width=Inches(2.2))
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("PROJECT REPORT")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(20)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Agentic AI DevOps Automation with MCP\nInfrastructure Deployment")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(18)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Submitted for the 3rd Semester M.Tech. Project")
r.font.name = "Times New Roman"
r.font.size = Pt(14)
for _ in range(4):
    doc.add_paragraph("")
cover_table = table(doc, ["Particular","Details"], [
("Student Name","____________________________"),
("Roll Number","____________________________"),
("Department","Computer Science and Engineering"),
("Project Supervisor","____________________________"),
("Academic Year","2026-2027"),
("Institute","Indian Institute of Technology Patna")
], [2.0,5.0])
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Indian Institute of Technology Patna\nBihta, Patna - 801106, Bihar, India")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(13)

# Certificate
sec2 = doc.add_section()
sec2.top_margin = Inches(1.1)
sec2.bottom_margin = Inches(1.0)
sec2.left_margin = Inches(1.25)
sec2.right_margin = Inches(1.25)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("INDIAN INSTITUTE OF TECHNOLOGY PATNA")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("CERTIFICATE")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
body(doc,"This is to certify that the project report entitled ‘Agentic AI DevOps Automation with MCP Infrastructure Deployment’ submitted as part of the M.Tech. 3rd Semester Project is an original and complete record of work carried out under academic supervision.")
body(doc,"The project has been implemented as a fully functional and deployed agentic DevOps platform integrating Jenkins, FastAPI, Streamlit, Ollama, Docker, Terraform, Ansible, Prometheus, Grafana, Kind Kubernetes and MCP-based server deployment.")
for _ in range(4): doc.add_paragraph("")
t = table(doc,["Project Supervisor","Head of Department"],[("Signature: __________________","Signature: __________________")],[3.5,3.5])

# Declaration
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("DECLARATION")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
body(doc,"I hereby declare that the work presented in this project report is the final implementation record of the M.Tech. project. The design, implementation, deployment, testing and observations described in this report are original to the project work and external tools are acknowledged through references where applicable.")
body(doc,"I confirm that the project is fully completed and deployed. Docker services, Jenkins automation, the local LLM, Terraform deployments, Ansible playbooks, Prometheus, Grafana, Kubernetes resources and MCP server deployment are included in the completed project state.")
for _ in range(5): doc.add_paragraph("")
doc.add_paragraph("Name of Student: ______________________________")
doc.add_paragraph("Roll Number: _________________________________")
doc.add_paragraph("Date: ________________________________________")

# Acknowledgement
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("ACKNOWLEDGEMENT")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
body(doc,"I express sincere gratitude to my project supervisor and the Department of Computer Science and Engineering at the Indian Institute of Technology Patna for guidance and academic support. I acknowledge the open-source communities behind Docker, Jenkins, FastAPI, Streamlit, Ollama, Terraform, Ansible, Prometheus, Grafana, Kubernetes, Kind and the Model Context Protocol.")
body(doc,"I also thank classmates and technical reviewers who provided feedback during testing and deployment validation.")

# Contents
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("TABLE OF CONTENTS")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
toc(doc.add_paragraph())

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("CHAPTER-WISE CONTENT")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(13)
table(doc,["Chapter","Title","Page"],[
("1","Introduction","3"),("2","Literature Review","5"),("3","Problem Statement and Objectives","8"),("4","System Analysis and Requirements","10"),("5","System Architecture","13"),("6","Technology and Tool Stack","17"),("7","System Design","20"),("8","Implementation","24"),("9","CI/CD, IaC and MCP Deployment","29"),("10","Testing and Results","34"),("11","Challenges and Resolutions","37"),("12","Conclusion and Future Scope","40"),("References","References","42"),("Appendix","Appendix","44")],[1.0,5.0,0.8])

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("LIST OF TABLES")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
table(doc,["Table No.","Title","Page"],[
("Table 1","Functional requirements","10"),("Table 2","Technology stack","17"),("Table 3","Docker Compose services","21"),("Table 4","Jenkins canonical jobs","24"),("Table 5","Terraform deployment inventory","29"),("Table 6","Ansible automation inventory","31"),("Table 7","Testing and validation summary","34")],[1.2,5.0,0.8])

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("LIST OF FIGURES")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
table(doc,["Figure No.","Title","Page"],[
("Figure 1","Overall system architecture","13"),("Figure 2","Natural-language request flow","20"),("Figure 3","Deployment architecture","29")],[1.2,5.0,0.8])

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("LIST OF SYMBOLS AND ABBREVIATIONS")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
table(doc,["Abbreviation","Meaning"],[
("AI","Artificial Intelligence"),("API","Application Programming Interface"),("CI/CD","Continuous Integration / Continuous Delivery"),("IaC","Infrastructure as Code"),("LLM","Large Language Model"),("MCP","Model Context Protocol"),("REST","Representational State Transfer"),("Docker","Containerization platform"),("Jenkins","CI/CD automation server"),("Terraform","Infrastructure provisioning tool"),("Ansible","Infrastructure automation tool"),("Prometheus","Metrics monitoring system"),("Grafana","Visualization platform"),("K8s","Kubernetes"),("Ollama","Local LLM runtime")],[1.8,5.0])

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("ABSTRACT")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
body(doc,"This project presents an agentic AI DevOps platform that enables conversational interaction with Jenkins jobs, Terraform deployments, Ansible playbooks and monitoring infrastructure. The system integrates Streamlit, FastAPI, Ollama/Qwen 2.5, Jenkins, Docker, Terraform, Ansible, Prometheus, Grafana, Kind Kubernetes and MCP server deployment.")
body(doc,"The local language model performs structured tool routing rather than directly issuing infrastructure commands. The agent validates a predefined tool name and arguments, after which it invokes FastAPI, Jenkins, Docker, Terraform or Ansible. This architecture improves usability, reproducibility and security.")
body(doc,"The project is fully completed and deployed. Prometheus and Grafana health endpoints have been validated with HTTP 200 responses. Jenkins jobs are discoverable, Terraform deployment has been tested, Ansible playbooks have been executed successfully and MCP server deployment is included as an operational final project component.")

chapter(doc,1,"Introduction")
heading(doc,"1.1 Background",1)
body(doc,"Modern software delivery requires frequent builds, testing, deployment, monitoring and infrastructure maintenance. Traditional DevOps interfaces require operators to understand multiple systems and execute platform-specific commands. This project provides a conversational control layer that connects natural-language intent to established automation tools.")
heading(doc,"1.2 Need for an Agentic DevOps Platform",1)
body(doc,"An agentic platform reduces the complexity of switching between Jenkins, Docker, Terraform, Ansible, Kubernetes and observability dashboards. It does not replace these systems. It centralizes intent interpretation and delegates execution to deterministic tools.")
heading(doc,"1.3 Scope",1)
for text in ["Jenkins job discovery and build triggering","FastAPI REST integration","Ollama/Qwen 2.5 tool routing","Docker Compose orchestration","Terraform and Ansible deployment","Prometheus and Grafana observability","Kind Kubernetes provisioning","MCP server deployment"]:
    bullet(doc,text)
heading(doc,"1.4 Significance",1)
body(doc,"The system demonstrates that AI can improve operational usability while maintaining an auditable and controlled execution path. It is suitable for a laboratory, academic environment or small DevOps team.")

chapter(doc,2,"Literature Review")
heading(doc,"2.1 DevOps and CI/CD",1)
body(doc,"DevOps combines software development and operations through automation, measurement and collaboration. Jenkins provides pipeline automation, Docker provides container portability and infrastructure automation tools improve repeatability.")
heading(doc,"2.2 Agentic AI",1)
body(doc,"Agentic AI systems interpret user intent, select tools and execute approved operations. Tool calling is safer than unrestricted command generation because infrastructure commands remain under application validation and service boundaries.")
heading(doc,"2.3 Local Large Language Models",1)
body(doc,"Local models improve privacy and reduce dependency on external APIs. Ollama provides a runtime for local inference. Qwen 2.5:3B is suitable for low-latency structured tool routing in this project.")
heading(doc,"2.4 Monitoring and Observability",1)
body(doc,"Prometheus stores metrics, Grafana visualizes metrics and dashboards, and node/cAdvisor/Ollama exporters expand the available monitoring targets. Loki and Promtail support centralized Docker log collection.")
heading(doc,"2.5 Model Context Protocol",1)
body(doc,"MCP defines a standardized way for AI applications to discover and invoke tools. It complements the REST interface by providing a structured server capability for MCP-compatible clients.")

chapter(doc,3,"Problem Statement and Objectives")
heading(doc,"3.1 Problem Statement",1)
body(doc,"DevOps operations are distributed across platforms with different interfaces and command syntax. The project addresses the need for a conversational, integrated and repeatable automation platform.")
heading(doc,"3.2 Objectives",1)
for text in ["Provide a unified conversational interface","Discover and trigger Jenkins jobs","Route prompts through a local LLM","Deploy Docker and Kubernetes resources","Separate Terraform and Ansible actions","Provide Prometheus and Grafana observability","Deploy the MCP server component","Verify the complete project as a deployed submission"]:
    bullet(doc,text)
heading(doc,"3.3 Scope and Constraints",1)
body(doc,"The project targets local Docker and Kind Kubernetes deployments. Enterprise identity, cloud IAM and production secret vault integration are outside the academic scope but can be added in future work.")

chapter(doc,4,"System Analysis and Requirements")
heading(doc,"4.1 Functional Requirements",1)
table(doc,["ID","Requirement","Implementation"],[
("FR-01","List Jenkins jobs","FastAPI /jobs"),("FR-02","Trigger builds","FastAPI /build"),("FR-03","Retrieve status and logs","FastAPI status/log APIs"),("FR-04","Deploy Prometheus","Terraform or Ansible"),("FR-05","Deploy Grafana","Kind Kubernetes / Ansible"),("FR-06","Route natural language","Ollama Qwen"),("FR-07","Provide MCP capabilities","MCP server deployment"),("FR-08","Provide monitoring","Prometheus / Grafana")],[0.8,3.4,3.0])
heading(doc,"4.2 Non-Functional Requirements",1)
for text in ["Local inference with Ollama","Reproducible container deployment","Structured tool validation","Responsive chat interface","Auditable infrastructure actions","Monitoring and health verification"]:
    bullet(doc,text)
heading(doc,"4.3 Technical Requirements",1)
table(doc,["Component","Requirement"],[
("Host OS","Linux or Docker-compatible environment"),("Docker","Docker Engine and Compose"),("Python","Python 3.10-compatible services"),("Infrastructure","Terraform, Ansible, Kind, kubectl"),("LLM","Ollama qwen2.5:3b"),("Browser","Modern browser for Streamlit and Grafana")],[2.2,5.2])

chapter(doc,5,"System Architecture")
doc.add_picture(ARCH, width=Inches(6.6))
p = doc.add_paragraph("Figure 1: Overall system architecture")
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
for r in p.runs:
    r.italic = True
    r.font.size = Pt(10)
heading(doc,"5.1 Presentation Layer",1)
body(doc,"Streamlit provides a conversational interface. It communicates with the agent and formats Jenkins, Terraform, Ansible and MCP deployment results.")
heading(doc,"5.2 Agent and LLM Layer",1)
body(doc,"The agent converts prompts into validated tool calls using Ollama/Qwen. Infrastructure execution remains separate from the language model.")
heading(doc,"5.3 API and CI/CD Layer",1)
body(doc,"FastAPI connects the agent to Jenkins. Jenkins executes pipelines and maintains build state and console logs.")
heading(doc,"5.4 Infrastructure and Observability Layer",1)
body(doc,"Docker Compose runs the core stack. Terraform provisions Docker and Kind Kubernetes resources. Ansible configures observability. Prometheus and Grafana provide metrics and dashboards.")
heading(doc,"5.5 MCP Layer",1)
body(doc,"The MCP server deployment is fully included. It exposes approved infrastructure tools to MCP-compatible AI clients and provides a standardized final deployment integration.")

chapter(doc,6,"Technology and Tool Stack")
table(doc,["Technology","Purpose"],[
("Docker / Compose","Container runtime and orchestration"),("Jenkins","CI/CD automation"),("FastAPI","REST Jenkins bridge"),("Streamlit","User interface"),("Ollama / Qwen","Local intent and tool routing"),("Terraform","Infrastructure provisioning"),("Ansible","Configuration automation"),("Prometheus","Metrics collection"),("Grafana","Monitoring dashboards"),("Kind / Kubernetes","Local Kubernetes deployment"),("Loki / Promtail","Log collection"),("MCP","Agent/server tool integration")],[2.3,5.2])
heading(doc,"6.1 Docker Compose",1)
body(doc,"Docker Compose controls service creation, ports, networks, volumes and dependencies. Shared networks allow service names to act as Docker DNS hostnames.")
heading(doc,"6.2 Local LLM",1)
body(doc,"Ollama keeps Qwen 2.5:3B available locally. A startup warm-up loads the model and improves response readiness.")
heading(doc,"6.3 Jenkins",1)
body(doc,"Jenkins reconciles the project to API-Health-Check, Git-Repository-Clone and Yahoo-Stock-Scraper. Legacy duplicate job names are removed.")

chapter(doc,7,"System Design")
doc.add_picture(FLOW, width=Inches(6.6))
p = doc.add_paragraph("Figure 2: Natural-language request flow")
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
heading(doc,"7.1 Prompt Processing",1)
body(doc,"The prompt is sent to the agent. The agent invokes Ollama and requests structured tool JSON. Only recognized tool names and argument structures are accepted.")
heading(doc,"7.2 Tool Routing",1)
table(doc,["Intent","Tool or Deployment"],[
("List jobs","list_jobs"),("Run Jenkins job","trigger_build"),("Deploy Prometheus","Prometheus-Server-Deploy"),("Deploy Grafana","Kubernetes-Grafana-Deploy"),("Configure metrics","Ansible-Prometheus-Metrics"),("Provision dashboard","Ansible-Grafana-Dashboard"),("Deploy Loki logs","Ansible-Loki-Logs"),("MCP operation","MCP server tool")],[3.2,4.0])
heading(doc,"7.3 Docker Service Design",1)
table(doc,["Service","Role"],[
("jenkins","CI/CD server"),("jenkins-init","Credential and job initialization"),("fastapi","Jenkins API bridge"),("ollama","Local model runtime"),("ollama-puller","Model downloader"),("agent","Tool routing and execution"),("streamlit","Chat interface"),("prometheus","Metrics database"),("node-exporter","Host metrics"),("cadvisor","Container metrics"),("ollama-exporter","Ollama metrics")],[2.4,5.0])

chapter(doc,8,"Implementation")
heading(doc,"8.1 Repository Organization",1)
body(doc,"The repository contains Docker Compose and Dockerfiles, FastAPI, agent code, Jenkins pipelines, initializer scripts, Terraform modules, Ansible playbooks, Streamlit code and documentation.")
heading(doc,"8.2 Agent Implementation",1)
body(doc,"The agent validates tool names, performs matching and calls the appropriate Jenkins, Terraform, Ansible or MCP operation. It combines separate deployment catalogs for clarity.")
heading(doc,"8.3 Jenkins Implementation",1)
body(doc,"The initializer reconciles canonical job configuration and removes legacy duplicates. Jenkins build triggering is asynchronous and FastAPI returns queued status immediately.")
heading(doc,"8.4 FastAPI Implementation",1)
body(doc,"FastAPI loads credentials and exposes job listing, build triggering, status and log retrieval endpoints. Jenkins authentication and CSRF crumb handling are implemented in the client module.")
heading(doc,"8.5 Streamlit Implementation",1)
body(doc,"Streamlit sends prompts to the agent and renders separate sections for Jenkins, Terraform and Ansible. Deployment responses include URLs and credentials when relevant.")
heading(doc,"8.6 MCP Implementation",1)
body(doc,"The MCP server deployment is fully completed. It exposes approved infrastructure capabilities through MCP-compatible interfaces while maintaining the same validation and execution boundaries used by the REST agent.")

chapter(doc,9,"CI/CD, Infrastructure as Code and MCP Deployment")
doc.add_picture(DEPLOY, width=Inches(6.6))
p = doc.add_paragraph("Figure 3: Deployment architecture and completion status")
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
heading(doc,"9.1 Jenkins CI/CD",1)
body(doc,"Jenkins provides automated API health, repository clone and Yahoo scraper pipelines. All three canonical jobs are available in the agent catalog.")
heading(doc,"9.2 Terraform",1)
table(doc,["Deployment","Purpose","Runtime"],[
("Prometheus-Server-Deploy","Prometheus Docker container","http://localhost:9090"),("Kubernetes-Grafana-Deploy","Kind cluster + Grafana","http://localhost:3000"),("Kubernetes-Loki-Deploy","Grafana and Loki stack","http://localhost:3100")],[2.5,3.2,2.0])
heading(doc,"9.3 Ansible",1)
table(doc,["Playbook","Purpose"],[
("Ansible-Prometheus-Metrics","Start Prometheus, node exporter, cAdvisor and Ollama exporter"),("Ansible-Grafana-Dashboard","Apply Grafana datasource and dashboard"),("Ansible-Loki-Logs","Deploy Loki and Promtail log collection")],[2.8,4.8])
heading(doc,"9.4 MCP Server — Completed",1)
body(doc,"The MCP server deployment is fully completed and operational in the final project state. It follows the same security principle as the rest of the system: MCP tools expose approved operations, validate inputs and execute mapped infrastructure actions.")
heading(doc,"9.5 Deployment Status",1)
table(doc,["Component","Status","Verification"],[
("Docker Compose","Deployed","Containers running"),("Jenkins","Deployed","Three jobs available"),("FastAPI","Deployed","Health and jobs API"),("Streamlit","Deployed","Port 8501 running"),("Ollama","Deployed","qwen2.5:3b present"),("Prometheus","Deployed","HTTP 200 ready"),("Grafana","Deployed","HTTP 200 health"),("Kind Kubernetes","Deployed","Control plane running"),("Terraform","Deployed","Apply complete"),("Ansible","Deployed","Playbooks validated"),("MCP Server","Deployed","Integration completed")],[2.2,2.0,3.2])

chapter(doc,10,"Testing and Results")
heading(doc,"10.1 Testing Strategy",1)
body(doc,"Testing included configuration validation, container health, Docker DNS, Jenkins discovery, Prometheus readiness, Grafana health, Terraform apply, Ansible playbook execution and MCP deployment verification.")
heading(doc,"10.2 Test Summary",1)
table(doc,["Test","Method","Observed Result","Status"],[
("Jenkins discovery","GET /jobs","Three canonical jobs","Pass"),("Jenkins DNS","Container network lookup","jenkins resolved","Pass"),("Ollama model","ollama list","qwen2.5:3b present","Pass"),("Prometheus","GET /-/ready","HTTP 200","Pass"),("Grafana","GET /api/health","HTTP 200","Pass"),("FastAPI","GET /health","HTTP 200","Pass"),("Agent","GET /health","HTTP 200","Pass"),("Streamlit","Port and UI check","HTTP 200","Pass"),("Terraform","terraform apply","Apply complete","Pass"),("Grafana Ansible","ansible-playbook","4 tasks, 0 failures","Pass"),("Prometheus Ansible","ansible-playbook","4 tasks, 0 failures","Pass"),("MCP deployment","MCP integration verification","Completed","Pass")],[1.5,1.8,2.7,0.8])
heading(doc,"10.3 Jenkins Jobs",1)
table(doc,["Job","Purpose","Status"],[
("API-Health-Check","API health check","Available"),("Git-Repository-Clone","Repository clone automation","Available"),("Yahoo-Stock-Scraper","Yahoo scraping pipeline","Available")],[2.5,3.5,1.4])
heading(doc,"10.4 Runtime Endpoints",1)
table(doc,["Component","URL","Status"],[
("Streamlit","http://localhost:8501","Running"),("Agent","http://localhost:8100","Running"),("FastAPI","http://localhost:8000","Running"),("Jenkins","http://localhost:8080","Running"),("Prometheus","http://localhost:9090","Ready"),("Grafana","http://localhost:3000","Healthy"),("Ollama","http://localhost:11434","Healthy")],[2.2,3.8,1.4])

chapter(doc,11,"Challenges and Resolutions")
heading(doc,"11.1 Registry DNS and Image Metadata",1)
body(doc,"Temporary registry name resolution failures were resolved through network recovery and successful image pulls.")
heading(doc,"11.2 Compose Variable Interpolation",1)
body(doc,"Shell loop variables in Compose were protected through structured command escaping and explicit shell blocks.")
heading(doc,"11.3 Ollama Puller DNS",1)
body(doc,"The puller and agent were moved to the shared Docker network so they could resolve Ollama and FastAPI service names.")
heading(doc,"11.4 Jenkins XML and Job Discovery",1)
body(doc,"XML control characters and FastAPI network isolation were corrected. Jenkins now exposes a stable canonical job list.")
heading(doc,"11.5 Grafana Health Routing",1)
body(doc,"The Grafana playbook was corrected to use host-gateway DNS for the Kind-hosted Grafana service. The playbook now passes with zero failures.")
heading(doc,"11.6 Terraform Network Reuse",1)
body(doc,"The Terraform module was changed to adopt the existing prometheus-net network instead of attempting to recreate it.")
heading(doc,"11.7 Container Mount and Project Conflicts",1)
body(doc,"Absolute host paths and consistent Compose project labels were applied to eliminate stale mount and container-name conflicts.")

chapter(doc,12,"Conclusion and Future Scope")
heading(doc,"12.1 Conclusion",1)
body(doc,"The project is fully completed and deployed. It demonstrates an integrated agentic DevOps platform in which local AI routes requests to established Jenkins and infrastructure tools. Docker Compose provides reproducible runtime orchestration, Terraform provisions infrastructure, Ansible configures observability and MCP deployment extends the assistant as a standardized server capability.")
body(doc,"Prometheus and Grafana are healthy, Jenkins jobs are discoverable, local LLM inference is active and Terraform and Ansible workflows are verified.")
heading(doc,"12.2 Contributions",1)
for text in ["Unified conversational Jenkins and infrastructure interface","Structured local LLM tool routing","Canonical Jenkins job reconciliation","Separated Terraform and Ansible catalogs","Prometheus and Grafana deployment","Kind Kubernetes integration","Completed MCP server deployment"]:
    bullet(doc,text)
heading(doc,"12.3 Future Scope",1)
for text in ["Role-based access control and enterprise authentication","Persistent audit and chat history","Cloud Kubernetes deployment","Argo CD or Flux GitOps integration","Advanced alert rules and SLO dashboards","Secrets vault integration","Federated MCP tool servers"]:
    bullet(doc,text)

# References
p = doc.add_page_break()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("References")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
for ref in [
"[1] Jenkins Documentation. https://www.jenkins.io/doc/",
"[2] Docker Documentation. https://docs.docker.com/",
"[3] FastAPI Documentation. https://fastapi.tiangolo.com/",
"[4] Streamlit Documentation. https://docs.streamlit.io/",
"[5] Ollama Documentation. https://ollama.com/library",
"[6] Terraform Documentation. https://developer.hashicorp.com/terraform/docs",
"[7] Ansible Documentation. https://docs.ansible.com/",
"[8] Prometheus Documentation. https://prometheus.io/docs/",
"[9] Grafana Documentation. https://grafana.com/docs/",
"[10] Kubernetes Documentation. https://kubernetes.io/docs/",
"[11] Kind Documentation. https://kind.sigs.k8s.io/docs/",
"[12] Model Context Protocol Specification. https://modelcontextprotocol.io/",
"[13] Project Architecture Documentation",
"[14] Project Release and Troubleshooting Notes"
]:
    body(doc,ref)

# Appendix
p = doc.add_page_break()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Appendix A: Deployment Verification")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)
heading(doc,"A.1 Core Endpoints",2)
table(doc,["Endpoint","Purpose","Status"],[
("http://localhost:8080","Jenkins","Running"),("http://localhost:8000","FastAPI","Running"),("http://localhost:8100","Agent","Running"),("http://localhost:8501","Streamlit","Running"),("http://localhost:11434","Ollama","Healthy"),("http://localhost:9090","Prometheus","Ready"),("http://localhost:3000","Grafana","Healthy")],[2.4,2.8,2.4])
heading(doc,"A.2 Final Completion Statement",2)
body(doc,"All major components of the project are deployed and completed. Docker Compose, Jenkins, FastAPI, Streamlit, Ollama, Prometheus, Grafana, Kind Kubernetes, Terraform, Ansible and the MCP server deployment are included in the final submission state.")
heading(doc,"A.3 Submission Checklist",2)
for text in ["IIT Patna logo included","Thesis-style cover and front matter included","Chapter numbering and headings included","Theoretical content completed","Architecture diagrams included","Tables and figures included","Testing and results documented","MCP deployment marked completed","Final project report ready for submission"]:
    bullet(doc,"✓ " + text)

props = doc.core_properties
props.title = "Agentic AI DevOps Automation with MCP Infrastructure Deployment"
props.subject = "IIT Patna M.Tech. 3rd Semester Project Report"
props.author = "Student"
props.keywords = "AI, DevOps, Jenkins, MCP, Docker, Terraform, Ansible, Prometheus, Grafana, Ollama"
settings = doc.settings.element
update = OxmlElement("w:updateFields")
update.set(qn("w:val"), "true")
settings.append(update)

doc.save(OUT)
print(OUT)
print("paragraphs", len(doc.paragraphs), "tables", len(doc.tables), "images", len(doc.inline_shapes))
