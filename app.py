"""
OneSattva — Health, understood.
Streamlit app · Supabase backend · Anthropic Claude Sonnet coach.

Governing principle: bio-individuality. The coach reasons from this person's
actual data through three frameworks (functional medicine, Ayurveda, TCM) —
it never applies population-level defaults, fixed doses, brand lists, or a
28-day cycle assumption. See ONESATTVA_PRODUCT_BRIEF_V2.md.
"""
import streamlit as st
import json, statistics, re
from datetime import date, datetime, timedelta
from supabase import create_client
from anthropic import Anthropic

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="OneSattva", page_icon="◎", layout="wide", initial_sidebar_state="expanded")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ANTHROPIC_KEY = st.secrets["ANTHROPIC_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)
CLAUDE_MODEL = "claude-sonnet-4-6"

MAX_HISTORY = 20

PLAN_MODES = {
    "Reset":     {"duration_days": 30,  "subtitle": "Foundation · 1 month",
                  "desc": "Break a pattern. Build a baseline. Understand your body for the first time. The coach is investigative — high-frequency check-ins, establishing rhythms, calibrating your picture."},
    "Restore":   {"duration_days": 90,  "subtitle": "Active correction · 3 months",
                  "desc": "Address a specific deficit or condition actively. The minimum meaningful intervention window in functional medicine. Labs should reflect measurable change by the end of this mode."},
    "Transform": {"duration_days": 180, "subtitle": "Systemic change · 6 months",
                  "desc": "Multiple systems shifting simultaneously. Sustainable habit formation and deeper pattern resolution. The coach reasons across functional medicine, Ayurveda, and TCM together."},
    "Sustain":   {"duration_days": None, "subtitle": "Long-term partner · 12m+",
                  "desc": "Acute issues resolved. Long-term optimisation and longevity. The coach references years of history. No fixed end — the horizon keeps extending as you evolve."},
}

# ── SVG Mark ──────────────────────────────────────────────────────────────────
def mark_svg(size=46, dark=False):
    outer = "#F7F5F2" if dark else "rgba(17,18,20,0.28)"
    inner = "#B6744A"
    r_vals = [size * 0.47, size * 0.42, size * 0.35, size * 0.30, size * 0.25, size * 0.20]
    cx = size / 2
    rings = ""
    for i, r in enumerate(r_vals):
        color = outer if i < 3 else inner
        rings += f'<circle cx="{cx}" cy="{cx}" r="{r}" fill="none" stroke="{color}" stroke-width="1.5"/>'
    rings += f'<circle cx="{cx}" cy="{cx}" r="{size*0.16}" fill="{inner}"/>'
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">{rings}</svg>'


def wordmark_html(size=19, tag=True, color="#F7F5F2", tag_color="var(--copper)"):
    h = f'<span style="font-family:\'Newsreader\',serif;font-weight:400;font-size:{size}px;letter-spacing:-0.02em;color:{color};line-height:1">OneSattva</span>'
    if tag:
        h += f'<div style="font-family:\'Newsreader\',serif;font-style:italic;font-size:11px;color:{tag_color};margin-top:3px">Health, understood.</div>'
    return h

# ── Global CSS ────────────────────────────────────────────────────────────────
def inject_css(auth_mode=False):
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;1,6..72,300;1,6..72,400&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
:root {{
  --bone:#F7F5F2; --graphite:#111214; --copper:#B6744A; --stone:#E6E3DF;
  --forest:#1F2F2A; --mid:#6B6358; --white:#FFFFFF;
  --line:rgba(17,18,20,0.09); --linem:rgba(17,18,20,0.14);
  --cu-bg:rgba(182,116,74,0.08); --cu-bd:rgba(182,116,74,0.22);
}}
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background-color: {'#111214' if auth_mode else 'var(--bone)'} !important; }}
[data-testid="stSidebar"] {{ background-color: #111214 !important; }}
[data-testid="stSidebar"] * {{ color: #F7F5F2; }}
[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer {{ visibility: hidden; }}

.sl {{ font-size:10px; font-weight:600; letter-spacing:0.09em; text-transform:uppercase; color:var(--mid); margin-top:20px; margin-bottom:9px; }}
.sl.first {{ margin-top:0; }}

.plan-banner {{ background:var(--forest); border-radius:10px; padding:12px 16px; margin-bottom:10px; }}
.pb-ml {{ font-size:10px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:rgba(247,245,242,0.4); }}
.pb-mn {{ font-family:'Newsreader',serif; font-style:italic; font-size:16px; color:#F7F5F2; margin-top:1px; }}
.pb-wk {{ font-size:11px; color:rgba(247,245,242,0.45); font-family:'JetBrains Mono',monospace; }}

.prio-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }}
.prio-card {{ background:var(--white); border:1px solid var(--line); border-radius:12px; padding:14px 15px; height:100%; }}
.triage {{ display:inline-block; font-size:10px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; padding:3px 9px; border-radius:20px; margin-bottom:8px; }}
.t-now   {{ background:rgba(182,116,74,0.10); color:var(--copper); border:1px solid var(--cu-bd); }}
.t-watch {{ background:rgba(230,227,223,0.7); color:#5A5248; border:1px solid var(--stone); }}
.t-bg    {{ background:transparent; color:var(--mid); font-style:italic; padding-left:0; }}
.pc-title {{ font-size:13px; font-weight:500; color:var(--graphite); margin-bottom:4px; }}
.pc-body  {{ font-size:11.5px; color:var(--mid); line-height:1.55; }}

.goal-card {{ background:var(--forest); border-radius:12px; padding:16px 20px; margin-bottom:14px; }}
.gc-lbl {{ font-size:10px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:rgba(247,245,242,0.36); margin-bottom:5px; }}
.gc-goal {{ font-family:'Newsreader',serif; font-style:italic; font-size:15px; color:#F7F5F2; margin-bottom:14px; line-height:1.5; }}
.gc-weeks {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }}
.gc-wk {{ background:rgba(247,245,242,0.06); border-radius:8px; padding:10px; font-size:11.5px; }}
.gc-wkn {{ font-family:'JetBrains Mono',monospace; font-size:10px; color:rgba(247,245,242,0.36); margin-bottom:4px; }}
.gc-wkf {{ color:rgba(247,245,242,0.7); line-height:1.4; }}
.gc-wk.now {{ background:rgba(182,116,74,0.14); border:1px solid rgba(182,116,74,0.2); }}

.snap-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }}
.snap-box  {{ background:var(--white); border:1px solid var(--line); border-radius:10px; padding:13px 14px; }}
.snap-lbl  {{ font-size:10px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:var(--mid); }}
.snap-val  {{ font-family:'JetBrains Mono',monospace; font-size:21px; color:var(--graphite); font-weight:500; }}
.snap-sub  {{ font-size:11px; color:var(--mid); margin-top:3px; }}
.snap-flag {{ color:var(--copper); font-size:11px; margin-top:2px; }}

.trends-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.trend-card  {{ background:var(--white); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }}
.tc-title    {{ font-size:12px; font-weight:500; color:var(--graphite); margin-bottom:3px; }}
.tc-insight  {{ font-size:11.5px; color:var(--mid); line-height:1.5; margin-bottom:10px; }}
.tc-bars     {{ height:40px; background:rgba(230,227,223,0.4); display:flex; align-items:flex-end; padding:0 4px 3px; gap:3px; border-radius:6px; }}
.tb          {{ border-radius:2px 2px 0 0; background:var(--copper); opacity:0.55; flex:1; }}

.insight-box {{ background:var(--forest); border-radius:12px; padding:15px 18px; margin-bottom:14px; }}
.ib-lbl      {{ font-size:10px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:rgba(247,245,242,0.34); margin-bottom:7px; }}
.ib-txt      {{ font-family:'Newsreader',serif; font-style:italic; font-size:14px; color:#F7F5F2; line-height:1.6; }}

.material-flag {{ background:var(--cu-bg); border:1px solid var(--cu-bd); border-radius:10px; padding:14px 18px; margin-bottom:16px; }}
.mf-lbl {{ font-size:10px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:var(--copper); margin-bottom:6px; }}
.mf-txt {{ font-size:13px; color:var(--graphite); line-height:1.55; }}

.sb-name {{ font-size:13px; color:#F7F5F2; font-weight:500; }}
.sb-meta {{ font-size:11px; color:rgba(247,245,242,0.36); margin-top:2px; }}
.plan-pill {{ background:rgba(182,116,74,0.14); border:1px solid rgba(182,116,74,0.26); border-radius:20px; padding:3px 9px; font-size:11px; color:var(--copper); font-family:'JetBrains Mono',monospace; display:inline-flex; margin-top:7px; }}
.sb-foot-t {{ font-size:10.5px; color:rgba(247,245,242,0.2); line-height:1.5; }}

.prof-card {{ background:var(--white); border:1px solid var(--line); border-radius:12px; padding:14px 16px; margin-bottom:12px; }}
.prof-card h4 {{ font-size:10px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:var(--mid); margin-bottom:8px; }}
.pr   {{ display:flex; justify-content:space-between; padding:5px 0; font-size:13px; border-bottom:1px solid rgba(17,18,20,0.04); }}
.pr-k {{ color:var(--mid); }}
.pr-v {{ color:var(--graphite); font-weight:500; }}

.ci-lbl {{ font-size:10px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:var(--mid); margin-bottom:4px; display:block; }}
.ch-hd {{ font-size:10px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:var(--copper); margin-bottom:5px; }}

.whoop-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }}
.wc     {{ background:var(--white); border:1px solid var(--line); border-radius:10px; padding:13px; }}
.wc-lbl {{ font-size:10px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:var(--mid); }}
.wc-val {{ font-family:'JetBrains Mono',monospace; font-size:20px; color:var(--graphite); font-weight:500; }}
.wc-sub {{ font-size:11px; color:var(--mid); margin-top:2px; }}
.wc-d   {{ font-size:11px; color:var(--copper); margin-top:2px; }}

.stTabs [data-baseweb="tab-list"] {{ gap:5px; background:transparent; padding:0; }}
.stTabs [data-baseweb="tab"] {{ border-radius:20px; color:var(--mid); font-weight:500; padding:6px 13px; font-size:12px; border:1.5px solid var(--line); background:transparent; }}
.stTabs [aria-selected="true"] {{ background:var(--graphite)!important; border-color:var(--graphite)!important; color:var(--bone)!important; }}
.stTabs [data-baseweb="tab-border"], .stTabs [data-baseweb="tab-highlight"] {{ display:none; }}

.pg-title {{ font-family:'Newsreader',serif; font-size:23px; color:var(--graphite); font-weight:400; margin-bottom:3px; }}
.pg-sub   {{ font-size:12.5px; color:var(--mid); margin-bottom:20px; line-height:1.5; }}

.cp-banner {{ background:var(--cu-bg); border:1px solid var(--cu-bd); border-radius:10px; padding:12px 16px; margin-bottom:16px; }}

.file-row {{ display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:rgba(230,227,223,0.3); border-radius:8px; font-size:12.5px; margin-bottom:6px; }}
.fn  {{ color:var(--graphite); font-weight:500; }}
.fok {{ color:#3A6B4A; font-size:11px; font-weight:600; }}

.ob-dot {{ width:27px;height:27px;border-radius:50%;border:2px solid var(--linem);background:var(--bone);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;color:var(--mid); }}
.tbl-card {{ background:var(--white); border:1px solid var(--line); border-radius:12px; overflow:hidden; margin-bottom:14px; }}

[data-testid="stForm"] {{ border:none; padding:0; }}
.stButton button {{ border-radius:8px; }}
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, div[data-baseweb="select"] {{ border-radius:8px !important; }}

::-webkit-scrollbar {{ width:6px; }}
::-webkit-scrollbar-thumb {{ background:rgba(17,18,20,0.15); border-radius:3px; }}
</style>
""", unsafe_allow_html=True)

# ── DB Helpers ─────────────────────────────────────────────────────────────────
def db_get(table, user_id, order_col=None, limit=None):
    try:
        q = supabase.table(table).select("*").eq("user_id", user_id)
        if order_col:
            q = q.order(order_col, desc=True)
        if limit:
            q = q.limit(limit)
        return q.execute().data or []
    except Exception:
        return []


def db_get_single(table, user_id):
    """profiles uses id as PK; every other table uses user_id."""
    try:
        key = "id" if table == "profiles" else "user_id"
        res = supabase.table(table).select("*").eq(key, user_id).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def db_upsert(table, data):
    try:
        return supabase.table(table).upsert(data).execute()
    except Exception as e:
        st.error(f"Save error: {e}")
        return None


def db_insert(table, data):
    try:
        return supabase.table(table).insert(data).execute()
    except Exception as e:
        st.error(f"Save error: {e}")
        return None


def db_delete(table, row_id):
    try:
        supabase.table(table).delete().eq("id", row_id).execute()
    except Exception as e:
        st.error(f"Delete error: {e}")

# ── Auth Functions ────────────────────────────────────────────────────────────
def sign_up(email, password, full_name):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password, "options": {"data": {"full_name": full_name}}})
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
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ── Onboarding State ─────────────────────────────────────────────────────────
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

# ── Cycle Calculation — only ever called when has_cycle is True ──────────────
def calculate_cycle_status(user_id):
    cd = db_get_single("cycle_data", user_id)
    if not cd or not cd.get("last_period_start"):
        return None, None, None
    try:
        last_start = datetime.strptime(cd["last_period_start"], "%Y-%m-%d").date()
        avg_len = cd.get("avg_cycle_length")
        if not avg_len:
            return None, None, None
        today = date.today()
        cycle_day = (today - last_start).days + 1
        while cycle_day > avg_len:
            cycle_day -= avg_len
        while cycle_day < 1:
            cycle_day += avg_len
        days_until_next = avg_len - cycle_day + 1
        period_len = cd.get("period_duration", 5) or 5
        follicular_end = round(avg_len * 0.5)
        ovulation_end = follicular_end + 3
        if cycle_day <= period_len:
            phase = f"Menstruation (Day 1–{period_len})"
        elif cycle_day <= follicular_end:
            phase = f"Follicular (Day {period_len+1}–{follicular_end})"
        elif cycle_day <= ovulation_end:
            phase = f"Ovulation (Day {follicular_end+1}–{ovulation_end})"
        else:
            phase = f"Luteal (Day {ovulation_end+1}–{avg_len})"
        return cycle_day, phase, days_until_next
    except Exception:
        return None, None, None

# ── WHOOP CSV helpers ──────────────────────────────────────────────────────────
COL_MAP = {
    "date": ["Cycle start time", "Cycle Start Time", "Wake onset", "Date", "date"],
    "recovery_score": ["Recovery score %", "Recovery Score %", "Recovery Score", "recovery_score"],
    "hrv": ["Heart rate variability (ms)", "HRV (ms)", "Heart Rate Variability (ms)", "hrv"],
    "resting_hr": ["Resting heart rate (bpm)", "Resting Heart Rate (bpm)", "resting_hr"],
    "strain": ["Day Strain", "Strain", "Day strain", "strain"],
    "sleep_performance": ["Sleep performance %", "Sleep Performance %", "Sleep Performance", "sleep_performance"],
    "sleep_efficiency": ["Sleep efficiency %", "Sleep Efficiency %", "sleep_efficiency"],
    "sleep_duration": ["Asleep duration (min)", "Total sleep duration (min)", "Sleep duration (min)", "sleep_duration"],
    "workout_name": ["Activity name", "Activity Name", "Sport", "workout_name"],
    "workout_strain": ["Activity Strain", "Workout Strain", "workout_strain"],
}


def find_col(cols, candidates):
    cols_lower = {c.lower(): c for c in cols}
    for c in candidates:
        if c in cols:
            return c
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None

# ── AI Helpers ────────────────────────────────────────────────────────────────
def ai_generate(system_prompt, user_prompt, max_tokens=4096):
    try:
        resp = anthropic_client.messages.create(
            model=CLAUDE_MODEL, max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"_Coach is temporarily unavailable: {e}_"


def ai_chat(system_prompt, messages, max_tokens=4096):
    try:
        resp = anthropic_client.messages.create(
            model=CLAUDE_MODEL, max_tokens=max_tokens,
            system=system_prompt,
            messages=messages[-MAX_HISTORY:],
        )
        return resp.content[0].text
    except Exception as e:
        return f"_Coach is temporarily unavailable: {e}_"

# ── System Prompt Builder — bio-individual: no hard-coded clinical rules ──────
# NOTE ON A CONFLICT BETWEEN THE TWO BRIEFS:
# BACKEND_REFERENCE.py's original build_system_prompt() hard-codes "favour cooked,
# never raw salads", a fixed India supplement-brand list, and India as a default
# location. ONESATTVA_PRODUCT_BRIEF_V2.md Sections 2, 3, 9, 10 and 13 explicitly
# forbid exactly this — bio-individuality means the coach must derive food and
# brand guidance from THIS person's gut data, location and labs, not from a
# population template baked into the prompt. Per the brief's own resolution rule
# ("if anything conflicts, the product brief wins"), this rewrite drops every
# hard-coded rule and instead gives the coach the patient's data plus the three
# reasoning frameworks, and tells it explicitly to use the patient's own
# location/labs/gut history to reach brand- and food-specific conclusions.
def build_system_prompt(user_id, profile, has_cycle=False):
    today = date.today()
    ninety_days_ago = today - timedelta(days=90)
    one_eighty_days_ago = today - timedelta(days=180)

    base = f"""You are OneSattva — a senior integrative medicine practitioner, functional nutritionist, and personal wellness coach. Today's date is {today.strftime("%A, %d %B %Y")}.

═══════════════════════════════════════════════════════
GOVERNING PRINCIPLE — BIO-INDIVIDUALITY
═══════════════════════════════════════════════════════
There is no universal rule for what this person should eat, supplement, or do. The right answer emerges only from THEIR data below — labs, check-ins, wearable trends, history, goals, location. You do not apply population defaults, fixed doses, brand lists, or templates. You reason from this individual's data to the individual answer, and you state the reasoning, not just the conclusion. If their gut data shows no issue, raw food may be exactly right for them; if it shows bloating and poor digestion, cooked food may be right — but only their data tells you which. Never assume a 28-day menstrual cycle. Never assume a location-specific brand list — derive brand and food suggestions from their actual location and what is realistically available there, asking if location is unclear.

═══════════════════════════════════════════════════════
NON-NEGOTIABLE RULES
═══════════════════════════════════════════════════════
RULE 1 — Always finish the response. Never cut off mid-sentence or mid-table.
RULE 2 — You are the expert. If their current routine works against their goals, say so directly, and say what to change. State non-negotiables with the mechanism. A plan contains changes, not a repackaging of what they already do.
RULE 3 — Data anomaly protocol: if a data point is unusual or contradicts trend, flag it and ask one specific clarifying question before recommending from it.
RULE 4 — Data freshness: labs ≤90 days = current/primary reference; 91-180 days = recent/trend only; >180 days = historical context only, flag explicitly that a retest is needed. Wearable data: last 7 days = current state; last 30 days = recent pattern; beyond 90 days = trend only. Check-ins: last 14 days inform current recommendations.
RULE 5 — Gap detection: 3-7 day check-in gap — note it, continue. 7-14 days — ask "It's been [X] days since your last log. Has anything changed?" before recommending. 14+ days — do not continue the old protocol; get a re-entry note first.
RULE 6 — Be specific when the data supports it: exact dose, exact timing, exact food, brand only if you know their location and it's genuinely the best available option there — never invent specificity the data doesn't support.
RULE 7 — Never deflect to "ask your doctor" without giving a complete expert answer first.

═══════════════════════════════════════════════════════
THREE FRAMEWORKS — READ SIMULTANEOUSLY, FIND THE CONVERGENCE
═══════════════════════════════════════════════════════
FUNCTIONAL MEDICINE — root cause, lab interpretation against functional (optimal) ranges not conventional population ranges, HPA axis, gut-brain-thyroid axis, microbiome, order of operations (gut before hormones, HPA before sleep supplements).
AYURVEDA — Prakriti (constitution), Agni (digestive fire — assess from check-in bloating/digestion/post-meal energy before any food recommendation), Dinacharya (daily rhythm), Ojas (the endpoint state protocols build toward).
TCM — organ system patterns (Liver Qi stagnation, Kidney Yang deficiency, Spleen Qi deficiency), Qi and Blood as functional currency, the 24-hour organ clock for supplement/activity timing, Five Element clustering.
Do not answer framework-by-framework. Find where they converge — that convergence is the most robust recommendation.

For complex questions, structure as: (1) what is happening — mechanism across frameworks, (2) what it means for this person specifically — cite their actual data, (3) the specific recommendation with rationale, (4) realistic timeline, (5) what to watch for.

"""

    if profile:
        name = profile.get("full_name", "the patient")
        base += "═══════════════════════════════════════════════════════\nPATIENT PROFILE\n═══════════════════════════════════════════════════════\n"
        base += f"Name: {name}"
        if profile.get("dob"):
            try:
                dob = date.fromisoformat(profile["dob"])
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                base += f" | Age: {age}"
            except Exception:
                pass
        if profile.get("sex"): base += f" | Sex: {profile['sex']}"
        if profile.get("height_cm") and profile.get("weight_kg"):
            base += f" | {profile['height_cm']}cm · {profile['weight_kg']}kg"
        if profile.get("location"): base += f" | Location: {profile['location']}"
        if profile.get("blood_group"): base += f" | Blood group: {profile['blood_group']}"
        if profile.get("eating_pattern"): base += f"\nEating pattern: {profile['eating_pattern']}"
        if profile.get("allergies"): base += f" | Allergies/intolerances: {profile['allergies']}"
        if profile.get("occupation"): base += f"\nOccupation: {profile['occupation']}"
        base += "\n"

    goals = db_get("goals", user_id)
    if goals:
        base += "\nGOALS:\n"
        for g in goals:
            tf = f" [{g['timeframe']}]" if g.get("timeframe") else ""
            base += f"- {g['goal']}{tf}\n"

    conditions = db_get("medical_history", user_id)
    if conditions:
        base += "\nMEDICAL CONDITIONS:\n"
        for c in conditions:
            base += f"- {c.get('condition','')}: {c.get('notes','')}\n"

    meds = db_get("medications", user_id)
    active_meds = [m for m in meds if m.get("active", True)] if meds else []
    if active_meds:
        base += "\nCURRENT MEDICATIONS:\n"
        for m in active_meds:
            base += f"- {m.get('name','')} {m.get('dose','')} {m.get('frequency','')}\n"

    supps = db_get("supplements", user_id)
    active_supps = [s for s in supps if s.get("active", True)] if supps else []
    if active_supps:
        base += "\nCURRENT SUPPLEMENTS:\n"
        for s in active_supps:
            base += f"- {s.get('name','')} {s.get('dose','')} ({s.get('timing','')})\n"

    notes = db_get_single("profile_notes", user_id)
    if notes and notes.get("notes"):
        base += f"\nLIFESTYLE / PROFILE NOTES:\n{notes['notes']}\n"

    labs = db_get("lab_reports", user_id, order_col="report_date", limit=10)
    if labs:
        base += "\n═══════════════════════════════════════════════════════\nLAB REPORTS\n═══════════════════════════════════════════════════════\n"
        current_labs, recent_labs, historical_labs = [], [], []
        for l in labs:
            try:
                rep_date = date.fromisoformat(l.get("report_date", ""))
                if rep_date >= ninety_days_ago:
                    current_labs.append(l)
                elif rep_date >= one_eighty_days_ago:
                    recent_labs.append(l)
                else:
                    historical_labs.append(l)
            except Exception:
                historical_labs.append(l)
        if current_labs:
            base += "CURRENT (≤90 days — primary reference):\n"
            for l in current_labs:
                base += f"- {l.get('report_date','')}: {l.get('summary','')} | Raw: {str(l.get('raw_values',''))[:400]}\n"
        else:
            base += "⚠️ NO CURRENT LABS. Flag this to the patient explicitly — do not treat older values as current status.\n"
        if recent_labs:
            base += "RECENT (91-180 days — trend only):\n"
            for l in recent_labs:
                base += f"- {l.get('report_date','')}: {l.get('summary','')}\n"
        if historical_labs:
            base += "HISTORICAL (>180 days — context only, retest needed):\n"
            for l in historical_labs:
                base += f"- {l.get('report_date','')}: {l.get('summary','')}\n"
    else:
        base += "\n⚠️ NO LAB REPORTS UPLOADED. Recommendations are provisional/general until labs are provided — say this plainly.\n"

    wearable_all = db_get("wearable_data", user_id, order_col="data_date", limit=90)
    if wearable_all:
        base += "\n═══════════════════════════════════════════════════════\nWEARABLE DATA\n═══════════════════════════════════════════════════════\n"
        seven_days_ago, thirty_days_ago = today - timedelta(days=7), today - timedelta(days=30)
        current_w, recent_w = [], []
        for w in wearable_all:
            try:
                wd = date.fromisoformat(w.get("data_date", ""))
                if wd >= seven_days_ago: current_w.append(w)
                elif wd >= thirty_days_ago: recent_w.append(w)
            except Exception:
                pass

        def fmt_wearable(w):
            parts = [w.get("data_date", "")]
            for f in ["recovery_score", "hrv", "resting_hr", "strain", "sleep_performance"]:
                if w.get(f) is not None: parts.append(f"{f.replace('_',' ')}: {w[f]}")
            return " | ".join(parts)

        if current_w:
            base += "CURRENT (last 7 days):\n" + "\n".join(f"- {fmt_wearable(w)}" for w in reversed(current_w)) + "\n"
        if recent_w:
            def avg_field(rows, field):
                vals = [float(r[field]) for r in rows if r.get(field) is not None]
                return round(statistics.mean(vals), 1) if vals else None
            r_avg = {f: avg_field(recent_w, f) for f in ["recovery_score", "hrv", "resting_hr", "strain", "sleep_performance"]}
            r_str = " | ".join(f"{k.replace('_',' ')}: {v}" for k, v in r_avg.items() if v is not None)
            base += f"RECENT 30-DAY AVERAGE ({len(recent_w)} days of data): {r_str}\n"
        if not current_w and not recent_w:
            base += "⚠️ No recent wearable data.\n"

    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=14)
    if checkins:
        latest_date_str = checkins[0].get("checkin_date", "")
        try:
            gap_days = (today - date.fromisoformat(latest_date_str)).days
        except Exception:
            gap_days = 0
        base += "\n═══════════════════════════════════════════════════════\nCHECK-IN DATA\n═══════════════════════════════════════════════════════\n"
        if gap_days >= 14:
            base += f"⚠️ GAP ALERT: {gap_days} days since last check-in. Do NOT continue the old protocol. Ask a re-entry question first.\n"
        elif gap_days >= 7:
            base += f"⚠️ {gap_days}-day check-in gap. Ask one re-calibration question before recommending.\n"
        elif gap_days >= 3:
            base += f"Note: {gap_days}-day gap. Continue but note it.\n"
        base += "RECENT CHECK-INS (last 14 days):\n"
        for c in reversed(checkins[:14]):
            base += (f"- {c.get('checkin_date','')}: Energy {c.get('energy','?')}/10 · Clarity {c.get('mental_clarity','?')}/10 · "
                     f"Sleep quality {c.get('sleep_quality','?')}/10 ({c.get('sleep_hours','?')}hrs) · Mood {c.get('mood','?')}/10 · "
                     f"Gut {c.get('gut','?')} · Libido {c.get('libido','?')} · Workout: {c.get('workout','?')} · Notes: {c.get('notes','')}\n")
    else:
        base += "\nNo check-in data yet.\n"

    if has_cycle:
        cycle_day, phase, days_until_next = calculate_cycle_status(user_id)
        cd = db_get_single("cycle_data", user_id)
        if cd:
            base += "\n═══════════════════════════════════════════════════════\nCYCLE DATA\n═══════════════════════════════════════════════════════\n"
            base += f"Last period start: {cd.get('last_period_start','?')} | Actual average cycle length: {cd.get('avg_cycle_length','?')} days (never assume 28)\n"
            if cycle_day:
                base += f"Current cycle day: {cycle_day} | Phase: {phase} | Days until next period: {days_until_next}\n"

    roadmap = db_get_single("roadmaps", user_id)
    if roadmap and roadmap.get("committed"):
        base += "\n═══════════════════════════════════════════════════════\nCOMMITTED ROADMAP\n═══════════════════════════════════════════════════════\n"
        base += f"Plan mode: {roadmap.get('plan_mode','?')} | Committed: {roadmap.get('generated_at','?')}\n"
        base += (roadmap.get("roadmap_text", "") or "")[:3000] + "\n"

    return base
# ── Auth Screen ───────────────────────────────────────────────────────────────
def show_auth():
    inject_css(auth_mode=True)
    mode = st.session_state.get("auth_mode", "login")

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown('<div style="height:48px"></div>', unsafe_allow_html=True)
        with st.container(border=False):
            st.markdown(f"""
<div style="background:var(--bone);border-radius:18px;padding:44px;box-shadow:0 8px 48px rgba(17,18,20,0.18)">
<div style="display:flex;flex-direction:column;align-items:center;margin-bottom:28px;gap:8px">
{mark_svg(44 if mode=='login' else 36)}
<span style="font-family:'Newsreader',serif;font-weight:400;font-size:{26 if mode=='login' else 22}px;letter-spacing:-0.02em;color:#111214;line-height:1">OneSattva</span>
<div style="font-family:'Newsreader',serif;font-style:italic;font-size:12.5px;color:var(--copper)">Health, understood.</div>
</div>
""", unsafe_allow_html=True)

            if mode == "login":
                with st.form("login_form", border=False):
                    email = st.text_input("Email", placeholder="your@email.com")
                    pw = st.text_input("Password", type="password", placeholder="••••••••")
                    submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")
                if submitted:
                    if not email or not pw:
                        st.error("Enter your email and password.")
                    else:
                        user, session, err = sign_in(email, pw)
                        if err:
                            st.error("Couldn't sign in — check your email and password.")
                        else:
                            st.session_state.user_id = user.id
                            st.session_state.user_email = user.email
                            st.rerun()
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Forgot password?", use_container_width=False, key="forgot_link"):
                        st.session_state.auth_mode = "reset"
                        st.rerun()
                st.markdown('<div style="text-align:center;margin-top:8px;font-size:12.5px;color:var(--mid)">New to OneSattva?</div>', unsafe_allow_html=True)
                if st.button("Create an account →", use_container_width=True, key="to_signup"):
                    st.session_state.auth_mode = "signup"
                    st.rerun()

            elif mode == "signup":
                with st.form("signup_form", border=False):
                    c1, c2 = st.columns(2)
                    first = c1.text_input("First name", placeholder="Arjun")
                    last = c2.text_input("Last name", placeholder="Mehta")
                    email = st.text_input("Email", placeholder="arjun@email.com")
                    pw = st.text_input("Create password", type="password", placeholder="Min. 8 characters")
                    st.markdown('<div style="border-top:1px solid var(--line);margin:6px 0 10px"></div>', unsafe_allow_html=True)
                    consent1 = st.checkbox("I agree to the Terms of Service and Privacy Policy")
                    consent2 = st.checkbox("I explicitly consent to OneSattva collecting, storing, and processing my personal health data — including lab results, wearable data, and symptom logs — solely for personalised health coaching.")
                    submitted = st.form_submit_button("Create account →", use_container_width=True, type="primary")
                if submitted:
                    if not (first and last and email and pw):
                        st.error("Please fill in every field.")
                    elif len(pw) < 8:
                        st.error("Password must be at least 8 characters.")
                    elif not (consent1 and consent2):
                        st.error("Both consents are required to create an account.")
                    else:
                        full_name = f"{first} {last}"
                        user, err = sign_up(email, pw, full_name)
                        if err:
                            st.error(f"Couldn't create account: {err}")
                        else:
                            db_upsert("profiles", {"id": user.id, "full_name": full_name, "email": email, "onboarding_complete": False})
                            st.success("Account created. Please sign in.")
                            st.session_state.auth_mode = "login"
                            st.rerun()
                st.markdown('<div style="text-align:center;margin-top:8px;font-size:12.5px;color:var(--mid)">Already have an account?</div>', unsafe_allow_html=True)
                if st.button("Sign in", use_container_width=True, key="to_login"):
                    st.session_state.auth_mode = "login"
                    st.rerun()

            else:  # reset
                st.markdown('<div style="font-size:13px;color:var(--mid);margin-bottom:14px">Enter your email and we\'ll send a reset link.</div>', unsafe_allow_html=True)
                with st.form("reset_form", border=False):
                    email = st.text_input("Email", placeholder="your@email.com")
                    submitted = st.form_submit_button("Send reset link", use_container_width=True, type="primary")
                if submitted and email:
                    try:
                        supabase.auth.reset_password_email(email, {"redirect_to": "https://wellness-coach-app-f2ssjkdxdey8vm2c287mnz.streamlit.app"})
                        st.success("If that email exists, a reset link is on its way.")
                    except Exception as e:
                        st.error(f"Couldn't send reset link: {e}")
                if st.button("← Back to sign in", key="back_to_login"):
                    st.session_state.auth_mode = "login"
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

# ── Onboarding progress header ────────────────────────────────────────────────
ONBOARDING_STEPS = ["About you", "Health history", "Lifestyle & goals", "Labs", "Coach analysis", "Plan mode", "Review & commit"]


def onboarding_progress(current_step):
    cols = st.columns(len(ONBOARDING_STEPS))
    for i, (col, label) in enumerate(zip(cols, ONBOARDING_STEPS), start=1):
        with col:
            if i < current_step:
                dot_style = "background:var(--forest);border-color:var(--forest);color:#fff"
                txt = "✓"
            elif i == current_step:
                dot_style = "background:var(--graphite);border-color:var(--graphite);color:var(--bone)"
                txt = str(i)
            else:
                dot_style = ""
                txt = str(i)
            lbl_color = "var(--graphite);font-weight:500" if i == current_step else "var(--mid)"
            st.markdown(f"""
<div style="text-align:center">
<div class="ob-dot" style="{dot_style};margin:0 auto 4px">{txt}</div>
<div style="font-size:10.5px;color:{lbl_color};white-space:nowrap">{label}</div>
</div>""", unsafe_allow_html=True)
    st.markdown('<div style="border-bottom:1px solid var(--line);margin:16px 0 22px"></div>', unsafe_allow_html=True)
# ── Onboarding ────────────────────────────────────────────────────────────────
def show_onboarding(user_id, profile):
    inject_css(auth_mode=False)
    step = st.session_state.get("ob_step", 1)
    st.markdown('<div style="max-width:820px;margin:0 auto;padding-top:18px">', unsafe_allow_html=True)
    onboarding_progress(step)

    if step == 1:
        onboarding_step1(user_id, profile)
    elif step == 2:
        onboarding_step2(user_id)
    elif step == 3:
        onboarding_step3(user_id)
    elif step == 4:
        onboarding_step4(user_id)
    elif step == 5:
        onboarding_step5(user_id, profile)
    elif step == 6:
        onboarding_step6(user_id)
    elif step == 7:
        onboarding_step7(user_id, profile)

    st.markdown("</div>", unsafe_allow_html=True)


def ob_nav(back_step=None, back_label="← Back", continue_label="Continue →", on_continue=None, continue_disabled=False):
    c1, c2 = st.columns([1, 1])
    with c1:
        if back_step:
            if st.button(back_label, key=f"back_{back_step}"):
                st.session_state.ob_step = back_step
                st.rerun()
    with c2:
        st.markdown('<div style="text-align:right">', unsafe_allow_html=True)
        clicked = st.button(continue_label, type="primary", disabled=continue_disabled, key=f"cont_{back_step}")
        st.markdown('</div>', unsafe_allow_html=True)
        if clicked and on_continue:
            on_continue()


# ── Step 1 — About you ─────────────────────────────────────────────────────
def onboarding_step1(user_id, profile):
    st.markdown('<div class="pg-title">Tell us about yourself</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">This personalises everything. You can edit any of this from Profile & Data later.</div>', unsafe_allow_html=True)

    p = profile or {}
    c1, c2 = st.columns(2)
    with c1:
        dob = st.date_input("Date of birth", value=date.fromisoformat(p["dob"]) if p.get("dob") else date(1990, 1, 1), min_value=date(1920, 1, 1), max_value=date.today())
        location = st.text_input("Location (city, country)", value=p.get("location", ""))
        height_cm = st.number_input("Height (cm)", min_value=100, max_value=230, value=int(p.get("height_cm") or 170))
        weight_kg = st.number_input("Weight (kg)", min_value=30, max_value=250, value=int(p.get("weight_kg") or 70))
    with c2:
        sex = st.selectbox("Biological sex", ["Male", "Female", "Intersex", "Prefer not to say"], index=["Male", "Female", "Intersex", "Prefer not to say"].index(p.get("sex")) if p.get("sex") in ["Male", "Female", "Intersex", "Prefer not to say"] else 0)
        blood_group = st.text_input("Blood group (optional)", value=p.get("blood_group", ""))
        eating_pattern = st.selectbox("Eating pattern", ["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"], index=["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"].index(p.get("eating_pattern")) if p.get("eating_pattern") in ["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"] else 0)
        occupation = st.text_input("Occupation (optional)", value=p.get("occupation", ""))

    has_cycle = None
    if sex in ("Female", "Intersex"):
        st.markdown('<div class="sl">Cycle tracking</div>', unsafe_allow_html=True)
        cycle_answer = st.radio("Do you currently have a menstrual cycle to track?", ["Yes", "No", "Not sure"], horizontal=True,
                                 index={"Yes": 0, "No": 1, "Not sure": 2}.get(st.session_state.get("ob_cycle_answer"), None))
        has_cycle = cycle_answer == "Yes"
        st.session_state.ob_cycle_answer = cycle_answer
        if has_cycle:
            st.caption("You'll enter your last period start date and actual average cycle length in the next steps.")
        else:
            st.caption("No cycle-related UI, prompts, or coaching will be shown anywhere in the app. You can change this later in Profile & Data.")

    def go_next():
        db_upsert("profiles", {
            "id": user_id, "dob": dob.isoformat(), "location": location,
            "height_cm": height_cm, "weight_kg": weight_kg, "sex": sex,
            "blood_group": blood_group, "eating_pattern": eating_pattern, "occupation": occupation,
            "has_cycle": bool(has_cycle) if has_cycle is not None else False,
            "full_name": p.get("full_name") or st.session_state.get("user_email", ""),
        })
        st.session_state.ob_step = 2
        st.rerun()

    ob_nav(back_step=None, on_continue=go_next)


# ── Step 2 — Health history ───────────────────────────────────────────────
def onboarding_step2(user_id):
    st.markdown('<div class="pg-title">Your health history</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Nothing here is mandatory — skip anything you\'re unsure about. More context means more precise coaching.</div>', unsafe_allow_html=True)

    for key, label, cols in [("ob_conditions", "Diagnosed conditions", ["Condition", "Since / notes"]),
                              ("ob_meds", "Current medications", ["Medication", "Dose", "Timing"]),
                              ("ob_supps", "Current supplements", ["Supplement", "Dose", "Timing"])]:
        if key not in st.session_state:
            st.session_state[key] = [{c: "" for c in cols}]
        st.markdown(f'<div class="sl">{label}</div>', unsafe_allow_html=True)
        for i, row in enumerate(st.session_state[key]):
            rcols = st.columns(len(cols))
            for j, c in enumerate(cols):
                row[c] = rcols[j].text_input(c, value=row.get(c, ""), key=f"{key}_{i}_{j}", label_visibility="collapsed" if i > 0 else "visible", placeholder=c)
        if st.button(f"+ Add another", key=f"add_{key}"):
            st.session_state[key].append({c: "" for c in cols})
            st.rerun()

    c1, c2 = st.columns(2)
    family_history = c1.text_area("Family history (optional)", value=st.session_state.get("ob_family_history", ""))
    surgeries = c2.text_area("Past surgeries or significant events (optional)", value=st.session_state.get("ob_surgeries", ""))

    def go_next():
        st.session_state.ob_family_history = family_history
        st.session_state.ob_surgeries = surgeries
        for row in st.session_state.ob_conditions:
            if row.get("Condition", "").strip():
                db_insert("medical_history", {"user_id": user_id, "condition": row["Condition"], "notes": row.get("Since / notes", "")})
        for row in st.session_state.ob_meds:
            if row.get("Medication", "").strip():
                db_insert("medications", {"user_id": user_id, "name": row["Medication"], "dose": row.get("Dose", ""), "frequency": row.get("Timing", ""), "active": True})
        for row in st.session_state.ob_supps:
            if row.get("Supplement", "").strip():
                db_insert("supplements", {"user_id": user_id, "name": row["Supplement"], "dose": row.get("Dose", ""), "timing": row.get("Timing", ""), "active": True})
        notes_text = f"Family history: {family_history}\nPast surgeries/events: {surgeries}" if (family_history or surgeries) else ""
        if notes_text:
            existing = db_get_single("profile_notes", user_id)
            combined = (existing.get("notes", "") + "\n\n" if existing else "") + notes_text
            db_upsert("profile_notes", {"user_id": user_id, "notes": combined})
        st.session_state.ob_step = 3
        st.rerun()

    ob_nav(back_step=1, on_continue=go_next)


# ── Step 3 — Lifestyle and goals ──────────────────────────────────────────
def onboarding_step3(user_id):
    st.markdown('<div class="pg-title">Your lifestyle and goals</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">The more specific you are here, the more precisely the coach can build your protocol.</div>', unsafe_allow_html=True)

    primary_goal = st.text_area("Primary health goal — in your own words", value=st.session_state.get("ob_primary_goal", ""), height=80)

    st.markdown('<div class="sl">Diet & activity</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    activity_level = c1.selectbox("Activity level", ["Sedentary", "Lightly active", "Moderately active", "Very active"])
    restrictions = c2.text_input("Dietary restrictions or intolerances", value="")
    alcohol = c1.selectbox("Alcohol consumption", ["None", "Occasionally (1–2×/week)", "Regularly (3+/week)"])
    smoking = c2.selectbox("Smoking / tobacco", ["Non-smoker", "Former smoker", "Occasional (social)", "Regular smoker", "Vaping / e-cigarettes"])
    exercise_routine = st.text_area("Exercise routine", height=60)

    st.markdown('<div class="sl">Sleep</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    bedtime = c1.text_input("Typical bedtime", placeholder="11:00 pm")
    wake_time = c2.text_input("Typical wake time", placeholder="6:30 am")
    sleep_duration = c3.text_input("Average sleep duration", placeholder="6.5 hrs")
    sleep_quality = st.slider("Sleep quality (self-rated)", 1, 10, 5)
    sleep_challenges = st.text_area("Sleep challenges (optional)", height=50)

    st.markdown('<div class="sl">Eating schedule</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    first_meal = c1.text_input("First meal time", placeholder="8:00 am")
    last_meal = c2.text_input("Last meal time", placeholder="8:30 pm")
    meals_per_day = c1.selectbox("Meals per day", ["2 meals", "3 meals", "3 meals + snacks", "Intermittent fasting"])
    eating_out = c2.selectbox("Eating out frequency", ["Rarely", "2–3× per week", "4–5× per week", "Daily"])
    food_prefs = st.text_area("Food preferences or patterns the coach should know about (optional)", height=60)

    st.markdown('<div class="sl">Stress & wellbeing</div>', unsafe_allow_html=True)
    stress_level = st.slider("Current stress level", 1, 10, 5)
    stressors = st.text_input("Primary stressors")
    symptoms = st.text_area("Current symptoms or main concerns — in your own words", height=70)
    anything_else = st.text_area("Anything else you'd like your coach to know (optional)", height=50)

    st.markdown('<div class="sl">Additional goals</div>', unsafe_allow_html=True)
    if "ob_extra_goals" not in st.session_state:
        st.session_state.ob_extra_goals = []
    for i, g in enumerate(st.session_state.ob_extra_goals):
        gc1, gc2 = st.columns([3, 1])
        g["goal"] = gc1.text_input("Goal", value=g.get("goal", ""), key=f"eg_{i}", label_visibility="collapsed")
        g["timeframe"] = gc2.selectbox("Timeframe", ["1 month", "3 months", "6 months", "Ongoing"], key=f"egt_{i}", label_visibility="collapsed")
    if st.button("+ Add goal"):
        st.session_state.ob_extra_goals.append({"goal": "", "timeframe": "3 months"})
        st.rerun()

    profile_row = db_get_single("profiles", user_id) or {}
    has_cycle = profile_row.get("has_cycle", False)
    cycle_last_start, cycle_avg_len, cycle_period_dur = None, None, None
    if has_cycle:
        st.markdown('<div class="sl">Cycle data</div>', unsafe_allow_html=True)
        st.caption("Your actual average cycle length — never assumed as 28 days.")
        c1, c2, c3 = st.columns(3)
        cycle_last_start = c1.date_input("Last period start date", value=date.today())
        cycle_avg_len = c2.number_input("Actual average cycle length (days)", min_value=15, max_value=60, value=28)
        cycle_period_dur = c3.number_input("Typical period duration (days, optional)", min_value=1, max_value=15, value=5)

    def go_next():
        st.session_state.ob_primary_goal = primary_goal
        if primary_goal.strip():
            existing_goals = db_get("goals", user_id)
            if not any(g.get("goal") == primary_goal for g in existing_goals):
                db_insert("goals", {"user_id": user_id, "goal": primary_goal, "timeframe": "Primary"})
        for g in st.session_state.ob_extra_goals:
            if g.get("goal", "").strip():
                db_insert("goals", {"user_id": user_id, "goal": g["goal"], "timeframe": g.get("timeframe", "")})
        lifestyle_notes = f"""
Activity level: {activity_level} | Dietary restrictions: {restrictions} | Alcohol: {alcohol} | Smoking: {smoking}
Exercise routine: {exercise_routine}
Sleep: bedtime {bedtime}, wake {wake_time}, duration {sleep_duration}, quality {sleep_quality}/10. Challenges: {sleep_challenges}
Eating schedule: first meal {first_meal}, last meal {last_meal}, {meals_per_day}, eating out {eating_out}. Preferences: {food_prefs}
Stress level: {stress_level}/10. Stressors: {stressors}
Current symptoms: {symptoms}
Other notes: {anything_else}
""".strip()
        existing = db_get_single("profile_notes", user_id)
        combined = (existing.get("notes", "") + "\n\n" if existing else "") + lifestyle_notes
        db_upsert("profile_notes", {"user_id": user_id, "notes": combined})
        if has_cycle and cycle_last_start and cycle_avg_len:
            db_upsert("cycle_data", {"user_id": user_id, "last_period_start": cycle_last_start.isoformat(),
                                      "avg_cycle_length": int(cycle_avg_len), "period_duration": int(cycle_period_dur or 5)})
        st.session_state.ob_step = 4
        st.rerun()

    ob_nav(back_step=2, on_continue=go_next)


# ── Step 4 — Labs ──────────────────────────────────────────────────────────
def onboarding_step4(user_id):
    st.markdown('<div class="pg-title">Your labs</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Labs are not optional — they\'re the foundation of a precise assessment. We need them to give you specific guidance rather than general recommendations. You have 7 days to upload your first report — your plan recommendation will be provisional until then.</div>', unsafe_allow_html=True)

    if "ob_recommended_panel" not in st.session_state:
        conditions = ", ".join(r.get("Condition", "") for r in st.session_state.get("ob_conditions", []) if r.get("Condition"))
        goal = st.session_state.get("ob_primary_goal", "")
        prompt = f"Patient's stated conditions: {conditions or 'none stated'}. Primary goal: {goal or 'not yet stated'}. Suggest the 12-20 most clinically relevant lab markers for this specific person to test first, grouped by category, in a short markdown table. Be specific to their picture — not a generic panel."
        with st.spinner("Coach is selecting the most relevant markers for you..."):
            st.session_state.ob_recommended_panel = ai_generate(
                "You are OneSattva, a functional medicine practitioner selecting a lab panel for a specific new patient based on what little is known so far.",
                prompt, max_tokens=1200)
    st.markdown(st.session_state.ob_recommended_panel)

    with st.expander("Paste your lab values"):
        report_date = st.date_input("Report date", value=date.today())
        raw_values = st.text_area("Paste values (marker: value, one per line, or freeform)", height=160)
        if st.button("Analyse and save"):
            if raw_values.strip():
                with st.spinner("Interpreting against functional ranges..."):
                    summary = ai_generate(
                        "You are OneSattva, interpreting lab values against functional (optimal) ranges, not conventional population reference ranges. Give a concise 2-4 sentence clinical summary.",
                        raw_values, max_tokens=500)
                db_insert("lab_reports", {"user_id": user_id, "report_date": report_date.isoformat(), "raw_values": raw_values, "summary": summary})
                st.session_state.ob_labs_uploaded = True
                st.success("Lab report saved and interpreted.")

    skipped = not st.session_state.get("ob_labs_uploaded", False)
    if skipped:
        st.caption("No labs yet — that's fine. You have 7 days. Your assessment will be marked provisional until labs are in.")

    def go_next():
        st.session_state.ob_step = 5
        st.rerun()

    ob_nav(back_step=3, on_continue=go_next)


# ── Step 5 — Coach analysis ───────────────────────────────────────────────
def onboarding_step5(user_id, profile):
    st.markdown('<div class="pg-title">Your coach\'s first read</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Using everything you\'ve shared, here\'s what OneSattva sees so far — and which plan mode it recommends.</div>', unsafe_allow_html=True)

    if "ob_coach_analysis" not in st.session_state:
        prof = db_get_single("profiles", user_id) or {}
        has_cycle = prof.get("has_cycle", False)
        sys_prompt = build_system_prompt(user_id, prof, has_cycle=has_cycle)
        labs_present = bool(db_get("lab_reports", user_id))
        mode_table = "\n".join(f"- {m}: {v['duration_days'] or 'ongoing'} days — {v['desc']}" for m, v in PLAN_MODES.items())
        prompt = f"""This is a brand-new patient's first-ever consultation, at the end of onboarding, before any roadmap exists.
Plan modes available:
{mode_table}

Labs {'have' if labs_present else 'have NOT'} been uploaded yet — {'note this explicitly and say the recommendation may sharpen once labs are in' if not labs_present else 'use them as primary reference'}.

Write a short, direct, first-person clinical read (180-280 words) in your voice: what you see in the picture, the likely root drivers reasoned across functional medicine, Ayurveda and TCM, and which ONE plan mode you recommend with explicit reasoning. End with one line stating the recommended mode name clearly, e.g. "I'd recommend Restore, our 90-day programme."
"""
        with st.spinner("Your coach is reading your full picture..."):
            analysis = ai_generate(sys_prompt, prompt, max_tokens=900)
        st.session_state.ob_coach_analysis = analysis
        recommended = "Restore"
        for m in PLAN_MODES:
            if re.search(rf"\b{m}\b", analysis):
                recommended = m
                break
        st.session_state.ob_recommended_mode = recommended

    st.markdown(f"""
<div class="insight-box">
<div class="ib-lbl">✦ OneSattva Coach · Initial assessment</div>
<div class="ib-txt">{st.session_state.ob_coach_analysis}</div>
</div>""", unsafe_allow_html=True)

    def go_next():
        st.session_state.ob_step = 6
        st.rerun()

    ob_nav(back_step=4, on_continue=go_next)


# ── Step 6 — Plan mode selection ──────────────────────────────────────────
def onboarding_step6(user_id):
    st.markdown('<div class="pg-title">Choose your plan mode</div>', unsafe_allow_html=True)
    recommended = st.session_state.get("ob_recommended_mode", "Restore")
    st.markdown(f'<div class="pg-sub">Your coach recommended <strong>{recommended}</strong> based on what you\'ve shared. The choice is always yours — bio-individuality applies to the decision too.</div>', unsafe_allow_html=True)

    selected = st.session_state.get("ob_plan_mode", recommended)
    cols = st.columns(2)
    for i, (mode, info) in enumerate(PLAN_MODES.items()):
        with cols[i % 2]:
            is_rec = mode == recommended
            is_sel = mode == selected
            border = "2px solid var(--graphite)" if is_sel else "2px solid var(--line)"
            rec_tag = '<div style="font-size:10px;color:var(--copper);font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:4px">★ Recommended</div>' if is_rec else ""
            dur = f"{info['duration_days']} days" if info["duration_days"] else "Ongoing"
            st.markdown(f"""
<div style="background:var(--white);border:{border};border-radius:12px;padding:17px;margin-bottom:11px">
{rec_tag}
<div style="font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--mid);margin-bottom:5px">{dur}</div>
<div style="font-family:'Newsreader',serif;font-size:19px;color:var(--graphite);margin-bottom:2px">{mode}</div>
<div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--copper);margin-bottom:9px">{info['subtitle']}</div>
<div style="font-size:12px;color:var(--mid);line-height:1.55">{info['desc']}</div>
</div>""", unsafe_allow_html=True)
            if st.button(f"{'✓ Selected' if is_sel else 'Choose ' + mode}", key=f"mode_{mode}", use_container_width=True):
                st.session_state.ob_plan_mode = mode
                st.rerun()

    def go_next():
        db_upsert("roadmaps", {"user_id": user_id, "plan_mode": st.session_state.get("ob_plan_mode", recommended), "committed": False})
        st.session_state.ob_step = 7
        st.rerun()

    ob_nav(back_step=5, on_continue=go_next)


# ── Step 7 — Plan review and commit ───────────────────────────────────────
def onboarding_step7(user_id, profile):
    plan_mode = st.session_state.get("ob_plan_mode", st.session_state.get("ob_recommended_mode", "Restore"))
    info = PLAN_MODES[plan_mode]
    dur_label = f"{info['duration_days']} days" if info["duration_days"] else "ongoing"

    if "ob_roadmap_text" not in st.session_state:
        prof = db_get_single("profiles", user_id) or {}
        has_cycle = prof.get("has_cycle", False)
        sys_prompt = build_system_prompt(user_id, prof, has_cycle=has_cycle)
        labs_present = bool(db_get("lab_reports", user_id))
        prompt = f"""Generate a comprehensive {plan_mode} programme roadmap, duration {dur_label}.
{'Labs are not yet available — generate this roadmap clearly marked PROVISIONAL, with a note it becomes definitive once labs are analysed.' if not labs_present else ''}

FORMAT:
## Your {plan_mode} Programme — Generated {date.today().strftime('%-d %B %Y')}
One sentence on what this programme addresses, grounded in this specific person's data — not generic.

## Phase Timeline
Table: Phase | Focus | Key milestones | Checkpoint
(phases matching the plan duration — fewer/shorter phases for Reset, more for Transform/Sustain)

## Phase 1 — [Title]: [duration]
What changes and why, reasoned from this person's actual data. Specific supplements/nutrition/training with exact doses where the data supports it.
**Retest at checkpoint:** [markers chosen for this person]
**What success looks like:** [outcomes specific to their stated goals]

[Repeat per phase]

## If Phase 1 Shows No Progress
[Escalation path]

**Start today:** [one specific immediate action]
"""
        with st.spinner(f"Building your {plan_mode} roadmap..."):
            st.session_state.ob_roadmap_text = ai_generate(sys_prompt, prompt, max_tokens=3000)

    first_name = (profile or {}).get("full_name", "").split(" ")[0] or "there"
    st.markdown(f"""
<div style="background:var(--forest);border-radius:12px 12px 0 0;padding:24px 30px">
<div style="font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:rgba(247,245,242,0.38);margin-bottom:6px">Your personalised {plan_mode} programme · {dur_label} · Generated {date.today().strftime('%-d %B %Y')}</div>
<div style="font-family:'Newsreader',serif;font-style:italic;font-size:22px;color:#F7F5F2;margin-bottom:5px">Here's what OneSattva has built for you, {first_name}.</div>
</div>
<div style="background:var(--white);border:1px solid var(--line);border-top:none;border-radius:0 0 12px 12px;padding:24px 30px">
""", unsafe_allow_html=True)
    st.markdown(st.session_state.ob_roadmap_text)
    st.markdown(f"""
<div style="background:var(--cu-bg);border:1px solid var(--cu-bd);border-radius:10px;padding:13px 16px;font-size:12.5px;color:var(--mid);line-height:1.6;margin-top:10px">
<strong style="color:var(--graphite)">What committing means:</strong> your roadmap locks in as your active plan and stays that way unless something material changes — see the Coach for how that works.
</div>
</div>
""", unsafe_allow_html=True)

    def go_back():
        st.session_state.ob_step = 6
        st.session_state.pop("ob_roadmap_text", None)
        st.rerun()

    def commit():
        labs_present = bool(db_get("lab_reports", user_id))
        db_upsert("roadmaps", {
            "user_id": user_id, "plan_mode": plan_mode, "roadmap_text": st.session_state.ob_roadmap_text,
            "committed": True, "generated_at": date.today().isoformat(), "phase_start_date": date.today().isoformat(),
            "provisional": not labs_present,
        })
        db_upsert("profiles", {"id": user_id, "onboarding_complete": True})
        for key in list(st.session_state.keys()):
            if key.startswith("ob_"):
                del st.session_state[key]
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Revise my inputs"):
            go_back()
    with c2:
        st.markdown('<div style="text-align:right">', unsafe_allow_html=True)
        if st.button("Commit to this plan →", type="primary"):
            commit()
        st.markdown('</div>', unsafe_allow_html=True)
# ── Plan info helper ───────────────────────────────────────────────────────
def get_plan_info(user_id, profile):
    roadmap = db_get_single("roadmaps", user_id)
    if not roadmap or not roadmap.get("committed"):
        return None
    mode = roadmap.get("plan_mode", "Restore")
    info = PLAN_MODES.get(mode, PLAN_MODES["Restore"])
    start = roadmap.get("phase_start_date") or roadmap.get("generated_at")
    try:
        start_date = date.fromisoformat(start)
        days_in = (date.today() - start_date).days
    except Exception:
        days_in = 0
    duration_days = info["duration_days"]
    if duration_days:
        week_num = min(max(days_in // 7 + 1, 1), (duration_days // 7) or 1)
        total_weeks = max(duration_days // 7, 1)
        pct = min(100, round(days_in / duration_days * 100))
    else:
        week_num, total_weeks, pct = days_in // 7 + 1, None, None
    return {"mode": mode, "roadmap": roadmap, "week_num": week_num, "total_weeks": total_weeks,
            "pct": pct, "duration_days": duration_days, "days_in": days_in}


# ── Sidebar ───────────────────────────────────────────────────────────────────
def show_sidebar(user_id, profile):
    plan = get_plan_info(user_id, profile)
    with st.sidebar:
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;padding-bottom:16px;border-bottom:1px solid rgba(247,245,242,0.07);margin-bottom:16px">
{mark_svg(22, dark=True)}
<div>{wordmark_html(19)}</div>
</div>""", unsafe_allow_html=True)

        name = profile.get("full_name", "") if profile else ""
        loc = profile.get("location", "") if profile else ""
        sex = profile.get("sex", "") if profile else ""
        dob = profile.get("dob") if profile else None
        age_str = ""
        if dob:
            try:
                d = date.fromisoformat(dob)
                age = date.today().year - d.year - ((date.today().month, date.today().day) < (d.month, d.day))
                age_str = f"{age}yr"
            except Exception:
                pass
        meta = " · ".join(x for x in [loc, age_str, sex] if x)
        plan_pill = f'<div class="plan-pill">{plan["mode"]} · Wk {plan["week_num"]}{" / " + str(plan["total_weeks"]) if plan["total_weeks"] else ""}</div>' if plan else ""
        st.markdown(f"""
<div style="padding-bottom:14px;border-bottom:1px solid rgba(247,245,242,0.05);margin-bottom:14px">
<div class="sb-name">{name}</div>
<div class="sb-meta">{meta}</div>
{plan_pill}
</div>""", unsafe_allow_html=True)

        st.markdown('<div style="font-size:10px;font-weight:600;letter-spacing:0.08em;color:rgba(247,245,242,0.24);text-transform:uppercase;margin-bottom:6px">Navigation</div>', unsafe_allow_html=True)
        nav_items = [("home", "⌂ Home"), ("protocol", "◈ Protocol"), ("checkin", "✓ Check-In"), ("coach", "✦ Coach"), ("profile", "◎ Profile & Data")]
        current = st.session_state.get("page", "home")
        for key, label in nav_items:
            if st.button(label, key=f"nav_{key}", use_container_width=True, type=("primary" if key == current else "secondary")):
                st.session_state.page = key
                st.rerun()

        st.markdown('<div style="margin-top:auto"></div>', unsafe_allow_html=True)
        if plan:
            dur_label = f"{plan['duration_days']}-day programme" if plan["duration_days"] else "Ongoing programme"
            week_label = f"Week {plan['week_num']} of {plan['total_weeks']}" if plan["total_weeks"] else f"Week {plan['week_num']}"
            st.markdown(f'<div class="sb-foot-t">{plan["mode"]} · {dur_label}<br>{week_label}</div>', unsafe_allow_html=True)
        if st.button("Sign out", key="signout", use_container_width=True):
            sign_out()


# ── Daily priorities cache (once per calendar day, DB-backed) ────────────────
def get_or_generate_daily_priorities(user_id, sys_prompt, force=False):
    today_str = date.today().isoformat()
    if not force:
        existing = supabase.table("daily_priorities").select("*").eq("user_id", user_id).eq("for_date", today_str).limit(1).execute()
        if existing.data:
            try:
                return json.loads(existing.data[0]["priorities_json"])
            except Exception:
                pass
    prompt = """Generate exactly 3 priority cards for the user's Home screen today, based on the full picture in the system prompt (committed roadmap, current phase/week, labs, wearable, check-ins, cycle if applicable).
Return ONLY valid JSON, a list of exactly 3 objects: [{"triage": "now"|"watch"|"background", "title": "...", "body": "..."}]
triage "now" = act today, "watch" = monitor closely, "background" = lower urgency context. title under 12 words. body 1-3 sentences, specific to this person's actual data."""
    raw = ai_generate(sys_prompt, prompt, max_tokens=900)
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        priorities = json.loads(match.group(0) if match else raw)
    except Exception:
        priorities = [{"triage": "background", "title": "Coach is still building today's read", "body": raw[:200]}]
    supabase.table("daily_priorities").upsert({"user_id": user_id, "for_date": today_str, "priorities_json": json.dumps(priorities)}).execute()
    return priorities


def greeting():
    h = datetime.now().hour
    return "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"


# ── Home Page ─────────────────────────────────────────────────────────────────
def show_home(user_id, profile):
    plan = get_plan_info(user_id, profile)
    if plan:
        dur_label = f"{plan['duration_days']}-day programme" if plan["duration_days"] else "Ongoing programme"
        bar = f'<div style="width:112px;height:4px;background:rgba(247,245,242,0.14);border-radius:2px"><div style="height:100%;background:var(--copper);border-radius:2px;width:{plan["pct"] or 30}%"></div></div>' if plan["pct"] is not None else ""
        wk_label = f'Wk {plan["week_num"]} / {plan["total_weeks"]}' if plan["total_weeks"] else f'Wk {plan["week_num"]}'
        st.markdown(f"""
<div class="plan-banner" style="display:flex;justify-content:space-between;align-items:center">
<div style="display:flex;align-items:center;gap:14px">
<div><div class="pb-ml">Plan mode</div><div class="pb-mn">{plan['mode']} · {dur_label}</div></div>
<div style="display:flex;align-items:center;gap:8px">{bar}<div class="pb-wk">{wk_label}</div></div>
</div>
</div>""", unsafe_allow_html=True)
        if st.button("View roadmap →", key="home_view_roadmap"):
            st.session_state.page = "protocol"
            st.rerun()
    else:
        st.markdown('<div style="border:1.5px dashed var(--stone);border-radius:10px;padding:18px;text-align:center;color:var(--mid);margin-bottom:14px">No committed roadmap yet.</div>', unsafe_allow_html=True)

    first_name = (profile.get("full_name", "") if profile else "").split(" ")[0] or "there"
    st.markdown(f'<div class="pg-title" style="margin-bottom:2px">{greeting()}, {first_name}.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pg-sub">{datetime.now().strftime("%A, %d %B %Y")} · Here\'s what matters today.</div>', unsafe_allow_html=True)

    goals = db_get("goals", user_id)
    primary_goals = [g for g in goals if g.get("timeframe") == "Primary"]
    other_goals = [g for g in goals if g.get("timeframe") != "Primary"]
    if goals or plan:
        st.markdown('<div class="sl first">Your goals</div>', unsafe_allow_html=True)
        primary_text = primary_goals[0]["goal"] if primary_goals else (goals[0]["goal"] if goals else "No primary goal set yet.")
        weeks_html = ""
        if plan and plan["roadmap"].get("roadmap_text"):
            phase_match = re.findall(r"##\s*Phase\s*\d+[^\n]*", plan["roadmap"]["roadmap_text"])
            shown = phase_match[:4] if phase_match else []
            for i, ph in enumerate(shown):
                is_now = (i == 0)
                weeks_html += f'<div class="gc-wk{" now" if is_now else ""}"><div class="gc-wkn">{"Now" if is_now else f"Phase {i+1}"}</div><div class="gc-wkf">{ph.replace("##","").strip()[:80]}</div></div>'
        st.markdown(f"""
<div class="goal-card">
<div class="gc-lbl">Primary goal</div>
<div class="gc-goal">"{primary_text}"</div>
{f'<div class="gc-weeks">{weeks_html}</div>' if weeks_html else ''}
</div>""", unsafe_allow_html=True)
        if other_goals:
            with st.expander(f"View all goals ({len(other_goals)} more)"):
                for g in other_goals:
                    st.markdown(f"- {g['goal']} *{('· ' + g['timeframe']) if g.get('timeframe') else ''}*")

    st.markdown('<div class="sl">Today\'s priorities</div>', unsafe_allow_html=True)
    has_cycle = profile.get("has_cycle", False) if profile else False
    sys_prompt = build_system_prompt(user_id, profile, has_cycle=has_cycle)
    priorities = get_or_generate_daily_priorities(user_id, sys_prompt)
    triage_class = {"now": "t-now", "watch": "t-watch", "background": "t-bg"}
    triage_label = {"now": "Act today", "watch": "Watch", "background": "Background"}
    cols = st.columns(3)
    for i, p in enumerate(priorities[:3]):
        with cols[i]:
            t = p.get("triage", "background")
            st.markdown(f"""
<div class="prio-card">
<span class="triage {triage_class.get(t,'t-bg')}">{triage_label.get(t,'Background')}</span>
<div class="pc-title">{p.get('title','')}</div>
<div class="pc-body">{p.get('body','')}</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="sl">Today\'s snapshot</div>', unsafe_allow_html=True)
    wearable = db_get("wearable_data", user_id, order_col="data_date", limit=30)
    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)
    latest_w = wearable[0] if wearable else {}
    latest_c = checkins[0] if checkins else {}
    avg_hrv = round(statistics.mean([w["hrv"] for w in wearable if w.get("hrv")]), 0) if any(w.get("hrv") for w in wearable) else None
    snaps = [
        ("HRV", f"{latest_w.get('hrv','—')}", "ms", f"WHOOP · {latest_w.get('data_date','—')}", f"30d avg: {avg_hrv}ms" if avg_hrv else ""),
        ("Recovery", f"{latest_w.get('recovery_score','—')}", "%", "WHOOP", ""),
        ("Sleep", f"{latest_w.get('sleep_performance','—')}", "%", "WHOOP", ""),
        ("Energy", f"{latest_c.get('energy','—')}", "/10", f"Check-in · {latest_c.get('checkin_date','—')}", ""),
    ]
    cols = st.columns(4)
    for i, (lbl, val, unit, sub, flag) in enumerate(snaps):
        with cols[i]:
            st.markdown(f"""
<div class="snap-box">
<div class="snap-lbl">{lbl}</div>
<div class="snap-val">{val}<span style="font-size:13px;color:var(--mid)">{unit}</span></div>
<div class="snap-sub">{sub}</div>
{f'<div class="snap-flag">{flag}</div>' if flag else ''}
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="sl">Trends</div>', unsafe_allow_html=True)
    checkins_30 = list(reversed(db_get("checkins", user_id, order_col="checkin_date", limit=30)))
    wearable_30 = list(reversed(db_get("wearable_data", user_id, order_col="data_date", limit=30)))

    def make_bars(values, max_val=10):
        bars = ""
        for v in values[-15:]:
            h = max(8, min(100, round((v or 0) / max_val * 100)))
            bars += f'<div class="tb" style="height:{h}%"></div>'
        return bars or '<div style="color:var(--mid);font-size:11px;padding:10px">Not enough data yet.</div>'

    c1, c2 = st.columns(2)
    with c1:
        energy_vals = [c.get("energy") for c in checkins_30]
        st.markdown(f"""
<div class="trend-card">
<div class="tc-title">Energy · 30 days</div>
<div class="tc-insight">{f"{len(checkins_30)} check-ins logged in the last 30 days." if checkins_30 else "Log a check-in to start building this trend."}</div>
<div class="tc-bars">{make_bars(energy_vals)}</div>
</div>""", unsafe_allow_html=True)
    with c2:
        hrv_vals = [w.get("hrv") for w in wearable_30]
        max_hrv = max([v for v in hrv_vals if v] or [100])
        st.markdown(f"""
<div class="trend-card">
<div class="tc-title">HRV trajectory · 30 days</div>
<div class="tc-insight">{f"{len(wearable_30)} days of wearable data in the last 30 days." if wearable_30 else "Import wearable data from Profile & Data to see this trend."}</div>
<div class="tc-bars">{make_bars(hrv_vals, max_hrv)}</div>
</div>""", unsafe_allow_html=True)
# ── Materiality flags — the single gate for any plan change (Brief §6) ───────
def get_open_materiality_flag(user_id, level):
    try:
        res = supabase.table("materiality_flags").select("*").eq("user_id", user_id).eq("level", level).eq("resolved", False).order("created_at", desc=True).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def render_materiality_flag(flag):
    if not flag:
        return
    st.markdown(f"""
<div class="material-flag">
<div class="mf-lbl">✦ Coach flag — possible material change</div>
<div class="mf-txt">{flag.get('flag_text','')}</div>
</div>""", unsafe_allow_html=True)
    if st.button("Discuss with coach →", key=f"flag_discuss_{flag.get('id')}"):
        st.session_state.page = "coach"
        st.session_state.coach_seed = f"You flagged something about my {flag.get('level')} — let's talk about it."
        st.rerun()


def get_or_generate(table, user_id, build_fn, force=False):
    if not force:
        existing = db_get_single(table, user_id)
        if existing and existing.get("content"):
            return existing["content"]
    content = build_fn()
    db_upsert(table, {"user_id": user_id, "content": content, "generated_at": date.today().isoformat()})
    return content


# ── Protocol Page ─────────────────────────────────────────────────────────────
def show_protocol(user_id, profile):
    st.markdown('<div class="pg-title">Protocol</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Generated from your roadmap. Stable by default — only changes when your coach\'s judgment says something is material and you agree. Everything here is built by OneSattva, not entered by you.</div>', unsafe_allow_html=True)

    roadmap = db_get_single("roadmaps", user_id)
    if not roadmap or not roadmap.get("committed"):
        st.info("No committed roadmap yet — complete onboarding to generate your protocol.")
        return

    has_cycle = profile.get("has_cycle", False) if profile else False
    sys_prompt = build_system_prompt(user_id, profile, has_cycle=has_cycle)

    tabs = st.tabs(["Treatment Roadmap", "Monthly Goal", "Supplements", "Nutrition", "Workouts"])

    with tabs[0]:
        render_materiality_flag(get_open_materiality_flag(user_id, "roadmap"))
        plan = get_plan_info(user_id, profile)
        st.markdown(f'<div class="sl first">{roadmap.get("plan_mode","")} · roadmap · Committed {roadmap.get("generated_at","")}</div>', unsafe_allow_html=True)
        if roadmap.get("provisional"):
            st.warning("This roadmap is provisional — labs were not yet available when it was generated.")
        st.markdown(roadmap.get("roadmap_text", "_No roadmap text._"))
        st.download_button("Download roadmap", roadmap.get("roadmap_text", ""), file_name="onesattva_roadmap.md")

    with tabs[1]:
        render_materiality_flag(get_open_materiality_flag(user_id, "monthly_focus"))
        def build_monthly():
            prompt = "Generate this phase's Monthly Goal focus: one italic-style focus statement (1-2 sentences) plus a 4-week breakdown table (Week | Focus). Base this on the committed roadmap's current phase. Keep it tight — this is displayed as a small card, not a long document."
            return ai_generate(sys_prompt, prompt, max_tokens=900)
        monthly = get_or_generate("monthly_focus", user_id, build_monthly)
        st.markdown(f'<div class="goal-card"><div class="gc-lbl">Current phase focus</div><div class="gc-goal" style="font-style:normal;font-size:13.5px">{monthly}</div></div>', unsafe_allow_html=True)

    with tabs[2]:
        render_materiality_flag(get_open_materiality_flag(user_id, "supplements"))
        def build_supps():
            prompt = "Generate this week's committed supplement schedule as a markdown table: Time | Supplement | Dose | Clinical notes. Derive dose, brand suitability, and timing from this person's actual labs, medications, and absorption considerations — explain timing rationale in the notes column. If a thyroid medication is present, reason explicitly about its absorption timing relative to other supplements."
            return ai_generate(sys_prompt, prompt, max_tokens=1200)
        supps = get_or_generate("supplement_plan", user_id, build_supps)
        st.markdown(supps)
        with st.expander("Want to adjust something?"):
            adj = st.text_area("Describe what you'd like to change", key="adj_supp")
            if st.button("Discuss with coach", key="adj_supp_btn") and adj:
                st.session_state.page = "coach"
                st.session_state.coach_seed = f"About my supplement schedule: {adj}"
                st.rerun()

    with tabs[3]:
        render_materiality_flag(get_open_materiality_flag(user_id, "nutrition"))
        def build_nutrition():
            prompt = "Generate this week's committed 7-day nutrition plan. Start with a short info box on this phase's nutrition focus, reasoned from this person's actual gut/digestion check-in data, goals, and dietary preferences — not a generic rule. Then a markdown table: Meal | Focus | Examples. Respect their stated dietary pattern and restrictions exactly."
            return ai_generate(sys_prompt, prompt, max_tokens=1400)
        nutrition = get_or_generate("nutrition_plan", user_id, build_nutrition)
        st.markdown(nutrition)
        with st.expander("Want to adjust something?"):
            adj = st.text_area("Describe what you'd like to change", key="adj_nutr")
            if st.button("Discuss with coach", key="adj_nutr_btn") and adj:
                st.session_state.page = "coach"
                st.session_state.coach_seed = f"About my nutrition plan: {adj}"
                st.rerun()

    with tabs[4]:
        render_materiality_flag(get_open_materiality_flag(user_id, "workouts"))
        def build_workouts():
            prompt = "Generate this week's committed 7-day training plan. Start with a short info box on this phase's training principle, reasoned from this person's recovery/wearable data and goals. Then a markdown table: Day | Session type | Focus & exercises | Target duration. Calibrate intensity to recovery data if available."
            return ai_generate(sys_prompt, prompt, max_tokens=1200)
        workouts = get_or_generate("workout_plan", user_id, build_workouts)
        st.markdown(workouts)
# ── Materiality check — runs after new data is submitted, not on a timer ─────
def check_materiality(user_id, sys_prompt, trigger_desc):
    prompt = f"""A new data point just came in: {trigger_desc}.
Given everything you know about this patient, is there anything here material enough that the committed roadmap, this phase's monthly focus, or a weekly protocol (supplements/nutrition/workouts) should be revisited? Use your own clinical judgment — there is no fixed checklist. A change that's material for one patient may be irrelevant for another.
Respond with ONLY valid JSON: {{"material": true/false, "level": "roadmap"|"monthly_focus"|"supplements"|"nutrition"|"workouts"|null, "flag_text": "what changed, why it's material for this person specifically, what level should change, what you're proposing" or null}}"""
    raw = ai_generate(sys_prompt, prompt, max_tokens=500)
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(match.group(0) if match else raw)
    except Exception:
        return
    if result.get("material") and result.get("level"):
        db_insert("materiality_flags", {"user_id": user_id, "level": result["level"], "flag_text": result.get("flag_text", ""), "resolved": False, "created_at": datetime.now().isoformat()})


# ── Check-In Page ─────────────────────────────────────────────────────────────
CHECKIN_METRICS = ["energy", "mental_clarity", "sleep_quality", "mood", "gut", "libido"]
CHECKIN_LABELS = {"energy": "Energy", "mental_clarity": "Mental clarity", "sleep_quality": "Sleep quality",
                   "mood": "Mood", "gut": "Gut / digestion", "libido": "Libido"}


def get_or_generate_checkin_insight(user_id, sys_prompt, force=False):
    today_str = date.today().isoformat()
    if not force:
        existing = supabase.table("checkin_insights").select("*").eq("user_id", user_id).eq("for_date", today_str).limit(1).execute()
        if existing.data:
            return existing.data[0]["insight_text"]
    insight = ai_generate(sys_prompt, "Generate one short clinical observation (2-4 sentences, your voice) from today's check-in data in the context of recent patterns. Be specific and reference actual numbers.", max_tokens=300)
    supabase.table("checkin_insights").upsert({"user_id": user_id, "for_date": today_str, "insight_text": insight}).execute()
    return insight


def show_checkin(user_id, profile):
    has_cycle = profile.get("has_cycle", False) if profile else False
    cycle_str = ""
    if has_cycle:
        cycle_day, phase, _ = calculate_cycle_status(user_id)
        if cycle_day:
            cycle_str = f" · Cycle Day {cycle_day}"

    today_str = date.today().isoformat()
    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)
    today_checkin = checkins[0] if checkins and checkins[0].get("checkin_date") == today_str else None

    st.markdown('<div class="pg-title">Daily Check-In</div>', unsafe_allow_html=True)
    h = datetime.now().hour
    tod = "Morning" if h < 12 else "Afternoon" if h < 18 else "Evening"
    st.markdown(f'<div class="pg-sub">{tod} check-in · {datetime.now().strftime("%A, %d %B")}{cycle_str} · Pre-filled from yesterday. Edit anything that has changed today. Takes less than 2 minutes.</div>', unsafe_allow_html=True)

    editing = st.session_state.get("checkin_editing", False)

    if today_checkin and not editing:
        sys_prompt = build_system_prompt(user_id, profile, has_cycle=has_cycle)
        insight = get_or_generate_checkin_insight(user_id, sys_prompt)
        st.markdown(f"""
<div class="insight-box">
<div class="ib-lbl">✦ Coach · Today's insight</div>
<div class="ib-txt">{insight}</div>
</div>""", unsafe_allow_html=True)
        cols = st.columns(4)
        for i, m in enumerate(["energy", "mental_clarity", "sleep_quality", "mood"]):
            with cols[i]:
                st.markdown(f'<div class="snap-box"><div class="snap-lbl">{CHECKIN_LABELS[m]}</div><div class="snap-val">{today_checkin.get(m,"—")}<span style="font-size:13px;color:var(--mid)">/10</span></div></div>', unsafe_allow_html=True)
        if today_checkin.get("notes"):
            st.caption(today_checkin["notes"])
        if st.button("✏️ Edit today's check-in"):
            st.session_state.checkin_editing = True
            st.rerun()
        return

    yesterday = db_get("checkins", user_id, order_col="checkin_date", limit=2)
    prefill = today_checkin or (yesterday[1] if len(yesterday) > 1 else (yesterday[0] if yesterday else {}))

    c1, c2 = st.columns(2)
    vals = {}
    with c1:
        st.markdown(f'<p class="ci-lbl">{CHECKIN_LABELS["energy"]}</p>', unsafe_allow_html=True)
        vals["energy"] = st.slider("energy", 1, 10, int(prefill.get("energy", 5) or 5), label_visibility="collapsed")
        st.markdown(f'<p class="ci-lbl">{CHECKIN_LABELS["sleep_quality"]}</p>', unsafe_allow_html=True)
        vals["sleep_quality"] = st.slider("sleep_quality", 1, 10, int(prefill.get("sleep_quality", 5) or 5), label_visibility="collapsed")
        st.markdown(f'<p class="ci-lbl">{CHECKIN_LABELS["gut"]}</p>', unsafe_allow_html=True)
        vals["gut"] = st.selectbox("gut", ["Excellent", "Good", "Bloated", "Uncomfortable", "Poor"],
                                    index=["Excellent", "Good", "Bloated", "Uncomfortable", "Poor"].index(prefill.get("gut")) if prefill.get("gut") in ["Excellent", "Good", "Bloated", "Uncomfortable", "Poor"] else 1,
                                    label_visibility="collapsed")
    with c2:
        st.markdown(f'<p class="ci-lbl">{CHECKIN_LABELS["mental_clarity"]}</p>', unsafe_allow_html=True)
        vals["mental_clarity"] = st.slider("mental_clarity", 1, 10, int(prefill.get("mental_clarity", 5) or 5), label_visibility="collapsed")
        st.markdown(f'<p class="ci-lbl">{CHECKIN_LABELS["mood"]}</p>', unsafe_allow_html=True)
        vals["mood"] = st.slider("mood", 1, 10, int(prefill.get("mood", 5) or 5), label_visibility="collapsed")
        st.markdown(f'<p class="ci-lbl">{CHECKIN_LABELS["libido"]}</p>', unsafe_allow_html=True)
        vals["libido"] = st.selectbox("libido", ["High", "Normal", "Low", "Very low"],
                                       index=["High", "Normal", "Low", "Very low"].index(prefill.get("libido")) if prefill.get("libido") in ["High", "Normal", "Low", "Very low"] else 1,
                                       label_visibility="collapsed")

    c3, c4 = st.columns(2)
    sleep_hours = c3.number_input("Sleep hours", min_value=0.0, max_value=14.0, step=0.5, value=float(prefill.get("sleep_hours", 7) or 7))
    workout = c4.selectbox("Today's workout", ["None", "Strength", "Cardio", "Mobility / Yoga", "Walk", "Rest day"],
                            index=["None", "Strength", "Cardio", "Mobility / Yoga", "Walk", "Rest day"].index(prefill.get("workout")) if prefill.get("workout") in ["None", "Strength", "Cardio", "Mobility / Yoga", "Walk", "Rest day"] else 0)
    notes = st.text_area("Notes (optional)", value=prefill.get("notes", "") if today_checkin else "", placeholder="Anything notable today — symptoms, observations, questions for your coach...")

    if st.button("Save today's check-in →", type="primary"):
        row = {"user_id": user_id, "checkin_date": today_str, "sleep_hours": sleep_hours, "workout": workout, "notes": notes, **vals}
        db_upsert("checkins", row)
        supabase.table("checkin_insights").delete().eq("user_id", user_id).eq("for_date", today_str).execute()
        st.session_state.checkin_editing = False
        has_cycle2 = profile.get("has_cycle", False) if profile else False
        sys_prompt = build_system_prompt(user_id, profile, has_cycle=has_cycle2)
        check_materiality(user_id, sys_prompt, f"Today's check-in: {row}")
        st.success("Check-in saved.")
        st.rerun()


# ── Coach Page ────────────────────────────────────────────────────────────────
def show_coach(user_id, profile):
    st.markdown('<div class="pg-title">Coach</div>', unsafe_allow_html=True)
    has_cycle = profile.get("has_cycle", False) if profile else False

    if "coach_messages" not in st.session_state:
        st.session_state.coach_messages = []

    if not st.session_state.coach_messages:
        first_name = (profile.get("full_name", "") if profile else "").split(" ")[0] or "there"
        cycle_line = ""
        if has_cycle:
            cycle_day, phase, _ = calculate_cycle_status(user_id)
            if cycle_day:
                cycle_line = f" You're on cycle day {cycle_day} — {phase}."
        st.markdown(f"""
<div class="insight-box">
<div class="ib-lbl">✦ OneSattva Coach</div>
<div class="ib-txt">Hello {first_name}. I'm holding your complete picture — labs, check-ins, wearable trends, and your committed roadmap.{cycle_line} Ask me anything.</div>
</div>""", unsafe_allow_html=True)

        prompts = ["What should I focus on this week?", "Explain my latest lab results"]
        if has_cycle:
            prompts.append("How should I train this cycle phase?")
        else:
            prompts.append("How should I adjust training around my recovery?")
        prompts.append("Review my supplement timing")
        cols = st.columns(2)
        for i, p in enumerate(prompts[:4]):
            with cols[i % 2]:
                if st.button(p, key=f"qp_{i}", use_container_width=True):
                    st.session_state.coach_seed = p

    for msg in st.session_state.coach_messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown('<div class="ch-hd">✦ OneSattva Coach</div>', unsafe_allow_html=True)
            st.markdown(msg["content"])

    if st.button("Clear chat", key="clear_chat"):
        st.session_state.coach_messages = []
        st.rerun()

    seed = st.session_state.pop("coach_seed", None)
    user_input = st.chat_input("Ask your coach anything…")
    final_input = seed or user_input

    if final_input:
        st.session_state.coach_messages.append({"role": "user", "content": final_input})
        sys_prompt = build_system_prompt(user_id, profile, has_cycle=has_cycle)
        flags = []
        for level in ["roadmap", "monthly_focus", "supplements", "nutrition", "workouts"]:
            f = get_open_materiality_flag(user_id, level)
            if f:
                flags.append(f"[{level}] {f.get('flag_text','')}")
        if flags:
            sys_prompt += "\n\nPENDING MATERIALITY FLAGS (reference naturally if relevant):\n" + "\n".join(flags)
        api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.coach_messages]
        with st.spinner("Thinking..."):
            reply = ai_chat(sys_prompt, api_messages)
        st.session_state.coach_messages.append({"role": "assistant", "content": reply})
        st.rerun()
# ── Profile & Data Page ───────────────────────────────────────────────────────
def show_profile(user_id, profile):
    st.markdown('<div class="pg-title">Profile & Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Everything you\'ve brought to OneSattva. All fields are editable at any time — your data is always yours.</div>', unsafe_allow_html=True)

    labs = db_get("lab_reports", user_id, order_col="report_date", limit=1)
    if labs:
        try:
            days_old = (date.today() - date.fromisoformat(labs[0]["report_date"])).days
            if days_old > 90:
                st.markdown(f'<div class="cp-banner"><strong>Your latest lab report is {days_old} days old.</strong> Consider a retest — recommendations from labs older than 90 days are used for trend only, not current status.</div>', unsafe_allow_html=True)
        except Exception:
            pass

    open_flags = [f for level in ["roadmap", "monthly_focus", "supplements", "nutrition", "workouts"] if (f := get_open_materiality_flag(user_id, level))]
    if open_flags:
        f = open_flags[0]
        st.markdown(f'<div class="cp-banner"><strong>Coach notice ({f.get("level")}):</strong> {f.get("flag_text","")}</div>', unsafe_allow_html=True)

    tabs = st.tabs(["User Profile", "Lab Reports & Documents", "Wearable Data"])
    with tabs[0]:
        show_profile_user(user_id, profile)
    with tabs[1]:
        show_profile_labs(user_id, profile)
    with tabs[2]:
        show_profile_wearable(user_id, profile)


def show_profile_user(user_id, profile):
    p = profile or {}
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown('#### Demographics')
            dob_str = p.get("dob", "")
            age_str = ""
            if dob_str:
                try:
                    d = date.fromisoformat(dob_str)
                    age = date.today().year - d.year - ((date.today().month, date.today().day) < (d.month, d.day))
                    age_str = f" ({age})"
                except Exception:
                    pass
            st.markdown(f"""
<div class="pr"><span class="pr-k">Name</span><span class="pr-v">{p.get('full_name','—')}</span></div>
<div class="pr"><span class="pr-k">Date of birth</span><span class="pr-v">{dob_str}{age_str}</span></div>
<div class="pr"><span class="pr-k">Biological sex</span><span class="pr-v">{p.get('sex','—')}</span></div>
<div class="pr"><span class="pr-k">Location</span><span class="pr-v">{p.get('location','—')}</span></div>
<div class="pr"><span class="pr-k">Height</span><span class="pr-v">{p.get('height_cm','—')} cm</span></div>
<div class="pr"><span class="pr-k">Weight</span><span class="pr-v">{p.get('weight_kg','—')} kg</span></div>
<div class="pr"><span class="pr-k">Occupation</span><span class="pr-v">{p.get('occupation') or '—'}</span></div>
""", unsafe_allow_html=True)
            with st.expander("Edit demographics"):
                height = st.number_input("Height (cm)", 100, 230, int(p.get("height_cm") or 170), key="ed_h")
                weight = st.number_input("Weight (kg)", 30, 250, int(p.get("weight_kg") or 70), key="ed_w")
                location = st.text_input("Location", value=p.get("location", ""), key="ed_loc")
                occupation = st.text_input("Occupation", value=p.get("occupation", ""), key="ed_occ")
                has_cycle_now = p.get("has_cycle", False)
                new_has_cycle = has_cycle_now
                if p.get("sex") in ("Female", "Intersex"):
                    new_has_cycle = st.checkbox("I currently have a menstrual cycle to track", value=bool(has_cycle_now), key="ed_hc")
                if st.button("Save changes", key="save_demo"):
                    db_upsert("profiles", {"id": user_id, "height_cm": height, "weight_kg": weight, "location": location, "occupation": occupation, "has_cycle": bool(new_has_cycle)})
                    st.success("Saved.")
                    st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown('#### Medical History')
            conditions = db_get("medical_history", user_id)
            meds = db_get("medications", user_id)
            if conditions:
                for c in conditions:
                    st.markdown(f'<div class="pr"><span class="pr-k">{c.get("condition","")}</span><span class="pr-v">{c.get("notes","")}</span></div>', unsafe_allow_html=True)
            if meds:
                for m in meds:
                    st.markdown(f'<div class="pr"><span class="pr-k">{m.get("name","")}</span><span class="pr-v">{m.get("dose","")} · {m.get("frequency","")}</span></div>', unsafe_allow_html=True)
            if not conditions and not meds:
                st.caption("No conditions or medications on file.")
            with st.expander("Add condition or medication"):
                new_cond = st.text_input("New condition", key="new_cond")
                cond_notes = st.text_input("Notes", key="new_cond_notes")
                if st.button("Add condition", key="add_cond") and new_cond:
                    db_insert("medical_history", {"user_id": user_id, "condition": new_cond, "notes": cond_notes})
                    st.rerun()
                st.markdown("---")
                new_med = st.text_input("New medication", key="new_med")
                med_dose = st.text_input("Dose", key="new_med_dose")
                med_freq = st.text_input("Frequency / timing", key="new_med_freq")
                if st.button("Add medication", key="add_med") and new_med:
                    db_insert("medications", {"user_id": user_id, "name": new_med, "dose": med_dose, "frequency": med_freq, "active": True})
                    st.rerun()

    with st.expander("Goals", expanded=True):
        goals = db_get("goals", user_id)
        for g in goals:
            gc1, gc2 = st.columns([5, 1])
            gc1.markdown(f"- {g['goal']} *{('· ' + g['timeframe']) if g.get('timeframe') else ''}*")
            if gc2.button("Delete", key=f"del_goal_{g['id']}"):
                db_delete("goals", g["id"])
                st.rerun()
        new_goal = st.text_input("Add a goal", key="new_goal")
        if st.button("+ Add goal", key="add_goal_btn") and new_goal:
            db_insert("goals", {"user_id": user_id, "goal": new_goal, "timeframe": "3 months"})
            st.rerun()

    with st.expander("Current supplements"):
        supps = db_get("supplements", user_id)
        for s in supps:
            sc1, sc2 = st.columns([5, 1])
            sc1.markdown(f"- {s.get('name','')} — {s.get('dose','')} ({s.get('timing','')})")
            if sc2.button("Delete", key=f"del_supp_{s['id']}"):
                db_delete("supplements", s["id"])
                st.rerun()
        n1, n2, n3 = st.columns(3)
        sn = n1.text_input("Name", key="new_supp_n")
        sd = n2.text_input("Dose", key="new_supp_d")
        st_ = n3.text_input("Timing", key="new_supp_t")
        if st.button("+ Add supplement", key="add_supp_btn") and sn:
            db_insert("supplements", {"user_id": user_id, "name": sn, "dose": sd, "timing": st_, "active": True})
            st.rerun()

    with st.expander("Dietary profile & restrictions"):
        eating_pattern = st.selectbox("Eating pattern", ["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"],
                                       index=["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"].index(p.get("eating_pattern")) if p.get("eating_pattern") in ["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"] else 0, key="ed_diet")
        allergies = st.text_input("Allergies / intolerances", value=p.get("allergies", ""), key="ed_allerg")
        if st.button("Save dietary profile", key="save_diet"):
            db_upsert("profiles", {"id": user_id, "eating_pattern": eating_pattern, "allergies": allergies})
            st.success("Saved.")
            st.rerun()

    with st.expander("Lifestyle — activity, sleep, stress"):
        notes = db_get_single("profile_notes", user_id)
        lifestyle_text = st.text_area("Lifestyle notes", value=(notes or {}).get("notes", ""), height=160, key="ed_lifestyle")
        if st.button("Save lifestyle notes", key="save_lifestyle"):
            db_upsert("profile_notes", {"user_id": user_id, "notes": lifestyle_text})
            st.success("Saved.")
            st.rerun()

    if p.get("has_cycle"):
        with st.expander("Cycle tracking"):
            cd = db_get_single("cycle_data", user_id) or {}
            cycle_day, phase, days_until = calculate_cycle_status(user_id)
            if cycle_day:
                st.markdown(f"**Day {cycle_day}** · {phase} · {days_until} days until next period")
            c1, c2 = st.columns(2)
            last_start = c1.date_input("Last period start", value=date.fromisoformat(cd["last_period_start"]) if cd.get("last_period_start") else date.today(), key="ed_cycle_start")
            avg_len = c2.number_input("Actual average cycle length (days)", 15, 60, int(cd.get("avg_cycle_length") or 28), key="ed_cycle_len")
            if st.button("Save cycle data", key="save_cycle"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": last_start.isoformat(), "avg_cycle_length": int(avg_len)})
                st.success("Saved.")
                st.rerun()
            if st.button("New period started today", key="new_period"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": date.today().isoformat(), "avg_cycle_length": int(cd.get("avg_cycle_length") or 28)})
                st.rerun()
    # has_cycle False/unset: accordion deliberately absent — not collapsed, not greyed out.

    with st.expander("Plan mode"):
        roadmap = db_get_single("roadmaps", user_id)
        if roadmap:
            st.markdown(f"{roadmap.get('plan_mode','—')} · started {roadmap.get('phase_start_date','—')}")
        st.caption("Changing plan mode is a conversation with your coach, not a free dropdown.")
        if st.button("Discuss plan mode with coach", key="discuss_plan_mode"):
            st.session_state.page = "coach"
            st.session_state.coach_seed = "I'd like to talk about possibly changing my plan mode."
            st.rerun()


def show_profile_labs(user_id, profile):
    st.markdown('<div class="sl first">Upload a new report</div>', unsafe_allow_html=True)
    report_date = st.date_input("Report date", value=date.today(), key="lab_date")
    raw_values = st.text_area("Paste lab values", height=140, key="lab_raw")
    if st.button("Analyse and save", key="lab_save"):
        if raw_values.strip():
            with st.spinner("Interpreting against functional ranges..."):
                summary = ai_generate(
                    "You are OneSattva, interpreting lab values against functional (optimal) ranges, not conventional population reference ranges. Give a concise 2-4 sentence clinical summary.",
                    raw_values, max_tokens=500)
            db_insert("lab_reports", {"user_id": user_id, "report_date": report_date.isoformat(), "raw_values": raw_values, "summary": summary})
            has_cycle = profile.get("has_cycle", False) if profile else False
            sys_prompt = build_system_prompt(user_id, profile, has_cycle=has_cycle)
            check_materiality(user_id, sys_prompt, f"New lab report uploaded: {summary}")
            st.success("Lab report saved and interpreted.")
            st.rerun()

    st.markdown('<div class="sl">Saved reports</div>', unsafe_allow_html=True)
    labs = db_get("lab_reports", user_id, order_col="report_date")
    if not labs:
        st.caption("No lab reports yet.")
    for l in labs:
        try:
            days_old = (date.today() - date.fromisoformat(l["report_date"])).days
            freshness = "✓ Current" if days_old <= 90 else ("Recent" if days_old <= 180 else "Historical")
        except Exception:
            freshness = "—"
        lc1, lc2, lc3 = st.columns([3, 1, 1])
        lc1.markdown(f"**{l.get('report_date','')}** — {l.get('summary','')[:100]}")
        lc2.markdown(f"`{freshness}`")
        if lc3.button("Delete", key=f"del_lab_{l['id']}"):
            db_delete("lab_reports", l["id"])
            st.rerun()


def show_profile_wearable(user_id, profile):
    wearable = db_get("wearable_data", user_id, order_col="data_date", limit=90)
    if wearable:
        last_sync = wearable[0].get("data_date", "—")
        st.caption(f"Last data point: {last_sync} · {len(wearable)} days on file")
        recent7 = wearable[:7]
        recent30 = wearable[:30]

        def avg(rows, field):
            vals = [float(r[field]) for r in rows if r.get(field) is not None]
            return round(statistics.mean(vals), 1) if vals else None

        st.markdown('<div class="sl">This week vs 30-day average</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        metrics = [("HRV", "hrv", "ms"), ("Recovery", "recovery_score", "%"), ("Sleep performance", "sleep_performance", "%")]
        for i, (lbl, field, unit) in enumerate(metrics):
            wk = avg(recent7, field)
            mo = avg(recent30, field)
            with cols[i]:
                st.markdown(f"""
<div class="wc"><div class="wc-lbl">{lbl}</div><div class="wc-val">{wk if wk is not None else '—'}{unit}</div>
<div class="wc-sub">30d avg: {mo if mo is not None else '—'}{unit}</div></div>""", unsafe_allow_html=True)
    else:
        st.caption("No wearable data imported yet.")

    st.markdown('<div class="sl">Import WHOOP CSV export</div>', unsafe_allow_html=True)
    files = st.file_uploader("Upload cycles.csv / sleep.csv / workout.csv / journal.csv", accept_multiple_files=True, type="csv")
    if files and st.button("Import files"):
        import pandas as pd
        imported = 0
        merged = {}
        for f in files:
            try:
                df = pd.read_csv(f)
            except Exception:
                continue
            date_col = find_col(df.columns, COL_MAP["date"])
            if not date_col:
                continue
            for _, row in df.iterrows():
                try:
                    d = str(row[date_col])[:10]
                except Exception:
                    continue
                merged.setdefault(d, {"user_id": user_id, "data_date": d})
                for field in ["recovery_score", "hrv", "resting_hr", "strain", "sleep_performance", "sleep_efficiency", "sleep_duration"]:
                    col = find_col(df.columns, COL_MAP[field])
                    if col and col in row and pd.notna(row[col]):
                        merged[d][field] = float(row[col])
        for d, rec in merged.items():
            db_upsert("wearable_data", rec)
            imported += 1
        st.success(f"Imported {imported} days of data.")
        st.rerun()

    with st.expander("Manual entry"):
        m_date = st.date_input("Date", value=date.today(), key="manual_w_date")
        c1, c2, c3 = st.columns(3)
        hrv = c1.number_input("HRV (ms)", 0, 200, 50, key="manual_hrv")
        recovery = c2.number_input("Recovery (%)", 0, 100, 60, key="manual_rec")
        sleep_perf = c3.number_input("Sleep performance (%)", 0, 100, 75, key="manual_sleep")
        if st.button("Save manual entry"):
            db_upsert("wearable_data", {"user_id": user_id, "data_date": m_date.isoformat(), "hrv": hrv, "recovery_score": recovery, "sleep_performance": sleep_perf})
            st.success("Saved.")
            st.rerun()


# ── Main Entry Point ──────────────────────────────────────────────────────────
def main():
    if "user_id" not in st.session_state:
        st.session_state.auth_mode = st.session_state.get("auth_mode", "login")
        show_auth()
        return

    user_id = st.session_state.user_id
    profile = db_get_single("profiles", user_id)

    if not profile or not profile.get("onboarding_complete"):
        inject_css(auth_mode=False)
        show_onboarding(user_id, profile)
        return

    inject_css(auth_mode=False)
    show_sidebar(user_id, profile)

    page = st.session_state.get("page", "home")
    if page == "home":
        show_home(user_id, profile)
    elif page == "protocol":
        show_protocol(user_id, profile)
    elif page == "checkin":
        show_checkin(user_id, profile)
    elif page == "coach":
        show_coach(user_id, profile)
    elif page == "profile":
        show_profile(user_id, profile)


if __name__ == "__main__":
    main()

