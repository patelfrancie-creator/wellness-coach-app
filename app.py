"""
OneSattva — Health, understood.
app.py · June 2026
Stack: Streamlit / Supabase / Anthropic Claude Sonnet / Resend / GitHub / Streamlit Cloud
Supabase: fxzqxovsisdbfgixnjgj — profiles table PK is `id` not `user_id`
UI source of truth: OneSattva_Prototype_Part1.html + OneSattva_Prototype_Part2.html
"""

import streamlit as st
import anthropic
import json as _json
import statistics
from datetime import date, datetime, timedelta
import pandas as pd
from supabase import create_client, Client

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="OneSattva — Health, understood.",
    page_icon="data:image/svg+xml,<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 100 100\'><circle cx=\'50\' cy=\'50\' r=\'42\' fill=\'%23B6744A\'/></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL CSS — verbatim from prototype Part 2
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url(\'https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;1,6..72,300;1,6..72,400&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap\');
:root{
  --bone:#F7F5F2;--graphite:#111214;--copper:#B6744A;
  --stone:#E6E3DF;--forest:#1F2F2A;--mid:#6B6358;
  --white:#FFFFFF;--line:rgba(17,18,20,0.09);--linem:rgba(17,18,20,0.14);
  --cu-bg:rgba(182,116,74,0.08);--cu-bd:rgba(182,116,74,0.22);
}
html,body,[class*="css"]{font-family:\'Inter\',sans-serif;font-size:14px;color:var(--graphite);}
.stApp{background-color:var(--bone);}
/* Sidebar */
[data-testid="stSidebar"]{background-color:var(--graphite)!important;}
[data-testid="stSidebar"] *{color:var(--bone)!important;}
[data-testid="stSidebar"] hr{border-color:rgba(247,245,242,0.07)!important;}
[data-testid="stSidebar"] [data-testid="stButton"]>button{
  background:transparent!important;border:none!important;border-radius:8px!important;
  color:rgba(247,245,242,0.48)!important;font-family:Inter,sans-serif!important;
  font-size:13px!important;font-weight:400!important;text-align:left!important;
  padding:9px 8px!important;margin-bottom:1px!important;width:100%!important;
  transition:all 0.12s!important;display:flex!important;align-items:center!important;gap:9px!important;
}
[data-testid="stSidebar"] [data-testid="stButton"]>button:hover{
  background:rgba(247,245,242,0.05)!important;color:rgba(247,245,242,0.8)!important;
}
/* Main buttons */
.stButton>button{border-radius:8px;border:1.5px solid var(--linem);color:var(--graphite);
  background:var(--white);font-weight:500;font-family:\'Inter\',sans-serif;font-size:13px;transition:all 0.15s;}
.stButton>button:hover{background:var(--graphite);color:var(--bone);border-color:var(--graphite);}
.stButton>button[kind="primary"]{background:var(--graphite);border-color:var(--graphite);color:var(--bone);}
.stButton>button[kind="primary"]:hover{opacity:0.82;}
/* Tabs — pill style matching prototype .st class */
.stTabs [data-baseweb="tab-list"]{gap:5px;background:transparent;padding:0;margin-bottom:16px;}
.stTabs [data-baseweb="tab"]{border-radius:20px;color:var(--mid);font-weight:500;
  padding:6px 13px;font-family:\'Inter\',sans-serif;font-size:12px;
  border:1.5px solid var(--line);background:transparent;}
.stTabs [aria-selected="true"]{background:var(--graphite)!important;border-color:var(--graphite)!important;color:var(--bone)!important;}
.stTabs [data-baseweb="tab-border"]{display:none;}
.stTabs [data-baseweb="tab-highlight"]{display:none;}
/* Metrics */
[data-testid="stMetric"]{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:13px 14px;}
[data-testid="stMetricLabel"]{color:var(--mid)!important;font-family:\'Inter\',sans-serif;font-size:10px!important;font-weight:600!important;letter-spacing:0.07em!important;text-transform:uppercase!important;}
[data-testid="stMetricValue"]{color:var(--graphite)!important;font-family:\'JetBrains Mono\',monospace!important;font-size:21px!important;font-weight:500!important;}
[data-testid="stMetricDelta"]{font-size:11px!important;}
/* Chat */
[data-testid="stChatMessage"]{background:var(--white);border:1px solid var(--line);border-radius:12px 12px 12px 2px;}
/* Alerts / dividers */
[data-testid="stAlert"]{border-radius:10px;border-left-width:3px;}
hr{border-color:var(--line)!important;margin:1.2rem 0!important;}
/* Prototype CSS classes — verbatim from Part 2 */
.sl{font-size:10px;font-weight:600;letter-spacing:0.09em;text-transform:uppercase;color:var(--mid);margin-bottom:9px;margin-top:20px;display:block;}
.sl.first{margin-top:0;}
.plan-banner{background:var(--forest);border-radius:10px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;}
.pb-l{display:flex;align-items:center;gap:14px;}
.pb-ml{font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:rgba(247,245,242,0.4);}
.pb-mn{font-family:\'Newsreader\',serif;font-style:italic;font-size:16px;color:#F7F5F2;margin-top:1px;}
.pb-bar-w{display:flex;align-items:center;gap:8px;}
.pb-bar{width:112px;height:4px;background:rgba(247,245,242,0.14);border-radius:2px;}
.pb-fill{height:100%;background:var(--copper);border-radius:2px;}
.pb-wk{font-size:11px;color:rgba(247,245,242,0.4);font-family:\'JetBrains Mono\',monospace;}
.pb-r{font-size:11.5px;color:rgba(182,116,74,0.7);cursor:pointer;}
.prio-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:18px;}
.prio-card{background:var(--white);border:1px solid var(--line);border-radius:12px;padding:14px 15px;}
.triage{display:inline-block;font-size:10px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;padding:3px 9px;border-radius:20px;margin-bottom:8px;}
.t-now{background:rgba(182,116,74,0.10);color:var(--copper);border:1px solid var(--cu-bd);}
.t-watch{background:rgba(230,227,223,0.7);color:#5A5248;border:1px solid var(--stone);}
.t-bg{background:transparent;color:var(--mid);font-style:italic;padding-left:0;}
.pc-title{font-size:13px;font-weight:500;color:var(--graphite);margin-bottom:4px;line-height:1.35;}
.pc-body{font-size:11.5px;color:var(--mid);line-height:1.55;}
.snap-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px;}
.snap-box{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:13px 14px;}
.snap-lbl{font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin-bottom:4px;}
.snap-val{font-family:\'JetBrains Mono\',monospace;font-size:21px;color:var(--graphite);font-weight:500;line-height:1;}
.snap-unit{font-family:\'Inter\',sans-serif;font-size:13px;color:var(--mid);}
.snap-sub{font-size:11px;color:var(--mid);margin-top:3px;}
.snap-flag{color:var(--copper);font-size:11px;margin-top:2px;}
.trends-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.trend-card{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:14px 16px;}
.tc-title{font-size:12px;font-weight:500;color:var(--graphite);margin-bottom:3px;}
.tc-insight{font-size:11.5px;color:var(--mid);line-height:1.5;margin-bottom:10px;}
.tc-bars{height:40px;border-radius:6px;background:rgba(230,227,223,0.4);display:flex;align-items:flex-end;padding:0 4px 3px;gap:3px;overflow:hidden;}
.tb{border-radius:2px 2px 0 0;background:var(--copper);opacity:0.55;flex:1;}
.pg-title{font-family:\'Newsreader\',serif;font-size:23px;color:var(--graphite);font-weight:400;margin-bottom:3px;}
.pg-sub{font-size:12.5px;color:var(--mid);margin-bottom:20px;line-height:1.5;}
.plan-pill{display:inline-flex;background:rgba(182,116,74,0.14);border:1px solid rgba(182,116,74,0.26);border-radius:20px;padding:3px 9px;margin-top:7px;font-size:11px;color:var(--copper);font-family:\'JetBrains Mono\',monospace;}
.sb-name{font-size:13px;color:#F7F5F2;font-weight:500;}
.sb-meta{font-size:11px;color:rgba(247,245,242,0.36);margin-top:2px;}
.sb-tag{font-family:\'Newsreader\',serif;font-style:italic;font-size:11px;color:var(--copper);margin-top:4px;}
.sb-foot-t{font-size:10.5px;color:rgba(247,245,242,0.2);line-height:1.5;}
.ci-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin-bottom:14px;}
.ci-field{background:var(--white);border:1px solid var(--line);border-radius:12px;padding:13px 14px;}
.ci-lbl{font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin-bottom:9px;}
.insight-box{background:var(--forest);border-radius:12px;padding:15px 18px;margin-bottom:14px;}
.ib-lbl{font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:rgba(247,245,242,0.34);margin-bottom:7px;}
.ib-txt{font-family:\'Newsreader\',serif;font-style:italic;font-size:14px;color:#F7F5F2;line-height:1.6;}
.ch-hd{font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--copper);margin-bottom:5px;}
.prof-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;}
.prof-card{background:var(--white);border:1px solid var(--line);border-radius:12px;padding:14px 16px;}
.prof-card-hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;padding-bottom:9px;border-bottom:1px solid var(--line);}
.prof-card-hd h4{font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:var(--mid);}
.pr{display:flex;justify-content:space-between;align-items:baseline;padding:5px 0;font-size:13px;border-bottom:1px solid rgba(17,18,20,0.04);}
.pr:last-child{border-bottom:none;}.pr-k{color:var(--mid);}.pr-v{color:var(--graphite);font-weight:500;}
.acc{background:var(--white);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:8px;}
.cp-banner{background:var(--cu-bg);border:1px solid var(--cu-bd);border-radius:10px;padding:12px 16px;display:flex;gap:12px;align-items:flex-start;margin-bottom:16px;}
.upload-zone{border:1.5px dashed var(--stone);border-radius:8px;padding:20px;text-align:center;font-size:12.5px;color:var(--mid);margin-bottom:12px;}
.file-list{display:flex;flex-direction:column;gap:6px;margin-bottom:12px;}
.file-row{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:rgba(230,227,223,0.3);border-radius:8px;font-size:12.5px;}
.fn{color:var(--graphite);font-weight:500;}.fok{color:#3A6B4A;font-size:11px;font-weight:600;}
.whoop-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px;}
.wc{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:13px;}
.wc-lbl{font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin-bottom:4px;}
.wc-val{font-family:\'JetBrains Mono\',monospace;font-size:20px;color:var(--graphite);font-weight:500;}
.wc-sub{font-size:11px;color:var(--mid);margin-top:2px;}.wc-d{font-size:11px;color:var(--copper);margin-top:2px;}
.tbl-card{background:var(--white);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:14px;}
.tbl{width:100%;border-collapse:collapse;font-size:12.5px;}
.tbl th{text-align:left;font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);padding:9px 14px;border-bottom:1px solid var(--line);background:rgba(230,227,223,0.18);}
.tbl td{padding:9px 14px;border-bottom:1px solid rgba(17,18,20,0.045);color:var(--graphite);vertical-align:top;line-height:1.4;}
.tbl tr:last-child td{border-bottom:none;}
.tb-b{font-weight:500;}.tb-m{font-family:\'JetBrains Mono\',monospace;font-size:12px;}.tb-mid{color:var(--mid);}
.tb-cu{color:var(--copper);font-weight:500;}.tb-gr{color:#3A6B4A;font-weight:500;}
.tr-flag td{background:rgba(182,116,74,0.04);}
.rm-wrap{margin-bottom:16px;}
.rm-track{display:flex;align-items:flex-start;padding-top:6px;position:relative;}
.rm-line{position:absolute;top:21px;left:12px;right:12px;height:2px;background:var(--linem);}
.rm-fill{height:100%;background:var(--copper);}
.rm-node{flex:1;display:flex;flex-direction:column;align-items:center;position:relative;z-index:1;}
.rm-dot{width:42px;height:42px;border-radius:50%;border:2px solid var(--linem);background:var(--bone);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;color:var(--mid);margin-bottom:7px;}
.rm-dot.done{background:var(--stone);border-color:var(--stone);color:var(--mid);}
.rm-dot.curr{background:var(--graphite);border-color:var(--graphite);color:var(--bone);}
.rm-ph{font-size:11px;font-weight:500;color:var(--graphite);text-align:center;line-height:1.3;}
.rm-ph.mid{color:var(--mid);font-weight:400;}
.rm-wk{font-size:10px;color:var(--copper);text-align:center;font-family:\'JetBrains Mono\',monospace;margin-top:2px;}
.goal-card{background:var(--forest);border-radius:12px;padding:16px 20px;margin-bottom:14px;}
.gc-lbl{font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:rgba(247,245,242,0.36);margin-bottom:5px;}
.gc-goal{font-family:\'Newsreader\',serif;font-style:italic;font-size:15px;color:#F7F5F2;margin-bottom:14px;line-height:1.5;}
.gc-weeks{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;}
.gc-wk{background:rgba(247,245,242,0.06);border-radius:8px;padding:10px;font-size:11.5px;}
.gc-wkn{font-family:\'JetBrains Mono\',monospace;font-size:10px;color:rgba(247,245,242,0.36);margin-bottom:4px;}
.gc-wkf{color:rgba(247,245,242,0.7);line-height:1.4;}
.gc-wk.now{background:rgba(182,116,74,0.14);border:1px solid rgba(182,116,74,0.2);}
.info-box{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:12px 15px;font-size:12.5px;color:var(--mid);line-height:1.6;margin-bottom:12px;}
.info-box strong{color:var(--graphite);}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SVG MARK (6-ring, from brand brief §04)
# ─────────────────────────────────────────────
_MARK_DARK = """<svg width="22" height="22" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><defs><radialGradient id="gD" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#B1643A"/><stop offset="40%" stop-color="#B1643A"/><stop offset="54%" stop-color="#BE7C58" stop-opacity="0.72"/><stop offset="70%" stop-color="#D2A084" stop-opacity="0.4"/><stop offset="86%" stop-color="#E6CCB8" stop-opacity="0.14"/><stop offset="100%" stop-color="#E6CCB8" stop-opacity="0"/></radialGradient></defs><circle cx="50" cy="50" r="47" fill="none" stroke="#F7F5F2" stroke-width="1.4"/><circle cx="50" cy="50" r="42" fill="none" stroke="#F7F5F2" stroke-width="1.4"/><circle cx="50" cy="50" r="35" fill="none" stroke="#F7F5F2" stroke-width="1.4"/><circle cx="50" cy="50" r="30" fill="none" stroke="#B6744A" stroke-width="1.7"/><circle cx="50" cy="50" r="25" fill="none" stroke="#B6744A" stroke-width="1.7"/><circle cx="50" cy="50" r="20" fill="none" stroke="#B6744A" stroke-width="1.7"/><circle cx="50" cy="50" r="16" fill="url(#gD)"/></svg>"""

def _mark_light(w=46):
    return f"""<svg width="{w}" height="{w}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><defs><radialGradient id="gL{w}" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#B1643A"/><stop offset="40%" stop-color="#B1643A"/><stop offset="54%" stop-color="#BE7C58" stop-opacity="0.72"/><stop offset="70%" stop-color="#D2A084" stop-opacity="0.4"/><stop offset="86%" stop-color="#E6CCB8" stop-opacity="0.14"/><stop offset="100%" stop-color="#E6CCB8" stop-opacity="0"/></radialGradient></defs><circle cx="50" cy="50" r="47" fill="none" stroke="#111214" stroke-width="1.4" opacity="0.18"/><circle cx="50" cy="50" r="42" fill="none" stroke="#111214" stroke-width="1.4" opacity="0.28"/><circle cx="50" cy="50" r="35" fill="none" stroke="#111214" stroke-width="1.4" opacity="0.40"/><circle cx="50" cy="50" r="30" fill="none" stroke="#B6744A" stroke-width="1.7" opacity="0.65"/><circle cx="50" cy="50" r="25" fill="none" stroke="#B6744A" stroke-width="1.7" opacity="0.80"/><circle cx="50" cy="50" r="20" fill="none" stroke="#B6744A" stroke-width="1.7"/><circle cx="50" cy="50" r="16" fill="url(#gL{w})"/></svg>"""

# ─────────────────────────────────────────────
# CONFIG / CLIENTS
# ─────────────────────────────────────────────
SUPABASE_URL  = st.secrets["SUPABASE_URL"]
SUPABASE_KEY  = st.secrets["SUPABASE_KEY"]
ANTHROPIC_KEY = st.secrets["ANTHROPIC_KEY"]

@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_anthropic():
    return anthropic.Anthropic(api_key=ANTHROPIC_KEY)

supabase  = get_supabase()
ai_client = get_anthropic()

# ─────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────
def sign_up(email, password, full_name):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password,
                                      "options": {"data": {"full_name": full_name}}})
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        supabase.postgrest.auth(res.session.access_token)
        return res.user, res.session, None
    except Exception as e:
        return None, None, str(e)

def sign_out():
    supabase.auth.sign_out()
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ─────────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────────
def db_get(table, user_id, order_col=None, limit=None):
    try:
        q = supabase.table(table).select("*").eq("user_id", user_id)
        if order_col: q = q.order(order_col, desc=True)
        if limit:     q = q.limit(limit)
        return q.execute().data or []
    except Exception:
        return []

def db_get_single(table, user_id):
    """profiles uses `id` as PK; every other table uses `user_id`."""
    try:
        col = "id" if table == "profiles" else "user_id"
        res = supabase.table(table).select("*").eq(col, user_id).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def db_upsert(table, data):
    try:
        supabase.table(table).upsert(data).execute()
        return True
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def db_delete(table, record_id):
    try:
        supabase.table(table).delete().eq("id", record_id).execute()
        return True
    except Exception:
        return False

def _safe_date(s):
    try:   return date.fromisoformat(s)
    except Exception: return date(2000, 1, 1)

# ─────────────────────────────────────────────
# CYCLE HELPERS
# ─────────────────────────────────────────────
def calculate_cycle_status(user_id):
    cd = db_get_single("cycle_data", user_id)
    if not cd or not cd.get("last_period_start"):
        return None, None, None
    try:
        last_start = datetime.strptime(cd["last_period_start"], "%Y-%m-%d").date()
        avg_len    = cd.get("avg_cycle_length", 27)
        today      = date.today()
        cycle_day  = (today - last_start).days + 1
        while cycle_day > avg_len:
            cycle_day -= avg_len
        days_until_next = avg_len - cycle_day + 1
        if   cycle_day <= 5:  phase = "Menstruation (Day 1–5)"
        elif cycle_day <= 13: phase = "Follicular (Day 1–14)"
        elif cycle_day <= 16: phase = "Ovulation (Day 14–16)"
        else:                 phase = "Luteal (Day 16–28)"
        return cycle_day, phase, days_until_next
    except Exception:
        return None, None, None


def build_system_prompt(user_id, profile):
    from datetime import date as _date, datetime as _datetime

    today = _date.today()
    three_months_ago = _date(today.year, today.month - 3 if today.month > 3 else today.month + 9,
                              today.day) if today.month > 3 else _date(today.year - 1, today.month + 9, today.day)

    # ── Core identity and operating principles ───────────────────────────────────
    base = f"""You are OneSattva — an expert integrative medicine practitioner, functional nutritionist, and personal wellness coach. You reason across functional medicine, Ayurveda, and Traditional Chinese Medicine simultaneously, not separately. Today's date is {today.strftime("%A, %d %B %Y")}.

═══════════════════════════════════════════════════════
NON-NEGOTIABLE RULES — ALWAYS FOLLOW THESE
═══════════════════════════════════════════════════════

RULE 1 — COMPLETE EVERY RESPONSE:
Never cut off mid-sentence, mid-table, or mid-section. If a response is long, compress with tables and bullets — but always finish. Every section listed must be completed. If continuation is needed, say "Continued in next message" and do so when asked.

RULE 2 — EXPERT VOICE, NOT SCHEDULER:
You are the expert. The patient has come to you for real clinical guidance. This means:
- If their current routine is suboptimal or working against their goals, say so directly and say what to change.
- State non-negotiables explicitly: "This is non-negotiable because [mechanism]."
- Where there is room for adjustment, propose a specific compromise that still achieves the goal.
- Never simply repackage what the patient already does as a "plan." A plan contains changes.

RULE 3 — DATA ANOMALY PROTOCOL:
If any data point (check-in, lab value, wearable metric) is unusual or contradicts the established trend, DO NOT assume or proceed. Instead: flag the anomaly clearly, then ask ONE specific clarifying question before making recommendations based on it.

RULE 4 — DATA FRESHNESS:
Lab reports older than 3 months: move to historical/trend context only. Do not treat as current status. If no lab report exists within the last 3 months, flag this explicitly rather than reasoning from stale data.
Wearable data: last 7 days = current state. Last 30 days = recent pattern. Beyond 3 months = trend context only.
Check-ins: last 14 days inform current recommendations. Beyond that, used for pattern recognition only.

RULE 5 — GAP DETECTION:
If the check-in data shows a gap of 3-7 days: note it but continue with the protocol.
If the gap is 1-2 weeks: ask a brief re-calibration question before making recommendations — "It's been [X] days since your last log. Has anything changed — symptoms, medications, how you're feeling?"
If the gap is 2+ weeks: do not continue the old protocol. Generate a fresh re-entry assessment before resuming.

RULE 6 — SPECIFIC, NOT GENERIC:
Always recommend exact brands (available in the patient's location), exact doses, exact timing. Never give generic supplement or food advice when the patient's labs, conditions, and goals give you enough context to be specific.

RULE 7 — NEVER DEFLECT:
Never say "consult a nutritionist" or "ask your doctor" without first giving a complete, specific answer yourself. You are their nutritionist and functional medicine coach. You can recommend they also discuss with their physician, but give your full expert answer first.

═══════════════════════════════════════════════════════
FUNCTIONAL NUTRITIONIST VOICE
═══════════════════════════════════════════════════════

When giving nutrition guidance, think and speak as an experienced functional nutritionist:
- Specific foods with exact portions, preparation methods, and timing — not food categories
- Reason through gut status, absorption capacity, and digestive fire (Agni) when selecting foods
- Consider cycle phase, time of day, workout timing, and medication interactions for every meal recommendation
- Favour cooked, warm, easily digestible proteins over raw (low stomach acid is common)
- No raw salads as main meals for patients with gut issues — always cooked vegetables
- Foods as medicine: specific therapeutic choices (e.g. bitter melon for insulin sensitivity, ashwagandha timing around cortisol rhythm, seed cycling for hormone balance)
- Gut-healing foods: bone broth (if non-vegetarian), cooked moong dal, ghee, fermented foods appropriate to the patient
- Diet must respect the patient's stated dietary preferences (vegetarian, vegan, etc.) — never suggest foods outside their diet without flagging it first

═══════════════════════════════════════════════════════
FITNESS TRAINER VOICE
═══════════════════════════════════════════════════════

When giving training guidance, think and speak as an experienced strength and conditioning coach with functional medicine awareness:
- Specific exercises, not just categories. "3 sets of 8 Romanian deadlifts at RPE 7" not "do some leg work"
- Cycle-phase periodisation for female patients: heavier compound lifts in follicular phase (Days 1-14), moderate in ovulation, deload in luteal, minimal in menstruation
- Recovery awareness: if wearable data shows HRV below baseline or recovery score below 50%, modify the session — do not push through
- Warm-up and cool-down as non-negotiable, not optional extras
- Progressive overload: give specific progression targets week on week, not just "increase weight when ready"
- Training around health conditions: adapt for thyroid, gut issues, hormonal imbalances — explain exactly how and why

═══════════════════════════════════════════════════════
INTEGRATIVE CROSS-SYSTEM REASONING
═══════════════════════════════════════════════════════

Always reason across all three systems simultaneously:
- FUNCTIONAL MEDICINE: root cause focus, lab interpretation against functional ranges (not just conventional), HPA axis, gut-brain-thyroid axis, microbiome
- AYURVEDA: constitutional type (Prakriti), Agni (digestive fire), seasonal and time-of-day recommendations, Dinacharya (daily routine)
- TCM: organ system patterns, Five Element theory, Qi and Blood, meridian timing for supplements and activities

For complex questions, structure your response:
1. What is happening — mechanism across all relevant systems
2. What it means for this patient specifically — reference their actual labs, conditions, and patterns
3. Exact protocol — brand, dose, timing, duration, what to watch for
4. What to expect and when — realistic timeline
5. One priority action to start today

═══════════════════════════════════════════════════════
GEOGRAPHY AND BRAND GUIDANCE
═══════════════════════════════════════════════════════

Always recommend brands and foods available in the patient's location. Default guidance is for India unless location specifies otherwise.

INDIA SUPPLEMENT BRANDS (in order of preference by category):
- General: Thorne (iHerb/Amazon), Himalayan Organics, Miduty, Wellbeing Nutrition, Carbamide Forte, Now Foods, Jarrow, Solgar
- Ayurvedic: Kottakkal, Organic India, Kerala Ayurveda, Baidyanath
- Functional food: True Elements, Sorich Organics, Conscious Food
- Testing: Thyrocare (Aarogyam panels), SRL Diagnostics, Apollo Diagnostics, Redcliffe Labs

INDIA FOOD GUIDANCE: Favour seasonally available, locally sourced foods. Mumbai-specific options where relevant: farmer's markets, Godrej Nature's Basket, organic stores.

"""

    # ── Patient profile ──────────────────────────────────────────────────────────
    if profile:
        name = profile.get("full_name", "the patient")
        base += f"\n═══════════════════════════════════════════════════════\nPATIENT PROFILE\n═══════════════════════════════════════════════════════\n"
        base += f"Name: {name}"
        if profile.get("age"): base += f" | Age: {profile['age']}"
        if profile.get("sex"): base += f" | Sex: {profile['sex']}"
        if profile.get("height_cm") and profile.get("weight_kg"):
            base += f" | {profile['height_cm']}cm · {profile['weight_kg']}kg"
        if profile.get("blood_group"): base += f" | Blood group: {profile['blood_group']}"
        if profile.get("location"): base += f" | Location: {profile['location']}"
        if profile.get("diet"): base += f"\nDiet: {profile['diet']}"
        if profile.get("allergies"): base += f" | Allergies: {profile['allergies']}"
        if profile.get("alcohol") and profile.get("alcohol") != "None":
            base += f" | Alcohol: {profile['alcohol']}"
        if profile.get("smoking") and profile.get("smoking") != "None":
            base += f" | Smoking/vaping: {profile['smoking']}"
        if profile.get("wake_time") or profile.get("sleep_time"):
            base += f"\nSchedule: Wake {profile.get('wake_time','?')} · Bed {profile.get('sleep_time','?')}"

    # ── Goals with timeframes ────────────────────────────────────────────────────
    goals = db_get("goals", user_id)
    if goals:
        base += "\n\nGOALS:\n"
        for g in goals:
            tf = f" [{g['timeframe']}]" if g.get("timeframe") else ""
            base += f"- {g['goal']}{tf}\n"

    # ── Medical history ──────────────────────────────────────────────────────────
    conditions = db_get("medical_history", user_id)
    if conditions:
        base += "\nMEDICAL CONDITIONS:\n"
        for c in conditions:
            base += f"- {c['condition']}: {c.get('notes','')}\n"

    # ── Medications ──────────────────────────────────────────────────────────────
    meds = db_get("medications", user_id)
    active_meds = [m for m in meds if m.get("active", True)] if meds else []
    if active_meds:
        base += "\nCURRENT MEDICATIONS:\n"
        for m in active_meds:
            base += f"- {m['name']} {m.get('dose','')} {m.get('frequency','')}\n"

    # ── Supplements ──────────────────────────────────────────────────────────────
    supps = db_get("supplements", user_id)
    active_supps = [s for s in supps if s.get("active", True)] if supps else []
    if active_supps:
        base += "\nCURRENT SUPPLEMENTS:\n"
        for s in active_supps:
            base += f"- {s['name']} {s.get('dose','')} ({s.get('timing','')})\n"

    # ── Profile notes ────────────────────────────────────────────────────────────
    notes = db_get_single("profile_notes", user_id)
    if notes and notes.get("notes"):
        base += f"\nPROFILE UPDATES / RECENT CHANGES:\n{notes['notes']}\n"

    # ── Lab reports with freshness classification ────────────────────────────────
    labs = db_get("lab_reports", user_id, order_col="report_date", limit=10)
    if labs:
        base += "\n═══════════════════════════════════════════════════════\nLAB REPORTS\n═══════════════════════════════════════════════════════\n"
        current_labs = []
        historical_labs = []
        for l in labs:
            try:
                rep_date = _date.fromisoformat(l.get("report_date",""))
                if rep_date >= three_months_ago:
                    current_labs.append(l)
                else:
                    historical_labs.append(l)
            except:
                historical_labs.append(l)

        if current_labs:
            base += "CURRENT LABS (within last 3 months — use as primary reference):\n"
            for l in current_labs:
                base += f"- {l.get('report_date','')}: {l.get('summary','')} | Raw: {l.get('raw_values','')[:300]}\n"
        else:
            base += "⚠️ NO CURRENT LABS (all reports older than 3 months). Flag this to the patient — do not treat old values as current status.\n"

        if historical_labs:
            base += "\nHISTORICAL LABS (older than 3 months — use for trend analysis only, not current status):\n"
            for l in historical_labs:
                base += f"- {l.get('report_date','')}: {l.get('summary','')}\n"
    else:
        base += "\n⚠️ NO LAB REPORTS UPLOADED. Recommendations will be general until labs are provided. Remind the patient that labs are needed for a precise protocol.\n"

    # ── Wearable data with freshness classification ──────────────────────────────
    wearable_all = db_get("wearable_data", user_id, order_col="data_date", limit=90)
    if wearable_all:
        base += "\n═══════════════════════════════════════════════════════\nWEARABLE DATA\n═══════════════════════════════════════════════════════\n"
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=30)
        ninety_days_ago = today - timedelta(days=90)

        current_w, recent_w, trend_w = [], [], []
        for w in wearable_all:
            try:
                wd = _date.fromisoformat(w.get("data_date",""))
                if wd >= seven_days_ago: current_w.append(w)
                elif wd >= thirty_days_ago: recent_w.append(w)
                elif wd >= ninety_days_ago: trend_w.append(w)
            except: pass

        def fmt_wearable(w):
            parts = [w.get("data_date","")]
            for f in ["recovery_score","hrv","resting_hr","strain","sleep_performance"]:
                if w.get(f) is not None: parts.append(f"{f.replace('_',' ')}: {w[f]}")
            return " | ".join(parts)

        if current_w:
            base += "CURRENT (last 7 days):\n" + "\n".join([f"- {fmt_wearable(w)}" for w in reversed(current_w)]) + "\n"
        if recent_w:
            # Summarise 8-30 days as averages rather than listing every row
            import statistics
            def avg_field(rows, field):
                vals = [float(r[field]) for r in rows if r.get(field) is not None]
                return round(statistics.mean(vals), 1) if vals else None
            r_avg = {f: avg_field(recent_w, f) for f in ["recovery_score","hrv","resting_hr","strain","sleep_performance"]}
            r_str = " | ".join([f"{k.replace('_',' ')}: {v}" for k, v in r_avg.items() if v is not None])
            base += f"RECENT AVERAGE (last 30 days, {len(recent_w)} days of data): {r_str}\n"
        if not current_w and not recent_w:
            base += "⚠️ No recent wearable data. Cannot assess current recovery or readiness.\n"

    # ── Check-ins with gap detection ─────────────────────────────────────────────
    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=14)
    if checkins:
        latest_checkin = checkins[0]
        try:
            latest_date = _date.fromisoformat(latest_checkin.get("checkin_date",""))
            gap_days = (today - latest_date).days
        except:
            gap_days = 0

        base += "\n═══════════════════════════════════════════════════════\nCHECK-IN DATA\n═══════════════════════════════════════════════════════\n"

        if gap_days >= 14:
            base += f"⚠️ GAP ALERT: Last check-in was {gap_days} days ago. Do NOT continue with the old protocol. First, ask a re-entry question: 'It's been {gap_days} days since your last log. Has anything changed — symptoms, medications, energy, how you're feeling overall?' Then reassess before resuming.\n"
        elif gap_days >= 7:
            base += f"⚠️ CHECK-IN GAP: {gap_days} days since last log. Before giving recommendations, ask: 'It's been {gap_days} days — anything changed recently?' One question only.\n"
        elif gap_days >= 3:
            base += f"Note: {gap_days}-day gap in check-ins. Continue with protocol but note the gap.\n"

        base += f"RECENT CHECK-INS (last 14 days):\n"
        for c in reversed(checkins[:14]):
            base += f"- {c.get('checkin_date','')}: Energy {c.get('energy','?')}/10 · Mood {c.get('mood','?')}/10 · Sleep {c.get('sleep_hours','?')}hrs (quality {c.get('sleep_quality','?')}/10) · Bloating: {c.get('bloating','?')} · Digestion: {c.get('digestion','?')} · Workout: {c.get('workout','?')} · Rumination: {c.get('rumination','?')} · Notes: {c.get('notes','')}\n"
    else:
        base += "\nNo check-in data yet.\n"

    return base

# ════════════════════════════════════════════════════════════════════════════════
# AUTH SCREEN (shown when not logged in)
# ════════════════════════════════════════════════════════════════════════════════


MARKERS_INFO = """
**Core panel — get these tested before your first roadmap:**
| Category | Markers |
|---|---|
| Thyroid | TSH, Free T3, Free T4, TPO Antibodies |
| Iron & Blood | Ferritin, Serum Iron, TIBC, Haemoglobin, CBC |
| Metabolic | Fasting Glucose, HbA1c, Fasting Insulin, HOMA-IR |
| Inflammation | hs-CRP, ESR |
| Hormones | Prolactin, Estradiol, Testosterone (total+free), SHBG, LH, FSH, DHEA-S |
| Vitamins | Vitamin D (25-OH), B12, Folate |
| Liver & Protein | Total Protein, Albumin, ALT, AST, Alkaline Phosphatase, GGT |
| Kidney | Creatinine, eGFR, Uric Acid |
| Lipids | Total Cholesterol, LDL, HDL, Triglycerides, ApoB |

**Extended:** Zonulin · Calprotectin · H. pylori antibody · ANA · Morning Cortisol · MTHFR · APOE

In India, Thyrocare's Aarogyam or Wellness packages cover most of the core panel at reasonable cost.
"""

# ─────────────────────────────────────────────
# AUTH SCREEN
# Prototype: S1 landing → S2 login / S3 signup
# ─────────────────────────────────────────────
def show_auth_screen():
    auth_mode = st.session_state.get("auth_mode", "landing")

    # ── LANDING (S1) ──────────────────────────────────────────────────────
    if auth_mode == "landing":
        # Full-page dark landing — CTAs embedded inside the HTML so they stay in-viewport.
        # Streamlit can't fill 100vh reliably; we use a large centred card instead.
        st.markdown(f"""
        <div style="min-height:92vh;background:var(--graphite);border-radius:16px;
                    display:flex;flex-direction:column;overflow:hidden;margin:-0.5rem 0;">
          <!-- nav bar -->
          <div style="padding:22px 40px;display:flex;justify-content:space-between;align-items:center;">
            <div style="display:flex;align-items:center;gap:10px;">
              {_MARK_DARK}
              <div>
                <div style="font-family:'Newsreader',serif;font-weight:400;font-size:18px;
                            letter-spacing:-0.02em;color:#F7F5F2;line-height:1;">OneSattva</div>
                <div style="font-family:'Newsreader',serif;font-style:italic;font-size:11px;
                            color:var(--copper);margin-top:3px;">Health, understood.</div>
              </div>
            </div>
          </div>
          <!-- hero body -->
          <div style="flex:1;display:flex;align-items:center;justify-content:center;
                      flex-direction:column;text-align:center;padding:40px 40px 20px;">
            {_mark_light(76)}
            <div style="font-family:'Newsreader',serif;font-style:italic;font-size:52px;
                        color:var(--bone);line-height:1.1;margin:24px 0 14px;max-width:540px;">
              Health, understood.
            </div>
            <div style="font-size:15px;color:rgba(247,245,242,0.42);line-height:1.65;
                        max-width:400px;margin-bottom:36px;">
              Your personal health intelligence — remembers your story, understands your context,
              and guides what matters next.
            </div>
          </div>
          <!-- footer -->
          <div style="padding:18px 40px;border-top:1px solid rgba(247,245,242,0.06);
                      display:flex;justify-content:space-between;">
            <div style="font-size:11px;color:rgba(247,245,242,0.2);">
              © 2026 OneSattva · Not a substitute for medical care
            </div>
            <div style="font-size:11px;color:rgba(247,245,242,0.2);">
              Functional Medicine · Ayurveda · TCM
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # CTAs rendered by Streamlit immediately below the dark card
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        _, col1, col2, _ = st.columns([3, 2, 2, 3])
        with col1:
            if st.button("Begin your journey", type="primary", use_container_width=True, key="landing_begin"):
                st.session_state.auth_mode = "signup"
                st.rerun()
        with col2:
            if st.button("Sign in", use_container_width=True, key="landing_signin"):
                st.session_state.auth_mode = "login"
                st.rerun()

    # ── LOGIN (S2) ────────────────────────────────────────────────────────
    elif auth_mode == "login":
        col1, col2, col3 = st.columns([1, 1.4, 1])
        with col2:
            # Mark + wordmark header above the card (no separate white box)
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;align-items:center;
                        margin:40px 0 24px;gap:10px;text-align:center;">
              {_mark_light(46)}
              <span style="font-family:'Newsreader',serif;font-weight:400;font-size:26px;
                           letter-spacing:-0.02em;color:#111214;line-height:1;">OneSattva</span>
              <div style="font-family:'Newsreader',serif;font-style:italic;
                          font-size:12.5px;color:var(--copper);">Health, understood.</div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.get("show_reset"):
                st.markdown("##### Reset your password")
                reset_email = st.text_input("Email", key="reset_email")
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("Send reset link", type="primary", use_container_width=True, key="send_reset"):
                        if reset_email:
                            try:
                                supabase.auth.reset_password_email(reset_email,
                                    options={"redirect_to": "https://wellness-coach-app-f2ssjkdxdey8vm2c287mnz.streamlit.app"})
                                st.success("Reset link sent — check your email.")
                                st.session_state.show_reset = False
                            except Exception as e:
                                st.error(str(e))
                with rc2:
                    if st.button("Back", use_container_width=True, key="back_reset"):
                        st.session_state.show_reset = False
                        st.rerun()
            else:
                email    = st.text_input("Email", key="login_email", placeholder="your@email.com")
                password = st.text_input("Password", type="password", key="login_pw", placeholder="••••••••")
                st.markdown("<div style='text-align:right;font-size:11.5px;color:var(--mid);'>", unsafe_allow_html=True)
                if st.button("Forgot password?", key="forgot_btn"):
                    st.session_state.show_reset = True
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                if st.button("Sign in", type="primary", use_container_width=True, key="signin_btn"):
                    if email and password:
                        user, session, err = sign_in(email, password)
                        if err:
                            st.error(f"Sign in failed: {err}")
                        else:
                            st.session_state.update({"user": user, "session": session,
                                                      "access_token": session.access_token})
                            st.rerun()
                    else:
                        st.warning("Please enter your email and password.")
                st.markdown("<div style='text-align:center;margin-top:14px;font-size:12.5px;color:var(--mid);'>New to OneSattva? <span style='color:var(--copper);cursor:pointer;'>", unsafe_allow_html=True)
                if st.button("Create an account →", key="goto_signup"):
                    st.session_state.auth_mode = "signup"
                    st.rerun()

    # ── SIGN UP (S3) ──────────────────────────────────────────────────────
    elif auth_mode == "signup":
        col1, col2, col3 = st.columns([1, 1.4, 1])
        with col2:
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;align-items:center;
                        margin:40px 0 20px;gap:10px;text-align:center;">
              {_mark_light(38)}
              <span style="font-family:'Newsreader',serif;font-weight:400;font-size:22px;
                           letter-spacing:-0.02em;color:#111214;line-height:1;">OneSattva</span>
            </div>
            """, unsafe_allow_html=True)

            fn_col, ln_col = st.columns(2)
            with fn_col:
                first_name = st.text_input("First name", key="su_fname", placeholder="Arjun")
            with ln_col:
                last_name  = st.text_input("Last name",  key="su_lname", placeholder="Mehta")
            email    = st.text_input("Email",           key="su_email", placeholder="arjun@email.com")
            password = st.text_input("Create password", key="su_pw",    placeholder="Min. 8 characters",
                                     type="password")

            st.markdown("<div style='border-top:1px solid var(--line);padding-top:12px;margin-top:4px;'></div>",
                        unsafe_allow_html=True)
            consent1 = st.checkbox("I agree to the **Terms of Service** and **Privacy Policy**",
                                   key="c1")
            consent2 = st.checkbox(
                "I explicitly consent to OneSattva collecting, storing, and processing my personal "
                "health data — including lab results, wearable data, and symptom logs — solely for "
                "personalised health coaching.", key="c2")

            if st.button("Create account →", type="primary", use_container_width=True, key="signup_btn"):
                full_name = f"{first_name.strip()} {last_name.strip()}".strip()
                if not full_name or not email or not password:
                    st.warning("Please fill in all fields.")
                elif not consent1:
                    st.error("Please agree to the Terms of Service and Privacy Policy.")
                elif not consent2:
                    st.error("Please provide explicit consent for health data processing.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    user, err = sign_up(email, password, full_name)
                    if err:
                        st.error(f"Sign up failed: {err}")
                    else:
                        st.success("Account created! Check your email for a verification link, then sign in.")

            st.markdown("<div style='text-align:center;margin-top:14px;font-size:12.5px;color:var(--mid);'>", unsafe_allow_html=True)
            if st.button("Already have an account? Sign in", key="goto_login"):
                st.session_state.auth_mode = "login"
                st.rerun()


# ─────────────────────────────────────────────
# ONBOARDING (prototype S4-S10)
# Steps: 1=Plan mode, 2=About you, 3=Health history,
#        4=Lifestyle & goals, 5=Data sources, 6=Plan review (S10)
# ─────────────────────────────────────────────
OB_STEPS = ["Your plan", "About you", "Health history", "Lifestyle & goals", "Data sources"]

def get_onboarding_state(user_id):
    try:
        res = supabase.table("onboarding").select("*").eq("user_id", user_id).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def save_onboarding_state(user_id, data):
    try:
        data["user_id"] = user_id
        supabase.table("onboarding").upsert(data).execute()
    except Exception as e:
        st.error(f"Save error: {e}")

def _ob_progress(current):
    html = "<div style='display:flex;align-items:center;margin-bottom:22px;'>"
    for i, label in enumerate(OB_STEPS):
        n = i + 1
        is_done = n < current
        is_curr = n == current
        dot_bg  = "#1F2F2A" if is_done else ("#111214" if is_curr else "var(--bone)")
        dot_col = "#fff"    if (is_done or is_curr) else "var(--mid)"
        dot_bdr = "#1F2F2A" if is_done else ("#111214" if is_curr else "var(--linem)")
        dot_txt = "✓"       if is_done else str(n)
        lbl_col = "var(--graphite)" if is_curr else "var(--mid)"
        lbl_wt  = "500" if is_curr else "400"
        html += f"""<div style="display:flex;align-items:center;gap:6px;">
          <div style="width:27px;height:27px;border-radius:50%;background:{dot_bg};
                      border:2px solid {dot_bdr};display:flex;align-items:center;
                      justify-content:center;font-size:11px;font-weight:600;
                      color:{dot_col};flex-shrink:0;">{dot_txt}</div>
          <span style="font-family:Inter,sans-serif;font-size:11px;color:{lbl_col};
                       font-weight:{lbl_wt};white-space:nowrap;">{label}</span></div>"""
        if i < len(OB_STEPS) - 1:
            conn_bg = "#1F2F2A" if is_done else "rgba(17,18,20,0.14)"
            html += f"<div style='flex:1;height:1px;background:{conn_bg};margin:0 7px;'></div>"
    html += "</div>"
    return html

def _ob_header(title, subtitle):
    st.markdown(f"""
    <div style="font-family:'Newsreader',serif;font-size:23px;color:var(--graphite);
                font-weight:400;margin-bottom:4px;">{title}</div>
    <div style="font-size:12.5px;color:var(--mid);line-height:1.5;margin-bottom:20px;">{subtitle}</div>
    """, unsafe_allow_html=True)

def _sec_lbl(text, css=""):
    st.markdown(f"<div style='font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:var(--mid);margin-top:14px;margin-bottom:8px;{css}'>{text}</div>", unsafe_allow_html=True)

def show_onboarding(user):
    user_id = user.id
    ob = get_onboarding_state(user_id)
    if not ob:
        save_onboarding_state(user_id, {"current_step": 1})
        ob = get_onboarding_state(user_id)
    profile = db_get_single("profiles", user_id)
    step    = ob.get("current_step", 1) if ob else 1

    col_main, col_tip = st.columns([10, 3])
    with col_main:
        st.markdown(_ob_progress(step), unsafe_allow_html=True)

        # ══ STEP 1 — Your plan (Reset/Restore/Transform/Sustain) ══════════
        if step == 1:
            _ob_header("What are you here for?",
                "Choose your plan mode. This shapes how your coach works with you. You can change "
                "it at any time from Profile & Data — your data always carries forward.")

            MODES = [
                ("Reset",     "30 days",   "Foundation · 1 month",
                 "Break a pattern. Build a baseline. Understand your body for the first time. The coach is investigative — high-frequency check-ins, establishing rhythms, calibrating your picture."),
                ("Restore",   "90 days",   "Active correction · 3 months",
                 "Address a specific deficit or condition actively. The minimum meaningful intervention window in functional medicine. Labs should reflect measurable change by the end of this mode."),
                ("Transform", "6 months",  "Systemic change · 6 months",
                 "Multiple systems shifting simultaneously. Sustainable habit formation and deeper pattern resolution. The coach reasons across functional medicine, Ayurveda, and TCM together."),
                ("Sustain",   "Ongoing",   "Long-term partner · 12m+",
                 "Acute issues resolved. Long-term optimisation and longevity. The coach references years of history. No fixed end — the horizon keeps extending as you evolve."),
            ]
            saved = ob.get("plan_mode", "") if ob else ""
            sel   = st.session_state.get("ob_plan", saved)

            c1, c2 = st.columns(2)
            for i, (key, dur, tag, desc) in enumerate(MODES):
                col = c1 if i % 2 == 0 else c2
                is_sel = sel == key
                border = "2px solid var(--graphite)" if is_sel else "2px solid var(--line)"
                bg     = "rgba(17,18,20,0.02)" if is_sel else "var(--white)"
                check  = "<div style='position:absolute;top:14px;right:14px;width:19px;height:19px;border-radius:50%;background:var(--graphite);display:flex;align-items:center;justify-content:center;color:#fff;font-size:10px;'>✓</div>" if is_sel else ""
                with col:
                    st.markdown(f"""
                    <div style="background:{bg};border:{border};border-radius:12px;padding:17px;
                                position:relative;margin-bottom:11px;">
                      {check}
                      <div style="font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin-bottom:5px;">{dur}</div>
                      <div style="font-family:'Newsreader',serif;font-size:19px;color:var(--graphite);margin-bottom:2px;">{key}</div>
                      <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--copper);margin-bottom:9px;">{tag}</div>
                      <div style="font-size:12px;color:var(--mid);line-height:1.55;">{desc}</div>
                    </div>""", unsafe_allow_html=True)
                    if st.button(f"Select {key}", key=f"sel_{key}", use_container_width=True):
                        st.session_state.ob_plan = key
                        st.rerun()

            _, cc = st.columns(2)
            with cc:
                if st.button("Continue →", type="primary", use_container_width=True, key="ob1_next"):
                    if not st.session_state.get("ob_plan"):
                        st.error("Please select a plan mode.")
                    else:
                        save_onboarding_state(user_id, {"current_step": 2,
                                                         "plan_mode": st.session_state.ob_plan})
                        st.rerun()

        # ══ STEP 2 — About you ════════════════════════════════════════════
        elif step == 2:
            _ob_header("Tell us about yourself",
                "This personalises everything. You can edit any of this from Profile & Data at any time.")
            with st.form("ob2"):
                c1, c2 = st.columns(2)
                with c1:
                    p_dob_val = profile.get("date_of_birth") if profile else None
                    p_dob     = st.date_input("Date of birth *",
                        value=date.fromisoformat(p_dob_val) if p_dob_val else date(1990,1,1),
                        min_value=date(1940,1,1), max_value=date.today())
                    p_loc     = st.text_input("Location / city *", placeholder="Mumbai",
                        value=profile.get("location","") if profile else "")
                    p_height  = st.text_input("Height", placeholder="175 cm",
                        value=f"{profile['height_cm']} cm" if profile and profile.get("height_cm") else "")
                    p_weight  = st.text_input("Current weight", placeholder="78 kg",
                        value=f"{profile['weight_kg']} kg" if profile and profile.get("weight_kg") else "")
                with c2:
                    sex_opts  = ["", "Male", "Female", "Prefer not to say"]
                    p_sex     = st.selectbox("Biological sex *", sex_opts,
                        index=sex_opts.index(profile.get("sex","")) if profile and profile.get("sex","") in sex_opts else 0)
                    bg_opts   = ["","A+","A-","B+","B-","O+","O-","AB+","AB-"]
                    p_blood   = st.selectbox("Blood group", bg_opts,
                        index=bg_opts.index(profile.get("blood_group","")) if profile and profile.get("blood_group","") in bg_opts else 0)
                    diet_opts = ["Omnivore","Vegetarian","Vegan","Pescatarian","Other"]
                    p_diet    = st.selectbox("Eating pattern", diet_opts)
                    p_occ     = st.text_input("Occupation (optional)",
                        placeholder="e.g. Senior finance manager")
                if p_sex == "Female":
                    st.info("🔄 Cycle tracking available — set it up in Lifestyle & Goals.")
                if st.form_submit_button("Continue →", type="primary", use_container_width=True):
                    if not p_loc or not p_sex:
                        st.error("Please fill in all required fields.")
                    else:
                        age = (date.today() - p_dob).days // 365
                        try:   h = int(p_height.replace("cm","").replace(" ",""))
                        except: h = 0
                        try:   w = int(p_weight.replace("kg","").replace(" ",""))
                        except: w = 0
                        db_upsert("profiles", {"id": user_id, "age": age,
                            "date_of_birth": p_dob.isoformat(), "sex": p_sex,
                            "height_cm": h, "weight_kg": w, "location": p_loc,
                            "diet": p_diet, "blood_group": p_blood, "occupation": p_occ})
                        save_onboarding_state(user_id, {"current_step": 3, "step2_done": True})
                        st.rerun()
            bc, _ = st.columns(2)
            with bc:
                if st.button("← Back", key="ob2_back"):
                    save_onboarding_state(user_id, {"current_step": 1}); st.rerun()

        # ══ STEP 3 — Health history ════════════════════════════════════════
        elif step == 3:
            _ob_header("Your health history",
                "Nothing here is mandatory — skip anything you're unsure about. More context means more precise coaching.")

            def _med_sec(lbl, items, add_form_key, placeholder, fields):
                st.markdown(f"<span style='font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);display:block;margin-bottom:8px;'>{lbl}</span>", unsafe_allow_html=True)
                for item in items:
                    r1, r2 = st.columns([8,1])
                    with r1:
                        st.write(f"{item[fields[0]]}" + (f" — {item[fields[1]]}" if len(fields)>1 and item.get(fields[1]) else ""))
                    with r2:
                        if st.button("✕", key=f"del_{add_form_key}_{item['id']}"):
                            db_delete(fields[0][:4] if len(fields[0])>4 else fields[0], item["id"])
                            st.rerun()

            conds = db_get("medical_history", user_id)
            _med_sec("Diagnosed conditions", conds, "cond", "Add another condition...", ["condition","notes"])
            with st.form("ob3_cond"):
                c1,c2 = st.columns([3,2])
                with c1: new_c = st.text_input("Condition", placeholder="e.g. Hypothyroidism")
                with c2: new_cn= st.text_input("Since / notes", placeholder="e.g. Since 2018")
                if st.form_submit_button("+ Add condition") and new_c:
                    db_upsert("medical_history", {"user_id": user_id, "condition": new_c, "notes": new_cn}); st.rerun()

            meds = db_get("medications", user_id)
            st.markdown("<span style='font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);display:block;margin:14px 0 8px;'>Current medications</span>", unsafe_allow_html=True)
            for m in meds:
                r1,r2 = st.columns([8,1])
                r1.write(f"**{m['name']}** {m.get('dose','')} — {m.get('frequency','')}")
                if r2.button("✕", key=f"del_med_{m['id']}"): db_delete("medications", m["id"]); st.rerun()
            with st.form("ob3_med"):
                m1,m2,m3 = st.columns(3)
                with m1: nm = st.text_input("Medication", placeholder="e.g. Levothyroxine 50mcg")
                with m2: nd = st.text_input("Dose", placeholder="e.g. 50mcg")
                with m3: nf = st.text_input("Timing", placeholder="e.g. Daily · 6am empty stomach")
                if st.form_submit_button("+ Add medication") and nm:
                    db_upsert("medications", {"user_id": user_id,"name": nm,"dose": nd,"frequency": nf,"active": True}); st.rerun()

            supps = db_get("supplements", user_id)
            st.markdown("<span style='font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);display:block;margin:14px 0 8px;'>Current supplements</span>", unsafe_allow_html=True)
            for s in supps:
                r1,r2 = st.columns([8,1])
                r1.write(f"**{s['name']}** {s.get('dose','')} — {s.get('timing','')}")
                if r2.button("✕", key=f"del_supp_{s['id']}"): db_delete("supplements", s["id"]); st.rerun()
            with st.form("ob3_supp"):
                s1,s2,s3 = st.columns(3)
                with s1: ns = st.text_input("Supplement", placeholder="e.g. Vitamin D3 + K2")
                with s2: nsd= st.text_input("Dose", placeholder="e.g. 5000IU")
                with s3: nst= st.text_input("Timing", placeholder="e.g. With lunch")
                if st.form_submit_button("+ Add supplement") and ns:
                    db_upsert("supplements", {"user_id": user_id,"name": ns,"dose": nsd,"timing": nst,"active": True}); st.rerun()

            with st.form("ob3_extra"):
                c1,c2 = st.columns(2)
                with c1: fam  = st.text_area("Family history (optional)", height=68, placeholder="e.g. Father — Type 2 diabetes. Mother — autoimmune thyroid disorder.")
                with c2: past = st.text_area("Past surgeries or significant events (optional)", height=68, placeholder="e.g. appendectomy 2015, kidney stone episode...")
                if st.form_submit_button("Save & Continue →", type="primary", use_container_width=True):
                    notes_parts = []
                    if fam:  notes_parts.append(f"Family history: {fam}")
                    if past: notes_parts.append(f"Past events: {past}")
                    if notes_parts:
                        ex = db_get_single("profile_notes", user_id)
                        combined = ((ex.get("notes","") if ex else "") + "\n" + "\n".join(notes_parts)).strip()
                        db_upsert("profile_notes", {"user_id": user_id, "notes": combined})
                    save_onboarding_state(user_id, {"current_step": 4, "step3_done": True}); st.rerun()

            bc, _ = st.columns(2)
            with bc:
                if st.button("← Back", key="ob3_back"):
                    save_onboarding_state(user_id, {"current_step": 2}); st.rerun()

        # ══ STEP 4 — Lifestyle & goals (full prototype S7) ═════════════════
        elif step == 4:
            _ob_header("Your lifestyle and goals",
                "The more specific you are here, the more precisely the coach can build your protocol. All of this is editable from Profile & Data later.")

            with st.form("ob4"):
                # Primary goal
                primary_goal = st.text_area("Primary health goal",
                    placeholder="e.g. Resolve chronic fatigue and brain fog. Restore hormonal balance after elevated prolactin. Improve sleep quality and consistent energy.",
                    height=68)

                # Diet & activity
                _sec_lbl("Diet & activity", "margin-top:16px;")
                da1,da2 = st.columns(2)
                with da1:
                    p_diet2 = st.selectbox("Eating pattern", ["Omnivore","Vegetarian","Vegan","Pescatarian","Other"])
                    p_act   = st.selectbox("Activity level", ["Sedentary","Lightly active","Moderately active","Very active"], index=1)
                    p_restr = st.text_input("Dietary restrictions or intolerances", placeholder="e.g. Mild lactose sensitivity.")
                with da2:
                    p_alc   = st.selectbox("Alcohol consumption", ["None","Occasionally (1–2×/week)","Regularly (3+/week)"])
                    p_smk   = st.selectbox("Smoking / tobacco", ["Non-smoker","Former smoker","Occasional (social)","Regular smoker","Vaping / e-cigarettes"])
                p_exc = st.text_area("Exercise routine", height=56, placeholder="e.g. Gym 3× per week — strength focus. Walking 30 min most days.")

                # Sleep
                _sec_lbl("Sleep")
                sl1,sl2,sl3 = st.columns(3)
                with sl1: p_bed  = st.text_input("Typical bedtime", placeholder="11:00 pm")
                with sl2: p_wake = st.text_input("Typical wake time", placeholder="6:30 am")
                with sl3: p_slp  = st.text_input("Average sleep duration", placeholder="6.5 hrs")
                p_slp_q = st.slider("Sleep quality (self-rated)", 1, 10, 5)
                p_slp_c = st.text_area("Sleep challenges (optional)", height=52, placeholder="e.g. Takes 20–30 min to fall asleep. Occasionally wakes around 3–4am.")

                # Eating schedule
                _sec_lbl("Eating schedule & patterns")
                es1,es2,es3,es4 = st.columns(4)
                with es1: p_first_meal = st.text_input("First meal time", placeholder="8:00 am")
                with es2: p_last_meal  = st.text_input("Last meal time", placeholder="8:30 pm")
                with es3: p_meals_day  = st.selectbox("Meals per day", ["2 meals","3 meals","3 meals + snacks","Intermittent fasting"], index=1)
                with es4: p_eat_out    = st.selectbox("Eating out frequency", ["Rarely","2–3× per week","4–5× per week","Daily"], index=1)
                p_food_notes = st.text_area("Food preferences or patterns (optional)", height=52, placeholder="e.g. Prefers home-cooked Indian meals. Coffee 2 cups daily before noon.")

                # Stress & wellbeing
                _sec_lbl("Stress & wellbeing")
                str1,str2 = st.columns(2)
                with str1: p_stress = st.slider("Current stress level", 1, 10, 5)
                with str2: p_stressors = st.text_input("Primary stressors", placeholder="e.g. Work deadlines, health uncertainty")
                p_symptoms   = st.text_area("Current symptoms or main concerns", height=68, placeholder="e.g. Persistent fatigue throughout the day. Brain fog most pronounced mid-afternoon.")
                p_extra_note = st.text_area("Anything else your coach should know (optional)", height=52, placeholder="e.g. Have tried improving diet over past 2 years without clear results.")

                if st.form_submit_button("Save & Continue →", type="primary", use_container_width=True):
                    db_upsert("profiles", {"id": user_id, "sleep_time": p_bed, "wake_time": p_wake,
                                           "alcohol": p_alc, "smoking": p_smk})
                    notes_parts = []
                    if primary_goal: notes_parts.append(f"Primary goal: {primary_goal}")
                    if p_exc:        notes_parts.append(f"Exercise: {p_exc}")
                    if p_restr:      notes_parts.append(f"Diet restrictions: {p_restr}")
                    if p_slp:        notes_parts.append(f"Sleep: {p_slp}")
                    if p_slp_c:      notes_parts.append(f"Sleep challenges: {p_slp_c}")
                    if p_food_notes: notes_parts.append(f"Food notes: {p_food_notes}")
                    if p_stressors:  notes_parts.append(f"Stressors: {p_stressors}")
                    if p_symptoms:   notes_parts.append(f"Symptoms: {p_symptoms}")
                    if p_extra_note: notes_parts.append(p_extra_note)
                    if notes_parts:
                        ex = db_get_single("profile_notes", user_id)
                        combined = ((ex.get("notes","") if ex else "") + "\n" + "\n".join(notes_parts)).strip()
                        db_upsert("profile_notes", {"user_id": user_id, "notes": combined})
                    if primary_goal:
                        db_upsert("goals", {"user_id": user_id, "goal": primary_goal, "timeframe": "3 months"})
                    save_onboarding_state(user_id, {"current_step": 5, "step4_done": True}); st.rerun()

            # Additional goals + cycle (outside form)
            goals_list = db_get("goals", user_id)
            if goals_list:
                st.caption(f"Goals added: {' · '.join([g['goal'][:40] for g in goals_list])}")
            with st.form("ob4_goal"):
                gg1,gg2 = st.columns([3,1])
                with gg1: extra_goal = st.text_input("Add another specific goal", placeholder="e.g. Resolve bloating and digestive issues")
                with gg2: extra_tf   = st.selectbox("Timeframe", ["3 months","6 months","12 months","12 months+"])
                if st.form_submit_button("+ Add goal") and extra_goal:
                    db_upsert("goals", {"user_id": user_id, "goal": extra_goal, "timeframe": extra_tf}); st.rerun()

            prof_now = db_get_single("profiles", user_id)
            if prof_now and prof_now.get("sex") == "Female":
                st.markdown("##### Cycle tracking")
                ob_cd = db_get_single("cycle_data", user_id)
                with st.form("ob4_cycle"):
                    cy1,cy2 = st.columns(2)
                    with cy1: lp_date = st.date_input("Last period start",
                        value=date.fromisoformat(ob_cd["last_period_start"]) if ob_cd and ob_cd.get("last_period_start") else date.today())
                    with cy2: avg_len = st.number_input("Avg cycle length (days)", 21, 40,
                        value=ob_cd.get("avg_cycle_length",28) if ob_cd else 28)
                    if st.form_submit_button("Save cycle data"):
                        db_upsert("cycle_data", {"user_id": user_id,
                            "last_period_start": lp_date.isoformat(), "avg_cycle_length": int(avg_len)})
                        st.success("Saved!")

            bc, _ = st.columns(2)
            with bc:
                if st.button("← Back", key="ob4_back"):
                    save_onboarding_state(user_id, {"current_step": 3}); st.rerun()

        # ══ STEP 5 — Data sources (prototype S8) ══════════════════════════
        elif step == 5:
            _ob_header("Connect your data",
                "Both optional. You can upload lab reports or connect wearable data at any time from Profile & Data inside the app.")

            existing_labs    = db_get("lab_reports", user_id, order_col="report_date")
            existing_wearable= db_get("wearable_data", user_id, order_col="data_date", limit=1)
            lab_ok           = bool(existing_labs)
            whoop_ok         = bool(existing_wearable)

            def _ds_card(icon, name, desc, status_ok, status_txt, status_pending):
                border_col = "var(--forest)" if status_ok else "var(--line)"
                bg_col     = "rgba(31,47,42,0.03)" if status_ok else "var(--white)"
                status_html= f"<div style='color:#3A6B4A;font-size:11.5px;font-weight:600;'>✓ {status_txt}</div>" if status_ok else f"<div style='color:var(--mid);font-size:11.5px;font-weight:500;'>{status_pending}</div>"
                st.markdown(f"""
                <div style="background:{bg_col};border:1.5px solid {border_col};border-radius:12px;
                            padding:16px 18px;display:flex;gap:14px;align-items:flex-start;margin-bottom:10px;">
                  <div style="width:38px;height:38px;border-radius:9px;background:var(--stone);
                              display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">{icon}</div>
                  <div style="flex:1;">
                    <div style="font-size:13px;font-weight:500;color:var(--graphite);margin-bottom:3px;">{name}</div>
                    <div style="font-size:12px;color:var(--mid);line-height:1.45;margin-bottom:6px;">{desc}</div>
                    {status_html}
                  </div>
                </div>""", unsafe_allow_html=True)

            _ds_card("🧪", "Lab Reports",
                "Upload PDF lab reports from any Indian or international diagnostic lab. OneSattva reads and interprets them against functional ranges — not conventional population reference ranges.",
                lab_ok, f"{len(existing_labs)} report(s) uploaded", "Not yet uploaded — upload below or skip for now")
            _ds_card("⌚", "WHOOP",
                "Export 4 CSV files from your WHOOP dashboard (sleep, recovery, workouts, cycles) and upload here. OneSattva reads HRV, recovery, sleep depth, and strain across your history.",
                whoop_ok, "Connected — data imported", "You can import from Profile & Data after setup")
            _ds_card("🍎", "Other wearables",
                "Oura Ring, Garmin, Apple Watch, and others — join the waitlist to be notified when your device is supported.",
                False, "", "Coming soon — join waitlist")

            st.markdown("<div style='background:rgba(17,18,20,0.03);border:1px solid var(--line);border-radius:8px;padding:11px 15px;font-size:12px;color:var(--mid);line-height:1.6;margin-bottom:16px;'>Your data is encrypted and stored securely. Used solely to personalise your coaching. Never sold or shared with third parties.</div>", unsafe_allow_html=True)

            with st.expander("📤 Upload a lab report", expanded=not lab_ok):
                with st.expander("📋 Recommended markers"):
                    st.markdown(MARKERS_INFO)
                ld = st.date_input("Report date", value=date.today(), key="ob5_ld")
                ln = st.text_input("Lab name", placeholder="e.g. Thyrocare, SRL, Apollo", key="ob5_ln")
                lv = st.text_area("Paste lab values", height=160, key="ob5_lv",
                    placeholder="TSH: 2.1\nFT3: 2.8\nFT4: 1.2\nProlactin: 18.5\nFerritin: 42\nVitamin D: 38\n...")
                if st.button("🔍 Analyse & Save", type="primary", use_container_width=True, key="ob5_save"):
                    if lv.strip():
                        with st.spinner("Analysing against functional medicine ranges..."):
                            try:
                                resp = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=2000,
                                    system="Expert integrative medicine practitioner. Analyse lab values against functional medicine optimal ranges. Be direct and concise.",
                                    messages=[{"role":"user","content": f"Lab {ld}, lab: {ln}\n\nValues:\n{lv}\n\n## Key Findings\nTable: Marker | Value | Functional Status | Priority\n## Summary\n2-3 sentences\n## Most Urgent\nTop 3"}])
                                st.divider(); st.markdown(resp.content[0].text)
                                sr = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=150,
                                    messages=[{"role":"user","content": f"One line summary max 120 chars: {lv}"}])
                                db_upsert("lab_reports", {"user_id": user_id, "report_date": ld.isoformat(),
                                    "lab_name": ln, "raw_values": lv, "summary": sr.content[0].text[:500]})
                                save_onboarding_state(user_id, {"lab_upload_acknowledged": True})
                                st.success("✅ Saved."); st.rerun()
                            except Exception as e:
                                st.error(str(e))
                    else:
                        st.warning("Paste your lab values above.")

            ob_fresh  = get_onboarding_state(user_id)
            has_labs  = bool(db_get("lab_reports", user_id))
            ack       = ob_fresh and ob_fresh.get("lab_upload_acknowledged")

            bc, cc = st.columns(2)
            with bc:
                if st.button("← Back", key="ob5_back"):
                    save_onboarding_state(user_id, {"current_step": 4}); st.rerun()
            with cc:
                btn_lbl = "Build my roadmap →" if (has_labs or ack) else "I'll upload labs later — continue"
                if st.button(btn_lbl, type="primary", use_container_width=True, key="ob5_next"):
                    save_onboarding_state(user_id, {"current_step": 6, "step5_done": True,
                        "lab_upload_acknowledged": True, "lab_acknowledged_at": datetime.now().isoformat()})
                    st.rerun()

        # ══ STEP 6 — Plan review & commit (prototype S9→S10) ══════════════
        elif step == 6:
            # Generate roadmap if not already done
            if not st.session_state.get("ob_roadmap_text"):
                saved_rm = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
                if saved_rm and saved_rm[0].get("roadmap_text"):
                    st.session_state.ob_roadmap_text = saved_rm[0]["roadmap_text"]
                    st.session_state.ob_roadmap_date = saved_rm[0].get("generated_at","")[:10]

            if not st.session_state.get("ob_roadmap_text"):
                # Generating screen (prototype S9)
                ob_meta = get_onboarding_state(user_id)
                plan    = ob_meta.get("plan_mode","Restore") if ob_meta else "Restore"
                plan_weeks = {"Reset":4,"Restore":13,"Transform":26,"Sustain":52}.get(plan,13)
                st.markdown(f"""
                <div style="text-align:center;padding:32px 0;">
                  {_mark_light(56)}
                  <div style="font-family:'Newsreader',serif;font-size:25px;color:var(--graphite);margin:20px 0 8px;">Building your roadmap</div>
                  <div style="font-size:13px;color:var(--mid);line-height:1.6;margin-bottom:24px;">
                    OneSattva is reading your full profile, lab data, and wearable history to build
                    your personalised {plan_weeks}-{"day" if plan_weeks==4 else "week"} {plan} protocol.
                  </div>
                </div>""", unsafe_allow_html=True)

                sp = build_system_prompt(user_id, db_get_single("profiles", user_id))
                ob_meta2 = get_onboarding_state(user_id)
                plan2 = ob_meta2.get("plan_mode","Restore") if ob_meta2 else "Restore"
                gen_prompt = f"""Generate a comprehensive treatment roadmap for this {plan2} programme.

FORMAT — use phases matching the {plan2} duration:
## Your {plan2} Programme — Generated {date.today().strftime("%d %B %Y")}
One sentence on what this programme addresses and why.

## Phase Timeline
| Phase | Focus | Key milestones | Checkpoint |
|---|---|---|---|
[4 phases for Restore/Transform, 2 for Reset, ongoing for Sustain — exact durations]

## Phase 1 — [Title]: [weeks/months]
What changes and why. Specific supplements/nutrition/training adjustments with exact doses.
**Retest at checkpoint:** [markers]
**What success looks like:** [2-3 measurable outcomes]

[Repeat for each phase]

## If Phase 1 Shows No Progress
[Escalation path]

**Start today:** [one specific immediate action]

Complete every section. Never cut off."""

                with st.spinner(f"Building your {plan2} roadmap — this takes 30-40 seconds..."):
                    resp = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                        system=sp, messages=[{"role":"user","content":gen_prompt}])
                    rm_text = resp.content[0].text
                    db_upsert("roadmaps", {"user_id": user_id, "roadmap_text": rm_text,
                        "committed": False, "priority_focus": plan2, "intensity": "Moderate"})
                    st.session_state.ob_roadmap_text = rm_text
                    st.session_state.ob_roadmap_date = date.today().isoformat()
                    st.rerun()
            else:
                # Review & commit screen (prototype S10)
                ob_meta3  = get_onboarding_state(user_id)
                plan3     = ob_meta3.get("plan_mode","Restore") if ob_meta3 else "Restore"
                prof_name = (db_get_single("profiles", user_id) or {}).get("full_name","")
                first3    = prof_name.split()[0] if prof_name else "there"

                st.markdown(f"""
                <div style="background:var(--forest);border-radius:12px 12px 0 0;padding:30px 30px 24px;">
                  <div style="font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;
                              color:rgba(247,245,242,0.38);margin-bottom:6px;">
                    Your personalised {plan3} programme · Generated {st.session_state.ob_roadmap_date}
                  </div>
                  <div style="font-family:'Newsreader',serif;font-style:italic;font-size:24px;color:#F7F5F2;margin-bottom:5px;">
                    Here's what OneSattva has built for you, {first3}.
                  </div>
                  <div style="font-size:12.5px;color:rgba(247,245,242,0.48);line-height:1.55;max-width:620px;">
                    Based on your profile, goals, and data. Review the roadmap. When you're ready, commit to begin.
                    You can update your data at any point — the roadmap recalibrates. It only regenerates from scratch
                    if you choose or if a major clinical shift warrants it.
                  </div>
                </div>
                <div style="background:var(--bone);border:1px solid var(--line);
                            border-radius:0 0 12px 12px;padding:24px 30px;margin-bottom:16px;">
                """, unsafe_allow_html=True)

                st.markdown(st.session_state.ob_roadmap_text)
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("""
                <div style="background:var(--cu-bg);border:1px solid var(--cu-bd);border-radius:10px;
                            padding:13px 16px;font-size:12.5px;color:var(--mid);line-height:1.6;margin-bottom:16px;">
                  <strong style="color:var(--graphite);">What committing means:</strong> Your roadmap locks in as your active plan.
                  Supplement, nutrition, and workout protocols are generated immediately. You can edit your profile data at any
                  time and the protocol recalibrates. The roadmap only changes if you request it or a major clinical finding warrants it.
                </div>""", unsafe_allow_html=True)

                c_foot1, c_foot2 = st.columns([2,1])
                with c_foot1:
                    st.caption(f"Generated from your profile on {st.session_state.ob_roadmap_date}. A starting point, not a fixed prescription.")
                with c_foot2:
                    bc2, cc2 = st.columns(2)
                    with bc2:
                        if st.button("← Revise my inputs", use_container_width=True, key="ob6_back"):
                            save_onboarding_state(user_id, {"current_step": 5}); st.rerun()
                    with cc2:
                        if st.button("Commit to this plan →", type="primary", use_container_width=True, key="ob6_commit"):
                            db_upsert("roadmaps", {"user_id": user_id,
                                "roadmap_text": st.session_state.ob_roadmap_text,
                                "committed": True, "priority_focus": plan3})
                            db_upsert("profiles", {"id": user_id, "onboarding_complete": True})
                            st.session_state.treatment_roadmap   = st.session_state.ob_roadmap_text
                            st.session_state.roadmap_committed   = True
                            st.session_state.roadmap_date        = st.session_state.ob_roadmap_date
                            st.balloons(); st.rerun()

    # Tips column
    with col_tip:
        tips = {
            1: ("Why plan mode matters",
                "Your plan mode shapes the tone of your roadmap, the urgency of protocols, and how your coach prioritises between competing goals. You can switch it later — your data always carries forward."),
            2: ("Why we ask",
                "Age, sex, height, and weight affect how we interpret your labs and calibrate nutrition and training. Location helps us suggest locally available foods and brands."),
            3: ("Your data is private",
                "Only you can see your health information. Add as much or as little as you're comfortable with. More context means more precise coaching."),
            4: ("Goals shape everything",
                "Your roadmap is built around your goals and their timeframes. After each goal is achieved, we build a maintenance guide so you keep the results long-term."),
            5: ("Why labs matter so much",
                "Functional medicine reads values differently from conventional medicine. A TSH of 2.5 might look 'normal' but mask a T3 conversion problem. Reports older than 3 months move to trend context only."),
        }
        tip_step = min(step, 5)
        title, body = tips.get(tip_step, ("",""))
        if title:
            st.markdown(f"""
            <div style="background:var(--bone);border-radius:12px;padding:16px;margin-top:52px;
                        border:1px solid var(--line);">
              <p style="font-family:Inter,sans-serif;font-weight:600;color:#111214;font-size:13px;margin:0 0 8px;">{title}</p>
              <p style="font-family:Inter,sans-serif;color:#6B6358;font-size:12.5px;margin:0;line-height:1.55;">{body}</p>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN APP — sidebar + section router
# ─────────────────────────────────────────────
def show_main_app(user):
    user_id = user.id
    profile = db_get_single("profiles", user_id)
    name    = profile.get("full_name","there") if profile else "there"
    first   = name.split()[0] if name != "there" else "there"
    cycle_day, cycle_phase, days_to_next = calculate_cycle_status(user_id)
    cycle_phase = cycle_phase or "Follicular (Day 1–14)"

    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = build_system_prompt(user_id, profile)

    # Plan context
    ob = get_onboarding_state(user_id)
    plan_mode  = ob.get("plan_mode","Restore") if ob else "Restore"
    plan_weeks = {"Reset":4,"Restore":13,"Transform":26,"Sustain":52}.get(plan_mode,13)

    saved_rm = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
    roadmap_start = None
    if saved_rm and saved_rm[0].get("committed"):
        try:
            roadmap_start = datetime.fromisoformat(saved_rm[0]["generated_at"].replace("Z","")).date()
            if not st.session_state.get("treatment_roadmap"):
                st.session_state.treatment_roadmap = saved_rm[0].get("roadmap_text","")
                st.session_state.roadmap_committed  = True
                st.session_state.roadmap_date       = roadmap_start.isoformat()
        except Exception:
            pass

    days_in       = (date.today() - roadmap_start).days if roadmap_start else 0
    current_week  = (days_in // 7) + 1 if roadmap_start else 1
    progress_pct  = min(100, int((current_week / plan_weeks) * 100)) if roadmap_start else 0

    # ── SIDEBAR ────────────────────────────────────────────────────────
    with st.sidebar:
        # Header: mark + wordmark + tagline
        sb_meta_parts = []
        if profile:
            if profile.get("location"): sb_meta_parts.append(profile["location"])
            if profile.get("age"):      sb_meta_parts.append(f"{profile['age']}yr")
            if profile.get("sex"):      sb_meta_parts.append(profile["sex"])
        sb_meta = " · ".join(sb_meta_parts)
        plan_pill_txt = f"{plan_mode} · Wk {current_week} / {plan_weeks}" if roadmap_start else plan_mode
        checkpoint_wk = min(current_week + 2, plan_weeks)

        st.markdown(f"""
        <div style="padding:0 20px 18px;border-bottom:1px solid rgba(247,245,242,0.07);">
          <div style="display:flex;align-items:center;gap:10px;">
            {_MARK_DARK}
            <div>
              <div style="font-family:'Newsreader',serif;font-weight:400;font-size:19px;
                           letter-spacing:-0.02em;color:#F7F5F2;line-height:1;">OneSattva</div>
              <div class="sb-tag">Health, understood.</div>
            </div>
          </div>
        </div>
        <div style="padding:14px 20px;border-bottom:1px solid rgba(247,245,242,0.05);margin-bottom:14px;">
          <div class="sb-name">{name}</div>
          <div class="sb-meta">{sb_meta}</div>
          <div class="plan-pill">{plan_pill_txt}</div>
        </div>
        """, unsafe_allow_html=True)

        # Nav
        if "active_section" not in st.session_state:
            st.session_state.active_section = "home"

        st.markdown('<div style="font-size:10px;font-weight:600;letter-spacing:0.08em;color:rgba(247,245,242,0.24);text-transform:uppercase;padding:0 8px;margin-bottom:5px;">Navigation</div>', unsafe_allow_html=True)

        # Inject active-state CSS for the currently active nav button
        active_now = st.session_state.get("active_section", "home")
        nav_css = ""
        nav_keys = ["home","protocol","checkin","coach","profile"]
        for nk in nav_keys:
            if active_now == nk:
                nav_css += f"[data-testid='stSidebar'] [data-testid='stButton']:has(button[data-testid='stButton'][key='nav_{nk}']) > button{{background:rgba(182,116,74,0.11)!important;color:#F7F5F2!important;}}"
        if nav_css:
            st.markdown(f"<style>{nav_css}</style>", unsafe_allow_html=True)

        NAV = [("home","⌂","Home"), ("protocol","◈","Protocol"),
               ("checkin","✓","Check-In"), ("coach","✦","Coach")]
        for sec, icon, label in NAV:
            if st.button(f"{icon}  {label}", key=f"nav_{sec}", use_container_width=True):
                st.session_state.active_section = sec; st.rerun()

        st.markdown('<div style="height:1px;background:rgba(247,245,242,0.05);margin:9px 8px;"></div>', unsafe_allow_html=True)
        if st.button("◎  Profile & Data", key="nav_profile", use_container_width=True):
            st.session_state.active_section = "profile"; st.rerun()

        # Footer
        st.markdown(f"""
        <div style="padding:0 20px;margin-top:16px;">
          <div class="sb-foot-t">{plan_mode} · {plan_weeks}-{"day" if plan_weeks==4 else "week"} programme<br>
          {"Week "+str(current_week)+" of "+str(plan_weeks)+" · Checkpoint Wk "+str(checkpoint_wk) if roadmap_start else "No active roadmap yet"}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(f'<div style="padding:0 20px;font-size:11px;color:rgba(247,245,242,0.2);">{user.email}</div>', unsafe_allow_html=True)
        if st.button("Sign out", key="signout_btn", use_container_width=True):
            sign_out()

    # ── SECTION ROUTER ─────────────────────────────────────────────────
    active = st.session_state.active_section
    if   active == "home":     _home(user_id, profile, first, cycle_day, cycle_phase, days_to_next, plan_mode, plan_weeks, current_week, progress_pct, roadmap_start)
    elif active == "protocol": _protocol(user_id, profile, cycle_day, cycle_phase, plan_mode, current_week, plan_weeks, roadmap_start, days_in)
    elif active == "checkin":  _checkin(user_id, name, first, cycle_day, cycle_phase)
    elif active == "coach":    _coach(user_id, profile, name, first, cycle_day, cycle_phase, days_to_next)
    elif active == "profile":  _profile(user_id, profile, cycle_day, cycle_phase, days_to_next)

# ─────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────
def _home(user_id, profile, first, cycle_day, cycle_phase, days_to_next,
          plan_mode, plan_weeks, current_week, progress_pct, roadmap_start):
    checkins_home   = db_get("checkins",     user_id, order_col="checkin_date", limit=1)
    wearable_home   = db_get("wearable_data",user_id, order_col="data_date",    limit=1)
    labs_home       = db_get("lab_reports",  user_id, order_col="report_date",  limit=3)
    recent_checkins = db_get("checkins",     user_id, order_col="checkin_date", limit=30)
    wearable_30d    = db_get("wearable_data",user_id, order_col="data_date",    limit=30)

    # Plan banner (forest bg, prototype-exact)
    if roadmap_start and st.session_state.get("roadmap_committed"):
        rm_name = f"{plan_mode} · {plan_weeks}-week programme"
        for ln in (st.session_state.get("treatment_roadmap","") or "").split("\n"):
            ln = ln.strip().lstrip("#").strip()
            if ln and 5 < len(ln) < 80:
                rm_name = ln; break
        st.markdown(f"""
        <div class="plan-banner">
          <div class="pb-l">
            <div>
              <div class="pb-ml">Plan mode</div>
              <div class="pb-mn">{rm_name[:60]}</div>
            </div>
            <div class="pb-bar-w">
              <div class="pb-bar"><div class="pb-fill" style="width:{progress_pct}%;"></div></div>
              <div class="pb-wk">Wk {current_week} / {plan_weeks}</div>
            </div>
          </div>
          <div class="pb-r">View roadmap →</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:var(--stone);border-radius:10px;padding:12px 16px;margin-bottom:18px;border:1px dashed rgba(17,18,20,0.15);">
          <div style="font-size:13px;color:var(--mid);">No active plan — generate a Treatment Roadmap in Protocol to unlock priorities and tracking.</div>
        </div>""", unsafe_allow_html=True)

    # Greeting
    hour = datetime.now().hour
    greeting = "Good morning" if hour<12 else ("Good afternoon" if hour<17 else "Good evening")
    st.markdown(f'<div class="pg-title">{greeting}, {first}.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pg-sub">{date.today().strftime("%A, %d %B %Y")} · Here\'s what matters today.</div>', unsafe_allow_html=True)

    # Today\'s priorities
    st.markdown('<span class="sl first">Today\'s priorities</span>', unsafe_allow_html=True)

    if "home_priorities" not in st.session_state:
        has_data = st.session_state.get("roadmap_committed") or labs_home or checkins_home or wearable_home
        if has_data:
            with st.spinner("Preparing your priorities…"):
                try:
                    rm_text = st.session_state.get("treatment_roadmap","") or ""
                    lab_sum = "\n".join([f"- {l.get('report_date','')}: {l.get('summary','')}" for l in labs_home[:3]]) if labs_home else "No labs"
                    w_sum   = ""
                    if wearable_home:
                        w = wearable_home[0]
                        w_sum = f"Latest ({w.get('data_date','')}): Recovery {w.get('recovery_score','?')}% · HRV {w.get('hrv','?')}ms"
                    c_sum = ""
                    if checkins_home:
                        c = checkins_home[0]
                        c_sum = f"Latest ({c.get('checkin_date','')}): Energy {c.get('energy','?')}/10 · Bloating {c.get('bloating','?')}"
                    pp = f"""Generate exactly 3 priority cards for today. Respond ONLY with valid JSON, no markdown:
[{{"triage":"act_today","title":"...","body":"..."}},{{"triage":"watch","title":"...","body":"..."}},{{"triage":"background","title":"...","body":"..."}}]
triage: act_today|watch|background. Title max 8 words. Body 2-3 sentences, clinical.
DATA:
Roadmap: {rm_text[:500] if rm_text else 'None'}
Labs: {lab_sum}
Wearable: {w_sum or 'None'}
Check-in: {c_sum or 'None'}
Today: {date.today().strftime('%A, %d %B %Y')}
Cycle: Day {cycle_day or '?'}, {(cycle_phase or 'Unknown').split(' (')[0]}"""
                    r = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=600,
                        messages=[{"role":"user","content":pp}])
                    raw = r.content[0].text.strip().replace("```json","").replace("```","").strip()
                    st.session_state.home_priorities = _json.loads(raw)
                except Exception:
                    st.session_state.home_priorities = []
        else:
            st.session_state.home_priorities = []

    priorities = st.session_state.get("home_priorities", [])
    TMAP = {"act_today":("Act today","t-now"), "watch":("Watch","t-watch"), "background":("Background","t-bg")}
    if priorities:
        st.markdown('<div class="prio-grid">', unsafe_allow_html=True)
        for p in priorities[:3]:
            lbl, css = TMAP.get(p.get("triage","background"), ("Background","t-bg"))
            st.markdown(f"""
            <div class="prio-card">
              <span class="triage {css}">{lbl}</span>
              <div class="pc-title">{p.get("title","")}</div>
              <div class="pc-body">{p.get("body","")}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("↺ Refresh priorities", key="refresh_prio"):
            del st.session_state["home_priorities"]; st.rerun()
    else:
        st.markdown('<div style="background:var(--stone);border-radius:12px;padding:20px;border:1px dashed rgba(17,18,20,0.12);margin-bottom:18px;"><div style="font-size:13px;color:var(--mid);">Priorities appear here once you have a roadmap, labs, or check-in data.</div></div>', unsafe_allow_html=True)

    # Snapshot
    st.markdown('<span class="sl">Today\'s snapshot</span>', unsafe_allow_html=True)
    w = wearable_home[0] if wearable_home else {}
    c = checkins_home[0] if checkins_home else {}

    def _snap(lbl, val, unit, sub, flag=""):
        flag_h = f'<div class="snap-flag">{flag}</div>' if flag else ""
        if val is None:
            return f'<div class="snap-box"><div class="snap-lbl">{lbl}</div><div style="font-size:12px;color:var(--mid);opacity:0.55;">No data</div></div>'
        return f'<div class="snap-box"><div class="snap-lbl">{lbl}</div><div class="snap-val">{val}<span class="snap-unit"> {unit}</span></div><div class="snap-sub">{sub}</div>{flag_h}</div>'

    rec = round(float(w["recovery_score"])) if w.get("recovery_score") else None
    st.markdown(f"""
    <div class="snap-grid">
      {_snap("HRV", w.get("hrv"), "ms", "WHOOP · today")}
      {_snap("Recovery", rec, "%", "WHOOP · today")}
      {_snap("Sleep", w.get("sleep_performance"), "%", "WHOOP · today")}
      {_snap("Energy", c.get("energy"), "/10", f"Check-in · {c.get('checkin_date','')}" if c else "No check-in")}
    </div>""", unsafe_allow_html=True)

    # Trends
    st.markdown('<span class="sl">Trends</span>', unsafe_allow_html=True)
    df_ci = pd.DataFrame(recent_checkins).sort_values("checkin_date") if recent_checkins else pd.DataFrame()
    df_ww = pd.DataFrame(wearable_30d).sort_values("data_date")       if wearable_30d   else pd.DataFrame()

    def _bars(vals, mx=None):
        m = mx or (max(vals) if vals else 1) or 1
        return "".join([f'<div class="tb" style="height:{max(8,int((v/m)*100))}%;"></div>' for v in vals[-15:]])

    e_insight = "Log 7+ check-ins to see your energy trend."
    e_bars    = ""
    if len(df_ci) >= 7 and "energy" in df_ci.columns:
        ev = pd.to_numeric(df_ci["energy"], errors="coerce").dropna().tolist()
        if ev:
            e_insight = f"Avg {sum(ev)/len(ev):.1f}/10 over {len(ev)} logged days."
            e_bars    = _bars(ev, 10)

    h_insight = "Upload 7+ days of wearable data to see your HRV trend."
    h_bars    = ""
    if len(df_ww) >= 7 and "hrv" in df_ww.columns:
        hv = pd.to_numeric(df_ww["hrv"], errors="coerce").dropna().tolist()
        if hv:
            h_insight = f"Avg {sum(hv)/len(hv):.0f} ms · Latest {hv[-1]:.0f} ms."
            h_bars    = _bars(hv)

    st.markdown(f"""
    <div class="trends-grid">
      <div class="trend-card">
        <div class="tc-title">Energy vs Sleep quality · 30 days</div>
        <div class="tc-insight">{e_insight}</div>
        {'<div class="tc-bars">' + e_bars + '</div>' if e_bars else '<div style="height:40px;background:rgba(230,227,223,0.4);border-radius:6px;display:flex;align-items:center;justify-content:center;"><span style="font-size:11px;color:var(--mid);">Not enough data yet</span></div>'}
      </div>
      <div class="trend-card">
        <div class="tc-title">HRV trajectory · 30 days</div>
        <div class="tc-insight">{h_insight}</div>
        {'<div class="tc-bars">' + h_bars + '</div>' if h_bars else '<div style="height:40px;background:rgba(230,227,223,0.4);border-radius:6px;display:flex;align-items:center;justify-content:center;"><span style="font-size:11px;color:var(--mid);">Not enough data yet</span></div>'}
      </div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PROTOCOL — 5 pill sub-tabs
# ─────────────────────────────────────────────
def _protocol(user_id, profile, cycle_day, cycle_phase, plan_mode, current_week, plan_weeks, roadmap_start, days_in):
    st.markdown('<div class="pg-title">Protocol</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Generated from your roadmap. Updated as your data evolves. Everything here is built by OneSattva — not entered by you.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Treatment Roadmap", "Monthly Goal", "Supplements", "Nutrition", "Workouts"])

    # ── Gap detection (7-day / 14-day logic) ────────────────────────────
    last_ci = db_get("checkins", user_id, order_col="checkin_date", limit=1)
    gap_days = 0
    if last_ci:
        try:
            gap_days = (date.today() - date.fromisoformat(last_ci[0]["checkin_date"])).days
        except Exception:
            gap_days = 0

    if gap_days >= 14:
        st.markdown("""
        <div style="background:var(--cu-bg);border:1px solid var(--cu-bd);border-radius:10px;
                    padding:14px 18px;margin-bottom:16px;">
          <div style="font-size:13px;font-weight:500;color:var(--graphite);margin-bottom:6px;">
            ⚠️ It's been """ + str(gap_days) + """ days since your last check-in
          </div>
          <div style="font-size:12.5px;color:var(--mid);line-height:1.5;">
            A gap this long may mean your protocol needs a review before continuing.
            Your coach will ask a re-entry question before making new recommendations.
            Update your profile notes with anything that has changed.
          </div>
        </div>""", unsafe_allow_html=True)
        reentry = st.text_area("What's changed in the last few weeks? (optional)",
            placeholder="e.g. Been travelling, stopped some supplements, energy has been low...",
            key="reentry_note")
        if st.button("Update my coach and continue", type="primary", key="reentry_btn"):
            if reentry.strip():
                ex = db_get_single("profile_notes", user_id)
                combined = ((ex.get("notes","") if ex else "") + f"\n\n[Re-entry {date.today()}]: {reentry}").strip()
                db_upsert("profile_notes", {"user_id": user_id, "notes": combined})
                st.session_state.system_prompt = build_system_prompt(user_id, profile)
                for k in ["weekly_supplements","weekly_nutrition","weekly_workouts","monthly_protocol"]:
                    st.session_state.pop(k, None)
                st.success("Updated. Your protocol will reflect this context.")
                st.rerun()
    elif gap_days >= 7:
        st.info(f"👋 It's been {gap_days} days since your last check-in. Has anything changed? If so, update your profile notes before generating this week's protocol.")

    # Load roadmap into session if not present
    if "treatment_roadmap" not in st.session_state: st.session_state.treatment_roadmap = None
    if "roadmap_committed" not in st.session_state: st.session_state.roadmap_committed = False
    if not st.session_state.treatment_roadmap:
        saved = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
        if saved:
            st.session_state.treatment_roadmap = saved[0].get("roadmap_text","")
            st.session_state.roadmap_committed  = saved[0].get("committed", False)
            try: st.session_state.roadmap_date = datetime.fromisoformat(saved[0]["generated_at"].replace("Z","")).strftime("%d %b %Y")
            except Exception: st.session_state.roadmap_date = "Previously"

    # ── Treatment Roadmap ─────────────────────────────────────────────
    with tab1:
        if st.session_state.treatment_roadmap and st.session_state.roadmap_committed:
            st.success(f"✅ Committed roadmap — generated {st.session_state.get('roadmap_date','Previously')}")
            st.markdown(st.session_state.treatment_roadmap)
            st.divider()
            st.download_button("⬇️ Download roadmap", data=st.session_state.treatment_roadmap,
                file_name=f"onesattva_roadmap_{date.today()}.txt", use_container_width=True)
            with st.expander("⚠️ Significant new information — update my roadmap"):
                st.warning("Update only if something significant has changed — new lab results, medication change, major health event, or goal shift.")
                change_reason = st.text_area("Describe what has changed:",
                    placeholder="e.g. New Thyrocare panel shows prolactin has normalised. Starting Cabergoline.")
                if st.button("🔄 Generate Updated Roadmap", type="primary", use_container_width=True, key="rm_update"):
                    if change_reason.strip():
                        st.session_state.roadmap_committed = False
                        st.session_state.treatment_roadmap = None
                        st.session_state.roadmap_change_reason = change_reason
                        st.rerun()
                    else:
                        st.error("Please describe what has changed.")
        elif st.session_state.treatment_roadmap:
            st.info("📋 Review your roadmap. When ready, commit to it.")
            st.markdown(st.session_state.treatment_roadmap)
            st.divider()
            c1,c2 = st.columns(2)
            with c1:
                if st.button("✅ Commit to this roadmap", type="primary", use_container_width=True, key="rm_commit"):
                    db_upsert("roadmaps", {"user_id": user_id, "roadmap_text": st.session_state.treatment_roadmap,
                        "committed": True, "priority_focus": st.session_state.get("rm_priority",""),
                        "intensity": st.session_state.get("rm_intensity","")})
                    st.session_state.roadmap_committed = True; st.rerun()
            with c2:
                if st.button("🔄 Regenerate instead", use_container_width=True, key="rm_regen"):
                    st.session_state.treatment_roadmap = None; st.rerun()
        else:
            st.markdown("##### Generate your treatment roadmap")
            rmc1,rmc2 = st.columns(2)
            with rmc1: rm_priority = st.selectbox("Priority focus", ["Balanced — all areas","Fastest path to natural conception","Fastest path to fat loss","Fastest path off thyroid medication","Gut/digestion first"], key="rm_priority")
            with rmc2: rm_intensity = st.selectbox("Change intensity", ["Moderate — sustainable, gradual","Aggressive — willing to make bigger changes faster"], key="rm_intensity")
            if st.button("🗺️ Generate My Treatment Roadmap", type="primary", use_container_width=True, key="rm_gen"):
                cc = ""
                if st.session_state.get("roadmap_change_reason"):
                    cc = f"\n\nIMPORTANT — UPDATE: {st.session_state.roadmap_change_reason}"
                rp = f"""Generate a comprehensive treatment roadmap. Priority: {rm_priority} | Intensity: {rm_intensity}{cc}

FORMAT — complete every section:
## Where Things Stand
3-4 sentences: core biological blockers, why current approach is insufficient, priority order.

## Phase 1 — Months 0-3: [title]
Table: Change | Current → New | Clinical Reason (5-7 rows, exact doses/timing)
**Retest at 3 months:** [4-5 markers]
**What success looks like:** [2-3 outcomes]

## Phase 2 — Months 3-6: [title]
Same format, 4-5 rows.
**Retest:** [markers]  **Success:** [outcomes]

## Phase 3 — Months 6-12: [title]
3-4 rows.
**Retest:** [markers]  **Success:** [outcomes]

## If Phase 1 Shows No Progress
2-3 sentences: escalation path.

## Maintenance
2-3 sentences.

**Start today:** [one specific immediate action]

Complete every section. Never cut off."""
                with st.spinner("Building your treatment roadmap — 30-40 seconds..."):
                    rr = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                        system=st.session_state.system_prompt, messages=[{"role":"user","content":rp}])
                    st.session_state.treatment_roadmap = rr.content[0].text
                    st.session_state.roadmap_date      = date.today().strftime("%d %b %Y")
                    db_upsert("roadmaps", {"user_id": user_id, "roadmap_text": st.session_state.treatment_roadmap,
                        "committed": False, "priority_focus": rm_priority, "intensity": rm_intensity})
                    st.rerun()

    # ── Monthly Goal ─────────────────────────────────────────────────
    with tab2:
        if not st.session_state.get("treatment_roadmap"):
            st.info("💡 Generate and commit your Treatment Roadmap first.")
        else:
            current_month_name = date.today().strftime("%B %Y")
            current_month_num  = (days_in // 30) + 1 if roadmap_start else 1
            roadmap_phase      = "Phase 1" if days_in < 90 else ("Phase 2" if days_in < 180 else "Phase 3")
            mhc, mbc = st.columns([3,1])
            with mbc:
                if st.button("↻ Regenerate", use_container_width=True, key="refresh_month"):
                    st.session_state.monthly_protocol = None
            if "monthly_protocol" not in st.session_state: st.session_state.monthly_protocol = None
            if "monthly_protocol_month" not in st.session_state: st.session_state.monthly_protocol_month = None
            if not st.session_state.monthly_protocol or st.session_state.monthly_protocol_month != current_month_name:
                with st.spinner(f"Building {current_month_name} goal..."):
                    mp = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=1500,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":
                            f"Generate monthly protocol for Month {current_month_num} ({current_month_name}). Roadmap phase: {roadmap_phase}. Week {current_week}.\n\n"
                            "FORMAT:\n## Month focus — [one sentence]\n\n**Milestones to hit this month:**\n- [3-4 measurable milestones]\n\n"
                            "**What changes this month:**\n| Area | Change |\n|---|---|\n| Supplements | |\n| Nutrition | |\n| Training | |\n| Lifestyle | |\n\n"
                            "**What to monitor:**\n- [2-3 things]\n\n**End of month check:** [what to assess]"}])
                    st.session_state.monthly_protocol       = mp.content[0].text
                    st.session_state.monthly_protocol_month = current_month_name
            st.markdown(st.session_state.monthly_protocol)

    # ── Supplements ───────────────────────────────────────────────────
    with tab3:
        if not st.session_state.get("treatment_roadmap"):
            st.info("💡 Generate and commit your Treatment Roadmap first.")
        else:
            if "weekly_supplements" not in st.session_state: st.session_state.weekly_supplements = None
            if st.session_state.weekly_supplements:
                supp_feedback = st.text_input("Want to adjust anything?",
                    placeholder="e.g. I stopped taking Zinc, add Ashwagandha for stress",
                    key="supp_feedback")
                regen_col, _ = st.columns([2,3])
                with regen_col:
                    regen_supps = st.button("↻ Regenerate with changes", key="regen_supps")
            else:
                supp_feedback = ""
                regen_supps   = False
            if st.button("Generate Supplement Schedule", type="primary", use_container_width=True, key="gen_supps") or regen_supps:
                if regen_supps: st.session_state.weekly_supplements = None
                with st.spinner("Building supplement schedule..."):
                    rs = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=2000,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":
                            f"Generate the daily supplement & timing schedule for Week {current_week}.\n\n"
                            "## Daily Routine & Supplement Schedule\n"
                            "Table: Time | Supplement | Dose | Clinical Notes\n"
                            "If Thyronorm/Levothyroxine prescribed: MUST be first row at wake time, water only, 45-60 min before anything else.\n"
                            "Complete fully. Never cut off."}])
                    st.session_state.weekly_supplements = rs.content[0].text
            if st.session_state.weekly_supplements:
                st.markdown(st.session_state.weekly_supplements)

    # ── Nutrition ─────────────────────────────────────────────────────
    with tab4:
        if not st.session_state.get("treatment_roadmap"):
            st.info("💡 Generate and commit your Treatment Roadmap first.")
        else:
            if "weekly_nutrition" not in st.session_state: st.session_state.weekly_nutrition = None
            np_focus = st.selectbox("Priority focus", ["Balanced","Fat loss","Fertility & conception","Gut healing","Energy & thyroid","Sleep & recovery"], key="np_focus")
            if st.session_state.weekly_nutrition:
                nut_feedback = st.text_input("Want to adjust anything?",
                    placeholder="e.g. I'm travelling this week, need simpler meals",
                    key="nut_feedback")
                rn_col, _ = st.columns([2,3])
                with rn_col:
                    regen_nut = st.button("↻ Regenerate with changes", key="regen_nut")
            else:
                nut_feedback = ""
                regen_nut    = False
            if st.button("Generate Nutrition Plan", type="primary", use_container_width=True, key="gen_nutrition") or regen_nut:
                if regen_nut: st.session_state.weekly_nutrition = None
                day_names = [(datetime.now()+timedelta(days=i)).strftime("%A %d %b") for i in range(7)]
                with st.spinner("Building 7-day nutrition plan..."):
                    rn = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":
                            f"Generate 7-day nutrition plan. Focus: {np_focus}. Cycle Day {cycle_day or '?'} ({(cycle_phase or '').split(' (')[0]}).\n\n"
                            f"## 7-Day Nutrition Plan\nTable columns: Meal Slot | {' | '.join(day_names)}\n"
                            "Rows: First Meal | Lunch | Evening Snack | Dinner\n"
                            "One specific food + portion per cell, max 10 words. Gut-friendly, cooked/warm. Vary each day. Complete all 7 days."}])
                    st.session_state.weekly_nutrition = rn.content[0].text
            if st.session_state.weekly_nutrition:
                st.markdown(st.session_state.weekly_nutrition)

    # ── Workouts ──────────────────────────────────────────────────────
    with tab5:
        if not st.session_state.get("treatment_roadmap"):
            st.info("💡 Generate and commit your Treatment Roadmap first.")
        else:
            if "weekly_workouts" not in st.session_state: st.session_state.weekly_workouts = None
            if st.session_state.weekly_workouts:
                wo_feedback = st.text_input("Want to adjust anything?",
                    placeholder="e.g. Knee is sore this week, avoid squats",
                    key="wo_feedback")
                rw_col, _ = st.columns([2,3])
                with rw_col:
                    regen_wo = st.button("↻ Regenerate with changes", key="regen_wo")
            else:
                wo_feedback = ""
                regen_wo    = False
            if st.button("Generate Training Plan", type="primary", use_container_width=True, key="gen_workouts") or regen_wo:
                if regen_wo: st.session_state.weekly_workouts = None
                day_names = [(datetime.now()+timedelta(days=i)).strftime("%A %d %b") for i in range(7)]
                with st.spinner("Building training plan..."):
                    rw = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=3000,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":
                            f"Generate 7-day training plan for Week {current_week}. Cycle Day {cycle_day or '?'} ({(cycle_phase or '').split(' (')[0]}).\n\n"
                            f"## 7-Day Training Plan\nTable: Day | Session Type | Specific Focus | Key Exercises\n"
                            f"Days: {', '.join(day_names)}\nInclude rest day, recovery-aware sessions, cycle-phase appropriate loads.\n\n"
                            "## This Week's Priorities\n3 bullets: (1) sleep/recovery target (2) lifestyle/gut-healing practice (3) thing to monitor\n\n"
                            f"**Start today ({day_names[0]}):** [one specific action]\n\nComplete fully."}])
                    st.session_state.weekly_workouts = rw.content[0].text
            if st.session_state.weekly_workouts:
                st.markdown(st.session_state.weekly_workouts)


# ─────────────────────────────────────────────
# CHECK-IN (prototype-exact: insight-box first, ci-grid 6 fields)
# ─────────────────────────────────────────────
def _checkin(user_id, name, first, cycle_day, cycle_phase):
    hour = datetime.now().hour
    time_g = "Morning check-in" if hour<12 else ("Afternoon check-in" if hour<17 else "Evening check-in")
    st.markdown('<div class="pg-title">Daily Check-In</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pg-sub">{time_g} · {date.today().strftime("%A, %d %B")} · Cycle Day {cycle_day or "?"}. Pre-filled from yesterday. Edit anything that has changed. Takes less than 2 minutes.</div>', unsafe_allow_html=True)

    today_ci = db_get("checkins", user_id, order_col="checkin_date", limit=2)
    already  = today_ci and today_ci[0].get("checkin_date") == date.today().isoformat()
    prev     = today_ci[0] if already else (today_ci[0] if today_ci else {})
    # If already logged, use yesterday\'s for defaults in edit mode
    if already and len(today_ci) > 1:
        yest = today_ci[1]
    else:
        yest = prev if not already else {}

    def pv(k, d):
        val = prev.get(k, yest.get(k, d)) if already else yest.get(k, d)
        try:   return type(d)(val) if val is not None else d
        except: return d

    # INSIGHT BOX — shown when already logged
    if already:
        row = today_ci[0]
        if "checkin_insight" not in st.session_state:
            rfi = db_get("checkins", user_id, order_col="checkin_date", limit=7)
            rp  = ", ".join([f"energy {c.get('energy','?')}, bloating {c.get('bloating','?')}" for c in (rfi or [])[:5]])
            ip  = (f"Today's check-in for {name}: Cycle Day {cycle_day or '?'} · {cycle_phase or 'Unknown'}\n"
                   f"Energy: {row.get('energy')}/10 · Mental clarity: {row.get('mood')}/10 · "
                   f"Sleep quality: {row.get('sleep_quality')}/10 · Gut: {row.get('bloating')} bloating\n"
                   f"Notes: {row.get('notes','')}\nRecent pattern: {rp}\n\n"
                   "Give ONE sharp clinical observation in 2-3 sentences. Reference cycle phase and pattern. "
                   "Be direct. End with one concrete action for today if warranted.")
            with st.spinner(""):
                ir = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=300,
                    system=st.session_state.system_prompt, messages=[{"role":"user","content":ip}])
                st.session_state.checkin_insight = ir.content[0].text

        if st.session_state.get("checkin_insight"):
            st.markdown(f"""
            <div class="insight-box">
              <div class="ib-lbl">✦ Coach · Yesterday's insight</div>
              <div class="ib-txt">"{st.session_state.checkin_insight}"</div>
            </div>""", unsafe_allow_html=True)

        st.success("✅ Logged for today")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Energy",        f"{row.get('energy','?')}/10")
        c2.metric("Mental clarity", f"{row.get('mood','?')}/10")
        c3.metric("Sleep quality",  f"{row.get('sleep_quality','?')}/10")
        c4.metric("Gut",            row.get("bloating","?"))
        if row.get("notes"): st.caption(f"📝 {row['notes']}")
        st.divider()
        if st.button("✏️ Edit today's check-in", use_container_width=True, key="edit_ci"):
            st.session_state.edit_checkin = True; st.rerun()

    if not already or st.session_state.get("edit_checkin"):
        ci_col1, ci_col2 = st.columns(2)
        with ci_col1:
            st.markdown("<p style='font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin-bottom:4px;'>Energy</p>", unsafe_allow_html=True)
            c_energy = st.slider("Energy", 1, 10, pv("energy",5), key="ci_e", label_visibility="collapsed")
            st.markdown("<p style='font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin:12px 0 4px;'>Sleep quality</p>", unsafe_allow_html=True)
            c_sleep_q = st.slider("Sleep quality", 1, 10, pv("sleep_quality",5), key="ci_sq", label_visibility="collapsed")
            st.markdown("<p style='font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin:12px 0 4px;'>Gut / digestion</p>", unsafe_allow_html=True)
            bloat_opts = ["None","Mild","Moderate","Severe"]
            c_bloating = st.selectbox("Gut", bloat_opts,
                index=bloat_opts.index(pv("bloating","None")) if pv("bloating","None") in bloat_opts else 0,
                key="ci_b", label_visibility="collapsed")

        with ci_col2:
            st.markdown("<p style='font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin-bottom:4px;'>Mental clarity</p>", unsafe_allow_html=True)
            c_mood = st.slider("Mental clarity", 1, 10, pv("mood",5), key="ci_m", label_visibility="collapsed")
            st.markdown("<p style='font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin:12px 0 4px;'>Mood</p>", unsafe_allow_html=True)
            c_stress = st.slider("Mood", 1, 10, pv("stress",5), key="ci_s", label_visibility="collapsed")
            st.markdown("<p style='font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin:12px 0 4px;'>Libido</p>", unsafe_allow_html=True)
            lib_opts = ["Good","Average","Poor"]
            c_libido = st.selectbox("Libido", lib_opts,
                index=lib_opts.index(pv("digestion","Good")) if pv("digestion","Good") in lib_opts else 0,
                key="ci_l", label_visibility="collapsed")

        c_sleep_hrs = st.number_input("Sleep hours last night", 0.0, 12.0, pv("sleep_hours",7.0), step=0.5, key="ci_sh")
        c_workout   = st.selectbox("Today's workout",
            ["Strength Training","Padel","Cardio","Pilates","Walk/Steps only","Rest day","Other"], key="ci_w")
        c_notes     = st.text_area("Anything notable today? (optional)",
            placeholder="e.g. Headache this morning. Noticed more energy after lunch. Want to ask about increasing training load...",
            height=80, key="ci_n")

        if st.button("Save today's check-in →", type="primary", use_container_width=True, key="ci_save"):
            if cycle_day:
                if   cycle_day <= 5:  ph = "Menstruation"
                elif cycle_day <= 13: ph = "Follicular"
                elif cycle_day <= 16: ph = "Ovulation"
                else:                 ph = "Luteal"
            else: ph = "Unknown"
            db_upsert("checkins", {"user_id": user_id, "checkin_date": date.today().isoformat(),
                "cycle_day": cycle_day, "cycle_phase": ph,
                "energy": c_energy, "mood": c_mood, "stress": c_stress,
                "sleep_hours": c_sleep_hrs, "sleep_quality": c_sleep_q,
                "bloating": c_bloating, "digestion": c_libido, "workout": c_workout, "notes": c_notes})
            st.session_state.system_prompt = build_system_prompt(user_id, db_get_single("profiles", user_id))
            st.session_state.pop("checkin_insight", None)
            st.session_state.pop("edit_checkin", None)
            st.rerun()

# ─────────────────────────────────────────────
# COACH (prototype-exact: forest welcome box + ch-hd labels)
# ─────────────────────────────────────────────
def _coach(user_id, profile, name, first, cycle_day, cycle_phase, days_to_next):
    st.markdown('<div class="pg-title">Coach</div>', unsafe_allow_html=True)

    if "messages" not in st.session_state: st.session_state.messages = []

    rm_ctx = ""
    if st.session_state.get("treatment_roadmap") and st.session_state.get("roadmap_committed"):
        rm_ctx += f"\n\nCOMMITTED ROADMAP:\n{st.session_state.treatment_roadmap[:1500]}"
    if st.session_state.get("monthly_protocol"):
        rm_ctx += f"\n\nCURRENT MONTH PROTOCOL:\n{st.session_state.monthly_protocol[:800]}"

    cycle_ctx  = f"\n\nCYCLE: {cycle_phase or 'Unknown'}"
    if cycle_day:     cycle_ctx += f", Day {cycle_day}"
    if days_to_next:  cycle_ctx += f", ~{days_to_next}d until next period"
    cycle_ctx += f". Today: {date.today().strftime('%A %d %B %Y')}."

    full_system = st.session_state.system_prompt + cycle_ctx + rm_ctx

    # Welcome (shown when no messages)
    if not st.session_state.messages:
        last_ci   = db_get("checkins",     user_id, order_col="checkin_date", limit=1)
        recent_w  = db_get("wearable_data",user_id, order_col="data_date",    limit=1)
        ctx_parts = []
        if cycle_day: ctx_parts.append(f"Day {cycle_day} · {cycle_phase.split(' (')[0]}")
        if last_ci and last_ci[0].get("energy"):
            e = last_ci[0]["energy"]; ci_d = last_ci[0].get("checkin_date","")
            if int(e) <= 4: ctx_parts.append(f"Low energy ({e}/10) on last check-in ({ci_d})")
            elif last_ci[0].get("bloating","") in ["Moderate","Severe"]: ctx_parts.append(f"{last_ci[0]['bloating'].lower()} bloating on last check-in")
        if recent_w and recent_w[0].get("recovery_score") and float(recent_w[0]["recovery_score"]) < 50:
            ctx_parts.append(f"WHOOP recovery {recent_w[0]['recovery_score']}% — low")
        ctx_line = " · ".join(ctx_parts)

        # Prototype-exact: forest insight-box as welcome
        st.markdown(f"""
        <div class="insight-box" style="margin-bottom:20px;">
          <div class="ib-lbl">✦ OneSattva Coach</div>
          <div class="ib-txt">Good to see you, {first}. I have your full profile, labs, and goals. Ask me anything.</div>
          {f'<div style="font-size:12px;color:rgba(182,116,74,0.8);margin-top:8px;">{ctx_line}</div>' if ctx_line else ""}
        </div>""", unsafe_allow_html=True)

        # Quick prompts
        if cycle_phase and "Luteal" in cycle_phase:
            q3 = ("🧘 Managing luteal phase", f"I'm in Luteal phase, Day {cycle_day}. What should I do differently this week for training, nutrition, and lifestyle?")
        elif cycle_phase and "Follicular" in cycle_phase:
            q3 = ("⚡ Maximising follicular phase", f"I'm in Follicular phase, Day {cycle_day}. How do I maximise the energy and anabolic advantage this week?")
        elif cycle_phase and "Ovulation" in cycle_phase:
            q3 = ("🌸 Ovulation — what to do", f"I'm at ovulation, Day {cycle_day}. Most important things for the next 48-72 hours?")
        else:
            q3 = ("🩸 Managing menstruation", f"I'm menstruating, Day {cycle_day}. Training modifications, nutrition priorities, what to avoid?")

        prompts = [
            ("💊 My supplement protocol today", f"Complete supplement schedule for today ({date.today().strftime('%A')}), Cycle Day {cycle_day or '?'} ({(cycle_phase or '').split(' (')[0]}). Exact brands, doses, timing in order."),
            ("🍽️ What to eat today", f"What to eat today — {date.today().strftime('%A')}, Cycle Day {cycle_day or '?'}, {(cycle_phase or '').split(' (')[0]} phase. Specific meals with portions and timing."),
            q3,
            ("⚡ Why is my energy low?", "Based on my labs and current cycle phase, most likely biological reasons for low energy and what I can do today."),
        ]
        qc1,qc2 = st.columns(2)
        for i, (lbl, content) in enumerate(prompts):
            with (qc1 if i%2==0 else qc2):
                if st.button(lbl, use_container_width=True, key=f"qp_{i}"):
                    st.session_state.messages.append({"role":"user","content":content}); st.rerun()

    MAX_H = 20
    for msg in st.session_state.messages[-MAX_H:]:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown('<div class="ch-hd">✦ OneSattva Coach</div>', unsafe_allow_html=True)
            st.markdown(msg["content"])

    ctrl1,ctrl2 = st.columns([5,1])
    with ctrl2:
        if st.button("Clear chat", use_container_width=True, key="clear_chat"):
            st.session_state.messages = []; st.rerun()

    if prompt := st.chat_input("Ask your coach anything…"):
        st.session_state.messages.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner(""):
                rr = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                    system=full_system, messages=st.session_state.messages[-MAX_H:])
                reply = rr.content[0].text
                st.markdown('<div class="ch-hd">✦ OneSattva Coach</div>', unsafe_allow_html=True)
                st.markdown(reply)
        st.session_state.messages.append({"role":"assistant","content":reply})


# ─────────────────────────────────────────────
# PROFILE & DATA (3 sub-tabs: User Profile | Lab Reports & Documents | Wearable Data)
# ─────────────────────────────────────────────
def _profile(user_id, profile, cycle_day, cycle_phase, days_to_next):
    st.markdown('<div class="pg-title">Profile & Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Everything you\'ve brought to OneSattva. All fields are editable at any time — your data is always yours.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["User Profile", "Lab Reports & Documents", "Wearable Data"])

    # ── User Profile ─────────────────────────────────────────────────
    with tab1:
        all_labs_p = db_get("lab_reports", user_id, order_col="report_date", limit=1)
        if all_labs_p:
            lab_age_p = (date.today() - _safe_date(all_labs_p[0].get("report_date",""))).days
            if lab_age_p > 90:
                st.markdown(f"""
                <div class="cp-banner">
                  <div style="color:var(--copper);font-size:15px;flex-shrink:0;margin-top:1px;">✦</div>
                  <div>
                    <div style="font-size:12.5px;color:var(--graphite);line-height:1.5;">
                      <strong style="color:var(--copper);">Coach notice:</strong> Your last lab report ({all_labs_p[0].get("report_date","")}) is {lab_age_p} days old — outside the 3-month active window. New labs would enable more precise protocol calibration.
                    </div>
                    <div style="color:var(--copper);font-weight:500;font-size:12px;margin-top:5px;cursor:pointer;">Upload new labs in the Lab Reports tab →</div>
                  </div>
                </div>""", unsafe_allow_html=True)

        # 2-card grid: Demographics + Medical History
        conds_p = db_get("medical_history", user_id)
        meds_p  = db_get("medications", user_id)
        supps_p = db_get("supplements", user_id)
        goals_p = db_get("goals", user_id)

        st.markdown('<div class="prof-grid">', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown("""<div class="prof-card">
              <div class="prof-card-hd"><h4>Demographics</h4></div>""", unsafe_allow_html=True)
            if profile:
                rows = [
                    ("Name",         profile.get("full_name","")),
                    ("Date of birth", f"{profile.get('date_of_birth','')} ({profile.get('age','')}yr)" if profile.get("age") else profile.get("date_of_birth","")),
                    ("Biological sex",profile.get("sex","")),
                    ("Location",     profile.get("location","")),
                    ("Height",       f"{profile.get('height_cm','')} cm" if profile.get("height_cm") else ""),
                    ("Weight",       f"{profile.get('weight_kg','')} kg" if profile.get("weight_kg") else ""),
                ]
                for k,v in rows:
                    if v: st.markdown(f'<div class="pr"><span class="pr-k">{k}</span><span class="pr-v">{v}</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("✏️ Edit demographics"):
                with st.form("demo_form"):
                    p_name = st.text_input("Full Name", value=profile.get("full_name","") if profile else "")
                    p_loc  = st.text_input("Location",  value=profile.get("location","")  if profile else "")
                    p_h    = st.number_input("Height (cm)", 100, 220, value=int(profile.get("height_cm",165)) if profile and profile.get("height_cm") else 165)
                    p_w    = st.number_input("Weight (kg)", 30, 200,  value=int(profile.get("weight_kg",60))  if profile and profile.get("weight_kg")  else 60)
                    p_d    = st.selectbox("Eating pattern", ["Omnivore","Vegetarian","Vegan","Pescatarian","Other"])
                    if st.form_submit_button("Save changes", type="primary"):
                        db_upsert("profiles", {"id": user_id, "full_name": p_name, "location": p_loc, "height_cm": p_h, "weight_kg": p_w, "diet": p_d})
                        st.session_state.system_prompt = build_system_prompt(user_id, db_get_single("profiles", user_id))
                        st.success("Saved!"); st.rerun()

        with pc2:
            st.markdown("""<div class="prof-card">
              <div class="prof-card-hd"><h4>Medical History</h4></div>""", unsafe_allow_html=True)
            for c in conds_p[:3]:
                st.markdown(f'<div class="pr"><span class="pr-k">{c["condition"]}</span><span class="pr-v">{c.get("notes","")[:25]}</span></div>', unsafe_allow_html=True)
            for m in meds_p[:3]:
                st.markdown(f'<div class="pr"><span class="pr-k">{m["name"]}</span><span class="pr-v">{m.get("dose","")} {m.get("frequency","")[:20]}</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            with st.expander("✏️ Edit medical history"):
                for c in conds_p:
                    r1,r2 = st.columns([8,1])
                    r1.write(f"**{c['condition']}** — {c.get('notes','')[:40]}")
                    if r2.button("✕", key=f"dc_{c['id']}"): db_delete("medical_history", c["id"]); st.rerun()
                with st.form("add_cond_p"):
                    n1,n2 = st.columns([3,2])
                    with n1: nc = st.text_input("Condition")
                    with n2: nn = st.text_input("Notes")
                    if st.form_submit_button("+ Add") and nc:
                        db_upsert("medical_history", {"user_id": user_id, "condition": nc, "notes": nn}); st.rerun()

        # Accordions: Goals / Supplements / Dietary / Lifestyle / Cycle / Plan mode
        with st.expander("Goals", expanded=True):
            if goals_p:
                st.write(" · ".join([g["goal"][:60] for g in goals_p]))
            with st.form("add_goal_p"):
                gg1,gg2 = st.columns([3,1])
                with gg1: ng = st.text_input("Add a goal", placeholder="e.g. Reach 52kg by December")
                with gg2: ntf= st.selectbox("Timeframe", ["3 months","6 months","12 months","12 months+"])
                if st.form_submit_button("+ Add goal") and ng:
                    db_upsert("goals", {"user_id": user_id, "goal": ng, "timeframe": ntf}); st.rerun()
            for g in goals_p:
                gc1,gc2 = st.columns([8,1])
                gc1.caption(f"**{g['goal']}** · _{g.get('timeframe','')}_")
                if gc2.button("✕", key=f"dg_{g['id']}"): db_delete("goals", g["id"]); st.rerun()

        with st.expander("Current supplements"):
            if supps_p:
                st.write(" · ".join([f"{s['name']} — {s.get('dose','')} ({s.get('timing','')})" for s in supps_p]))
            for s in supps_p:
                sc1,sc2 = st.columns([8,1])
                sc1.caption(f"**{s['name']}** — {s.get('dose','')} ({s.get('timing','')})")
                if sc2.button("✕", key=f"ds_{s['id']}"): db_delete("supplements", s["id"]); st.rerun()
            with st.form("add_supp_p"):
                ss1,ss2,ss3 = st.columns(3)
                with ss1: ns = st.text_input("Supplement")
                with ss2: nsd= st.text_input("Dose")
                with ss3: nst= st.text_input("Timing")
                if st.form_submit_button("+ Add") and ns:
                    db_upsert("supplements", {"user_id": user_id, "name": ns, "dose": nsd, "timing": nst, "active": True}); st.rerun()

        with st.expander("Medications"):
            for m in meds_p:
                mc1,mc2 = st.columns([8,1])
                mc1.write(f"**{m['name']}** — {m.get('dose','')} {m.get('frequency','')}")
                if mc2.button("✕", key=f"dm_{m['id']}"): db_delete("medications", m["id"]); st.rerun()
            with st.form("add_med_p"):
                mm1,mm2,mm3 = st.columns(3)
                with mm1: nm = st.text_input("Medication")
                with mm2: nd = st.text_input("Dose")
                with mm3: nf = st.text_input("Frequency")
                if st.form_submit_button("+ Add") and nm:
                    db_upsert("medications", {"user_id": user_id, "name": nm, "dose": nd, "frequency": nf, "active": True}); st.rerun()

        with st.expander("Dietary profile & restrictions"):
            if profile:
                st.write(profile.get("diet","") + (f" · {profile.get('allergies','')}" if profile.get("allergies") else ""))
            with st.form("diet_form"):
                p_diet3 = st.selectbox("Eating pattern", ["Omnivore","Vegetarian","Vegan","Pescatarian","Other"])
                p_alg   = st.text_input("Allergies / intolerances", value=profile.get("allergies","") if profile else "")
                if st.form_submit_button("Save"): db_upsert("profiles", {"id": user_id, "diet": p_diet3, "allergies": p_alg}); st.success("Saved!")

        with st.expander("Lifestyle — activity, sleep, stress"):
            notes_r = db_get_single("profile_notes", user_id)
            cur_n   = notes_r.get("notes","") if notes_r else ""
            new_n   = st.text_area("Notes (lifestyle, activity, sleep, stress)", value=cur_n, height=120,
                placeholder="e.g. Gym 3× per week. Sleep 6.5hrs avg. Stress 7/10. Started Thorne B-Complex on 15 June.")
            if st.button("💾 Save notes", type="primary", key="save_notes"):
                db_upsert("profile_notes", {"user_id": user_id, "notes": new_n})
                st.session_state.system_prompt = build_system_prompt(user_id, profile)
                st.success("Saved.")

        with st.expander("Cycle tracking"):
            cd_p = db_get_single("cycle_data", user_id)
            if cycle_day: st.metric(f"Today — Day {cycle_day}", cycle_phase.split(' (')[0])
            with st.form("cycle_p_form"):
                cy1,cy2 = st.columns(2)
                with cy1: new_lp = st.date_input("Last period start", value=date.fromisoformat(cd_p["last_period_start"]) if cd_p and cd_p.get("last_period_start") else date.today())
                with cy2: new_al = st.number_input("Avg cycle length", 21, 40, value=cd_p.get("avg_cycle_length",27) if cd_p else 27)
                if st.form_submit_button("Update"):
                    db_upsert("cycle_data", {"user_id": user_id, "last_period_start": new_lp.isoformat(), "avg_cycle_length": int(new_al)}); st.success("Updated!"); st.rerun()
            if st.button("New period started today", key="new_period_p"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": date.today().isoformat()})
                st.session_state.system_prompt = build_system_prompt(user_id, profile); st.rerun()

        with st.expander("Plan mode"):
            ob_p = get_onboarding_state(user_id)
            pm = ob_p.get("plan_mode","Restore") if ob_p else "Restore"
            st.write(f"{pm} · Started via onboarding · Change plan mode by contacting support or regenerating your roadmap.")


    # ── Lab Reports & Documents ──────────────────────────────────────
    with tab2:
        all_labs = db_get("lab_reports", user_id, order_col="report_date")
        if all_labs:
            latest_lab = all_labs[-1]
            try:
                lad = (date.today() - date.fromisoformat(latest_lab["report_date"])).days
                if   lad <= 90:  st.success(f"✅ Current labs: {latest_lab['report_date']} ({lad} days ago)")
                elif lad <= 180: st.warning(f"⚠️ Last labs: {latest_lab['report_date']} ({lad} days ago) — consider retesting")
                else:            st.error(  f"🚨 Last labs: {latest_lab['report_date']} ({lad} days ago) — too old.")
            except Exception: pass

        st.markdown("""<div class="upload-zone"><div class="uz-icon">↑</div>
        <div>Drop your lab report here, or click to browse</div>
        <div style="font-size:11px;margin-top:4px;opacity:0.7;">PDF or image · Thyrocare, SRL, Metropolis, Apollo, or any standard format</div></div>""", unsafe_allow_html=True)

        with st.expander("📤 Paste lab values to analyse & save", expanded=not bool(all_labs)):
            with st.expander("📋 Recommended markers"):
                st.markdown(MARKERS_INFO)
            rdate = st.date_input("Report date", value=date.today(), key="lab_date")
            lname = st.text_input("Lab name", placeholder="e.g. Thyrocare, SRL, Apollo", key="lab_name")
            lvals = st.text_area("Paste lab values", height=200, key="lab_raw",
                placeholder="TSH: 1.83\nFT3: 2.2\nFT4: 1.31\nProlactin: 43.6\nFerritin: 35\n...")
            if st.button("🔍 Analyse & Save Report", type="primary", use_container_width=True, key="lab_analyse"):
                if lvals.strip():
                    prev_ctx = ""
                    if all_labs:
                        prev = all_labs[-1]
                        prev_ctx = "\n\nMOST RECENT PREVIOUS REPORT (" + str(prev.get("report_date","")) + " · " + str(prev.get("lab_name","")) + "):\n" + str(prev.get("raw_values",""))[:800]
                    ap = ("New lab report — date: " + str(rdate.isoformat()) + ", lab: " + lname + "\n\nNEW VALUES:\n" + lvals + prev_ctx +
                          "\n\nAnalyse against functional medicine optimal ranges.\n\n"
                          "## Key Findings\nTable: Marker | Value | Functional Range | Status | Trend vs Previous\n"
                          "Status: ✅ Optimal · ⚠️ Suboptimal · 🚨 Needs attention\n"
                          "Trend: ↑ Rising · ↓ Falling · → Stable · — No previous data\n\n"
                          "## What This Report Tells Us\n2-3 sentences.\n\n"
                          "## Priority Actions\n3-5 specific changes.\n\n"
                          "## What to Retest Next Time\n\n**Start today:** [one immediate action]\n\nComplete every section.")
                    with st.spinner("Analysing against functional medicine ranges..."):
                        rr = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                            system=st.session_state.system_prompt, messages=[{"role":"user","content":ap}])
                        analysis = rr.content[0].text
                    st.divider(); st.markdown(analysis)
                    sr = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=150,
                        messages=[{"role":"user","content":"One dense line summary max 150 chars: " + lvals}])
                    db_upsert("lab_reports", {"user_id": user_id, "report_date": rdate.isoformat(),
                        "lab_name": lname, "raw_values": lvals, "summary": sr.content[0].text[:500]})
                    st.success("✅ Report saved.")
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.rerun()
                else:
                    st.warning("Paste your lab values above.")

        if all_labs:
            st.markdown("<span class=\'sl\'>Imported reports (" + str(len(all_labs)) + ")</span>", unsafe_allow_html=True)
            for lab in reversed(all_labs):
                try:
                    la = (date.today() - date.fromisoformat(lab["report_date"])).days
                    tag    = "🟢 Current" if la<=90 else ("🟡 Recent" if la<=180 else "⚪ Historical")
                    status = "Interpreted" if la<=180 else "Historical context"
                except Exception:
                    tag = ""; status = ""
                row_html = ("<div class=\'file-row\'><div><div class=\'fn\'>" + tag + " " +
                            lab.get("report_date","") + " · " + lab.get("lab_name","") +
                            "</div><div style=\'color:var(--mid);font-size:11px;\'>" +
                            lab.get("summary","")[:70] + "</div></div>" +
                            "<div class=\'fok\'>✓ " + status + "</div></div>")
                st.markdown(row_html, unsafe_allow_html=True)
                with st.expander("View · " + lab.get("report_date","") + " · " + lab.get("lab_name","")):
                    st.text_area("Raw values", value=lab.get("raw_values",""), key="lrv_" + str(lab["id"]), height=100)
                    if st.button("🗑️ Delete", key="dl_" + str(lab["id"])):
                        db_delete("lab_reports", lab["id"]); st.rerun()

    # ── Wearable Data ────────────────────────────────────────────────
    with tab3:
        
                COL_MAP = {
                    "date": ["Cycle start time","Cycle Start Time","Wake onset","Date","date"],
                    "recovery_score": ["Recovery score %","Recovery Score %","Recovery Score","recovery_score"],
                    "hrv": ["Heart rate variability (ms)","HRV (ms)","Heart Rate Variability (ms)","hrv"],
                    "resting_hr": ["Resting heart rate (bpm)","Resting Heart Rate (bpm)","resting_hr"],
                    "strain": ["Day Strain","Strain","Day strain","strain"],
                    "sleep_performance": ["Sleep performance %","Sleep Performance %","Sleep Performance","sleep_performance"],
                    "sleep_efficiency": ["Sleep efficiency %","Sleep Efficiency %","sleep_efficiency"],
                    "sleep_duration": ["Asleep duration (min)","Total sleep duration (min)","Sleep duration (min)","sleep_duration"],
                    "workout_name": ["Activity name","Activity Name","Sport","workout_name"],
                    "workout_strain": ["Activity Strain","Workout Strain","workout_strain"],
                }
        
                def find_col(cols, candidates):
                    cols_lower = {c.lower(): c for c in cols}
                    for c in candidates:
                        if c in cols:
                            return c
                        if c.lower() in cols_lower:
                            return cols_lower[c.lower()]
                    return None
        
                import_method = st.radio("Import method", ["Upload WHOOP CSVs", "Manual entry"], horizontal=True)
        
                if import_method == "Upload WHOOP CSVs":
                    st.caption("Export from WHOOP app → Profile → App Settings → Export Data (you'll receive a zip with 4 CSVs)")
                    wc1, wc2 = st.columns(2)
                    with wc1:
                        cycles_file = st.file_uploader("📊 cycles.csv — recovery, HRV, RHR, strain", type=["csv"], key="cycles_up")
                        sleep_file = st.file_uploader("😴 sleep.csv — sleep performance and stages", type=["csv"], key="sleep_up")
                    with wc2:
                        workout_file = st.file_uploader("🏋️ workout.csv — workout type and strain", type=["csv"], key="workout_up")
                        st.file_uploader("📓 journal_entries.csv (optional)", type=["csv"], key="journal_up")
        
                    if st.button("💾 Process & Save WHOOP Data", type="primary", use_container_width=True):
                        merged = {}
                        files_processed = 0
        
                        for f, fields in [
                            (cycles_file, ["recovery_score","hrv","resting_hr","strain"]),
                            (sleep_file, ["sleep_performance","sleep_efficiency","sleep_duration"]),
                        ]:
                            if f:
                                try:
                                    df = pd.read_csv(f)
                                    # Show detected columns for debugging
                                    date_col = find_col(df.columns.tolist(), COL_MAP["date"])
                                    if not date_col:
                                        st.warning(f"⚠️ {f.name}: couldn't find date column. Columns found: {', '.join(df.columns.tolist()[:8])}")
                                        continue
                                    dates = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
                                    found_fields = []
                                    for field in fields:
                                        col = find_col(df.columns.tolist(), COL_MAP[field])
                                        if col:
                                            found_fields.append(field)
                                            for d, v in zip(dates, df[col]):
                                                if pd.notna(d) and pd.notna(v):
                                                    try:
                                                        merged.setdefault(d, {})[field] = float(v)
                                                    except:
                                                        merged.setdefault(d, {})[field] = v
                                    st.success(f"✅ {f.name}: {len(df)} rows · fields found: {', '.join(found_fields)}")
                                    files_processed += 1
                                except Exception as e:
                                    st.error(f"❌ {f.name}: {e}")
        
                        if workout_file:
                            try:
                                wdf = pd.read_csv(workout_file)
                                date_col = find_col(wdf.columns.tolist(), COL_MAP["date"])
                                if date_col:
                                    dates = pd.to_datetime(wdf[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
                                    name_col = find_col(wdf.columns.tolist(), COL_MAP["workout_name"])
                                    strain_col = find_col(wdf.columns.tolist(), COL_MAP["workout_strain"])
                                    for i, d in enumerate(dates):
                                        if pd.notna(d):
                                            if name_col:
                                                existing = merged.get(d, {}).get("workout_name","")
                                                new_name = str(wdf[name_col].iloc[i])
                                                merged.setdefault(d, {})["workout_name"] = f"{existing}+{new_name}".strip("+") if existing else new_name
                                            if strain_col:
                                                try:
                                                    merged.setdefault(d, {})["workout_strain"] = float(wdf[strain_col].iloc[i])
                                                except: pass
                                    st.success(f"✅ workout.csv: {len(wdf)} rows processed")
                                    files_processed += 1
                            except Exception as e:
                                st.error(f"❌ workout.csv: {e}")
        
                        if merged:
                            saved_count = 0
                            for d, vals in merged.items():
                                row = {"user_id": user_id, "data_date": d}
                                row.update(vals)
                                if db_upsert("wearable_data", row):
                                    saved_count += 1
                            st.success(f"✅ Saved {saved_count} days of data across {files_processed} file(s).")
                            st.session_state.system_prompt = build_system_prompt(user_id, profile)
                            st.rerun()
                        elif files_processed == 0:
                            st.warning("No files uploaded yet. Upload at least one CSV above.")
        
                else:
                    with st.form("manual_wearable"):
                        wc1, wc2 = st.columns(2)
                        with wc1:
                            w_date = st.date_input("Date", value=date.today())
                            w_recovery = st.number_input("Recovery (%)", 0, 100, 50)
                            w_hrv = st.number_input("HRV (ms)", 0, 200, 40)
                        with wc2:
                            w_sleep = st.number_input("Sleep Performance (%)", 0, 100, 70)
                            w_strain = st.number_input("Strain", 0.0, 21.0, 10.0, step=0.1)
                            w_rhr = st.number_input("Resting HR (bpm)", 30, 120, 65)
                        if st.form_submit_button("💾 Save", type="primary"):
                            db_upsert("wearable_data", {
                                "user_id": user_id, "data_date": w_date.isoformat(),
                                "recovery_score": w_recovery, "hrv": w_hrv,
                                "sleep_performance": w_sleep, "strain": w_strain, "resting_hr": w_rhr
                            })
                            st.success("Saved!")
                            st.rerun()
        
                st.divider()
        
                # ── Wearable trends display ───────────────────────────────────────────────
                wearable_all = db_get("wearable_data", user_id, order_col="data_date")
                if not wearable_all:
                    st.info("No wearable data yet. Upload your WHOOP export above.")
                else:
                    wdf_all = pd.DataFrame(wearable_all)
                    wdf_all["data_date"] = pd.to_datetime(wdf_all["data_date"])
                    wdf_all = wdf_all.sort_values("data_date")
        
                    # Freshness check
                    latest_w_date = wdf_all["data_date"].max().date()
                    w_age = (date.today() - latest_w_date).days
                    if w_age <= 2:
                        st.success(f"✅ Wearable data current — last sync {latest_w_date}")
                    elif w_age <= 7:
                        st.info(f"ℹ️ Last sync {latest_w_date} ({w_age} days ago)")
                    else:
                        st.warning(f"⚠️ Last sync {latest_w_date} ({w_age} days ago) — consider re-importing your WHOOP data")
        
                    # ── Current week vs 30-day average ──────────────────────────────────
                    recent_7 = wdf_all.tail(7)
                    recent_30 = wdf_all.tail(30)
        
                    st.markdown("##### This week vs 30-day average")
                    metrics_w = [
                        ("recovery_score","Recovery %"),
                        ("hrv","HRV ms"),
                        ("resting_hr","RHR bpm"),
                        ("sleep_performance","Sleep %"),
                        ("strain","Strain"),
                    ]
                    available = [(f,l) for f,l in metrics_w if f in wdf_all.columns]
                    if available:
                        wcols = st.columns(len(available))
                        for i, (field, label) in enumerate(available):
                            week_val = pd.to_numeric(recent_7[field], errors="coerce").mean()
                            month_val = pd.to_numeric(recent_30[field], errors="coerce").mean()
                            if not pd.isna(week_val):
                                delta = round(week_val - month_val, 1) if not pd.isna(month_val) else None
                                wcols[i].metric(
                                    label,
                                    f"{week_val:.1f}",
                                    delta=f"{delta:+.1f} vs 30d avg" if delta is not None else None
                                )
        
                    # ── Charts ───────────────────────────────────────────────────────────
                    chart_w1, chart_w2 = st.tabs(["Recovery & HRV", "Sleep & Strain"])
                    with chart_w1:
                        rc_fields = [f for f in ["recovery_score","hrv"] if f in wdf_all.columns]
                        if rc_fields:
                            st.line_chart(wdf_all[["data_date"]+rc_fields].set_index("data_date"))
                    with chart_w2:
                        sl_fields = [f for f in ["sleep_performance","strain"] if f in wdf_all.columns]
                        if sl_fields:
                            st.line_chart(wdf_all[["data_date"]+sl_fields].set_index("data_date"))
        
                    # ── Data management ───────────────────────────────────────────────────
                    st.divider()
                    del1, del2 = st.columns(2)
                    with del1:
                        dates_list = wdf_all["data_date"].dt.strftime("%Y-%m-%d").tolist()
                        del_date = st.selectbox("Delete a specific date", ["— select —"] + list(reversed(dates_list)), key="del_w_date")
                        if del_date != "— select —":
                            if st.button(f"🗑️ Delete {del_date}", key="del_w_btn"):
                                matches = [w for w in wearable_all if w["data_date"] == del_date]
                                for w in matches:
                                    db_delete("wearable_data", w["id"])
                                st.rerun()
                    with del2:
                        if st.button("🗑️ Clear all wearable data", key="clear_w_btn"):
                            for w in wearable_all:
                                db_delete("wearable_data", w["id"])
                            st.rerun()
        
                    # Full table
                    with st.expander("Full data table"):
                        display_cols = ["data_date"] + [f for f,_ in metrics_w if f in wdf_all.columns]
                        st.dataframe(wdf_all[display_cols].sort_values("data_date", ascending=False), use_container_width=True, hide_index=True)
        
                    # Delete by date
                    dates_list = wdf_all["data_date"].dt.strftime("%Y-%m-%d").tolist()
                    del_date = st.selectbox("Delete a specific date", ["-- none --"] + dates_list)
                    if del_date != "-- none --":
                        if st.button(f"🗑️ Delete {del_date}"):
                            match = [w for w in wearable_all if w["data_date"] == del_date]
                            for w in match:
                                db_delete("wearable_data", w["id"])
                            st.rerun()
        


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if "user" not in st.session_state:
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "landing"
    show_auth_screen()
else:
    if "access_token" in st.session_state:
        supabase.postgrest.auth(st.session_state["access_token"])
    user    = st.session_state["user"]
    user_id = user.id
    profile_check        = db_get_single("profiles", user_id)
    onboarding_complete  = profile_check.get("onboarding_complete", False) if profile_check else False
    if not onboarding_complete:
        show_onboarding(user)
    else:
        show_main_app(user)
