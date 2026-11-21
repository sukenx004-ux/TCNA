# PROOF V3 — Android Local Test (Termux)

ဒီ edition ကို Android ဖုန်းတစ်လုံးတည်းမှာ local စမ်းသုံးရန် ပြင်ဆင်ထားသည်။ Public Internet ပေါ်သို့ မတင်ပါ။ Database သည် `data/proof.db` (SQLite) ဖြစ်ပြီး Evidence များကို `data/evidence/` ထဲတွင် encrypted သိမ်းသည်။

## 1. Termux ထည့်သွင်းရန်

Termux ကို F-Droid သို့မဟုတ် Termux GitHub Releases မှသာ ထည့်ပါ။ Google Play Store ရှိ အဟောင်း version ကို မသုံးပါနှင့်။ Source မတူသော Termux APK များကို အပြန်အလှန် update မလုပ်နိုင်သည့်အတွက် တစ်ခုတည်းသော source ကို အမြဲသုံးပါ။

- F-Droid: https://f-droid.org/en/packages/com.termux/
- GitHub: https://github.com/termux/termux-app/releases

## 2. ZIP ဖိုင်ကို ဖုန်းထဲသို့ ယူရန်

1. `PROOF-PORTAL-V3-100-FEATURE-DEMO.zip` ကို Android Downloads ထဲသို့ Download လုပ်ပါ။
2. Termux ကိုဖွင့်ပြီး အောက်ပါ command များကို run လုပ်ပါ။

```bash
pkg update -y
pkg install -y unzip
termux-setup-storage
```

Permission တောင်းလျှင် Allow နှိပ်ပါ။ ထို့နောက်:

```bash
mkdir -p ~/proof-v3
cd ~/storage/downloads
unzip PROOF-PORTAL-V3-100-FEATURE-DEMO.zip -d ~/proof-v3
cd ~/proof-v3/PROOF-Portal
```

## 3. Setup လုပ်ရန်

```bash
bash android-setup.sh
```

ပထမဆုံးအကြိမ်တွင် Python packages များ Download/Install လုပ်ရန် အင်တာနက်လိုသည်။ အချိန်အနည်းငယ်ကြာနိုင်သည်။

## 4. Admin Account ဖန်တီးရန်

```bash
source .venv/bin/activate
python -m app.cli create-admin --username admin --email admin@example.com
```

Password ကို ကိုယ်တိုင်ထည့်ပါ။ အနည်းဆုံး 12 characters ရှိရမည်။ Password ရိုက်နေချိန်မှာ မျက်နှာပြင်ပေါ် မပေါ်ခြင်းက ပုံမှန်ဖြစ်သည်။

## 5. Server စတင်ရန်

```bash
bash android-start.sh
```

Termux ကို ဖွင့်ထားပြီး Chrome ကိုဖွင့်ပါ။ ဒီလိပ်စာကို သွားပါ:

`http://127.0.0.1:8000`

API health စစ်ရန်:

`http://127.0.0.1:8000/api/health`

100 Feature Demo: `http://127.0.0.1:8000/demo`

API docs:

`http://127.0.0.1:8000/api/docs`

## 6. Server ရပ်ရန် / ပြန်ဖွင့်ရန်

Termux ကို ပြန်ဝင်ပြီး `Ctrl+C` နှိပ်ပါ။ နောက်တစ်ကြိမ် စမ်းသုံးရန် `bash android-start.sh` ကို ထပ် run လုပ်ပါ။ Server run နေစဉ် Termux ကို Force stop မလုပ်ပါနှင့်။ Android Battery settings ထဲမှာ Termux အတွက် Battery usage ကို Unrestricted / Don't optimize ထားပါ။

## 7. Data သိမ်းဆည်းရာနေရာ

- SQLite database: `data/proof.db`
- Encrypted evidence: `data/evidence/`
- Encryption key: `data/.fernet.key`
- Configuration: `.env`

ဒီ ၄ ခုကို မဖျက်ပါနှင့်။ Backup လုပ်လျှင် database, evidence folder, encryption key တို့ကို အတူတူ backup လုပ်ပါ။ Key ပျောက်သွားပါက encrypted report/evidence ကို ပြန်ဖတ်မရနိုင်ပါ။

## Android Local Test ကန့်သတ်ချက်များ

- ဒီ server သည် `127.0.0.1` ကိုသာ listen လုပ်သောကြောင့် ဖုန်းတစ်လုံးတည်းမှသာ ဝင်သုံးနိုင်သည်။ Public website မဟုတ်ပါ။
- SQLite သည် ဖုန်းထဲတွင်သာရှိသည်။ App data ဖျက်ခြင်း၊ Termux uninstall လုပ်ခြင်း သို့မဟုတ် data folder ဖျက်ခြင်းကြောင့် data ပျောက်နိုင်သည်။
- Email notification, email forwarding နှင့် email password recovery အတွက် SMTP မထည့်ထားပါ။ Password မေ့ပါက Termux မှ `python -m app.cli reset-password --username admin` ကို အသုံးပြုပါ။
- PDF export သည် ReportLab fallback ဖြင့် ထုတ်နိုင်သည်။ Built-in PDF font သည် Latin-only ဖြစ်သောကြောင့် Burmese စာသားအချို့ မမှန်နိုင်ပါ။ အပြည့်အစုံ Burmese PDF အတွက် WeasyPrint ပါသော Linux/Docker server ကို အသုံးပြုပါ။ CSV export ကိုလည်း အသုံးပြုနိုင်သည်။
- Video watermark preview အတွက် ffmpeg လိုအပ်သည်။ မဖြစ်မနေလိုပါက Termux တွင် `pkg install ffmpeg` ထည့်နိုင်သည်။ Original video ကို encrypted သိမ်းထားသည်။
- Browser Speech Recognition သည် Chrome/Android support နှင့် Internet ပေါ်မူတည်သည်။
- Offline draft သာ local အဖြစ်သိမ်းနိုင်သည်။ Final report တင်ရန် server run နေပြီး connection ရှိရမည်။
- စမ်းသပ်ချိန်တွင် အတုအယောင် data ကိုသာ အသုံးပြုပါ။ တကယ့် လျှို့ဝှက်/အန္တရာယ်ရှိသော အချက်အလက်များကို public service မဟုတ်သေးသော ဖုန်းတစ်လုံးထဲရှိ test server တွင် မထည့်ပါနှင့်။

## ပြဿနာဖြေရှင်းရန်

- `Permission denied`: `termux-setup-storage` ပြန် run လုပ်ပြီး permission Allow ပေးပါ။
- `No module named PIL` သို့မဟုတ် `cryptography`: `pkg install python-pillow python-cryptography -y` ပြန် run လုပ်ပါ၊ ထို့နောက် `.venv` ကို ပြန်ဖန်တီးပြီး setup script ပြန် run လုပ်ပါ။
- `Address already in use`: server တစ်ခု run နေပြီးသားဖြစ်နိုင်သည်။ အရင် Termux session ထဲမှာ Ctrl+C နှိပ်ပါ။
- Server ပိတ်သွားသည်: Termux ကို foreground မှာထားပါ၊ Battery optimization ပိတ်ပါ၊ `bash android-start.sh` ပြန် run လုပ်ပါ။
