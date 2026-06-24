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
        auth_mode = st.radio("", ["Sign In", "Create Account"], horizontal=True, label_visibility="collapsed")
        st.divider()

        if auth_mode == "Sign In":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Sign In", use_container_width=True, type="primary"):
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

        else:
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password (min 6 characters)", type="password")
            if st.button("Create Account", use_container_width=True, type="primary"):
                if full_name and email and password:
                    user, err = sign_up(email, password, full_name)
                    if err:
                        st.error(f"Sign up failed: {err}")
                    else:
                        st.success("Account created! Please sign in.")
                else:
                    st.warning("Please fill in all fields.")

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
[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:0!important;max-width:430px!important;margin:0 auto!important;}
header[data-testid="stHeader"]{display:none!important;}
footer{display:none!important;}
.os-screen{display:none;padding:16px 16px 100px;}
.os-screen.active{display:block;}
.os-card{background:#FFFFFF;border-radius:14px;border:0.5px solid rgba(28,35,48,0.10);padding:14px 16px;margin-bottom:10px;}
.os-mono{font-family:'JetBrains Mono',monospace;}
.os-serif{font-family:'Newsreader',serif;}
.os-label{font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#5B6270;}
.os-big{font-size:28px;font-weight:500;line-height:1;font-family:'JetBrains Mono',monospace;}
.os-pill{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:500;}
.os-nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:430px;background:#FFFFFF;border-top:0.5px solid rgba(28,35,48,0.10);display:flex;z-index:999;padding:6px 0 env(safe-area-inset-bottom,6px);}
.os-tab{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px 4px;cursor:pointer;border:none;background:transparent;color:#5B6270;font-size:10px;font-family:'Inter',sans-serif;transition:color 0.15s;}
.os-tab i{font-size:22px;}
.os-tab.active{color:#B68A3D;}
.os-dark{background:#1C2330;border-radius:14px;padding:14px 16px;margin-bottom:10px;}
.os-metric-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;}
.os-metric{background:#FFFFFF;border-radius:14px;border:0.5px solid rgba(28,35,48,0.10);padding:12px 14px;}
.os-sub-tabs{display:flex;gap:6px;margin-bottom:12px;}
.os-sub-tab{flex:1;padding:8px;border-radius:10px;border:0.5px solid rgba(28,35,48,0.10);background:transparent;color:#5B6270;font-size:12px;font-weight:500;cursor:pointer;font-family:'Inter',sans-serif;transition:all 0.15s;}
.os-sub-tab.active{background:#1C2330;border-color:#1C2330;color:#F2F3EF;}
.os-insight{background:#F2F3EF;border-left:2px solid #B68A3D;border-radius:0 10px 10px 0;padding:12px 14px;margin-bottom:12px;}
.os-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:0.5px solid rgba(28,35,48,0.07);}
.os-row:last-child{border-bottom:none;}
.os-status-green{color:#1D9E75;}
.os-status-amber{color:#B68A3D;}
.os-status-red{color:#C8384A;}
.stButton>button{border-radius:10px;border:0.5px solid rgba(28,35,48,0.10);color:#1C2330;background:#FFFFFF;font-weight:500;font-family:'Inter',sans-serif;}
.stButton>button[kind="primary"]{background:#1C2330;border-color:#1C2330;color:#F2F3EF;}
[data-testid="stAlert"]{border-radius:10px;}
[data-testid="stMetric"]{background:#FFFFFF;border-radius:12px;border:0.5px solid rgba(28,35,48,0.10);padding:12px 14px;}
[data-testid="stMetricValue"]{font-family:'JetBrains Mono',monospace!important;}
input,textarea,select{font-family:'Inter',sans-serif!important;}
.stSlider{padding:0!important;}
hr{border-color:rgba(28,35,48,0.08)!important;}
</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@2.44.0/tabler-icons.min.css">
""", unsafe_allow_html=True)

    # ── Screen state ─────────────────────────────────────────────────────────────
    if "screen" not in st.session_state:
        st.session_state.screen = "home"
    if "proto_tab" not in st.session_state:
        st.session_state.proto_tab = "supps"
    if "profile_section" not in st.session_state:
        st.session_state.profile_section = "overview"

    screen = st.session_state.screen

    # ── Navigation JS injection ───────────────────────────────────────────────────
    st.markdown("""
<script>
function osNav(s){
  window.parent.postMessage({type:'streamlit:setComponentValue',value:s},'*');
}
</script>
""", unsafe_allow_html=True)

    # ── Nav bar ───────────────────────────────────────────────────────────────────
    nav_items = [
        ("home","ti-home","Home"),
        ("protocol","ti-calendar","Protocol"),
        ("checkin","ti-circle-plus","Check-in"),
        ("coach","ti-sparkles","Coach"),
        ("profile","ti-user","Profile"),
    ]
    nav_cols = st.columns(5)
    for i, (sid, icon, label) in enumerate(nav_items):
        with nav_cols[i]:
            active_style = "color:#B68A3D;font-weight:600;" if screen == sid else "color:#5B6270;"
            if st.button(f"{'●' if screen==sid else '○'} {label}", key=f"nav_{sid}",
                         use_container_width=True,
                         help=label):
                st.session_state.screen = sid
                st.session_state.checkin_insight = None
                st.rerun()

    st.divider()

    # ════════════════════════════════════
    # HOME SCREEN
    # ════════════════════════════════════
    if screen == "home":
        now = datetime.now()
        hour = now.hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

        # Header
        st.markdown(f"""
<div style='padding:4px 0 12px;'>
  <div style='display:flex;align-items:center;gap:7px;margin-bottom:6px;'>
    <svg width="16" height="16" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <defs><radialGradient id="hg" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#FAFAF7"/><stop offset="62%" stop-color="#B68A3D"/>
        <stop offset="100%" stop-color="#1C2330" stop-opacity="0"/>
      </radialGradient></defs>
      <circle cx="50" cy="50" r="32" fill="url(#hg)"/><circle cx="50" cy="50" r="6" fill="#FAFAF7"/>
    </svg>
    <span style="font-family:'Newsreader',serif;font-style:italic;font-size:13px;color:#1C2330;">
      <span style="font-style:normal;opacity:0.45;font-size:0.6em;vertical-align:0.28em;">one</span>Sattva
    </span>
  </div>
  <p style='font-size:22px;font-weight:500;margin:0;font-family:"Newsreader",serif;color:#1C2330;'>{greeting}, {first_name}.</p>
  <p style='font-size:12px;color:#5B6270;margin:3px 0 0;'>{date.today().strftime('%A, %d %B')} · Cycle Day {cycle_day or '?'} · {(cycle_phase or '').split(' (')[0]}</p>
</div>
""", unsafe_allow_html=True)

        # Check-in prompt or status
        checkins_today = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        today_logged = checkins_today and checkins_today[0].get("checkin_date") == date.today().isoformat()

        if not today_logged:
            st.markdown("""
<div style='background:#1C2330;border-radius:14px;padding:16px;margin-bottom:10px;'>
  <div style='display:flex;justify-content:space-between;align-items:center;'>
    <div>
      <p style='font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:rgba(242,243,239,0.45);margin:0 0 4px;'>Today's check-in</p>
      <p style='font-size:15px;color:#F2F3EF;margin:0;'>Not logged yet</p>
      <p style='font-size:11px;color:rgba(242,243,239,0.45);margin:3px 0 0;'>Takes 60 seconds</p>
    </div>
    <div style='width:38px;height:38px;border-radius:50%;background:#B68A3D;display:flex;align-items:center;justify-content:center;'>
      <span style='color:#F2F3EF;font-size:22px;line-height:1;'>+</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
            if st.button("Log today's check-in", use_container_width=True, type="primary", key="home_checkin_btn"):
                st.session_state.screen = "checkin"
                st.rerun()
        else:
            row = checkins_today[0]
            st.markdown(f"""
<div style='background:#F2F3EF;border-radius:14px;padding:12px 16px;margin-bottom:10px;border-left:2px solid #1D9E75;border-radius:0 14px 14px 0;'>
  <p style='font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#5B6270;margin:0 0 4px;'>Today logged ✓</p>
  <p style='font-size:13px;color:#1C2330;margin:0;'>Energy {row.get('energy','?')}/10 · Mood {row.get('mood','?')}/10 · Sleep {row.get('sleep_hours','?')}hrs · Bloating: {row.get('bloating','?')}</p>
</div>
""", unsafe_allow_html=True)

        # Status cards
        wearable_rec = db_get("wearable_data", user_id, order_col="data_date", limit=1)
        rec_score = None
        hrv_val = None
        if wearable_rec:
            rec_score = wearable_rec[0].get("recovery_score")
            hrv_val = wearable_rec[0].get("hrv")

        col1, col2 = st.columns(2)
        with col1:
            if rec_score:
                rec = float(rec_score)
                color = "#1D9E75" if rec >= 67 else ("#B68A3D" if rec >= 34 else "#C8384A")
                st.markdown(f"""
<div class='os-metric'>
  <p class='os-label' style='margin:0 0 6px;'>Recovery</p>
  <p class='os-big' style='color:{color};margin:0 0 2px;'>{rec:.0f}<span style='font-size:14px;opacity:0.5;'>%</span></p>
  <p style='font-size:11px;color:#5B6270;margin:0;'>HRV {hrv_val or '?'} ms</p>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
<div class='os-metric' style='border:0.5px dashed rgba(28,35,48,0.15);'>
  <p class='os-label' style='margin:0 0 6px;'>Recovery</p>
  <p style='font-size:12px;color:#5B6270;margin:0;'>No WHOOP data</p>
</div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
<div class='os-metric'>
  <p class='os-label' style='margin:0 0 6px;'>Cycle</p>
  <p class='os-big' style='color:#1C2330;margin:0 0 2px;'>{cycle_day or '?'}</p>
  <p style='font-size:11px;color:#5B6270;margin:0;'>{(cycle_phase or '').split(' (')[0]}{f' · {days_to_next}d' if days_to_next else ''}</p>
</div>""", unsafe_allow_html=True)

        # 7-day averages
        recent_ci = db_get("checkins", user_id, order_col="checkin_date", limit=7)
        if recent_ci and len(recent_ci) >= 3:
            df_r = pd.DataFrame(recent_ci)
            col3, col4 = st.columns(2)
            with col3:
                if "energy" in df_r.columns:
                    avg_e = pd.to_numeric(df_r["energy"], errors="coerce").mean()
                    st.markdown(f"""
<div class='os-metric'>
  <p class='os-label' style='margin:0 0 6px;'>Avg energy · 7d</p>
  <p class='os-big' style='color:#1C2330;margin:0 0 2px;'>{avg_e:.1f}<span style='font-size:14px;opacity:0.5;'>/10</span></p>
</div>""", unsafe_allow_html=True)
            with col4:
                saved_rm = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
                if saved_rm and saved_rm[0].get("committed"):
                    try:
                        rm_start = datetime.fromisoformat(saved_rm[0]["generated_at"].replace("Z","")).date()
                        days_in = (date.today() - rm_start).days
                        week_in = (days_in // 7) + 1
                        phase_in = "Phase 1" if days_in < 90 else ("Phase 2" if days_in < 180 else "Phase 3")
                        st.markdown(f"""
<div class='os-metric' style='cursor:pointer;'>
  <p class='os-label' style='margin:0 0 6px;'>Roadmap</p>
  <p class='os-big' style='color:#B68A3D;margin:0 0 2px;'>W{week_in}</p>
  <p style='font-size:11px;color:#5B6270;margin:0;'>{phase_in} · committed ✓</p>
</div>""", unsafe_allow_html=True)
                    except: pass

        # Monthly focus
        if st.session_state.get("monthly_protocol"):
            st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:14px 0 8px;'>This month's focus</p>", unsafe_allow_html=True)
            lines = [l.strip() for l in st.session_state.monthly_protocol.split("\n") if l.strip() and not l.startswith("#")][:4]
            st.markdown(f"""
<div class='os-card' style='border-left:2px solid #B68A3D;border-radius:0 14px 14px 0;'>
  <p style='font-size:13px;color:#1C2330;margin:0;line-height:1.6;'>{' '.join(lines[:2])}</p>
</div>""", unsafe_allow_html=True)

        # Goals
        goals = db_get("goals", user_id)
        if goals:
            st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:14px 0 8px;'>Goals</p>", unsafe_allow_html=True)
            for g in goals[:4]:
                tf = g.get("timeframe","")
                st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:#FFFFFF;border-radius:10px;border:0.5px solid rgba(28,35,48,0.10);margin-bottom:6px;'>
  <span style='font-size:13px;color:#1C2330;'>{g['goal'][:55]}</span>
  {f"<span style='font-size:11px;color:#B68A3D;white-space:nowrap;margin-left:8px;'>{tf}</span>" if tf else ""}
</div>""", unsafe_allow_html=True)

        # Flags
        labs_check = db_get("lab_reports", user_id, order_col="report_date", limit=1)
        if not labs_check:
            st.warning("No lab reports uploaded. Add them in Profile → Labs for a precise roadmap.")
        elif labs_check:
            try:
                lab_age = (date.today() - date.fromisoformat(labs_check[0]["report_date"])).days
                if lab_age > 90:
                    st.warning(f"Labs are {lab_age} days old — consider retesting.")
            except: pass

    # ════════════════════════════════════
    # PROTOCOL SCREEN
    # ════════════════════════════════════
    elif screen == "protocol":
        st.markdown("<p style='font-size:22px;font-weight:500;font-family:\"Newsreader\",serif;color:#1C2330;margin:4px 0 2px;'>Protocol</p>", unsafe_allow_html=True)

        # Gap detection
        checkins_gap = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        gap_days = 0
        if checkins_gap:
            try:
                gap_days = (date.today() - date.fromisoformat(checkins_gap[0]["checkin_date"])).days
            except: pass
        if gap_days >= 14:
            st.warning(f"It's been {gap_days} days since your last check-in. Update your coach before viewing your protocol.")
            note = st.text_area("What's changed?", placeholder="e.g. Travelling, stopped a supplement, energy has been low...", key="gap_note")
            if st.button("Update and continue", type="primary", use_container_width=True):
                if note.strip():
                    existing = db_get_single("profile_notes", user_id)
                    curr = existing.get("notes","") if existing else ""
                    db_upsert("profile_notes", {"user_id": user_id, "notes": curr + f"\n\n[Re-entry {date.today()}]: {note}"})
                    st.session_state.weekly_protocol = None
                    st.session_state.monthly_protocol = None
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.rerun()
            st.stop()
        elif gap_days >= 7:
            st.info(f"Welcome back — {gap_days} days since last check-in. Has anything changed?")

        if not st.session_state.get("treatment_roadmap"):
            saved = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
            if saved:
                st.session_state.treatment_roadmap = saved[0]["roadmap_text"]
                st.session_state.roadmap_committed = saved[0].get("committed", False)
            else:
                st.info("Generate your Treatment Roadmap first — go to Profile → Roadmap.")
                st.stop()

        # Calculate position
        saved_rm = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
        roadmap_start = date.today()
        if saved_rm:
            try:
                roadmap_start = datetime.fromisoformat(saved_rm[0]["generated_at"].replace("Z","")).date()
            except: pass
        days_in = (date.today() - roadmap_start).days
        week_num = (days_in // 7) + 1
        month_num = (days_in // 30) + 1
        phase = "Phase 1" if days_in < 90 else ("Phase 2" if days_in < 180 else "Phase 3")
        month_name = date.today().strftime("%B %Y")

        today_dt = datetime.now()
        day_names = [(today_dt + timedelta(days=i)).strftime("%A %d %b") for i in range(7)]
        days_str = ", ".join(day_names)

        st.markdown(f"<p style='font-size:12px;color:#5B6270;margin:0 0 14px;'>Week {week_num} · {day_names[0].split(' ')[0]} {day_names[0].split(' ')[1]} – {day_names[6].split(' ')[0]} {day_names[6].split(' ')[1]} · {phase}</p>", unsafe_allow_html=True)

        # Monthly overview
        if "monthly_protocol" not in st.session_state:
            st.session_state.monthly_protocol = None
        if "monthly_month" not in st.session_state:
            st.session_state.monthly_month = None

        if not st.session_state.monthly_protocol or st.session_state.monthly_month != month_name:
            with st.spinner(f"Building {month_name} overview..."):
                mp = ai_client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=1000,
                    system=st.session_state.system_prompt,
                    messages=[{"role":"user","content":f"""Month {month_num} protocol overview. {phase}. Week {week_num}. Cycle: {cycle_phase}.

FORMAT — concise, no fluff:
**Month {month_num} focus:** [1 sentence]
**Milestones:** 3 bullet points max
**Key changes this month:** table — Area | Change (Supplements / Nutrition / Training)
**Monitor:** 2-3 things to log
Keep it tight."""}])
                st.session_state.monthly_protocol = mp.content[0].text
                st.session_state.monthly_month = month_name

        with st.expander(f"📅 {month_name} — Month {month_num} overview", expanded=True):
            st.markdown(st.session_state.monthly_protocol)

        st.divider()

        # Sub-tab selector
        proto_tabs = [("supps","Supplements"), ("nutrition","Nutrition"), ("training","Training")]
        pt_cols = st.columns(3)
        for i, (tid, tlabel) in enumerate(proto_tabs):
            with pt_cols[i]:
                active = st.session_state.proto_tab == tid
                if st.button(tlabel, key=f"pt_{tid}", use_container_width=True,
                             type="primary" if active else "secondary"):
                    st.session_state.proto_tab = tid
                    st.rerun()

        # Generate button
        if "weekly_protocol" not in st.session_state:
            st.session_state.weekly_protocol = None

        if not st.session_state.weekly_protocol:
            if st.button("Generate this week's protocol", type="primary", use_container_width=True):
                default_phase_idx = 0
                if cycle_phase:
                    phases = ["Follicular (Day 1–14)","Ovulation (Day 14–16)","Luteal (Day 16–28)","Menstruation (Day 1–5)"]
                    for i, p in enumerate(phases):
                        if cycle_phase.startswith(p.split(" (")[0]):
                            default_phase_idx = i; break
                wp_phase = ["Follicular (Day 1–14)","Ovulation (Day 14–16)","Luteal (Day 16–28)","Menstruation (Day 1–5)"][default_phase_idx]
                roadmap_ctx = f"\n\nROADMAP — Week {week_num}, {phase}:\n{(st.session_state.treatment_roadmap or '')[:1500]}\nMonthly overview:\n{st.session_state.monthly_protocol or ''}"
                base = f"""Week {week_num} · {phase} · Cycle Day {cycle_day or '?'} · {wp_phase}
Days: {days_str}{roadmap_ctx}
RULES: Complete every table fully. Never cut off. Gut-friendly cooked foods. No eggs. Thyronorm first on waking if prescribed."""
                with st.spinner("Building supplements & routine..."):
                    r1 = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=2000, system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":base+"\n\nGenerate ONLY: ## Daily Routine & Supplement Schedule\nTable: Time | Item | Dose | Notes. Thyronorm first if prescribed. Complete all supplements."}])
                    p1 = r1.content[0].text
                with st.spinner("Building nutrition plan..."):
                    r2 = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096, system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":base+f"\n\nGenerate ONLY: ## 7-Day Nutrition Plan\nTable columns: Meal | {days_str}\nRows: Pre-Workout | First Meal (10-11am) | Lunch (2-3pm) | Snack (6-7pm) | Dinner (8-9pm) | Seed Cycling\nOne specific food + portion per cell, max 10 words. Complete all 7 days."}])
                    p2 = r2.content[0].text
                with st.spinner("Building training plan..."):
                    r3 = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=2500, system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":base+f"\n\nGenerate ONLY:\n## 7-Day Training Plan\nTable: Day | Session | Focus | Key exercises\nDays: {days_str}. Cycle-phase loads. Include rest day.\n\n## This Week\n3 bullets: sleep target, lifestyle practice, thing to monitor.\n**Start today:** [one action]"}])
                    p3 = r3.content[0].text
                st.session_state.weekly_protocol = {"supps":p1,"nutrition":p2,"training":p3}
                st.rerun()
        else:
            tab = st.session_state.proto_tab
            content = st.session_state.weekly_protocol.get(tab, "")
            st.markdown(content)
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Regenerate", use_container_width=True):
                    st.session_state.weekly_protocol = None; st.rerun()
            with col2:
                all_content = "\n\n".join(st.session_state.weekly_protocol.values())
                st.download_button("Download", data=all_content, file_name=f"onesattva_week{week_num}.txt", use_container_width=True)

    # ════════════════════════════════════
    # CHECK-IN SCREEN
    # ════════════════════════════════════
    elif screen == "checkin":
        now_ci = datetime.now()
        hour_ci = now_ci.hour
        time_str = "Morning" if hour_ci < 12 else ("Afternoon" if hour_ci < 17 else "Evening")
        st.markdown(f"<p style='font-size:22px;font-weight:500;font-family:\"Newsreader\",serif;color:#1C2330;margin:4px 0 2px;'>Check-in</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:12px;color:#5B6270;margin:0 0 14px;'>{time_str} · {date.today().strftime('%A %d %B')} · Day {cycle_day or '?'}</p>", unsafe_allow_html=True)

        today_ci = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        already = today_ci and today_ci[0].get("checkin_date") == date.today().isoformat()

        prev = db_get("checkins", user_id, order_col="checkin_date", limit=2)
        yest = prev[1] if len(prev) > 1 else None
        pe = int(yest.get("energy",5)) if yest else 5
        pm = int(yest.get("mood",5)) if yest else 5
        ps = int(yest.get("stress",3)) if yest else 3
        psh = float(yest.get("sleep_hours",7)) if yest else 7.0
        psq = int(yest.get("sleep_quality",5)) if yest else 5

        if already and not st.session_state.get("edit_checkin"):
            row = today_ci[0]
            st.markdown(f"""
<div style='background:#F2F3EF;border-left:2px solid #1D9E75;border-radius:0 14px 14px 0;padding:12px 14px;margin-bottom:12px;'>
  <p style='font-size:12px;font-weight:600;color:#5B6270;margin:0 0 4px;text-transform:uppercase;letter-spacing:0.06em;'>Logged today ✓</p>
  <p style='font-size:13px;color:#1C2330;margin:0;'>Energy {row.get('energy','?')} · Mood {row.get('mood','?')} · Sleep {row.get('sleep_hours','?')}h · {row.get('bloating','?')} bloating</p>
</div>""", unsafe_allow_html=True)

            if "checkin_insight" not in st.session_state or not st.session_state.checkin_insight:
                recent_for_insight = db_get("checkins", user_id, order_col="checkin_date", limit=7)
                with st.spinner(""):
                    ir = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=250,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":f"Today Day {cycle_day}, {cycle_phase}. Energy {row.get('energy')}/10, bloating {row.get('bloating')}, sleep {row.get('sleep_hours')}h. Recent pattern: {', '.join([f'Day {c.get(chr(99)+chr(121)+chr(99)+chr(108)+chr(101)+chr(95)+chr(100)+chr(97)+chr(121),chr(63))}: E{c.get(chr(101)+chr(110)+chr(101)+chr(114)+chr(103)+chr(121),chr(63))}' for c in (recent_for_insight or [])[:4]])}. ONE sharp clinical observation, 2-3 sentences. Direct and specific. End with one action if warranted."}])
                    st.session_state.checkin_insight = ir.content[0].text

            if st.session_state.get("checkin_insight"):
                st.markdown(f"""
<div class='os-insight'>
  <p style='font-size:13px;color:#1C2330;margin:0;line-height:1.6;'>{st.session_state.checkin_insight}</p>
</div>""", unsafe_allow_html=True)

            if st.button("Edit today's entry", use_container_width=True):
                st.session_state.edit_checkin = True; st.rerun()

        else:
            if st.session_state.get("edit_checkin") and already:
                row = today_ci[0]
                pe = int(row.get("energy",pe)); pm = int(row.get("mood",pm))
                ps = int(row.get("stress",ps)); psh = float(row.get("sleep_hours",psh))
                psq = int(row.get("sleep_quality",psq))

            with st.form("ci_form"):
                st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:0 0 10px;'>How are you feeling?</p>", unsafe_allow_html=True)
                c_energy = st.slider("Energy", 1, 10, pe)
                c_mood = st.slider("Mood", 1, 10, pm)
                c_stress = st.slider("Stress", 1, 10, ps)
                st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:12px 0 8px;'>Sleep</p>", unsafe_allow_html=True)
                sl1, sl2 = st.columns(2)
                with sl1: c_sleep = st.number_input("Hours", 0.0, 12.0, psh, step=0.5)
                with sl2: c_sleepq = st.slider("Quality", 1, 10, psq)
                st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:12px 0 8px;'>Gut</p>", unsafe_allow_html=True)
                g1, g2 = st.columns(2)
                with g1: c_bloat = st.selectbox("Bloating", ["None","Mild","Moderate","Severe"])
                with g2: c_dig = st.selectbox("Digestion", ["Good","Average","Poor"])
                c_bowel = st.selectbox("Bowel", ["Normal","Loose","Constipated","None today"])
                st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:12px 0 8px;'>Activity</p>", unsafe_allow_html=True)
                a1, a2 = st.columns(2)
                with a1: c_work = st.selectbox("Workout", ["Strength Training","Padel","Cardio","Pilates","Walk/Steps only","Rest day","Other"])
                with a2: c_rum = st.selectbox("Rumination", ["None","Mild (1-2)","Moderate (3-5)","Frequent (5+)"])
                c_notes = st.text_area("Notes", placeholder="Anything unusual...", height=72)
                if st.form_submit_button("Save", type="primary", use_container_width=True):
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
    # COACH SCREEN
    # ════════════════════════════════════
    elif screen == "coach":
        st.markdown("<p style='font-size:22px;font-weight:500;font-family:\"Newsreader\",serif;color:#1C2330;margin:4px 0 2px;'>Your Sattva</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px;color:#5B6270;margin:0 0 14px;'>Integrative medicine · Functional labs · Ayurveda · TCM</p>", unsafe_allow_html=True)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        roadmap_ctx = ""
        if st.session_state.get("treatment_roadmap") and st.session_state.get("roadmap_committed"):
            roadmap_ctx += f"\n\nCOMMITTED ROADMAP:\n{st.session_state.treatment_roadmap[:1200]}"
        if st.session_state.get("monthly_protocol"):
            roadmap_ctx += f"\n\nMONTHLY PROTOCOL:\n{st.session_state.monthly_protocol[:600]}"
        cycle_ctx = f"\n\nTODAY: {date.today().strftime('%A %d %B %Y')} · Cycle Day {cycle_day or '?'} · {cycle_phase or 'Unknown'}"
        if days_to_next: cycle_ctx += f" · {days_to_next}d until next period"
        full_system = st.session_state.system_prompt + cycle_ctx + roadmap_ctx

        if not st.session_state.messages:
            last_ci = db_get("checkins", user_id, order_col="checkin_date", limit=1)
            ctx_line = f"Day {cycle_day}, {(cycle_phase or '').split(' (')[0]}"
            if last_ci and last_ci[0].get("energy") and int(last_ci[0]["energy"]) <= 4:
                ctx_line += f" · Low energy ({last_ci[0]['energy']}/10) logged"
            elif last_ci and last_ci[0].get("bloating") in ["Moderate","Severe"]:
                ctx_line += f" · {last_ci[0]['bloating'].lower()} bloating logged"
            wr = db_get("wearable_data", user_id, order_col="data_date", limit=1)
            if wr and wr[0].get("recovery_score") and float(wr[0]["recovery_score"]) < 50:
                ctx_line += f" · Recovery {float(wr[0]['recovery_score']):.0f}%"

            st.markdown(f"""
<div class='os-insight' style='margin-bottom:16px;'>
  <p style='font-size:13px;color:#1C2330;margin:0 0 4px;font-weight:500;'>Good to see you, {first_name}.</p>
  <p style='font-size:12px;color:#5B6270;margin:0;'>{ctx_line}</p>
</div>""", unsafe_allow_html=True)

            st.markdown("<p style='font-size:12px;font-weight:600;color:#5B6270;margin:0 0 8px;letter-spacing:0.05em;text-transform:uppercase;'>Ask me</p>", unsafe_allow_html=True)
            quick_prompts = [
                (f"Supplements today, Day {cycle_day} {(cycle_phase or '').split(' (')[0]} — exact brands, doses, timing in order.",
                 "Supplements today"),
                (f"What to eat today — Day {cycle_day}, {(cycle_phase or '').split(' (')[0]} phase. Specific meals with portions and timing.",
                 "What to eat today"),
                (f"I'm in {(cycle_phase or '').split(' (')[0]} phase, Day {cycle_day}. What should I do differently this week for training and lifestyle?",
                 f"{(cycle_phase or '').split(' (')[0]} phase guidance"),
                ("Based on my labs — prolactin, FT3, ferritin — what are the specific biological blockers stopping me from losing weight?",
                 "Why am I not losing weight?"),
            ]
            for prompt_text, btn_label in quick_prompts:
                if st.button(f"{btn_label} ↗", use_container_width=True, key=f"qp_{btn_label}"):
                    st.session_state.messages.append({"role":"user","content":prompt_text})
                    st.rerun()

        MAX_HIST = 20
        for msg in st.session_state.messages[-MAX_HIST:]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        _, clear_col = st.columns([5,1])
        with clear_col:
            if st.button("Clear", key="clear_chat"):
                st.session_state.messages = []; st.rerun()

        if prompt := st.chat_input("Ask your Sattva anything..."):
            st.session_state.messages.append({"role":"user","content":prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner(""):
                    r = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                        system=full_system, messages=st.session_state.messages[-MAX_HIST:])
                    reply = r.content[0].text
                    st.markdown(reply)
            st.session_state.messages.append({"role":"assistant","content":reply})

    # ════════════════════════════════════
    # PROFILE SCREEN
    # ════════════════════════════════════
    elif screen == "profile":
        st.markdown("<p style='font-size:22px;font-weight:500;font-family:\"Newsreader\",serif;color:#1C2330;margin:4px 0 2px;'>Profile</p>", unsafe_allow_html=True)

        # Section selector
        sections = [("overview","Overview"),("edit","Edit details"),("labs","Labs"),("wearable","Wearable"),("roadmap","Roadmap")]
        sec_cols = st.columns(len(sections))
        for i, (sid, slabel) in enumerate(sections):
            with sec_cols[i]:
                active = st.session_state.profile_section == sid
                if st.button(slabel, key=f"ps_{sid}", use_container_width=True,
                             type="primary" if active else "secondary"):
                    st.session_state.profile_section = sid
                    st.rerun()

        st.divider()
        psec = st.session_state.profile_section

        # ── OVERVIEW ──────────────────────────────────────────────────────────────
        if psec == "overview":
            if profile:
                st.markdown(f"""
<div class='os-card' style='display:flex;align-items:center;gap:12px;'>
  <div style='width:48px;height:48px;border-radius:50%;background:#1C2330;display:flex;align-items:center;justify-content:center;flex-shrink:0;'>
    <span style='color:#F2F3EF;font-size:16px;font-weight:500;'>{"".join([w[0] for w in (profile.get("full_name","?? ")).split()[:2]])}</span>
  </div>
  <div>
    <p style='font-size:15px;font-weight:500;margin:0;color:#1C2330;'>{profile.get("full_name","")}</p>
    <p style='font-size:12px;color:#5B6270;margin:2px 0 0;'>{profile.get("age","?")} · {profile.get("sex","")} · {profile.get("blood_group","")} · {profile.get("location","")}</p>
    <p style='font-size:12px;color:#5B6270;margin:2px 0 0;'>{profile.get("diet","")}</p>
  </div>
</div>""", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
<div class='os-metric'>
  <p class='os-label' style='margin:0 0 4px;'>Height</p>
  <p class='os-big' style='color:#1C2330;margin:0;font-size:22px;'>{profile.get("height_cm","?") if profile else "?"}<span style='font-size:12px;opacity:0.5;'>cm</span></p>
</div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
<div class='os-metric'>
  <p class='os-label' style='margin:0 0 4px;'>Weight</p>
  <p class='os-big' style='color:#1C2330;margin:0;font-size:22px;'>{profile.get("weight_kg","?") if profile else "?"}<span style='font-size:12px;opacity:0.5;'>kg</span></p>
</div>""", unsafe_allow_html=True)

            # Conditions, meds, supps
            conditions = db_get("medical_history", user_id)
            meds = db_get("medications", user_id)
            supps = db_get("supplements", user_id)
            if conditions:
                st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:14px 0 8px;'>Conditions</p>", unsafe_allow_html=True)
                for c in conditions:
                    st.markdown(f"<p style='font-size:13px;color:#1C2330;margin:0 0 4px;'>· {c['condition']} — <span style='color:#5B6270;'>{c.get('notes','')[:60]}</span></p>", unsafe_allow_html=True)
            if meds:
                st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:14px 0 8px;'>Medications</p>", unsafe_allow_html=True)
                for m in [x for x in meds if x.get("active",True)]:
                    st.markdown(f"<p style='font-size:13px;color:#1C2330;margin:0 0 4px;'>· {m['name']} {m.get('dose','')} — <span style='color:#5B6270;'>{m.get('frequency','')}</span></p>", unsafe_allow_html=True)
            if supps:
                st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:14px 0 8px;'>Supplements</p>", unsafe_allow_html=True)
                for s in [x for x in supps if x.get("active",True)]:
                    st.markdown(f"<p style='font-size:13px;color:#1C2330;margin:0 0 4px;'>· {s['name']} {s.get('dose','')} — <span style='color:#5B6270;'>{s.get('timing','')}</span></p>", unsafe_allow_html=True)

            # Profile notes
            notes_rec = db_get_single("profile_notes", user_id)
            if notes_rec and notes_rec.get("notes"):
                st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:14px 0 8px;'>Notes</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size:12px;color:#5B6270;line-height:1.6;'>{notes_rec['notes'][:400]}</p>", unsafe_allow_html=True)

            # Cycle
            st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:14px 0 8px;'>Cycle</p>", unsafe_allow_html=True)
            cd = db_get_single("cycle_data", user_id)
            with st.form("cycle_quick"):
                cyc1, cyc2 = st.columns(2)
                with cyc1:
                    lp = st.date_input("Last period", value=date.fromisoformat(cd["last_period_start"]) if cd and cd.get("last_period_start") else date.today())
                with cyc2:
                    al = st.number_input("Avg length", 21, 40, value=cd.get("avg_cycle_length",27) if cd else 27)
                if st.form_submit_button("Update cycle"):
                    db_upsert("cycle_data", {"user_id":user_id,"last_period_start":lp.isoformat(),"avg_cycle_length":int(al)})
                    st.success("Updated!"); st.rerun()

            # Quick notes update
            st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:14px 0 8px;'>Update your coach</p>", unsafe_allow_html=True)
            curr_notes = notes_rec.get("notes","") if notes_rec else ""
            new_n = st.text_area("Notes", value=curr_notes, height=80, placeholder="Medication change, new symptom, anything your coach should know...")
            if st.button("Save notes", type="primary"):
                db_upsert("profile_notes", {"user_id":user_id,"notes":new_n})
                st.session_state.system_prompt = build_system_prompt(user_id, profile)
                st.success("Saved.")

        # ── EDIT ──────────────────────────────────────────────────────────────────
        elif psec == "edit":
            with st.form("profile_edit_form"):
                pc1, pc2 = st.columns(2)
                with pc1:
                    p_name = st.text_input("Full name", value=profile.get("full_name","") if profile else "")
                    p_dob_v = profile.get("date_of_birth") if profile else None
                    p_dob = st.date_input("Date of birth", value=date.fromisoformat(p_dob_v) if p_dob_v else date(1990,1,1), min_value=date(1940,1,1), max_value=date.today())
                    p_sex = st.selectbox("Sex", ["","Female","Male","Intersex"], index=["","Female","Male","Intersex"].index(profile.get("sex","")) if profile and profile.get("sex","") in ["Female","Male","Intersex"] else 0)
                    p_h = st.number_input("Height (cm)", 100, 220, value=int(profile.get("height_cm",165)) if profile and profile.get("height_cm") else 165)
                with pc2:
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
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown("**Goals**")
                goals = db_get("goals", user_id)
                for g in goals:
                    gc1,gc2 = st.columns([5,1])
                    gc1.write(f"{g['goal'][:40]} _{g.get('timeframe','')}_")
                    if gc2.button("✕",key=f"dg_{g['id']}"): db_delete("goals",g["id"]); st.rerun()
                with st.form("ag"):
                    ng1,ng2 = st.columns([3,1])
                    with ng1: ng = st.text_input("Goal")
                    with ng2: ntf = st.selectbox("",["3mo","6mo","12mo","12mo+"])
                    if st.form_submit_button("+ Add") and ng:
                        db_upsert("goals",{"user_id":user_id,"goal":ng,"timeframe":ntf}); st.rerun()

                st.markdown("**Conditions**")
                conds = db_get("medical_history", user_id)
                for c in conds:
                    cc1,cc2 = st.columns([5,1])
                    cc1.write(f"**{c['condition']}** {c.get('notes','')[:30]}")
                    if cc2.button("✕",key=f"dc_{c['id']}"): db_delete("medical_history",c["id"]); st.rerun()
                with st.form("ac"):
                    nc1,nc2 = st.columns([3,2])
                    with nc1: nc = st.text_input("Condition")
                    with nc2: nn = st.text_input("Notes")
                    if st.form_submit_button("+ Add") and nc:
                        db_upsert("medical_history",{"user_id":user_id,"condition":nc,"notes":nn}); st.rerun()

            with col_r:
                st.markdown("**Medications**")
                meds = db_get("medications", user_id)
                for m in meds:
                    mc1,mc2 = st.columns([5,1])
                    mc1.write(f"**{m['name']}** {m.get('dose','')} {m.get('frequency','')}")
                    if mc2.button("✕",key=f"dm_{m['id']}"): db_delete("medications",m["id"]); st.rerun()
                with st.form("am"):
                    mm1,mm2,mm3 = st.columns(3)
                    with mm1: nm = st.text_input("Med")
                    with mm2: nd = st.text_input("Dose")
                    with mm3: nf = st.text_input("Freq")
                    if st.form_submit_button("+ Add") and nm:
                        db_upsert("medications",{"user_id":user_id,"name":nm,"dose":nd,"frequency":nf,"active":True}); st.rerun()

                st.markdown("**Supplements**")
                supps = db_get("supplements", user_id)
                for s in supps:
                    sc1,sc2 = st.columns([5,1])
                    sc1.write(f"**{s['name']}** {s.get('dose','')} ({s.get('timing','')})")
                    if sc2.button("✕",key=f"ds_{s['id']}"): db_delete("supplements",s["id"]); st.rerun()
                with st.form("as"):
                    ss1,ss2,ss3 = st.columns(3)
                    with ss1: ns = st.text_input("Supp")
                    with ss2: nsd = st.text_input("Dose")
                    with ss3: nst = st.text_input("Timing")
                    if st.form_submit_button("+ Add") and ns:
                        db_upsert("supplements",{"user_id":user_id,"name":ns,"dose":nsd,"timing":nst,"active":True}); st.rerun()

        # ── LABS ──────────────────────────────────────────────────────────────────
        elif psec == "labs":
            all_labs = db_get("lab_reports", user_id, order_col="report_date")
            if all_labs:
                try:
                    latest = all_labs[-1]
                    age = (date.today()-date.fromisoformat(latest["report_date"])).days
                    color = "#1D9E75" if age<=90 else ("#B68A3D" if age<=180 else "#C8384A")
                    st.markdown(f"<p style='font-size:12px;color:{color};margin:0 0 12px;'>{'✅ Current' if age<=90 else '⚠️ Stale'} · Last: {latest['report_date']} ({age} days ago)</p>", unsafe_allow_html=True)
                except: pass

            with st.expander("Upload new report", expanded=not bool(all_labs)):
                ld = st.date_input("Report date", value=date.today(), key="lab_d")
                ln = st.text_input("Lab name", placeholder="Thyrocare, SRL...", key="lab_n")
                lv = st.text_area("Paste values", height=160, key="lab_v", placeholder="TSH: 1.83\nFT3: 2.2\nProlactin: 43.6\n...")
                if st.button("Analyse & save", type="primary", use_container_width=True, key="lab_save"):
                    if lv.strip():
                        prev_ctx = ""
                        if all_labs:
                            prev = all_labs[-1]
                            prev_ctx = f"\n\nPREVIOUS ({prev['report_date']}):\n{prev.get('raw_values','')[:600]}"
                        with st.spinner("Analysing..."):
                            r = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                                system=st.session_state.system_prompt,
                                messages=[{"role":"user","content":f"Lab report {ld}, {ln}:\n{lv}{prev_ctx}\n\nAnalyse vs functional ranges. Format:\n## Key Findings\nTable: Marker | Value | Functional Range | Status (✅⚠️🚨) | vs Previous (↑↓→—)\n\n## Clinical picture\n2-3 sentences\n\n## Priority actions\n3-5 numbered, specific\n\n## Retest\nWhat and when\n\n**Start today:** [one action]\n\nComplete everything."}])
                            st.markdown(r.content[0].text)
                            sr = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=120,
                                messages=[{"role":"user","content":f"One line summary max 120 chars: {lv}"}])
                            db_upsert("lab_reports",{"user_id":user_id,"report_date":ld.isoformat(),"lab_name":ln,"raw_values":lv,"summary":sr.content[0].text[:500]})
                            st.success("Saved.")
                            st.session_state.system_prompt = build_system_prompt(user_id, profile)
                            st.rerun()
                    else: st.warning("Paste lab values.")

            if all_labs:
                st.markdown(f"<p style='font-size:13px;font-weight:500;color:#1C2330;margin:14px 0 8px;'>{len(all_labs)} report(s)</p>", unsafe_allow_html=True)
                for lab in reversed(all_labs):
                    try:
                        age = (date.today()-date.fromisoformat(lab["report_date"])).days
                        tag = "🟢" if age<=90 else ("🟡" if age<=180 else "⚪")
                    except: tag = ""
                    with st.expander(f"{tag} {lab['report_date']} · {lab.get('lab_name','')}"):
                        st.caption(lab.get("summary",""))
                        st.text_area("Values", value=lab.get("raw_values",""), key=f"lrv_{lab['id']}", height=100)
                        if st.button("Delete", key=f"dl_{lab['id']}"):
                            db_delete("lab_reports",lab["id"]); st.rerun()

        # ── WEARABLE ──────────────────────────────────────────────────────────────
        elif psec == "wearable":
            COL_MAP = {
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
            def find_col_w(cols, cands):
                cl = {c.lower():c for c in cols}
                for c in cands:
                    if c in cols: return c
                    if c.lower() in cl: return cl[c.lower()]
                return None

            imp = st.radio("Import", ["Upload WHOOP CSVs","Manual entry"], horizontal=True)
            if imp == "Upload WHOOP CSVs":
                wc1,wc2 = st.columns(2)
                with wc1:
                    cf = st.file_uploader("cycles.csv",type=["csv"],key="wu_cycles")
                    sf = st.file_uploader("sleep.csv",type=["csv"],key="wu_sleep")
                with wc2:
                    wf = st.file_uploader("workout.csv",type=["csv"],key="wu_workout")
                if st.button("Process & save", type="primary", use_container_width=True):
                    merged = {}
                    for f, fields in [(cf,["recovery_score","hrv","resting_hr","strain"]),(sf,["sleep_performance","sleep_efficiency","sleep_duration"])]:
                        if f:
                            try:
                                df = pd.read_csv(f)
                                dc = find_col_w(df.columns.tolist(), COL_MAP["date"])
                                if not dc: st.warning(f"{f.name}: no date column"); continue
                                dates = pd.to_datetime(df[dc],errors="coerce").dt.strftime("%Y-%m-%d")
                                for field in fields:
                                    col = find_col_w(df.columns.tolist(), COL_MAP[field])
                                    if col:
                                        for d,v in zip(dates,df[col]):
                                            if pd.notna(d) and pd.notna(v):
                                                try: merged.setdefault(d,{})[field]=float(v)
                                                except: merged.setdefault(d,{})[field]=v
                                st.success(f"✅ {f.name}: {len(df)} rows")
                            except Exception as e: st.error(f"{f.name}: {e}")
                    if wf:
                        try:
                            wdf2 = pd.read_csv(wf)
                            dc = find_col_w(wdf2.columns.tolist(), COL_MAP["date"])
                            if dc:
                                dates = pd.to_datetime(wdf2[dc],errors="coerce").dt.strftime("%Y-%m-%d")
                                nc = find_col_w(wdf2.columns.tolist(), COL_MAP["workout_name"])
                                sc_col = find_col_w(wdf2.columns.tolist(), COL_MAP["workout_strain"])
                                for i,d in enumerate(dates):
                                    if pd.notna(d):
                                        if nc: merged.setdefault(d,{})["workout_name"]=str(wdf2[nc].iloc[i])
                                        if sc_col:
                                            try: merged.setdefault(d,{})["workout_strain"]=float(wdf2[sc_col].iloc[i])
                                            except: pass
                                st.success(f"✅ workout.csv: {len(wdf2)} rows")
                        except Exception as e: st.error(f"workout.csv: {e}")
                    if merged:
                        for d,vals in merged.items():
                            db_upsert("wearable_data",{"user_id":user_id,"data_date":d,**vals})
                        st.success(f"Saved {len(merged)} days.")
                        st.session_state.system_prompt = build_system_prompt(user_id, profile)
                        st.rerun()
            else:
                with st.form("mw"):
                    mc1,mc2 = st.columns(2)
                    with mc1:
                        wd = st.date_input("Date",value=date.today())
                        wr2 = st.number_input("Recovery (%)",0,100,50)
                        wh = st.number_input("HRV (ms)",0,200,40)
                    with mc2:
                        ws = st.number_input("Sleep perf (%)",0,100,70)
                        wst = st.number_input("Strain",0.0,21.0,10.0,step=0.1)
                        wrhr = st.number_input("RHR (bpm)",30,120,65)
                    if st.form_submit_button("Save",type="primary"):
                        db_upsert("wearable_data",{"user_id":user_id,"data_date":wd.isoformat(),"recovery_score":wr2,"hrv":wh,"sleep_performance":ws,"strain":wst,"resting_hr":wrhr})
                        st.success("Saved!"); st.rerun()

            # Trends
            wall = db_get("wearable_data", user_id, order_col="data_date")
            if wall:
                wdf3 = pd.DataFrame(wall)
                wdf3["data_date"] = pd.to_datetime(wdf3["data_date"])
                wdf3 = wdf3.sort_values("data_date")
                r7 = wdf3.tail(7); r30 = wdf3.tail(30)
                metrics_w = [("recovery_score","Recovery %"),("hrv","HRV ms"),("resting_hr","RHR"),("sleep_performance","Sleep %"),("strain","Strain")]
                avail = [(f,l) for f,l in metrics_w if f in wdf3.columns]
                if avail:
                    st.markdown("<p style='font-size:13px;font-weight:500;color:#1C2330;margin:14px 0 8px;'>This week vs 30-day avg</p>", unsafe_allow_html=True)
                    mc = st.columns(min(len(avail),2))
                    for i,(field,label) in enumerate(avail[:4]):
                        wv = pd.to_numeric(r7[field],errors="coerce").mean()
                        mv = pd.to_numeric(r30[field],errors="coerce").mean()
                        if not pd.isna(wv):
                            d = round(wv-mv,1) if not pd.isna(mv) else None
                            mc[i%2].metric(label,f"{wv:.1f}",delta=f"{d:+.1f}" if d else None)

                ct1,ct2 = st.tabs(["Recovery & HRV","Sleep & Strain"])
                with ct1:
                    rf = [f for f in ["recovery_score","hrv"] if f in wdf3.columns]
                    if rf: st.line_chart(wdf3[["data_date"]+rf].set_index("data_date"))
                with ct2:
                    sf2 = [f for f in ["sleep_performance","strain"] if f in wdf3.columns]
                    if sf2: st.line_chart(wdf3[["data_date"]+sf2].set_index("data_date"))

                dl1,dl2 = st.columns(2)
                with dl1:
                    dl = wdf3["data_date"].dt.strftime("%Y-%m-%d").tolist()
                    dd = st.selectbox("Delete date",["—"]+list(reversed(dl)),key="del_w_d")
                    if dd != "—" and st.button("Delete",key="del_w_b"):
                        [db_delete("wearable_data",w["id"]) for w in wall if w["data_date"]==dd]
                        st.rerun()
                with dl2:
                    if st.button("Clear all wearable data"):
                        [db_delete("wearable_data",w["id"]) for w in wall]
                        st.rerun()

        # ── ROADMAP ───────────────────────────────────────────────────────────────
        elif psec == "roadmap":
            if "treatment_roadmap" not in st.session_state:
                st.session_state.treatment_roadmap = None
            if "roadmap_committed" not in st.session_state:
                st.session_state.roadmap_committed = False

            if not st.session_state.treatment_roadmap:
                saved = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
                if saved:
                    st.session_state.treatment_roadmap = saved[0]["roadmap_text"]
                    st.session_state.roadmap_committed = saved[0].get("committed", False)
                    try:
                        st.session_state.roadmap_date = datetime.fromisoformat(saved[0]["generated_at"].replace("Z","")).strftime("%d %b %Y")
                    except: st.session_state.roadmap_date = "Previously"

            if st.session_state.treatment_roadmap and st.session_state.roadmap_committed:
                st.success(f"Committed roadmap · {st.session_state.get('roadmap_date','')}")
                st.markdown(st.session_state.treatment_roadmap)
                st.divider()
                st.download_button("Download roadmap", data=st.session_state.treatment_roadmap, file_name=f"onesattva_roadmap_{date.today()}.txt", use_container_width=True)
                with st.expander("Update roadmap — significant change only"):
                    st.warning("Describe what changed before regenerating.")
                    reason = st.text_area("What has changed?")
                    if st.button("Regenerate roadmap", type="primary") and reason.strip():
                        st.session_state.roadmap_committed = False
                        st.session_state.treatment_roadmap = None
                        st.session_state.roadmap_change_reason = reason
                        st.rerun()

            elif st.session_state.treatment_roadmap:
                st.info("Review your roadmap below, then commit to it.")
                st.markdown(st.session_state.treatment_roadmap)
                st.divider()
                col1,col2 = st.columns(2)
                with col1:
                    if st.button("Commit to this roadmap", type="primary", use_container_width=True):
                        db_upsert("roadmaps",{"user_id":user_id,"roadmap_text":st.session_state.treatment_roadmap,"committed":True,"priority_focus":"","intensity":""})
                        st.session_state.roadmap_committed = True; st.rerun()
                with col2:
                    if st.button("Regenerate", use_container_width=True):
                        st.session_state.treatment_roadmap = None; st.rerun()

            else:
                rm1,rm2 = st.columns(2)
                with rm1: rp = st.selectbox("Priority",["Balanced","Fastest path to conception","Fastest path to fat loss","Gut first"])
                with rm2: ri = st.selectbox("Intensity",["Moderate","Aggressive"])
                if st.button("Generate my treatment roadmap", type="primary", use_container_width=True):
                    change_ctx = f"\n\nSIGNIFICANT CHANGE: {st.session_state.get('roadmap_change_reason','')}" if st.session_state.get("roadmap_change_reason") else ""
                    with st.spinner("Building your 12-month roadmap..."):
                        r = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                            system=st.session_state.system_prompt,
                            messages=[{"role":"user","content":f"""Generate a 12-month treatment roadmap.
Priority: {rp} · Intensity: {ri}{change_ctx}

FORMAT — complete every section:

## Where Things Stand
3-4 sentences: core blockers, why current approach is insufficient.

## Phase 1 — Months 0-3: [title]
Table: Change | Current → New | Clinical Reason (5-7 rows)
**Retest at 3 months:** [4-5 markers]
**Success looks like:** [2-3 measurable outcomes]

## Phase 2 — Months 3-6: [title]
Same table, 4-5 rows
**Retest:** [markers] · **Success:** [outcomes]

## Phase 3 — Months 6-12: [title]
Same table, 3-4 rows
**Retest:** [markers] · **Success:** [outcomes]

## If Phase 1 shows no progress
2-3 sentences: escalation path

## After goals are achieved
Maintenance guidance

**Start today:** [immediate action]"""}])
                        st.session_state.treatment_roadmap = r.content[0].text
                        st.session_state.roadmap_date = date.today().strftime("%d %b %Y")
                        db_upsert("roadmaps",{"user_id":user_id,"roadmap_text":st.session_state.treatment_roadmap,"committed":False,"priority_focus":rp,"intensity":ri})
                        st.rerun()

        st.divider()
        if st.button("Sign out", key="signout"):
            sign_out()



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
                    p_blood = st.selectbox("Blood group", ["","A+","A-","B+","B-","O+","O-","AB+","AB-"],
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
                with nc2: new_notes = st.text_input("Notes", placeholder="e.g. diagnosed 2020")
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
                with mm1: new_med = st.text_input("Medication", placeholder="e.g. Thyronorm")
                with mm2: new_dose = st.text_input("Dose", placeholder="e.g. 50mcg")
                with mm3: new_freq = st.text_input("Frequency", placeholder="e.g. Daily on waking")
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
                with ss1: new_supp = st.text_input("Supplement", placeholder="e.g. Magnesium Glycinate")
                with ss2: new_sdose = st.text_input("Dose", placeholder="e.g. 400mg")
                with ss3: new_stiming = st.text_input("Timing", placeholder="e.g. Before bed")
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
                    lp_date = st.date_input("Last period start", value=date.fromisoformat(ob_cd["last_period_start"]) if ob_cd and ob_cd.get("last_period_start") else date.today())
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
