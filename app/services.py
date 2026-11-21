from __future__ import annotations
import os, re, io, json, smtplib, hashlib, mimetypes, subprocess, tempfile
from pathlib import Path
from email.message import EmailMessage
from datetime import datetime, timezone
from typing import Any
from PIL import Image, ImageOps, ImageDraw, ImageFont
import qrcode
from reportlab.lib import colors
from reportlab.pdfgen import canvas
try:
    from weasyprint import HTML
except Exception:  # Optional on Android/Termux; ReportLab fallback is used.
    HTML = None
from pypdf import PdfReader, PdfWriter
from .db import DATA_DIR
from .security import encrypt_bytes, decrypt_bytes, encrypt_text, decrypt_text

EVIDENCE_DIR = DATA_DIR / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "application/pdf", "text/plain", "video/mp4", "video/webm"
}
MAX_UPLOAD = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024
MAX_FILES = int(os.getenv("MAX_FILES_PER_REPORT", "10"))

class UploadProblem(ValueError): pass

def now_iso(dt=None):
    dt = dt or datetime.now(timezone.utc)
    return dt.isoformat()

def safe_filename(name: str) -> str:
    name = Path(name or "evidence").name
    name = re.sub(r"[^\w.() -]", "_", name, flags=re.UNICODE).strip(" .")
    return (name or "evidence")[:180]

def _watermark_image(data: bytes, case_id: str) -> bytes:
    with Image.open(io.BytesIO(data)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        text = f"PROOF  |  {case_id}"
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", max(14, image.width // 45))
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        pad = max(8, image.width // 100)
        x = pad
        y = image.height - (bbox[3] - bbox[1]) - pad * 2
        draw.rounded_rectangle((x-pad//2, y-pad//2, x+(bbox[2]-bbox[0])+pad, y+(bbox[3]-bbox[1])+pad), radius=5, fill=(0,0,0,120))
        draw.text((x, y), text, font=font, fill=(255,255,255,205))
        output = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        buf = io.BytesIO()
        output.save(buf, format="WEBP", quality=78, method=5)
        return buf.getvalue()

def _watermark_pdf(data: bytes, case_id: str) -> bytes:
    source = PdfReader(io.BytesIO(data), strict=False)
    writer = PdfWriter()
    for page in source.pages:
        width = float(page.mediabox.width); height = float(page.mediabox.height)
        overlay = io.BytesIO()
        c = canvas.Canvas(overlay, pagesize=(width, height))
        c.saveState(); c.setFillColor(colors.Color(0.1,0.2,0.3,alpha=0.16)); c.setFont("Helvetica-Bold", 28)
        c.translate(width/2, height/2); c.rotate(35); c.drawCentredString(0, 0, f"PROOF  |  {case_id}")
        c.restoreState(); c.save(); overlay.seek(0)
        page.merge_page(PdfReader(overlay).pages[0])
        writer.add_page(page)
    out=io.BytesIO(); writer.write(out); return out.getvalue()

def _watermark_video(data: bytes, case_id: str) -> bytes | None:
    if not shutil_which("ffmpeg"):
        return None
    with tempfile.TemporaryDirectory() as tmp:
        src=Path(tmp)/"source.bin"; dst=Path(tmp)/"preview.mp4"
        src.write_bytes(data)
        text=f"PROOF | {case_id}".replace(":", "\\:").replace("'", "\\'")
        cmd=["ffmpeg","-y","-loglevel","error","-i",str(src),"-vf",f"drawtext=text='{text}':fontcolor=white@0.75:fontsize=20:box=1:boxcolor=black@0.35:boxborderw=8:x=20:y=h-th-20","-c:v","libx264","-preset","veryfast","-crf","28","-c:a","aac","-movflags","+faststart",str(dst)]
        try:
            subprocess.run(cmd, check=True, timeout=90, capture_output=True)
            if dst.exists() and dst.stat().st_size <= MAX_UPLOAD * 2:
                return dst.read_bytes()
        except Exception:
            return None
    return None

def shutil_which(name: str):
    import shutil
    return shutil.which(name)

def store_upload(file_name: str, mime_type: str, data: bytes, case_id: str) -> dict[str, Any]:
    if not data: raise UploadProblem("ဖိုင်အလွတ်ဖြစ်နေပါသည်။")
    if len(data) > MAX_UPLOAD: raise UploadProblem(f"ဖိုင်တစ်ဖိုင်လျှင် {MAX_UPLOAD//(1024*1024)} MB ထက် မကျော်ရပါ။")
    mime_type = (mime_type or mimetypes.guess_type(file_name)[0] or "application/octet-stream").split(";")[0].lower()
    if mime_type not in ALLOWED_MIME: raise UploadProblem("ဤဖိုင်အမျိုးအစားကို လက်မခံပါ။")
    preview = None
    try:
        if mime_type.startswith("image/"):
            # Re-encode strips EXIF/GPS metadata; original is kept encrypted for evidence integrity.
            with Image.open(io.BytesIO(data)) as check:
                check.verify()
            preview = _watermark_image(data, case_id)
        elif mime_type == "application/pdf":
            if not data.startswith(b"%PDF-"): raise UploadProblem("PDF ဖိုင်ပုံစံ မမှန်ပါ။")
            try: preview = _watermark_pdf(data, case_id)
            except Exception: preview = None
        elif mime_type.startswith("video/"):
            if mime_type == "video/mp4" and b"ftyp" not in data[:64]: raise UploadProblem("MP4 ဖိုင်ပုံစံ မမှန်ပါ။")
            preview = _watermark_video(data, case_id)
        elif mime_type == "text/plain":
            data.decode("utf-8")
            preview = (f"PROOF | {case_id}\n\n".encode() + data[:2_000_000])
    except UploadProblem:
        raise
    except Exception as exc:
        raise UploadProblem("ဖိုင်အကြောင်းအရာကို ဖတ်မရပါ။") from exc
    storage_name = os.urandom(24).hex() + ".enc"
    preview_name = None
    try:
        (EVIDENCE_DIR / storage_name).write_bytes(encrypt_bytes(data))
        try: (EVIDENCE_DIR / storage_name).chmod(0o600)
        except OSError: pass
        if preview:
            preview_name = os.urandom(24).hex() + ".preview.enc"
            (EVIDENCE_DIR / preview_name).write_bytes(encrypt_bytes(preview))
            try: (EVIDENCE_DIR / preview_name).chmod(0o600)
            except OSError: pass
    except Exception:
        delete_stored(storage_name); delete_stored(preview_name)
        raise
    original = safe_filename(file_name)
    ext = Path(original).suffix[:16]
    return {
        "original_name": "evidence" + ext, "original_name_enc": encrypt_text(original), "mime_type": mime_type,
        "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "storage_name": storage_name, "preview_storage_name": preview_name
    }

def read_stored(name: str) -> bytes:
    path = EVIDENCE_DIR / name
    if not path.exists() or path.parent != EVIDENCE_DIR: raise FileNotFoundError
    return decrypt_bytes(path.read_bytes())

def delete_stored(name: str | None):
    if not name: return
    path = EVIDENCE_DIR / name
    if path.parent == EVIDENCE_DIR and path.exists(): path.unlink()

def make_qr(case_id: str, base_url: str) -> bytes:
    url = base_url.rstrip("/") + "/#case=" + case_id
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=7, border=3)
    qr.add_data(url); qr.make(fit=True)
    image=qr.make_image(fill_color="#0a0e17", back_color="white").convert("RGB")
    buf=io.BytesIO(); image.save(buf, format="PNG", optimize=True); return buf.getvalue()

def smtp_ready() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))

def send_email(to: str | None, subject: str, body: str):
    if not to or not smtp_ready(): return False
    host=os.getenv("SMTP_HOST"); port=int(os.getenv("SMTP_PORT","587"))
    msg=EmailMessage(); msg["Subject"]=subject; msg["From"]=os.getenv("SMTP_FROM"); msg["To"]=to; msg.set_content(body)
    try:
        with smtplib.SMTP(host,port,timeout=12) as server:
            if os.getenv("SMTP_USE_TLS","true").lower()=="true": server.starttls()
            user=os.getenv("SMTP_USERNAME"); password=os.getenv("SMTP_PASSWORD")
            if user: server.login(user,password or "")
            server.send_message(msg)
        return True
    except Exception:
        return False

def export_reports_pdf(rows: list[dict[str, Any]]) -> bytes:
    generated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cases=[]
    for row in rows:
        tags=", ".join(row.get("tags",[]))
        fields=[("Title",row.get("title")),("Category",row.get("category")),("Created",row.get("created_at")),("Location",row.get("location")),("Summary",row.get("summary")),("Tags",tags)]
        table="".join(f"<tr><th>{esc_pdf(label)}</th><td>{esc_pdf(value)}</td></tr>" for label,value in fields)
        cases.append(f"<section class='case'><header><strong>{esc_pdf(row.get('case_id'))}</strong><span>{esc_pdf(row.get('status'))}</span></header><table>{table}</table></section>")
    html=f"""<!doctype html><html lang='my'><head><meta charset='utf-8'><title>PROOF Case Export</title><style>
    @page {{ size:A4; margin:17mm 15mm 18mm; @bottom-right {{ content:'Page ' counter(page) ' / ' counter(pages); font-size:8pt; color:#667085; }} }}
    * {{ box-sizing:border-box; }} body {{ font-family:'Noto Sans Myanmar','Noto Sans',sans-serif; color:#172033; font-size:9pt; line-height:1.55; }}
    h1 {{ font-family:'Noto Sans Myanmar',sans-serif; font-size:19pt; margin:0 0 3mm; color:#17324d; }} .meta {{ color:#667085; font-size:8pt; margin-bottom:8mm; }}
    .case {{ border:0.5pt solid #cbd5e1; border-radius:5pt; margin:0 0 6mm; padding:4mm; break-inside:avoid; }}
    .case header {{ display:flex; justify-content:space-between; gap:8mm; font-size:9pt; margin-bottom:3mm; color:#17324d; }}
    table {{ width:100%; border-collapse:collapse; table-layout:fixed; }} th,td {{ border:0.5pt solid #d7dee8; padding:2.2mm; text-align:left; vertical-align:top; overflow-wrap:anywhere; }}
    th {{ width:24%; background:#eef2f7; font-weight:600; }} td {{ white-space:pre-wrap; }} .empty {{ color:#667085; }}
    </style></head><body><h1>PROOF — Case Report Export</h1><div class='meta'>Generated: {esc_pdf(generated)} · Records: {len(rows)}</div>{''.join(cases) if cases else "<p class='empty'>No records.</p>"}</body></html>"""
    if HTML is not None:
        return HTML(string=html,base_url=str(DATA_DIR)).write_pdf()
    # Android/Termux fallback: simple, portable PDF metadata summary.
    # ReportLab's built-in font is Latin-only; Burmese content may not render here.
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase.pdfmetrics import stringWidth
    out=io.BytesIO(); pdf=canvas.Canvas(out,pagesize=A4)
    width,height=A4; y=height-42
    pdf.setTitle("PROOF Case Report Export")
    pdf.setFont("Helvetica-Bold",16); pdf.drawString(40,y,"PROOF - Case Report Export"); y-=22
    pdf.setFont("Helvetica",8); pdf.drawString(40,y,f"Generated: {generated} | Records: {len(rows)}"); y-=24
    for row in rows:
        if y<90: pdf.showPage(); y=height-42
        pdf.setFont("Helvetica-Bold",10); pdf.drawString(40,y,str(row.get("case_id",""))[:55]); y-=14
        pdf.setFont("Helvetica",8)
        for label,value in (("Status",row.get("status")),("Category",row.get("category")),("Title",row.get("title")),("Created",row.get("created_at"))):
            line=f"{label}: {str(value or '-')[:100]}"
            pdf.drawString(48,y,line[:120]); y-=12
        y-=10
    pdf.save(); return out.getvalue()

def esc_pdf(value: Any) -> str:
    text=str(value or "—")
    return text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br/>")
