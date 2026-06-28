"""
OneSattva — Health, understood.
Clean rewrite · June 2026
Stack: Streamlit / Supabase / Anthropic Claude Sonnet / Resend / GitHub / Streamlit Cloud
Supabase project: fxzqxovsisdbfgixnjgj — profiles table uses `id` (not user_id) as PK
Authoritative base: git commit 52639fa
"""

import streamlit as st
import anthropic
import json as _json
import statistics
from datetime import date, datetime, timedelta
import pandas as pd
from supabase import create_client, Client

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="OneSattva — Health, understood.",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
              "<circle cx='50' cy='50' r='42' fill='%23B6744A'/></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bone:     #F7F5F2;
  --graphite: #111214;
  --copper:   #B6744A;
  --stone:    #E6E3DF;
  --forest:   #1F2F2A;
  --white:    #FFFFFF;
  --mid:      #6B6358;
  --line:     rgba(17,18,20,0.10);
}

html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, sans-serif;
}

h1, h2, h3 {
  font-family: 'Newsreader', serif !important;
  color: var(--graphite) !important;
  font-weight: 500 !important;
}
h1 {
  font-size: 2rem !important;
  border-bottom: 1px solid var(--line);
  padding-bottom: 10px;
  margin-bottom: 1.1rem !important;
}

.stApp { background-color: var(--bone); }

/* ── Sidebar ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] { background-color: var(--graphite); }
[data-testid="stSidebar"] * { color: var(--bone) !important; }
[data-testid="stSidebar"] hr { border-color: rgba(247,245,242,0.10) !important; }

/* Sidebar nav buttons */
[data-testid="stSidebar"] [data-testid="stButton"] > button {
  background: transparent !important;
  border: none !important;
  border-radius: 8px !important;
  color: rgba(247,245,242,0.60) !important;
  font-family: Inter, sans-serif !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  text-align: left !important;
  padding: 9px 12px !important;
  margin-bottom: 2px !important;
  transition: background 0.12s ease !important;
  width: 100% !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
  background: rgba(247,245,242,0.08) !important;
  color: #F7F5F2 !important;
}

/* ── Main buttons ─────────────────────────────────────────────── */
.stButton > button {
  border-radius: 10px;
  border: 1.5px solid var(--line);
  color: var(--graphite);
  background-color: var(--white);
  font-weight: 500;
  font-family: 'Inter', sans-serif;
  transition: all 0.15s ease;
}
.stButton > button:hover {
  background-color: var(--graphite);
  color: var(--bone);
  border-color: var(--graphite);
}
.stButton > button[kind="primary"] {
  background-color: var(--graphite);
  border-color: var(--graphite);
  color: var(--bone);
}
.stButton > button[kind="primary"]:hover {
  background-color: var(--forest);
  border-color: var(--forest);
}

/* ── Tabs ─────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  gap: 4px;
  background-color: var(--stone);
  padding: 5px;
  border-radius: 10px;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 7px;
  color: var(--mid);
  font-weight: 500;
  padding: 9px 16px;
  font-family: 'Inter', sans-serif;
  font-size: 13px;
}
.stTabs [aria-selected="true"] {
  background-color: var(--white) !important;
  color: var(--graphite) !important;
  box-shadow: 0 1px 4px rgba(17,18,20,0.08);
}

/* ── Metrics ─────────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background-color: var(--white);
  padding: 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
}
[data-testid="stMetricLabel"] { color: var(--mid) !important; font-family: 'Inter', sans-serif; }
[data-testid="stMetricValue"] { color: var(--graphite) !important; font-family: 'JetBrains Mono', monospace !important; }

/* ── Chat ────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
  background-color: var(--white);
  border-radius: 12px;
  border: 1px solid var(--line);
}

/* ── Alerts & dividers ────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 10px; border-left-width: 3px; }
hr { border-color: var(--line) !important; margin: 1.4rem 0 !important; }

/* ── Triage pills ─────────────────────────────────────────────── */
.triage-now {
  background: rgba(182,116,74,0.12); color: #B6744A;
  border: 1px solid rgba(182,116,74,0.35); border-radius: 20px;
  padding: 4px 13px; font-family: Inter, sans-serif;
  font-size: 12px; font-weight: 500; display: inline-block;
}
.triage-watch {
  background: rgba(230,227,223,0.45); color: #6B6358;
  border: 1px solid rgba(230,227,223,0.80); border-radius: 20px;
  padding: 4px 13px; font-family: Inter, sans-serif;
  font-size: 12px; display: inline-block;
}
.triage-background {
  background: transparent; color: #6B6358;
  font-family: Inter, sans-serif; font-size: 12px;
  font-style: italic; display: inline-block;
}

/* ── Data / lab values ────────────────────────────────────────── */
.lab-value { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--graphite); }

/* ── Section label ────────────────────────────────────────────── */
.sec-label {
  font-family: Inter, sans-serif; font-size: 10.5px; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--mid);
  margin: 0 0 10px;
}

/* ── Insight strip ────────────────────────────────────────────── */
.insight-strip {
  background: var(--bone); border-left: 3px solid var(--copper);
  border-radius: 0 10px 10px 0; padding: 14px 18px;
}

input, textarea, select { font-family: 'Inter', sans-serif !important; }
.stDataFrame { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--mid) !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SVG ASSETS
# ══════════════════════════════════════════════════════════════════════════════

# Primary mark — dark backgrounds (Graphite / Forest)
_MARK_DARK = """<svg width="28" height="28" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <defs><radialGradient id="gd" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#B1643A"/>
    <stop offset="40%" stop-color="#B1643A"/>
    <stop offset="54%" stop-color="#BE7C58" stop-opacity="0.72"/>
    <stop offset="70%" stop-color="#D2A084" stop-opacity="0.4"/>
    <stop offset="86%" stop-color="#E6CCB8" stop-opacity="0.14"/>
    <stop offset="100%" stop-color="#E6CCB8" stop-opacity="0"/>
  </radialGradient></defs>
  <circle cx="50" cy="50" r="47" fill="none" stroke="#F7F5F2" stroke-width="1.4"/>
  <circle cx="50" cy="50" r="42" fill="none" stroke="#F7F5F2" stroke-width="1.4"/>
  <circle cx="50" cy="50" r="35" fill="none" stroke="#F7F5F2" stroke-width="1.4"/>
  <circle cx="50" cy="50" r="30" fill="none" stroke="#B6744A" stroke-width="1.7"/>
  <circle cx="50" cy="50" r="25" fill="none" stroke="#B6744A" stroke-width="1.7"/>
  <circle cx="50" cy="50" r="20" fill="none" stroke="#B6744A" stroke-width="1.7"/>
  <circle cx="50" cy="50" r="16" fill="url(#gd)"/>
</svg>"""

# Secondary mark — light backgrounds (Bone / Stone)
_MARK_LIGHT = """<svg width="64" height="64" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <defs><radialGradient id="gl" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#B1643A"/>
    <stop offset="40%" stop-color="#B1643A"/>
    <stop offset="54%" stop-color="#BE7C58" stop-opacity="0.72"/>
    <stop offset="70%" stop-color="#D2A084" stop-opacity="0.4"/>
    <stop offset="86%" stop-color="#E6CCB8" stop-opacity="0.14"/>
    <stop offset="100%" stop-color="#E6CCB8" stop-opacity="0"/>
  </radialGradient></defs>
  <circle cx="50" cy="50" r="47" fill="none" stroke="#111214" stroke-width="1.4" opacity="0.18"/>
  <circle cx="50" cy="50" r="42" fill="none" stroke="#111214" stroke-width="1.4" opacity="0.28"/>
  <circle cx="50" cy="50" r="35" fill="none" stroke="#111214" stroke-width="1.4" opacity="0.40"/>
  <circle cx="50" cy="50" r="30" fill="none" stroke="#B6744A" stroke-width="1.7" opacity="0.65"/>
  <circle cx="50" cy="50" r="25" fill="none" stroke="#B6744A" stroke-width="1.7" opacity="0.80"/>
  <circle cx="50" cy="50" r="20" fill="none" stroke="#B6744A" stroke-width="1.7"/>
  <circle cx="50" cy="50" r="16" fill="url(#gl)"/>
</svg>"""

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG / CLIENTS
# ══════════════════════════════════════════════════════════════════════════════

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ANTHROPIC_KEY = st.secrets["ANTHROPIC_KEY"]


@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@st.cache_resource
def get_anthropic():
    return anthropic.Anthropic(api_key=ANTHROPIC_KEY)


supabase = get_supabase()
ai_client = get_anthropic()

# ══════════════════════════════════════════════════════════════════════════════
# AUTH HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def sign_up(email, password, full_name):
    try:
        res = supabase.auth.sign_up({
            "email": email, "password": password,
            "options": {"data": {"full_name": full_name}},
        })
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

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

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
    """profiles uses `id` as PK; everything else uses `user_id`."""
    try:
        key_col = "id" if table == "profiles" else "user_id"
        res = supabase.table(table).select("*").eq(key_col, user_id).limit(1).execute()
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

# ══════════════════════════════════════════════════════════════════════════════
# CYCLE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def calculate_cycle_status(user_id):
    cd = db_get_single("cycle_data", user_id)
    if not cd or not cd.get("last_period_start"):
        return None, None, None
    try:
        last_start = datetime.strptime(cd["last_period_start"], "%Y-%m-%d").date()
        avg_len = cd.get("avg_cycle_length", 27)
        today = date.today()
        cycle_day = (today - last_start).days + 1
        while cycle_day > avg_len:
            cycle_day -= avg_len
        days_until_next = avg_len - cycle_day + 1
        if cycle_day <= 5:
            phase = "Menstruation (Day 1–5)"
        elif cycle_day <= 13:
            phase = "Follicular (Day 1–14)"
        elif cycle_day <= 16:
            phase = "Ovulation (Day 14–16)"
        else:
            phase = "Luteal (Day 16–28)"
        return cycle_day, phase, days_until_next
    except Exception:
        return None, None, None

# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_system_prompt(user_id, profile):
    today = date.today()
    three_months_ago = today - timedelta(days=90)

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

    # Patient profile
    if profile:
        name = profile.get("full_name", "the patient")
        base += "\n═══════════════════════════════════════════════════════\nPATIENT PROFILE\n═══════════════════════════════════════════════════════\n"
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

    # Goals
    goals = db_get("goals", user_id)
    if goals:
        base += "\n\nGOALS:\n"
        for g in goals:
            tf = f" [{g['timeframe']}]" if g.get("timeframe") else ""
            base += f"- {g['goal']}{tf}\n"

    # Medical history
    conditions = db_get("medical_history", user_id)
    if conditions:
        base += "\nMEDICAL CONDITIONS:\n"
        for c in conditions:
            base += f"- {c['condition']}: {c.get('notes','')}\n"

    # Medications
    meds = db_get("medications", user_id)
    active_meds = [m for m in meds if m.get("active", True)]
    if active_meds:
        base += "\nCURRENT MEDICATIONS:\n"
        for m in active_meds:
            base += f"- {m['name']} {m.get('dose','')} {m.get('frequency','')}\n"

    # Supplements
    supps = db_get("supplements", user_id)
    active_supps = [s for s in supps if s.get("active", True)]
    if active_supps:
        base += "\nCURRENT SUPPLEMENTS:\n"
        for s in active_supps:
            base += f"- {s['name']} {s.get('dose','')} ({s.get('timing','')})\n"

    # Profile notes
    notes = db_get_single("profile_notes", user_id)
    if notes and notes.get("notes"):
        base += f"\nPROFILE UPDATES / RECENT CHANGES:\n{notes['notes']}\n"

    # Lab reports with freshness classification
    labs = db_get("lab_reports", user_id, order_col="report_date", limit=10)
    if labs:
        base += "\n═══════════════════════════════════════════════════════\nLAB REPORTS\n═══════════════════════════════════════════════════════\n"
        current_labs, historical_labs = [], []
        for l in labs:
            try:
                rep_date = date.fromisoformat(l.get("report_date", ""))
                (current_labs if rep_date >= three_months_ago else historical_labs).append(l)
            except Exception:
                historical_labs.append(l)

        if current_labs:
            base += "CURRENT LABS (within last 3 months — use as primary reference):\n"
            for l in current_labs:
                base += f"- {l.get('report_date','')}: {l.get('summary','')} | Raw: {l.get('raw_values','')[:300]}\n"
        else:
            base += "⚠️ NO CURRENT LABS (all reports older than 3 months). Flag this to the patient — do not treat old values as current status.\n"

        if historical_labs:
            base += "\nHISTORICAL LABS (older than 3 months — use for trend analysis only):\n"
            for l in historical_labs:
                base += f"- {l.get('report_date','')}: {l.get('summary','')}\n"
    else:
        base += "\n⚠️ NO LAB REPORTS UPLOADED. Recommendations will be general until labs are provided. Remind the patient that labs are needed for a precise protocol.\n"

    # Wearable data with freshness classification
    wearable_all = db_get("wearable_data", user_id, order_col="data_date", limit=90)
    if wearable_all:
        base += "\n═══════════════════════════════════════════════════════\nWEARABLE DATA\n═══════════════════════════════════════════════════════\n"
        seven_ago = today - timedelta(days=7)
        thirty_ago = today - timedelta(days=30)
        current_w, recent_w = [], []
        for w in wearable_all:
            try:
                wd = date.fromisoformat(w.get("data_date", ""))
                if wd >= seven_ago:
                    current_w.append(w)
                elif wd >= thirty_ago:
                    recent_w.append(w)
            except Exception:
                pass

        def fmt_wearable(w):
            parts = [w.get("data_date", "")]
            for f in ["recovery_score", "hrv", "resting_hr", "strain", "sleep_performance"]:
                if w.get(f) is not None:
                    parts.append(f"{f.replace('_',' ')}: {w[f]}")
            return " | ".join(parts)

        if current_w:
            base += "CURRENT (last 7 days):\n" + "\n".join([f"- {fmt_wearable(w)}" for w in reversed(current_w)]) + "\n"
        if recent_w:
            def avg_field(rows, field):
                vals = [float(r[field]) for r in rows if r.get(field) is not None]
                return round(statistics.mean(vals), 1) if vals else None
            r_avg = {f: avg_field(recent_w, f) for f in ["recovery_score", "hrv", "resting_hr", "strain", "sleep_performance"]}
            r_str = " | ".join([f"{k.replace('_',' ')}: {v}" for k, v in r_avg.items() if v is not None])
            base += f"RECENT AVERAGE (last 30 days, {len(recent_w)} days of data): {r_str}\n"
        if not current_w and not recent_w:
            base += "⚠️ No recent wearable data. Cannot assess current recovery or readiness.\n"

    # Check-ins with gap detection
    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=14)
    if checkins:
        latest_checkin = checkins[0]
        try:
            latest_date = date.fromisoformat(latest_checkin.get("checkin_date", ""))
            gap_days = (today - latest_date).days
        except Exception:
            gap_days = 0

        base += "\n═══════════════════════════════════════════════════════\nCHECK-IN DATA\n═══════════════════════════════════════════════════════\n"

        if gap_days >= 14:
            base += f"⚠️ GAP ALERT: Last check-in was {gap_days} days ago. Do NOT continue with the old protocol. First, ask a re-entry question: 'It's been {gap_days} days since your last log. Has anything changed — symptoms, medications, energy, how you're feeling overall?' Then reassess before resuming.\n"
        elif gap_days >= 7:
            base += f"⚠️ CHECK-IN GAP: {gap_days} days since last log. Before giving recommendations, ask: 'It's been {gap_days} days — anything changed recently?' One question only.\n"
        elif gap_days >= 3:
            base += f"Note: {gap_days}-day gap in check-ins. Continue with protocol but note the gap.\n"

        base += "RECENT CHECK-INS (last 14 days):\n"
        for c in reversed(checkins[:14]):
            base += (f"- {c.get('checkin_date','')}: Energy {c.get('energy','?')}/10 · Mood {c.get('mood','?')}/10 · "
                     f"Sleep {c.get('sleep_hours','?')}hrs (quality {c.get('sleep_quality','?')}/10) · "
                     f"Bloating: {c.get('bloating','?')} · Digestion: {c.get('digestion','?')} · "
                     f"Workout: {c.get('workout','?')} · Rumination: {c.get('rumination','?')} · "
                     f"Notes: {c.get('notes','')}\n")
    else:
        base += "\nNo check-in data yet.\n"

    return base

# ══════════════════════════════════════════════════════════════════════════════
# LAB MARKERS REFERENCE
# ══════════════════════════════════════════════════════════════════════════════

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

**Extended panel — add if you have a specific concern:**
Zonulin (gut permeability) · Calprotectin · H. pylori antibody · ANA · Morning Cortisol · MTHFR · APOE

In India, Thyrocare's Aarogyam or Wellness packages cover most of the core panel at reasonable cost.
"""

# ══════════════════════════════════════════════════════════════════════════════
# AUTH SCREEN
# ══════════════════════════════════════════════════════════════════════════════

def show_auth_screen():
    st.markdown(f"""
    <div style='max-width:400px;margin:48px auto 28px;text-align:center;'>
      <div style='display:inline-flex;flex-direction:column;align-items:center;gap:8px;margin-bottom:20px;'>
        {_MARK_LIGHT}
        <span style='font-family:Newsreader,serif;font-weight:400;font-style:normal;
                     font-size:2rem;color:#111214;line-height:1;letter-spacing:-0.02em;'>
          OneSattva
        </span>
        <span style='font-family:Newsreader,serif;font-style:italic;color:#B6744A;font-size:0.95rem;'>
          Health, understood.
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_mode = st.radio("", ["Sign In", "Create Account"], horizontal=True,
                             label_visibility="collapsed")
        st.divider()

        if auth_mode == "Sign In":
            if st.session_state.get("show_forgot_password"):
                st.markdown("##### Reset your password")
                st.caption("Enter your email and we'll send a reset link.")
                reset_email = st.text_input("Email address", key="reset_email_input")
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("Send reset link", type="primary",
                                 use_container_width=True, key="send_reset_btn"):
                        if reset_email:
                            try:
                                supabase.auth.reset_password_email(
                                    reset_email,
                                    options={"redirect_to":
                                             "https://wellness-coach-app-f2ssjkdxdey8vm2c287mnz.streamlit.app"}
                                )
                                st.success("Reset link sent — check your email. Expires in 1 hour.")
                                st.session_state.show_forgot_password = False
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.warning("Please enter your email address.")
                with rc2:
                    if st.button("Back to sign in", use_container_width=True, key="back_signin_btn"):
                        st.session_state.show_forgot_password = False
                        st.rerun()
            else:
                email = st.text_input("Email", key="signin_email")
                password = st.text_input("Password", type="password", key="signin_password")
                if st.button("Sign In", use_container_width=True, type="primary", key="signin_btn"):
                    if email and password:
                        user, session, err = sign_in(email, password)
                        if err:
                            st.error(f"Sign in failed: {err}")
                        else:
                            st.session_state["user"] = user
                            st.session_state["session"] = session
                            st.session_state["access_token"] = session.access_token
                            st.rerun()
                    else:
                        st.warning("Please enter your email and password.")
                if st.button("Forgot your password?", key="forgot_pw_btn"):
                    st.session_state.show_forgot_password = True
                    st.rerun()

        else:  # Create Account
            full_name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")
            st.divider()
            st.markdown("""
<div style='background:#E6E3DF;border-radius:10px;padding:14px 16px;margin-bottom:12px;
            font-size:12px;color:#6B6358;line-height:1.6;'>
<strong style='color:#111214;display:block;margin-bottom:6px;'>
  OneSattva is a pilot wellness tool — not a medical device
</strong>
OneSattva provides AI-generated health guidance to support, not replace, qualified medical professionals.
This product is in closed pilot testing and under active development. Do not use it as the sole basis
for medical decisions. Always consult your doctor before changing medications, supplements, or treatment plans.
</div>
""", unsafe_allow_html=True)
            consent1 = st.checkbox(
                "I agree to OneSattva collecting and storing my personal health information "
                "(medical history, lab results, lifestyle data, wearable metrics) to generate "
                "personalised wellness guidance. My data is stored securely, not shared with "
                "third parties, and I can request deletion at any time.",
                key="consent_general"
            )
            consent2 = st.checkbox(
                "I explicitly consent to OneSattva collecting and processing my sensitive health "
                "data — including medical conditions, medications, lab reports, and biometric "
                "information — for personalised wellness recommendations. I understand I am "
                "participating in a closed pilot under active development.",
                key="consent_health"
            )
            st.divider()
            if st.button("Create Account", use_container_width=True, type="primary", key="signup_btn"):
                if not full_name or not email or not password:
                    st.warning("Please fill in all fields.")
                elif not consent1:
                    st.error("Please agree to the data collection terms to continue.")
                elif not consent2:
                    st.error("Please provide explicit consent for health data processing.")
                else:
                    user, err = sign_up(email, password, full_name)
                    if err:
                        st.error(f"Sign up failed: {err}")
                    else:
                        st.success("Account created! Check your email for a verification link, then sign in.")

# ══════════════════════════════════════════════════════════════════════════════
# ONBOARDING HELPERS
# ══════════════════════════════════════════════════════════════════════════════

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


def calculate_completeness(user_id, ob_state):
    score = 0
    if ob_state and ob_state.get("step2_done"):
        score += 25
    if ob_state and ob_state.get("step3_done"):
        score += 25
    if ob_state and ob_state.get("step4_done"):
        score += 25
    if db_get("lab_reports", user_id):
        score += 25
    elif ob_state and ob_state.get("lab_upload_acknowledged"):
        score += 10
    return score

# ══════════════════════════════════════════════════════════════════════════════
# ONBOARDING WIZARD
# ══════════════════════════════════════════════════════════════════════════════

OB_STEPS = ["Your plan", "About you", "Health history", "Lifestyle & goals", "Data sources"]


def _ob_progress_html(current):
    html = "<div style='display:flex;align-items:center;margin-bottom:22px;'>"
    for i, label in enumerate(OB_STEPS):
        n = i + 1
        is_done = n < current
        is_curr = n == current
        dot_bg = "#1F2F2A" if is_done else ("#111214" if is_curr else "var(--bone)")
        dot_col = "#F7F5F2" if (is_done or is_curr) else "var(--mid)"
        dot_border = "#1F2F2A" if is_done else ("#111214" if is_curr else "rgba(17,18,20,0.18)")
        dot_txt = "✓" if is_done else str(n)
        lbl_col = "var(--graphite)" if is_curr else "var(--mid)"
        lbl_wt = "500" if is_curr else "400"
        html += f"""
          <div style='display:flex;align-items:center;gap:6px;'>
            <div style='width:27px;height:27px;border-radius:50%;background:{dot_bg};
                        border:2px solid {dot_border};display:flex;align-items:center;
                        justify-content:center;font-size:11px;font-weight:600;
                        color:{dot_col};flex-shrink:0;'>{dot_txt}</div>
            <span style='font-family:Inter,sans-serif;font-size:11px;color:{lbl_col};
                         font-weight:{lbl_wt};white-space:nowrap;'>{label}</span>
          </div>"""
        if i < len(OB_STEPS) - 1:
            conn_bg = "#1F2F2A" if is_done else "rgba(17,18,20,0.12)"
            html += f"<div style='flex:1;height:1px;background:{conn_bg};margin:0 6px;'></div>"
    html += "</div>"
    return html


def _ob_title_html(title, subtitle=""):
    sub = (f"<div style='font-family:Inter,sans-serif;font-size:13px;color:var(--mid);"
           f"line-height:1.5;margin-top:4px;'>{subtitle}</div>") if subtitle else ""
    return (f"<div style='margin-bottom:20px;'>"
            f"<div style='font-family:Newsreader,serif;font-size:1.4rem;color:var(--graphite);"
            f"font-weight:400;line-height:1.2;'>{title}</div>{sub}</div>")


def show_onboarding(user):
    user_id = user.id
    ob = get_onboarding_state(user_id)
    if not ob:
        save_onboarding_state(user_id, {"current_step": 1})
        ob = get_onboarding_state(user_id)

    profile = db_get_single("profiles", user_id)
    current_step = ob.get("current_step", 1) if ob else 1

    col_main, col_r = st.columns([10, 3])
    with col_main:

        # ── STEP 1 — Your plan ────────────────────────────────────────────────
        if current_step == 1:
            st.markdown(_ob_progress_html(1), unsafe_allow_html=True)
            st.markdown(_ob_title_html(
                "What are you here for?",
                "Choose your plan mode. This shapes how your coach works with you. "
                "You can change it at any time from Profile & Data."
            ), unsafe_allow_html=True)

            PLAN_MODES = [
                ("Restore", "90-day programme",
                 "Hormonal reset, gut repair, thyroid optimisation, fatigue resolution. "
                 "Structured 13-week phases with checkpoints."),
                ("Optimise", "Ongoing",
                 "You're in good health and want to stay ahead. Performance, longevity, "
                 "cycle optimisation, cognitive sharpness."),
                ("Targeted", "Condition-specific",
                 "One primary condition driving everything — PCOS, IBS, hypothyroidism, fertility. "
                 "Laser-focused protocol."),
                ("Maintain", "Ongoing",
                 "Your roadmap is done. Monthly check-ins, protocol maintenance, wearable monitoring."),
            ]

            saved_plan = ob.get("plan_mode", "") if ob else ""
            selected_plan = st.session_state.get("ob_plan_select", saved_plan)

            mc1, mc2 = st.columns(2)
            for i, (key, sub, desc) in enumerate(PLAN_MODES):
                col = mc1 if i % 2 == 0 else mc2
                is_sel = selected_plan == key
                border = "2px solid #111214" if is_sel else "1px solid rgba(17,18,20,0.12)"
                bg = "#FFFFFF" if is_sel else "var(--bone)"
                check_html = ("<div style='position:absolute;top:12px;right:12px;width:18px;height:18px;"
                              "border-radius:50%;background:#111214;display:flex;align-items:center;"
                              "justify-content:center;color:#fff;font-size:10px;'>✓</div>") if is_sel else ""
                with col:
                    st.markdown(f"""
                    <div style='background:{bg};border:{border};border-radius:12px;
                                padding:16px;margin-bottom:10px;position:relative;cursor:pointer;'>
                      {check_html}
                      <div style='font-size:10px;font-weight:600;letter-spacing:0.07em;
                                  text-transform:uppercase;color:var(--mid);margin-bottom:4px;'>{sub}</div>
                      <div style='font-family:Newsreader,serif;font-size:19px;
                                  color:var(--graphite);margin-bottom:2px;'>{key}</div>
                      <div style='font-size:12px;color:var(--mid);line-height:1.55;'>{desc}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Select {key}", key=f"plan_{key}", use_container_width=True):
                        st.session_state.ob_plan_select = key
                        st.rerun()

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            if st.button("Continue →", type="primary", use_container_width=True, key="ob_plan_next"):
                plan_choice = st.session_state.get("ob_plan_select", "")
                if not plan_choice:
                    st.error("Please select a plan mode to continue.")
                else:
                    save_onboarding_state(user_id, {"current_step": 2, "plan_mode": plan_choice})
                    st.rerun()

        # ── STEP 2 — About you ────────────────────────────────────────────────
        elif current_step == 2:
            st.markdown(_ob_progress_html(2), unsafe_allow_html=True)
            st.markdown(_ob_title_html(
                "Tell us about yourself",
                "This personalises everything. You can edit any of this from Profile & Data at any time."
            ), unsafe_allow_html=True)

            with st.form("ob_step2"):
                c1, c2 = st.columns(2)
                with c1:
                    p_name = st.text_input("Full name *", value=profile.get("full_name", "") if profile else "")
                    p_dob_val = profile.get("date_of_birth") if profile else None
                    p_dob = st.date_input("Date of birth *",
                        value=date.fromisoformat(p_dob_val) if p_dob_val else date(1990, 1, 1),
                        min_value=date(1940, 1, 1), max_value=date.today())
                    p_sex = st.selectbox("Sex assigned at birth *", ["", "Female", "Male", "Intersex"],
                        index=["", "Female", "Male", "Intersex"].index(profile.get("sex", ""))
                        if profile and profile.get("sex", "") in ["Female", "Male", "Intersex"] else 0)
                    p_blood = st.selectbox("Blood group",
                        ["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"],
                        index=["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"].index(
                            profile.get("blood_group", ""))
                        if profile and profile.get("blood_group", "") in
                        ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"] else 0)
                with c2:
                    p_height = st.number_input("Height (cm) *", 100, 220,
                        value=int(profile.get("height_cm", 165)) if profile and profile.get("height_cm") else 165)
                    p_weight = st.number_input("Weight (kg) *", 30, 200,
                        value=int(profile.get("weight_kg", 60)) if profile and profile.get("weight_kg") else 60)
                    p_location = st.text_input("City / Location *",
                        value=profile.get("location", "") if profile else "")
                    p_diet = st.selectbox("Diet *", [
                        "Vegetarian (no eggs)", "Vegetarian (with eggs)",
                        "Non-vegetarian", "Vegan", "Pescatarian"])

                lc1, lc2, lc3 = st.columns(3)
                with lc1:
                    p_alcohol = st.selectbox("Alcohol", ["None", "Occasional", "Weekly", "Daily"])
                with lc2:
                    p_smoking = st.selectbox("Smoking / Vaping", ["None", "Occasional", "Daily"])
                with lc3:
                    p_allergies = st.text_input("Known allergies", placeholder="e.g. gluten, nuts")

                if st.form_submit_button("Save & Continue →", type="primary", use_container_width=True):
                    if not p_name or not p_sex or not p_location:
                        st.error("Please fill in all required fields marked with *")
                    else:
                        age = (date.today() - p_dob).days // 365
                        db_upsert("profiles", {
                            "id": user_id, "full_name": p_name, "age": age,
                            "date_of_birth": p_dob.isoformat(), "sex": p_sex,
                            "height_cm": p_height, "weight_kg": p_weight,
                            "location": p_location, "diet": p_diet, "blood_group": p_blood,
                            "alcohol": p_alcohol, "smoking": p_smoking, "allergies": p_allergies,
                        })
                        save_onboarding_state(user_id, {"current_step": 3, "step2_done": True})
                        st.rerun()

        # ── STEP 3 — Health history ───────────────────────────────────────────
        elif current_step == 3:
            st.markdown(_ob_progress_html(3), unsafe_allow_html=True)
            st.markdown(_ob_title_html(
                "Your health history",
                "Medical conditions, medications, and supplements. Share what you're comfortable with."
            ), unsafe_allow_html=True)

            st.markdown("##### Medical conditions & challenges")
            conditions = db_get("medical_history", user_id)
            for c in conditions:
                cc1, cc2 = st.columns([5, 1])
                cc1.write(f"**{c['condition']}** — {c.get('notes','')[:60]}")
                if cc2.button("✕", key=f"dc_{c['id']}"):
                    db_delete("medical_history", c["id"]); st.rerun()
            with st.form("add_cond_ob"):
                nc1, nc2 = st.columns([3, 2])
                with nc1:
                    new_cond = st.text_input("Condition or challenge", placeholder="e.g. Hypothyroidism, PCOS")
                with nc2:
                    new_cond_notes = st.text_input("Notes", placeholder="e.g. diagnosed 2020")
                if st.form_submit_button("+ Add") and new_cond:
                    db_upsert("medical_history", {"user_id": user_id, "condition": new_cond,
                                                  "notes": new_cond_notes})
                    st.rerun()

            st.divider()
            st.markdown("##### Current medications")
            meds = db_get("medications", user_id)
            for m in meds:
                mc1, mc2 = st.columns([5, 1])
                mc1.write(f"**{m['name']}** — {m.get('dose','')} {m.get('frequency','')}")
                if mc2.button("✕", key=f"dm_{m['id']}"):
                    db_delete("medications", m["id"]); st.rerun()
            with st.form("add_med_ob"):
                mm1, mm2, mm3 = st.columns(3)
                with mm1:
                    new_med = st.text_input("Medication", placeholder="e.g. Thyronorm")
                with mm2:
                    new_dose = st.text_input("Dose", placeholder="e.g. 50mcg")
                with mm3:
                    new_freq = st.text_input("Frequency", placeholder="e.g. Daily on waking")
                if st.form_submit_button("+ Add medication") and new_med:
                    db_upsert("medications", {"user_id": user_id, "name": new_med,
                                              "dose": new_dose, "frequency": new_freq, "active": True})
                    st.rerun()

            st.divider()
            st.markdown("##### Current supplements")
            supps = db_get("supplements", user_id)
            for s in supps:
                sc1, sc2 = st.columns([5, 1])
                sc1.write(f"**{s['name']}** — {s.get('dose','')} ({s.get('timing','')})")
                if sc2.button("✕", key=f"ds_{s['id']}"):
                    db_delete("supplements", s["id"]); st.rerun()
            with st.form("add_supp_ob"):
                ss1, ss2, ss3 = st.columns(3)
                with ss1:
                    new_supp = st.text_input("Supplement", placeholder="e.g. Magnesium Glycinate")
                with ss2:
                    new_sdose = st.text_input("Dose", placeholder="e.g. 400mg")
                with ss3:
                    new_stiming = st.text_input("Timing", placeholder="e.g. Before bed")
                if st.form_submit_button("+ Add supplement") and new_supp:
                    db_upsert("supplements", {"user_id": user_id, "name": new_supp,
                                              "dose": new_sdose, "timing": new_stiming, "active": True})
                    st.rerun()

            st.divider()
            nav1, nav2 = st.columns(2)
            with nav1:
                if st.button("← Back", use_container_width=True, key="ob3_back"):
                    save_onboarding_state(user_id, {"current_step": 2}); st.rerun()
            with nav2:
                if st.button("Save & Continue →", type="primary", use_container_width=True, key="ob3_next"):
                    save_onboarding_state(user_id, {"current_step": 4, "step3_done": True}); st.rerun()

        # ── STEP 4 — Lifestyle & goals ────────────────────────────────────────
        elif current_step == 4:
            st.markdown(_ob_progress_html(4), unsafe_allow_html=True)
            st.markdown(_ob_title_html(
                "Lifestyle & goals",
                "Daily routine, sleep, exercise, and what you want to achieve."
            ), unsafe_allow_html=True)

            with st.form("ob_step4_schedule"):
                st.markdown("##### Daily schedule")
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    wake_time = st.text_input("Wake time",
                        value=profile.get("wake_time", "7:00 AM") if profile and profile.get("wake_time") else "7:00 AM")
                with sc2:
                    first_meal = st.text_input("First meal", placeholder="e.g. 9:00 AM")
                with sc3:
                    sleep_time = st.text_input("Bedtime target",
                        value=profile.get("sleep_time", "10:30 PM") if profile and profile.get("sleep_time") else "10:30 PM")

                st.markdown("##### Exercise")
                ex1, ex2 = st.columns(2)
                with ex1:
                    workout_freq = st.selectbox("How often?",
                        ["Not currently", "1-2x per week", "3-4x per week", "5+ per week"])
                    workout_types = st.multiselect("Types",
                        ["Strength training", "Cardio", "Yoga/Pilates", "Swimming",
                         "Cycling", "Team sports", "Walking", "Other"])
                with ex2:
                    workout_time = st.text_input("Preferred time", placeholder="e.g. 7:00 AM")
                    sleep_hours = st.number_input("Average sleep (hrs)", 3.0, 12.0, 7.0, step=0.5)

                if st.form_submit_button("Save schedule", use_container_width=True):
                    notes_val = (f"Wake: {wake_time} | First meal: {first_meal} | Bedtime: {sleep_time} | "
                                 f"Exercise: {workout_freq}, {', '.join(workout_types)}, at {workout_time} | "
                                 f"Sleep: {sleep_hours}hrs")
                    db_upsert("profiles", {"id": user_id, "wake_time": wake_time, "sleep_time": sleep_time})
                    db_upsert("profile_notes", {"user_id": user_id, "notes": notes_val})
                    st.success("Schedule saved!")

            st.markdown("##### Goals")
            st.caption("Be specific. 'Lose weight' is less useful than 'reach 58kg and reduce belly fat by September.'")
            goals_list = db_get("goals", user_id)
            for g in goals_list:
                gc1, gc2 = st.columns([5, 1])
                gc1.write(f"**{g['goal']}** · _{g.get('timeframe','')}_")
                if gc2.button("✕", key=f"dg_{g['id']}"):
                    db_delete("goals", g["id"]); st.rerun()
            with st.form("add_goal_ob"):
                gg1, gg2 = st.columns([3, 1])
                with gg1:
                    new_goal = st.text_input("Add a goal", placeholder="e.g. Resolve bloating and digestive issues")
                with gg2:
                    new_tf = st.selectbox("Timeframe", ["3 months", "6 months", "12 months", "12 months+"])
                if st.form_submit_button("+ Add goal") and new_goal:
                    db_upsert("goals", {"user_id": user_id, "goal": new_goal, "timeframe": new_tf})
                    st.rerun()

            st.markdown("##### Cycle tracking")
            st.caption("For females — this shapes your protocol around your cycle phases.")
            ob_cd = db_get_single("cycle_data", user_id)
            with st.form("cycle_ob"):
                cyc1, cyc2 = st.columns(2)
                with cyc1:
                    lp_date = st.date_input("Last period start",
                        value=date.fromisoformat(ob_cd["last_period_start"])
                        if ob_cd and ob_cd.get("last_period_start") else date.today())
                with cyc2:
                    avg_len = st.number_input("Avg cycle length (days)", 21, 40,
                        value=ob_cd.get("avg_cycle_length", 28) if ob_cd else 28)
                if st.form_submit_button("Save cycle data"):
                    db_upsert("cycle_data", {"user_id": user_id,
                                             "last_period_start": lp_date.isoformat(),
                                             "avg_cycle_length": int(avg_len)})
                    st.success("Saved!")

            st.divider()
            nav1, nav2 = st.columns(2)
            with nav1:
                if st.button("← Back", use_container_width=True, key="ob4_back"):
                    save_onboarding_state(user_id, {"current_step": 3}); st.rerun()
            with nav2:
                if st.button("Save & Continue →", type="primary", use_container_width=True, key="ob4_next"):
                    save_onboarding_state(user_id, {"current_step": 5, "step4_done": True}); st.rerun()

        # ── STEP 5 — Data sources ─────────────────────────────────────────────
        elif current_step == 5:
            st.markdown(_ob_progress_html(5), unsafe_allow_html=True)
            st.markdown(_ob_title_html(
                "Lab reports & data sources",
                "Lab reports are the foundation of your treatment roadmap. "
                "Upload what you have — even a partial report helps."
            ), unsafe_allow_html=True)

            st.info("Lab reports are required for a precise treatment roadmap. "
                    "Upload what you have — even a partial panel helps significantly.")

            with st.expander("📋 Recommended markers — what to get tested", expanded=False):
                st.markdown(MARKERS_INFO)

            existing_labs = db_get("lab_reports", user_id, order_col="report_date")
            if existing_labs:
                st.success(f"✅ {len(existing_labs)} report(s) uploaded.")
                for lab in existing_labs:
                    st.markdown(f"- **{lab['report_date']}** · {lab.get('lab_name','')} · "
                                f"{lab.get('summary','')[:80]}")
                st.divider()

            st.markdown("##### Upload a report")
            ob_lab_date = st.date_input("Report date", value=date.today(), key="ob_ld")
            ob_lab_name = st.text_input("Lab name", placeholder="e.g. Thyrocare, SRL, Apollo", key="ob_ln")
            ob_lab_vals = st.text_area("Paste lab values", height=180, key="ob_lv",
                placeholder="TSH: 2.1\nFT3: 2.8\nFT4: 1.2\nProlactin: 18.5\nFerritin: 42\nVitamin D: 38\n...")

            if st.button("🔍 Analyse & Save", type="primary", use_container_width=True, key="ob_lab_save"):
                if ob_lab_vals.strip():
                    with st.spinner("Analysing against functional medicine ranges..."):
                        try:
                            resp = ai_client.messages.create(
                                model="claude-sonnet-4-6", max_tokens=2000,
                                system="You are an expert integrative medicine practitioner. "
                                       "Analyse lab values against functional medicine optimal ranges. "
                                       "Be direct, specific, and concise.",
                                messages=[{"role": "user", "content":
                                    f"Lab report {ob_lab_date}, lab: {ob_lab_name}\n\nValues:\n{ob_lab_vals}\n\n"
                                    "Analyse against functional ranges. Format:\n"
                                    "## Key Findings\nTable: Marker | Value | Functional Status | Priority\n\n"
                                    "## Summary\n2-3 sentences on overall picture\n\n"
                                    "## Most Urgent\nTop 2-3 priorities"}]
                            )
                            st.divider()
                            st.markdown(resp.content[0].text)
                            sum_resp = ai_client.messages.create(
                                model="claude-sonnet-4-6", max_tokens=150,
                                messages=[{"role": "user",
                                           "content": f"One line summary max 120 chars: {ob_lab_vals}"}]
                            )
                            db_upsert("lab_reports", {
                                "user_id": user_id, "report_date": ob_lab_date.isoformat(),
                                "lab_name": ob_lab_name, "raw_values": ob_lab_vals,
                                "summary": sum_resp.content[0].text[:500],
                            })
                            save_onboarding_state(user_id, {"step5_done": True, "lab_upload_acknowledged": True})
                            st.success("✅ Saved.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Paste your lab values above.")

            st.divider()
            ob_fresh = get_onboarding_state(user_id)
            has_labs = bool(existing_labs)
            acknowledged = ob_fresh and ob_fresh.get("lab_upload_acknowledged")

            if not has_labs:
                st.markdown("**Don't have reports yet?**")
                st.caption("You can continue — your roadmap will be provisional for 2 weeks while you arrange testing.")
                if st.button("I'll upload labs within 2 weeks — continue",
                             use_container_width=True, key="ob_lab_ack"):
                    save_onboarding_state(user_id, {
                        "current_step": 6, "step5_done": True,
                        "lab_upload_acknowledged": True,
                        "lab_acknowledged_at": datetime.now().isoformat(),
                    })
                    st.rerun()

            nav1, nav2 = st.columns(2)
            with nav1:
                if st.button("← Back", use_container_width=True, key="ob5_back"):
                    save_onboarding_state(user_id, {"current_step": 4}); st.rerun()
            with nav2:
                if (has_labs or acknowledged) and st.button(
                        "Continue →", type="primary", use_container_width=True, key="ob5_next"):
                    save_onboarding_state(user_id, {"current_step": 6, "step5_done": True}); st.rerun()

        # ── STEP 6 — Ready ────────────────────────────────────────────────────
        elif current_step == 6:
            ob_final = get_onboarding_state(user_id)
            completeness = calculate_completeness(user_id, ob_final)
            labs_exist = bool(db_get("lab_reports", user_id))
            acknowledged = ob_final and ob_final.get("lab_upload_acknowledged")

            st.markdown("### You're ready")
            if completeness >= 70:
                st.success(f"✅ Profile {completeness}% complete — your roadmap will be precise.")
            else:
                st.warning(f"⚠️ Profile {completeness}% complete — go back to add more detail.")
            st.progress(completeness)

            checks = [
                ("Plan mode", bool(ob_final and ob_final.get("plan_mode"))),
                ("About you", bool(ob_final and ob_final.get("step2_done"))),
                ("Health history", bool(ob_final and ob_final.get("step3_done"))),
                ("Lifestyle & goals", bool(ob_final and ob_final.get("step4_done"))),
                ("Lab reports", labs_exist),
            ]
            for label, done in checks:
                icon = "✅" if done else ("⏳" if label == "Lab reports" and acknowledged else "⬜")
                st.markdown(f"{icon} &nbsp; {label}")

            if not labs_exist and acknowledged:
                ob_ack_time = ob_final.get("lab_acknowledged_at") if ob_final else None
                days_remaining = 14
                if ob_ack_time:
                    try:
                        ack_dt = datetime.fromisoformat(ob_ack_time.replace("Z", ""))
                        days_remaining = max(0, 14 - (datetime.now() - ack_dt).days)
                    except Exception:
                        pass
                st.info(f"📋 {days_remaining} days remaining to upload labs. "
                        "Roadmap will be provisional until then.")

            st.divider()
            st.markdown("**What happens next:**")
            st.markdown("""
- Your **12-month treatment roadmap** generates now
- **Monthly protocols** break it into milestones
- **Weekly protocols** give you the day-by-day detail
- **Your Sattva** is always there for questions
""")
            if completeness >= 50:
                if st.button("✦ Enter OneSattva", type="primary",
                             use_container_width=True, key="ob_finish"):
                    save_onboarding_state(user_id, {
                        "completed": True, "completed_at": datetime.now().isoformat()
                    })
                    db_upsert("profiles", {"id": user_id, "onboarding_complete": True})
                    st.balloons()
                    st.rerun()
            else:
                st.button("Complete more steps to unlock OneSattva",
                          disabled=True, use_container_width=True)

            if st.button("← Back", key="ob6_back"):
                save_onboarding_state(user_id, {"current_step": 5}); st.rerun()

    # Right column tips
    with col_r:
        tips = {
            1: ("Why plan mode matters",
                "Your plan mode shapes the tone of your roadmap, the urgency of protocols, "
                "and how your coach prioritises between competing goals. You can switch it later."),
            2: ("Why we ask",
                "Age, sex, height, and weight affect how we interpret your labs and calibrate "
                "nutrition and training. Location helps us suggest locally available foods and brands. "
                "Alcohol and smoking directly influence hormone metabolism."),
            3: ("Your data is private",
                "Only you can see your health information. No one else — including practitioners — "
                "can access your data unless you explicitly grant permission. Add as much or "
                "as little as you're comfortable with."),
            4: ("Goals shape everything",
                "Your roadmap is built around your goals and their timeframes. After each goal "
                "is achieved, we build a maintenance guide so you keep the results long-term."),
            5: ("Why labs matter so much",
                "Functional medicine reads values differently from conventional medicine. A TSH of 2.5 "
                "might look 'normal' but mask a T3 conversion problem. Reports older than 3 months "
                "move to trend context only — recent labs always take priority."),
        }
        title, body = tips.get(current_step, ("", ""))
        if title:
            st.markdown(f"""
            <div style='background:var(--bone);border-radius:12px;padding:16px;margin-top:52px;
                        border:1px solid var(--line);'>
              <p style='font-family:Inter,sans-serif;font-weight:600;color:#111214;
                        font-size:13px;margin:0 0 8px;'>{title}</p>
              <p style='font-family:Inter,sans-serif;color:#6B6358;font-size:12.5px;
                        margin:0;line-height:1.55;'>{body}</p>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

def show_main_app(user):
    user_id = user.id
    profile = db_get_single("profiles", user_id)
    name = profile.get("full_name", "there") if profile else "there"
    cycle_day, cycle_phase, days_to_next = calculate_cycle_status(user_id)
    cycle_phase = cycle_phase or "Follicular (Day 1–14)"

    # Build system prompt once per session
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = build_system_prompt(user_id, profile)

    # ── SIDEBAR ────────────────────────────────────────────────────────────────
    with st.sidebar:
        # Brand mark + wordmark
        st.markdown(f"""
        <div style='padding:20px 4px 16px;border-bottom:1px solid rgba(247,245,242,0.10);margin-bottom:18px;'>
          <div style='display:flex;align-items:center;gap:9px;margin-bottom:10px;'>
            {_MARK_DARK}
            <span style='font-family:Newsreader,serif;font-weight:400;font-style:normal;
                         font-size:18px;color:#F7F5F2;line-height:1;letter-spacing:-0.02em;'>
              OneSattva
            </span>
          </div>
          <div style='font-family:Inter,sans-serif;font-size:13px;color:#F7F5F2;opacity:0.70;'>
            {name}
          </div>
          {f"<div style='font-family:Inter,sans-serif;font-size:11px;color:#F7F5F2;opacity:0.40;margin-top:2px;'>{profile.get('age','')}{'yr' if profile.get('age') else ''}{' · ' if profile.get('age') and profile.get('location') else ''}{profile.get('location','')}</div>" if profile else ""}
        </div>
        """, unsafe_allow_html=True)

        # Cycle status widget
        st.markdown("""<p style='font-family:Inter,sans-serif;font-size:10px;font-weight:600;
            letter-spacing:0.09em;color:#F7F5F2;opacity:0.40;margin:0 0 7px;
            text-transform:uppercase;'>Cycle</p>""", unsafe_allow_html=True)
        if cycle_day:
            st.markdown(f"""
            <div style='background:rgba(247,245,242,0.07);border-radius:10px;
                        padding:11px 13px;margin-bottom:8px;'>
              <div style='font-family:JetBrains Mono,monospace;font-size:22px;
                          color:#F7F5F2;font-weight:500;line-height:1;'>Day {cycle_day}</div>
              <div style='font-family:Inter,sans-serif;font-size:12px;color:#F7F5F2;
                          opacity:0.55;margin-top:4px;'>{cycle_phase.split(' (')[0]}</div>
              {f"<div style='font-family:Inter,sans-serif;font-size:11px;color:#B6744A;margin-top:5px;'>~{days_to_next}d until next period</div>" if days_to_next else ""}
            </div>
            """, unsafe_allow_html=True)
            if st.button("New period started today", use_container_width=True, key="new_period"):
                db_upsert("cycle_data", {"user_id": user_id,
                                         "last_period_start": date.today().isoformat()})
                st.session_state.system_prompt = build_system_prompt(user_id, profile)
                st.rerun()
        else:
            st.markdown("""<div style='font-family:Inter,sans-serif;font-size:12px;
                color:#F7F5F2;opacity:0.45;'>Set period date in Profile & Data</div>""",
                        unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # Goals preview
        goals = db_get("goals", user_id)
        if goals:
            st.markdown("""<p style='font-family:Inter,sans-serif;font-size:10px;font-weight:600;
                letter-spacing:0.09em;color:#F7F5F2;opacity:0.40;margin:0 0 7px;
                text-transform:uppercase;'>Goals</p>""", unsafe_allow_html=True)
            for g in goals[:3]:
                st.markdown(f"""<div style='font-family:Inter,sans-serif;font-size:12px;
                    color:#F7F5F2;opacity:0.65;padding:3px 0;
                    border-bottom:1px solid rgba(247,245,242,0.06);'>
                    {g['goal'][:48]}</div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        # Nav
        if "active_section" not in st.session_state:
            st.session_state.active_section = "home"

        NAV_ITEMS = [
            ("home",     "⌂  Home"),
            ("protocol", "◈  Protocol"),
            ("checkin",  "✓  Check-In"),
            ("coach",    "✦  Coach"),
            ("profile",  "◎  Profile & Data"),
        ]
        for section_key, label in NAV_ITEMS:
            is_active = st.session_state.active_section == section_key
            display_label = f"**{label}**" if is_active else label
            if st.button(display_label, key=f"nav_{section_key}", use_container_width=True):
                st.session_state.active_section = section_key
                st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Sign out
        st.markdown(f"""<div style='font-family:Inter,sans-serif;font-size:11px;
            color:#F7F5F2;opacity:0.30;margin-bottom:6px;'>{user.email}</div>""",
                    unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True, key="signout_btn"):
            sign_out()

    # ── SECTION ROUTING ────────────────────────────────────────────────────────
    active = st.session_state.active_section

    # ══════════════════════════════
    # HOME
    # ══════════════════════════════
    if active == "home":
        _render_home(user_id, profile, name, cycle_day, cycle_phase, days_to_next)

    # ══════════════════════════════
    # PROTOCOL
    # ══════════════════════════════
    elif active == "protocol":
        _render_protocol(user_id, profile, cycle_day, cycle_phase)

    # ══════════════════════════════
    # CHECK-IN
    # ══════════════════════════════
    elif active == "checkin":
        _render_checkin(user_id, name, cycle_day, cycle_phase)

    # ══════════════════════════════
    # COACH
    # ══════════════════════════════
    elif active == "coach":
        _render_coach(user_id, profile, name, cycle_day, cycle_phase, days_to_next)

    # ══════════════════════════════
    # PROFILE & DATA
    # ══════════════════════════════
    elif active == "profile":
        _render_profile_and_data(user_id, profile, cycle_day, cycle_phase, days_to_next)


# ══════════════════════════════════════════════════════════════════════════════
# HOME SECTION
# ══════════════════════════════════════════════════════════════════════════════

def _render_home(user_id, profile, name, cycle_day, cycle_phase, days_to_next):
    # Data fetches
    checkins_home = db_get("checkins", user_id, order_col="checkin_date", limit=1)
    wearable_home = db_get("wearable_data", user_id, order_col="data_date", limit=1)
    labs_home = db_get("lab_reports", user_id, order_col="report_date", limit=3)
    recent_checkins = db_get("checkins", user_id, order_col="checkin_date", limit=30)
    wearable_30d = db_get("wearable_data", user_id, order_col="data_date", limit=30)

    # Plan mode banner
    if st.session_state.get("roadmap_committed"):
        saved_rm = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
        rm_start, rm_name = None, "Active programme"
        if saved_rm:
            try:
                rm_start = datetime.fromisoformat(
                    saved_rm[0]["generated_at"].replace("Z", "")).date()
                for ln in (saved_rm[0].get("roadmap_text", "") or "").split("\n"):
                    ln = ln.strip().lstrip("#").strip()
                    if ln and len(ln) < 80:
                        rm_name = ln
                        break
            except Exception:
                pass
        days_in = (date.today() - rm_start).days if rm_start else 0
        week_in = (days_in // 7) + 1
        progress_pct = min(100, int((days_in / 90) * 100))
        st.markdown(f"""
        <div style='background:var(--graphite);border-radius:14px;padding:18px 22px;margin-bottom:24px;'>
          <div style='font-family:Inter,sans-serif;font-size:10px;font-weight:600;
                      letter-spacing:0.08em;color:rgba(247,245,242,0.40);
                      text-transform:uppercase;margin-bottom:5px;'>Plan mode</div>
          <div style='font-family:Newsreader,serif;font-size:1.1rem;color:#F7F5F2;
                      font-weight:500;margin-bottom:10px;'>{rm_name[:60]}</div>
          <div style='display:flex;align-items:center;gap:10px;'>
            <div style='flex:1;height:3px;background:rgba(247,245,242,0.12);
                        border-radius:2px;overflow:hidden;'>
              <div style='width:{progress_pct}%;height:100%;background:#B6744A;border-radius:2px;'></div>
            </div>
            <div style='font-family:JetBrains Mono,monospace;font-size:11px;
                        color:rgba(247,245,242,0.50);white-space:nowrap;'>Wk {week_in}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:var(--stone);border-radius:14px;padding:15px 20px;
                    margin-bottom:24px;border:1px dashed rgba(17,18,20,0.15);'>
          <div style='font-family:Inter,sans-serif;font-size:13px;color:var(--mid);'>
            No active plan — generate a Treatment Roadmap in Protocol to unlock priorities and tracking.
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Greeting
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
    first_name = name.split()[0] if name and name != "there" else "there"

    st.markdown(f"""
    <div style='padding:0 0 20px;'>
      <h1 style='border:none;margin-bottom:3px !important;padding-bottom:0 !important;
                 font-family:Newsreader,serif;font-size:2rem;color:var(--graphite);'>
        {greeting}, {first_name}.
      </h1>
      <p style='color:var(--mid);font-family:Inter,sans-serif;font-size:0.9rem;margin:0;'>
        {date.today().strftime('%A, %d %B %Y')} · Here's what matters today.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Today's priorities
    st.markdown("""<p class='sec-label'>Today's priorities</p>""", unsafe_allow_html=True)

    if "home_priorities" not in st.session_state:
        has_data = (
            st.session_state.get("roadmap_committed") or labs_home
            or checkins_home or wearable_home
        )
        if has_data:
            with st.spinner("Preparing your priorities…"):
                try:
                    rm_text = st.session_state.get("treatment_roadmap", "") or ""
                    lab_summary = "\n".join([
                        f"- {l.get('test_name','Lab')} {l.get('report_date','')}: "
                        f"{l.get('summary') or l.get('notes','')}"
                        for l in labs_home[:3]
                    ]) if labs_home else "No labs uploaded"

                    wearable_summary = ""
                    if wearable_home:
                        w = wearable_home[0]
                        wearable_summary = (
                            f"Latest wearable ({w.get('data_date','')}):\n"
                            f"- Recovery: {w.get('recovery_score','?')}%\n"
                            f"- HRV: {w.get('hrv','?')} ms\n"
                            f"- Sleep performance: {w.get('sleep_performance','?')}%"
                        )

                    checkin_summary = ""
                    if checkins_home:
                        c = checkins_home[0]
                        checkin_summary = (
                            f"Latest check-in ({c.get('checkin_date','')}):\n"
                            f"- Energy: {c.get('energy','?')}/10\n"
                            f"- Mood: {c.get('mood','?')}/10\n"
                            f"- Sleep: {c.get('sleep_hours','?')}h, quality {c.get('sleep_quality','?')}/10"
                        )

                    priority_prompt = f"""Generate exactly 3 priority cards for today.

Respond ONLY with valid JSON — no markdown, no preamble:
[
  {{"triage": "act_today", "title": "...", "body": "..."}},
  {{"triage": "watch", "title": "...", "body": "..."}},
  {{"triage": "background", "title": "...", "body": "..."}}
]

triage values: act_today | watch | background
Title: max 8 words. Body: 2-3 sentences, specific and clinical. Order by urgency.

USER DATA:
Roadmap: {rm_text[:600] if rm_text else 'No roadmap yet'}
Labs: {lab_summary}
Wearable: {wearable_summary or 'No wearable data'}
Check-in: {checkin_summary or 'No check-in data'}
Today: {date.today().strftime('%A, %d %B %Y')}
Cycle: Day {cycle_day or '?'}, {(cycle_phase or 'Unknown').split(' (')[0]}"""

                    resp = ai_client.messages.create(
                        model="claude-sonnet-4-6", max_tokens=600,
                        messages=[{"role": "user", "content": priority_prompt}]
                    )
                    raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
                    st.session_state.home_priorities = _json.loads(raw)
                except Exception:
                    st.session_state.home_priorities = []
        else:
            st.session_state.home_priorities = []

    TRIAGE_LABELS = {
        "act_today": ("Act today", "triage-now"),
        "watch":     ("Watch",     "triage-watch"),
        "background": ("Background", "triage-background"),
    }

    priorities = st.session_state.get("home_priorities", [])
    if priorities:
        pc_cols = st.columns(len(priorities))
        for i, p in enumerate(priorities[:3]):
            triage_key = p.get("triage", "background")
            label, css_class = TRIAGE_LABELS.get(triage_key, ("Background", "triage-background"))
            with pc_cols[i]:
                st.markdown(f"""
                <div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;
                            padding:16px 18px;min-height:140px;'>
                  <span class='{css_class}' style='display:inline-block;margin-bottom:10px;'>{label}</span>
                  <div style='font-family:Inter,sans-serif;font-size:13.5px;font-weight:600;
                              color:var(--graphite);margin-bottom:8px;line-height:1.35;'>
                    {p.get('title','')}
                  </div>
                  <div style='font-family:Inter,sans-serif;font-size:12.5px;color:var(--mid);
                              line-height:1.55;'>
                    {p.get('body','')}
                  </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("↺ Refresh priorities", key="refresh_priorities"):
            del st.session_state["home_priorities"]
            st.rerun()
    else:
        st.markdown("""
        <div style='background:var(--stone);border-radius:12px;padding:20px 22px;
                    border:1px dashed rgba(17,18,20,0.12);'>
          <div style='font-family:Inter,sans-serif;font-size:13px;color:var(--mid);'>
            Priorities will appear here once you have a roadmap, labs, or check-in data.
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)

    # Today's snapshot — 4 boxes
    st.markdown("""<p class='sec-label'>Today's snapshot</p>""", unsafe_allow_html=True)

    w = wearable_home[0] if wearable_home else {}
    c = checkins_home[0] if checkins_home else {}

    def _snap_box(label, value, unit, sub, flag=""):
        flag_html = (f"<div style='font-family:Inter,sans-serif;font-size:11px;"
                     f"color:#B6744A;margin-top:5px;'>{flag}</div>") if flag else ""
        if value is None:
            return (f"<div style='background:#FFFFFF;border:1px dashed var(--line);border-radius:12px;padding:15px;'>"
                    f"<div style='font-family:Inter,sans-serif;font-size:10px;font-weight:600;"
                    f"letter-spacing:0.07em;color:var(--mid);text-transform:uppercase;margin-bottom:7px;'>{label}</div>"
                    f"<div style='font-family:Inter,sans-serif;font-size:12px;color:var(--mid);opacity:0.55;'>No data</div>"
                    f"</div>")
        return (f"<div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;padding:15px;'>"
                f"<div style='font-family:Inter,sans-serif;font-size:10px;font-weight:600;"
                f"letter-spacing:0.07em;color:var(--mid);text-transform:uppercase;margin-bottom:7px;'>{label}</div>"
                f"<div style='font-family:JetBrains Mono,monospace;font-size:1.55rem;"
                f"color:var(--graphite);line-height:1;'>{value}"
                f"<span style='font-size:0.6em;opacity:0.45;margin-left:2px;'>{unit}</span></div>"
                f"<div style='font-family:Inter,sans-serif;font-size:11px;color:var(--mid);margin-top:4px;'>{sub}</div>"
                f"{flag_html}</div>")

    sn1, sn2, sn3, sn4 = st.columns(4)
    with sn1:
        st.markdown(_snap_box("HRV", w.get("hrv"), "ms", "WHOOP · latest"), unsafe_allow_html=True)
    with sn2:
        rec_val = round(float(w["recovery_score"])) if w.get("recovery_score") else None
        st.markdown(_snap_box("Recovery", rec_val, "%", "WHOOP · latest"), unsafe_allow_html=True)
    with sn3:
        st.markdown(_snap_box("Sleep", w.get("sleep_performance"), "%", "WHOOP · latest"),
                    unsafe_allow_html=True)
    with sn4:
        energy_sub = f"Check-in · {c.get('checkin_date','')}" if c else "No check-in"
        st.markdown(_snap_box("Energy", c.get("energy"), "/10", energy_sub), unsafe_allow_html=True)

    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)

    # Trends
    st.markdown("""<p class='sec-label'>Trends</p>""", unsafe_allow_html=True)
    tr1, tr2 = st.columns(2)

    # Energy trend
    with tr1:
        if len(recent_checkins) >= 7:
            df_ci = pd.DataFrame(recent_checkins).sort_values("checkin_date")
            energy_vals = pd.to_numeric(
                df_ci.get("energy", pd.Series()), errors="coerce").dropna().tolist()
            if energy_vals:
                bars = "".join([
                    f"<div style='flex:1;background:var(--graphite);border-radius:2px 2px 0 0;"
                    f"height:{max(8,int((v/10)*100))}%;opacity:0.72;'></div>"
                    for v in energy_vals[-14:]
                ])
                st.markdown(f"""
                <div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;padding:18px;'>
                  <div style='font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;
                              color:var(--graphite);margin-bottom:6px;'>Energy · 30 days</div>
                  <div style='display:flex;align-items:flex-end;gap:3px;height:50px;margin-bottom:9px;'>
                    {bars}
                  </div>
                  <div style='font-family:Inter,sans-serif;font-size:12px;color:var(--mid);line-height:1.5;'>
                    Avg {sum(energy_vals)/len(energy_vals):.1f}/10 over {len(energy_vals)} logged days.
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:#FFFFFF;border:1px dashed var(--line);border-radius:12px;
                        padding:18px;min-height:120px;'>
              <div style='font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;
                          color:var(--graphite);margin-bottom:6px;'>Energy · 30 days</div>
              <div style='font-family:Inter,sans-serif;font-size:12px;color:var(--mid);'>
                Log 7+ check-ins to see your energy trend.
              </div>
            </div>
            """, unsafe_allow_html=True)

    # HRV trend
    with tr2:
        if len(wearable_30d) >= 7:
            df_w = pd.DataFrame(wearable_30d).sort_values("data_date")
            hrv_vals = pd.to_numeric(
                df_w.get("hrv", pd.Series()), errors="coerce").dropna().tolist()
            if hrv_vals:
                max_hrv = max(hrv_vals) or 1
                bars = "".join([
                    f"<div style='flex:1;background:var(--graphite);border-radius:2px 2px 0 0;"
                    f"height:{max(8,int((v/max_hrv)*100))}%;opacity:0.72;'></div>"
                    for v in hrv_vals[-14:]
                ])
                st.markdown(f"""
                <div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;padding:18px;'>
                  <div style='font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;
                              color:var(--graphite);margin-bottom:6px;'>HRV trajectory · 30 days</div>
                  <div style='display:flex;align-items:flex-end;gap:3px;height:50px;margin-bottom:9px;'>
                    {bars}
                  </div>
                  <div style='font-family:Inter,sans-serif;font-size:12px;color:var(--mid);line-height:1.5;'>
                    Avg {sum(hrv_vals)/len(hrv_vals):.0f} ms · Latest {hrv_vals[-1]:.0f} ms.
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:#FFFFFF;border:1px dashed var(--line);border-radius:12px;
                        padding:18px;min-height:120px;'>
              <div style='font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;
                          color:var(--graphite);margin-bottom:6px;'>HRV trajectory · 30 days</div>
              <div style='font-family:Inter,sans-serif;font-size:12px;color:var(--mid);'>
                Upload 7+ days of wearable data to see your HRV trend.
              </div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PROTOCOL SECTION
# ══════════════════════════════════════════════════════════════════════════════

def _render_protocol(user_id, profile, cycle_day, cycle_phase):
    proto_tab1, proto_tab2, proto_tab3 = st.tabs(["Treatment Roadmap", "Protocol", "Trends"])

    # ── ROADMAP TAB ───────────────────────────────────────────────────────────
    with proto_tab1:
        st.markdown("## Treatment Roadmap")
        st.caption("Your 12-month strategic plan — generated once, committed to, updated only when significant new information warrants it.")

        if "treatment_roadmap" not in st.session_state:
            st.session_state.treatment_roadmap = None
        if "roadmap_date" not in st.session_state:
            st.session_state.roadmap_date = None
        if "roadmap_committed" not in st.session_state:
            st.session_state.roadmap_committed = False

        if not st.session_state.treatment_roadmap:
            saved = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
            if saved:
                st.session_state.treatment_roadmap = saved[0]["roadmap_text"]
                st.session_state.roadmap_committed = saved[0].get("committed", False)
                try:
                    gen_dt = datetime.fromisoformat(saved[0]["generated_at"].replace("Z", ""))
                    st.session_state.roadmap_date = gen_dt.strftime("%d %b %Y")
                except Exception:
                    st.session_state.roadmap_date = "Previously"

        if st.session_state.treatment_roadmap and st.session_state.roadmap_committed:
            st.success(f"✅ Committed roadmap — generated {st.session_state.roadmap_date} · This is your active plan.")
            st.markdown(st.session_state.treatment_roadmap)
            st.divider()
            st.download_button("⬇️ Download roadmap",
                data=st.session_state.treatment_roadmap,
                file_name=f"onesattva_roadmap_{date.today()}.txt",
                use_container_width=True)
            with st.expander("⚠️ I have significant new information and need to update my roadmap"):
                st.warning("Your roadmap is your committed plan. Update it only if something significant has changed.")
                change_reason = st.text_area("Describe what has changed:",
                    placeholder="e.g. New Thyrocare panel shows prolactin has normalised.")
                if st.button("🔄 Generate Updated Roadmap", type="primary", use_container_width=True):
                    if change_reason.strip():
                        st.session_state.roadmap_committed = False
                        st.session_state.treatment_roadmap = None
                        st.session_state.roadmap_change_reason = change_reason
                        st.rerun()
                    else:
                        st.error("Please describe what has changed before regenerating.")

        elif st.session_state.treatment_roadmap:
            st.info("📋 Review your roadmap below. When you're ready, commit to it.")
            st.markdown(st.session_state.treatment_roadmap)
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Commit to this roadmap", type="primary", use_container_width=True):
                    db_upsert("roadmaps", {
                        "user_id": user_id,
                        "roadmap_text": st.session_state.treatment_roadmap,
                        "committed": True,
                        "priority_focus": st.session_state.get("rm_priority_saved", ""),
                        "intensity": st.session_state.get("rm_intensity_saved", ""),
                    })
                    st.session_state.roadmap_committed = True
                    st.success("Roadmap committed.")
                    st.rerun()
            with col2:
                if st.button("🔄 Regenerate instead", use_container_width=True):
                    st.session_state.treatment_roadmap = None
                    st.rerun()

        else:
            st.markdown("##### Generate your treatment roadmap")
            st.caption("Generated once from your full profile, labs, and goals. Review before committing.")
            rm_col1, rm_col2 = st.columns(2)
            with rm_col1:
                rm_priority = st.selectbox("Priority focus", [
                    "Balanced — all areas", "Fastest path to natural conception",
                    "Fastest path to fat loss", "Fastest path off thyroid medication",
                    "Gut/digestion first"], key="rm_priority")
            with rm_col2:
                rm_intensity = st.selectbox("Change intensity", [
                    "Moderate — sustainable, gradual",
                    "Aggressive — willing to make bigger changes faster"], key="rm_intensity")

            if st.button("🗺️ Generate My Treatment Roadmap", type="primary", use_container_width=True):
                change_context = ""
                if st.session_state.get("roadmap_change_reason"):
                    change_context = (f"\n\nIMPORTANT — This is an UPDATE. The patient has reported: "
                                      f"{st.session_state.roadmap_change_reason}")

                roadmap_prompt = f"""Generate a comprehensive 12-month treatment roadmap for this patient.

Priority: {rm_priority}
Intensity: {rm_intensity}
{change_context}

FORMAT — complete every section fully:

## Where Things Stand
3-4 sentences: core biological blockers right now, why current approach is insufficient, priority order. Be direct.

## Phase 1 — Months 0-3: [give this phase a clear title]
Markdown table: Change | Current → New | Clinical Reason (5-7 rows, exact doses/timing/foods)
**Retest at 3 months:** [4-5 specific markers]
**What success looks like:** [2-3 measurable outcomes]

## Phase 2 — Months 3-6: [title]
Same table format, 4-5 rows — builds on Phase 1 results
**Retest at 6 months:** [markers]
**What success looks like:** [outcomes]

## Phase 3 — Months 6-12: [title]
Same table format, 3-4 rows — longer-term goals, medication conversations, maintenance
**Retest at 12 months:** [markers]
**What success looks like:** [outcomes]

## If Phase 1 Shows No Progress
2-3 sentences: what it means, escalation, additional testing needed.

## Maintenance — After Goals Are Achieved
2-3 sentences: what to continue long-term, what to watch for, when to return.

**Start today:** [one specific immediate action]

Complete every section. Never cut off."""

                with st.spinner("Building your 12-month treatment roadmap — 30-40 seconds..."):
                    response = ai_client.messages.create(
                        model="claude-sonnet-4-6", max_tokens=4096,
                        system=st.session_state.system_prompt,
                        messages=[{"role": "user", "content": roadmap_prompt}]
                    )
                    st.session_state.treatment_roadmap = response.content[0].text
                    st.session_state.roadmap_date = date.today().strftime("%d %b %Y")
                    st.session_state.rm_priority_saved = rm_priority
                    st.session_state.rm_intensity_saved = rm_intensity
                    db_upsert("roadmaps", {
                        "user_id": user_id,
                        "roadmap_text": st.session_state.treatment_roadmap,
                        "committed": False,
                        "priority_focus": rm_priority,
                        "intensity": rm_intensity,
                    })
                    st.rerun()

    # ── PROTOCOL TAB ──────────────────────────────────────────────────────────
    with proto_tab2:
        st.markdown("## Protocol")
        st.caption("Monthly overview · Weekly execution · Built from your committed roadmap.")

        checkins_recent = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        gap_days = 0
        if checkins_recent:
            try:
                last_ci = date.fromisoformat(checkins_recent[0]["checkin_date"])
                gap_days = (date.today() - last_ci).days
            except Exception:
                pass

        if gap_days >= 14:
            st.warning(f"⚠️ It's been {gap_days} days since your last check-in. "
                       "Tell your coach what's changed before viewing your protocol.")
            reentry_note = st.text_area("What's changed in the last few weeks?",
                placeholder="e.g. Been travelling, energy has been low, stopped some supplements...",
                key="reentry_note")
            if st.button("📋 Update my coach and continue", type="primary", use_container_width=True):
                if reentry_note.strip():
                    existing_notes = db_get_single("profile_notes", user_id)
                    current_notes = existing_notes.get("notes", "") if existing_notes else ""
                    updated_notes = current_notes + f"\n\n[Re-entry note {date.today()}]: {reentry_note}"
                    db_upsert("profile_notes", {"user_id": user_id, "notes": updated_notes})
                    st.session_state.weekly_protocol = None
                    st.session_state.monthly_protocol = None
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.success("Updated. Your protocol will be refreshed with this context.")
                    st.rerun()
                else:
                    st.error("Please share what's changed before continuing.")
            st.stop()
        elif gap_days >= 7:
            st.info(f"👋 Welcome back — it's been {gap_days} days. Has anything changed?")

        if not st.session_state.get("treatment_roadmap"):
            st.info("💡 Generate and commit your Treatment Roadmap first — protocols are built from it.")
            st.stop()

        # Roadmap position
        roadmap_start = date.today()
        saved_roadmaps = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
        if saved_roadmaps and saved_roadmaps[0].get("committed"):
            try:
                roadmap_start = datetime.fromisoformat(
                    saved_roadmaps[0]["generated_at"].replace("Z", "")).date()
            except Exception:
                pass

        days_into = (date.today() - roadmap_start).days
        current_week_num = (days_into // 7) + 1
        current_month_num = (days_into // 30) + 1
        current_month_name = date.today().strftime("%B %Y")
        roadmap_phase = "Phase 1" if days_into < 90 else ("Phase 2" if days_into < 180 else "Phase 3")

        # Monthly overview
        if "monthly_protocol" not in st.session_state:
            st.session_state.monthly_protocol = None
        if "monthly_protocol_month" not in st.session_state:
            st.session_state.monthly_protocol_month = None

        needs_monthly = (
            not st.session_state.monthly_protocol
            or st.session_state.monthly_protocol_month != current_month_name
        )

        mh_col, mb_col = st.columns([3, 1])
        with mh_col:
            st.markdown(f"""
            <div style='background:var(--bone);border-left:3px solid #B6744A;
                        border-radius:0 10px 10px 0;padding:13px 18px;margin-bottom:4px;'>
              <p style='font-family:Newsreader,serif;font-size:1.05rem;
                        color:var(--graphite);margin:0;font-weight:500;'>
                {current_month_name} · Month {current_month_num} · {roadmap_phase} · Week {current_week_num}
              </p>
            </div>
            """, unsafe_allow_html=True)
        with mb_col:
            if st.button("↻ Refresh month", use_container_width=True, key="refresh_month"):
                st.session_state.monthly_protocol = None

        if needs_monthly:
            with st.spinner(f"Building {current_month_name} overview..."):
                monthly_prompt = f"""Generate the monthly protocol overview for Month {current_month_num}.

Today: {date.today().strftime("%d %B %Y")}
Roadmap phase: {roadmap_phase} (Week {current_week_num})
Cycle phase today: {cycle_phase or 'Unknown'}

FORMAT — concise:

## Month {current_month_num} — {current_month_name}
**Roadmap phase:** {roadmap_phase}
**This month's focus:** [1-2 sentences]

**Milestones to hit this month:**
- [3-4 specific, measurable milestones]

**What changes this month:**
| Area | Change |
|---|---|
| Supplements | [specific changes] |
| Nutrition | [specific focus] |
| Training | [specific focus] |
| Lifestyle | [specific focus] |

**What to monitor:**
- [2-3 specific things to watch and log]

**End of month check:** [what to assess]

Keep it tight."""

                monthly_resp = ai_client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=1500,
                    system=st.session_state.system_prompt,
                    messages=[{"role": "user", "content": monthly_prompt}]
                )
                st.session_state.monthly_protocol = monthly_resp.content[0].text
                st.session_state.monthly_protocol_month = current_month_name

        if st.session_state.monthly_protocol:
            with st.expander(f"📅 {current_month_name} — Monthly Overview", expanded=True):
                st.markdown(st.session_state.monthly_protocol)

        st.divider()

        # Weekly protocol
        today_dt = datetime.now()
        day_names = [(today_dt + timedelta(days=i)).strftime("%A %d %b") for i in range(7)]
        week_start = day_names[0]
        week_end = day_names[6]
        week_label = f"Week {current_week_num} · {week_start} – {week_end}"

        wp1, wp2, wp3 = st.columns(3)
        with wp1:
            phases_list = ["Follicular (Day 1–14)", "Ovulation (Day 14–16)",
                           "Luteal (Day 16–28)", "Menstruation (Day 1–5)"]
            default_idx = 0
            if cycle_phase:
                for i, p in enumerate(phases_list):
                    if cycle_phase.startswith(p.split(" (")[0]):
                        default_idx = i
                        break
            wp_phase = st.selectbox("Cycle phase", phases_list, index=default_idx, key="wp_phase")
        with wp2:
            st.metric("Cycle Day", cycle_day if cycle_day else "?")
        with wp3:
            wp_focus = st.selectbox("Priority focus",
                ["Balanced", "Fat loss", "Fertility & conception",
                 "Gut healing", "Energy & thyroid", "Sleep & recovery"],
                key="wp_focus")

        if "weekly_protocol" not in st.session_state:
            st.session_state.weekly_protocol = None

        st.markdown(f"**{week_label}**")

        gen_col, dl_col = st.columns([3, 1])
        with gen_col:
            gen_btn = st.button("🔄 Generate This Week's Protocol",
                                type="primary", use_container_width=True)
        with dl_col:
            if st.session_state.weekly_protocol:
                st.download_button("⬇️", data=st.session_state.weekly_protocol,
                    file_name=f"onesattva_week{current_week_num}_{date.today()}.txt",
                    use_container_width=True)

        if gen_btn:
            base_ctx = (
                f"Weekly protocol — Week {current_week_num} · {roadmap_phase} · {week_label}\n"
                f"Cycle: Day {cycle_day or '?'} · {wp_phase} · Focus: {wp_focus}\n"
                f"Days: {', '.join(day_names)}\n\n"
                f"Committed roadmap (Week {current_week_num}, {roadmap_phase}):\n"
                f"{(st.session_state.treatment_roadmap or '')[:2000]}\n\n"
                f"Monthly overview:\n{st.session_state.monthly_protocol or 'Not yet generated'}\n\n"
                "RULES: Output ONLY markdown tables. Complete all tables fully. "
                "Respect diet. Thyronorm always first on waking if prescribed."
            )

            with st.spinner("Building supplement & routine schedule..."):
                r1 = ai_client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=2000,
                    system=st.session_state.system_prompt,
                    messages=[{"role": "user", "content":
                        base_ctx + "\n\nGenerate ONLY:\n## Daily Routine & Supplement Schedule\n"
                        "Table: Time | Item | Dose | Notes\n"
                        "Thyronorm as first row if prescribed. Include all supplements. Complete fully."}]
                )
                part1 = r1.content[0].text

            with st.spinner("Building 7-day nutrition plan..."):
                r2 = ai_client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=4096,
                    system=st.session_state.system_prompt,
                    messages=[{"role": "user", "content":
                        base_ctx + f"\n\nGenerate ONLY:\n## 7-Day Nutrition Plan\n"
                        f"Table columns: Meal Slot | {' | '.join(day_names)}\n"
                        "Rows: Pre-Workout Snack | First Meal | Lunch | Evening Snack | Dinner | Seed Cycling\n"
                        "One specific food + portion per cell, max 10 words. Gut-friendly, cooked/warm. "
                        "Vary day to day. Complete all 7 days fully."}]
                )
                part2 = r2.content[0].text

            with st.spinner("Building training & lifestyle plan..."):
                r3 = ai_client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=3000,
                    system=st.session_state.system_prompt,
                    messages=[{"role": "user", "content":
                        base_ctx + f"\n\nGenerate ONLY:\n## 7-Day Training Plan\n"
                        f"Table: Day | Session Type | Specific Focus | Key Exercises\n"
                        f"Use actual day+date names: {', '.join(day_names)}\n"
                        "Include rest day, recovery-aware sessions, cycle-phase appropriate loads.\n\n"
                        "## This Week's Priorities\n"
                        "Exactly 3 bullets: (1) sleep/recovery target (2) one lifestyle or gut-healing practice "
                        "(3) one thing to monitor and log\n\n"
                        f"**Start today ({day_names[0]}):** [one specific immediate action]\n\n"
                        "Complete both sections fully."}]
                )
                part3 = r3.content[0].text

            st.session_state.weekly_protocol = part1 + "\n\n---\n\n" + part2 + "\n\n---\n\n" + part3
            st.rerun()

        if st.session_state.weekly_protocol:
            st.markdown(st.session_state.weekly_protocol)
            if st.button("🔄 Regenerate this week", use_container_width=True, key="regen_weekly"):
                st.session_state.weekly_protocol = None
                st.rerun()

    # ── TRENDS TAB ────────────────────────────────────────────────────────────
    with proto_tab3:
        st.markdown("## Trends")
        st.caption("Patterns across your check-ins, wearable data, and cycle phases.")

        all_checkins = db_get("checkins", user_id, order_col="checkin_date")
        if not all_checkins:
            st.info("No check-ins yet. Complete your first daily check-in to see trends here.")
        else:
            df_t = pd.DataFrame(all_checkins)
            df_t["checkin_date"] = pd.to_datetime(df_t["checkin_date"])
            df_t = df_t.sort_values("checkin_date")
            recent_t = df_t.tail(7)
            last_30 = df_t.tail(30)

            st.markdown("#### Last 7 days")
            tc1, tc2, tc3, tc4, tc5 = st.columns(5)
            for col, field, label, unit in [
                (tc1, "energy", "Energy", ""),
                (tc2, "mood", "Mood", ""),
                (tc3, "sleep_hours", "Sleep", "hrs"),
                (tc4, "sleep_quality", "Sleep Quality", ""),
                (tc5, "stress", "Stress", ""),
            ]:
                if field in recent_t.columns:
                    val = pd.to_numeric(recent_t[field], errors="coerce").mean()
                    if not pd.isna(val):
                        col.metric(label, f"{val:.1f}{unit}")

            st.divider()
            st.markdown("#### Pattern flags")
            flags = []

            if "energy" in df_t.columns and "cycle_phase" in df_t.columns:
                for phase in ["Luteal", "Follicular", "Ovulation", "Menstruation"]:
                    phase_data = df_t[df_t["cycle_phase"] == phase]
                    if len(phase_data) >= 3:
                        avg_e = pd.to_numeric(phase_data["energy"], errors="coerce").mean()
                        if avg_e <= 4:
                            flags.append(f"⚠️ **Consistently low energy in {phase} phase** "
                                         f"(avg {avg_e:.1f}/10 across {len(phase_data)} logged days)")

            if "bloating" in df_t.columns:
                bc = last_30["bloating"].value_counts()
                mod_severe = bc.get("Moderate", 0) + bc.get("Severe", 0)
                if mod_severe >= 10:
                    flags.append(f"⚠️ **Bloating {mod_severe} of last 30 days** at moderate or severe")

            if "sleep_hours" in df_t.columns:
                avg_sleep = pd.to_numeric(last_30["sleep_hours"], errors="coerce").mean()
                if not pd.isna(avg_sleep) and avg_sleep < 6.5:
                    flags.append(f"⚠️ **Average sleep {avg_sleep:.1f}hrs over last 30 days** "
                                 "— below functional threshold of 7hrs")

            if "energy" in df_t.columns:
                last_7_e = pd.to_numeric(recent_t["energy"], errors="coerce").mean()
                prev_7_e = pd.to_numeric(df_t.tail(14).head(7)["energy"], errors="coerce").mean()
                if not pd.isna(last_7_e) and not pd.isna(prev_7_e):
                    if last_7_e < prev_7_e - 1.5:
                        flags.append(f"📉 **Energy declining** — down {prev_7_e-last_7_e:.1f} pts vs previous week")
                    elif last_7_e > prev_7_e + 1.5:
                        flags.append(f"📈 **Energy improving** — up {last_7_e-prev_7_e:.1f} pts vs previous week")

            if flags:
                for f in flags:
                    st.markdown(f)
            else:
                st.success("✅ No significant pattern flags in your recent data.")

            if len(df_t) >= 7:
                if st.button("✦ Ask your coach to interpret these trends",
                             use_container_width=True, key="trend_insight_btn"):
                    trend_summary = df_t[["checkin_date", "cycle_phase", "energy", "mood",
                                          "sleep_hours", "bloating", "digestion"]].tail(30).to_string(index=False)
                    trend_prompt = (f"Analyse this patient's check-in trends over the last 30 days.\n\n"
                                    f"Data:\n{trend_summary}\n\n"
                                    f"Current cycle phase: {cycle_phase}\nCurrent cycle day: {cycle_day}\n\n"
                                    "Identify 2-3 meaningful patterns. Reference cycle phase where relevant. "
                                    "Be direct. If something warrants a protocol change, say so. "
                                    "Keep under 200 words.")
                    with st.spinner("Analysing your patterns..."):
                        trend_resp = ai_client.messages.create(
                            model="claude-sonnet-4-6", max_tokens=500,
                            system=st.session_state.system_prompt,
                            messages=[{"role": "user", "content": trend_prompt}]
                        )
                        st.session_state.trend_insight = trend_resp.content[0].text

                if st.session_state.get("trend_insight"):
                    st.markdown(f"""
                    <div class='insight-strip' style='margin:16px 0;'>
                      <p style='font-family:Inter,sans-serif;font-size:13px;color:#111214;
                                 margin:0;line-height:1.6;'>
                        {st.session_state.trend_insight}
                      </p>
                    </div>
                    """, unsafe_allow_html=True)

            st.divider()
            chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Energy & Mood", "Sleep", "Gut"])
            with chart_tab1:
                plot_fields = [f for f in ["energy", "mood"] if f in df_t.columns]
                if plot_fields:
                    st.line_chart(df_t[["checkin_date"] + plot_fields].set_index("checkin_date"))
            with chart_tab2:
                sleep_fields = [f for f in ["sleep_hours", "sleep_quality"] if f in df_t.columns]
                if sleep_fields:
                    st.line_chart(df_t[["checkin_date"] + sleep_fields].set_index("checkin_date"))
            with chart_tab3:
                if "bloating" in df_t.columns:
                    st.markdown("**Bloating frequency**")
                    st.bar_chart(df_t["bloating"].value_counts())
                if "digestion" in df_t.columns:
                    st.markdown("**Digestion frequency**")
                    st.bar_chart(df_t["digestion"].value_counts())

            st.divider()
            display_cols = [c for c in ["checkin_date", "cycle_phase", "energy", "mood", "stress",
                                         "sleep_hours", "sleep_quality", "bloating", "digestion",
                                         "workout", "notes"] if c in df_t.columns]
            st.dataframe(df_t[display_cols].sort_values("checkin_date", ascending=False),
                         use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# CHECK-IN SECTION
# ══════════════════════════════════════════════════════════════════════════════

def _render_checkin(user_id, name, cycle_day, cycle_phase):
    st.markdown("## Daily Check-In")

    hour = datetime.now().hour
    time_greeting = "Morning check-in" if hour < 12 else ("Afternoon check-in" if hour < 17 else "Evening check-in")
    st.caption(f"{time_greeting} · {date.today().strftime('%A, %d %B')} · Cycle Day {cycle_day or '?'}")

    today_checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)
    already_logged = today_checkins and today_checkins[0].get("checkin_date") == date.today().isoformat()

    # Defaults from yesterday
    yesterday_checkins = db_get("checkins", user_id, order_col="checkin_date", limit=2)
    yesterday = yesterday_checkins[1] if len(yesterday_checkins) > 1 else None
    prev_energy = int(yesterday.get("energy", 5)) if yesterday else 5
    prev_mood = int(yesterday.get("mood", 5)) if yesterday else 5
    prev_sleep_hrs = float(yesterday.get("sleep_hours", 7)) if yesterday else 7.0
    prev_sleep_q = int(yesterday.get("sleep_quality", 5)) if yesterday else 5
    prev_stress = int(yesterday.get("stress", 3)) if yesterday else 3

    if already_logged:
        row = today_checkins[0]
        st.success("✅ Logged for today")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Energy", f"{row.get('energy','?')}/10")
        c2.metric("Mood", f"{row.get('mood','?')}/10")
        c3.metric("Sleep", f"{row.get('sleep_hours','?')}h")
        c4.metric("Bloating", row.get("bloating", "?"))
        c5.metric("Workout", (row.get("workout", "?") or "?")[:8])

        if row.get("notes"):
            st.caption(f"📝 {row['notes']}")

        if "checkin_insight" not in st.session_state:
            recent_for_insight = db_get("checkins", user_id, order_col="checkin_date", limit=7)
            recent_pattern = ", ".join([
                f"energy {c.get('energy','?')}, bloating {c.get('bloating','?')}"
                for c in (recent_for_insight or [])[:5]
            ])
            insight_prompt = (
                f"Today's check-in for {name}:\n"
                f"Cycle Day {cycle_day or '?'} · {cycle_phase or 'Unknown phase'}\n"
                f"Energy: {row.get('energy')}/10 · Mood: {row.get('mood')}/10 · "
                f"Sleep: {row.get('sleep_hours')}hrs (quality {row.get('sleep_quality')}/10)\n"
                f"Bloating: {row.get('bloating')} · Digestion: {row.get('digestion')} · "
                f"Workout: {row.get('workout')}\nNotes: {row.get('notes','')}\n\n"
                f"Recent 7-day pattern: {recent_pattern}\n\n"
                "Give ONE sharp clinical observation in 2-3 sentences. Reference cycle phase and pattern if relevant. "
                "Be direct and specific. End with one concrete action for today if warranted."
            )
            with st.spinner(""):
                insight_resp = ai_client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=300,
                    system=st.session_state.system_prompt,
                    messages=[{"role": "user", "content": insight_prompt}]
                )
                st.session_state.checkin_insight = insight_resp.content[0].text

        if st.session_state.get("checkin_insight"):
            st.markdown(f"""
            <div class='insight-strip' style='margin-top:16px;'>
              <p style='font-family:Inter,sans-serif;font-size:13px;color:#111214;
                         margin:0;line-height:1.6;'>
                {st.session_state.checkin_insight}
              </p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        if st.button("✏️ Edit today's check-in", use_container_width=True):
            st.session_state.edit_checkin = True
            st.rerun()

    if not already_logged or st.session_state.get("edit_checkin"):
        if st.session_state.get("edit_checkin") and today_checkins:
            st.caption("Editing today's check-in")
            prefill = today_checkins[0]
            prev_energy = int(prefill.get("energy", prev_energy))
            prev_mood = int(prefill.get("mood", prev_mood))
            prev_sleep_hrs = float(prefill.get("sleep_hours", prev_sleep_hrs))
            prev_sleep_q = int(prefill.get("sleep_quality", prev_sleep_q))
            prev_stress = int(prefill.get("stress", prev_stress))

        with st.form("checkin_form"):
            st.markdown("**How are you feeling?**")
            s1, s2, s3 = st.columns(3)
            with s1:
                c_energy = st.slider("⚡ Energy", 1, 10, prev_energy)
            with s2:
                c_mood = st.slider("😊 Mood", 1, 10, prev_mood)
            with s3:
                c_stress = st.slider("😤 Stress", 1, 10, prev_stress)

            st.markdown("**Sleep last night**")
            sl1, sl2 = st.columns(2)
            with sl1:
                c_sleep_hrs = st.number_input("Hours", 0.0, 12.0, prev_sleep_hrs, step=0.5)
            with sl2:
                c_sleep_q = st.slider("Quality", 1, 10, prev_sleep_q)

            st.markdown("**Gut & digestion**")
            g1, g2, g3 = st.columns(3)
            with g1:
                c_bloating = st.selectbox("Bloating", ["None", "Mild", "Moderate", "Severe"])
            with g2:
                c_digestion = st.selectbox("Digestion", ["Good", "Average", "Poor"])
            with g3:
                c_bowel = st.selectbox("Bowel", ["Normal", "Loose", "Constipated", "None today"])

            st.markdown("**Activity**")
            a1, a2 = st.columns(2)
            with a1:
                c_workout = st.selectbox("Today's workout",
                    ["Strength Training", "Padel", "Cardio", "Pilates",
                     "Walk/Steps only", "Rest day", "Other"])
            with a2:
                c_rumination = st.selectbox("Rumination",
                    ["None", "Mild (1-2 episodes)", "Moderate (3-5)", "Frequent (5+)"])

            c_notes = st.text_area("Anything else?",
                placeholder="Unusual symptoms, stress, travel, medication change...", height=80)

            if st.form_submit_button("✅ Save", type="primary", use_container_width=True):
                if cycle_day:
                    if cycle_day <= 5: c_phase = "Menstruation"
                    elif cycle_day <= 13: c_phase = "Follicular"
                    elif cycle_day <= 16: c_phase = "Ovulation"
                    else: c_phase = "Luteal"
                else:
                    c_phase = "Unknown"

                db_upsert("checkins", {
                    "user_id": user_id,
                    "checkin_date": date.today().isoformat(),
                    "cycle_day": cycle_day,
                    "cycle_phase": c_phase,
                    "energy": c_energy, "mood": c_mood, "stress": c_stress,
                    "sleep_hours": c_sleep_hrs, "sleep_quality": c_sleep_q,
                    "bloating": c_bloating, "digestion": c_digestion, "bowel": c_bowel,
                    "workout": c_workout, "rumination": c_rumination, "notes": c_notes,
                })
                st.session_state.system_prompt = build_system_prompt(user_id,
                    db_get_single("profiles", user_id))
                st.session_state.pop("checkin_insight", None)
                st.session_state.pop("edit_checkin", None)
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# COACH SECTION
# ══════════════════════════════════════════════════════════════════════════════

def _render_coach(user_id, profile, name, cycle_day, cycle_phase, days_to_next):
    st.markdown("## Your Coach")
    st.caption("OneSattva · Integrative Medicine · Functional Labs · Ayurveda · TCM")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Build full system prompt with roadmap + cycle context
    roadmap_chat_ctx = ""
    if st.session_state.get("treatment_roadmap") and st.session_state.get("roadmap_committed"):
        roadmap_chat_ctx += (f"\n\nCOMMITTED TREATMENT ROADMAP:\n"
                             f"{st.session_state.treatment_roadmap[:1500]}")
    if st.session_state.get("monthly_protocol"):
        roadmap_chat_ctx += f"\n\nCURRENT MONTH PROTOCOL:\n{st.session_state.monthly_protocol[:800]}"

    cycle_ctx = f"\n\nCURRENT CYCLE STATUS: {cycle_phase or 'Unknown phase'}"
    if cycle_day:
        cycle_ctx += f", Day {cycle_day}"
    if days_to_next:
        cycle_ctx += f", ~{days_to_next} days until next period"
    cycle_ctx += f". Today is {date.today().strftime('%A %d %B %Y')}. Factor this into all recommendations."

    full_system = st.session_state.system_prompt + cycle_ctx + roadmap_chat_ctx

    # Welcome screen
    if not st.session_state.messages:
        last_checkin = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        energy_note = ""
        if last_checkin:
            energy = last_checkin[0].get("energy")
            bloating = last_checkin[0].get("bloating", "")
            ci_date = last_checkin[0].get("checkin_date", "")
            if energy and int(energy) <= 4:
                energy_note = f"Last check-in ({ci_date}): low energy ({energy}/10)."
            elif bloating in ["Moderate", "Severe"]:
                energy_note = f"Last check-in ({ci_date}): {bloating.lower()} bloating."

        wearable_note = ""
        recent_w = db_get("wearable_data", user_id, order_col="data_date", limit=1)
        if recent_w and recent_w[0].get("recovery_score"):
            rec = recent_w[0]["recovery_score"]
            if float(rec) < 50:
                wearable_note = f"WHOOP recovery today: {rec}% — low."

        context_line = " · ".join(filter(None, [
            f"Day {cycle_day} · {cycle_phase.split(' (')[0]}" if cycle_day else None,
            energy_note or None,
            wearable_note or None,
        ]))

        first_name = name.split()[0] if name and name != "there" else "there"
        st.markdown(f"""
        <div style='background:var(--bone);padding:20px 24px;border-radius:14px;
                    border-left:3px solid #B6744A;margin-bottom:20px;'>
          <p style='font-family:Newsreader,serif;font-size:1.15rem;color:#111214;
                     margin:0 0 4px;font-weight:500;'>Good to see you, {first_name}.</p>
          <p style='font-family:Inter,sans-serif;font-size:13px;color:#6B6358;margin:0;'>
            I have your full profile, labs, and goals. Ask me anything — or pick a question below.
          </p>
          {f"<p style='font-family:Inter,sans-serif;font-size:12px;color:#B6744A;margin:8px 0 0;'>{context_line}</p>" if context_line else ""}
        </div>
        """, unsafe_allow_html=True)

        # Dynamic quick prompts
        q_supplement = ("💊 My supplement protocol today",
            f"Give me my complete supplement schedule for today ({date.today().strftime('%A')}), "
            f"Cycle Day {cycle_day or '?'} ({(cycle_phase or '').split(' (')[0]}). "
            "Exact brands, doses, and timing in order.")

        q_nutrition = ("🍽️ What to eat today",
            f"What should I eat today — {date.today().strftime('%A')}, Cycle Day {cycle_day or '?'}, "
            f"{(cycle_phase or '').split(' (')[0]} phase. "
            "Specific meals with portions and timing for my schedule.")

        if cycle_phase and "Luteal" in cycle_phase:
            q_dynamic = ("🧘 Managing luteal phase",
                f"I'm in Luteal phase, Day {cycle_day}. What should I do differently this week "
                "for training, nutrition, and lifestyle to manage luteal symptoms and support progesterone?")
        elif cycle_phase and "Follicular" in cycle_phase:
            q_dynamic = ("⚡ Maximising follicular phase",
                f"I'm in Follicular phase, Day {cycle_day}. What should I do differently this week "
                "to maximise the energy and anabolic advantage of this phase?")
        elif cycle_phase and "Ovulation" in cycle_phase:
            q_dynamic = ("🌸 Ovulation — what to do now",
                f"I'm at ovulation, Day {cycle_day}. What are the most important things to do in the "
                "next 48-72 hours — training, nutrition, lifestyle, and if relevant, fertility timing?")
        else:
            q_dynamic = ("🩸 Managing menstruation",
                f"I'm menstruating, Day {cycle_day}. What should I do differently this week — "
                "training modifications, nutrition priorities, and what to avoid?")

        if last_checkin and last_checkin[0].get("energy") and int(last_checkin[0]["energy"]) <= 4:
            q_energy = ("⚡ My energy is low — why?",
                f"My last check-in showed energy at {last_checkin[0]['energy']}/10. "
                "Based on my labs and current cycle phase, what are the most likely biological "
                "reasons and what can I do today to address them?")
        else:
            q_energy = ("⚖️ Why am I not losing weight?",
                "Based on my labs and current health picture, what are the specific biological "
                "blockers stopping me from losing weight? Be direct — what needs to change?")

        prompts = [q_supplement, q_nutrition, q_dynamic, q_energy]
        qc1, qc2 = st.columns(2)
        for i, (label, content) in enumerate(prompts):
            col = qc1 if i % 2 == 0 else qc2
            with col:
                if st.button(label, use_container_width=True, key=f"qp_{i}"):
                    st.session_state.messages.append({"role": "user", "content": content})
                    st.rerun()

    MAX_HISTORY = 20
    display_messages = st.session_state.messages[-MAX_HISTORY:]
    for message in display_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    ctrl1, ctrl2 = st.columns([5, 1])
    with ctrl2:
        if st.button("Clear chat", use_container_width=True, key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    if prompt := st.chat_input("Ask your Sattva anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner(""):
                response = ai_client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=4096,
                    system=full_system,
                    messages=st.session_state.messages[-MAX_HISTORY:]
                )
                reply = response.content[0].text
                st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})


# ══════════════════════════════════════════════════════════════════════════════
# PROFILE & DATA SECTION
# ══════════════════════════════════════════════════════════════════════════════

def _render_profile_and_data(user_id, profile, cycle_day, cycle_phase, days_to_next):
    pd_tab1, pd_tab2, pd_tab3 = st.tabs(["My Profile", "Lab Reports & Documents", "Wearable Data"])

    # ── MY PROFILE TAB ────────────────────────────────────────────────────────
    with pd_tab1:
        st.markdown("## My Profile")
        st.caption("Everything you bring to OneSattva — the foundation your coach reasons from.")

        if profile:
            pcol1, pcol2 = st.columns([2, 1])
            with pcol1:
                st.markdown(f"""
                <div style='background:var(--bone);border-radius:12px;padding:18px;margin-bottom:8px;'>
                  <p style='font-family:Newsreader,serif;font-size:1.3rem;color:#111214;margin:0 0 4px;'>
                    {profile.get('full_name','')}
                  </p>
                  <p style='font-family:Inter,sans-serif;font-size:13px;color:#6B6358;margin:0;'>
                    {profile.get('age','?')} years · {profile.get('sex','')} · 
                    {profile.get('height_cm','?')}cm · {profile.get('weight_kg','?')}kg · 
                    {profile.get('blood_group','')}
                  </p>
                  <p style='font-family:Inter,sans-serif;font-size:13px;color:#6B6358;margin:3px 0 0;'>
                    {profile.get('location','')} · {profile.get('diet','')}
                  </p>
                  {f"<p style='font-family:Inter,sans-serif;font-size:12px;color:#9B9B92;margin:3px 0 0;'>Allergies: {profile.get('allergies')}</p>" if profile.get('allergies') else ""}
                </div>
                """, unsafe_allow_html=True)
            with pcol2:
                st.markdown(f"""
                <div style='background:var(--bone);border-radius:12px;padding:18px;text-align:center;'>
                  <div style='font-family:JetBrains Mono,monospace;font-size:1.55rem;color:#B6744A;'>
                    Day {cycle_day or '?'}
                  </div>
                  <div style='font-family:Inter,sans-serif;font-size:12px;color:#6B6358;margin-top:4px;'>
                    {(cycle_phase or '').split(' (')[0]}
                  </div>
                  {f"<div style='font-family:Inter,sans-serif;font-size:11px;color:#9B9B92;margin-top:2px;'>~{days_to_next}d until next period</div>" if days_to_next else ""}
                </div>
                """, unsafe_allow_html=True)

        with st.expander("✏️ Edit personal details"):
            with st.form("profile_form"):
                pc1, pc2 = st.columns(2)
                with pc1:
                    p_name = st.text_input("Full Name", value=profile.get("full_name", "") if profile else "")
                    p_dob_val = profile.get("date_of_birth") if profile else None
                    p_dob = st.date_input("Date of birth",
                        value=date.fromisoformat(p_dob_val) if p_dob_val else date(1990, 1, 1),
                        min_value=date(1940, 1, 1), max_value=date.today())
                    p_sex = st.selectbox("Sex", ["", "Female", "Male", "Intersex"],
                        index=["", "Female", "Male", "Intersex"].index(profile.get("sex", ""))
                        if profile and profile.get("sex", "") in ["Female", "Male", "Intersex"] else 0)
                    p_height = st.number_input("Height (cm)", 100, 220,
                        value=int(profile.get("height_cm", 165)) if profile and profile.get("height_cm") else 165)
                with pc2:
                    p_weight = st.number_input("Weight (kg)", 30, 200,
                        value=int(profile.get("weight_kg", 60)) if profile and profile.get("weight_kg") else 60)
                    p_blood = st.selectbox("Blood Group",
                        ["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"],
                        index=["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"].index(
                            profile.get("blood_group", ""))
                        if profile and profile.get("blood_group", "") in
                        ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"] else 0)
                    p_location = st.text_input("Location",
                        value=profile.get("location", "") if profile else "")
                    p_diet = st.selectbox("Diet", [
                        "Vegetarian (no eggs)", "Vegetarian (with eggs)",
                        "Non-vegetarian", "Vegan", "Pescatarian"])
                p_allergies = st.text_input("Allergies",
                    value=profile.get("allergies", "") if profile else "")
                if st.form_submit_button("💾 Save", type="primary"):
                    age = (date.today() - p_dob).days // 365
                    success = db_upsert("profiles", {
                        "id": user_id, "full_name": p_name, "age": age,
                        "date_of_birth": p_dob.isoformat(), "sex": p_sex,
                        "height_cm": p_height, "weight_kg": p_weight,
                        "blood_group": p_blood, "location": p_location,
                        "diet": p_diet, "allergies": p_allergies,
                    })
                    if success:
                        st.success("Saved!")
                        st.session_state.system_prompt = build_system_prompt(user_id,
                            db_get_single("profiles", user_id))
                        st.rerun()

        st.divider()

        # Cycle tracking
        st.markdown("##### Cycle")
        cd = db_get_single("cycle_data", user_id)
        with st.form("cycle_profile_form"):
            cyc1, cyc2, cyc3 = st.columns(3)
            with cyc1:
                default_date = date.fromisoformat(cd["last_period_start"]) \
                    if cd and cd.get("last_period_start") else date.today()
                new_period_date = st.date_input("Last period start", value=default_date, key="profile_cycle_date")
            with cyc2:
                new_avg_len = st.number_input("Avg cycle length", 21, 40,
                    value=cd.get("avg_cycle_length", 27) if cd else 27, key="profile_avg_len")
            with cyc3:
                if cycle_day:
                    st.metric("Today", f"Day {cycle_day}")
            if st.form_submit_button("Update cycle data"):
                db_upsert("cycle_data", {"user_id": user_id,
                                         "last_period_start": new_period_date.isoformat(),
                                         "avg_cycle_length": new_avg_len})
                st.success("Updated!")
                st.rerun()

        st.divider()
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("##### Goals")
            goals = db_get("goals", user_id)
            for g in goals:
                gc1, gc2 = st.columns([5, 1])
                gc1.markdown(f"**{g['goal']}** · _{g.get('timeframe','')}_")
                if gc2.button("✕", key=f"del_goal_{g['id']}"):
                    db_delete("goals", g["id"]); st.rerun()
            with st.form("add_goal_profile"):
                gg1, gg2 = st.columns([3, 1])
                with gg1:
                    new_goal = st.text_input("New goal", placeholder="e.g. Reach 52kg by December")
                with gg2:
                    new_tf = st.selectbox("Timeframe", ["3 months", "6 months", "12 months", "12 months+"])
                if st.form_submit_button("+ Add") and new_goal:
                    db_upsert("goals", {"user_id": user_id, "goal": new_goal, "timeframe": new_tf})
                    st.rerun()

            st.divider()
            st.markdown("##### Medical conditions")
            conditions = db_get("medical_history", user_id)
            for c in conditions:
                cc1, cc2 = st.columns([5, 1])
                cc1.write(f"**{c['condition']}** — {c.get('notes','')[:50]}")
                if cc2.button("✕", key=f"del_cond_{c['id']}"):
                    db_delete("medical_history", c["id"]); st.rerun()
            with st.form("add_cond_profile"):
                nc1, nc2 = st.columns([3, 2])
                with nc1:
                    new_cond = st.text_input("Condition", placeholder="e.g. Hypothyroidism")
                with nc2:
                    new_notes = st.text_input("Notes", placeholder="e.g. since 2020")
                if st.form_submit_button("+ Add") and new_cond:
                    db_upsert("medical_history", {"user_id": user_id,
                                                  "condition": new_cond, "notes": new_notes})
                    st.rerun()

        with col_right:
            st.markdown("##### Medications")
            meds = db_get("medications", user_id)
            for m in meds:
                mc1, mc2 = st.columns([5, 1])
                mc1.write(f"**{m['name']}** — {m.get('dose','')} {m.get('frequency','')}")
                if mc2.button("✕", key=f"del_med_{m['id']}"):
                    db_delete("medications", m["id"]); st.rerun()
            with st.form("add_med_profile"):
                mm1, mm2, mm3 = st.columns(3)
                with mm1:
                    new_med = st.text_input("Medication")
                with mm2:
                    new_dose = st.text_input("Dose")
                with mm3:
                    new_freq = st.text_input("Frequency")
                if st.form_submit_button("+ Add") and new_med:
                    db_upsert("medications", {"user_id": user_id, "name": new_med,
                                              "dose": new_dose, "frequency": new_freq, "active": True})
                    st.rerun()

            st.divider()
            st.markdown("##### Supplements")
            supps = db_get("supplements", user_id)
            for s in supps:
                sc1, sc2 = st.columns([5, 1])
                sc1.write(f"**{s['name']}** — {s.get('dose','')} ({s.get('timing','')})")
                if sc2.button("✕", key=f"del_supp_{s['id']}"):
                    db_delete("supplements", s["id"]); st.rerun()
            with st.form("add_supp_profile"):
                ss1, ss2, ss3 = st.columns(3)
                with ss1:
                    new_supp = st.text_input("Supplement")
                with ss2:
                    new_sdose = st.text_input("Dose")
                with ss3:
                    new_stiming = st.text_input("Timing")
                if st.form_submit_button("+ Add") and new_supp:
                    db_upsert("supplements", {"user_id": user_id, "name": new_supp,
                                              "dose": new_sdose, "timing": new_stiming, "active": True})
                    st.rerun()

        st.divider()
        st.markdown("##### Profile notes")
        st.caption("Medication changes, new symptoms, anything your coach should know.")
        notes_rec = db_get_single("profile_notes", user_id)
        current_notes = notes_rec.get("notes", "") if notes_rec else ""
        new_notes = st.text_area("Notes", value=current_notes, height=100,
            placeholder="e.g. Started Thorne B-Complex on 15 June. Energy better since adding Magnesium.")
        if st.button("💾 Save notes", type="primary"):
            db_upsert("profile_notes", {"user_id": user_id, "notes": new_notes})
            st.session_state.system_prompt = build_system_prompt(user_id, profile)
            st.success("Saved.")

    # ── LAB REPORTS TAB ───────────────────────────────────────────────────────
    with pd_tab2:
        st.markdown("## Lab Reports & Documents")
        st.caption("Upload results — AI analyses against functional ranges and compares to your history.")

        all_labs = db_get("lab_reports", user_id, order_col="report_date")
        three_months_ago = date.today() - timedelta(days=90)

        if all_labs:
            latest_lab = all_labs[-1]
            try:
                latest_lab_date = date.fromisoformat(latest_lab["report_date"])
                lab_age_days = (date.today() - latest_lab_date).days
                if lab_age_days <= 90:
                    st.success(f"✅ Current labs: {latest_lab['report_date']} "
                               f"({lab_age_days} days ago) — within 3-month active window")
                elif lab_age_days <= 180:
                    st.warning(f"⚠️ Last labs: {latest_lab['report_date']} ({lab_age_days} days ago) "
                               "— consider retesting for current status")
                else:
                    st.error(f"🚨 Last labs: {latest_lab['report_date']} ({lab_age_days} days ago) "
                             "— too old. Retest needed.")
            except Exception:
                pass

        st.divider()

        with st.expander("📤 Upload new lab report", expanded=not bool(all_labs)):
            report_date_l = st.date_input("Report date", value=date.today(), key="lab_report_date")
            lab_name_l = st.text_input("Lab name", placeholder="e.g. Thyrocare, SRL, Apollo", key="lab_name")
            raw_values_l = st.text_area("Paste lab values", height=200, key="lab_raw_vals",
                placeholder="TSH: 1.83\nFT3: 2.2\nFT4: 1.31\nProlactin: 43.6\nFerritin: 35\n...")

            if st.button("🔍 Analyse & Save Report", type="primary",
                         use_container_width=True, key="lab_analyse_btn"):
                if raw_values_l.strip():
                    prev_lab_context = ""
                    if all_labs:
                        prev = all_labs[-1]
                        prev_lab_context = (f"\n\nMOST RECENT PREVIOUS REPORT "
                                            f"({prev['report_date']} · {prev.get('lab_name','')}):\n"
                                            f"{prev.get('raw_values','')[:800]}")

                    analysis_prompt = (
                        f"New lab report — date: {report_date_l.isoformat()}, lab: {lab_name_l}\n\n"
                        f"NEW VALUES:\n{raw_values_l}\n{prev_lab_context}\n\n"
                        "Analyse against functional medicine optimal ranges.\n\n"
                        "FORMAT — complete all sections fully:\n\n"
                        "## Key Findings\n"
                        "Table: Marker | Value | Functional Range | Status | Trend vs Previous\n"
                        "Status: ✅ Optimal · ⚠️ Suboptimal · 🚨 Needs attention\n"
                        "Trend: ↑ Rising · ↓ Falling · → Stable · — No previous data\n\n"
                        "## What This Report Tells Us\n2-3 sentences on overall clinical picture.\n\n"
                        "## Priority Actions\nNumbered list of 3-5 specific changes.\n\n"
                        "## What to Retest Next Time\nWhich markers and in how many weeks/months.\n\n"
                        "**Start today:** [one immediate action]\n\nComplete every section. Never cut off."
                    )

                    with st.spinner("Analysing against functional medicine ranges..."):
                        response = ai_client.messages.create(
                            model="claude-sonnet-4-6", max_tokens=4096,
                            system=st.session_state.system_prompt,
                            messages=[{"role": "user", "content": analysis_prompt}]
                        )
                        analysis = response.content[0].text

                    st.divider()
                    st.markdown(analysis)

                    sum_resp = ai_client.messages.create(
                        model="claude-sonnet-4-6", max_tokens=150,
                        messages=[{"role": "user",
                                   "content": f"One dense line summary, max 150 chars: {raw_values_l}"}]
                    )
                    db_upsert("lab_reports", {
                        "user_id": user_id,
                        "report_date": report_date_l.isoformat(),
                        "lab_name": lab_name_l,
                        "raw_values": raw_values_l,
                        "summary": sum_resp.content[0].text[:500],
                    })
                    st.success("✅ Report saved.")
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.rerun()
                else:
                    st.warning("Paste your lab values above.")

        st.divider()

        if not all_labs:
            st.info("No reports uploaded yet. Upload your first report above.")
        else:
            st.markdown(f"##### Lab history · {len(all_labs)} report(s)")
            if st.button("🗑️ Clear all lab history", key="clear_labs_btn"):
                for l in all_labs:
                    db_delete("lab_reports", l["id"])
                st.rerun()

            for lab in reversed(all_labs):
                try:
                    lab_date = date.fromisoformat(lab["report_date"])
                    age_days = (date.today() - lab_date).days
                    freshness_tag = "🟢 Current" if age_days <= 90 else (
                        "🟡 Recent" if age_days <= 180 else "⚪ Historical")
                except Exception:
                    freshness_tag = ""

                with st.expander(f"{freshness_tag} · {lab['report_date']} · {lab.get('lab_name','')}"):
                    st.caption(lab.get("summary", ""))
                    st.text_area("Raw values", value=lab.get("raw_values", ""),
                        key=f"lab_raw_{lab['id']}", height=120)
                    if st.button("🗑️ Delete this report", key=f"del_lab_{lab['id']}"):
                        db_delete("lab_reports", lab["id"])
                        st.rerun()

    # ── WEARABLE DATA TAB ─────────────────────────────────────────────────────
    with pd_tab3:
        st.markdown("## Wearable Data")
        st.caption("WHOOP data — recovery, HRV, sleep, and strain feed directly into your coach and protocols.")

        COL_MAP = {
            "date": ["Cycle start time", "Cycle Start Time", "Wake onset", "Date", "date"],
            "recovery_score": ["Recovery score %", "Recovery Score %", "Recovery Score", "recovery_score"],
            "hrv": ["Heart rate variability (ms)", "HRV (ms)", "Heart Rate Variability (ms)", "hrv"],
            "resting_hr": ["Resting heart rate (bpm)", "Resting Heart Rate (bpm)", "resting_hr"],
            "strain": ["Day Strain", "Strain", "Day strain", "strain"],
            "sleep_performance": ["Sleep performance %", "Sleep Performance %", "Sleep Performance", "sleep_performance"],
            "sleep_efficiency": ["Sleep efficiency %", "Sleep Efficiency %", "sleep_efficiency"],
            "sleep_duration": ["Asleep duration (min)", "Total sleep duration (min)", "sleep_duration"],
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

        import_method = st.radio("Import method", ["Upload WHOOP CSVs", "Manual entry"], horizontal=True)

        if import_method == "Upload WHOOP CSVs":
            st.caption("Export from WHOOP app → Profile → App Settings → Export Data")
            wc1, wc2 = st.columns(2)
            with wc1:
                cycles_file = st.file_uploader("📊 cycles.csv — recovery, HRV, RHR, strain",
                                               type=["csv"], key="cycles_up")
                sleep_file = st.file_uploader("😴 sleep.csv — sleep performance and stages",
                                              type=["csv"], key="sleep_up")
            with wc2:
                workout_file = st.file_uploader("🏋️ workout.csv — workout type and strain",
                                                type=["csv"], key="workout_up")
                st.file_uploader("📓 journal_entries.csv (optional)", type=["csv"], key="journal_up")

            if st.button("💾 Process & Save WHOOP Data", type="primary", use_container_width=True):
                merged = {}
                files_processed = 0

                for f, fields in [
                    (cycles_file, ["recovery_score", "hrv", "resting_hr", "strain"]),
                    (sleep_file, ["sleep_performance", "sleep_efficiency", "sleep_duration"]),
                ]:
                    if f:
                        try:
                            df = pd.read_csv(f)
                            date_col = find_col(df.columns.tolist(), COL_MAP["date"])
                            if not date_col:
                                st.warning(f"⚠️ {f.name}: couldn't find date column. "
                                           f"Columns: {', '.join(df.columns.tolist()[:8])}")
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
                                            except Exception:
                                                merged.setdefault(d, {})[field] = v
                            st.success(f"✅ {f.name}: {len(df)} rows · fields: {', '.join(found_fields)}")
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
                                        existing = merged.get(d, {}).get("workout_name", "")
                                        new_name = str(wdf[name_col].iloc[i])
                                        merged.setdefault(d, {})["workout_name"] = (
                                            f"{existing}+{new_name}".strip("+") if existing else new_name)
                                    if strain_col:
                                        try:
                                            merged.setdefault(d, {})["workout_strain"] = float(
                                                wdf[strain_col].iloc[i])
                                        except Exception:
                                            pass
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
                    st.warning("No files uploaded yet.")

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
                        "sleep_performance": w_sleep, "strain": w_strain, "resting_hr": w_rhr,
                    })
                    st.success("Saved!")
                    st.rerun()

        st.divider()

        wearable_all = db_get("wearable_data", user_id, order_col="data_date")
        if not wearable_all:
            st.info("No wearable data yet. Upload your WHOOP export above.")
        else:
            wdf_all = pd.DataFrame(wearable_all)
            wdf_all["data_date"] = pd.to_datetime(wdf_all["data_date"])
            wdf_all = wdf_all.sort_values("data_date")

            latest_w_date = wdf_all["data_date"].max().date()
            w_age = (date.today() - latest_w_date).days
            if w_age <= 2:
                st.success(f"✅ Wearable data current — last sync {latest_w_date}")
            elif w_age <= 7:
                st.info(f"ℹ️ Last sync {latest_w_date} ({w_age} days ago)")
            else:
                st.warning(f"⚠️ Last sync {latest_w_date} ({w_age} days ago) — consider re-importing")

            st.markdown("##### This week vs 30-day average")
            recent_7 = wdf_all.tail(7)
            recent_30 = wdf_all.tail(30)
            metrics_w = [
                ("recovery_score", "Recovery %"), ("hrv", "HRV ms"),
                ("resting_hr", "RHR bpm"), ("sleep_performance", "Sleep %"), ("strain", "Strain"),
            ]
            available = [(f, l) for f, l in metrics_w if f in wdf_all.columns]
            if available:
                wcols = st.columns(len(available))
                for i, (field, label) in enumerate(available):
                    week_val = pd.to_numeric(recent_7[field], errors="coerce").mean()
                    month_val = pd.to_numeric(recent_30[field], errors="coerce").mean()
                    if not pd.isna(week_val):
                        delta = round(week_val - month_val, 1) if not pd.isna(month_val) else None
                        wcols[i].metric(label, f"{week_val:.1f}",
                                        delta=f"{delta:+.1f} vs 30d avg" if delta is not None else None)

            chart_w1, chart_w2 = st.tabs(["Recovery & HRV", "Sleep & Strain"])
            with chart_w1:
                rc_fields = [f for f in ["recovery_score", "hrv"] if f in wdf_all.columns]
                if rc_fields:
                    st.line_chart(wdf_all[["data_date"] + rc_fields].set_index("data_date"))
            with chart_w2:
                sl_fields = [f for f in ["sleep_performance", "strain"] if f in wdf_all.columns]
                if sl_fields:
                    st.line_chart(wdf_all[["data_date"] + sl_fields].set_index("data_date"))

            st.divider()
            del1, del2 = st.columns(2)
            with del1:
                dates_list = wdf_all["data_date"].dt.strftime("%Y-%m-%d").tolist()
                del_date = st.selectbox("Delete a specific date",
                                        ["— select —"] + list(reversed(dates_list)), key="del_w_date")
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

            with st.expander("Full data table"):
                display_cols = ["data_date"] + [f for f, _ in metrics_w if f in wdf_all.columns]
                st.dataframe(wdf_all[display_cols].sort_values("data_date", ascending=False),
                             use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if "user" not in st.session_state:
    show_auth_screen()
else:
    # Re-attach session token on every rerun
    if "access_token" in st.session_state:
        supabase.postgrest.auth(st.session_state["access_token"])

    user = st.session_state["user"]
    user_id = user.id

    if "access_token" in st.session_state:
        profile_check = db_get_single("profiles", user_id)
        onboarding_complete = profile_check.get("onboarding_complete", False) if profile_check else False

        if not onboarding_complete:
            show_onboarding(user)
        else:
            show_main_app(user)
