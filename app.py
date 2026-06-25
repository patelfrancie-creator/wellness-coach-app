import streamlit as st
import anthropic
import os
import json as _json
from datetime import date, datetime, timedelta
import pandas as pd
from supabase import create_client, Client

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OneSattva",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='%23B68A3D'/></svg>",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --mist: #F2F3EF;
  --ink: #1C2330;
  --gold: #B68A3D;
  --signal: #3D5A52;
  --paper: #FAFAF7;
  --mid: #5B6270;
  --line: rgba(28,35,48,0.10);
}

html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }

h1, h2, h3 {
  font-family: 'Newsreader', serif !important;
  color: var(--ink) !important;
  font-weight: 500 !important;
}
h1 {
  font-size: 2.2rem !important;
  border-bottom: 1px solid var(--line);
  padding-bottom: 12px;
  margin-bottom: 1.2rem !important;
}

.stApp { background-color: var(--mist); }

[data-testid="stSidebar"] { background-color: var(--ink); }
[data-testid="stSidebar"] * { color: var(--mist) !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  color: var(--mist) !important;
  font-family: 'Newsreader', serif !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(242,243,239,0.10) !important; }

[data-testid="stSidebar"] .stButton > button {
  background-color: rgba(242,243,239,0.08) !important;
  border: 1px solid rgba(242,243,239,0.15) !important;
  color: #F2F3EF !important;
  font-family: Inter, sans-serif !important;
  font-size: 12px !important;
  font-weight: 400 !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background-color: rgba(242,243,239,0.15) !important;
  border-color: rgba(242,243,239,0.25) !important;
  color: #F2F3EF !important;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 4px;
  background-color: var(--paper);
  padding: 6px;
  border-radius: 12px;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 8px;
  color: var(--mid);
  font-weight: 500;
  padding: 10px 18px;
  font-family: 'Inter', sans-serif;
}
.stTabs [aria-selected="true"] {
  background-color: var(--paper) !important;
  color: var(--ink) !important;
  box-shadow: 0 1px 3px rgba(28,35,48,0.08);
}

.stButton > button {
  border-radius: 10px;
  border: 1.5px solid var(--line);
  color: var(--ink);
  background-color: var(--paper);
  font-weight: 500;
  font-family: 'Inter', sans-serif;
  transition: all 0.15s ease;
}
.stButton > button:hover {
  background-color: var(--ink);
  color: var(--mist);
  border-color: var(--ink);
}
.stButton > button[kind="primary"] {
  background-color: var(--ink);
  border-color: var(--ink);
  color: var(--mist);
}
.stButton > button[kind="primary"]:hover {
  background-color: var(--signal);
  border-color: var(--signal);
}

[data-testid="stAlert"] { border-radius: 10px; border-left-width: 3px; }

[data-testid="stMetric"] {
  background-color: var(--paper);
  padding: 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
}
[data-testid="stMetricLabel"] { color: var(--mid) !important; font-family: 'Inter', sans-serif; }
[data-testid="stMetricValue"] { color: var(--ink) !important; font-family: 'JetBrains Mono', monospace !important; }

[data-testid="stChatMessage"] {
  background-color: var(--paper);
  border-radius: 14px;
  border: 1px solid var(--line);
}

hr { border-color: var(--line) !important; margin: 1.5rem 0 !important; }

.triage-now {
  background: rgba(61,90,82,0.10);
  color: #3D5A52;
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 12.5px;
  font-family: 'Inter', sans-serif;
  display: inline-block;
}
.triage-watch {
  background: rgba(199,194,184,0.28);
  color: #6B6358;
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 12.5px;
  font-family: 'Inter', sans-serif;
  display: inline-block;
}

.lab-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: var(--ink);
}

input, textarea, select {
  font-family: 'Inter', sans-serif !important;
}

.stDataFrame { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--mid) !important; }
</style>
""", unsafe_allow_html=True)

# ── Config ─────────────────────────────────────────────────────────────────────
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ANTHROPIC_KEY = st.secrets["ANTHROPIC_KEY"]

# ── Clients ────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_anthropic():
    return anthropic.Anthropic(api_key=ANTHROPIC_KEY)

supabase = get_supabase()
ai_client = get_anthropic()

# ── Auth helpers ───────────────────────────────────────────────────────────────
def sign_up(email, password, full_name):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password, "options": {"data": {"full_name": full_name}}})
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        # CRITICAL: attach the authenticated session to the client so RLS policies
        # (auth.uid() = user_id) pass on every subsequent table call
        supabase.postgrest.auth(res.session.access_token)
        return res.user, res.session, None
    except Exception as e:
        return None, None, str(e)

def sign_out():
    supabase.auth.sign_out()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ── DB helpers ─────────────────────────────────────────────────────────────────
def db_get(table, user_id, order_col=None, limit=None):
    try:
        q = supabase.table(table).select("*").eq("user_id", user_id)
        if order_col:
            q = q.order(order_col, desc=True)
        if limit:
            q = q.limit(limit)
        return q.execute().data or []
    except:
        return []

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
    except:
        return False

def db_get_single(table, user_id):
    try:
        # profiles table uses 'id' as its key (references auth.users.id directly);
        # every other table uses 'user_id'
        key_col = "id" if table == "profiles" else "user_id"
        res = supabase.table(table).select("*").eq(key_col, user_id).limit(1).execute()
        return res.data[0] if res.data else None
    except:
        return None

# ── Cycle helpers ──────────────────────────────────────────────────────────────
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
    except:
        return None, None, None

# ── System prompt builder ──────────────────────────────────────────────────────
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
def show_auth_screen():
    # ── Brand mark ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='max-width:380px;margin:40px auto 24px;text-align:center;'>
      <div style='display:inline-flex;align-items:center;justify-content:center;gap:10px;margin-bottom:8px;'>
        <svg width="36" height="36" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="glow-login" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stop-color="#FAFAF7"/>
              <stop offset="62%" stop-color="#B68A3D"/>
              <stop offset="100%" stop-color="#1C2330" stop-opacity="0"/>
            </radialGradient>
          </defs>
          <circle cx="50" cy="50" r="32" fill="url(#glow-login)"/>
          <circle cx="50" cy="50" r="6" fill="#FAFAF7"/>
        </svg>
        <span style='font-family:Newsreader,serif;font-style:italic;font-size:2.2rem;color:#1C2330;line-height:1;'>
          <span style='font-style:normal;opacity:0.45;font-size:0.55em;vertical-align:0.3em;margin-right:0.02em;'>one</span>Sattva
        </span>
      </div>
      <p style='font-family:Newsreader,serif;font-style:italic;color:#B68A3D;font-size:0.95rem;margin:0 0 28px;letter-spacing:0.01em;'>With you. For you.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # ── Auth mode selector ────────────────────────────────────────────────────
        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "Sign In"

        auth_mode = st.radio("", ["Sign In", "Create Account"], horizontal=True,
            label_visibility="collapsed", key="auth_mode_radio",
            index=0 if st.session_state.auth_mode == "Sign In" else 1)
        st.session_state.auth_mode = auth_mode
        st.divider()

        # ── SIGN IN ───────────────────────────────────────────────────────────────
        if auth_mode == "Sign In":
            if st.session_state.get("show_forgot_password"):
                # Forgot password flow
                st.markdown("##### Reset your password")
                st.caption("Enter your email and we'll send you a reset link.")
                reset_email = st.text_input("Email address", key="reset_email_input")
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("Send reset link", type="primary", use_container_width=True):
                        if reset_email:
                            try:
                                supabase.auth.reset_password_email(
                                    reset_email,
                                    options={"redirect_to": "https://wellness-coach-app-f2ssjkdxdey8vm2c287mnz.streamlit.app"}
                                )
                                st.success("Reset link sent — check your email. The link expires in 1 hour.")
                                st.session_state.show_forgot_password = False
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.warning("Please enter your email address.")
                with rc2:
                    if st.button("Back to sign in", use_container_width=True):
                        st.session_state.show_forgot_password = False
                        st.rerun()
            else:
                # Normal sign in
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

                # Forgot password link
                st.markdown("<div style='text-align:center;margin-top:8px;'>", unsafe_allow_html=True)
                if st.button("Forgot your password?", key="forgot_pw_btn",
                             help="We'll send a reset link to your email"):
                    st.session_state.show_forgot_password = True
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        # ── CREATE ACCOUNT ────────────────────────────────────────────────────────
        else:
            full_name = st.text_input("Full name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")

            st.divider()

            # Disclaimer
            st.markdown("""
<div style='background:#F2F3EF;border-radius:10px;padding:14px 16px;margin-bottom:12px;font-size:12px;color:#5B6270;line-height:1.6;'>
<strong style='color:#1C2330;display:block;margin-bottom:6px;'>OneSattva is a pilot wellness tool — not a medical device</strong>
OneSattva provides AI-generated health guidance to support, not replace, qualified medical professionals.
This product is in closed pilot testing and is under active development. Do not use it as the sole basis for medical decisions.
Always consult your doctor before changing medications, supplements, or treatment plans.
</div>
""", unsafe_allow_html=True)

            # Consent checkboxes
            consent1 = st.checkbox(
                "I agree to OneSattva collecting and storing my personal health information "
                "(medical history, lab results, lifestyle data, wearable metrics) to generate "
                "personalised wellness guidance. My data is stored securely, not shared with "
                "third parties, and I can request deletion at any time by emailing "
                "patel.francie@gmail.com.",
                key="consent_general"
            )
            consent2 = st.checkbox(
                "I explicitly consent to OneSattva collecting and processing my sensitive health data "
                "— including medical conditions, medications, lab reports, and biometric information "
                "— for the purpose of generating personalised wellness recommendations. I understand "
                "I am participating in a closed pilot and the product is under active development.",
                key="consent_health_data"
            )

            st.divider()

            if st.button("Create Account", use_container_width=True, type="primary", key="signup_btn"):
                if not full_name or not email or not password:
                    st.warning("Please fill in all fields.")
                elif not consent1:
                    st.error("Please agree to the data collection terms to continue.")
                elif not consent2:
                    st.error("Please provide explicit consent for health data processing to continue.")
                else:
                    user, err = sign_up(email, password, full_name)
                    if err:
                        st.error(f"Sign up failed: {err}")
                    else:
                        st.success("Account created! Check your email for a verification link, then sign in.")

# ════════════════════════════════════════════════════════════════════════════════
# MAIN APP (shown when logged in)
# ════════════════════════════════════════════════════════════════════════════════


def show_main_app(user):
    user_id = user.id
    profile = db_get_single("profiles", user_id)
    name = profile.get("full_name", "there") if profile else "there"
    first_name = name.split()[0] if name and name != "there" else "there"
    cycle_day, cycle_phase, days_to_next = calculate_cycle_status(user_id)
    cycle_phase = cycle_phase or "Follicular (Day 1–14)"

    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = build_system_prompt(user_id, profile)

    # ── CSS ──────────────────────────────────────────────────────────────────────
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Inter',system-ui,sans-serif;}
.stApp{background:#F2F3EF;}
h1,h2,h3{font-family:'Newsreader',serif!important;font-weight:500!important;color:#1C2330!important;}
h1{font-size:2rem!important;border-bottom:1px solid rgba(28,35,48,0.08);padding-bottom:10px;margin-bottom:1.2rem!important;}
[data-testid="stSidebar"]{background:#1C2330!important;}
[data-testid="stSidebar"] *{color:#F2F3EF!important;}
[data-testid="stSidebar"] hr{border-color:rgba(242,243,239,0.10)!important;}
[data-testid="stSidebar"] .stButton>button{
  background:rgba(242,243,239,0.07)!important;
  border:0.5px solid rgba(242,243,239,0.12)!important;
  color:#F2F3EF!important;
  border-radius:8px!important;
  font-size:13px!important;
  text-align:left!important;
  width:100%!important;
}
[data-testid="stSidebar"] .stButton>button:hover{background:rgba(242,243,239,0.14)!important;}
.stTabs [data-baseweb="tab-list"]{background:#FAFAF7;border-radius:10px;padding:4px;gap:4px;}
.stTabs [data-baseweb="tab"]{border-radius:7px;color:#5B6270;font-weight:500;font-size:13px;padding:8px 16px;}
.stTabs [aria-selected="true"]{background:#FFFFFF!important;color:#1C2330!important;box-shadow:0 1px 3px rgba(28,35,48,0.08)!important;}
.stButton>button{border-radius:9px;border:0.5px solid rgba(28,35,48,0.12);color:#1C2330;background:#FFFFFF;font-weight:500;font-family:'Inter',sans-serif;}
.stButton>button[kind="primary"]{background:#1C2330;border-color:#1C2330;color:#F2F3EF;}
.stButton>button[kind="primary"]:hover{background:#3D5A52;border-color:#3D5A52;}
[data-testid="stMetric"]{background:#FFFFFF;border-radius:12px;border:0.5px solid rgba(28,35,48,0.10);padding:14px;}
[data-testid="stMetricValue"]{font-family:'JetBrains Mono',monospace!important;color:#1C2330!important;}
[data-testid="stMetricLabel"]{color:#5B6270!important;font-size:12px!important;}
[data-testid="stChatMessage"]{background:#FFFFFF;border-radius:12px;border:0.5px solid rgba(28,35,48,0.08);}
[data-testid="stAlert"]{border-radius:10px;}
hr{border-color:rgba(28,35,48,0.08)!important;margin:1.2rem 0!important;}
.os-card{background:#FFFFFF;border-radius:14px;border:0.5px solid rgba(28,35,48,0.10);padding:18px 20px;margin-bottom:12px;}
.os-dark{background:#1C2330;border-radius:14px;padding:18px 20px;margin-bottom:12px;}
.os-insight{background:#F2F3EF;border-left:3px solid #B68A3D;border-radius:0 10px 10px 0;padding:14px 18px;margin-bottom:14px;}
.os-mono{font-family:'JetBrains Mono',monospace;}
.os-label{font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#5B6270;}
.os-pill{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:500;}
.os-row{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:0.5px solid rgba(28,35,48,0.07);}
.os-row:last-child{border-bottom:none;}
input,textarea,select{font-family:'Inter',sans-serif!important;}
.stDataFrame{border:0.5px solid rgba(28,35,48,0.10);border-radius:10px;overflow:hidden;}
</style>
""", unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────────
    with st.sidebar:
        # Brand mark + wordmark
        st.markdown(f"""
<div style='padding:16px 0 20px;border-bottom:1px solid rgba(242,243,239,0.10);margin-bottom:20px;'>
  <div style='display:flex;align-items:center;gap:9px;margin-bottom:12px;'>
    <svg width="20" height="20" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <defs><radialGradient id="sg" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#F2F3EF"/>
        <stop offset="62%" stop-color="#B68A3D"/>
        <stop offset="100%" stop-color="#1C2330" stop-opacity="0"/>
      </radialGradient></defs>
      <circle cx="50" cy="50" r="32" fill="url(#sg)"/>
      <circle cx="50" cy="50" r="6" fill="#F2F3EF"/>
    </svg>
    <span style="font-family:'Newsreader',serif;font-style:italic;font-size:18px;color:#F2F3EF;line-height:1;">
      <span style="font-style:normal;opacity:0.45;font-size:0.55em;vertical-align:0.3em;margin-right:0.02em;">one</span>Sattva
    </span>
  </div>
  <p style="font-family:'Newsreader',serif;font-style:italic;font-size:0.8rem;color:#B68A3D;margin:0 0 10px;">With you. For you.</p>
  <p style="font-family:'Inter',sans-serif;font-size:13px;color:#F2F3EF;opacity:0.8;margin:0;">{name}</p>
  {f"<p style='font-family:Inter,sans-serif;font-size:11px;color:#F2F3EF;opacity:0.4;margin:2px 0 0;'>{profile.get('age','')}yr · {profile.get('location','')}</p>" if profile and profile.get('age') else ""}
</div>
""", unsafe_allow_html=True)

        # Cycle tracker
        st.markdown("<p style='font-family:Inter,sans-serif;font-size:11px;font-weight:600;letter-spacing:0.08em;color:#F2F3EF;opacity:0.4;margin:0 0 8px;text-transform:uppercase;'>Cycle</p>", unsafe_allow_html=True)
        if cycle_day:
            st.markdown(f"""
<div style='background:rgba(242,243,239,0.07);border-radius:10px;padding:12px 14px;margin-bottom:12px;'>
  <div style='font-family:"JetBrains Mono",monospace;font-size:24px;color:#F2F3EF;font-weight:500;line-height:1;'>Day {cycle_day}</div>
  <div style='font-family:Inter,sans-serif;font-size:12px;color:#F2F3EF;opacity:0.55;margin-top:4px;'>{(cycle_phase or '').split(' (')[0]}</div>
  {f"<div style='font-family:Inter,sans-serif;font-size:11px;color:#B68A3D;margin-top:5px;'>~{days_to_next}d until next period</div>" if days_to_next else ""}
</div>""", unsafe_allow_html=True)
            if st.button("New period started today", use_container_width=True, key="new_period_sb"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": date.today().isoformat()})
                st.session_state.system_prompt = build_system_prompt(user_id, profile)
                st.rerun()
        else:
            st.caption("Set period date in Profile → Cycle")

        st.divider()

        # Wearable snapshot
        wr = db_get("wearable_data", user_id, order_col="data_date", limit=1)
        if wr and wr[0].get("recovery_score"):
            rec = float(wr[0]["recovery_score"])
            col = "#1D9E75" if rec >= 67 else ("#B68A3D" if rec >= 34 else "#C8384A")
            st.markdown(f"""
<p style='font-family:Inter,sans-serif;font-size:11px;font-weight:600;letter-spacing:0.08em;color:#F2F3EF;opacity:0.4;margin:0 0 8px;text-transform:uppercase;'>Recovery</p>
<div style='background:rgba(242,243,239,0.07);border-radius:10px;padding:10px 14px;margin-bottom:12px;display:flex;align-items:center;gap:12px;'>
  <div style='font-family:"JetBrains Mono",monospace;font-size:22px;font-weight:500;color:{col};'>{rec:.0f}%</div>
  <div style='font-size:11px;color:#F2F3EF;opacity:0.5;'>HRV {wr[0].get("hrv","?") or "?"} ms</div>
</div>""", unsafe_allow_html=True)

        st.divider()
        st.markdown(f"<p style='font-family:Inter,sans-serif;font-size:11px;color:#F2F3EF;opacity:0.3;margin-bottom:8px;'>{user.email}</p>", unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True, key="signout_main"):
            sign_out()

    # ── Main tabs ─────────────────────────────────────────────────────────────────
    tab_home, tab_protocol, tab_checkin, tab_coach, tab_profile = st.tabs([
        "🏡 Home", "📅 Protocol", "📋 Check-in", "✦ Coach", "👤 Profile"
    ])

    # ════════════════════════════════════
    # HOME
    # ════════════════════════════════════
    with tab_home:
        now_h = datetime.now()
        hour_h = now_h.hour
        greeting = "Good morning" if hour_h < 12 else ("Good afternoon" if hour_h < 17 else "Good evening")

        st.markdown(f"""
<div style='padding:4px 0 16px;'>
  <h1 style='border:none!important;padding:0!important;margin-bottom:4px!important;font-size:2.2rem!important;'>{greeting}, {first_name}.</h1>
  <p style='font-size:14px;color:#5B6270;margin:0;'>{date.today().strftime('%A, %d %B %Y')} · Cycle Day {cycle_day or '?'} · {(cycle_phase or '').split(' (')[0]}</p>
</div>""", unsafe_allow_html=True)

        # Flags
        checkins_h = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        today_logged_h = checkins_h and checkins_h[0].get("checkin_date") == date.today().isoformat()
        labs_h = db_get("lab_reports", user_id, order_col="report_date", limit=1)

        if not today_logged_h:
            st.info("📋 Daily check-in not done yet — go to the Check-in tab.")
        if not labs_h:
            st.warning("🧪 No lab reports uploaded — your roadmap will be generic without them. Go to Profile → Labs.")
        elif labs_h:
            try:
                lab_age = (date.today() - date.fromisoformat(labs_h[0]["report_date"])).days
                if lab_age > 90:
                    st.warning(f"🧪 Labs are {lab_age} days old — consider retesting for current status.")
            except: pass
        if not st.session_state.get("roadmap_committed"):
            saved_rm_h = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
            if not saved_rm_h:
                st.info("🗺️ No treatment roadmap yet — generate one in Profile → Roadmap.")

        st.divider()

        # Status row
        hc1, hc2, hc3, hc4 = st.columns(4)
        with hc1:
            if today_logged_h:
                row_h = checkins_h[0]
                st.metric("Energy today", f"{row_h.get('energy','?')}/10")
            else:
                st.metric("Energy today", "—")
        with hc2:
            wr_h = db_get("wearable_data", user_id, order_col="data_date", limit=1)
            if wr_h and wr_h[0].get("recovery_score"):
                st.metric("Recovery", f"{float(wr_h[0]['recovery_score']):.0f}%")
            else:
                st.metric("Recovery", "—")
        with hc3:
            st.metric("Cycle day", cycle_day or "—")
        with hc4:
            saved_rm_h = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
            if saved_rm_h and saved_rm_h[0].get("committed"):
                try:
                    rm_s = datetime.fromisoformat(saved_rm_h[0]["generated_at"].replace("Z","")).date()
                    wk = (date.today() - rm_s).days // 7 + 1
                    ph = "Phase 1" if (date.today()-rm_s).days < 90 else ("Phase 2" if (date.today()-rm_s).days < 180 else "Phase 3")
                    st.metric("Roadmap", f"Week {wk} · {ph}")
                except: st.metric("Roadmap", "Active")
            else:
                st.metric("Roadmap", "Not started")

        # Monthly focus
        if st.session_state.get("monthly_protocol"):
            st.divider()
            st.markdown("##### This month's focus")
            st.markdown(f"""
<div class='os-insight'>
  <p style='font-size:13px;color:#1C2330;margin:0;line-height:1.7;'>{" ".join([l.strip() for l in st.session_state.monthly_protocol.split(chr(10)) if l.strip() and not l.startswith("#")][:5])}</p>
</div>""", unsafe_allow_html=True)

        # 7-day trends
        recent_h = db_get("checkins", user_id, order_col="checkin_date", limit=7)
        if recent_h and len(recent_h) >= 3:
            st.divider()
            st.markdown("##### Last 7 days")
            df_h = pd.DataFrame(recent_h)
            tc1, tc2, tc3, tc4 = st.columns(4)
            for col, field, label in [(tc1,"energy","Avg Energy"),(tc2,"mood","Avg Mood"),(tc3,"sleep_hours","Avg Sleep"),(tc4,"stress","Avg Stress")]:
                if field in df_h.columns:
                    val = pd.to_numeric(df_h[field], errors="coerce").mean()
                    suffix = "/10" if field != "sleep_hours" else "h"
                    col.metric(label, f"{val:.1f}{suffix}" if not pd.isna(val) else "—")

        # Goals
        goals_h = db_get("goals", user_id)
        if goals_h:
            st.divider()
            st.markdown("##### Goals")
            gcols = st.columns(min(len(goals_h), 3))
            for i, g in enumerate(goals_h[:3]):
                with gcols[i]:
                    st.markdown(f"""
<div class='os-card' style='height:100%;'>
  <p style='font-size:13px;color:#1C2330;margin:0 0 6px;font-weight:500;'>{g['goal'][:60]}</p>
  {f"<p class='os-pill' style='background:#F2F3EF;color:#B68A3D;margin:0;'>{g.get('timeframe','')}</p>" if g.get('timeframe') else ""}
</div>""", unsafe_allow_html=True)

    # ════════════════════════════════════
    # PROTOCOL
    # ════════════════════════════════════
    with tab_protocol:
        st.title("📅 Protocol")

        # Gap detection
        gap_ci = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        gap_days = 0
        if gap_ci:
            try: gap_days = (date.today() - date.fromisoformat(gap_ci[0]["checkin_date"])).days
            except: pass
        if gap_days >= 14:
            st.warning(f"⚠️ {gap_days} days since your last check-in. Update your coach before viewing your protocol.")
            gap_note = st.text_area("What's changed in the last few weeks?", key="gap_note_p")
            if st.button("Update and continue", type="primary"):
                if gap_note.strip():
                    en = db_get_single("profile_notes", user_id)
                    curr = en.get("notes","") if en else ""
                    db_upsert("profile_notes", {"user_id":user_id,"notes":curr+f"\n\n[Re-entry {date.today()}]: {gap_note}"})
                    st.session_state.weekly_protocol = None
                    st.session_state.monthly_protocol = None
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.rerun()
            st.stop()
        elif gap_days >= 7:
            st.info(f"Welcome back — {gap_days} days since last check-in. Has anything changed?")

        if not st.session_state.get("treatment_roadmap"):
            saved_p = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
            if saved_p:
                st.session_state.treatment_roadmap = saved_p[0]["roadmap_text"]
                st.session_state.roadmap_committed = saved_p[0].get("committed", False)
            else:
                st.info("Generate your Treatment Roadmap first — go to Profile → Roadmap tab.")
                st.stop()

        # Position
        saved_rm_p = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
        rm_start_p = date.today()
        if saved_rm_p:
            try: rm_start_p = datetime.fromisoformat(saved_rm_p[0]["generated_at"].replace("Z","")).date()
            except: pass
        days_in_p = (date.today() - rm_start_p).days
        week_num_p = (days_in_p // 7) + 1
        month_num_p = (days_in_p // 30) + 1
        phase_p = "Phase 1" if days_in_p < 90 else ("Phase 2" if days_in_p < 180 else "Phase 3")
        month_name_p = date.today().strftime("%B %Y")

        today_dt_p = datetime.now()
        day_names_p = [(today_dt_p + timedelta(days=i)).strftime("%A %d %b") for i in range(7)]
        days_str_p = ", ".join(day_names_p)

        st.caption(f"Week {week_num_p} · {day_names_p[0]} – {day_names_p[6]} · {phase_p} · Cycle Day {cycle_day or '?'}")

        # Monthly overview
        if "monthly_protocol" not in st.session_state:
            st.session_state.monthly_protocol = None
        if "monthly_month" not in st.session_state:
            st.session_state.monthly_month = None

        needs_monthly = not st.session_state.monthly_protocol or st.session_state.monthly_month != month_name_p
        with st.expander(f"📅 {month_name_p} — Month {month_num_p} overview", expanded=True):
            if needs_monthly:
                if st.button("Generate monthly overview", type="primary", key="gen_monthly"):
                    with st.spinner(f"Building {month_name_p} overview..."):
                        mp = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=1200,
                            system=st.session_state.system_prompt,
                            messages=[{"role":"user","content":f"""Month {month_num_p} protocol overview. {phase_p}. Week {week_num_p}. Cycle: {cycle_phase}.
Roadmap context: {(st.session_state.treatment_roadmap or '')[:800]}

FORMAT — concise:
**Month {month_num_p} focus:** [1 sentence]
**Milestones this month:** 3 bullets max
**Key changes:** table — Area | Change (Supplements / Nutrition / Training / Lifestyle)
**Monitor:** 2-3 things to log daily
**End of month check:** what to assess"""}])
                        st.session_state.monthly_protocol = mp.content[0].text
                        st.session_state.monthly_month = month_name_p
                        st.rerun()
            else:
                mcol1, mcol2 = st.columns([5,1])
                with mcol1: st.markdown(st.session_state.monthly_protocol)
                with mcol2:
                    if st.button("Refresh", key="refresh_month_p"):
                        st.session_state.monthly_protocol = None
                        st.rerun()

        st.divider()

        # Weekly protocol tabs
        if "weekly_protocol" not in st.session_state:
            st.session_state.weekly_protocol = None

        wp_col1, wp_col2 = st.columns([3,1])
        with wp_col1:
            st.markdown(f"**Week {week_num_p} · {day_names_p[0].split(' ')[0]} {day_names_p[0].split(' ')[1]} – {day_names_p[6].split(' ')[0]} {day_names_p[6].split(' ')[1]}**")
        with wp_col2:
            if st.session_state.weekly_protocol:
                all_wp = "\n\n---\n\n".join(st.session_state.weekly_protocol.values())
                st.download_button("⬇️ Download", data=all_wp, file_name=f"onesattva_week{week_num_p}.txt", use_container_width=True)

        if not st.session_state.weekly_protocol:
            focus = st.selectbox("Priority focus", ["Balanced","Fat loss","Fertility & conception","Gut healing","Energy & thyroid","Sleep & recovery"], key="wp_focus_p")
            if st.button("Generate this week's protocol", type="primary", use_container_width=True):
                default_phase_idx = 0
                phases_list = ["Follicular (Day 1–14)","Ovulation (Day 14–16)","Luteal (Day 16–28)","Menstruation (Day 1–5)"]
                if cycle_phase:
                    for i, p in enumerate(phases_list):
                        if cycle_phase.startswith(p.split(" (")[0]):
                            default_phase_idx = i; break
                wp_phase = phases_list[default_phase_idx]
                roadmap_ctx_p = f"\n\nROADMAP — Week {week_num_p}, {phase_p}:\n{(st.session_state.treatment_roadmap or '')[:1500]}\nMonthly overview:\n{st.session_state.monthly_protocol or ''}"
                base_p = f"""Week {week_num_p} · {phase_p} · Cycle Day {cycle_day or '?'} · {wp_phase} · Focus: {focus}
Days: {days_str_p}{roadmap_ctx_p}
RULES: Complete every table fully. Never cut off. Gut-friendly cooked foods only. No eggs. Thyronorm first on waking if prescribed."""

                with st.spinner("Building supplement & routine schedule..."):
                    r1 = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=2000,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":base_p+"\n\nGenerate ONLY: ## Daily Routine & Supplement Schedule\nMarkdown table: Time | Item | Dose | Notes\nThyronorm first if prescribed. All supplements with exact timing. Complete fully."}])
                    p1 = r1.content[0].text

                with st.spinner("Building 7-day nutrition plan..."):
                    r2 = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":base_p+f"\n\nGenerate ONLY: ## 7-Day Nutrition Plan\nMarkdown table. Columns: Meal Slot | {days_str_p}\nRows: Pre-Workout | First Meal (10-11am) | Lunch (2-3pm) | Snack (6-7pm) | Dinner (8-9pm) | Seed Cycling\nOne specific food + portion per cell, max 10 words. Complete all 7 days fully."}])
                    p2 = r2.content[0].text

                with st.spinner("Building training & lifestyle plan..."):
                    r3 = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=2500,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":base_p+f"\n\nGenerate ONLY:\n## 7-Day Training Plan\nTable: Day | Session | Focus | Key exercises\nDays: {days_str_p}. Cycle-phase appropriate loads. Include rest day.\n\n## This Week's Priorities\n3 bullets: sleep target, lifestyle practice, thing to monitor.\n\n**Start today ({day_names_p[0]}):** [one specific action]\n\nComplete both sections fully."}])
                    p3 = r3.content[0].text

                st.session_state.weekly_protocol = {"supps":p1,"nutrition":p2,"training":p3}
                st.rerun()
        else:
            wt1, wt2, wt3 = st.tabs(["💊 Supplements & Routine","🍽️ Nutrition","🏋️ Training & Lifestyle"])
            with wt1: st.markdown(st.session_state.weekly_protocol.get("supps",""))
            with wt2: st.markdown(st.session_state.weekly_protocol.get("nutrition",""))
            with wt3: st.markdown(st.session_state.weekly_protocol.get("training",""))
            if st.button("🔄 Regenerate this week", use_container_width=True):
                st.session_state.weekly_protocol = None; st.rerun()

    # ════════════════════════════════════
    # CHECK-IN
    # ════════════════════════════════════
    with tab_checkin:
        now_ci = datetime.now()
        time_str = "Morning" if now_ci.hour < 12 else ("Afternoon" if now_ci.hour < 17 else "Evening")
        st.title("📋 Daily Check-in")
        st.caption(f"{time_str} · {date.today().strftime('%A, %d %B')} · Cycle Day {cycle_day or '?'} · {(cycle_phase or '').split(' (')[0]}")

        today_ci2 = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        already_ci = today_ci2 and today_ci2[0].get("checkin_date") == date.today().isoformat()

        prev_ci = db_get("checkins", user_id, order_col="checkin_date", limit=2)
        yest_ci = prev_ci[1] if len(prev_ci) > 1 else None
        pe = int(yest_ci.get("energy",5)) if yest_ci else 5
        pm = int(yest_ci.get("mood",5)) if yest_ci else 5
        ps = int(yest_ci.get("stress",3)) if yest_ci else 3
        psh = float(yest_ci.get("sleep_hours",7)) if yest_ci else 7.0
        psq = int(yest_ci.get("sleep_quality",5)) if yest_ci else 5

        if already_ci and not st.session_state.get("edit_checkin"):
            row_ci = today_ci2[0]
            st.success("✅ Logged today")
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Energy", f"{row_ci.get('energy','?')}/10")
            c2.metric("Mood", f"{row_ci.get('mood','?')}/10")
            c3.metric("Sleep", f"{row_ci.get('sleep_hours','?')}h")
            c4.metric("Bloating", row_ci.get('bloating','?'))
            c5.metric("Workout", (row_ci.get('workout','?') or '')[:10])

            if "checkin_insight" not in st.session_state or not st.session_state.get("checkin_insight"):
                recent_insight = db_get("checkins", user_id, order_col="checkin_date", limit=7)
                with st.spinner(""):
                    ir = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=300,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":f"Today Day {cycle_day}, {cycle_phase}. Energy {row_ci.get('energy')}/10, bloating {row_ci.get('bloating')}, sleep {row_ci.get('sleep_hours')}h, workout {row_ci.get('workout')}. Pattern (last 5 days): {', '.join([f'E{c.get(chr(101)+chr(110)+chr(101)+chr(114)+chr(103)+chr(121),chr(63))} B{c.get(chr(98)+chr(108)+chr(111)+chr(97)+chr(116)+chr(105)+chr(110)+chr(103),chr(63))}' for c in (recent_insight or [])[:5]])}. ONE sharp clinical observation, 2 sentences max. Direct, specific. One action if warranted."}])
                    st.session_state.checkin_insight = ir.content[0].text

            if st.session_state.get("checkin_insight"):
                st.markdown(f'<div class="os-insight"><p style="font-size:13px;color:#1C2330;margin:0;line-height:1.7;">{st.session_state.checkin_insight}</p></div>', unsafe_allow_html=True)

            if st.button("✏️ Edit today's entry"):
                st.session_state.edit_checkin = True; st.rerun()
        else:
            if st.session_state.get("edit_checkin") and already_ci:
                row_ci = today_ci2[0]
                pe = int(row_ci.get("energy",pe)); pm = int(row_ci.get("mood",pm))
                ps = int(row_ci.get("stress",ps)); psh = float(row_ci.get("sleep_hours",psh))
                psq = int(row_ci.get("sleep_quality",psq))

            with st.form("ci_form_desk"):
                fc1, fc2 = st.columns(2)
                with fc1:
                    st.markdown("**How are you feeling?**")
                    c_energy = st.slider("Energy", 1, 10, pe)
                    c_mood = st.slider("Mood", 1, 10, pm)
                    c_stress = st.slider("Stress", 1, 10, ps)
                    st.markdown("**Sleep**")
                    c_sleep = st.number_input("Hours", 0.0, 12.0, psh, step=0.5)
                    c_sleepq = st.slider("Quality", 1, 10, psq)
                with fc2:
                    st.markdown("**Gut & digestion**")
                    c_bloat = st.selectbox("Bloating", ["None","Mild","Moderate","Severe"])
                    c_dig = st.selectbox("Digestion", ["Good","Average","Poor"])
                    c_bowel = st.selectbox("Bowel", ["Normal","Loose","Constipated","None today"])
                    st.markdown("**Activity**")
                    c_work = st.selectbox("Workout", ["Strength Training","Padel","Cardio","Pilates","Walk/Steps only","Rest day","Other"])
                    c_rum = st.selectbox("Rumination", ["None","Mild (1-2)","Moderate (3-5)","Frequent (5+)"])
                c_notes = st.text_area("Notes", placeholder="Anything unusual today...", height=72)
                if st.form_submit_button("✅ Save check-in", type="primary"):
                    if cycle_day:
                        cp = "Menstruation" if cycle_day<=5 else ("Follicular" if cycle_day<=13 else ("Ovulation" if cycle_day<=16 else "Luteal"))
                    else: cp = "Unknown"
                    db_upsert("checkins",{"user_id":user_id,"checkin_date":date.today().isoformat(),
                        "cycle_day":cycle_day,"cycle_phase":cp,"energy":c_energy,"mood":c_mood,
                        "stress":c_stress,"sleep_hours":c_sleep,"sleep_quality":c_sleepq,
                        "bloating":c_bloat,"digestion":c_dig,"bowel":c_bowel,
                        "workout":c_work,"rumination":c_rum,"notes":c_notes})
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.session_state.pop("checkin_insight", None)
                    st.session_state.pop("edit_checkin", None)
                    st.rerun()

    # ════════════════════════════════════
    # COACH
    # ════════════════════════════════════
    with tab_coach:
        st.title("✦ Your Coach")
        st.caption("Integrative medicine · Functional labs · Ayurveda · TCM")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        rm_ctx = ""
        if st.session_state.get("treatment_roadmap") and st.session_state.get("roadmap_committed"):
            rm_ctx += f"\n\nCOMMITTED ROADMAP:\n{st.session_state.treatment_roadmap[:1200]}"
        if st.session_state.get("monthly_protocol"):
            rm_ctx += f"\n\nMONTHLY PROTOCOL:\n{st.session_state.monthly_protocol[:600]}"
        cycle_ctx_c = f"\n\nTODAY: {date.today().strftime('%A %d %B %Y')} · Day {cycle_day or '?'} · {cycle_phase or 'Unknown'}"
        if days_to_next: cycle_ctx_c += f" · {days_to_next}d until next period"
        full_system_c = st.session_state.system_prompt + cycle_ctx_c + rm_ctx

        if not st.session_state.messages:
            last_ci_c = db_get("checkins", user_id, order_col="checkin_date", limit=1)
            ctx_bits = [f"Day {cycle_day}, {(cycle_phase or '').split(' (')[0]}"]
            if last_ci_c and last_ci_c[0].get("energy") and int(last_ci_c[0]["energy"]) <= 4:
                ctx_bits.append(f"Low energy ({last_ci_c[0]['energy']}/10)")
            if last_ci_c and last_ci_c[0].get("bloating") in ["Moderate","Severe"]:
                ctx_bits.append(f"{last_ci_c[0]['bloating'].lower()} bloating")
            wr_c = db_get("wearable_data", user_id, order_col="data_date", limit=1)
            if wr_c and wr_c[0].get("recovery_score") and float(wr_c[0]["recovery_score"]) < 50:
                ctx_bits.append(f"Recovery {float(wr_c[0]['recovery_score']):.0f}%")

            st.markdown(f'<div class="os-insight"><p style="font-size:14px;font-weight:500;color:#1C2330;margin:0 0 4px;">{first_name}\'s context today</p><p style="font-size:13px;color:#5B6270;margin:0;">{" · ".join(ctx_bits)}</p></div>', unsafe_allow_html=True)

            st.markdown("<p style='font-size:12px;font-weight:600;color:#5B6270;margin:0 0 8px;letter-spacing:0.06em;text-transform:uppercase;'>Quick questions</p>", unsafe_allow_html=True)
            quick = [
                (f"My supplement schedule today — Day {cycle_day} {(cycle_phase or '').split(' (')[0]}. Exact brands, doses, timing in order.", "Supplements today"),
                (f"What to eat today — Day {cycle_day}, {(cycle_phase or '').split(' (')[0]} phase. Specific meals with portions and timing for my schedule.", "What to eat today"),
                (f"I'm in {(cycle_phase or '').split(' (')[0]} phase, Day {cycle_day}. What should I do differently this week for training and lifestyle?", f"{(cycle_phase or '').split(' (')[0]} phase guidance"),
                ("Based on my labs — prolactin, FT3, ferritin — what are the specific biological blockers stopping me from losing weight? Be direct.", "Why am I not losing weight?"),
            ]
            qc1, qc2 = st.columns(2)
            for i, (pt, bl) in enumerate(quick):
                col = qc1 if i % 2 == 0 else qc2
                with col:
                    if st.button(f"{bl} ↗", use_container_width=True, key=f"qp_desk_{i}"):
                        st.session_state.messages.append({"role":"user","content":pt}); st.rerun()

        MAX_H = 20
        for msg in st.session_state.messages[-MAX_H:]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        _, clr = st.columns([6,1])
        with clr:
            if st.button("Clear", key="clear_chat_desk"):
                st.session_state.messages = []; st.rerun()

        if prompt_c := st.chat_input("Ask your Sattva anything..."):
            st.session_state.messages.append({"role":"user","content":prompt_c})
            with st.chat_message("user"): st.markdown(prompt_c)
            with st.chat_message("assistant"):
                with st.spinner(""):
                    r_c = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                        system=full_system_c, messages=st.session_state.messages[-MAX_H:])
                    reply_c = r_c.content[0].text
                    st.markdown(reply_c)
            st.session_state.messages.append({"role":"assistant","content":reply_c})

    # ════════════════════════════════════
    # PROFILE
    # ════════════════════════════════════
    with tab_profile:
        st.title("👤 Profile")

        pt1, pt2, pt3, pt4, pt5 = st.tabs(["Overview","Edit Details","Labs","Wearable","Roadmap"])

        # ── OVERVIEW ─────────────────────────────────────────────────────────────
        with pt1:
            if profile:
                ov1, ov2 = st.columns([2,1])
                with ov1:
                    st.markdown(f"""
<div class='os-card'>
  <p style='font-family:"Newsreader",serif;font-size:1.3rem;color:#1C2330;margin:0 0 4px;font-weight:500;'>{profile.get("full_name","")}</p>
  <p style='font-size:13px;color:#5B6270;margin:0;'>{profile.get("age","?")} yr · {profile.get("sex","")} · {profile.get("blood_group","")} · {profile.get("location","")}</p>
  <p style='font-size:13px;color:#5B6270;margin:3px 0 0;'>{profile.get("diet","")}{f" · Allergies: {profile.get('allergies')}" if profile.get("allergies") else ""}</p>
  {f"<p style='font-size:12px;color:#5B6270;margin:3px 0 0;'>Alcohol: {profile.get('alcohol')} · Smoking: {profile.get('smoking')}</p>" if profile.get("alcohol") and profile.get("alcohol") != "None" else ""}
</div>""", unsafe_allow_html=True)
                with ov2:
                    st.markdown(f"""
<div class='os-card' style='text-align:center;'>
  <p class='os-label' style='margin:0 0 6px;'>Today</p>
  <p style='font-family:"JetBrains Mono",monospace;font-size:2rem;color:#B68A3D;margin:0;'>Day {cycle_day or '?'}</p>
  <p style='font-size:12px;color:#5B6270;margin:4px 0 0;'>{(cycle_phase or '').split(' (')[0]}</p>
  {f"<p style='font-size:11px;color:#B68A3D;margin:4px 0 0;'>~{days_to_next}d until next period</p>" if days_to_next else ""}
</div>""", unsafe_allow_html=True)

            oc1, oc2 = st.columns(2)
            with oc1:
                conds = db_get("medical_history", user_id)
                if conds:
                    st.markdown("##### Conditions")
                    for c in conds:
                        st.markdown(f"<p style='font-size:13px;color:#1C2330;margin:0 0 4px;'>· **{c['condition']}** — <span style='color:#5B6270;'>{c.get('notes','')[:60]}</span></p>", unsafe_allow_html=True)
                meds = db_get("medications", user_id)
                if meds:
                    st.markdown("##### Medications")
                    for m in [x for x in meds if x.get("active",True)]:
                        st.markdown(f"<p style='font-size:13px;color:#1C2330;margin:0 0 4px;'>· **{m['name']}** {m.get('dose','')} — <span style='color:#5B6270;'>{m.get('frequency','')}</span></p>", unsafe_allow_html=True)
            with oc2:
                supps = db_get("supplements", user_id)
                if supps:
                    st.markdown("##### Supplements")
                    for s in [x for x in supps if x.get("active",True)]:
                        st.markdown(f"<p style='font-size:13px;color:#1C2330;margin:0 0 4px;'>· **{s['name']}** {s.get('dose','')} — <span style='color:#5B6270;'>{s.get('timing','')}</span></p>", unsafe_allow_html=True)
                goals_ov = db_get("goals", user_id)
                if goals_ov:
                    st.markdown("##### Goals")
                    for g in goals_ov:
                        st.markdown(f"<p style='font-size:13px;color:#1C2330;margin:0 0 4px;'>· {g['goal']} <span style='color:#B68A3D;font-size:11px;'>({g.get('timeframe','')})</span></p>", unsafe_allow_html=True)

            st.divider()
            st.markdown("##### Cycle tracking")
            cd_ov = db_get_single("cycle_data", user_id)
            with st.form("cycle_ov"):
                cc1, cc2 = st.columns(2)
                with cc1:
                    lp_ov = st.date_input("Last period start", value=date.fromisoformat(cd_ov["last_period_start"]) if cd_ov and cd_ov.get("last_period_start") else date.today())
                with cc2:
                    al_ov = st.number_input("Avg cycle length", 21, 40, value=cd_ov.get("avg_cycle_length",27) if cd_ov else 27)
                if st.form_submit_button("Update cycle data"):
                    db_upsert("cycle_data",{"user_id":user_id,"last_period_start":lp_ov.isoformat(),"avg_cycle_length":int(al_ov)})
                    st.success("Updated!"); st.rerun()

            st.divider()
            st.markdown("##### Update your coach")
            st.caption("Medication changes, new symptoms, anything your coach should know.")
            notes_ov = db_get_single("profile_notes", user_id)
            curr_ov = notes_ov.get("notes","") if notes_ov else ""
            new_notes_ov = st.text_area("Notes", value=curr_ov, height=100, placeholder="e.g. Started B-Complex on 15 June. Stopped Sampraz.", key="notes_1177")
            if st.button("Save notes", type="primary", key="save_notes_ov"):
                db_upsert("profile_notes",{"user_id":user_id,"notes":new_notes_ov})
                st.session_state.system_prompt = build_system_prompt(user_id, profile)
                st.success("Saved.")

        # ── EDIT DETAILS ─────────────────────────────────────────────────────────
        with pt2:
            with st.form("profile_edit"):
                ed1, ed2 = st.columns(2)
                with ed1:
                    p_name = st.text_input("Full name", value=profile.get("full_name","") if profile else "")
                    p_dob_v = profile.get("date_of_birth") if profile else None
                    p_dob = st.date_input("Date of birth", value=date.fromisoformat(p_dob_v) if p_dob_v else date(1990,1,1), min_value=date(1940,1,1), max_value=date.today())
                    p_sex = st.selectbox("Sex", ["","Female","Male","Intersex"], index=["","Female","Male","Intersex"].index(profile.get("sex","")) if profile and profile.get("sex","") in ["Female","Male","Intersex"] else 0)
                    p_h = st.number_input("Height (cm)", 100, 220, value=int(profile.get("height_cm",165)) if profile and profile.get("height_cm") else 165)
                with ed2:
                    p_w = st.number_input("Weight (kg)", 30, 200, value=int(profile.get("weight_kg",60)) if profile and profile.get("weight_kg") else 60)
                    p_bl = st.selectbox("Blood group", ["","A+","A-","B+","B-","O+","O-","AB+","AB-"], index=["","A+","A-","B+","B-","O+","O-","AB+","AB-"].index(profile.get("blood_group","")) if profile and profile.get("blood_group","") in ["A+","A-","B+","B-","O+","O-","AB+","AB-"] else 0)
                    p_loc = st.text_input("Location", value=profile.get("location","") if profile else "")
                    p_diet = st.selectbox("Diet", ["Vegetarian (no eggs)","Vegetarian (with eggs)","Non-vegetarian","Vegan","Pescatarian"])
                p_allerg = st.text_input("Allergies", value=profile.get("allergies","") if profile else "")
                if st.form_submit_button("Save", type="primary"):
                    age = (date.today()-p_dob).days//365
                    db_upsert("profiles",{"id":user_id,"full_name":p_name,"age":age,"date_of_birth":p_dob.isoformat(),"sex":p_sex,"height_cm":p_h,"weight_kg":p_w,"blood_group":p_bl,"location":p_loc,"diet":p_diet,"allergies":p_allerg})
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.success("Saved!"); st.rerun()

            st.divider()
            el1, el2 = st.columns(2)
            with el1:
                st.markdown("##### Goals")
                goals_e = db_get("goals", user_id)
                for g in goals_e:
                    gc1,gc2 = st.columns([5,1])
                    gc1.write(f"{g['goal'][:50]} _{g.get('timeframe','')}_")
                    if gc2.button("✕",key=f"dg_e_{g['id']}"): db_delete("goals",g["id"]); st.rerun()
                with st.form("ag_e"):
                    ag1,ag2 = st.columns([3,1])
                    with ag1: ng = st.text_input("Goal")
                    with ag2: ntf = st.selectbox("",["3mo","6mo","12mo","12mo+"])
                    if st.form_submit_button("+ Add") and ng:
                        db_upsert("goals",{"user_id":user_id,"goal":ng,"timeframe":ntf}); st.rerun()

                st.markdown("##### Conditions")
                conds_e = db_get("medical_history", user_id)
                for c in conds_e:
                    cc1,cc2 = st.columns([5,1])
                    cc1.write(f"**{c['condition']}** {c.get('notes','')[:40]}")
                    if cc2.button("✕",key=f"dc_e_{c['id']}"): db_delete("medical_history",c["id"]); st.rerun()
                with st.form("ac_e"):
                    ac1,ac2 = st.columns([3,2])
                    with ac1: nc = st.text_input("Condition")
                    with ac2: nn = st.text_input("Notes", key="notes_1230")
                    if st.form_submit_button("+ Add") and nc:
                        db_upsert("medical_history",{"user_id":user_id,"condition":nc,"notes":nn}); st.rerun()

            with el2:
                st.markdown("##### Medications")
                meds_e = db_get("medications", user_id)
                for m in meds_e:
                    mc1,mc2 = st.columns([5,1])
                    mc1.write(f"**{m['name']}** {m.get('dose','')} {m.get('frequency','')}")
                    if mc2.button("✕",key=f"dm_e_{m['id']}"): db_delete("medications",m["id"]); st.rerun()
                with st.form("am_e"):
                    am1,am2,am3 = st.columns(3)
                    with am1: nm = st.text_input("Medication")
                    with am2: nd = st.text_input("Dose")
                    with am3: nf = st.text_input("Frequency")
                    if st.form_submit_button("+ Add") and nm:
                        db_upsert("medications",{"user_id":user_id,"name":nm,"dose":nd,"frequency":nf,"active":True}); st.rerun()

                st.markdown("##### Supplements")
                supps_e = db_get("supplements", user_id)
                for s in supps_e:
                    sc1,sc2 = st.columns([5,1])
                    sc1.write(f"**{s['name']}** {s.get('dose','')} ({s.get('timing','')})")
                    if sc2.button("✕",key=f"ds_e_{s['id']}"): db_delete("supplements",s["id"]); st.rerun()
                with st.form("as_e"):
                    as1,as2,as3 = st.columns(3)
                    with as1: ns = st.text_input("Supplement")
                    with as2: nsd = st.text_input("Dose", key="dose_1258")
                    with as3: nst = st.text_input("Timing")
                    if st.form_submit_button("+ Add") and ns:
                        db_upsert("supplements",{"user_id":user_id,"name":ns,"dose":nsd,"timing":nst,"active":True}); st.rerun()

        # ── LABS ─────────────────────────────────────────────────────────────────
        with pt3:
            all_labs = db_get("lab_reports", user_id, order_col="report_date")
            if all_labs:
                try:
                    latest_l = all_labs[-1]
                    age_l = (date.today()-date.fromisoformat(latest_l["report_date"])).days
                    col_l = "#1D9E75" if age_l<=90 else ("#B68A3D" if age_l<=180 else "#C8384A")
                    tag_l = "✅ Current" if age_l<=90 else ("⚠️ Stale" if age_l<=180 else "🚨 Outdated")
                    st.markdown(f"<p style='font-size:13px;color:{col_l};margin:0 0 12px;'>{tag_l} · Last: {latest_l['report_date']} ({age_l} days ago)</p>", unsafe_allow_html=True)
                except: pass

            with st.expander("📤 Upload new report", expanded=not bool(all_labs)):
                ld = st.date_input("Report date", value=date.today(), key="lab_d_d")
                ln = st.text_input("Lab name", placeholder="Thyrocare, SRL, Apollo...", key="lab_n_d")
                lv = st.text_area("Paste lab values", height=180, key="lab_v_d",
                    placeholder="TSH: 1.83\nFT3: 2.2\nFT4: 1.31\nProlactin: 43.6\nFerritin: 35\nVitamin D: 46\n...")
                if st.button("Analyse & Save", type="primary", use_container_width=True, key="lab_save_d"):
                    if lv.strip():
                        prev_ctx_l = ""
                        if all_labs:
                            prev_l = all_labs[-1]
                            prev_ctx_l = f"\n\nPREVIOUS ({prev_l['report_date']} · {prev_l.get('lab_name','')}):\n{prev_l.get('raw_values','')[:600]}"
                        with st.spinner("Analysing against functional medicine ranges..."):
                            r_l = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                                system=st.session_state.system_prompt,
                                messages=[{"role":"user","content":f"Lab report {ld}, {ln}:\n{lv}{prev_ctx_l}\n\nAnalyse vs functional ranges. Complete all sections:\n\n## Key Findings\nTable: Marker | Value | Functional Range | Status (✅⚠️🚨) | vs Previous (↑↓→—)\n\n## Clinical picture\n2-3 sentences\n\n## Priority actions\n3-5 numbered, specific actions\n\n## Retest\nWhich markers and when\n\n**Start today:** [one action]"}])
                            st.divider()
                            st.markdown(r_l.content[0].text)
                            sr_l = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=120,
                                messages=[{"role":"user","content":f"One line, max 120 chars: {lv}"}])
                            db_upsert("lab_reports",{"user_id":user_id,"report_date":ld.isoformat(),"lab_name":ln,"raw_values":lv,"summary":sr_l.content[0].text[:500]})
                            st.success("✅ Saved.")
                            st.session_state.system_prompt = build_system_prompt(user_id, profile)
                            st.rerun()
                    else: st.warning("Paste lab values above.")

            if all_labs:
                st.markdown(f"##### {len(all_labs)} report(s)")
                if st.button("🗑️ Clear all lab history", key="clear_labs_d"):
                    for l in all_labs: db_delete("lab_reports",l["id"])
                    st.rerun()
                for lab in reversed(all_labs):
                    try:
                        age_t = (date.today()-date.fromisoformat(lab["report_date"])).days
                        tag_t = "🟢" if age_t<=90 else ("🟡" if age_t<=180 else "⚪")
                    except: tag_t = ""
                    with st.expander(f"{tag_t} {lab['report_date']} · {lab.get('lab_name','')}"):
                        st.caption(lab.get("summary",""))
                        st.text_area("Values", value=lab.get("raw_values",""), key=f"lrv_d_{lab['id']}", height=100)
                        if st.button("🗑️ Delete", key=f"dl_d_{lab['id']}"):
                            db_delete("lab_reports",lab["id"]); st.rerun()

        # ── WEARABLE ─────────────────────────────────────────────────────────────
        with pt4:
            COL_MAP_W = {
                "date":["Cycle start time","Cycle Start Time","Wake onset","Date","date"],
                "recovery_score":["Recovery score %","Recovery Score %","Recovery Score","recovery_score"],
                "hrv":["Heart rate variability (ms)","HRV (ms)","Heart Rate Variability (ms)","hrv"],
                "resting_hr":["Resting heart rate (bpm)","Resting Heart Rate (bpm)","resting_hr"],
                "strain":["Day Strain","Strain","Day strain","strain"],
                "sleep_performance":["Sleep performance %","Sleep Performance %","sleep_performance"],
                "sleep_efficiency":["Sleep efficiency %","Sleep Efficiency %","sleep_efficiency"],
                "sleep_duration":["Asleep duration (min)","Total sleep duration (min)","sleep_duration"],
                "workout_name":["Activity name","Activity Name","Sport","workout_name"],
                "workout_strain":["Activity Strain","Workout Strain","workout_strain"],
            }
            def fcw(cols, cands):
                cl = {c.lower():c for c in cols}
                for c in cands:
                    if c in cols: return c
                    if c.lower() in cl: return cl[c.lower()]
                return None

            st.caption("Export from WHOOP app → Profile → App Settings → Export Data")
            imp_w = st.radio("", ["Upload WHOOP CSVs","Manual entry"], horizontal=True, key="imp_w_d")
            if imp_w == "Upload WHOOP CSVs":
                wc1_d,wc2_d = st.columns(2)
                with wc1_d:
                    cf_d = st.file_uploader("cycles.csv",type=["csv"],key="wu_c_d")
                    sf_d = st.file_uploader("sleep.csv",type=["csv"],key="wu_s_d")
                with wc2_d:
                    wf_d = st.file_uploader("workout.csv",type=["csv"],key="wu_w_d")
                if st.button("Process & Save WHOOP Data", type="primary", use_container_width=True, key="whoop_save_d"):
                    merged_w = {}
                    for f_w, flds in [(cf_d,["recovery_score","hrv","resting_hr","strain"]),(sf_d,["sleep_performance","sleep_efficiency","sleep_duration"])]:
                        if f_w:
                            try:
                                df_w = pd.read_csv(f_w)
                                dc_w = fcw(df_w.columns.tolist(), COL_MAP_W["date"])
                                if not dc_w: st.warning(f"{f_w.name}: no date col. Found: {', '.join(df_w.columns.tolist()[:6])}"); continue
                                dts_w = pd.to_datetime(df_w[dc_w],errors="coerce").dt.strftime("%Y-%m-%d")
                                found_f = []
                                for fld in flds:
                                    col_w = fcw(df_w.columns.tolist(), COL_MAP_W[fld])
                                    if col_w:
                                        found_f.append(fld)
                                        for d_w,v_w in zip(dts_w,df_w[col_w]):
                                            if pd.notna(d_w) and pd.notna(v_w):
                                                try: merged_w.setdefault(d_w,{})[fld]=float(v_w)
                                                except: merged_w.setdefault(d_w,{})[fld]=v_w
                                st.success(f"✅ {f_w.name}: {len(df_w)} rows · {', '.join(found_f)}")
                            except Exception as e: st.error(f"{f_w.name}: {e}")
                    if wf_d:
                        try:
                            wdf_d = pd.read_csv(wf_d)
                            dc_wd = fcw(wdf_d.columns.tolist(), COL_MAP_W["date"])
                            if dc_wd:
                                dts_wd = pd.to_datetime(wdf_d[dc_wd],errors="coerce").dt.strftime("%Y-%m-%d")
                                nc_w = fcw(wdf_d.columns.tolist(), COL_MAP_W["workout_name"])
                                sc_w = fcw(wdf_d.columns.tolist(), COL_MAP_W["workout_strain"])
                                for i_w,d_wd in enumerate(dts_wd):
                                    if pd.notna(d_wd):
                                        if nc_w: merged_w.setdefault(d_wd,{})["workout_name"]=str(wdf_d[nc_w].iloc[i_w])
                                        if sc_w:
                                            try: merged_w.setdefault(d_wd,{})["workout_strain"]=float(wdf_d[sc_w].iloc[i_w])
                                            except: pass
                                st.success(f"✅ workout.csv: {len(wdf_d)} rows")
                        except Exception as e: st.error(f"workout.csv: {e}")
                    if merged_w:
                        for d_mw,vals_mw in merged_w.items():
                            db_upsert("wearable_data",{"user_id":user_id,"data_date":d_mw,**vals_mw})
                        st.success(f"✅ Saved {len(merged_w)} days.")
                        st.session_state.system_prompt = build_system_prompt(user_id, profile)
                        st.rerun()
            else:
                with st.form("mw_d"):
                    mwc1,mwc2 = st.columns(2)
                    with mwc1:
                        wd_d = st.date_input("Date",value=date.today())
                        wr2_d = st.number_input("Recovery (%)",0,100,50)
                        wh_d = st.number_input("HRV (ms)",0,200,40)
                    with mwc2:
                        ws_d = st.number_input("Sleep perf (%)",0,100,70)
                        wst_d = st.number_input("Strain",0.0,21.0,10.0,step=0.1)
                        wrhr_d = st.number_input("RHR (bpm)",30,120,65)
                    if st.form_submit_button("Save",type="primary"):
                        db_upsert("wearable_data",{"user_id":user_id,"data_date":wd_d.isoformat(),"recovery_score":wr2_d,"hrv":wh_d,"sleep_performance":ws_d,"strain":wst_d,"resting_hr":wrhr_d})
                        st.success("Saved!"); st.rerun()

            wall_d = db_get("wearable_data", user_id, order_col="data_date")
            if wall_d:
                wdf_da = pd.DataFrame(wall_d)
                wdf_da["data_date"] = pd.to_datetime(wdf_da["data_date"])
                wdf_da = wdf_da.sort_values("data_date")
                latest_wd = wdf_da["data_date"].max().date()
                w_age_d = (date.today()-latest_wd).days
                st.markdown(f"<p style='font-size:13px;color:{'#1D9E75' if w_age_d<=2 else '#B68A3D'};margin:12px 0;'>{'✅' if w_age_d<=2 else '⚠️'} Last sync: {latest_wd} ({w_age_d} days ago)</p>", unsafe_allow_html=True)

                r7_d = wdf_da.tail(7); r30_d = wdf_da.tail(30)
                mets_d = [("recovery_score","Recovery %"),("hrv","HRV ms"),("resting_hr","RHR"),("sleep_performance","Sleep %"),("strain","Strain")]
                avail_d = [(f,l) for f,l in mets_d if f in wdf_da.columns]
                if avail_d:
                    st.markdown("##### This week vs 30-day average")
                    wcols_d = st.columns(len(avail_d))
                    for i_d,(f_d,l_d) in enumerate(avail_d):
                        wv_d = pd.to_numeric(r7_d[f_d],errors="coerce").mean()
                        mv_d = pd.to_numeric(r30_d[f_d],errors="coerce").mean()
                        if not pd.isna(wv_d):
                            delta_d = round(wv_d-mv_d,1) if not pd.isna(mv_d) else None
                            wcols_d[i_d].metric(l_d,f"{wv_d:.1f}",delta=f"{delta_d:+.1f}" if delta_d else None)

                ct_d1,ct_d2 = st.tabs(["Recovery & HRV","Sleep & Strain"])
                with ct_d1:
                    rf_d = [f for f in ["recovery_score","hrv"] if f in wdf_da.columns]
                    if rf_d: st.line_chart(wdf_da[["data_date"]+rf_d].set_index("data_date"))
                with ct_d2:
                    sf_d2 = [f for f in ["sleep_performance","strain"] if f in wdf_da.columns]
                    if sf_d2: st.line_chart(wdf_da[["data_date"]+sf_d2].set_index("data_date"))

                dl_d1,dl_d2 = st.columns(2)
                with dl_d1:
                    dts_list_d = wdf_da["data_date"].dt.strftime("%Y-%m-%d").tolist()
                    dd_d = st.selectbox("Delete date",["—"]+list(reversed(dts_list_d)),key="del_wd_d")
                    if dd_d != "—" and st.button("Delete",key="del_wb_d"):
                        [db_delete("wearable_data",w["id"]) for w in wall_d if w["data_date"]==dd_d]
                        st.rerun()
                with dl_d2:
                    if st.button("Clear all wearable data",key="clear_wd_d"):
                        [db_delete("wearable_data",w["id"]) for w in wall_d]
                        st.rerun()

        # ── ROADMAP ───────────────────────────────────────────────────────────────
        with pt5:
            if "treatment_roadmap" not in st.session_state:
                st.session_state.treatment_roadmap = None
            if "roadmap_committed" not in st.session_state:
                st.session_state.roadmap_committed = False

            if not st.session_state.treatment_roadmap:
                saved_r = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
                if saved_r:
                    st.session_state.treatment_roadmap = saved_r[0]["roadmap_text"]
                    st.session_state.roadmap_committed = saved_r[0].get("committed",False)
                    try: st.session_state.roadmap_date = datetime.fromisoformat(saved_r[0]["generated_at"].replace("Z","")).strftime("%d %b %Y")
                    except: st.session_state.roadmap_date = "Previously"

            if st.session_state.treatment_roadmap and st.session_state.roadmap_committed:
                st.success(f"✅ Committed roadmap · {st.session_state.get('roadmap_date','')}")
                st.markdown(st.session_state.treatment_roadmap)
                st.divider()
                dl_r1, dl_r2 = st.columns(2)
                with dl_r1:
                    st.download_button("⬇️ Download roadmap", data=st.session_state.treatment_roadmap, file_name=f"onesattva_roadmap_{date.today()}.txt", use_container_width=True)
                with st.expander("⚠️ Update roadmap — significant change only"):
                    st.warning("Only update if something major has changed — new labs, new diagnosis, achieved a major goal.")
                    reason_r = st.text_area("What has changed?", key="rm_reason_d")
                    if st.button("Generate updated roadmap", type="primary", key="regen_rm_d") and reason_r.strip():
                        st.session_state.roadmap_committed = False
                        st.session_state.treatment_roadmap = None
                        st.session_state.roadmap_change_reason = reason_r
                        st.rerun()

            elif st.session_state.treatment_roadmap:
                st.info("Review your roadmap below. Commit when ready — this becomes your active plan.")
                st.markdown(st.session_state.treatment_roadmap)
                st.divider()
                rm_c1, rm_c2 = st.columns(2)
                with rm_c1:
                    if st.button("✅ Commit to this roadmap", type="primary", use_container_width=True, key="commit_rm_d"):
                        db_upsert("roadmaps",{"user_id":user_id,"roadmap_text":st.session_state.treatment_roadmap,"committed":True,"priority_focus":"","intensity":""})
                        st.session_state.roadmap_committed = True; st.rerun()
                with rm_c2:
                    if st.button("🔄 Regenerate", use_container_width=True, key="regen_rm_d2"):
                        st.session_state.treatment_roadmap = None; st.rerun()
            else:
                st.caption("Generate once, commit to it. Updates only when something significant changes.")
                rp_d = st.selectbox("Priority", ["Balanced — all areas","Fastest path to conception","Fastest path to fat loss","Gut/digestion first"], key="rp_d")
                ri_d = st.selectbox("Intensity", ["Moderate — sustainable","Aggressive — bigger changes faster"], key="ri_d")
                if st.button("🗺️ Generate my treatment roadmap", type="primary", use_container_width=True, key="gen_rm_d"):
                    chg = f"\n\nSIGNIFICANT CHANGE: {st.session_state.get('roadmap_change_reason','')}" if st.session_state.get("roadmap_change_reason") else ""
                    with st.spinner("Building your 12-month roadmap — takes 30-40 seconds..."):
                        r_rm = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                            system=st.session_state.system_prompt,
                            messages=[{"role":"user","content":f"""Generate a comprehensive 12-month treatment roadmap.
Priority: {rp_d} · Intensity: {ri_d}{chg}

Use the full patient profile, labs, check-ins, and wearable data from your context.

FORMAT — complete every section:

## Where Things Stand
3-4 sentences: core biological blockers right now and why the current approach is insufficient.

## Phase 1 — Months 0-3: [title]
Table: Change | Current → New | Clinical Reason (5-7 rows — supplements, diet, training, routine)
**Retest at 3 months:** [4-5 specific markers]
**Success looks like:** [2-3 measurable outcomes]

## Phase 2 — Months 3-6: [title]
Same table format, 4-5 rows
**Retest:** [markers] · **Success:** [outcomes]

## Phase 3 — Months 6-12: [title]
Same table, 3-4 rows
**Retest:** [markers] · **Success:** [outcomes]

## If Phase 1 shows no progress
2-3 sentences: what it means and escalation path

## After goals are achieved
Maintenance guidance

**Start today:** [one specific immediate action]"""}])
                        st.session_state.treatment_roadmap = r_rm.content[0].text
                        st.session_state.roadmap_date = date.today().strftime("%d %b %Y")
                        db_upsert("roadmaps",{"user_id":user_id,"roadmap_text":st.session_state.treatment_roadmap,"committed":False,"priority_focus":rp_d,"intensity":ri_d})
                        st.rerun()



def get_onboarding_state(user_id):
    try:
        res = supabase.table("onboarding").select("*").eq("user_id", user_id).limit(1).execute()
        return res.data[0] if res.data else None
    except:
        return None

def save_onboarding_state(user_id, data):
    try:
        data["user_id"] = user_id
        supabase.table("onboarding").upsert(data).execute()
    except Exception as e:
        st.error(f"Save error: {e}")

def calculate_completeness(user_id, ob_state):
    score = 0
    if ob_state and ob_state.get("step1_done"): score += 25
    if ob_state and ob_state.get("step2_done"): score += 25
    if ob_state and ob_state.get("step3_done"): score += 25
    labs = db_get("lab_reports", user_id)
    if labs:
        score += 25
    elif ob_state and ob_state.get("lab_upload_acknowledged"):
        score += 10
    return score

def show_onboarding(user):
    user_id = user.id

    ob = get_onboarding_state(user_id)
    if not ob:
        save_onboarding_state(user_id, {"current_step": 1})
        ob = get_onboarding_state(user_id)

    profile = db_get_single("profiles", user_id)
    current_step = ob.get("current_step", 1) if ob else 1

    # Header
    st.markdown("""
    <div style='text-align:center;padding:28px 0 20px;'>
      <div style='display:inline-flex;align-items:center;gap:10px;margin-bottom:8px;'>
        <svg width="28" height="28" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <defs><radialGradient id="og" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#FAFAF7"/>
            <stop offset="62%" stop-color="#B68A3D"/>
            <stop offset="100%" stop-color="#1C2330" stop-opacity="0"/>
          </radialGradient></defs>
          <circle cx="50" cy="50" r="32" fill="url(#og)"/>
          <circle cx="50" cy="50" r="6" fill="#FAFAF7"/>
        </svg>
        <span style="font-family:Newsreader,serif;font-style:italic;font-size:1.6rem;color:#1C2330;">
          <span style="font-style:normal;opacity:0.45;font-size:0.55em;vertical-align:0.3em;">one</span>Sattva
        </span>
      </div>
      <p style="font-family:Newsreader,serif;font-style:italic;color:#B68A3D;font-size:0.9rem;margin:4px 0 0;">With you. For you.</p>
      <p style="font-family:Inter,sans-serif;font-size:0.9rem;color:#5B6270;margin-top:10px;">Let's build your health profile — takes about 5 minutes.</p>
    </div>
    """, unsafe_allow_html=True)

    # Progress
    steps = ["Basic Info", "Health", "Lifestyle", "Labs", "Ready"]
    step_html = "<div style='display:flex;gap:5px;margin-bottom:10px;'>"
    for i, s in enumerate(steps):
        is_done = (i + 1) < current_step
        is_current = (i + 1) == current_step
        bg = "#1C2330" if is_done else ("#B68A3D" if is_current else "#E8E8E4")
        color = "#F2F3EF" if (is_done or is_current) else "#9B9B92"
        step_html += f"<div style='flex:1;text-align:center;background:{bg};color:{color};border-radius:8px;padding:8px 2px;font-family:Inter,sans-serif;font-size:11px;font-weight:500;'>{s}</div>"
    step_html += "</div>"
    st.markdown(step_html, unsafe_allow_html=True)
    done_steps = sum([ob.get(f"step{i}_done", False) for i in range(1,5)]) if ob else 0
    st.progress(max(int((done_steps/4)*100), 5))
    st.caption(f"Step {current_step} of 5")
    st.divider()

    col_main, col_r = st.columns([2,1])

    with col_main:

        # ── STEP 1 ──────────────────────────────────────────────────────────────
        if current_step == 1:
            st.markdown("### Basic information")
            with st.form("ob_step1"):
                c1, c2 = st.columns(2)
                with c1:
                    p_name = st.text_input("Full name *", value=profile.get("full_name","") if profile else "")
                    p_dob = st.date_input("Date of birth *",
                        value=date.fromisoformat(profile["date_of_birth"]) if profile and profile.get("date_of_birth") else date(1990,1,1),
                        min_value=date(1940,1,1), max_value=date.today())
                    p_sex = st.selectbox("Sex assigned at birth *", ["","Female","Male","Intersex"],
                        index=["","Female","Male","Intersex"].index(profile.get("sex","")) if profile and profile.get("sex","") in ["Female","Male","Intersex"] else 0)
                    p_blood = st.selectbox("Blood group", ["","A+","A-","B+","B-","O+","O-","AB+","AB-"], key="blood_group_1625",
                        index=["","A+","A-","B+","B-","O+","O-","AB+","AB-"].index(profile.get("blood_group","")) if profile and profile.get("blood_group","") in ["A+","A-","B+","B-","O+","O-","AB+","AB-"] else 0)
                with c2:
                    p_height = st.number_input("Height (cm) *", 100, 220, value=int(profile.get("height_cm",165)) if profile and profile.get("height_cm") else 165)
                    p_weight = st.number_input("Weight (kg) *", 30, 200, value=int(profile.get("weight_kg",60)) if profile and profile.get("weight_kg") else 60)
                    p_location = st.text_input("City / Location *", value=profile.get("location","") if profile else "")
                    p_diet = st.selectbox("Diet *", ["Vegetarian (no eggs)","Vegetarian (with eggs)","Non-vegetarian","Vegan","Pescatarian"])
                lc1, lc2, lc3 = st.columns(3)
                with lc1:
                    p_alcohol = st.selectbox("Alcohol", ["None","Occasional","Weekly","Daily"])
                with lc2:
                    p_smoking = st.selectbox("Smoking / Vaping", ["None","Occasional","Daily"])
                with lc3:
                    p_allergies = st.text_input("Known allergies", placeholder="e.g. gluten, nuts")
                if st.form_submit_button("Save & Continue →", type="primary", use_container_width=True):
                    if not p_name or not p_sex or not p_location:
                        st.error("Please fill in all required fields marked with *")
                    else:
                        age = (date.today() - p_dob).days // 365
                        db_upsert("profiles", {"id": user_id, "full_name": p_name, "age": age,
                            "date_of_birth": p_dob.isoformat(), "sex": p_sex,
                            "height_cm": p_height, "weight_kg": p_weight,
                            "location": p_location, "diet": p_diet, "blood_group": p_blood,
                            "alcohol": p_alcohol, "smoking": p_smoking, "allergies": p_allergies})
                        save_onboarding_state(user_id, {"current_step": 2, "step1_done": True})
                        st.rerun()

        # ── STEP 2 ──────────────────────────────────────────────────────────────
        elif current_step == 2:
            st.markdown("### Your health profile")
            st.caption("Add as little or as much as you're comfortable with. You can update this anytime.")

            st.markdown("##### Medical conditions & challenges")
            conditions = db_get("medical_history", user_id)
            for c in conditions:
                cc1, cc2 = st.columns([5,1])
                cc1.write(f"**{c['condition']}** — {c.get('notes','')[:60]}")
                if cc2.button("✕", key=f"dc_{c['id']}"):
                    db_delete("medical_history", c["id"]); st.rerun()
            with st.form("add_cond_ob"):
                nc1, nc2 = st.columns([3,2])
                with nc1: new_cond = st.text_input("Condition or challenge", placeholder="e.g. Hypothyroidism, PCOS")
                with nc2: new_notes = st.text_input("Notes", placeholder="e.g. diagnosed 2020", key="notes_1667")
                if st.form_submit_button("+ Add") and new_cond:
                    db_upsert("medical_history", {"user_id": user_id, "condition": new_cond, "notes": new_notes}); st.rerun()

            st.divider()
            st.markdown("##### Current medications")
            meds = db_get("medications", user_id)
            for m in meds:
                mc1, mc2 = st.columns([5,1])
                mc1.write(f"**{m['name']}** — {m.get('dose','')} {m.get('frequency','')}")
                if mc2.button("✕", key=f"dm_{m['id']}"):
                    db_delete("medications", m["id"]); st.rerun()
            with st.form("add_med_ob"):
                mm1, mm2, mm3 = st.columns(3)
                with mm1: new_med = st.text_input("Medication", placeholder="e.g. Thyronorm", key="medication_1681")
                with mm2: new_dose = st.text_input("Dose", placeholder="e.g. 50mcg", key="dose_1682")
                with mm3: new_freq = st.text_input("Frequency", placeholder="e.g. Daily on waking", key="frequency_1683")
                if st.form_submit_button("+ Add medication") and new_med:
                    db_upsert("medications", {"user_id": user_id, "name": new_med, "dose": new_dose, "frequency": new_freq, "active": True}); st.rerun()

            st.divider()
            st.markdown("##### Current supplements")
            supps = db_get("supplements", user_id)
            for s in supps:
                sc1, sc2 = st.columns([5,1])
                sc1.write(f"**{s['name']}** — {s.get('dose','')} ({s.get('timing','')})")
                if sc2.button("✕", key=f"ds_{s['id']}"):
                    db_delete("supplements", s["id"]); st.rerun()
            with st.form("add_supp_ob"):
                ss1, ss2, ss3 = st.columns(3)
                with ss1: new_supp = st.text_input("Supplement", placeholder="e.g. Magnesium Glycinate", key="supplement_1697")
                with ss2: new_sdose = st.text_input("Dose", placeholder="e.g. 400mg", key="dose_1698")
                with ss3: new_stiming = st.text_input("Timing", placeholder="e.g. Before bed", key="timing_1699")
                if st.form_submit_button("+ Add supplement") and new_supp:
                    db_upsert("supplements", {"user_id": user_id, "name": new_supp, "dose": new_sdose, "timing": new_stiming, "active": True}); st.rerun()

            st.divider()
            nav1, nav2 = st.columns(2)
            with nav1:
                if st.button("← Back", use_container_width=True, key="b2"):
                    save_onboarding_state(user_id, {"current_step": 1}); st.rerun()
            with nav2:
                if st.button("Save & Continue →", type="primary", use_container_width=True, key="n2"):
                    save_onboarding_state(user_id, {"current_step": 3, "step2_done": True}); st.rerun()

        # ── STEP 3 ──────────────────────────────────────────────────────────────
        elif current_step == 3:
            st.markdown("### Lifestyle & goals")

            with st.form("ob_step3_schedule"):
                st.markdown("##### Daily schedule")
                sc1, sc2, sc3 = st.columns(3)
                with sc1: wake_time = st.text_input("Wake time", value=profile.get("wake_time","7:00 AM") if profile and profile.get("wake_time") else "7:00 AM")
                with sc2: first_meal = st.text_input("First meal", placeholder="e.g. 9:00 AM")
                with sc3: sleep_time = st.text_input("Bedtime target", value=profile.get("sleep_time","10:30 PM") if profile and profile.get("sleep_time") else "10:30 PM")
                st.markdown("##### Exercise")
                ex1, ex2 = st.columns(2)
                with ex1:
                    workout_freq = st.selectbox("How often?", ["Not currently","1-2x per week","3-4x per week","5+ per week"])
                    workout_types = st.multiselect("Types", ["Strength training","Cardio","Yoga/Pilates","Swimming","Cycling","Team sports","Walking","Other"])
                with ex2:
                    workout_time = st.text_input("Preferred time", placeholder="e.g. 7:00 AM")
                    sleep_hours = st.number_input("Average sleep (hrs)", 3.0, 12.0, 7.0, step=0.5)
                if st.form_submit_button("Save schedule", use_container_width=True):
                    notes_val = f"Wake: {wake_time} | First meal: {first_meal} | Bedtime: {sleep_time} | Exercise: {workout_freq}, {', '.join(workout_types)}, at {workout_time} | Sleep: {sleep_hours}hrs"
                    db_upsert("profiles", {"id": user_id, "wake_time": wake_time, "sleep_time": sleep_time})
                    db_upsert("profile_notes", {"user_id": user_id, "notes": notes_val})
                    st.success("Schedule saved!")

            st.markdown("##### Goals")
            st.caption("Be specific. 'Lose weight' is less useful than 'reach 58kg and reduce belly fat by September.'")
            goals_list = db_get("goals", user_id)
            for g in goals_list:
                gc1, gc2 = st.columns([5,1])
                gc1.write(f"**{g['goal']}** · _{g.get('timeframe','')}_")
                if gc2.button("✕", key=f"dg_{g['id']}"):
                    db_delete("goals", g["id"]); st.rerun()
            with st.form("add_goal_ob"):
                gg1, gg2 = st.columns([3,1])
                with gg1: new_goal = st.text_input("Add a goal", placeholder="e.g. Resolve bloating and digestive issues")
                with gg2: new_tf = st.selectbox("Timeframe", ["3 months","6 months","12 months","12 months+"])
                if st.form_submit_button("+ Add goal") and new_goal:
                    db_upsert("goals", {"user_id": user_id, "goal": new_goal, "timeframe": new_tf}); st.rerun()

            st.markdown("##### Cycle tracking")
            st.caption("For females — this shapes your protocol around your cycle phases.")
            ob_cd = db_get_single("cycle_data", user_id)
            with st.form("cycle_ob"):
                cyc1, cyc2 = st.columns(2)
                with cyc1:
                    lp_date = st.date_input("Last period start", value=date.fromisoformat(ob_cd["last_period_start"]) if ob_cd and ob_cd.get("last_period_start") else date.today(), key="last_period_start_1757")
                with cyc2:
                    avg_len = st.number_input("Avg cycle length (days)", 21, 40, value=ob_cd.get("avg_cycle_length",28) if ob_cd else 28)
                if st.form_submit_button("Save cycle data"):
                    db_upsert("cycle_data", {"user_id": user_id, "last_period_start": lp_date.isoformat(), "avg_cycle_length": int(avg_len)})
                    st.success("Saved!")

            st.divider()
            nav1, nav2 = st.columns(2)
            with nav1:
                if st.button("← Back", use_container_width=True, key="b3"):
                    save_onboarding_state(user_id, {"current_step": 2}); st.rerun()
            with nav2:
                if st.button("Save & Continue →", type="primary", use_container_width=True, key="n3"):
                    save_onboarding_state(user_id, {"current_step": 4, "step3_done": True}); st.rerun()

        # ── STEP 4 ──────────────────────────────────────────────────────────────
        elif current_step == 4:
            st.markdown("### Lab reports")
            st.info("Lab reports are required for a precise treatment roadmap. Upload what you have — even a partial panel helps significantly.")

            with st.expander("📋 Recommended markers — what to get tested", expanded=False):
                st.markdown(MARKERS_INFO)

            existing_labs = db_get("lab_reports", user_id, order_col="report_date")
            if existing_labs:
                st.success(f"✅ {len(existing_labs)} report(s) uploaded.")
                for lab in existing_labs:
                    st.markdown(f"- **{lab['report_date']}** · {lab.get('lab_name','')} · {lab.get('summary','')[:80]}")
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
                                system="You are an expert integrative medicine practitioner. Analyse lab values against functional medicine optimal ranges. Be direct, specific, and concise.",
                                messages=[{"role":"user","content":f"Lab report {ob_lab_date}, lab: {ob_lab_name}\n\nValues:\n{ob_lab_vals}\n\nAnalyse against functional ranges. Format:\n## Key Findings\nTable: Marker | Value | Functional Status | Priority\n\n## Summary\n2-3 sentences on overall picture\n\n## Most Urgent\nTop 2-3 priorities"}]
                            )
                            st.divider()
                            st.markdown(resp.content[0].text)
                            sum_resp = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=150,
                                messages=[{"role":"user","content":f"One line summary max 120 chars: {ob_lab_vals}"}])
                            db_upsert("lab_reports", {"user_id": user_id, "report_date": ob_lab_date.isoformat(),
                                "lab_name": ob_lab_name, "raw_values": ob_lab_vals, "summary": sum_resp.content[0].text[:500]})
                            save_onboarding_state(user_id, {"step4_done": True, "lab_upload_acknowledged": True})
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
                if st.button("I'll upload labs within 2 weeks — continue", use_container_width=True, key="ob_lab_ack"):
                    save_onboarding_state(user_id, {"current_step": 5, "step4_done": True,
                        "lab_upload_acknowledged": True, "lab_acknowledged_at": datetime.now().isoformat()})
                    st.rerun()

            nav1, nav2 = st.columns(2)
            with nav1:
                if st.button("← Back", use_container_width=True, key="b4"):
                    save_onboarding_state(user_id, {"current_step": 3}); st.rerun()
            with nav2:
                if (has_labs or acknowledged) and st.button("Continue →", type="primary", use_container_width=True, key="n4"):
                    save_onboarding_state(user_id, {"current_step": 5, "step4_done": True}); st.rerun()

        # ── STEP 5 ──────────────────────────────────────────────────────────────
        elif current_step == 5:
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
                ("Basic information", ob_final.get("step1_done", False) if ob_final else False),
                ("Health profile", ob_final.get("step2_done", False) if ob_final else False),
                ("Lifestyle & goals", ob_final.get("step3_done", False) if ob_final else False),
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
                        ack_dt = datetime.fromisoformat(ob_ack_time.replace("Z",""))
                        days_remaining = max(0, 14 - (datetime.now() - ack_dt).days)
                    except: pass
                st.info(f"📋 {days_remaining} days remaining to upload labs. Roadmap will be provisional until then.")

            st.divider()
            st.markdown("**What happens next:**")
            st.markdown("""
- Your **12-month treatment roadmap** generates now
- **Monthly protocols** break it into milestones
- **Weekly protocols** give you the day-by-day detail
- **Your Sattva** is always there for questions
""")
            if completeness >= 50:
                if st.button("✦ Generate my treatment roadmap", type="primary", use_container_width=True, key="ob_finish"):
                    save_onboarding_state(user_id, {"completed": True, "completed_at": datetime.now().isoformat()})
                    db_upsert("profiles", {"id": user_id, "onboarding_complete": True})
                    st.balloons()
                    st.rerun()
            else:
                st.button("Complete more steps to unlock your roadmap", disabled=True, use_container_width=True)

            if st.button("← Back", key="b5"):
                save_onboarding_state(user_id, {"current_step": 4}); st.rerun()

    with col_r:
        tips = {
            1: ("Why we ask", "Your age, sex, height and weight affect how we interpret your labs and calibrate nutrition and training. Location helps us suggest locally available foods and brands. Alcohol and smoking directly influence hormone metabolism."),
            2: ("Your data is private", "Only you can see your health information. No one else — including practitioners — can access your data unless you explicitly grant permission. Add as much or as little as you're comfortable with."),
            3: ("Goals shape everything", "Your roadmap is built around your goals and their timeframes. After each goal is achieved, we build a maintenance guide so you keep the results long-term."),
            4: ("Why labs matter so much", "Functional medicine reads values differently from conventional medicine. A TSH of 2.5 might look 'normal' but mask a T3 conversion problem. Reports older than 3 months move to trend context only — recent labs always take priority."),
            5: ("You're in control", "Your roadmap is a living plan — it updates when your labs change, when you hit milestones, or when your goals shift. Nothing is set in stone.")
        }
        title, body = tips.get(current_step, ("", ""))
        if title:
            st.markdown(f"""
            <div style='background:#F2F3EF;border-radius:12px;padding:16px;margin-top:48px;'>
            <p style='font-family:Inter,sans-serif;font-weight:600;color:#1C2330;font-size:13px;margin:0 0 8px;'>{title}</p>
            <p style='font-family:Inter,sans-serif;color:#5B6270;font-size:13px;margin:0;line-height:1.5;'>{body}</p>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
if "user" not in st.session_state:
    show_auth_screen()
else:
    # Re-attach session token on every rerun
    if "access_token" in st.session_state:
        supabase.postgrest.auth(st.session_state["access_token"])

    user = st.session_state["user"]
    user_id = user.id

    # Check onboarding status
    if "access_token" in st.session_state:
        profile_check = db_get_single("profiles", user_id)
        onboarding_complete = profile_check.get("onboarding_complete", False) if profile_check else False

        if not onboarding_complete:
            show_onboarding(user)
        else:
            show_main_app(user)
# ════════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════════
if "user" not in st.session_state:
    show_auth_screen()
else:
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
