from __future__ import annotations
import argparse, getpass, os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import select
from .db import Base, engine, SessionLocal, DATA_DIR
from .models import User, AdminSession
from cryptography.fernet import Fernet

def prompt_password(label="Password"):
    while True:
        first=getpass.getpass(f"{label} (အနည်းဆုံး 12 characters): ")
        second=getpass.getpass("Confirm password: ")
        if first!=second: print("Password မတူပါ။ ထပ်ကြိုးစားပါ။"); continue
        if len(first)<12: print("12 characters အနည်းဆုံးလိုအပ်သည်။"); continue
        return first

def main():
    parser=argparse.ArgumentParser(prog="proof-cli")
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("generate-secrets")
    p=sub.add_parser("create-admin"); p.add_argument("--username",default="admin"); p.add_argument("--email",default="")
    p=sub.add_parser("create-staff"); p.add_argument("--username",required=True); p.add_argument("--email",default=""); p.add_argument("--role",choices=["admin","reviewer","publisher"],default="reviewer")
    p=sub.add_parser("reset-password"); p.add_argument("--username",required=True)
    args=parser.parse_args()
    if args.command=="generate-secrets":
        env=Path(".env")
        content=env.read_text() if env.exists() else "APP_ENV=development\nDATABASE_URL=sqlite:///./data/proof.db\n"
        import re
        existing=re.search(r"^PROOF_ENCRYPTION_KEY=(.+)$",content,re.M)
        if existing and existing.group(1).strip() and existing.group(1).strip()!="REPLACE_WITH_FERNET_KEY":
            print(".env ထဲတွင် Encryption Key ရှိပြီးသားဖြစ်သည်။ Data မပျက်စေရန် မပြောင်းလဲပါ။")
            return
        fallback=DATA_DIR/".fernet.key"
        key=fallback.read_text().strip() if fallback.exists() else Fernet.generate_key().decode()
        if existing: content=re.sub(r"^PROOF_ENCRYPTION_KEY=.*$",f"PROOF_ENCRYPTION_KEY={key}",content,flags=re.M)
        else: content+=f"\nPROOF_ENCRYPTION_KEY={key}\n"
        env.write_text(content)
        try: env.chmod(0o600)
        except OSError: pass
        print("Encryption key ကို .env ထဲတွင် သိမ်းပြီးပါပြီ။ Backup လုပ်ပြီး လျှို့ဝှက်ထားပါ။ Key ပျောက်လျှင် encrypted data ကို ပြန်ဖတ်မရနိုင်ပါ။")
        return
    from .security import password_hash
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if args.command in ("create-admin","create-staff"):
            username=args.username.strip()
            if db.scalar(select(User).where(User.username==username)):
                print("Username ရှိပြီးသားဖြစ်သည်။"); return
            pwd=prompt_password()
            role="admin" if args.command=="create-admin" else args.role
            row=User(username=username,email=args.email.strip() or None,password_hash=password_hash(pwd),role=role)
            db.add(row); db.commit()
            print(f"Created {role}: {username}")
        elif args.command=="reset-password":
            user=db.scalar(select(User).where(User.username==args.username))
            if not user: print("User မတွေ့ပါ။"); return
            user.password_hash=password_hash(prompt_password("New password"))
            db.query(AdminSession).filter(AdminSession.user_id==user.id).delete(synchronize_session=False)
            db.commit(); print("Password reset လုပ်ပြီးပါပြီ။ Login ပြန်ဝင်ပါ။")

if __name__=="__main__": main()
