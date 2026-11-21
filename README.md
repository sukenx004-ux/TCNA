# PROOF Accountability Portal — Server Edition

မူလ Server Portal တွင် Feature registry နှင့် Core Portal capabilities ကို Database/API အခြေခံဖြင့် ထည့်သွင်းထားသည်။ ထပ်မံ၍ Screenshot များမှ စုစည်းထားသော **Complete Feature Registry + 100 Feature Interactive Demo** ကို `/demo` တွင် ထည့်ထားသည်။

ဤ Project တွင် FastAPI backend + PostgreSQL/SQLite database + encrypted evidence storage ပါဝင်သော self-hosted web application နှင့် သီးခြား Demo Lab ပါဝင်သည်။ Production Case Database ကို Browser Local Storage ဖြင့် အစားမထိုးပါ။ Demo Lab ၏ test data သာ ဖုန်း Browser ထဲတွင် local သိမ်းသည်။

**UI Color:** Main Portal နှင့် Demo Lab ကို Screenshot နှင့်ကိုက်ညီသော Black & Gold palette (`#0A0E17`, `#141B2E`, `#F39E0D`) ဖြင့် ပြင်ဆင်ထားသည်။

## ပါဝင်သော Feature များ

| နံပါတ် | လုပ်ဆောင်ချက် | အလုပ်လုပ်ပုံ |
|---|---|---|
| 1 | Anonymous / confidential report | အမည်မတောင်းဘဲတင်နိုင်၊ report content/contact ကို application encryption ဖြင့် သိမ်း |
| 2 | Emergency / email notifications | Hotline ခေါ်ဆိုမှု၊ optional submitter email၊ SMTP admin alert |
| 3 | Evidence edit/delete | Admin က file အသစ်ထည့်၊ ဖိုင်ဖျက်၊ original/preview ကို ရယူနိုင် |
| 4 | Category/date filters | Admin list တွင် category, status, date range, keyword filter |
| 5, 28 | Dark/Light theme | Browser preference ဖြင့် ပြောင်းလဲသိမ်း |
| 6 | PDF export | Admin-authenticated PDF export |
| 7 | Status alerts | In-app admin notifications၊ email opt-in submitter alert၊ Case status lookup |
| 8 | Public/Private | Verified + Public Summary ရှိမှသာ public ထုတ်ပြန်နိုင် |
| 9 | FAQ | Public FAQ page |
| 10 | Cloud server/API | FastAPI REST API; PostgreSQL production / SQLite development |
| 11 | Case comments | Submitter comments, internal/public admin comments |
| 12 | Panic button | Local draft ဖျက်၊ page မှ ချက်ချင်းထွက်; server report မဖျက် |
| 13 | Multi-language | မြန်မာ/English switch; navigation, common UI labels, FAQ နှင့် templates; user-entered content သည် မူရင်းဘာသာဖြင့်သာ ပြမည် |
| 14 | File compression | Image/video preview ကို re-encode/compress; evidence integrity အတွက် original ကို encrypted အတိုင်းထိန်းသိမ်း (upload bandwidth ကို မလျှော့ပါ) |
| 15 | Multiple files | Image/PDF/TXT/MP4/WebM, configurable max count/size |
| 16 | Voice-to-Text | Browser Speech Recognition ပံ့ပိုးပါက အသုံးပြုနိုင် |
| 26 | Admin password recovery | SMTP ချိတ်ထားလျှင် one-time email link; SMTP မရှိလျှင် server CLI reset |
| 27 | Offline Mode | App shell cache + offline draft save/restore; final submit ကို Internet ရှိမှသာ server သို့ပို့ |
| 29 | Automatic forwarding | Category routing email ကို admin settings မှ သတ်မှတ်၊ SMTP ဖြင့် forward |
| 30 | Auto moderation | Honeypot, in-memory rate limit, duplicate/link heuristics; suspicious report ကို Flag လုပ်၍ human review |
| 31 | IP/location privacy | App က IP/Device Location ကို database ထဲ မသိမ်း၊ browser geolocation မတောင်း၊ image preview မှ EXIF/GPS metadata ဖယ် |
| 32 | QR Code | Case ID lookup link QR |
| 33 | Audio feedback | Submit/status အောင်မြင်မှုကို browser speech synthesis ဖြင့် ဖတ်ပြ |
| 34 | Audit trail | Status, visibility, comments, files, export, login စသည့် admin actions မှတ်တမ်း |
| 35 | Hotline buttons | Admin သတ်မှတ်ထားသော ဖုန်းနံပါတ်များကို tap-to-call |
| 36 | Templates | Report form အတွက် အသင့်သုံး templates |
| 37 | Dashboard charts | Status/category/month charts |
| 38 | Tags | Case တစ်ခုချင်းစီတွင် tags ထည့်/ပြင် |
| 39 | Watermark | Image/PDF/video အတွက် watermarked preview ထုတ်; original evidence နှင့် original filename ကို encrypted သိမ်း |
| 40 | Feedback form | Public feedback + admin review |
| 41 | Session timeout | Server-side idle timeout + browser auto logout; default 15 minutes |


## Complete Feature Registry + 100 Feature Interactive Demo

Portal တွင် Login မလိုဘဲ `/demo` သို့ဝင်ပြီး Feature 100 ခုကို တစ်ခုချင်း စမ်းနိုင်သည်။ Search, Category Filter, Tested Progress, Reset, File Hash, Image Compression, Watermark, CSV Export/Import, AES-GCM browser encryption test, offline draft queue, QR lookup, Case ID lookup, Feedback API, Password Recovery API, Server Health, API latency, speech recognition, theme, font, PIN/OTP simulation, map link, archive/restore စသည့်လုပ်ဆောင်ချက်များ ပါဝင်သည်။

**အရေးကြီးသော ခွဲခြားချက်:** 100 Feature Lab သည် အပြည့်အဝစမ်းသပ်နိုင်ရန် ရည်ရွယ်ထားသော Demo ဖြစ်သည်။ Local Demo state များသည် Browser ထဲတွင်သာ သိမ်းသည်။ Telegram/Viber Bot, SMS, SMTP, AI cloud assistant, live GPS, biometric authentication, screenshot blocking, production 2FA နှင့် cloud backup တို့ကို အမှန်တကယ် Live အသုံးပြုရန် သက်ဆိုင်ရာ provider credentials, HTTPS, device/browser API နှင့် server configuration လိုအပ်သည်။ Demo UI သည် ထို Integration များကို ချိတ်ထားသကဲ့သို့ မဟန်ဆောင်ပါ။ Browser မှ Screenshot ကို လုံးဝတားဆီး၍ မရပါ။

Demo ထဲရှိ Feature 10, 26, 32, 34, 40, 62, 94, 97 တို့သည် သက်ဆိုင်ရာအခြေအနေအလိုက် လက်ရှိ Server API ကို တကယ်ခေါ်စမ်းသည်။ Admin-only API များအတွက် Admin Login လိုအပ်နိုင်သည်။

## Android ဖုန်းတစ်လုံးတည်းတွင် Local Demo စမ်းရန် (Termux)

အဆင့်လိုက် လမ်းညွှန်ကို `README-ANDROID-MM.md` တွင် ဖတ်ပါ။ အတိုချုပ်အားဖြင့် Termux ကို F-Droid သို့မဟုတ် Termux GitHub Releases မှ တပ်ဆင်ပြီး ZIP ကို Extract လုပ်ပါ။ ထို့နောက်:

```bash
pkg update -y
pkg install -y unzip
termux-setup-storage
cd ~/storage/downloads
unzip PROOF-PORTAL-V3-100-FEATURE-DEMO.zip -d ~/proof-v3
cd ~/proof-v3/PROOF-Portal
bash android-setup.sh
source .venv/bin/activate
python -m app.cli create-admin --username admin --email admin@example.com
bash android-start.sh
```

Chrome တွင် `http://127.0.0.1:8000` ကိုဖွင့်ပါ။ 100 Feature Lab အတွက် `http://127.0.0.1:8000/demo` ကိုဖွင့်ပါ။ Admin Password ကို ကိုယ်တိုင်သတ်မှတ်ပါ။ ဒီ Android setup သည် ဖုန်းတစ်လုံးတည်းအတွက် Local Test ဖြစ်ပြီး Public Website မဟုတ်ပါ။

## Local development (Windows / macOS / Linux)

Python 3.11+ လိုအပ်သည်။

```bash
cd PROOF-Portal
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli generate-secrets
python -m app.cli create-admin --username admin --email admin@example.org
uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Browser တွင် `http://127.0.0.1:8000` ဖွင့်ပါ။ Admin login အတွက် create-admin အဆင့်တွင် သင်သတ်မှတ်ထားသော username/password ကို အသုံးပြုပါ။ Default password မပါဝင်ပါ။

## Production deployment (Docker + PostgreSQL)

1. Server/VPS တစ်ခုတွင် Docker + Docker Compose တပ်ဆင်ပါ။ Domain ၏ DNS A/AAAA record ကို VPS IP သို့ ချိတ်ပြီး inbound port 80/443 ဖွင့်ပါ။ ပါဝင်ပြီးသား Caddy သည် HTTPS certificate ကို အလိုအလျောက် ရယူပါမည်။
2. `.env.example` ကို `.env` အဖြစ်ကူးပြီး အောက်ပါအချက်များ ဖြည့်ပါ။
   - `POSTGRES_PASSWORD`: ခန့်မှန်းရခက်ပြီး URL-safe (A–Z, a–z, 0–9, `_`, `-`) ဖြစ်သော database password
   - `PROOF_ENCRYPTION_KEY`: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` ဖြင့် ထုတ်ပါ
   - `DOMAIN`: `your-domain.example`
   - `APP_BASE_URL`: `https://your-domain.example`
   - SMTP settings: Email notification/password recovery လိုအပ်ပါက ဖြည့်ပါ
3. Compose file သည် `POSTGRES_PASSWORD` ကိုလည်း လိုအပ်သဖြင့် `.env` ထဲတွင် သီးခြားထည့်ပါ။
4. Run:

```bash
docker compose up -d --build
docker compose exec web python -m app.cli create-admin --username admin --email admin@your-domain.example
```

5. Caddy သည် `web:8000` သို့ reverse proxy လုပ်ပြီး HTTPS ကို အလိုအလျောက် ဖွင့်ပေးပါမည်။ Uvicorn access log ကို ပိတ်ထားသည်။ Caddy/Hosting provider logs ထဲတွင် client IP မသိမ်းစေရန် provider policy ကိုလည်း သီးခြားစစ်ဆေးပါ။

## Email Routing

Admin Login → System Settings → Category Email Routing ထဲတွင် JSON ထည့်ပါ။ ဥပမာ:

```json
{
  "အဂတိလိုက်စားမှု / လိမ်လည်မှု": "integrity-team@example.org",
  "လုံခြုံရေး စည်းမျဉ်းဖောက်ဖျက်မှု": "safety-team@example.org",
  "default": "admin@example.org"
}
```

SMTP မချိတ်ထားပါက database/in-app notifications အလုပ်လုပ်မည်၊ Email forward/recovery မပို့နိုင်ပါ။

## Staff accounts

Admin login ဝင်ပြီး Admin Dashboard ၏ Staff Access Form မှ staff ဖန်တီးနိုင်သည်။ API `POST /api/admin/users` လည်း အသုံးပြုနိုင်သည်။ Role များမှာ `admin`, `reviewer`, `publisher` ဖြစ်သည်။ Reviewer သည် report/evidence ကို စိစစ်ပြီး internal note ရေးနိုင်သည်။ Publisher သည် contact email, original evidence နှင့် internal comments မမြင်ဘဲ public summary/visibility ကိုသာ ထိန်းချုပ်နိုင်သည်။ Admin သည် staff/settings အားလုံးကို စီမံနိုင်သည်။ ပထမ Admin ကို CLI ဖြင့် ဖန်တီးပါ။

Password ကို email link ဖြင့် reset လုပ်ရန် SMTP ကို configure လုပ်ထားရမည်။ SMTP မရှိလျှင် server shell မှ:

```bash
docker compose exec web python -m app.cli reset-password --username admin
```

## Data / Security notes — မဖြစ်မနေဖတ်ရန်

- Report body, contact email, comments, feedback, evidence files နှင့် original filenames များကို application encryption ဖြင့် သိမ်းဆည်းသည်။ `PROOF_ENCRYPTION_KEY` ပျောက်သွားပါက ထို encrypted data များကို ပြန်ဖတ်မရနိုင်ပါ။ Key ကို password manager/offline secure backup ထဲတွင် သိမ်းပါ။ Key ကို database backup နှင့်အတူ တစ်နေရာတည်း မထားပါနှင့်။
- Database နှင့် `/app/data` evidence volume ကို သီးခြား encrypted backup လုပ်ပါ။ Restore လုပ်ရန် encryption key လိုအပ်သည်။
- Application သည် IP address သို့မဟုတ် GPS location ကို database ထဲ မသိမ်းပါ။ Rate limiting အတွက် request host ကို memory ထဲ ယာယီအသုံးပြုပြီး persist မလုပ်ပါ။ သို့သော် Hosting Provider, CDN, reverse proxy, ISP သို့မဟုတ် browser က IP/network metadata ကို log လုပ်နိုင်သည်။ အမည်မဖော်မှုကို လုံးဝအာမမခံပါ။
- Original evidence ကို မပြောင်းလဲဘဲ encrypt လုပ်သိမ်းထားသည်။ Watermark/metadata-stripped/compressed files များသည် preview derivatives ဖြစ်သည်။ Original download ကို Audit Log တွင် မှတ်တမ်းတင်သည်။
- Offline mode သည် စာသား/ဖောင်အချက်အလက် draft ကိုသာ local browser ထဲ သိမ်းသည်။ Evidence file များကို offline draft နှင့်အတူ မသိမ်းပါ။ Offline ဖြစ်နေချိန်တွင် report ကို server သို့ မပို့နိုင်ပါ။ Shared device တွင် draft မထားပါနှင့်။
- Auto moderation သည် spam heuristic သာဖြစ်ပြီး AI/human investigation အစားမထိုးပါ။ Flagged report များကို staff က စိစစ်ရမည်။
- ဤ project ကို public internet ပေါ် မတင်မီ threat model, legal/privacy review, backup restore test, mail delivery test, malware scanning strategy, penetration test, admin access review တို့ လုပ်ဆောင်ပါ။
- လက်ရှိ deployment package သည် server software ကို ပေးထားခြင်းဖြစ်သည်။ OpenAI/ChatGPT မှ သင့်အတွက် domain, hosting account, SMTP, TLS certificate သို့မဟုတ် cloud database ကို အလိုအလျောက် provision မလုပ်ထားပါ။ Server ပေါ် deploy လုပ်ပြီးမှ အများသုံးအဖြစ် တကယ်အသုံးပြုနိုင်မည်။

## Automated tests

```bash
python -m pytest -q
```

## API

- Demo: `/demo`
- Public: `/api/health`, `/api/public/config`, `/api/public/stats`, `/api/public/records`, `/api/reports`, `/api/cases/{case_id}`
- Admin: `/api/admin/reports`, `/api/admin/stats`, `/api/admin/audit`, `/api/admin/export.csv`, `/api/admin/export.pdf`, `/api/admin/settings`
- Development API docs: `/api/docs`

Production mode တွင် interactive API docs ပိတ်ထားသည်။

## V3.1 Mobile smoothness patch (2026-11-19)

This patch improves responsiveness on Android and lower-memory browsers:
- Debounced the 100-feature catalog search and admin case search to avoid rendering or API calls on every keystroke.
- Added a 20-second API request timeout and clearer mobile-friendly network errors.
- Added reduced-motion accessibility handling and reduced expensive visual effects on small screens.
- Updated the service-worker shell cache version and kept all `/api/` responses out of cache; offline fallback is limited to cached app-shell pages/assets.

Validation performed for this patch: Python compile check, JavaScript syntax checks, and the existing API test suite. The 8 existing API tests pass. This is not a claim that every item in the 100-feature catalog is production-live; demo-only integrations still require implementation and, where relevant, provider credentials.


## Complete Feature Registry

`static/feature-registry.json` သည် Security, User/Team, Case, Investigation, Evidence, Chain of Custody, AI, Location, Timeline, Notification, Analytics, Reporting, Search, Archive/Data, Mobile/PWA, UI/UX, Admin/System, API/Integration, Reliability နှင့် Emergency/Operational အပါအဝင် တောင်းဆိုထားသော feature catalog အားလုံးကို စုစည်းထားသည်။ Portal ၏ Feature Hub က registry ကို တိုက်ရိုက်ဖတ်ပြီး search/filter/export လုပ်နိုင်သည်။ Browser-local feature toggles များသည် workspace state ဖြစ်ပြီး OAuth, biometric, SMS, live maps, AI cloud, push delivery, production backup စသည့် provider/backend လိုအပ်သော integration များကို credential မရှိဘဲ fake-live မလုပ်ထားပါ။


## Complete feature registry
The bundled registry includes the full requested expansion and is exposed through the Feature Suite UI. Provider-dependent capabilities still require production credentials/backend services.

## Complete Feature Registry

The bundled `static/feature-registry.json` contains the complete feature catalog requested in the conversation, including the original 627 entries plus the additional advanced organization, intelligence, evidence, review, relationship, historical, decision-support, security-intelligence, data-integrity, knowledge, training, simulation, collaboration, physical-evidence, classification, legal/policy, sharing, monitoring, configuration, AI-governance, localization, self-service-admin, governance and future-ready entries.

The registry is a product/UX capability catalog. Features requiring external credentials, third-party providers, production backend services, device capabilities, or infrastructure are represented as integration-ready surfaces rather than falsely claimed as live services.


## Smooth / 120Hz readiness
The web app cannot force a device display refresh rate. The UI is optimized to keep main-thread work small enough for 60Hz (16.67ms) and 120Hz (8.33ms) frame budgets: feature cards are paginated, event handlers are delegated, touch hover transforms are disabled, mobile backdrop filters are reduced, and the PWA shell caches the feature assets.
