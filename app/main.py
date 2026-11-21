from __future__ import annotations
import os, json, re, io, csv, time, hmac, secrets, asyncio
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Request, Response, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc
from sqlalchemy.exc import IntegrityError

from .db import Base, engine, get_db, DATA_DIR, SessionLocal
from . import models as m
from .security import encrypt_text, decrypt_text, token_hash, new_token, password_hash, verify_password
from .services import (store_upload, read_stored, delete_stored, make_qr, send_email, smtp_ready,
                       export_reports_pdf, UploadProblem, MAX_FILES, MAX_UPLOAD)

APP_ENV=os.getenv("APP_ENV","development").lower()
APP_BASE_URL=os.getenv("APP_BASE_URL","http://127.0.0.1:8000").rstrip("/")
SESSION_IDLE_MINUTES=max(5,min(120,int(os.getenv("SESSION_IDLE_MINUTES","15"))))
COOKIE_SECURE=os.getenv("COOKIE_SECURE","true" if APP_ENV=="production" else "false").lower()=="true"

@asynccontextmanager
async def lifespan(app):
    with SessionLocal() as db:
        if not db.get(m.Setting,"hotlines"): save_setting(db,"hotlines",[])
        if not db.get(m.Setting,"category_routes"): save_setting(db,"category_routes",{})
        if not db.get(m.Setting,"session_timeout"): save_setting(db,"session_timeout",SESSION_IDLE_MINUTES)
        db.commit()
    yield

app=FastAPI(title="PROOF Accountability Portal API", version="3.0.0", docs_url="/api/docs" if APP_ENV!="production" else None, redoc_url=None, lifespan=lifespan)
app.mount("/static",StaticFiles(directory=Path(__file__).resolve().parents[1]/"static"),name="static")
Base.metadata.create_all(bind=engine)

DEFAULT_FAQ=[
 {"q":"တိုင်ကြားချက်ကို အမည်မဖော်ဘဲ တင်နိုင်ပါသလား?","a":"ရပါတယ်။ Anonymous ကို ရွေးချယ်နိုင်ပါတယ်။ သို့သော် အွန်လိုင်းဝန်ဆောင်မှုတစ်ခုတွင် လုံးဝအမည်မသိဖြစ်ကြောင်း အာမမခံနိုင်ပါ။ Hosting provider ၏ network logs နှင့် browser/device အချက်အလက်များကိုလည်း သတိပြုပါ။"},
 {"q":"Case ID ကို ဘာကြောင့် သိမ်းထားရပါသလဲ?","a":"Case ID သည် သင့်တိုင်ကြားချက်အခြေအနေကို ပြန်လည်စစ်ဆေးရန် လျှို့ဝှက်သော key ဖြစ်ပါတယ်။ အခြားသူနှင့် မမျှဝေပါနှင့်။"},
 {"q":"တင်ထားသော Evidence ကို ဘယ်သူမြင်နိုင်ပါသလဲ?","a":"ခွင့်ပြုထားသော စီမံခန့်ခွဲရေးအဖွဲ့ဝင်များသာ ကြည့်နိုင်ပါတယ်။ Public ထုတ်ပြန်မှုတွင် Evidence များကို မဖော်ပြပါ။"},
 {"q":"Internet မရှိလျှင် တိုင်ကြားချက်တင်နိုင်ပါသလား?","a":"Offline အချိန်တွင် Draft ကို စက်အတွင်း ယာယီသိမ်းထားနိုင်ပါတယ်။ Internet ပြန်ရမှ Server သို့ တင်သွင်းပါ။ Shared device များတွင် Draft မထားပါနှင့်။"},
 {"q":"အခြေအနေပြောင်းလဲလျှင် ဘယ်လိုသိနိုင်ပါသလဲ?","a":"Case ID ဖြင့် ပြန်စစ်နိုင်ပါတယ်။ Email အသိပေးချက်ကို ရယူလိုပါက တင်သွင်းချိန်တွင် email ထည့်ပြီး ခွင့်ပြုနိုင်ပါတယ်။"},
]
DEFAULT_FAQ_EN=[
 {"q":"Can I submit anonymously?","a":"Yes. You can submit without your name. However, no internet service can guarantee complete anonymity. Hosting provider network logs and browser/device information may still exist."},
 {"q":"Why must I keep my Case ID?","a":"Your Case ID is a private key for checking your report status. Do not share it with anyone."},
 {"q":"Who can see my evidence?","a":"Only authorized staff can access evidence. Evidence is never displayed on the public records page."},
 {"q":"Can I submit while offline?","a":"You can save a temporary draft on this device while offline. Submit it to the server after reconnecting. Avoid saving drafts on shared devices."},
 {"q":"How will I know when the status changes?","a":"Check your case using the Case ID. If you provide an email and opt in, status updates can also be emailed."},
]
DEFAULT_TEMPLATES_EN=[
 {"id":"general","name":"General incident","category":"အခြား","title":"Incident summary","prompt":"Describe when and where it happened, people involved (if known), what you personally saw or heard, and which evidence can be verified."},
 {"id":"corruption","name":"Corruption / fraud","category":"အဂတိလိုက်စားမှု / လိမ်လည်မှု","title":"Corruption report","prompt":"Describe the decision, payment, or benefit involved; dates; relevant department; and verifiable documents. Do not present guesses as facts."},
 {"id":"safety","name":"Safety / harassment","category":"လုံခြုံရေး စည်းမျဉ်းဖောက်ဖျက်မှု","title":"Safety incident","prompt":"Describe when and where it happened, whether there is an immediate risk, whether urgent help is needed, and what you have done to stay safe."},
]
DEFAULT_TEMPLATES=[
 {"id":"general","name":"အထွေထွေဖြစ်ရပ်","category":"အခြား","title":"ဖြစ်ရပ်အကျဉ်းချုပ်","prompt":"ဖြစ်ပွားခဲ့သည့်အချိန်၊ နေရာ၊ ပါဝင်သူများ (သိရှိပါက)၊ ကိုယ်တိုင်မြင်တွေ့/ကြားသိခဲ့သည့်အချက်များနှင့် အတည်ပြုနိုင်သော အထောက်အထားများကို ခွဲခြားရေးသားပါ။"},
 {"id":"corruption","name":"အဂတိလိုက်စားမှု / လိမ်လည်မှု","category":"အဂတိလိုက်စားမှု / လိမ်လည်မှု","title":"အဂတိလိုက်စားမှုဆိုင်ရာ တင်ပြချက်","prompt":"မည်သည့် ဆုံးဖြတ်ချက်/ငွေပေးချေမှု/အကျိုးအမြတ်နှင့် ပတ်သက်သနည်း။ ရက်စွဲ၊ ပါဝင်သည့်ဌာန၊ အတည်ပြုနိုင်သော စာရွက်စာတမ်းများကို ဖော်ပြပါ။ ခန့်မှန်းချက်ကို အချက်အလက်အဖြစ် မရေးပါနှင့်။"},
 {"id":"safety","name":"လုံခြုံရေး / နှောင့်ယှက်မှု","category":"လုံခြုံရေး စည်းမျဉ်းဖောက်ဖျက်မှု","title":"လုံခြုံရေးဆိုင်ရာ ဖြစ်ရပ်","prompt":"ဖြစ်ရပ်၏ အချိန်နှင့် နေရာ၊ လက်ရှိအန္တရာယ်ရှိ/မရှိ၊ ချက်ချင်းကူညီရန် လိုအပ်/မလိုအပ်၊ မိမိလုံခြုံရေးအတွက် ဆောင်ရွက်ထားသည်များကို ဖော်ပြပါ။"},
]

class LoginIn(BaseModel): username:str; password:str
class ForgotIn(BaseModel): username_or_email:str
class ResetIn(BaseModel): token:str; password:str
class ReportUpdate(BaseModel):
 status: Optional[str]=None
 visibility: Optional[str]=None
 public_summary: Optional[str]=None
 public_note: Optional[str]=None
 admin_note: Optional[str]=None
 tags: Optional[list[str]]=None
 assigned_team: Optional[str]=None
class CommentIn(BaseModel): body:str=Field(min_length=1,max_length=3000); visibility:str="internal"
class PublicCommentIn(BaseModel): body:str=Field(min_length=1,max_length=2000)
class FeedbackIn(BaseModel): message:str=Field(min_length=3,max_length=3000); rating:Optional[int]=Field(default=None,ge=1,le=5); email:Optional[str]=None
class SettingsIn(BaseModel): hotlines:Optional[list[dict]]=None; category_routes:Optional[dict[str,str]]=None; session_timeout:Optional[int]=Field(default=None,ge=5,le=120)
class UserIn(BaseModel): username:str=Field(min_length=3,max_length=80); email:Optional[str]=None; password:str=Field(min_length=12); role:str="reviewer"

# In-memory throttles only; request IPs are not written to the database or application logs.
_RATE:dict[str,deque]=defaultdict(deque)
_RATE_SECRET=secrets.token_bytes(32)
def ensure_same_origin(request:Request):
    origin=request.headers.get("origin")
    host=request.headers.get("host","").lower()
    if origin and urlsplit(origin).netloc.lower()!=host: raise HTTPException(403,"Cross-origin request ကို ပိတ်ထားပါသည်။")
    if request.headers.get("sec-fetch-site")=="cross-site": raise HTTPException(403,"Cross-site request ကို ပိတ်ထားပါသည်။")

def rate_limit(request:Request, bucket:str, limit:int, seconds:int):
    ensure_same_origin(request)
    host=request.client.host if request.client else "unknown"
    key=f"{bucket}:{hmac.new(_RATE_SECRET,host.encode(),'sha256').hexdigest()}"
    now=time.monotonic(); q=_RATE[key]
    while q and now-q[0]>seconds: q.popleft()
    if len(q)>=limit: raise HTTPException(429,"ခဏစောင့်ပြီး ပြန်လည်ကြိုးစားပါ။")
    q.append(now)

def utcnow(): return datetime.now(timezone.utc)
def dt_out(value): return value.isoformat() if value else None
def json_load(value, default):
    try: return json.loads(value) if value else default
    except Exception: return default

def get_payload(report:m.Report)->dict:
    return json_load(decrypt_text(report.payload_enc),{})
def set_payload(report:m.Report,payload:dict): report.payload_enc=encrypt_text(json.dumps(payload,ensure_ascii=False))
def add_audit(db:Session, action:str, actor_id:int|None=None, report_id:int|None=None, details:dict|None=None):
    db.add(m.AuditLog(actor_id=actor_id,report_id=report_id,action=action,details_json=json.dumps(details or {},ensure_ascii=False)))
def notify_admins(db:Session, kind:str, title:str, body:str, report_id:int|None=None):
    admins=db.scalars(select(m.User).where(m.User.active==True)).all()
    if admins:
        for user in admins: db.add(m.Notification(user_id=user.id,report_id=report_id,kind=kind,title=title,body=body))
    else: db.add(m.Notification(user_id=None,report_id=report_id,kind=kind,title=title,body=body))
def setting(db:Session,key:str,default):
    row=db.get(m.Setting,key)
    return json_load(row.value,default) if row else default
def save_setting(db:Session,key:str,value):
    row=db.get(m.Setting,key)
    if row: row.value=json.dumps(value,ensure_ascii=False)
    else: db.add(m.Setting(key=key,value=json.dumps(value,ensure_ascii=False)))
def case_or_404(db:Session,case_id:str):
    row=db.scalar(select(m.Report).where(m.Report.case_id==case_id.upper()))
    if not row: raise HTTPException(404,"Case မတွေ့ပါ။")
    return row

def admin_user(request:Request,db:Session=Depends(get_db)):
    raw=request.cookies.get("proof_session")
    if not raw: raise HTTPException(401,"Admin Login လုပ်ရန် လိုအပ်ပါသည်။")
    sess=db.scalar(select(m.AdminSession).where(m.AdminSession.token_hash==token_hash(raw)))
    if not sess: raise HTTPException(401,"Session မမှန်ပါ။ ပြန်လည် Login ဝင်ပါ။")
    now=utcnow()
    last=sess.last_seen
    if last.tzinfo is None: last=last.replace(tzinfo=timezone.utc)
    idle_minutes=setting(db,"session_timeout",SESSION_IDLE_MINUTES)
    if now-last>timedelta(minutes=idle_minutes) or sess.expires_at.replace(tzinfo=timezone.utc if sess.expires_at.tzinfo is None else sess.expires_at.tzinfo)<now:
        db.delete(sess); db.commit(); raise HTTPException(401,"Session သက်တမ်းကုန်သွားပါပြီ။ ပြန်လည် Login ဝင်ပါ။")
    sess.last_seen=now
    db.commit()
    user=db.get(m.User,sess.user_id)
    if not user or not user.active: raise HTTPException(401,"Account ပိတ်ထားပါသည်။")
    request.state.admin_session_id=sess.id
    request.state.admin_user_id=user.id
    return user

def admin_write(request:Request,db:Session=Depends(get_db),user:m.User=Depends(admin_user)):
    csrf_cookie=request.cookies.get("proof_csrf","")
    csrf_header=request.headers.get("x-csrf-token","")
    sess=db.get(m.AdminSession,getattr(request.state,"admin_session_id",0))
    if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie,csrf_header) or not sess or not hmac.compare_digest(token_hash(csrf_header),sess.csrf_hash):
        raise HTTPException(403,"CSRF token မမှန်ပါ။ Page ကို refresh လုပ်ပါ။")
    return user

def role_check(user:m.User, allowed:tuple[str,...]):
    if user.role not in allowed: raise HTTPException(403,"ဤလုပ်ဆောင်ချက်အတွက် ခွင့်ပြုချက်မရှိပါ။")
    return user

def report_public_dict(report:m.Report):
    return {"case_id":report.case_id,"category":report.category,"status":report.status,"visibility":report.visibility,"created_at":dt_out(report.created_at),"updated_at":dt_out(report.updated_at)}
def report_admin_dict(report:m.Report,user:m.User|None=None):
    p=get_payload(report); publisher=bool(user and user.role=="publisher")
    return {"case_id":report.case_id,"category":report.category,"status":report.status,"visibility":report.visibility,"flagged":report.flagged,"flag_reason":report.flag_reason,"role":p.get("role"),"incident_date":p.get("incident_date"),"location":p.get("location"),"title":p.get("title"),"summary":p.get("summary"),"public_summary":p.get("public_summary"),"public_note":p.get("public_note"),"admin_note":"" if publisher else p.get("admin_note"),"anonymous":p.get("anonymous"),"contact_email":"" if publisher else p.get("contact_email"),"notify_email":False if publisher else p.get("notify_email"),"tags":json_load(report.tags_json,[]),"assigned_team":None if publisher else report.assigned_team,"created_at":dt_out(report.created_at),"updated_at":dt_out(report.updated_at),"attachments":([] if publisher else [{"id":a.id,"name":decrypt_text(a.original_name_enc) if a.original_name_enc else a.original_name,"mime_type":a.mime_type,"size":a.size,"sha256":a.sha256,"created_at":dt_out(a.created_at)} for a in report.attachments if not a.deleted_at]),"comments":[{"id":c.id,"author_type":c.author_type,"visibility":c.visibility,"body":decrypt_text(c.body_enc),"created_at":dt_out(c.created_at)} for c in sorted(report.comments,key=lambda c:c.created_at) if c.visibility=="public" or (not publisher and c.visibility=="internal")]}


def route_for(db:Session,category:str):
    routes=setting(db,"category_routes",{})
    return routes.get(category) or routes.get("default")

@app.middleware("http")
async def security_headers(request:Request,call_next):
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["Referrer-Policy"]="no-referrer"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    response.headers["Permissions-Policy"]="camera=(), geolocation=(), payment=()"
    response.headers["Cache-Control"]="no-store" if request.url.path.startswith("/api/") else response.headers.get("Cache-Control","no-cache")
    if APP_ENV=="production": response.headers["Strict-Transport-Security"]="max-age=31536000; includeSubDomains"
    return response

@app.get("/",response_class=HTMLResponse)
def index():
    return FileResponse(Path(__file__).resolve().parents[1]/"static"/"index.html")

@app.get("/demo",response_class=HTMLResponse)
def feature_demo():
    """Interactive 100-feature demo; demo-only state is stored in the browser."""
    return FileResponse(Path(__file__).resolve().parents[1]/"static"/"demo.html")

@app.get("/api/health")
def health(): return {"status":"ok","service":"PROOF","environment":APP_ENV,"api_version":"3.0.0"}

@app.get("/api/public/config")
def public_config(db:Session=Depends(get_db)):
    return {"hotlines":setting(db,"hotlines",[]),"faq":DEFAULT_FAQ,"faq_en":DEFAULT_FAQ_EN,"templates":DEFAULT_TEMPLATES,"templates_en":DEFAULT_TEMPLATES_EN,"max_upload_mb":int(os.getenv("MAX_UPLOAD_MB","20")),"max_files":MAX_FILES,"smtp_notifications":smtp_ready()}

@app.post("/api/reports")
async def create_report(background:BackgroundTasks,request:Request,
    role:str=Form(...),category:str=Form(...),incident_date:str=Form(""),location:str=Form(""),
    title:str=Form(...),summary:str=Form(...),public_summary:str=Form(""),contact_email:str=Form(""),
    anonymous:bool=Form(False),notify_email:bool=Form(False),consent:bool=Form(False),website:str=Form(""),
    files:list[UploadFile]=File(default=[]),db:Session=Depends(get_db)):
    rate_limit(request,"submit",5,900)
    if website.strip(): raise HTTPException(400,"Submission rejected")
    if not consent: raise HTTPException(400,"သဘောတူညီချက်ကို အတည်ပြုပါ။")
    if len(files)>MAX_FILES: raise HTTPException(413,f"ဖိုင်အများဆုံး {MAX_FILES} ခုသာ တင်နိုင်ပါသည်။")
    if len(title.strip())<3 or len(summary.strip())<10: raise HTTPException(422,"ခေါင်းစဉ်နှင့် အသေးစိတ်ကို ပြည့်စုံစွာ ဖြည့်ပါ။")
    if contact_email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",contact_email.strip()): raise HTTPException(422,"Email လိပ်စာ မမှန်ပါ။")
    if notify_email and not contact_email.strip(): raise HTTPException(422,"Email အသိပေးချက်အတွက် Contact Email ထည့်ပါ။")
    case_id=f"PRF-{datetime.now(timezone.utc).year}-{secrets.token_hex(16).upper()}"
    payload={"role":role[:100],"incident_date":incident_date[:20],"location":location.strip()[:300],"title":title.strip()[:180],"summary":summary.strip()[:12000],"public_summary":public_summary.strip()[:4000],"public_note":"","admin_note":"တိုင်ကြားချက် လက်ခံရရှိပြီး စိစစ်ရန် စောင့်ဆိုင်းနေပါသည်။","anonymous":bool(anonymous),"contact_email":contact_email.strip() if contact_email else "","notify_email":bool(notify_email and contact_email)}
    duplicate_hash=__import__('hashlib').sha256((payload["title"].lower()+payload["summary"].lower()).encode()).hexdigest()
    recent=db.scalars(select(m.Report).where(m.Report.created_at>=utcnow()-timedelta(hours=24)).limit(500)).all()
    flagged=False; reason=None
    for old in recent:
        oldp=get_payload(old)
        oldhash=__import__('hashlib').sha256((oldp.get("title","").lower()+oldp.get("summary","").lower()).encode()).hexdigest()
        if hmac.compare_digest(duplicate_hash,oldhash): flagged=True; reason="Repeated report content"; break
    if len(re.findall(r"https?://",payload["summary"],re.I))>=5: flagged=True; reason=reason or "Excessive links"
    assigned=route_for(db,category)
    report=m.Report(case_id=case_id,category=category[:100],status="Pending Review",visibility="private",flagged=flagged,flag_reason=reason,payload_enc=encrypt_text(json.dumps(payload,ensure_ascii=False)),assigned_team=(assigned or "")[:120] or None)
    db.add(report); db.flush()
    total=0; stored_names=[]
    try:
        for upload in files:
            raw=await upload.read(MAX_UPLOAD+1); total+=len(raw)
            if total>MAX_UPLOAD*MAX_FILES: raise UploadProblem("စုစုပေါင်းဖိုင်အရွယ်အစား ကန့်သတ်ချက်ကို ကျော်သွားပါသည်။")
            stored=store_upload(upload.filename or "evidence",upload.content_type or "",raw,case_id)
            stored_names.extend([stored["storage_name"],stored.get("preview_storage_name")])
            db.add(m.Attachment(report_id=report.id,**stored))
        notify_admins(db,"new_report","တိုင်ကြားချက်အသစ် လက်ခံရရှိ","Case ID: "+case_id+(" · Spam စိစစ်ရန်လို" if flagged else ""),report.id)
        add_audit(db,"report.submitted",None,report.id,{"anonymous":bool(anonymous),"attachment_count":len(files),"flagged":flagged})
        db.commit()
    except UploadProblem as exc:
        db.rollback()
        for name in stored_names: delete_stored(name)
        raise HTTPException(413,str(exc))
    except Exception:
        db.rollback()
        for name in stored_names: delete_stored(name)
        raise
    route_email=assigned if assigned and "@" in assigned else None
    if route_email: background.add_task(send_email,route_email,f"PROOF: New report {case_id}",f"A new report was submitted. Case ID: {case_id}. Sign in to the secure portal to review it. No report details are included in this email.")
    if payload["notify_email"]: background.add_task(send_email,payload["contact_email"],f"PROOF case received: {case_id}",f"Your report was received. Your Case ID is {case_id}. Keep it private to check status. This email contains no report details.")
    return {"ok":True,"case_id":case_id,"status":"Pending Review","qr_url":f"/api/cases/{case_id}/qr.png","message":"တိုင်ကြားချက်ကို Server တွင် လက်ခံသိမ်းဆည်းပြီးပါပြီ။ Case ID ကို လုံခြုံစွာ သိမ်းထားပါ။","flagged_for_review":flagged}

@app.get("/api/cases/{case_id}")
def track_case(case_id:str,db:Session=Depends(get_db)):
    report=case_or_404(db,case_id)
    p=get_payload(report)
    comments=db.scalars(select(m.Comment).where(m.Comment.report_id==report.id,m.Comment.visibility=="public").order_by(m.Comment.created_at)).all()
    return {"case_id":report.case_id,"status":report.status,"category":report.category,"created_at":dt_out(report.created_at),"updated_at":dt_out(report.updated_at),"public_note":p.get("public_note") or "လက်ခံရရှိပြီး စိစစ်ဆဲဖြစ်ပါသည်။","comments":[{"body":decrypt_text(c.body_enc),"created_at":dt_out(c.created_at),"author":"PROOF Team" if c.author_type=="admin" else "You"} for c in comments]}

@app.post("/api/cases/{case_id}/comments")
def submit_case_comment(case_id:str,data:PublicCommentIn,request:Request,db:Session=Depends(get_db)):
    rate_limit(request,"case_comment",8,900)
    report=case_or_404(db,case_id)
    comment=m.Comment(report_id=report.id,author_type="submitter",visibility="public",body_enc=encrypt_text(data.body.strip()))
    db.add(comment); notify_admins(db,"case_message","Case Message အသစ်","Case ID: "+report.case_id,report.id); add_audit(db,"comment.submitter",None,report.id,{"length":len(data.body)})
    db.commit(); return {"ok":True,"message":"မှတ်ချက်ကို လက်ခံရရှိပါပြီ။"}

@app.get("/api/cases/{case_id}/qr.png")
def case_qr(case_id:str,db:Session=Depends(get_db)):
    report=case_or_404(db,case_id)
    data=make_qr(report.case_id,APP_BASE_URL)
    return Response(data,media_type="image/png",headers={"Cache-Control":"no-store"})

@app.get("/api/public/stats")
def public_stats(db:Session=Depends(get_db)):
    rows=db.scalars(select(m.Report)).all()
    statuses={"Pending Review":0,"Under Investigation":0,"Verified & Published":0,"Dismissed":0}
    for r in rows: statuses[r.status]=statuses.get(r.status,0)+1
    return {"total":len(rows),"open":statuses["Pending Review"]+statuses["Under Investigation"],"closed":statuses["Verified & Published"]+statuses["Dismissed"],"published":sum(1 for r in rows if r.status=="Verified & Published" and r.visibility=="public")}

@app.get("/api/public/records")
def public_records(db:Session=Depends(get_db)):
    rows=db.scalars(select(m.Report).where(m.Report.status=="Verified & Published",m.Report.visibility=="public").order_by(desc(m.Report.updated_at)).limit(100)).all()
    result=[]
    for r in rows:
        p=get_payload(r)
        result.append({"category":r.category,"title":p.get("title"),"summary":p.get("public_summary") or "အများပြည်သူဖတ်ရှုရန် အကျဉ်းချုပ် မထည့်ထားပါ။","date":p.get("incident_date"),"tags":json_load(r.tags_json,[])})
    return result

@app.get("/api/public/faq")
def public_faq(): return DEFAULT_FAQ

@app.post("/api/feedback")
def submit_feedback(data:FeedbackIn,request:Request,db:Session=Depends(get_db)):
    rate_limit(request,"feedback",5,3600)
    email=data.email.strip() if data.email else ""
    if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email): raise HTTPException(422,"Email မမှန်ပါ။")
    db.add(m.Feedback(rating=data.rating,message_enc=encrypt_text(data.message.strip()),email_enc=encrypt_text(email) if email else None))
    notify_admins(db,"feedback","Feedback အသစ်","အသုံးပြုသူ Feedback အသစ် လက်ခံရရှိပါသည်။")
    add_audit(db,"feedback.submitted",None,None,{"rating":data.rating}); db.commit()
    return {"ok":True,"message":"Feedback ပေးပို့ပြီးပါပြီ။"}

@app.post("/api/auth/login")
def login(data:LoginIn,request:Request,response:Response,db:Session=Depends(get_db)):
    rate_limit(request,"login",8,900)
    user=db.scalar(select(m.User).where(m.User.username==data.username.strip()))
    if not user or not user.active or not verify_password(data.password,user.password_hash):
        raise HTTPException(401,"Username သို့မဟုတ် Password မမှန်ပါ။")
    session_token=new_token(48); csrf_token=new_token(24); now=utcnow()
    sess=m.AdminSession(token_hash=token_hash(session_token),csrf_hash=token_hash(csrf_token),user_id=user.id,created_at=now,last_seen=now,expires_at=now+timedelta(hours=12))
    db.add(sess); add_audit(db,"auth.login",user.id,None,{"username":user.username}); db.commit()
    response.set_cookie("proof_session",session_token,httponly=True,secure=COOKIE_SECURE,samesite="strict",max_age=12*3600,path="/")
    response.set_cookie("proof_csrf",csrf_token,httponly=False,secure=COOKIE_SECURE,samesite="strict",max_age=12*3600,path="/")
    return {"ok":True,"user":{"username":user.username,"role":user.role,"email":user.email},"csrf_token":csrf_token,"idle_timeout_minutes":setting(db,"session_timeout",SESSION_IDLE_MINUTES)}

@app.get("/api/auth/me")
def auth_me(user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    return {"authenticated":True,"user":{"username":user.username,"role":user.role,"email":user.email},"idle_timeout_minutes":setting(db,"session_timeout",SESSION_IDLE_MINUTES)}

@app.post("/api/auth/logout")
def logout(request:Request,response:Response,db:Session=Depends(get_db),user:m.User=Depends(admin_write)):
    raw=request.cookies.get("proof_session","")
    sess=db.scalar(select(m.AdminSession).where(m.AdminSession.token_hash==token_hash(raw))) if raw else None
    if sess: db.delete(sess)
    add_audit(db,"auth.logout",user.id); db.commit()
    response.delete_cookie("proof_session",path="/"); response.delete_cookie("proof_csrf",path="/")
    return {"ok":True}

@app.post("/api/auth/forgot")
def forgot_password(data:ForgotIn,background:BackgroundTasks,request:Request,db:Session=Depends(get_db)):
    rate_limit(request,"forgot",4,3600)
    key=data.username_or_email.strip()
    user=db.scalar(select(m.User).where((m.User.username==key)|(m.User.email==key)))
    if user and user.active and user.email and smtp_ready():
        raw=new_token(32); db.add(m.PasswordReset(user_id=user.id,token_hash=token_hash(raw),expires_at=utcnow()+timedelta(minutes=30)))
        db.commit(); link=APP_BASE_URL+"/#reset="+raw
        background.add_task(send_email,user.email,"PROOF Admin Password Reset",f"A password reset was requested. Use this one-time link within 30 minutes: {link}\nIf you did not request this, ignore this email.")
    return {"ok":True,"message":"အကောင့်ရှိပါက Password Recovery လမ်းညွှန်ကို Email သို့ ပို့ထားပါသည်။ SMTP မချိတ်ထားပါက Server Admin မှ CLI ဖြင့် Reset လုပ်နိုင်ပါသည်။"}

@app.post("/api/auth/reset")
def reset_password(data:ResetIn,request:Request,db:Session=Depends(get_db)):
    rate_limit(request,"reset",5,3600)
    row=db.scalar(select(m.PasswordReset).where(m.PasswordReset.token_hash==token_hash(data.token),m.PasswordReset.used_at.is_(None)))
    if not row or row.expires_at.replace(tzinfo=timezone.utc if row.expires_at.tzinfo is None else row.expires_at.tzinfo)<utcnow(): raise HTTPException(400,"Recovery Link မမှန်ပါ သို့မဟုတ် သက်တမ်းကုန်သွားပါပြီ။")
    user=db.get(m.User,row.user_id); user.password_hash=password_hash(data.password); row.used_at=utcnow()
    db.query(m.AdminSession).filter(m.AdminSession.user_id==user.id).delete(synchronize_session=False)
    add_audit(db,"auth.password_reset",user.id); db.commit(); return {"ok":True,"message":"Password ပြောင်းလဲပြီးပါပြီ။ ပြန်လည် Login ဝင်ပါ။"}

@app.get("/api/admin/reports")
def admin_reports(category:str="",status:str="",date_from:str="",date_to:str="",q:str="",flagged:str="",user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    stmt=select(m.Report)
    if category: stmt=stmt.where(m.Report.category==category)
    if status: stmt=stmt.where(m.Report.status==status)
    if date_from:
        try: stmt=stmt.where(m.Report.created_at>=datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc))
        except ValueError: raise HTTPException(422,"Start date မမှန်ပါ။")
    if date_to:
        try: stmt=stmt.where(m.Report.created_at<datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)+timedelta(days=1))
        except ValueError: raise HTTPException(422,"End date မမှန်ပါ။")
    if flagged=="true": stmt=stmt.where(m.Report.flagged==True)
    elif flagged=="false": stmt=stmt.where(m.Report.flagged==False)
    rows=db.scalars(stmt.order_by(desc(m.Report.created_at)).limit(500)).all()
    result=[report_admin_dict(r,user) for r in rows]
    if q:
        ql=q.lower(); result=[x for x in result if ql in " ".join(str(x.get(k,"")) for k in ("case_id","title","summary","category","location","tags")).lower()]
    return result

@app.get("/api/admin/reports/{case_id}")
def admin_report(case_id:str,user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    return report_admin_dict(case_or_404(db,case_id),user)

@app.patch("/api/admin/reports/{case_id}")
def update_report(case_id:str,data:ReportUpdate,background:BackgroundTasks,request:Request,user:m.User=Depends(admin_write),db:Session=Depends(get_db)):
    report=case_or_404(db,case_id); p=get_payload(report); old_status=report.status
    if data.status is not None:
        allowed={"Pending Review","Under Investigation","Verified & Published","Dismissed"}
        if data.status not in allowed: raise HTTPException(422,"Status မမှန်ပါ။")
        if data.status=="Verified & Published" and user.role not in ("admin","publisher"): raise HTTPException(403,"Publisher/Admin ခွင့်ပြုချက် လိုအပ်ပါသည်။")
        report.status=data.status
    if data.visibility is not None:
        if user.role not in ("admin","publisher"): raise HTTPException(403,"Public/Private ပြောင်းရန် Publisher/Admin ခွင့်ပြုချက် လိုအပ်ပါသည်။")
        if data.visibility not in ("public","private"): raise HTTPException(422,"Visibility မမှန်ပါ။")
        if data.visibility=="public" and report.status!="Verified & Published" and data.status is not None and data.status!="Verified & Published":
            report.visibility="private"
        elif data.visibility=="public" and (report.status!="Verified & Published" or not (data.public_summary or p.get("public_summary"))):
            raise HTTPException(400,"Public ထုတ်ပြန်ရန် Verified status နှင့် Public Summary လိုအပ်ပါသည်။")
        else:
            report.visibility=data.visibility
    if report.status!="Verified & Published": report.visibility="private"
    if data.public_summary is not None:
        if user.role not in ("admin","publisher"): raise HTTPException(403,"Public Summary ပြင်ရန် Publisher/Admin ခွင့်ပြုချက် လိုအပ်ပါသည်။")
        p["public_summary"]=data.public_summary.strip()[:4000]
    if data.public_note is not None:
        if user.role not in ("admin","publisher"): raise HTTPException(403,"Public Status Note ပြင်ရန် Publisher/Admin ခွင့်ပြုချက် လိုအပ်ပါသည်။")
        p["public_note"]=data.public_note.strip()[:2000]
    if data.admin_note is not None:
        if user.role not in ("admin","reviewer"): raise HTTPException(403,"Internal Admin Note ပြင်ရန် Reviewer/Admin ခွင့်ပြုချက် လိုအပ်ပါသည်။")
        p["admin_note"]=data.admin_note.strip()[:3000]
    if data.tags is not None: report.tags_json=json.dumps(list(dict.fromkeys(t.strip()[:40] for t in data.tags if t.strip()))[:20],ensure_ascii=False)
    if data.assigned_team is not None:
        if user.role not in ("admin","reviewer"): raise HTTPException(403,"Assigned Team ပြင်ရန် Reviewer/Admin ခွင့်ပြုချက် လိုအပ်ပါသည်။")
        report.assigned_team=data.assigned_team.strip()[:120] or None
    set_payload(report,p); report.updated_at=utcnow()
    add_audit(db,"report.updated",user.id,report.id,{"status_from":old_status,"status_to":report.status,"visibility":report.visibility,"tags":json_load(report.tags_json,[])})
    if old_status!=report.status:
        notify_admins(db,"status_changed","Case Status ပြောင်းလဲသွားသည်",f"{report.case_id}: {report.status}",report.id)
        email=p.get("contact_email") if p.get("notify_email") else None
        if email: background.add_task(send_email,email,f"PROOF status update: {report.case_id}",f"Your case status changed to: {report.status}. Sign in with your Case ID to view the latest public update.")
    db.commit(); return report_admin_dict(report,user)

@app.post("/api/admin/reports/{case_id}/comments")
def admin_comment(case_id:str,data:CommentIn,user:m.User=Depends(admin_write),db:Session=Depends(get_db)):
    role_check(user,("admin","reviewer","publisher")); report=case_or_404(db,case_id)
    if data.visibility not in ("internal","public"): raise HTTPException(422,"Comment visibility မမှန်ပါ။")
    db.add(m.Comment(report_id=report.id,author_type="admin",author_id=user.id,visibility=data.visibility,body_enc=encrypt_text(data.body.strip())))
    add_audit(db,"comment.admin",user.id,report.id,{"visibility":data.visibility,"length":len(data.body)}); db.commit(); return {"ok":True}

@app.post("/api/admin/reports/{case_id}/attachments")
async def admin_add_attachment(case_id:str,request:Request,file:UploadFile=File(...),user:m.User=Depends(admin_write),db:Session=Depends(get_db)):
    role_check(user,("admin","reviewer")); report=case_or_404(db,case_id)
    active=[a for a in report.attachments if not a.deleted_at]
    if len(active)>=MAX_FILES: raise HTTPException(413,"ဖိုင်အများဆုံးအရေအတွက် ပြည့်နေပါသည်။")
    raw=await file.read(MAX_UPLOAD+1)
    try: stored=store_upload(file.filename or "evidence",file.content_type or "",raw,report.case_id)
    except UploadProblem as exc: raise HTTPException(413,str(exc))
    attachment=m.Attachment(report_id=report.id,**stored); db.add(attachment)
    try:
        db.flush(); add_audit(db,"attachment.added",user.id,report.id,{"attachment_id":attachment.id,"sha256":attachment.sha256}); db.commit()
    except Exception:
        db.rollback(); delete_stored(stored.get("storage_name")); delete_stored(stored.get("preview_storage_name")); raise
    return {"ok":True,"attachment_id":attachment.id}

@app.delete("/api/admin/reports/{case_id}/attachments/{attachment_id}")
def delete_attachment(case_id:str,attachment_id:int,user:m.User=Depends(admin_write),db:Session=Depends(get_db)):
    role_check(user,("admin","reviewer")); report=case_or_404(db,case_id)
    att=db.scalar(select(m.Attachment).where(m.Attachment.id==attachment_id,m.Attachment.report_id==report.id,m.Attachment.deleted_at.is_(None)))
    if not att: raise HTTPException(404,"ဖိုင်မတွေ့ပါ။")
    att.deleted_at=utcnow(); original_name=att.storage_name; preview_name=att.preview_storage_name
    add_audit(db,"attachment.deleted",user.id,report.id,{"attachment_id":att.id,"sha256":att.sha256}); db.commit()
    delete_stored(original_name); delete_stored(preview_name); return {"ok":True}

@app.get("/api/admin/attachments/{attachment_id}")
def download_attachment(attachment_id:int,preview:bool=False,user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    role_check(user,("admin","reviewer"))
    att=db.scalar(select(m.Attachment).where(m.Attachment.id==attachment_id,m.Attachment.deleted_at.is_(None)))
    if not att: raise HTTPException(404,"ဖိုင်မတွေ့ပါ။")
    if preview and att.preview_storage_name:
        data=read_stored(att.preview_storage_name)
        if att.mime_type.startswith("image/"): mime="image/webp"; ext=".webp"
        elif att.mime_type=="application/pdf": mime="application/pdf"; ext=".pdf"
        elif att.mime_type.startswith("video/"): mime="video/mp4"; ext=".mp4"
        else: mime="text/plain"; ext=".txt"
        original_name=decrypt_text(att.original_name_enc) if att.original_name_enc else att.original_name
        filename="preview-"+Path(original_name).stem+ext
    else:
        data=read_stored(att.storage_name); mime=att.mime_type; filename=decrypt_text(att.original_name_enc) if att.original_name_enc else att.original_name
        add_audit(db,"attachment.original_downloaded",user.id,att.report_id,{"attachment_id":att.id,"sha256":att.sha256}); db.commit()
    return Response(data,media_type=mime,headers={"Content-Disposition":f"attachment; filename*=UTF-8''{__import__('urllib.parse').parse.quote(filename)}","X-Content-Type-Options":"nosniff","Cache-Control":"no-store"})

@app.get("/api/admin/stats")
def admin_stats(user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    reports=db.scalars(select(m.Report)).all()
    statuses={s:0 for s in ["Pending Review","Under Investigation","Verified & Published","Dismissed"]}
    categories={}; months={}
    for r in reports:
        statuses[r.status]=statuses.get(r.status,0)+1
        categories[r.category]=categories.get(r.category,0)+1
        month=r.created_at.strftime("%Y-%m"); months[month]=months.get(month,0)+1
    return {"total":len(reports),"statuses":statuses,"categories":categories,"months":dict(sorted(months.items())[-12:]),"flagged":sum(1 for r in reports if r.flagged),"published":sum(1 for r in reports if r.visibility=="public" and r.status=="Verified & Published")}

@app.get("/api/admin/audit")
def admin_audit(limit:int=100,user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(m.AuditLog).order_by(desc(m.AuditLog.created_at)).limit(max(1,min(limit,300)))).all()
    users={u.id:u.username for u in db.scalars(select(m.User)).all()}
    return [{"id":x.id,"actor":users.get(x.actor_id,"System/Anonymous"),"case_id":db.get(m.Report,x.report_id).case_id if x.report_id and db.get(m.Report,x.report_id) else None,"action":x.action,"details":json_load(x.details_json,{}),"created_at":dt_out(x.created_at)} for x in rows]

@app.get("/api/admin/notifications")
def admin_notifications(user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(m.Notification).where((m.Notification.user_id==user.id)|(m.Notification.user_id.is_(None))).order_by(desc(m.Notification.created_at)).limit(100)).all()
    return [{"id":x.id,"kind":x.kind,"title":x.title,"body":x.body,"read":x.is_read,"created_at":dt_out(x.created_at)} for x in rows]

@app.post("/api/admin/notifications/read")
def mark_notifications_read(user:m.User=Depends(admin_write),db:Session=Depends(get_db)):
    db.query(m.Notification).filter((m.Notification.user_id==user.id)|(m.Notification.user_id.is_(None))).update({m.Notification.is_read:True},synchronize_session=False); db.commit(); return {"ok":True}

@app.get("/api/admin/export.csv")
def export_csv(user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    role_check(user,("admin","reviewer"))
    rows=db.scalars(select(m.Report).order_by(desc(m.Report.created_at))).all()
    buf=io.StringIO(); writer=csv.writer(buf); writer.writerow(["Case ID","Status","Visibility","Category","Title","Date","Location","Summary","Anonymous","Tags","Created","Updated"])
    def csv_safe(value):
        text="" if value is None else str(value)
        return "'"+text if text.startswith(("=","+","-","@","\t","\r")) else text
    for r in rows:
        p=get_payload(r); writer.writerow([csv_safe(v) for v in [r.case_id,r.status,r.visibility,r.category,p.get("title"),p.get("incident_date"),p.get("location"),p.get("summary"),p.get("anonymous"),", ".join(json_load(r.tags_json,[])),dt_out(r.created_at),dt_out(r.updated_at)]])
    add_audit(db,"export.csv",user.id,None,{"count":len(rows)}); db.commit()
    return Response("\ufeff"+buf.getvalue(),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=proof-cases.csv"})

@app.get("/api/admin/export.pdf")
def export_pdf(user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    role_check(user,("admin","reviewer"))
    rows=db.scalars(select(m.Report).order_by(desc(m.Report.created_at))).all()
    data=[{"case_id":r.case_id,"status":r.status,"category":r.category,"created_at":dt_out(r.created_at),"title":get_payload(r).get("title"),"location":get_payload(r).get("location"),"summary":get_payload(r).get("summary"),"tags":json_load(r.tags_json,[])} for r in rows]
    pdf=export_reports_pdf(data); add_audit(db,"export.pdf",user.id,None,{"count":len(rows)}); db.commit()
    return Response(pdf,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=proof-cases.pdf"})

@app.get("/api/admin/settings")
def admin_settings(user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    role_check(user,("admin",))
    return {"hotlines":setting(db,"hotlines",[]),"category_routes":setting(db,"category_routes",{}),"session_timeout":setting(db,"session_timeout",SESSION_IDLE_MINUTES),"smtp_ready":smtp_ready()}

@app.put("/api/admin/settings")
def update_settings(data:SettingsIn,user:m.User=Depends(admin_write),db:Session=Depends(get_db)):
    role_check(user,("admin",))
    if data.hotlines is not None:
        cleaned=[]
        for h in data.hotlines[:20]:
            label=str(h.get("label","")).strip()[:80]; number=str(h.get("number","")).strip()
            if label and re.fullmatch(r"\+?[0-9*# -]{3,30}",number): cleaned.append({"label":label,"number":number})
        save_setting(db,"hotlines",cleaned)
    if data.category_routes is not None:
        cleaned={}
        for k,v in list(data.category_routes.items())[:30]:
            k=str(k)[:100]; v=str(v).strip()[:254]
            if v and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",v): raise HTTPException(422,f"{k} အတွက် Email မမှန်ပါ။")
            cleaned[k]=v
        save_setting(db,"category_routes",cleaned)
    if data.session_timeout is not None:
        save_setting(db,"session_timeout",data.session_timeout)
    add_audit(db,"settings.updated",user.id,None,{}); db.commit(); return admin_settings(user,db)

@app.get("/api/admin/feedback")
def admin_feedback(user:m.User=Depends(admin_user),db:Session=Depends(get_db)):
    role_check(user,("admin",))
    rows=db.scalars(select(m.Feedback).order_by(desc(m.Feedback.created_at)).limit(200)).all()
    return [{"id":x.id,"rating":x.rating,"message":decrypt_text(x.message_enc),"email":decrypt_text(x.email_enc) if x.email_enc else "","created_at":dt_out(x.created_at)} for x in rows]

@app.post("/api/admin/users")
def create_staff(data:UserIn,user:m.User=Depends(admin_write),db:Session=Depends(get_db)):
    role_check(user,("admin",))
    if data.role not in ("admin","reviewer","publisher"): raise HTTPException(422,"Role မမှန်ပါ။")
    row=m.User(username=data.username.strip(),email=data.email.strip() if data.email else None,password_hash=password_hash(data.password),role=data.role)
    db.add(row)
    try: db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409,"Username ရှိပြီးသားဖြစ်သည်။")
    add_audit(db,"staff.created",user.id,None,{"username":row.username,"role":row.role}); db.commit()
    return {"ok":True,"username":row.username,"role":row.role}

@app.get("/api/admin/templates")
def admin_templates(user:m.User=Depends(admin_user)): return DEFAULT_TEMPLATES

@app.get("/manifest.webmanifest")
def manifest():
    return JSONResponse({"name":"PROOF Accountability Portal","short_name":"PROOF","start_url":"/","display":"standalone","background_color":"#0a0e17","theme_color":"#0a0e17","icons":[]},media_type="application/manifest+json")

@app.get("/sw.js")
def service_worker(): return FileResponse(Path(__file__).resolve().parents[1]/"static"/"sw.js",media_type="application/javascript",headers={"Service-Worker-Allowed":"/","Cache-Control":"no-cache"})

@app.exception_handler(Exception)
async def safe_error(request:Request,exc:Exception):
    # Never log request bodies, IPs, or exception text that might contain sensitive report content.
    if isinstance(exc,HTTPException): return JSONResponse(status_code=exc.status_code,content={"detail":exc.detail})
    return JSONResponse(status_code=500,content={"detail":"Server error. Reference the server health and application logs without including report content."})
