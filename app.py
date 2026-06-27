import streamlit as st
import anthropic
import os
import json as _json
from datetime import date, datetime, timedelta
import pandas as pd
from supabase import create_client, Client

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OneSattva — Health, understood.",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='%23B6744A'/></svg>",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bone:       #F7F5F2;   /* primary background */
  --graphite:   #111214;   /* text, structure, dark surfaces */
  --copper:     #B6744A;   /* signature accent — use sparingly */
  --stone:      #E6E3DF;   /* support surfaces */
  --forest:     #1F2F2A;   /* deep dark — 2% use only */
  --paper:      #FAFAF7;   /* white card surfaces */
  --mid:        #6B6358;   /* secondary text */
  --line:       rgba(17,18,20,0.10);  /* dividers and borders */

  /* Legacy aliases for any remaining references */
  --mist:   #F7F5F2;
  --ink:    #111214;
  --gold:   #B6744A;
  --signal: #1F2F2A;
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

.stApp { background-color: var(--bone); }

[data-testid="stSidebar"] { background-color: var(--graphite); }
[data-testid="stSidebar"] * { color: var(--bone) !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  color: var(--bone) !important;
  font-family: 'Newsreader', serif !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(247,245,242,0.10) !important; }

[data-testid="stSidebar"] .stButton > button {
  background-color: rgba(247,245,242,0.08) !important;
  border: 1px solid rgba(247,245,242,0.15) !important;
  color: #F7F5F2 !important;
  font-family: Inter, sans-serif !important;
  font-size: 12px !important;
  font-weight: 400 !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background-color: rgba(247,245,242,0.15) !important;
  border-color: rgba(247,245,242,0.25) !important;
  color: #F7F5F2 !important;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 4px;
  background-color: var(--stone);
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
  color: var(--graphite) !important;
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
  background-color: var(--graphite);
  color: var(--bone);
  border-color: var(--ink);
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
  background: rgba(182,116,74,0.12);
  color: #B6744A;
  border: 1px solid rgba(182,116,74,0.35);
  border-radius: 20px;
  padding: 5px 14px;
  font-size: 12.5px;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  display: inline-block;
}
.triage-watch {
  background: rgba(230,227,223,0.45);
  color: #6B6358;
  border: 1px solid rgba(230,227,223,0.80);
  border-radius: 20px;
  padding: 5px 14px;
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
        <svg width="64" height="64" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><defs><radialGradient id="osg-dark" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#B1643A"/><stop offset="40%" stop-color="#B1643A"/><stop offset="54%" stop-color="#BE7C58" stop-opacity="0.72"/><stop offset="70%" stop-color="#D2A084" stop-opacity="0.4"/><stop offset="86%" stop-color="#E6CCB8" stop-opacity="0.14"/><stop offset="100%" stop-color="#E6CCB8" stop-opacity="0"/></radialGradient></defs><path d="M194.49 100.00 L194.46 102.97 L194.34 105.94 L194.12 108.90 L193.81 111.85 L193.40 114.79 L192.90 117.72 L192.31 120.63 L191.62 123.52 L190.84 126.39 L189.97 129.23 L189.01 132.05 L187.96 134.82 L186.81 137.57 L185.57 140.27 L184.25 142.93 L182.84 145.54 L181.34 148.10 L179.76 150.61 L178.09 153.07 L176.35 155.47 L174.53 157.81 L172.64 160.09 L170.67 162.31 L168.64 164.46 L166.55 166.55 L164.39 168.57 L162.18 170.53 L159.91 172.42 L157.58 174.24 L155.21 175.99 L152.78 177.67 L150.31 179.28 L147.79 180.81 L145.23 182.27 L142.62 183.64 L139.97 184.94 L137.28 186.16 L134.56 187.28 L131.80 188.33 L129.01 189.27 L126.19 190.13 L123.34 190.89 L120.47 191.56 L117.57 192.13 L114.67 192.60 L111.74 192.97 L108.81 193.24 L105.88 193.42 L102.94 193.51 L100.00 193.50 L97.06 193.40 L94.14 193.22 L91.21 192.95 L88.30 192.60 L85.40 192.16 L82.52 191.65 L79.64 191.07 L76.79 190.41 L73.95 189.67 L71.13 188.86 L68.33 187.98 L65.55 187.02 L62.79 185.99 L60.06 184.87 L57.36 183.68 L54.70 182.41 L52.07 181.05 L49.48 179.61 L46.94 178.08 L44.45 176.46 L42.01 174.76 L39.64 172.97 L37.33 171.09 L35.09 169.12 L32.92 167.08 L30.84 164.95 L28.84 162.74 L26.92 160.46 L25.09 158.11 L23.34 155.69 L21.69 153.22 L20.12 150.69 L18.65 148.11 L17.26 145.49 L15.96 142.82 L14.75 140.12 L13.62 137.38 L12.58 134.61 L11.62 131.82 L10.74 129.00 L9.95 126.16 L9.23 123.31 L8.60 120.43 L8.04 117.54 L7.57 114.64 L7.19 111.73 L6.88 108.80 L6.66 105.87 L6.53 102.94 L6.49 100.00 L6.53 97.06 L6.67 94.13 L6.89 91.20 L7.21 88.28 L7.61 85.37 L8.11 82.47 L8.70 79.59 L9.37 76.73 L10.14 73.89 L10.99 71.08 L11.93 68.29 L12.95 65.53 L14.05 62.81 L15.24 60.11 L16.50 57.46 L17.85 54.84 L19.27 52.26 L20.77 49.72 L22.35 47.23 L24.00 44.78 L25.73 42.39 L27.53 40.05 L29.41 37.76 L31.36 35.54 L33.38 33.38 L35.47 31.29 L37.64 29.26 L39.87 27.31 L42.16 25.44 L44.52 23.64 L46.94 21.92 L49.41 20.29 L51.94 18.74 L54.52 17.27 L57.15 15.90 L59.82 14.60 L62.52 13.40 L65.27 12.28 L68.04 11.24 L70.85 10.29 L73.69 9.43 L76.54 8.64 L79.42 7.95 L82.32 7.34 L85.24 6.81 L88.17 6.37 L91.12 6.02 L94.07 5.75 L97.03 5.58 L100.00 5.50 L102.97 5.52 L105.94 5.63 L108.90 5.84 L111.85 6.16 L114.80 6.58 L117.72 7.10 L120.62 7.73 L123.50 8.47 L126.35 9.31 L129.16 10.25 L131.94 11.29 L134.67 12.43 L137.36 13.67 L140.00 15.00 L142.59 16.41 L145.13 17.91 L147.62 19.48 L150.05 21.13 L152.43 22.84 L154.76 24.62 L157.04 26.46 L159.26 28.36 L161.44 30.31 L163.56 32.32 L165.63 34.37 L167.65 36.48 L169.61 38.63 L171.52 40.83 L173.38 43.08 L175.18 45.38 L176.93 47.72 L178.61 50.12 L180.22 52.56 L181.76 55.05 L183.23 57.59 L184.63 60.18 L185.94 62.81 L187.17 65.49 L188.31 68.21 L189.36 70.97 L190.31 73.76 L191.17 76.59 L191.93 79.45 L192.59 82.34 L193.16 85.25 L193.62 88.17 L193.99 91.12 L194.25 94.07 L194.42 97.03 L194.49 100.00 Z" fill="none" stroke="#111214" stroke-width="1.3"/><path d="M183.80 100.00 L183.77 102.63 L183.66 105.26 L183.45 107.89 L183.17 110.51 L182.80 113.11 L182.34 115.71 L181.80 118.29 L181.18 120.84 L180.48 123.38 L179.69 125.89 L178.82 128.38 L177.87 130.83 L176.84 133.25 L175.73 135.64 L174.54 137.98 L173.28 140.29 L171.94 142.54 L170.52 144.76 L169.04 146.92 L167.48 149.03 L165.86 151.09 L164.18 153.09 L162.43 155.04 L160.63 156.93 L158.77 158.77 L156.86 160.55 L154.90 162.27 L152.89 163.93 L150.83 165.53 L148.73 167.07 L146.59 168.55 L144.40 169.97 L142.18 171.32 L139.91 172.61 L137.62 173.82 L135.28 174.97 L132.91 176.05 L130.51 177.06 L128.08 177.98 L125.61 178.83 L123.13 179.60 L120.61 180.29 L118.08 180.89 L115.53 181.41 L112.96 181.84 L110.38 182.19 L107.79 182.46 L105.20 182.64 L102.60 182.73 L100.00 182.75 L97.40 182.68 L94.81 182.54 L92.22 182.33 L89.64 182.04 L87.06 181.68 L84.50 181.25 L81.95 180.75 L79.41 180.18 L76.89 179.55 L74.38 178.85 L71.89 178.08 L69.42 177.25 L66.96 176.34 L64.54 175.37 L62.13 174.32 L59.76 173.20 L57.42 172.00 L55.12 170.72 L52.86 169.37 L50.64 167.93 L48.48 166.42 L46.37 164.83 L44.32 163.16 L42.33 161.41 L40.42 159.58 L38.57 157.69 L36.80 155.72 L35.10 153.69 L33.49 151.59 L31.95 149.44 L30.49 147.24 L29.12 144.98 L27.82 142.69 L26.61 140.35 L25.47 137.97 L24.41 135.57 L23.43 133.13 L22.53 130.67 L21.70 128.19 L20.94 125.69 L20.25 123.17 L19.64 120.63 L19.09 118.08 L18.62 115.52 L18.23 112.95 L17.90 110.37 L17.65 107.78 L17.47 105.19 L17.37 102.60 L17.34 100.00 L17.40 97.40 L17.53 94.81 L17.73 92.22 L18.02 89.64 L18.39 87.07 L18.83 84.52 L19.35 81.97 L19.95 79.45 L20.63 76.94 L21.38 74.45 L22.21 71.99 L23.10 69.55 L24.08 67.14 L25.12 64.76 L26.23 62.41 L27.41 60.09 L28.66 57.81 L29.98 55.56 L31.36 53.35 L32.81 51.19 L34.33 49.06 L35.92 46.99 L37.57 44.96 L39.29 42.99 L41.07 41.07 L42.91 39.20 L44.82 37.41 L46.78 35.67 L48.81 34.00 L50.89 32.40 L53.02 30.87 L55.21 29.42 L57.44 28.04 L59.72 26.74 L62.04 25.51 L64.41 24.36 L66.80 23.28 L69.23 22.29 L71.69 21.37 L74.18 20.52 L76.69 19.75 L79.22 19.06 L81.77 18.44 L84.34 17.90 L86.92 17.44 L89.52 17.05 L92.13 16.74 L94.75 16.51 L97.37 16.36 L100.00 16.29 L102.63 16.31 L105.26 16.41 L107.88 16.61 L110.50 16.89 L113.10 17.27 L115.69 17.74 L118.26 18.30 L120.81 18.95 L123.33 19.70 L125.82 20.54 L128.27 21.46 L130.69 22.48 L133.07 23.57 L135.41 24.75 L137.70 26.00 L139.95 27.33 L142.15 28.72 L144.31 30.18 L146.42 31.69 L148.48 33.27 L150.50 34.89 L152.47 36.57 L154.40 38.29 L156.28 40.06 L158.12 41.88 L159.91 43.74 L161.66 45.64 L163.36 47.58 L165.01 49.57 L166.62 51.60 L168.17 53.67 L169.66 55.79 L171.10 57.95 L172.48 60.16 L173.79 62.40 L175.03 64.69 L176.20 67.03 L177.30 69.40 L178.31 71.81 L179.25 74.25 L180.10 76.73 L180.87 79.24 L181.54 81.77 L182.13 84.33 L182.64 86.91 L183.05 89.51 L183.37 92.12 L183.60 94.74 L183.75 97.37 L183.80 100.00 Z" fill="none" stroke="#111214" stroke-width="1.3"/><path d="M170.96 100.00 L170.92 102.23 L170.80 104.45 L170.61 106.67 L170.35 108.89 L170.03 111.09 L169.63 113.28 L169.16 115.46 L168.63 117.62 L168.02 119.76 L167.35 121.88 L166.61 123.98 L165.81 126.06 L164.94 128.10 L164.00 130.12 L163.00 132.10 L161.94 134.05 L160.81 135.96 L159.62 137.84 L158.38 139.67 L157.08 141.47 L155.72 143.22 L154.31 144.93 L152.84 146.59 L151.33 148.21 L149.77 149.77 L148.17 151.30 L146.52 152.77 L144.84 154.20 L143.11 155.57 L141.34 156.90 L139.53 158.17 L137.69 159.39 L135.81 160.55 L133.90 161.66 L131.95 162.71 L129.97 163.70 L127.96 164.62 L125.93 165.48 L123.86 166.28 L121.77 167.00 L119.65 167.65 L117.52 168.23 L115.36 168.73 L113.19 169.16 L111.01 169.52 L108.82 169.79 L106.62 170.00 L104.41 170.13 L102.21 170.18 L100.00 170.17 L97.80 170.09 L95.60 169.94 L93.41 169.73 L91.23 169.45 L89.05 169.12 L86.89 168.73 L84.74 168.28 L82.60 167.78 L80.47 167.22 L78.36 166.61 L76.26 165.95 L74.17 165.23 L72.11 164.46 L70.06 163.63 L68.03 162.74 L66.03 161.79 L64.05 160.78 L62.11 159.71 L60.19 158.57 L58.32 157.37 L56.48 156.10 L54.69 154.77 L52.95 153.37 L51.26 151.91 L49.62 150.38 L48.04 148.79 L46.53 147.14 L45.07 145.44 L43.69 143.68 L42.37 141.87 L41.12 140.02 L39.93 138.12 L38.82 136.18 L37.77 134.21 L36.79 132.21 L35.87 130.18 L35.02 128.12 L34.24 126.04 L33.52 123.93 L32.87 121.81 L32.28 119.68 L31.75 117.52 L31.28 115.36 L30.88 113.19 L30.54 111.00 L30.26 108.81 L30.06 106.61 L29.91 104.41 L29.83 102.21 L29.82 100.00 L29.88 97.80 L30.00 95.60 L30.20 93.40 L30.46 91.21 L30.78 89.04 L31.18 86.87 L31.64 84.72 L32.17 82.58 L32.76 80.47 L33.42 78.37 L34.13 76.29 L34.91 74.23 L35.75 72.20 L36.65 70.19 L37.60 68.20 L38.61 66.25 L39.67 64.32 L40.79 62.43 L41.97 60.56 L43.20 58.73 L44.49 56.94 L45.83 55.18 L47.22 53.47 L48.67 51.80 L50.17 50.17 L51.72 48.59 L53.33 47.06 L54.99 45.59 L56.69 44.17 L58.45 42.81 L60.25 41.50 L62.09 40.26 L63.98 39.09 L65.90 37.97 L67.86 36.92 L69.86 35.94 L71.88 35.02 L73.93 34.17 L76.01 33.38 L78.12 32.66 L80.24 32.00 L82.39 31.40 L84.55 30.87 L86.73 30.41 L88.91 30.01 L91.12 29.68 L93.33 29.41 L95.55 29.22 L97.77 29.09 L100.00 29.03 L102.23 29.05 L104.46 29.14 L106.68 29.31 L108.90 29.56 L111.11 29.88 L113.30 30.28 L115.48 30.76 L117.63 31.32 L119.77 31.96 L121.87 32.68 L123.95 33.47 L126.00 34.33 L128.01 35.27 L129.99 36.27 L131.93 37.34 L133.83 38.46 L135.69 39.64 L137.52 40.88 L139.30 42.16 L141.05 43.50 L142.76 44.87 L144.43 46.29 L146.07 47.75 L147.66 49.24 L149.23 50.77 L150.75 52.34 L152.24 53.95 L153.68 55.59 L155.09 57.27 L156.46 58.98 L157.78 60.73 L159.06 62.52 L160.28 64.35 L161.46 66.21 L162.57 68.12 L163.63 70.06 L164.63 72.03 L165.56 74.04 L166.42 76.09 L167.21 78.16 L167.93 80.26 L168.57 82.39 L169.14 84.55 L169.63 86.72 L170.04 88.91 L170.38 91.11 L170.64 93.32 L170.82 95.54 L170.93 97.77 L170.96 100.00 Z" fill="none" stroke="#111214" stroke-width="1.3"/><path d="M161.03 100.00 L160.99 101.92 L160.89 103.83 L160.74 105.74 L160.52 107.65 L160.25 109.54 L159.93 111.43 L159.54 113.31 L159.10 115.17 L158.60 117.03 L158.05 118.86 L157.44 120.68 L156.77 122.48 L156.04 124.25 L155.25 126.00 L154.41 127.72 L153.50 129.41 L152.55 131.08 L151.53 132.70 L150.46 134.29 L149.34 135.85 L148.17 137.36 L146.94 138.83 L145.67 140.26 L144.36 141.65 L143.00 143.00 L141.60 144.30 L140.16 145.55 L138.68 146.76 L137.17 147.92 L135.63 149.04 L134.05 150.11 L132.45 151.13 L130.81 152.10 L129.15 153.03 L127.46 153.90 L125.75 154.72 L124.01 155.49 L122.25 156.20 L120.47 156.86 L118.67 157.46 L116.85 158.00 L115.02 158.49 L113.17 158.91 L111.31 159.27 L109.44 159.57 L107.56 159.81 L105.67 159.99 L103.78 160.11 L101.89 160.18 L100.00 160.18 L98.11 160.14 L96.22 160.03 L94.34 159.88 L92.46 159.68 L90.59 159.42 L88.72 159.12 L86.86 158.78 L85.01 158.38 L83.17 157.94 L81.33 157.45 L79.51 156.92 L77.70 156.33 L75.90 155.69 L74.12 155.00 L72.36 154.26 L70.61 153.46 L68.89 152.60 L67.20 151.68 L65.55 150.70 L63.92 149.66 L62.34 148.56 L60.79 147.39 L59.30 146.17 L57.85 144.88 L56.46 143.54 L55.12 142.15 L53.83 140.70 L52.61 139.20 L51.44 137.66 L50.34 136.08 L49.29 134.46 L48.31 132.80 L47.38 131.12 L46.51 129.41 L45.69 127.67 L44.93 125.91 L44.22 124.14 L43.57 122.34 L42.96 120.54 L42.40 118.71 L41.89 116.88 L41.43 115.04 L41.02 113.18 L40.66 111.32 L40.35 109.45 L40.10 107.57 L39.89 105.68 L39.74 103.79 L39.65 101.90 L39.61 100.00 L39.63 98.10 L39.72 96.21 L39.86 94.32 L40.06 92.43 L40.33 90.55 L40.66 88.68 L41.05 86.82 L41.50 84.98 L42.01 83.15 L42.57 81.34 L43.20 79.55 L43.88 77.78 L44.61 76.03 L45.39 74.30 L46.22 72.60 L47.11 70.92 L48.04 69.27 L49.02 67.64 L50.04 66.05 L51.11 64.48 L52.23 62.94 L53.39 61.44 L54.60 59.97 L55.85 58.54 L57.14 57.14 L58.48 55.79 L59.86 54.47 L61.29 53.21 L62.75 51.98 L64.26 50.81 L65.81 49.69 L67.39 48.61 L69.01 47.59 L70.66 46.63 L72.34 45.72 L74.05 44.86 L75.79 44.06 L77.56 43.31 L79.34 42.62 L81.15 41.99 L82.98 41.41 L84.82 40.88 L86.68 40.42 L88.56 40.00 L90.44 39.65 L92.34 39.35 L94.24 39.11 L96.16 38.94 L98.08 38.82 L100.00 38.77 L101.92 38.78 L103.85 38.86 L105.77 39.00 L107.68 39.22 L109.58 39.50 L111.47 39.86 L113.35 40.28 L115.21 40.78 L117.04 41.35 L118.85 41.98 L120.64 42.68 L122.39 43.44 L124.12 44.26 L125.82 45.14 L127.48 46.07 L129.11 47.06 L130.70 48.09 L132.26 49.16 L133.79 50.28 L135.29 51.43 L136.75 52.62 L138.19 53.84 L139.59 55.09 L140.97 56.38 L142.31 57.69 L143.63 59.03 L144.91 60.41 L146.16 61.81 L147.38 63.25 L148.57 64.71 L149.72 66.21 L150.82 67.75 L151.89 69.31 L152.91 70.91 L153.88 72.55 L154.79 74.22 L155.65 75.92 L156.46 77.65 L157.20 79.41 L157.88 81.20 L158.49 83.01 L159.04 84.84 L159.52 86.70 L159.93 88.57 L160.27 90.45 L160.55 92.35 L160.77 94.26 L160.92 96.17 L161.00 98.08 L161.03 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><path d="M150.19 100.00 L150.18 101.58 L150.13 103.15 L150.03 104.73 L149.88 106.30 L149.68 107.87 L149.43 109.43 L149.13 110.98 L148.78 112.52 L148.38 114.06 L147.93 115.57 L147.42 117.07 L146.86 118.56 L146.25 120.02 L145.59 121.45 L144.88 122.87 L144.11 124.25 L143.29 125.60 L142.43 126.93 L141.52 128.22 L140.57 129.48 L139.58 130.70 L138.55 131.89 L137.48 133.04 L136.38 134.16 L135.25 135.25 L134.08 136.30 L132.90 137.31 L131.68 138.30 L130.44 139.25 L129.18 140.17 L127.90 141.05 L126.59 141.91 L125.27 142.72 L123.92 143.51 L122.55 144.25 L121.16 144.96 L119.74 145.62 L118.31 146.25 L116.86 146.83 L115.39 147.35 L113.90 147.83 L112.39 148.26 L110.87 148.63 L109.34 148.95 L107.79 149.21 L106.24 149.42 L104.69 149.57 L103.12 149.66 L101.56 149.70 L100.00 149.68 L98.44 149.61 L96.89 149.50 L95.34 149.33 L93.79 149.13 L92.26 148.88 L90.73 148.59 L89.21 148.27 L87.70 147.91 L86.20 147.51 L84.70 147.09 L83.21 146.62 L81.74 146.13 L80.27 145.60 L78.81 145.03 L77.37 144.42 L75.93 143.78 L74.52 143.09 L73.12 142.36 L71.74 141.58 L70.39 140.76 L69.07 139.88 L67.77 138.96 L66.52 137.98 L65.30 136.96 L64.12 135.88 L62.99 134.76 L61.91 133.58 L60.87 132.37 L59.89 131.11 L58.96 129.81 L58.09 128.48 L57.27 127.12 L56.51 125.72 L55.80 124.30 L55.14 122.86 L54.53 121.40 L53.97 119.92 L53.45 118.43 L52.99 116.93 L52.56 115.41 L52.18 113.89 L51.84 112.37 L51.54 110.83 L51.28 109.29 L51.05 107.75 L50.87 106.21 L50.72 104.66 L50.62 103.11 L50.55 101.55 L50.53 100.00 L50.54 98.45 L50.61 96.89 L50.71 95.34 L50.87 93.79 L51.07 92.25 L51.31 90.71 L51.61 89.18 L51.95 87.66 L52.34 86.15 L52.78 84.66 L53.26 83.17 L53.80 81.71 L54.38 80.26 L55.00 78.83 L55.67 77.41 L56.39 76.03 L57.15 74.66 L57.95 73.32 L58.80 72.00 L59.68 70.71 L60.61 69.45 L61.58 68.21 L62.58 67.01 L63.62 65.84 L64.70 64.70 L65.82 63.60 L66.97 62.53 L68.15 61.50 L69.37 60.51 L70.62 59.56 L71.90 58.65 L73.20 57.78 L74.54 56.95 L75.90 56.16 L77.28 55.41 L78.69 54.71 L80.12 54.05 L81.56 53.43 L83.03 52.86 L84.51 52.33 L86.01 51.84 L87.52 51.40 L89.05 51.01 L90.59 50.66 L92.14 50.35 L93.70 50.10 L95.26 49.89 L96.84 49.74 L98.42 49.64 L100.00 49.59 L101.58 49.60 L103.17 49.66 L104.75 49.78 L106.32 49.96 L107.89 50.20 L109.44 50.50 L110.99 50.85 L112.51 51.27 L114.02 51.74 L115.51 52.26 L116.98 52.84 L118.42 53.47 L119.84 54.15 L121.23 54.88 L122.60 55.65 L123.94 56.45 L125.25 57.30 L126.54 58.18 L127.80 59.10 L129.03 60.04 L130.24 61.01 L131.42 62.02 L132.58 63.04 L133.71 64.10 L134.82 65.18 L135.90 66.28 L136.96 67.41 L137.99 68.57 L138.99 69.76 L139.96 70.97 L140.90 72.21 L141.80 73.47 L142.66 74.77 L143.49 76.09 L144.28 77.44 L145.02 78.82 L145.71 80.22 L146.36 81.64 L146.96 83.09 L147.51 84.56 L148.01 86.05 L148.45 87.56 L148.85 89.08 L149.19 90.62 L149.48 92.16 L149.72 93.72 L149.91 95.28 L150.05 96.85 L150.15 98.42 L150.19 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><path d="M139.49 100.00 L139.50 101.24 L139.47 102.48 L139.39 103.72 L139.27 104.96 L139.10 106.19 L138.89 107.42 L138.64 108.64 L138.34 109.84 L138.00 111.04 L137.62 112.22 L137.19 113.39 L136.73 114.54 L136.22 115.67 L135.68 116.79 L135.10 117.88 L134.49 118.96 L133.84 120.01 L133.16 121.04 L132.45 122.05 L131.71 123.04 L130.95 124.00 L130.16 124.95 L129.34 125.87 L128.50 126.76 L127.63 127.63 L126.75 128.48 L125.83 129.30 L124.90 130.10 L123.95 130.87 L122.97 131.61 L121.97 132.32 L120.95 133.01 L119.90 133.65 L118.84 134.27 L117.75 134.85 L116.65 135.39 L115.53 135.89 L114.39 136.35 L113.24 136.77 L112.07 137.15 L110.89 137.49 L109.70 137.79 L108.50 138.04 L107.30 138.26 L106.09 138.43 L104.87 138.57 L103.66 138.67 L102.44 138.73 L101.22 138.76 L100.00 138.75 L98.78 138.72 L97.57 138.65 L96.36 138.55 L95.15 138.42 L93.94 138.27 L92.74 138.08 L91.54 137.87 L90.34 137.62 L89.15 137.35 L87.96 137.05 L86.78 136.71 L85.61 136.34 L84.45 135.93 L83.30 135.49 L82.16 135.01 L81.04 134.50 L79.93 133.94 L78.84 133.34 L77.77 132.71 L76.73 132.03 L75.71 131.32 L74.71 130.57 L73.75 129.78 L72.82 128.95 L71.91 128.09 L71.05 127.19 L70.21 126.26 L69.41 125.30 L68.65 124.32 L67.93 123.30 L67.24 122.27 L66.58 121.21 L65.97 120.13 L65.39 119.03 L64.85 117.91 L64.34 116.78 L63.87 115.63 L63.44 114.47 L63.05 113.30 L62.69 112.12 L62.37 110.93 L62.09 109.73 L61.84 108.53 L61.64 107.32 L61.47 106.10 L61.33 104.88 L61.23 103.66 L61.17 102.44 L61.15 101.22 L61.16 100.00 L61.21 98.78 L61.29 97.56 L61.40 96.35 L61.55 95.14 L61.73 93.94 L61.95 92.74 L62.19 91.55 L62.47 90.36 L62.78 89.19 L63.12 88.02 L63.49 86.86 L63.89 85.70 L64.33 84.56 L64.80 83.44 L65.30 82.32 L65.84 81.22 L66.41 80.14 L67.02 79.07 L67.66 78.02 L68.34 77.00 L69.05 75.99 L69.80 75.02 L70.58 74.06 L71.40 73.14 L72.24 72.24 L73.12 71.38 L74.03 70.55 L74.97 69.74 L75.93 68.98 L76.92 68.24 L77.94 67.54 L78.97 66.87 L80.03 66.23 L81.10 65.62 L82.19 65.05 L83.30 64.51 L84.42 64.00 L85.56 63.52 L86.70 63.07 L87.87 62.65 L89.04 62.27 L90.22 61.92 L91.42 61.60 L92.62 61.31 L93.83 61.07 L95.05 60.85 L96.28 60.68 L97.52 60.55 L98.76 60.46 L100.00 60.42 L101.24 60.42 L102.49 60.47 L103.73 60.56 L104.96 60.71 L106.19 60.90 L107.41 61.14 L108.62 61.42 L109.82 61.75 L111.00 62.13 L112.17 62.55 L113.32 63.01 L114.45 63.51 L115.56 64.04 L116.65 64.61 L117.72 65.22 L118.77 65.85 L119.80 66.52 L120.81 67.21 L121.80 67.92 L122.77 68.66 L123.72 69.43 L124.64 70.21 L125.55 71.02 L126.44 71.85 L127.30 72.70 L128.15 73.57 L128.97 74.46 L129.77 75.37 L130.55 76.31 L131.30 77.26 L132.02 78.24 L132.72 79.23 L133.39 80.25 L134.03 81.29 L134.64 82.35 L135.22 83.43 L135.76 84.52 L136.27 85.64 L136.75 86.77 L137.19 87.92 L137.59 89.08 L137.96 90.25 L138.29 91.44 L138.58 92.64 L138.83 93.85 L139.05 95.07 L139.22 96.29 L139.35 97.52 L139.44 98.76 L139.49 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><circle cx="100" cy="100" r="31.3" fill="url(#osg-dark)"/></svg>
        <span style='font-family:Newsreader,serif;font-weight:400;font-style:normal;font-size:2.2rem;color:#111214;line-height:1;letter-spacing:-0.02em;'>
          OneSattva
        </span>
      </div>
      <p style='font-family:Newsreader,serif;font-style:italic;color:#B6744A;font-size:0.95rem;margin:0 0 28px;letter-spacing:0.01em;'>Health, understood.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        auth_mode = st.radio("", ["Sign In", "Create Account"], horizontal=True, label_visibility="collapsed")
        st.divider()

        if auth_mode == "Sign In":
            if st.session_state.get("show_forgot_password"):
                st.markdown("##### Reset your password")
                st.caption("Enter your email and we'll send a reset link.")
                reset_email = st.text_input("Email address", key="reset_email_input")
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("Send reset link", type="primary", use_container_width=True, key="send_reset_btn"):
                        if reset_email:
                            try:
                                supabase.auth.reset_password_email(
                                    reset_email,
                                    options={"redirect_to": "https://wellness-coach-app-f2ssjkdxdey8vm2c287mnz.streamlit.app"}
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

        else:
            full_name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")
            st.divider()
            st.markdown("""
<div style='background:#E6E3DF;border-radius:10px;padding:14px 16px;margin-bottom:12px;font-size:12px;color:#6B6864;line-height:1.6;'>
<strong style='color:#111214;display:block;margin-bottom:6px;'>OneSattva is a pilot wellness tool — not a medical device</strong>
OneSattva provides AI-generated health guidance to support, not replace, qualified medical professionals.
This product is in closed pilot testing and under active development. Do not use it as the sole basis for medical decisions.
Always consult your doctor before changing medications, supplements, or treatment plans.
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

# ════════════════════════════════════════════════════════════════════════════════
# MAIN APP (shown when logged in)
# ════════════════════════════════════════════════════════════════════════════════
def show_main_app(user):
    user_id = user.id

    # Load profile
    profile = db_get_single("profiles", user_id)
    name = profile.get("full_name", "there") if profile else "there"
    cycle_day, cycle_phase, days_to_next = calculate_cycle_status(user_id)
    cycle_phase = cycle_phase or "Follicular (Day 1–14)"

    # Build system prompt once per session
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = build_system_prompt(user_id, profile)

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        # ── Brand mark + wordmark ──
        st.markdown(f"""
        <div style='padding:20px 4px 16px;border-bottom:1px solid rgba(242,243,239,0.12);margin-bottom:20px;'>
          <div style='display:flex;align-items:center;gap:9px;margin-bottom:12px;'>
            <svg width="28" height="28" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><defs><radialGradient id="osg-sb" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#B1643A"/><stop offset="40%" stop-color="#B1643A"/><stop offset="54%" stop-color="#BE7C58" stop-opacity="0.72"/><stop offset="70%" stop-color="#D2A084" stop-opacity="0.4"/><stop offset="86%" stop-color="#E6CCB8" stop-opacity="0.14"/><stop offset="100%" stop-color="#E6CCB8" stop-opacity="0"/></radialGradient></defs><path d="M194.49 100.00 L194.46 102.97 L194.34 105.94 L194.12 108.90 L193.81 111.85 L193.40 114.79 L192.90 117.72 L192.31 120.63 L191.62 123.52 L190.84 126.39 L189.97 129.23 L189.01 132.05 L187.96 134.82 L186.81 137.57 L185.57 140.27 L184.25 142.93 L182.84 145.54 L181.34 148.10 L179.76 150.61 L178.09 153.07 L176.35 155.47 L174.53 157.81 L172.64 160.09 L170.67 162.31 L168.64 164.46 L166.55 166.55 L164.39 168.57 L162.18 170.53 L159.91 172.42 L157.58 174.24 L155.21 175.99 L152.78 177.67 L150.31 179.28 L147.79 180.81 L145.23 182.27 L142.62 183.64 L139.97 184.94 L137.28 186.16 L134.56 187.28 L131.80 188.33 L129.01 189.27 L126.19 190.13 L123.34 190.89 L120.47 191.56 L117.57 192.13 L114.67 192.60 L111.74 192.97 L108.81 193.24 L105.88 193.42 L102.94 193.51 L100.00 193.50 L97.06 193.40 L94.14 193.22 L91.21 192.95 L88.30 192.60 L85.40 192.16 L82.52 191.65 L79.64 191.07 L76.79 190.41 L73.95 189.67 L71.13 188.86 L68.33 187.98 L65.55 187.02 L62.79 185.99 L60.06 184.87 L57.36 183.68 L54.70 182.41 L52.07 181.05 L49.48 179.61 L46.94 178.08 L44.45 176.46 L42.01 174.76 L39.64 172.97 L37.33 171.09 L35.09 169.12 L32.92 167.08 L30.84 164.95 L28.84 162.74 L26.92 160.46 L25.09 158.11 L23.34 155.69 L21.69 153.22 L20.12 150.69 L18.65 148.11 L17.26 145.49 L15.96 142.82 L14.75 140.12 L13.62 137.38 L12.58 134.61 L11.62 131.82 L10.74 129.00 L9.95 126.16 L9.23 123.31 L8.60 120.43 L8.04 117.54 L7.57 114.64 L7.19 111.73 L6.88 108.80 L6.66 105.87 L6.53 102.94 L6.49 100.00 L6.53 97.06 L6.67 94.13 L6.89 91.20 L7.21 88.28 L7.61 85.37 L8.11 82.47 L8.70 79.59 L9.37 76.73 L10.14 73.89 L10.99 71.08 L11.93 68.29 L12.95 65.53 L14.05 62.81 L15.24 60.11 L16.50 57.46 L17.85 54.84 L19.27 52.26 L20.77 49.72 L22.35 47.23 L24.00 44.78 L25.73 42.39 L27.53 40.05 L29.41 37.76 L31.36 35.54 L33.38 33.38 L35.47 31.29 L37.64 29.26 L39.87 27.31 L42.16 25.44 L44.52 23.64 L46.94 21.92 L49.41 20.29 L51.94 18.74 L54.52 17.27 L57.15 15.90 L59.82 14.60 L62.52 13.40 L65.27 12.28 L68.04 11.24 L70.85 10.29 L73.69 9.43 L76.54 8.64 L79.42 7.95 L82.32 7.34 L85.24 6.81 L88.17 6.37 L91.12 6.02 L94.07 5.75 L97.03 5.58 L100.00 5.50 L102.97 5.52 L105.94 5.63 L108.90 5.84 L111.85 6.16 L114.80 6.58 L117.72 7.10 L120.62 7.73 L123.50 8.47 L126.35 9.31 L129.16 10.25 L131.94 11.29 L134.67 12.43 L137.36 13.67 L140.00 15.00 L142.59 16.41 L145.13 17.91 L147.62 19.48 L150.05 21.13 L152.43 22.84 L154.76 24.62 L157.04 26.46 L159.26 28.36 L161.44 30.31 L163.56 32.32 L165.63 34.37 L167.65 36.48 L169.61 38.63 L171.52 40.83 L173.38 43.08 L175.18 45.38 L176.93 47.72 L178.61 50.12 L180.22 52.56 L181.76 55.05 L183.23 57.59 L184.63 60.18 L185.94 62.81 L187.17 65.49 L188.31 68.21 L189.36 70.97 L190.31 73.76 L191.17 76.59 L191.93 79.45 L192.59 82.34 L193.16 85.25 L193.62 88.17 L193.99 91.12 L194.25 94.07 L194.42 97.03 L194.49 100.00 Z" fill="none" stroke="#F7F5F2" stroke-width="1.3"/><path d="M183.80 100.00 L183.77 102.63 L183.66 105.26 L183.45 107.89 L183.17 110.51 L182.80 113.11 L182.34 115.71 L181.80 118.29 L181.18 120.84 L180.48 123.38 L179.69 125.89 L178.82 128.38 L177.87 130.83 L176.84 133.25 L175.73 135.64 L174.54 137.98 L173.28 140.29 L171.94 142.54 L170.52 144.76 L169.04 146.92 L167.48 149.03 L165.86 151.09 L164.18 153.09 L162.43 155.04 L160.63 156.93 L158.77 158.77 L156.86 160.55 L154.90 162.27 L152.89 163.93 L150.83 165.53 L148.73 167.07 L146.59 168.55 L144.40 169.97 L142.18 171.32 L139.91 172.61 L137.62 173.82 L135.28 174.97 L132.91 176.05 L130.51 177.06 L128.08 177.98 L125.61 178.83 L123.13 179.60 L120.61 180.29 L118.08 180.89 L115.53 181.41 L112.96 181.84 L110.38 182.19 L107.79 182.46 L105.20 182.64 L102.60 182.73 L100.00 182.75 L97.40 182.68 L94.81 182.54 L92.22 182.33 L89.64 182.04 L87.06 181.68 L84.50 181.25 L81.95 180.75 L79.41 180.18 L76.89 179.55 L74.38 178.85 L71.89 178.08 L69.42 177.25 L66.96 176.34 L64.54 175.37 L62.13 174.32 L59.76 173.20 L57.42 172.00 L55.12 170.72 L52.86 169.37 L50.64 167.93 L48.48 166.42 L46.37 164.83 L44.32 163.16 L42.33 161.41 L40.42 159.58 L38.57 157.69 L36.80 155.72 L35.10 153.69 L33.49 151.59 L31.95 149.44 L30.49 147.24 L29.12 144.98 L27.82 142.69 L26.61 140.35 L25.47 137.97 L24.41 135.57 L23.43 133.13 L22.53 130.67 L21.70 128.19 L20.94 125.69 L20.25 123.17 L19.64 120.63 L19.09 118.08 L18.62 115.52 L18.23 112.95 L17.90 110.37 L17.65 107.78 L17.47 105.19 L17.37 102.60 L17.34 100.00 L17.40 97.40 L17.53 94.81 L17.73 92.22 L18.02 89.64 L18.39 87.07 L18.83 84.52 L19.35 81.97 L19.95 79.45 L20.63 76.94 L21.38 74.45 L22.21 71.99 L23.10 69.55 L24.08 67.14 L25.12 64.76 L26.23 62.41 L27.41 60.09 L28.66 57.81 L29.98 55.56 L31.36 53.35 L32.81 51.19 L34.33 49.06 L35.92 46.99 L37.57 44.96 L39.29 42.99 L41.07 41.07 L42.91 39.20 L44.82 37.41 L46.78 35.67 L48.81 34.00 L50.89 32.40 L53.02 30.87 L55.21 29.42 L57.44 28.04 L59.72 26.74 L62.04 25.51 L64.41 24.36 L66.80 23.28 L69.23 22.29 L71.69 21.37 L74.18 20.52 L76.69 19.75 L79.22 19.06 L81.77 18.44 L84.34 17.90 L86.92 17.44 L89.52 17.05 L92.13 16.74 L94.75 16.51 L97.37 16.36 L100.00 16.29 L102.63 16.31 L105.26 16.41 L107.88 16.61 L110.50 16.89 L113.10 17.27 L115.69 17.74 L118.26 18.30 L120.81 18.95 L123.33 19.70 L125.82 20.54 L128.27 21.46 L130.69 22.48 L133.07 23.57 L135.41 24.75 L137.70 26.00 L139.95 27.33 L142.15 28.72 L144.31 30.18 L146.42 31.69 L148.48 33.27 L150.50 34.89 L152.47 36.57 L154.40 38.29 L156.28 40.06 L158.12 41.88 L159.91 43.74 L161.66 45.64 L163.36 47.58 L165.01 49.57 L166.62 51.60 L168.17 53.67 L169.66 55.79 L171.10 57.95 L172.48 60.16 L173.79 62.40 L175.03 64.69 L176.20 67.03 L177.30 69.40 L178.31 71.81 L179.25 74.25 L180.10 76.73 L180.87 79.24 L181.54 81.77 L182.13 84.33 L182.64 86.91 L183.05 89.51 L183.37 92.12 L183.60 94.74 L183.75 97.37 L183.80 100.00 Z" fill="none" stroke="#F7F5F2" stroke-width="1.3"/><path d="M170.96 100.00 L170.92 102.23 L170.80 104.45 L170.61 106.67 L170.35 108.89 L170.03 111.09 L169.63 113.28 L169.16 115.46 L168.63 117.62 L168.02 119.76 L167.35 121.88 L166.61 123.98 L165.81 126.06 L164.94 128.10 L164.00 130.12 L163.00 132.10 L161.94 134.05 L160.81 135.96 L159.62 137.84 L158.38 139.67 L157.08 141.47 L155.72 143.22 L154.31 144.93 L152.84 146.59 L151.33 148.21 L149.77 149.77 L148.17 151.30 L146.52 152.77 L144.84 154.20 L143.11 155.57 L141.34 156.90 L139.53 158.17 L137.69 159.39 L135.81 160.55 L133.90 161.66 L131.95 162.71 L129.97 163.70 L127.96 164.62 L125.93 165.48 L123.86 166.28 L121.77 167.00 L119.65 167.65 L117.52 168.23 L115.36 168.73 L113.19 169.16 L111.01 169.52 L108.82 169.79 L106.62 170.00 L104.41 170.13 L102.21 170.18 L100.00 170.17 L97.80 170.09 L95.60 169.94 L93.41 169.73 L91.23 169.45 L89.05 169.12 L86.89 168.73 L84.74 168.28 L82.60 167.78 L80.47 167.22 L78.36 166.61 L76.26 165.95 L74.17 165.23 L72.11 164.46 L70.06 163.63 L68.03 162.74 L66.03 161.79 L64.05 160.78 L62.11 159.71 L60.19 158.57 L58.32 157.37 L56.48 156.10 L54.69 154.77 L52.95 153.37 L51.26 151.91 L49.62 150.38 L48.04 148.79 L46.53 147.14 L45.07 145.44 L43.69 143.68 L42.37 141.87 L41.12 140.02 L39.93 138.12 L38.82 136.18 L37.77 134.21 L36.79 132.21 L35.87 130.18 L35.02 128.12 L34.24 126.04 L33.52 123.93 L32.87 121.81 L32.28 119.68 L31.75 117.52 L31.28 115.36 L30.88 113.19 L30.54 111.00 L30.26 108.81 L30.06 106.61 L29.91 104.41 L29.83 102.21 L29.82 100.00 L29.88 97.80 L30.00 95.60 L30.20 93.40 L30.46 91.21 L30.78 89.04 L31.18 86.87 L31.64 84.72 L32.17 82.58 L32.76 80.47 L33.42 78.37 L34.13 76.29 L34.91 74.23 L35.75 72.20 L36.65 70.19 L37.60 68.20 L38.61 66.25 L39.67 64.32 L40.79 62.43 L41.97 60.56 L43.20 58.73 L44.49 56.94 L45.83 55.18 L47.22 53.47 L48.67 51.80 L50.17 50.17 L51.72 48.59 L53.33 47.06 L54.99 45.59 L56.69 44.17 L58.45 42.81 L60.25 41.50 L62.09 40.26 L63.98 39.09 L65.90 37.97 L67.86 36.92 L69.86 35.94 L71.88 35.02 L73.93 34.17 L76.01 33.38 L78.12 32.66 L80.24 32.00 L82.39 31.40 L84.55 30.87 L86.73 30.41 L88.91 30.01 L91.12 29.68 L93.33 29.41 L95.55 29.22 L97.77 29.09 L100.00 29.03 L102.23 29.05 L104.46 29.14 L106.68 29.31 L108.90 29.56 L111.11 29.88 L113.30 30.28 L115.48 30.76 L117.63 31.32 L119.77 31.96 L121.87 32.68 L123.95 33.47 L126.00 34.33 L128.01 35.27 L129.99 36.27 L131.93 37.34 L133.83 38.46 L135.69 39.64 L137.52 40.88 L139.30 42.16 L141.05 43.50 L142.76 44.87 L144.43 46.29 L146.07 47.75 L147.66 49.24 L149.23 50.77 L150.75 52.34 L152.24 53.95 L153.68 55.59 L155.09 57.27 L156.46 58.98 L157.78 60.73 L159.06 62.52 L160.28 64.35 L161.46 66.21 L162.57 68.12 L163.63 70.06 L164.63 72.03 L165.56 74.04 L166.42 76.09 L167.21 78.16 L167.93 80.26 L168.57 82.39 L169.14 84.55 L169.63 86.72 L170.04 88.91 L170.38 91.11 L170.64 93.32 L170.82 95.54 L170.93 97.77 L170.96 100.00 Z" fill="none" stroke="#F7F5F2" stroke-width="1.3"/><path d="M161.03 100.00 L160.99 101.92 L160.89 103.83 L160.74 105.74 L160.52 107.65 L160.25 109.54 L159.93 111.43 L159.54 113.31 L159.10 115.17 L158.60 117.03 L158.05 118.86 L157.44 120.68 L156.77 122.48 L156.04 124.25 L155.25 126.00 L154.41 127.72 L153.50 129.41 L152.55 131.08 L151.53 132.70 L150.46 134.29 L149.34 135.85 L148.17 137.36 L146.94 138.83 L145.67 140.26 L144.36 141.65 L143.00 143.00 L141.60 144.30 L140.16 145.55 L138.68 146.76 L137.17 147.92 L135.63 149.04 L134.05 150.11 L132.45 151.13 L130.81 152.10 L129.15 153.03 L127.46 153.90 L125.75 154.72 L124.01 155.49 L122.25 156.20 L120.47 156.86 L118.67 157.46 L116.85 158.00 L115.02 158.49 L113.17 158.91 L111.31 159.27 L109.44 159.57 L107.56 159.81 L105.67 159.99 L103.78 160.11 L101.89 160.18 L100.00 160.18 L98.11 160.14 L96.22 160.03 L94.34 159.88 L92.46 159.68 L90.59 159.42 L88.72 159.12 L86.86 158.78 L85.01 158.38 L83.17 157.94 L81.33 157.45 L79.51 156.92 L77.70 156.33 L75.90 155.69 L74.12 155.00 L72.36 154.26 L70.61 153.46 L68.89 152.60 L67.20 151.68 L65.55 150.70 L63.92 149.66 L62.34 148.56 L60.79 147.39 L59.30 146.17 L57.85 144.88 L56.46 143.54 L55.12 142.15 L53.83 140.70 L52.61 139.20 L51.44 137.66 L50.34 136.08 L49.29 134.46 L48.31 132.80 L47.38 131.12 L46.51 129.41 L45.69 127.67 L44.93 125.91 L44.22 124.14 L43.57 122.34 L42.96 120.54 L42.40 118.71 L41.89 116.88 L41.43 115.04 L41.02 113.18 L40.66 111.32 L40.35 109.45 L40.10 107.57 L39.89 105.68 L39.74 103.79 L39.65 101.90 L39.61 100.00 L39.63 98.10 L39.72 96.21 L39.86 94.32 L40.06 92.43 L40.33 90.55 L40.66 88.68 L41.05 86.82 L41.50 84.98 L42.01 83.15 L42.57 81.34 L43.20 79.55 L43.88 77.78 L44.61 76.03 L45.39 74.30 L46.22 72.60 L47.11 70.92 L48.04 69.27 L49.02 67.64 L50.04 66.05 L51.11 64.48 L52.23 62.94 L53.39 61.44 L54.60 59.97 L55.85 58.54 L57.14 57.14 L58.48 55.79 L59.86 54.47 L61.29 53.21 L62.75 51.98 L64.26 50.81 L65.81 49.69 L67.39 48.61 L69.01 47.59 L70.66 46.63 L72.34 45.72 L74.05 44.86 L75.79 44.06 L77.56 43.31 L79.34 42.62 L81.15 41.99 L82.98 41.41 L84.82 40.88 L86.68 40.42 L88.56 40.00 L90.44 39.65 L92.34 39.35 L94.24 39.11 L96.16 38.94 L98.08 38.82 L100.00 38.77 L101.92 38.78 L103.85 38.86 L105.77 39.00 L107.68 39.22 L109.58 39.50 L111.47 39.86 L113.35 40.28 L115.21 40.78 L117.04 41.35 L118.85 41.98 L120.64 42.68 L122.39 43.44 L124.12 44.26 L125.82 45.14 L127.48 46.07 L129.11 47.06 L130.70 48.09 L132.26 49.16 L133.79 50.28 L135.29 51.43 L136.75 52.62 L138.19 53.84 L139.59 55.09 L140.97 56.38 L142.31 57.69 L143.63 59.03 L144.91 60.41 L146.16 61.81 L147.38 63.25 L148.57 64.71 L149.72 66.21 L150.82 67.75 L151.89 69.31 L152.91 70.91 L153.88 72.55 L154.79 74.22 L155.65 75.92 L156.46 77.65 L157.20 79.41 L157.88 81.20 L158.49 83.01 L159.04 84.84 L159.52 86.70 L159.93 88.57 L160.27 90.45 L160.55 92.35 L160.77 94.26 L160.92 96.17 L161.00 98.08 L161.03 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><path d="M150.19 100.00 L150.18 101.58 L150.13 103.15 L150.03 104.73 L149.88 106.30 L149.68 107.87 L149.43 109.43 L149.13 110.98 L148.78 112.52 L148.38 114.06 L147.93 115.57 L147.42 117.07 L146.86 118.56 L146.25 120.02 L145.59 121.45 L144.88 122.87 L144.11 124.25 L143.29 125.60 L142.43 126.93 L141.52 128.22 L140.57 129.48 L139.58 130.70 L138.55 131.89 L137.48 133.04 L136.38 134.16 L135.25 135.25 L134.08 136.30 L132.90 137.31 L131.68 138.30 L130.44 139.25 L129.18 140.17 L127.90 141.05 L126.59 141.91 L125.27 142.72 L123.92 143.51 L122.55 144.25 L121.16 144.96 L119.74 145.62 L118.31 146.25 L116.86 146.83 L115.39 147.35 L113.90 147.83 L112.39 148.26 L110.87 148.63 L109.34 148.95 L107.79 149.21 L106.24 149.42 L104.69 149.57 L103.12 149.66 L101.56 149.70 L100.00 149.68 L98.44 149.61 L96.89 149.50 L95.34 149.33 L93.79 149.13 L92.26 148.88 L90.73 148.59 L89.21 148.27 L87.70 147.91 L86.20 147.51 L84.70 147.09 L83.21 146.62 L81.74 146.13 L80.27 145.60 L78.81 145.03 L77.37 144.42 L75.93 143.78 L74.52 143.09 L73.12 142.36 L71.74 141.58 L70.39 140.76 L69.07 139.88 L67.77 138.96 L66.52 137.98 L65.30 136.96 L64.12 135.88 L62.99 134.76 L61.91 133.58 L60.87 132.37 L59.89 131.11 L58.96 129.81 L58.09 128.48 L57.27 127.12 L56.51 125.72 L55.80 124.30 L55.14 122.86 L54.53 121.40 L53.97 119.92 L53.45 118.43 L52.99 116.93 L52.56 115.41 L52.18 113.89 L51.84 112.37 L51.54 110.83 L51.28 109.29 L51.05 107.75 L50.87 106.21 L50.72 104.66 L50.62 103.11 L50.55 101.55 L50.53 100.00 L50.54 98.45 L50.61 96.89 L50.71 95.34 L50.87 93.79 L51.07 92.25 L51.31 90.71 L51.61 89.18 L51.95 87.66 L52.34 86.15 L52.78 84.66 L53.26 83.17 L53.80 81.71 L54.38 80.26 L55.00 78.83 L55.67 77.41 L56.39 76.03 L57.15 74.66 L57.95 73.32 L58.80 72.00 L59.68 70.71 L60.61 69.45 L61.58 68.21 L62.58 67.01 L63.62 65.84 L64.70 64.70 L65.82 63.60 L66.97 62.53 L68.15 61.50 L69.37 60.51 L70.62 59.56 L71.90 58.65 L73.20 57.78 L74.54 56.95 L75.90 56.16 L77.28 55.41 L78.69 54.71 L80.12 54.05 L81.56 53.43 L83.03 52.86 L84.51 52.33 L86.01 51.84 L87.52 51.40 L89.05 51.01 L90.59 50.66 L92.14 50.35 L93.70 50.10 L95.26 49.89 L96.84 49.74 L98.42 49.64 L100.00 49.59 L101.58 49.60 L103.17 49.66 L104.75 49.78 L106.32 49.96 L107.89 50.20 L109.44 50.50 L110.99 50.85 L112.51 51.27 L114.02 51.74 L115.51 52.26 L116.98 52.84 L118.42 53.47 L119.84 54.15 L121.23 54.88 L122.60 55.65 L123.94 56.45 L125.25 57.30 L126.54 58.18 L127.80 59.10 L129.03 60.04 L130.24 61.01 L131.42 62.02 L132.58 63.04 L133.71 64.10 L134.82 65.18 L135.90 66.28 L136.96 67.41 L137.99 68.57 L138.99 69.76 L139.96 70.97 L140.90 72.21 L141.80 73.47 L142.66 74.77 L143.49 76.09 L144.28 77.44 L145.02 78.82 L145.71 80.22 L146.36 81.64 L146.96 83.09 L147.51 84.56 L148.01 86.05 L148.45 87.56 L148.85 89.08 L149.19 90.62 L149.48 92.16 L149.72 93.72 L149.91 95.28 L150.05 96.85 L150.15 98.42 L150.19 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><path d="M139.49 100.00 L139.50 101.24 L139.47 102.48 L139.39 103.72 L139.27 104.96 L139.10 106.19 L138.89 107.42 L138.64 108.64 L138.34 109.84 L138.00 111.04 L137.62 112.22 L137.19 113.39 L136.73 114.54 L136.22 115.67 L135.68 116.79 L135.10 117.88 L134.49 118.96 L133.84 120.01 L133.16 121.04 L132.45 122.05 L131.71 123.04 L130.95 124.00 L130.16 124.95 L129.34 125.87 L128.50 126.76 L127.63 127.63 L126.75 128.48 L125.83 129.30 L124.90 130.10 L123.95 130.87 L122.97 131.61 L121.97 132.32 L120.95 133.01 L119.90 133.65 L118.84 134.27 L117.75 134.85 L116.65 135.39 L115.53 135.89 L114.39 136.35 L113.24 136.77 L112.07 137.15 L110.89 137.49 L109.70 137.79 L108.50 138.04 L107.30 138.26 L106.09 138.43 L104.87 138.57 L103.66 138.67 L102.44 138.73 L101.22 138.76 L100.00 138.75 L98.78 138.72 L97.57 138.65 L96.36 138.55 L95.15 138.42 L93.94 138.27 L92.74 138.08 L91.54 137.87 L90.34 137.62 L89.15 137.35 L87.96 137.05 L86.78 136.71 L85.61 136.34 L84.45 135.93 L83.30 135.49 L82.16 135.01 L81.04 134.50 L79.93 133.94 L78.84 133.34 L77.77 132.71 L76.73 132.03 L75.71 131.32 L74.71 130.57 L73.75 129.78 L72.82 128.95 L71.91 128.09 L71.05 127.19 L70.21 126.26 L69.41 125.30 L68.65 124.32 L67.93 123.30 L67.24 122.27 L66.58 121.21 L65.97 120.13 L65.39 119.03 L64.85 117.91 L64.34 116.78 L63.87 115.63 L63.44 114.47 L63.05 113.30 L62.69 112.12 L62.37 110.93 L62.09 109.73 L61.84 108.53 L61.64 107.32 L61.47 106.10 L61.33 104.88 L61.23 103.66 L61.17 102.44 L61.15 101.22 L61.16 100.00 L61.21 98.78 L61.29 97.56 L61.40 96.35 L61.55 95.14 L61.73 93.94 L61.95 92.74 L62.19 91.55 L62.47 90.36 L62.78 89.19 L63.12 88.02 L63.49 86.86 L63.89 85.70 L64.33 84.56 L64.80 83.44 L65.30 82.32 L65.84 81.22 L66.41 80.14 L67.02 79.07 L67.66 78.02 L68.34 77.00 L69.05 75.99 L69.80 75.02 L70.58 74.06 L71.40 73.14 L72.24 72.24 L73.12 71.38 L74.03 70.55 L74.97 69.74 L75.93 68.98 L76.92 68.24 L77.94 67.54 L78.97 66.87 L80.03 66.23 L81.10 65.62 L82.19 65.05 L83.30 64.51 L84.42 64.00 L85.56 63.52 L86.70 63.07 L87.87 62.65 L89.04 62.27 L90.22 61.92 L91.42 61.60 L92.62 61.31 L93.83 61.07 L95.05 60.85 L96.28 60.68 L97.52 60.55 L98.76 60.46 L100.00 60.42 L101.24 60.42 L102.49 60.47 L103.73 60.56 L104.96 60.71 L106.19 60.90 L107.41 61.14 L108.62 61.42 L109.82 61.75 L111.00 62.13 L112.17 62.55 L113.32 63.01 L114.45 63.51 L115.56 64.04 L116.65 64.61 L117.72 65.22 L118.77 65.85 L119.80 66.52 L120.81 67.21 L121.80 67.92 L122.77 68.66 L123.72 69.43 L124.64 70.21 L125.55 71.02 L126.44 71.85 L127.30 72.70 L128.15 73.57 L128.97 74.46 L129.77 75.37 L130.55 76.31 L131.30 77.26 L132.02 78.24 L132.72 79.23 L133.39 80.25 L134.03 81.29 L134.64 82.35 L135.22 83.43 L135.76 84.52 L136.27 85.64 L136.75 86.77 L137.19 87.92 L137.59 89.08 L137.96 90.25 L138.29 91.44 L138.58 92.64 L138.83 93.85 L139.05 95.07 L139.22 96.29 L139.35 97.52 L139.44 98.76 L139.49 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><circle cx="100" cy="100" r="31.3" fill="url(#osg-sb)"/></svg>
            <span style="font-family:Newsreader,serif;font-weight:400;font-style:normal;font-size:18px;color:#F7F5F2;line-height:1;letter-spacing:-0.02em;">
              OneSattva
            </span>
          </div>
          <div style="font-family:Inter,sans-serif;font-size:13px;color:#F7F5F2;opacity:0.7;">{name}</div>
          {f"<div style='font-family:Inter,sans-serif;font-size:11px;color:#F7F5F2;opacity:0.45;margin-top:2px;'>{profile.get('age','')}{'yr' if profile.get('age') else ''} · {profile.get('location','')}</div>" if profile else ""}
        </div>
        """, unsafe_allow_html=True)

        # ── Cycle status ──
        st.markdown("""<p style='font-family:Inter,sans-serif;font-size:11px;font-weight:600;letter-spacing:0.08em;color:#F7F5F2;opacity:0.45;margin:0 0 8px;text-transform:uppercase;'>Cycle</p>""", unsafe_allow_html=True)
        if cycle_day:
            st.markdown(f"""
            <div style='background:rgba(242,243,239,0.07);border-radius:10px;padding:12px 14px;margin-bottom:8px;'>
              <div style='font-family:JetBrains Mono,monospace;font-size:22px;color:#F7F5F2;font-weight:500;line-height:1;'>Day {cycle_day}</div>
              <div style='font-family:Inter,sans-serif;font-size:12px;color:#F7F5F2;opacity:0.6;margin-top:4px;'>{cycle_phase.split(' (')[0]}</div>
              {f"<div style='font-family:Inter,sans-serif;font-size:11px;color:#B6744A;margin-top:6px;'>~{days_to_next}d until next period</div>" if days_to_next else ""}
            </div>
            """, unsafe_allow_html=True)
            if st.button("New period started today", use_container_width=True, key="new_period"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": date.today().isoformat()})
                st.session_state.system_prompt = build_system_prompt(user_id, profile)
                st.rerun()
        else:
            st.markdown("""<div style='font-family:Inter,sans-serif;font-size:12px;color:#F7F5F2;opacity:0.5;'>Set period date in Profile tab</div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # ── Goals ──
        goals = db_get("goals", user_id)
        if goals:
            st.markdown("""<p style='font-family:Inter,sans-serif;font-size:11px;font-weight:600;letter-spacing:0.08em;color:#F7F5F2;opacity:0.45;margin:0 0 8px;text-transform:uppercase;'>Goals</p>""", unsafe_allow_html=True)
            for g in goals[:3]:
                st.markdown(f"""<div style='font-family:Inter,sans-serif;font-size:12px;color:#F7F5F2;opacity:0.7;padding:4px 0;border-bottom:1px solid rgba(242,243,239,0.07);'>{g['goal'][:45]}</div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # ── Sign out ──
        st.markdown(f"""<div style='font-family:Inter,sans-serif;font-size:11px;color:#F7F5F2;opacity:0.35;margin-bottom:8px;'>{user.email}</div>""", unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True, key="signout_btn"):
            sign_out()

    # ── Sidebar nav ────────────────────────────────────────────────────────────
    if "active_section" not in st.session_state:
        st.session_state.active_section = "home"

    with st.sidebar:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        NAV_ITEMS = [
            ("home",     "⌂",  "Home"),
            ("protocol", "◈",  "Protocol"),
            ("checkin",  "✓",  "Check-In"),
            ("coach",    "✦",  "Coach"),
            ("profile",  "◎",  "Profile & Data"),
        ]

        for section_key, icon, label in NAV_ITEMS:
            is_active = st.session_state.active_section == section_key
            bg = "rgba(247,245,242,0.12)" if is_active else "transparent"
            border = "rgba(247,245,242,0.20)" if is_active else "transparent"
            weight = "600" if is_active else "400"
            opacity = "1" if is_active else "0.65"
            st.markdown(f"""
            <div style='background:{bg};border:1px solid {border};border-radius:8px;
                        padding:9px 12px;margin-bottom:3px;cursor:pointer;'>
              <span style='font-family:Inter,sans-serif;font-size:13px;font-weight:{weight};
                           color:#F7F5F2;opacity:{opacity};'>
                <span style='margin-right:8px;opacity:0.7;'>{icon}</span>{label}
              </span>
            </div>
            """, unsafe_allow_html=True)
            if st.button(label, key=f"nav_{section_key}", use_container_width=True,
                         help=label):
                st.session_state.active_section = section_key
                st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Hide sidebar nav buttons — rendered as invisible overlays behind styled divs
    st.markdown("""
    <style>
    [data-testid="stSidebar"] [data-testid="stButton"] > button {
        position: absolute !important;
        opacity: 0 !important;
        height: 38px !important;
        margin-top: -40px !important;
        width: 100% !important;
        cursor: pointer !important;
        z-index: 10 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Section routing ─────────────────────────────────────────────────────────
    active_section = st.session_state.active_section

    # ════════════════════════════
    # HOME
    # ════════════════════════════
    if active_section == "home":

        # ── Data fetches ─────────────────────────────────────────────────────────
        checkins_home = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        today_logged_h = checkins_home and checkins_home[0].get("checkin_date") == date.today().isoformat()
        wearable_home = db_get("wearable_data", user_id, order_col="data_date", limit=1)
        labs_home = db_get("lab_reports", user_id, order_col="report_date", limit=3)
        recent_checkins_h = db_get("checkins", user_id, order_col="checkin_date", limit=30)
        wearable_30d = db_get("wearable_data", user_id, order_col="data_date", limit=30)

        # ── Plan mode banner ─────────────────────────────────────────────────────
        if st.session_state.get("roadmap_committed"):
            saved_rm = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
            rm_start = None
            rm_name = "Active programme"
            if saved_rm:
                try:
                    rm_start = datetime.fromisoformat(saved_rm[0]["generated_at"].replace("Z","")).date()
                    # Extract programme name from first non-empty line of roadmap text
                    for ln in (saved_rm[0].get("roadmap_text","") or "").split("\n"):
                        ln = ln.strip().lstrip("#").strip()
                        if ln and len(ln) < 80:
                            rm_name = ln
                            break
                except: pass
            days_in = (date.today() - rm_start).days if rm_start else 0
            week_in = (days_in // 7) + 1
            # Progress bar: assume 90-day programme, cap at 100%
            progress_pct = min(100, int((days_in / 90) * 100))
            st.markdown(f"""
            <div style='background:var(--graphite);border-radius:14px;padding:18px 22px;
                        margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;'>
              <div style='flex:1;'>
                <div style='font-family:Inter,sans-serif;font-size:10px;font-weight:600;
                            letter-spacing:0.08em;color:rgba(247,245,242,0.45);
                            text-transform:uppercase;margin-bottom:6px;'>Plan mode</div>
                <div style='font-family:Newsreader,serif;font-size:1.1rem;color:#F7F5F2;
                            font-weight:500;margin-bottom:10px;'>{rm_name[:60]}</div>
                <div style='display:flex;align-items:center;gap:10px;'>
                  <div style='flex:1;height:3px;background:rgba(247,245,242,0.12);
                              border-radius:2px;overflow:hidden;'>
                    <div style='width:{progress_pct}%;height:100%;
                                background:#B6744A;border-radius:2px;'></div>
                  </div>
                  <div style='font-family:JetBrains Mono,monospace;font-size:11px;
                              color:rgba(247,245,242,0.5);white-space:nowrap;'>Wk {week_in}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:var(--stone);border-radius:14px;padding:16px 20px;
                        margin-bottom:24px;border:1px dashed rgba(17,18,20,0.15);'>
              <div style='font-family:Inter,sans-serif;font-size:13px;color:var(--mid);'>
                No active plan — generate a Treatment Roadmap to unlock priorities and tracking.
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Greeting ─────────────────────────────────────────────────────────────
        now_h = datetime.now()
        hour_h = now_h.hour
        if hour_h < 12: greeting = "Good morning"
        elif hour_h < 17: greeting = "Good afternoon"
        else: greeting = "Good evening"

        st.markdown(f"""
        <div style='padding:0 0 20px;'>
          <h1 style='border:none;margin-bottom:2px !important;padding-bottom:0 !important;
                     font-family:Newsreader,serif;font-size:2rem;color:var(--graphite);'>
            {greeting}, {name.split()[0] if name else 'there'}.
          </h1>
          <p style='color:var(--mid);font-family:Inter,sans-serif;font-size:0.9rem;margin:0;'>
            {date.today().strftime('%A, %d %B %Y')} · Here's what matters today.
          </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Today's priorities ───────────────────────────────────────────────────
        st.markdown("""<p style='font-family:Inter,sans-serif;font-size:11px;font-weight:600;
            letter-spacing:0.08em;color:var(--mid);text-transform:uppercase;
            margin:0 0 12px;'>Today's priorities</p>""", unsafe_allow_html=True)

        if "home_priorities" not in st.session_state:
            # Check we have enough data to generate meaningful priorities
            has_data = (
                st.session_state.get("roadmap_committed") or
                labs_home or
                checkins_home or
                wearable_home
            )
            if has_data:
                with st.spinner("Preparing your priorities…"):
                    try:
                        # Build context for priority generation
                        rm_text = st.session_state.get("treatment_roadmap","") or ""
                        lab_summary = ""
                        if labs_home:
                            lab_lines = []
                            for l in labs_home[:3]:
                                lab_lines.append(f"- {l.get('test_name','Lab')} {l.get('report_date','')}: {l.get('summary') or l.get('notes','')}")
                            lab_summary = "\n".join(lab_lines)
                        wearable_summary = ""
                        if wearable_home:
                            w = wearable_home[0]
                            wearable_summary = (
                                f"Latest wearable ({w.get('data_date','')}):\n"
                                f"- Recovery: {w.get('recovery_score','?')}%\n"
                                f"- HRV: {w.get('hrv','?')} ms\n"
                                f"- Sleep performance: {w.get('sleep_performance','?')}%\n"
                                f"- Strain: {w.get('strain','?')}"
                            )
                        checkin_summary = ""
                        if checkins_home:
                            c = checkins_home[0]
                            checkin_summary = (
                                f"Latest check-in ({c.get('checkin_date','')}):\n"
                                f"- Energy: {c.get('energy','?')}/10\n"
                                f"- Mood: {c.get('mood','?')}/10\n"
                                f"- Sleep: {c.get('sleep_hours','?')}h, quality {c.get('sleep_quality','?')}/10\n"
                                f"- Notes: {c.get('notes','')}"
                            )
                        priority_prompt = f"""You are OneSattva. Generate exactly 3 priority cards for today based on the user's data below.

Respond ONLY with valid JSON — no markdown, no preamble, no explanation. Format:
[
  {{"triage": "act_today", "title": "...", "body": "..."}},
  {{"triage": "watch", "title": "...", "body": "..."}},
  {{"triage": "background", "title": "...", "body": "..."}}
]

Triage values must be exactly: act_today, watch, or background.
Title: max 8 words. Body: 2-3 sentences, specific and clinical.
Order by urgency: most urgent first.

If data is limited, generate priorities based on what is available — do not refuse.

USER DATA:
Roadmap: {rm_text[:800] if rm_text else 'No roadmap yet'}
Labs: {lab_summary or 'No labs uploaded'}
Wearable: {wearable_summary or 'No wearable data'}
Check-in: {checkin_summary or 'No check-in data'}
Today: {date.today().strftime('%A, %d %B %Y')}
Cycle: Day {cycle_day or '?'}, {(cycle_phase or 'Unknown').split(' (')[0]}"""

                        resp = ai_client.messages.create(
                            model="claude-sonnet-4-6",
                            max_tokens=600,
                            messages=[{"role": "user", "content": priority_prompt}]
                        )
                        raw = resp.content[0].text.strip()
                        # Strip markdown fences if present
                        raw = raw.replace("```json","").replace("```","").strip()
                        st.session_state.home_priorities = _json.loads(raw)
                    except Exception as e:
                        st.session_state.home_priorities = []
            else:
                st.session_state.home_priorities = []

        priorities = st.session_state.get("home_priorities", [])

        TRIAGE_LABELS = {
            "act_today": ("Act today", "triage-now"),
            "watch":     ("Watch",     "triage-watch"),
            "background":("Background","triage-background"),
        }

        if priorities:
            pc_cols = st.columns(len(priorities))
            for i, p in enumerate(priorities[:3]):
                triage_key = p.get("triage","background")
                label, css_class = TRIAGE_LABELS.get(triage_key, ("Background","triage-background"))
                with pc_cols[i]:
                    st.markdown(f"""
                    <div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;
                                padding:16px 18px;height:100%;min-height:140px;'>
                      <span class='{css_class}' style='display:inline-block;margin-bottom:10px;'>
                        {label}
                      </span>
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
            # Refresh button
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("↺ Refresh priorities", key="refresh_priorities"):
                del st.session_state["home_priorities"]
                st.rerun()
        else:
            st.markdown("""
            <div style='background:var(--stone);border-radius:12px;padding:20px 22px;
                        border:1px dashed rgba(17,18,20,0.12);'>
              <div style='font-family:Inter,sans-serif;font-size:13px;color:var(--mid);'>
                Priorities will appear here once you have a roadmap, labs, or check-in data.
                Add your profile and upload labs to get started.
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

        # ── Today's snapshot ─────────────────────────────────────────────────────
        st.markdown("""<p style='font-family:Inter,sans-serif;font-size:11px;font-weight:600;
            letter-spacing:0.08em;color:var(--mid);text-transform:uppercase;
            margin:0 0 12px;'>Today's snapshot</p>""", unsafe_allow_html=True)

        w = wearable_home[0] if wearable_home else {}
        c = checkins_home[0] if checkins_home else {}

        def snap_box(label, value, unit, sub, flag=""):
            flag_html = f"<div style='font-family:Inter,sans-serif;font-size:11px;color:#B6744A;margin-top:5px;'>{flag}</div>" if flag else ""
            if value is None:
                return f"""
                <div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;
                            padding:16px;border-style:dashed;'>
                  <div style='font-family:Inter,sans-serif;font-size:10px;font-weight:600;
                              letter-spacing:0.07em;color:var(--mid);text-transform:uppercase;
                              margin-bottom:8px;'>{label}</div>
                  <div style='font-family:Inter,sans-serif;font-size:12px;color:var(--mid);
                              opacity:0.6;'>No data</div>
                </div>"""
            return f"""
            <div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;padding:16px;'>
              <div style='font-family:Inter,sans-serif;font-size:10px;font-weight:600;
                          letter-spacing:0.07em;color:var(--mid);text-transform:uppercase;
                          margin-bottom:8px;'>{label}</div>
              <div style='font-family:JetBrains Mono,monospace;font-size:1.6rem;
                          color:var(--graphite);line-height:1;'>
                {value}<span style='font-size:0.65em;opacity:0.5;margin-left:2px;'>{unit}</span>
              </div>
              <div style='font-family:Inter,sans-serif;font-size:11px;color:var(--mid);
                          margin-top:5px;'>{sub}</div>
              {flag_html}
            </div>"""

        sn1, sn2, sn3, sn4 = st.columns(4)

        hrv_val = w.get("hrv") if w else None
        with sn1:
            st.markdown(snap_box("HRV", hrv_val, "ms", "WHOOP · latest"), unsafe_allow_html=True)

        rec_val = round(float(w["recovery_score"])) if w.get("recovery_score") else None
        with sn2:
            st.markdown(snap_box("Recovery", rec_val, "%", "WHOOP · latest"), unsafe_allow_html=True)

        sleep_val = w.get("sleep_performance") if w else None
        with sn3:
            st.markdown(snap_box("Sleep", sleep_val, "%", "WHOOP · latest"), unsafe_allow_html=True)

        energy_val = c.get("energy") if c else None
        energy_sub = f"Check-in · {c.get('checkin_date','')}" if c else "No check-in"
        with sn4:
            st.markdown(snap_box("Energy", energy_val, "/10", energy_sub), unsafe_allow_html=True)

        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

        # ── Trends ───────────────────────────────────────────────────────────────
        has_checkin_trend = len(recent_checkins_h) >= 7
        has_wearable_trend = len(wearable_30d) >= 7

        if True:  # always show trends section; individual cards handle empty states
            st.markdown("""<p style='font-family:Inter,sans-serif;font-size:11px;font-weight:600;
                letter-spacing:0.08em;color:var(--mid);text-transform:uppercase;
                margin:0 0 12px;'>Trends</p>""", unsafe_allow_html=True)

            tr1, tr2 = st.columns(2)

            # Energy trend — left column
            with tr1:
                if has_checkin_trend:
                    df_ci = pd.DataFrame(recent_checkins_h)
                    df_ci = df_ci.sort_values("checkin_date")
                    energy_vals = pd.to_numeric(df_ci.get("energy", pd.Series()), errors="coerce").dropna().tolist()
                    if energy_vals:
                        bars_html_e = "".join([
                            f"<div style='flex:1;background:var(--graphite);border-radius:2px 2px 0 0;height:{max(8,int((v/10)*100))}%;opacity:0.75;'></div>"
                            for v in energy_vals[-15:]
                        ])
                        st.markdown(f"""
                        <div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;padding:18px;'>
                          <div style='font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;
                                      color:var(--graphite);margin-bottom:6px;'>Energy · 30 days</div>
                          <div style='display:flex;align-items:flex-end;gap:3px;height:52px;margin-bottom:10px;'>
                            {bars_html_e}
                          </div>
                          <div style='font-family:Inter,sans-serif;font-size:12px;color:var(--mid);line-height:1.5;'>
                            Avg {sum(energy_vals)/len(energy_vals):.1f}/10 over {len(energy_vals)} logged days.
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;
                                padding:18px;border-style:dashed;min-height:130px;'>
                      <div style='font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;
                                  color:var(--graphite);margin-bottom:6px;'>Energy · 30 days</div>
                      <div style='font-family:Inter,sans-serif;font-size:12px;color:var(--mid);'>
                        Log 7+ check-ins to see your energy trend.
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

            # HRV trend — right column
            with tr2:
                if has_wearable_trend:
                    df_w = pd.DataFrame(wearable_30d)
                    df_w = df_w.sort_values("data_date")
                    hrv_vals = pd.to_numeric(df_w.get("hrv", pd.Series()), errors="coerce").dropna().tolist()
                    if hrv_vals:
                        max_hrv = max(hrv_vals) or 1
                        bars_html_h = "".join([
                            f"<div style='flex:1;background:var(--graphite);border-radius:2px 2px 0 0;height:{max(8,int((v/max_hrv)*100))}%;opacity:0.75;'></div>"
                            for v in hrv_vals[-15:]
                        ])
                        st.markdown(f"""
                        <div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;padding:18px;'>
                          <div style='font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;
                                      color:var(--graphite);margin-bottom:6px;'>HRV trajectory · 30 days</div>
                          <div style='display:flex;align-items:flex-end;gap:3px;height:52px;margin-bottom:10px;'>
                            {bars_html_h}
                          </div>
                          <div style='font-family:Inter,sans-serif;font-size:12px;color:var(--mid);line-height:1.5;'>
                            Avg {sum(hrv_vals)/len(hrv_vals):.0f} ms over {len(hrv_vals)} days.
                            Latest {hrv_vals[-1]:.0f} ms.
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style='background:#FFFFFF;border:1px solid var(--line);border-radius:12px;
                                padding:18px;border-style:dashed;min-height:130px;'>
                      <div style='font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;
                                  color:var(--graphite);margin-bottom:6px;'>HRV trajectory · 30 days</div>
                      <div style='font-family:Inter,sans-serif;font-size:12px;color:var(--mid);'>
                        Upload 7+ days of wearable data to see your HRV trend.
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ════════════════════════════
    # PROFILE & DATA — My Profile
    # ════════════════════════════
    if active_section == "profile":
        st.title("👤 My Profile")
        st.caption("Your complete health record — the foundation your coach reasons from.")

        # ── Personal info card ───────────────────────────────────────────────────
        if profile:
            pcol1, pcol2 = st.columns([2,1])
            with pcol1:
                st.markdown(f"""
                <div style='background:#F7F5F2;border-radius:12px;padding:20px;margin-bottom:8px;'>
                  <p style='font-family:Newsreader,serif;font-size:1.3rem;color:#111214;margin:0 0 4px;'>{profile.get('full_name','')}</p>
                  <p style='font-family:Inter,sans-serif;font-size:13px;color:#6B6864;margin:0;'>
                    {profile.get('age','?')} years · {profile.get('sex','')} · {profile.get('height_cm','?')}cm · {profile.get('weight_kg','?')}kg · {profile.get('blood_group','')}
                  </p>
                  <p style='font-family:Inter,sans-serif;font-size:13px;color:#6B6864;margin:4px 0 0;'>
                    {profile.get('location','')} · {profile.get('diet','')}
                  </p>
                  {f"<p style='font-family:Inter,sans-serif;font-size:12px;color:#9B9B92;margin:4px 0 0;'>Allergies: {profile.get('allergies')}</p>" if profile.get('allergies') else ""}
                </div>
                """, unsafe_allow_html=True)
            with pcol2:
                st.markdown(f"""
                <div style='background:#F7F5F2;border-radius:12px;padding:20px;text-align:center;'>
                  <div style='font-family:JetBrains Mono,monospace;font-size:1.6rem;color:#B6744A;'>Day {cycle_day or '?'}</div>
                  <div style='font-family:Inter,sans-serif;font-size:12px;color:#6B6864;margin-top:4px;'>{(cycle_phase or '').split(' (')[0]}</div>
                  {f"<div style='font-family:Inter,sans-serif;font-size:11px;color:#9B9B92;margin-top:2px;'>~{days_to_next}d until next period</div>" if days_to_next else ""}
                </div>
                """, unsafe_allow_html=True)

        # ── Edit personal details ────────────────────────────────────────────────
        with st.expander("✏️ Edit personal details"):
            with st.form("profile_form"):
                pc1, pc2 = st.columns(2)
                with pc1:
                    p_name = st.text_input("Full Name", value=profile.get("full_name","") if profile else "")
                    p_dob_val = profile.get("date_of_birth") if profile else None
                    p_dob = st.date_input("Date of birth",
                        value=date.fromisoformat(p_dob_val) if p_dob_val else date(1990,1,1),
                        min_value=date(1940,1,1), max_value=date.today())
                    p_sex = st.selectbox("Sex", ["","Female","Male","Intersex"],
                        index=["","Female","Male","Intersex"].index(profile.get("sex","")) if profile and profile.get("sex","") in ["Female","Male","Intersex"] else 0)
                    p_height = st.number_input("Height (cm)", 100, 220, value=int(profile.get("height_cm",165)) if profile and profile.get("height_cm") else 165)
                with pc2:
                    p_weight = st.number_input("Weight (kg)", 30, 200, value=int(profile.get("weight_kg",60)) if profile and profile.get("weight_kg") else 60)
                    p_blood = st.selectbox("Blood Group", ["","A+","A-","B+","B-","O+","O-","AB+","AB-"],
                        index=["","A+","A-","B+","B-","O+","O-","AB+","AB-"].index(profile.get("blood_group","")) if profile and profile.get("blood_group","") in ["A+","A-","B+","B-","O+","O-","AB+","AB-"] else 0)
                    p_location = st.text_input("Location", value=profile.get("location","") if profile else "")
                    p_diet = st.selectbox("Diet", ["Vegetarian (no eggs)","Vegetarian (with eggs)","Non-vegetarian","Vegan","Pescatarian"])
                p_allergies = st.text_input("Allergies", value=profile.get("allergies","") if profile else "")
                if st.form_submit_button("💾 Save", type="primary"):
                    age = (date.today() - p_dob).days // 365
                    success = db_upsert("profiles", {"id": user_id, "full_name": p_name, "age": age,
                        "date_of_birth": p_dob.isoformat(), "sex": p_sex,
                        "height_cm": p_height, "weight_kg": p_weight,
                        "blood_group": p_blood, "location": p_location,
                        "diet": p_diet, "allergies": p_allergies})
                    if success:
                        st.success("Saved!")
                        st.session_state.system_prompt = build_system_prompt(user_id, profile)
                        st.rerun()

        st.divider()

        # ── Cycle tracking ───────────────────────────────────────────────────────
        st.markdown("##### 🔄 Cycle")
        cd = db_get_single("cycle_data", user_id)
        with st.form("cycle_profile_form"):
            cyc1, cyc2, cyc3 = st.columns(3)
            with cyc1:
                default_date = date.fromisoformat(cd["last_period_start"]) if cd and cd.get("last_period_start") else date.today()
                new_period_date = st.date_input("Last period start", value=default_date, key="profile_cycle_date")
            with cyc2:
                new_avg_len = st.number_input("Avg cycle length", min_value=21, max_value=40, value=cd.get("avg_cycle_length",27) if cd else 27, key="profile_avg_len")
            with cyc3:
                if cycle_day:
                    st.metric("Today", f"Day {cycle_day}")
            if st.form_submit_button("Update cycle data"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": new_period_date.isoformat(), "avg_cycle_length": new_avg_len})
                st.success("Updated!")
                st.rerun()

        st.divider()

        col_left, col_right = st.columns(2)

        with col_left:
            # Goals
            st.markdown("##### 🎯 Goals")
            goals = db_get("goals", user_id)
            for g in goals:
                gc1, gc2 = st.columns([5,1])
                gc1.markdown(f"**{g['goal']}** · _{g.get('timeframe','')}_")
                if gc2.button("✕", key=f"del_goal_{g['id']}"):
                    db_delete("goals", g["id"]); st.rerun()
            with st.form("add_goal_profile"):
                gg1, gg2 = st.columns([3,1])
                with gg1: new_goal = st.text_input("New goal", placeholder="e.g. Reach 52kg by December")
                with gg2: new_tf = st.selectbox("Timeframe", ["3 months","6 months","12 months","12 months+"])
                if st.form_submit_button("+ Add") and new_goal:
                    db_upsert("goals", {"user_id": user_id, "goal": new_goal, "timeframe": new_tf}); st.rerun()

            st.divider()

            # Medical conditions
            st.markdown("##### 🩺 Medical conditions")
            conditions = db_get("medical_history", user_id)
            for c in conditions:
                cc1, cc2 = st.columns([5,1])
                cc1.write(f"**{c['condition']}** — {c.get('notes','')[:50]}")
                if cc2.button("✕", key=f"del_cond_{c['id']}"):
                    db_delete("medical_history", c["id"]); st.rerun()
            with st.form("add_cond_profile"):
                nc1, nc2 = st.columns([3,2])
                with nc1: new_cond = st.text_input("Condition", placeholder="e.g. Hypothyroidism")
                with nc2: new_notes = st.text_input("Notes", placeholder="e.g. since 2020")
                if st.form_submit_button("+ Add") and new_cond:
                    db_upsert("medical_history", {"user_id": user_id, "condition": new_cond, "notes": new_notes}); st.rerun()

        with col_right:
            # Medications
            st.markdown("##### 💊 Medications")
            meds = db_get("medications", user_id)
            for m in meds:
                mc1, mc2 = st.columns([5,1])
                mc1.write(f"**{m['name']}** — {m.get('dose','')} {m.get('frequency','')}")
                if mc2.button("✕", key=f"del_med_{m['id']}"):
                    db_delete("medications", m["id"]); st.rerun()
            with st.form("add_med_profile"):
                mm1, mm2, mm3 = st.columns(3)
                with mm1: new_med = st.text_input("Medication")
                with mm2: new_dose = st.text_input("Dose")
                with mm3: new_freq = st.text_input("Frequency")
                if st.form_submit_button("+ Add") and new_med:
                    db_upsert("medications", {"user_id": user_id, "name": new_med, "dose": new_dose, "frequency": new_freq, "active": True}); st.rerun()

            st.divider()

            # Supplements
            st.markdown("##### 🌿 Supplements")
            supps = db_get("supplements", user_id)
            for s in supps:
                sc1, sc2 = st.columns([5,1])
                sc1.write(f"**{s['name']}** — {s.get('dose','')} ({s.get('timing','')})")
                if sc2.button("✕", key=f"del_supp_{s['id']}"):
                    db_delete("supplements", s["id"]); st.rerun()
            with st.form("add_supp_profile"):
                ss1, ss2, ss3 = st.columns(3)
                with ss1: new_supp = st.text_input("Supplement")
                with ss2: new_sdose = st.text_input("Dose")
                with ss3: new_stiming = st.text_input("Timing")
                if st.form_submit_button("+ Add") and new_supp:
                    db_upsert("supplements", {"user_id": user_id, "name": new_supp, "dose": new_sdose, "timing": new_stiming, "active": True}); st.rerun()

        st.divider()
        st.markdown("##### ✏️ Profile notes")
        st.caption("Medication changes, new symptoms, anything your coach should know.")
        notes_rec = db_get_single("profile_notes", user_id)
        current_notes = notes_rec.get("notes","") if notes_rec else ""
        new_notes = st.text_area("Notes", value=current_notes, height=100,
            placeholder="e.g. Started Thorne B-Complex on 15 June. Energy has been better since adding Magnesium.")
        if st.button("💾 Save notes", type="primary"):
            db_upsert("profile_notes", {"user_id": user_id, "notes": new_notes})
            st.session_state.system_prompt = build_system_prompt(user_id, profile)
            st.success("Saved.")



    # ════════════════════════════
    # PROFILE & DATA — Lab Reports
    # ════════════════════════════
    if active_section == "profile":
        st.title("🧪 Lab Reports")
        st.caption("Upload results — AI analyses against functional ranges and compares to your history.")

        all_labs = db_get("lab_reports", user_id, order_col="report_date")
        three_months_ago_l = date.today() - timedelta(days=90)

        # ── Freshness status ─────────────────────────────────────────────────────
        if all_labs:
            latest_lab = all_labs[-1]
            try:
                latest_lab_date = date.fromisoformat(latest_lab["report_date"])
                lab_age_days = (date.today() - latest_lab_date).days
                if lab_age_days <= 90:
                    st.success(f"✅ Current labs: {latest_lab['report_date']} ({lab_age_days} days ago) — within 3-month active window")
                elif lab_age_days <= 180:
                    st.warning(f"⚠️ Last labs: {latest_lab['report_date']} ({lab_age_days} days ago) — consider retesting for current status")
                else:
                    st.error(f"🚨 Last labs: {latest_lab['report_date']} ({lab_age_days} days ago) — too old for current recommendations. Retest needed.")
            except:
                pass

        st.divider()

        # ── Upload new report ────────────────────────────────────────────────────
        with st.expander("📤 Upload new lab report", expanded=not bool(all_labs)):
            report_date_l = st.date_input("Report date", value=date.today(), key="lab_report_date")
            lab_name_l = st.text_input("Lab name", placeholder="e.g. Thyrocare, SRL, Apollo", key="lab_name")
            raw_values_l = st.text_area("Paste lab values", height=200, key="lab_raw_vals",
                placeholder="TSH: 1.83\nFT3: 2.2\nFT4: 1.31\nProlactin: 43.6\nFerritin: 35\nVitamin D: 46\nHaemoglobin: 11.3\n...")

            if st.button("🔍 Analyse & Save Report", type="primary", use_container_width=True, key="lab_analyse_btn"):
                if raw_values_l.strip():
                    # Get previous report for comparison
                    prev_lab_context = ""
                    if all_labs:
                        prev = all_labs[-1]
                        prev_lab_context = f"\n\nMOST RECENT PREVIOUS REPORT ({prev['report_date']} · {prev.get('lab_name','')}):\n{prev.get('raw_values','')[:800]}"

                    analysis_prompt = f"""New lab report — date: {report_date_l.isoformat()}, lab: {lab_name_l}

NEW VALUES:
{raw_values_l}
{prev_lab_context}

Analyse against functional medicine optimal ranges (not just conventional lab reference ranges).

FORMAT — complete all sections fully:

## Key Findings
Markdown table: Marker | Value | Functional Range | Status | Trend vs Previous
Use status labels: ✅ Optimal · ⚠️ Suboptimal · 🚨 Needs attention
Include trend: ↑ Rising · ↓ Falling · → Stable · — No previous data

## What This Report Tells Us
2-3 sentences on the overall clinical picture from this panel.

## Priority Actions
Numbered list of 3-5 specific changes to make based on these results — exact supplements, doses, dietary changes, or medical conversations to initiate.

## What to Retest Next Time
Which markers need follow-up and in how many weeks/months.

**Start today:** [one immediate action]

Complete every section. Never cut off."""

                    with st.spinner("Analysing against functional medicine ranges..."):
                        response = ai_client.messages.create(
                            model="claude-sonnet-4-6",
                            max_tokens=4096,
                            system=st.session_state.system_prompt,
                            messages=[{"role":"user","content":analysis_prompt}]
                        )
                        analysis = response.content[0].text

                    st.divider()
                    st.markdown(analysis)

                    # Save
                    sum_resp = ai_client.messages.create(
                        model="claude-sonnet-4-6", max_tokens=150,
                        messages=[{"role":"user","content":f"One dense line summary, max 150 chars: {raw_values_l}"}]
                    )
                    db_upsert("lab_reports", {
                        "user_id": user_id,
                        "report_date": report_date_l.isoformat(),
                        "lab_name": lab_name_l,
                        "raw_values": raw_values_l,
                        "summary": sum_resp.content[0].text[:500]
                    })
                    st.success("✅ Report saved.")
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.rerun()
                else:
                    st.warning("Paste your lab values above.")

        st.divider()

        # ── Lab history with freshness tags ──────────────────────────────────────
        if not all_labs:
            st.info("No reports uploaded yet. Upload your first report above.")
        else:
            st.markdown(f"##### Lab history · {len(all_labs)} report(s)")

            # Clear all
            if st.button("🗑️ Clear all lab history", key="clear_labs_btn"):
                for l in all_labs:
                    db_delete("lab_reports", l["id"])
                st.rerun()

            for lab in reversed(all_labs):
                try:
                    lab_date = date.fromisoformat(lab["report_date"])
                    age_days = (date.today() - lab_date).days
                    if age_days <= 90:
                        freshness_tag = "🟢 Current"
                    elif age_days <= 180:
                        freshness_tag = "🟡 Recent"
                    else:
                        freshness_tag = "⚪ Historical"
                except:
                    freshness_tag = ""

                with st.expander(f"{freshness_tag} · {lab['report_date']} · {lab.get('lab_name','')}"):
                    st.caption(lab.get("summary",""))
                    st.text_area("Raw values", value=lab.get("raw_values",""),
                        key=f"lab_raw_{lab['id']}", height=120)
                    if st.button("🗑️ Delete this report", key=f"del_lab_{lab['id']}"):
                        db_delete("lab_reports", lab["id"])
                        st.rerun()



    # ════════════════════════════
    # PROFILE & DATA — Wearable Data
    # ════════════════════════════
    if active_section == "profile":
        st.title("⌚ Wearable Data")
        st.caption("WHOOP data — recovery, HRV, sleep, and strain feed directly into your coach and protocols.")

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

    # ════════════════════════════
    # CHECK-IN
    # ════════════════════════════
    if active_section == "checkin":
        st.title("📋 Daily Check-In")

        now = datetime.now()
        hour = now.hour
        if hour < 12:
            time_greeting = "Morning check-in"
        elif hour < 17:
            time_greeting = "Afternoon check-in"
        else:
            time_greeting = "Evening check-in"

        st.caption(f"{time_greeting} · {date.today().strftime('%A, %d %B')} · Cycle Day {cycle_day or '?'}")

        today_checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        already_logged = today_checkins and today_checkins[0].get("checkin_date") == date.today().isoformat()

        # Get yesterday's values for smart defaults
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

            # Show today's snapshot
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Energy", f"{row.get('energy','?')}/10")
            c2.metric("Mood", f"{row.get('mood','?')}/10")
            c3.metric("Sleep", f"{row.get('sleep_hours','?')}h")
            c4.metric("Bloating", row.get('bloating','?'))
            c5.metric("Workout", row.get('workout','?')[:8] if row.get('workout') else '?')

            if row.get("notes"):
                st.caption(f"📝 {row['notes']}")

            # Show AI insight if not already generated
            if "checkin_insight" not in st.session_state:
                recent_for_insight = db_get("checkins", user_id, order_col="checkin_date", limit=7)
                insight_prompt = f"""Today's check-in for {name}:
Cycle Day {cycle_day or '?'} · {cycle_phase or 'Unknown phase'}
Energy: {row.get('energy')}/10 · Mood: {row.get('mood')}/10 · Sleep: {row.get('sleep_hours')}hrs (quality {row.get('sleep_quality')}/10)
Bloating: {row.get('bloating')} · Digestion: {row.get('digestion')} · Workout: {row.get('workout')}
Notes: {row.get('notes','')}

Recent 7-day pattern: {', '.join([f"Day {c.get('cycle_day','?')}: energy {c.get('energy','?')}, bloating {c.get('bloating','?')}" for c in (recent_for_insight or [])[:5]])}

Give ONE sharp clinical observation in 2-3 sentences. Reference their cycle phase and pattern if relevant. Be direct and specific — not generic encouragement. End with one concrete action for today if warranted."""

                with st.spinner(""):
                    insight_resp = ai_client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=300,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":insight_prompt}]
                    )
                    st.session_state.checkin_insight = insight_resp.content[0].text

            if st.session_state.get("checkin_insight"):
                st.markdown(f"""
                <div style='background:#F7F5F2;border-left:3px solid #B6744A;border-radius:0 10px 10px 0;
                            padding:14px 18px;margin-top:16px;'>
                <p style='font-family:Inter,sans-serif;font-size:13px;color:#111214;margin:0;line-height:1.6;'>
                {st.session_state.checkin_insight}
                </p>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            if st.button("✏️ Edit today's check-in", use_container_width=True):
                st.session_state.edit_checkin = True
                st.rerun()

        if not already_logged or st.session_state.get("edit_checkin"):
            if st.session_state.get("edit_checkin"):
                st.caption("Editing today's check-in")
                prefill = today_checkins[0] if today_checkins else {}
                prev_energy = int(prefill.get("energy", prev_energy))
                prev_mood = int(prefill.get("mood", prev_mood))
                prev_sleep_hrs = float(prefill.get("sleep_hours", prev_sleep_hrs))
                prev_sleep_q = int(prefill.get("sleep_quality", prev_sleep_q))
                prev_stress = int(prefill.get("stress", prev_stress))

            with st.form("checkin_form"):
                # Row 1 — Vitals (sliders, pre-filled from yesterday)
                st.markdown("**How are you feeling?**")
                s1, s2, s3 = st.columns(3)
                with s1:
                    c_energy = st.slider("⚡ Energy", 1, 10, prev_energy,
                        help="1 = exhausted, 10 = peak energy")
                with s2:
                    c_mood = st.slider("😊 Mood", 1, 10, prev_mood,
                        help="1 = very low, 10 = excellent")
                with s3:
                    c_stress = st.slider("😤 Stress", 1, 10, prev_stress,
                        help="1 = none, 10 = very high")

                # Row 2 — Sleep
                st.markdown("**Sleep last night**")
                sl1, sl2 = st.columns(2)
                with sl1:
                    c_sleep_hrs = st.number_input("Hours", 0.0, 12.0, prev_sleep_hrs, step=0.5)
                with sl2:
                    c_sleep_q = st.slider("Quality", 1, 10, prev_sleep_q)

                # Row 3 — Gut (most important for this patient)
                st.markdown("**Gut & digestion**")
                g1, g2, g3 = st.columns(3)
                with g1:
                    c_bloating = st.selectbox("Bloating", ["None","Mild","Moderate","Severe"],
                        index=["None","Mild","Moderate","Severe"].index(
                            today_checkins[0].get("bloating","None") if st.session_state.get("edit_checkin") and today_checkins else "None"))
                with g2:
                    c_digestion = st.selectbox("Digestion", ["Good","Average","Poor"],
                        index=["Good","Average","Poor"].index(
                            today_checkins[0].get("digestion","Good") if st.session_state.get("edit_checkin") and today_checkins else "Good"))
                with g3:
                    c_bowel = st.selectbox("Bowel", ["Normal","Loose","Constipated","None today"])

                # Row 4 — Activity + Rumination
                st.markdown("**Activity**")
                a1, a2 = st.columns(2)
                with a1:
                    # Smart default based on weekly protocol if it exists
                    workout_options = ["Strength Training","Padel","Cardio","Pilates","Walk/Steps only","Rest day","Other"]
                    c_workout = st.selectbox("Today's workout", workout_options)
                with a2:
                    c_rumination = st.selectbox("Rumination", ["None","Mild (1-2 episodes)","Moderate (3-5)","Frequent (5+)"])

                # Notes — free text, optional
                c_notes = st.text_area("Anything else?", placeholder="Unusual symptoms, stress, travel, medication change...", height=80)

                submitted = st.form_submit_button("✅ Save", type="primary", use_container_width=True)
                if submitted:
                    # Derive cycle phase from auto-calculated cycle_day
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
                        "energy": c_energy,
                        "mood": c_mood,
                        "stress": c_stress,
                        "sleep_hours": c_sleep_hrs,
                        "sleep_quality": c_sleep_q,
                        "bloating": c_bloating,
                        "digestion": c_digestion,
                        "bowel": c_bowel,
                        "workout": c_workout,
                        "rumination": c_rumination,
                        "notes": c_notes
                    })
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.session_state.pop("checkin_insight", None)
                    st.session_state.pop("edit_checkin", None)
                    st.rerun()



    # ════════════════════════════
    # PROTOCOL — Treatment Roadmap
    # ════════════════════════════
    if active_section == "protocol":
        st.title("🗺️ Treatment Roadmap")
        st.caption("Your 12-month strategic plan — generated once, committed to, updated only when significant new information warrants it.")

        if "treatment_roadmap" not in st.session_state:
            st.session_state.treatment_roadmap = None
        if "roadmap_date" not in st.session_state:
            st.session_state.roadmap_date = None
        if "roadmap_committed" not in st.session_state:
            st.session_state.roadmap_committed = False

        # Load from DB on first load
        if not st.session_state.treatment_roadmap:
            saved = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
            if saved:
                st.session_state.treatment_roadmap = saved[0]["roadmap_text"]
                st.session_state.roadmap_committed = saved[0].get("committed", False)
                try:
                    gen_dt = datetime.fromisoformat(saved[0]["generated_at"].replace("Z",""))
                    st.session_state.roadmap_date = gen_dt.strftime("%d %b %Y")
                except:
                    st.session_state.roadmap_date = "Previously"

        # ── COMMITTED STATE — locked roadmap ─────────────────────────────────────
        if st.session_state.treatment_roadmap and st.session_state.roadmap_committed:
            st.success(f"✅ Committed roadmap — generated {st.session_state.roadmap_date} · This is your active plan.")

            st.markdown(st.session_state.treatment_roadmap)
            st.divider()

            st.download_button("⬇️ Download roadmap", data=st.session_state.treatment_roadmap,
                file_name=f"onesattva_roadmap_{date.today()}.txt", use_container_width=True)

            with st.expander("⚠️ I have significant new information and need to update my roadmap"):
                st.warning("Your roadmap is your committed plan. Update it only if something significant has changed — new lab results, a medication change, a major health event, or a goal shift. Small week-to-week variations are handled by the weekly protocol, not the roadmap.")
                st.markdown("**What qualifies as a significant change?**")
                st.markdown("- New lab report showing a major shift in key markers\n- New diagnosis or medication added/removed\n- Achieved a major goal and ready to move to the next phase\n- A health event that changes your baseline (surgery, illness, pregnancy)")
                change_reason = st.text_area("Describe what has changed:", placeholder="e.g. New Thyrocare panel shows prolactin has normalised. Starting Cabergoline. Ready to update Phase 2.")
                if st.button("🔄 Generate Updated Roadmap", type="primary", use_container_width=True):
                    if change_reason.strip():
                        st.session_state.roadmap_committed = False
                        st.session_state.treatment_roadmap = None
                        st.session_state.roadmap_change_reason = change_reason
                        st.rerun()
                    else:
                        st.error("Please describe what has changed before regenerating.")

        # ── UNCOMMITTED STATE — generate or review ────────────────────────────────
        else:
            if st.session_state.treatment_roadmap:
                # Has a roadmap but not yet committed — review and commit
                st.info("📋 Review your roadmap below. When you're ready, commit to it — this becomes your fixed plan that your weekly protocols are built from.")
                st.markdown(st.session_state.treatment_roadmap)
                st.divider()

                st.markdown("##### Ready to commit to this plan?")
                st.caption("Committing means this becomes your active roadmap. Your weekly protocols will be built from it. You can update it later if something significant changes.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Commit to this roadmap", type="primary", use_container_width=True):
                        db_upsert("roadmaps", {
                            "user_id": user_id,
                            "roadmap_text": st.session_state.treatment_roadmap,
                            "committed": True,
                            "priority_focus": st.session_state.get("rm_priority_saved",""),
                            "intensity": st.session_state.get("rm_intensity_saved","")
                        })
                        st.session_state.roadmap_committed = True
                        st.success("Roadmap committed. Your weekly protocols will now be built from this plan.")
                        st.rerun()
                with col2:
                    if st.button("🔄 Regenerate instead", use_container_width=True):
                        st.session_state.treatment_roadmap = None
                        st.rerun()
            else:
                # No roadmap yet — generate
                st.markdown("##### Generate your treatment roadmap")
                st.caption("This is generated once based on your full profile, labs, and goals. Take time to review it before committing.")

                rm_col1, rm_col2 = st.columns(2)
                with rm_col1:
                    rm_priority = st.selectbox("Priority focus", ["Balanced — all areas","Fastest path to natural conception","Fastest path to fat loss","Fastest path off thyroid medication","Gut/digestion first"], key="rm_priority")
                with rm_col2:
                    rm_intensity = st.selectbox("Change intensity", ["Moderate — sustainable, gradual","Aggressive — willing to make bigger changes faster"], key="rm_intensity")

                if st.button("🗺️ Generate My Treatment Roadmap", type="primary", use_container_width=True):
                    change_context = ""
                    if st.session_state.get("roadmap_change_reason"):
                        change_context = f"\n\nIMPORTANT — This is an UPDATE. The patient has reported the following significant change that warrants a new roadmap:\n{st.session_state.roadmap_change_reason}\nAdjust the new roadmap to account for this change specifically."

                    roadmap_prompt = f"""Generate a comprehensive 12-month treatment roadmap for this patient.

Priority: {rm_priority}
Intensity: {rm_intensity}
{change_context}

Use the patient's full profile, labs (current and historical), check-ins, and wearable data from your context. Be direct — state what is NOT working and what needs to change, not just a description of what they already do.

FORMAT — use this exact structure, completing every section fully:

## Where Things Stand
3-4 sentences: the core biological blockers right now, why the current approach is insufficient, and what the priority order should be. Be direct.

## Phase 1 — Months 0-3: [give this phase a clear title]
Markdown table with columns: Change | Current → New | Clinical Reason
Include 5-7 rows covering: supplement changes, dietary shifts, routine changes, training adjustments. Be specific — exact doses, exact timing, exact foods.
**Retest at 3 months:** [list 4-5 specific markers]
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
2-3 sentences: what it means, what the escalation would be, what additional testing or specialist input would be needed.

## Maintenance — After Goals Are Achieved
2-3 sentences: what the patient should continue doing long-term, what to watch for, when to return for guidance.

**Start today:** [one specific, immediate action]

Complete every section fully. Never cut off."""

                    with st.spinner("Building your 12-month treatment roadmap — this takes 30-40 seconds..."):
                        response = ai_client.messages.create(
                            model="claude-sonnet-4-6",
                            max_tokens=4096,
                            system=st.session_state.system_prompt,
                            messages=[{"role": "user", "content": roadmap_prompt}]
                        )
                        st.session_state.treatment_roadmap = response.content[0].text
                        st.session_state.roadmap_date = date.today().strftime("%d %b %Y")
                        st.session_state.rm_priority_saved = rm_priority
                        st.session_state.rm_intensity_saved = rm_intensity
                        # Save as uncommitted draft
                        db_upsert("roadmaps", {
                            "user_id": user_id,
                            "roadmap_text": st.session_state.treatment_roadmap,
                            "committed": False,
                            "priority_focus": rm_priority,
                            "intensity": rm_intensity
                        })
                        st.rerun()


    # ════════════════════════════
    # PROTOCOL — Weekly Protocol
    # ════════════════════════════
    if active_section == "protocol":
        st.title("📅 Protocol")
        st.caption("Monthly overview · Weekly execution · Built from your committed roadmap.")

        # ── Check for gap detection ──────────────────────────────────────────────
        checkins_recent = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        gap_days = 0
        if checkins_recent:
            try:
                last_ci = date.fromisoformat(checkins_recent[0]["checkin_date"])
                gap_days = (date.today() - last_ci).days
            except:
                gap_days = 0

        if gap_days >= 14:
            st.warning(f"⚠️ It's been {gap_days} days since your last check-in. Before viewing your protocol, tell your coach what's changed — your protocol may need to be refreshed.")
            reentry_note = st.text_area("What's changed in the last few weeks?",
                placeholder="e.g. Been travelling, energy has been low, stopped taking some supplements, had a stressful period...",
                key="reentry_note")
            if st.button("📋 Update my coach and continue", type="primary", use_container_width=True):
                if reentry_note.strip():
                    # Save as a note and clear the weekly protocol so it regenerates
                    existing_notes = db_get_single("profile_notes", user_id)
                    current_notes = existing_notes.get("notes","") if existing_notes else ""
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
            st.info(f"👋 Welcome back — it's been {gap_days} days. Has anything changed? If so, update your profile notes before generating this week's protocol.")

        # ── No roadmap state ─────────────────────────────────────────────────────
        if not st.session_state.get("treatment_roadmap"):
            st.info("💡 Generate and commit your Treatment Roadmap first — your monthly and weekly protocols are built from it.")
            st.stop()

        # ── Calculate roadmap position ───────────────────────────────────────────
        roadmap_start = None
        saved_roadmaps = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
        if saved_roadmaps and saved_roadmaps[0].get("committed"):
            try:
                roadmap_start = datetime.fromisoformat(
                    saved_roadmaps[0]["generated_at"].replace("Z","")).date()
            except:
                roadmap_start = date.today()
        else:
            roadmap_start = date.today()

        days_into_roadmap = (date.today() - roadmap_start).days
        current_week_num = (days_into_roadmap // 7) + 1
        current_month_num = (days_into_roadmap // 30) + 1
        current_month_name = date.today().strftime("%B %Y")

        if days_into_roadmap < 90:
            roadmap_phase = "Phase 1"
        elif days_into_roadmap < 180:
            roadmap_phase = "Phase 2"
        else:
            roadmap_phase = "Phase 3"

        # ── MONTHLY OVERVIEW ─────────────────────────────────────────────────────
        if "monthly_protocol" not in st.session_state:
            st.session_state.monthly_protocol = None
        if "monthly_protocol_month" not in st.session_state:
            st.session_state.monthly_protocol_month = None

        # Auto-generate monthly if it's a new month or doesn't exist
        needs_monthly = (
            not st.session_state.monthly_protocol or
            st.session_state.monthly_protocol_month != current_month_name
        )

        with st.container():
            month_header_col, month_btn_col = st.columns([3,1])
            with month_header_col:
                st.markdown(f"""
                <div style='background:var(--mist,#F7F5F2);border-left:3px solid #B6744A;border-radius:0 10px 10px 0;padding:14px 18px;margin-bottom:4px;'>
                <p style='font-family:Newsreader,serif;font-size:1.1rem;color:#111214;margin:0;font-weight:500;'>
                  {current_month_name} · Month {current_month_num} · {roadmap_phase} · Week {current_week_num} overall
                </p>
                </div>
                """, unsafe_allow_html=True)
            with month_btn_col:
                if st.button("↻ Refresh month", use_container_width=True, key="refresh_month"):
                    st.session_state.monthly_protocol = None

            if needs_monthly:
                with st.spinner(f"Building {current_month_name} overview..."):
                    monthly_prompt = f"""Generate the monthly protocol overview for Month {current_month_num} of this patient's treatment roadmap.

Today: {date.today().strftime("%d %B %Y")}
Roadmap phase: {roadmap_phase} (Week {current_week_num} of the roadmap)
Cycle phase today: {cycle_phase or 'Unknown'}

Use the committed roadmap from your context to extract what Phase this month falls in and what the priorities are.

FORMAT — concise, no fluff:

## Month {current_month_num} — {current_month_name}
**Roadmap phase:** {roadmap_phase}
**This month's focus:** [1-2 sentences — what is the primary clinical focus this month based on the roadmap]

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

**End of month check:** [what to assess at month end to know if Phase is working]

Keep it tight — this is the map for the month, not an essay."""

                    monthly_resp = ai_client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=1500,
                        system=st.session_state.system_prompt,
                        messages=[{"role":"user","content":monthly_prompt}]
                    )
                    st.session_state.monthly_protocol = monthly_resp.content[0].text
                    st.session_state.monthly_protocol_month = current_month_name

            if st.session_state.monthly_protocol:
                with st.expander(f"📅 {current_month_name} — Monthly Overview", expanded=True):
                    st.markdown(st.session_state.monthly_protocol)

        st.divider()

        # ── WEEKLY PROTOCOL ───────────────────────────────────────────────────────
        today_dt = datetime.now()
        day_names = [(today_dt + timedelta(days=i)).strftime("%A %d %b") for i in range(7)]
        days_str = ", ".join(day_names)
        week_start = day_names[0]
        week_end = day_names[6]

        # Cycle phase selector (auto-filled, overridable)
        wp1, wp2, wp3 = st.columns(3)
        with wp1:
            default_phase_idx = 0
            if cycle_phase:
                phases = ["Follicular (Day 1–14)","Ovulation (Day 14–16)","Luteal (Day 16–28)","Menstruation (Day 1–5)"]
                for i, p in enumerate(phases):
                    if cycle_phase.startswith(p.split(" (")[0]):
                        default_phase_idx = i
                        break
            wp_phase = st.selectbox("Cycle phase", phases, index=default_phase_idx, key="wp_phase")
        with wp2:
            st.metric("Cycle Day", cycle_day if cycle_day else "?")
        with wp3:
            wp_focus = st.selectbox("Priority focus", ["Balanced","Fat loss","Fertility & conception","Gut healing","Energy & thyroid","Sleep & recovery"], key="wp_focus")

        if "weekly_protocol" not in st.session_state:
            st.session_state.weekly_protocol = None
        if "weekly_protocol_week" not in st.session_state:
            st.session_state.weekly_protocol_week = None

        week_label = f"Week {current_week_num} · {week_start} – {week_end}"
        st.markdown(f"**{week_label}**")

        gen_col, dl_col = st.columns([3,1])
        with gen_col:
            gen_btn = st.button("🔄 Generate This Week's Protocol", type="primary", use_container_width=True)
        with dl_col:
            if st.session_state.weekly_protocol:
                st.download_button("⬇️", data=st.session_state.weekly_protocol,
                    file_name=f"onesattva_week{current_week_num}_{date.today()}.txt",
                    use_container_width=True)

        if gen_btn:
            roadmap_ctx = f"\n\nCOMMITTED ROADMAP — this is Week {current_week_num} of the roadmap ({roadmap_phase}). Implement the changes relevant to this phase. The monthly overview for this month is:\n{st.session_state.monthly_protocol or 'Not yet generated'}\n\nFull roadmap:\n{(st.session_state.treatment_roadmap or '')[:2000]}"

            base_ctx = f"""Weekly protocol — Week {current_week_num} of roadmap · {roadmap_phase} · {week_label}
Cycle: Day {cycle_day or '?'} · {wp_phase} · Focus: {wp_focus}
Days to plan: {days_str}
{roadmap_ctx}

RULES: Output ONLY markdown tables. Complete all tables fully — never cut off.
Respect diet (no eggs, gut-friendly, cooked/warm foods).
If medication includes Thyronorm — always first on waking, plain water only, 45-60 min gap before anything else."""

            with st.spinner("Building supplement & routine schedule..."):
                r1 = ai_client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=2000,
                    system=st.session_state.system_prompt,
                    messages=[{"role":"user","content":base_ctx+"\n\nGenerate ONLY: ## Daily Routine & Supplement Schedule\nMarkdown table: Time | Item | Dose | Notes\nThyronorm as first row if prescribed. Include all supplements with exact timing. Complete fully."}])
                part1 = r1.content[0].text

            with st.spinner("Building 7-day nutrition plan..."):
                r2 = ai_client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=4096,
                    system=st.session_state.system_prompt,
                    messages=[{"role":"user","content":base_ctx+f"\n\nGenerate ONLY: ## 7-Day Nutrition Plan\nMarkdown table. Columns: Meal Slot | {days_str}\nRows: Pre-Workout Snack | First Meal | Lunch | Evening Snack | Dinner | Seed Cycling\nOne specific food + portion per cell, max 10 words. Gut-friendly, cooked/warm. Vary day to day. Complete all 7 days fully."}])
                part2 = r2.content[0].text

            with st.spinner("Building training & lifestyle plan..."):
                r3 = ai_client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=3000,
                    system=st.session_state.system_prompt,
                    messages=[{"role":"user","content":base_ctx+f"\n\nGenerate ONLY:\n## 7-Day Training Plan\nTable: Day | Session Type | Specific Focus | Key Exercises\nUse actual day+date names: {days_str}\nInclude: rest day, recovery-aware sessions (check wearable data if available), cycle-phase appropriate loads.\n\n## This Week's Priorities\nExactly 3 bullets: (1) sleep/recovery target (2) one lifestyle or gut-healing practice (3) one thing to monitor and log\n\n**Start today ({day_names[0]}):** [one specific immediate action]\n\nComplete both sections fully."}])
                part3 = r3.content[0].text

            st.session_state.weekly_protocol = part1 + "\n\n---\n\n" + part2 + "\n\n---\n\n" + part3
            st.session_state.weekly_protocol_week = current_week_num
            st.rerun()

        if st.session_state.weekly_protocol:
            st.markdown(st.session_state.weekly_protocol)
            if st.button("🔄 Regenerate this week", use_container_width=True, key="regen_weekly"):
                st.session_state.weekly_protocol = None
                st.rerun()


    # ════════════════════════════
    # PROTOCOL — Trends
    # ════════════════════════════
    if active_section == "protocol":
        st.title("📊 My Trends")
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

            # ── 7-day snapshot ───────────────────────────────────────────────────
            st.markdown("#### Last 7 days")
            tc1,tc2,tc3,tc4,tc5 = st.columns(5)
            metrics = [
                (tc1,"energy","Energy",""),
                (tc2,"mood","Mood",""),
                (tc3,"sleep_hours","Sleep","hrs"),
                (tc4,"sleep_quality","Sleep Quality",""),
                (tc5,"stress","Stress",""),
            ]
            for col, field, label, unit in metrics:
                if field in recent_t.columns:
                    val = pd.to_numeric(recent_t[field], errors="coerce").mean()
                    if not pd.isna(val):
                        col.metric(label, f"{val:.1f}{unit}")

            # ── Pattern detection ─────────────────────────────────────────────────
            st.divider()
            st.markdown("#### Pattern flags")

            flags = []
            if "energy" in df_t.columns and "cycle_phase" in df_t.columns:
                for phase in ["Luteal","Follicular","Ovulation","Menstruation"]:
                    phase_data = df_t[df_t["cycle_phase"] == phase]
                    if len(phase_data) >= 3:
                        avg_energy = pd.to_numeric(phase_data["energy"], errors="coerce").mean()
                        if avg_energy <= 4:
                            flags.append(f"⚠️ **Consistently low energy in {phase} phase** (avg {avg_energy:.1f}/10 across {len(phase_data)} logged days)")

            if "bloating" in df_t.columns:
                bloating_counts = last_30["bloating"].value_counts()
                mod_severe = bloating_counts.get("Moderate",0) + bloating_counts.get("Severe",0)
                if mod_severe >= 10:
                    flags.append(f"⚠️ **Bloating {mod_severe} of last 30 days** at moderate or severe — persistent gut pattern")

            if "sleep_hours" in df_t.columns:
                avg_sleep = pd.to_numeric(last_30["sleep_hours"], errors="coerce").mean()
                if not pd.isna(avg_sleep) and avg_sleep < 6.5:
                    flags.append(f"⚠️ **Average sleep {avg_sleep:.1f}hrs over last 30 days** — consistently below functional threshold of 7hrs")

            if "energy" in df_t.columns and "mood" in df_t.columns:
                last_7_energy = pd.to_numeric(recent_t["energy"], errors="coerce").mean()
                prev_7_energy = pd.to_numeric(df_t.tail(14).head(7)["energy"], errors="coerce").mean()
                if not pd.isna(last_7_energy) and not pd.isna(prev_7_energy):
                    if last_7_energy < prev_7_energy - 1.5:
                        flags.append(f"📉 **Energy declining** — down {prev_7_energy-last_7_energy:.1f} points vs previous week")
                    elif last_7_energy > prev_7_energy + 1.5:
                        flags.append(f"📈 **Energy improving** — up {last_7_energy-prev_7_energy:.1f} points vs previous week")

            if flags:
                for f in flags:
                    st.markdown(f)
            else:
                st.success("✅ No significant pattern flags in your recent data.")

            # ── AI trend summary (generate once per session) ──────────────────────
            if len(df_t) >= 7:
                if st.button("✦ Ask your coach to interpret these trends", use_container_width=True, key="trend_insight_btn"):
                    trend_summary = df_t[["checkin_date","cycle_phase","energy","mood","sleep_hours","bloating","digestion"]].tail(30).to_string(index=False)
                    trend_prompt = f"""Analyse this patient's check-in trends over the last 30 days and give a clinical pattern interpretation.

Data:
{trend_summary}

Current cycle phase: {cycle_phase}
Current cycle day: {cycle_day}

Identify 2-3 meaningful patterns (not just describing the data — interpret what they mean clinically). Reference the cycle phase where relevant. Be direct and specific. If something warrants a change to the current protocol, say so. Keep it under 200 words total."""

                    with st.spinner("Analysing your patterns..."):
                        trend_resp = ai_client.messages.create(
                            model="claude-sonnet-4-6",
                            max_tokens=500,
                            system=st.session_state.system_prompt,
                            messages=[{"role":"user","content":trend_prompt}]
                        )
                        st.session_state.trend_insight = trend_resp.content[0].text

                if st.session_state.get("trend_insight"):
                    st.markdown(f"""
                    <div style='background:#F7F5F2;border-left:3px solid #B6744A;border-radius:0 10px 10px 0;
                                padding:16px 20px;margin:16px 0;'>
                    <p style='font-family:Inter,sans-serif;font-size:13px;color:#111214;margin:0;line-height:1.6;'>
                    {st.session_state.trend_insight}
                    </p>
                    </div>
                    """, unsafe_allow_html=True)

            st.divider()

            # ── Charts ────────────────────────────────────────────────────────────
            chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Energy & Mood", "Sleep", "Gut"])

            with chart_tab1:
                plot_fields = [f for f in ["energy","mood"] if f in df_t.columns]
                if plot_fields:
                    st.line_chart(df_t[["checkin_date"]+plot_fields].set_index("checkin_date"))

            with chart_tab2:
                sleep_fields = [f for f in ["sleep_hours","sleep_quality"] if f in df_t.columns]
                if sleep_fields:
                    st.line_chart(df_t[["checkin_date"]+sleep_fields].set_index("checkin_date"))

            with chart_tab3:
                if "bloating" in df_t.columns:
                    st.markdown("**Bloating frequency**")
                    st.bar_chart(df_t["bloating"].value_counts())
                if "digestion" in df_t.columns:
                    st.markdown("**Digestion frequency**")
                    st.bar_chart(df_t["digestion"].value_counts())

            st.divider()
            display_cols = [c for c in ["checkin_date","cycle_phase","energy","mood","stress","sleep_hours","sleep_quality","bloating","digestion","workout","notes"] if c in df_t.columns]
            st.dataframe(df_t[display_cols].sort_values("checkin_date", ascending=False), use_container_width=True, hide_index=True)



    # ════════════════════════════
    # COACH
    # ════════════════════════════
    if active_section == "coach":
        st.title("✦ Your Coach")
        st.caption("OneSattva · Integrative Medicine · Functional Labs · Ayurveda · TCM")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # ── Build full system prompt with roadmap + monthly context ─────────────
        roadmap_chat_ctx = ""
        if st.session_state.get("treatment_roadmap") and st.session_state.get("roadmap_committed"):
            roadmap_chat_ctx += f"\n\nCOMMITTED TREATMENT ROADMAP (the patient has committed to this plan — all advice must align with it):\n{st.session_state.treatment_roadmap[:1500]}"
        if st.session_state.get("monthly_protocol"):
            roadmap_chat_ctx += f"\n\nCURRENT MONTH PROTOCOL:\n{st.session_state.monthly_protocol[:800]}"

        cycle_ctx = f"\n\nCURRENT CYCLE STATUS: {cycle_phase or 'Unknown phase'}"
        if cycle_day:
            cycle_ctx += f", Day {cycle_day}"
        if days_to_next:
            cycle_ctx += f", ~{days_to_next} days until next period"
        cycle_ctx += f". Today is {date.today().strftime('%A %d %B %Y')}. Factor this into all recommendations."

        full_system = st.session_state.system_prompt + cycle_ctx + roadmap_chat_ctx

        # ── Welcome screen (shown when no messages yet) ──────────────────────────
        if not st.session_state.messages:
            # Dynamic context card
            last_checkin = db_get("checkins", user_id, order_col="checkin_date", limit=1)
            energy_note = ""
            if last_checkin:
                energy = last_checkin[0].get("energy")
                bloating = last_checkin[0].get("bloating","")
                ci_date = last_checkin[0].get("checkin_date","")
                if energy and int(energy) <= 4:
                    energy_note = f"Your last check-in ({ci_date}) showed low energy ({energy}/10)."
                elif bloating in ["Moderate","Severe"]:
                    energy_note = f"Your last check-in ({ci_date}) showed {bloating.lower()} bloating."

            wearable_note = ""
            recent_w = db_get("wearable_data", user_id, order_col="data_date", limit=1)
            if recent_w and recent_w[0].get("recovery_score"):
                rec = recent_w[0]["recovery_score"]
                if float(rec) < 50:
                    wearable_note = f"WHOOP recovery today: {rec}% — low."

            context_line = " · ".join(filter(None, [
                f"Day {cycle_day} · {cycle_phase.split(' (')[0]}" if cycle_day else None,
                energy_note or None,
                wearable_note or None
            ]))

            st.markdown(f"""
            <div style='background:#F7F5F2;padding:20px 24px;border-radius:14px;
                        border-left:3px solid #B6744A;margin-bottom:20px;'>
              <p style='font-family:Newsreader,serif;font-size:1.15rem;color:#111214;
                         margin:0 0 4px;font-weight:500;'>Good to see you, {name}.</p>
              <p style='font-family:Inter,sans-serif;font-size:13px;color:#6B6864;margin:0;'>
                I have your full profile, labs, and goals. Ask me anything — or pick a question below.
              </p>
              {f"<p style='font-family:Inter,sans-serif;font-size:12px;color:#B6744A;margin:8px 0 0;'>{context_line}</p>" if context_line else ""}
            </div>
            """, unsafe_allow_html=True)

            # Dynamic quick prompts based on current context
            st.markdown("<p style='font-family:Inter,sans-serif;font-size:13px;font-weight:500;color:#111214;margin-bottom:8px;'>Quick questions</p>", unsafe_allow_html=True)

            # Build dynamic prompts based on cycle phase, check-in data, roadmap status
            q_supplement = ("💊 My supplement protocol today",
                f"Give me my complete supplement schedule for today ({date.today().strftime('%A')}), Cycle Day {cycle_day or '?'} ({(cycle_phase or '').split(' (')[0]}). Exact brands, doses, and timing in order.")

            q_nutrition = ("🍽️ What to eat today",
                f"What should I eat today — {date.today().strftime('%A')}, Cycle Day {cycle_day or '?'}, {(cycle_phase or '').split(' (')[0]} phase. Give me specific meals with portions and timing for my schedule.")

            if cycle_phase and "Luteal" in cycle_phase:
                q_dynamic = ("🧘 Managing luteal phase symptoms",
                    f"I'm in Luteal phase, Day {cycle_day}. What should I specifically be doing differently this week for training, nutrition, and lifestyle to manage luteal symptoms and support progesterone?")
            elif cycle_phase and "Follicular" in cycle_phase:
                q_dynamic = ("⚡ Maximising follicular phase",
                    f"I'm in Follicular phase, Day {cycle_day}. What should I be doing differently this week to maximise the energy and anabolic advantage of this phase?")
            elif cycle_phase and "Ovulation" in cycle_phase:
                q_dynamic = ("🌸 Ovulation — what to do now",
                    f"I'm at ovulation, Day {cycle_day}. What are the most important things to do in the next 48-72 hours — training, nutrition, lifestyle, and if relevant, fertility timing?")
            else:
                q_dynamic = ("🩸 Managing menstruation",
                    f"I'm menstruating, Day {cycle_day}. What should I be doing differently this week — training modifications, nutrition priorities, and what to avoid?")

            if last_checkin and last_checkin[0].get("energy") and int(last_checkin[0]["energy"]) <= 4:
                q_energy = ("⚡ My energy is low — why?",
                    f"My last check-in showed energy at {last_checkin[0]['energy']}/10. Based on my labs and current cycle phase, what are the most likely biological reasons and what can I do today to address them?")
            else:
                q_energy = ("⚖️ Why am I not losing weight?",
                    "Based on my labs and current health picture, what are the specific biological blockers stopping me from losing weight? Be direct — what needs to change?")

            prompts = [q_supplement, q_nutrition, q_dynamic, q_energy]
            qc1, qc2 = st.columns(2)
            for i, (label, content) in enumerate(prompts):
                col = qc1 if i % 2 == 0 else qc2
                with col:
                    if st.button(label, use_container_width=True, key=f"qp_{i}"):
                        st.session_state.messages.append({"role":"user","content":content})
                        st.rerun()

        # ── Message history (capped at last 10 exchanges = 20 messages) ──────────
        MAX_HISTORY = 20
        display_messages = st.session_state.messages[-MAX_HISTORY:]
        for message in display_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # ── Controls ─────────────────────────────────────────────────────────────
        ctrl1, ctrl2 = st.columns([5,1])
        with ctrl2:
            if st.button("Clear chat", use_container_width=True, key="clear_chat"):
                st.session_state.messages = []
                st.rerun()

        # ── Chat input ────────────────────────────────────────────────────────────
        if prompt := st.chat_input(f"Ask your Sattva anything..."):
            st.session_state.messages.append({"role":"user","content":prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner(""):
                    # Send only last 10 exchanges to API to stay within token budget
                    api_messages = st.session_state.messages[-MAX_HISTORY:]
                    response = ai_client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=4096,
                        system=full_system,
                        messages=api_messages
                    )
                    reply = response.content[0].text
                    st.markdown(reply)
            st.session_state.messages.append({"role":"assistant","content":reply})

# ════════════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════════
# ONBOARDING WIZARD
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

**Extended panel — add if you have a specific concern:**
Zonulin (gut permeability) · Calprotectin · H. pylori antibody · ANA · Morning Cortisol · MTHFR · APOE

In India, Thyrocare's Aarogyam or Wellness packages cover most of the core panel at reasonable cost.
"""

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

    # Ensure onboarding row exists
    ob = get_onboarding_state(user_id)
    if not ob:
        save_onboarding_state(user_id, {"current_step": 1})
        ob = get_onboarding_state(user_id)

    profile = db_get_single("profiles", user_id)
    current_step = ob.get("current_step", 1) if ob else 1

    # ── Header ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center;padding:32px 0 24px;'>
      <div style='display:inline-flex;align-items:center;gap:10px;margin-bottom:8px;'>
        <svg width="40" height="40" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><defs><radialGradient id="osg-ob0" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#B1643A"/><stop offset="40%" stop-color="#B1643A"/><stop offset="54%" stop-color="#BE7C58" stop-opacity="0.72"/><stop offset="70%" stop-color="#D2A084" stop-opacity="0.4"/><stop offset="86%" stop-color="#E6CCB8" stop-opacity="0.14"/><stop offset="100%" stop-color="#E6CCB8" stop-opacity="0"/></radialGradient></defs><path d="M194.49 100.00 L194.46 102.97 L194.34 105.94 L194.12 108.90 L193.81 111.85 L193.40 114.79 L192.90 117.72 L192.31 120.63 L191.62 123.52 L190.84 126.39 L189.97 129.23 L189.01 132.05 L187.96 134.82 L186.81 137.57 L185.57 140.27 L184.25 142.93 L182.84 145.54 L181.34 148.10 L179.76 150.61 L178.09 153.07 L176.35 155.47 L174.53 157.81 L172.64 160.09 L170.67 162.31 L168.64 164.46 L166.55 166.55 L164.39 168.57 L162.18 170.53 L159.91 172.42 L157.58 174.24 L155.21 175.99 L152.78 177.67 L150.31 179.28 L147.79 180.81 L145.23 182.27 L142.62 183.64 L139.97 184.94 L137.28 186.16 L134.56 187.28 L131.80 188.33 L129.01 189.27 L126.19 190.13 L123.34 190.89 L120.47 191.56 L117.57 192.13 L114.67 192.60 L111.74 192.97 L108.81 193.24 L105.88 193.42 L102.94 193.51 L100.00 193.50 L97.06 193.40 L94.14 193.22 L91.21 192.95 L88.30 192.60 L85.40 192.16 L82.52 191.65 L79.64 191.07 L76.79 190.41 L73.95 189.67 L71.13 188.86 L68.33 187.98 L65.55 187.02 L62.79 185.99 L60.06 184.87 L57.36 183.68 L54.70 182.41 L52.07 181.05 L49.48 179.61 L46.94 178.08 L44.45 176.46 L42.01 174.76 L39.64 172.97 L37.33 171.09 L35.09 169.12 L32.92 167.08 L30.84 164.95 L28.84 162.74 L26.92 160.46 L25.09 158.11 L23.34 155.69 L21.69 153.22 L20.12 150.69 L18.65 148.11 L17.26 145.49 L15.96 142.82 L14.75 140.12 L13.62 137.38 L12.58 134.61 L11.62 131.82 L10.74 129.00 L9.95 126.16 L9.23 123.31 L8.60 120.43 L8.04 117.54 L7.57 114.64 L7.19 111.73 L6.88 108.80 L6.66 105.87 L6.53 102.94 L6.49 100.00 L6.53 97.06 L6.67 94.13 L6.89 91.20 L7.21 88.28 L7.61 85.37 L8.11 82.47 L8.70 79.59 L9.37 76.73 L10.14 73.89 L10.99 71.08 L11.93 68.29 L12.95 65.53 L14.05 62.81 L15.24 60.11 L16.50 57.46 L17.85 54.84 L19.27 52.26 L20.77 49.72 L22.35 47.23 L24.00 44.78 L25.73 42.39 L27.53 40.05 L29.41 37.76 L31.36 35.54 L33.38 33.38 L35.47 31.29 L37.64 29.26 L39.87 27.31 L42.16 25.44 L44.52 23.64 L46.94 21.92 L49.41 20.29 L51.94 18.74 L54.52 17.27 L57.15 15.90 L59.82 14.60 L62.52 13.40 L65.27 12.28 L68.04 11.24 L70.85 10.29 L73.69 9.43 L76.54 8.64 L79.42 7.95 L82.32 7.34 L85.24 6.81 L88.17 6.37 L91.12 6.02 L94.07 5.75 L97.03 5.58 L100.00 5.50 L102.97 5.52 L105.94 5.63 L108.90 5.84 L111.85 6.16 L114.80 6.58 L117.72 7.10 L120.62 7.73 L123.50 8.47 L126.35 9.31 L129.16 10.25 L131.94 11.29 L134.67 12.43 L137.36 13.67 L140.00 15.00 L142.59 16.41 L145.13 17.91 L147.62 19.48 L150.05 21.13 L152.43 22.84 L154.76 24.62 L157.04 26.46 L159.26 28.36 L161.44 30.31 L163.56 32.32 L165.63 34.37 L167.65 36.48 L169.61 38.63 L171.52 40.83 L173.38 43.08 L175.18 45.38 L176.93 47.72 L178.61 50.12 L180.22 52.56 L181.76 55.05 L183.23 57.59 L184.63 60.18 L185.94 62.81 L187.17 65.49 L188.31 68.21 L189.36 70.97 L190.31 73.76 L191.17 76.59 L191.93 79.45 L192.59 82.34 L193.16 85.25 L193.62 88.17 L193.99 91.12 L194.25 94.07 L194.42 97.03 L194.49 100.00 Z" fill="none" stroke="#111214" stroke-width="1.3"/><path d="M183.80 100.00 L183.77 102.63 L183.66 105.26 L183.45 107.89 L183.17 110.51 L182.80 113.11 L182.34 115.71 L181.80 118.29 L181.18 120.84 L180.48 123.38 L179.69 125.89 L178.82 128.38 L177.87 130.83 L176.84 133.25 L175.73 135.64 L174.54 137.98 L173.28 140.29 L171.94 142.54 L170.52 144.76 L169.04 146.92 L167.48 149.03 L165.86 151.09 L164.18 153.09 L162.43 155.04 L160.63 156.93 L158.77 158.77 L156.86 160.55 L154.90 162.27 L152.89 163.93 L150.83 165.53 L148.73 167.07 L146.59 168.55 L144.40 169.97 L142.18 171.32 L139.91 172.61 L137.62 173.82 L135.28 174.97 L132.91 176.05 L130.51 177.06 L128.08 177.98 L125.61 178.83 L123.13 179.60 L120.61 180.29 L118.08 180.89 L115.53 181.41 L112.96 181.84 L110.38 182.19 L107.79 182.46 L105.20 182.64 L102.60 182.73 L100.00 182.75 L97.40 182.68 L94.81 182.54 L92.22 182.33 L89.64 182.04 L87.06 181.68 L84.50 181.25 L81.95 180.75 L79.41 180.18 L76.89 179.55 L74.38 178.85 L71.89 178.08 L69.42 177.25 L66.96 176.34 L64.54 175.37 L62.13 174.32 L59.76 173.20 L57.42 172.00 L55.12 170.72 L52.86 169.37 L50.64 167.93 L48.48 166.42 L46.37 164.83 L44.32 163.16 L42.33 161.41 L40.42 159.58 L38.57 157.69 L36.80 155.72 L35.10 153.69 L33.49 151.59 L31.95 149.44 L30.49 147.24 L29.12 144.98 L27.82 142.69 L26.61 140.35 L25.47 137.97 L24.41 135.57 L23.43 133.13 L22.53 130.67 L21.70 128.19 L20.94 125.69 L20.25 123.17 L19.64 120.63 L19.09 118.08 L18.62 115.52 L18.23 112.95 L17.90 110.37 L17.65 107.78 L17.47 105.19 L17.37 102.60 L17.34 100.00 L17.40 97.40 L17.53 94.81 L17.73 92.22 L18.02 89.64 L18.39 87.07 L18.83 84.52 L19.35 81.97 L19.95 79.45 L20.63 76.94 L21.38 74.45 L22.21 71.99 L23.10 69.55 L24.08 67.14 L25.12 64.76 L26.23 62.41 L27.41 60.09 L28.66 57.81 L29.98 55.56 L31.36 53.35 L32.81 51.19 L34.33 49.06 L35.92 46.99 L37.57 44.96 L39.29 42.99 L41.07 41.07 L42.91 39.20 L44.82 37.41 L46.78 35.67 L48.81 34.00 L50.89 32.40 L53.02 30.87 L55.21 29.42 L57.44 28.04 L59.72 26.74 L62.04 25.51 L64.41 24.36 L66.80 23.28 L69.23 22.29 L71.69 21.37 L74.18 20.52 L76.69 19.75 L79.22 19.06 L81.77 18.44 L84.34 17.90 L86.92 17.44 L89.52 17.05 L92.13 16.74 L94.75 16.51 L97.37 16.36 L100.00 16.29 L102.63 16.31 L105.26 16.41 L107.88 16.61 L110.50 16.89 L113.10 17.27 L115.69 17.74 L118.26 18.30 L120.81 18.95 L123.33 19.70 L125.82 20.54 L128.27 21.46 L130.69 22.48 L133.07 23.57 L135.41 24.75 L137.70 26.00 L139.95 27.33 L142.15 28.72 L144.31 30.18 L146.42 31.69 L148.48 33.27 L150.50 34.89 L152.47 36.57 L154.40 38.29 L156.28 40.06 L158.12 41.88 L159.91 43.74 L161.66 45.64 L163.36 47.58 L165.01 49.57 L166.62 51.60 L168.17 53.67 L169.66 55.79 L171.10 57.95 L172.48 60.16 L173.79 62.40 L175.03 64.69 L176.20 67.03 L177.30 69.40 L178.31 71.81 L179.25 74.25 L180.10 76.73 L180.87 79.24 L181.54 81.77 L182.13 84.33 L182.64 86.91 L183.05 89.51 L183.37 92.12 L183.60 94.74 L183.75 97.37 L183.80 100.00 Z" fill="none" stroke="#111214" stroke-width="1.3"/><path d="M170.96 100.00 L170.92 102.23 L170.80 104.45 L170.61 106.67 L170.35 108.89 L170.03 111.09 L169.63 113.28 L169.16 115.46 L168.63 117.62 L168.02 119.76 L167.35 121.88 L166.61 123.98 L165.81 126.06 L164.94 128.10 L164.00 130.12 L163.00 132.10 L161.94 134.05 L160.81 135.96 L159.62 137.84 L158.38 139.67 L157.08 141.47 L155.72 143.22 L154.31 144.93 L152.84 146.59 L151.33 148.21 L149.77 149.77 L148.17 151.30 L146.52 152.77 L144.84 154.20 L143.11 155.57 L141.34 156.90 L139.53 158.17 L137.69 159.39 L135.81 160.55 L133.90 161.66 L131.95 162.71 L129.97 163.70 L127.96 164.62 L125.93 165.48 L123.86 166.28 L121.77 167.00 L119.65 167.65 L117.52 168.23 L115.36 168.73 L113.19 169.16 L111.01 169.52 L108.82 169.79 L106.62 170.00 L104.41 170.13 L102.21 170.18 L100.00 170.17 L97.80 170.09 L95.60 169.94 L93.41 169.73 L91.23 169.45 L89.05 169.12 L86.89 168.73 L84.74 168.28 L82.60 167.78 L80.47 167.22 L78.36 166.61 L76.26 165.95 L74.17 165.23 L72.11 164.46 L70.06 163.63 L68.03 162.74 L66.03 161.79 L64.05 160.78 L62.11 159.71 L60.19 158.57 L58.32 157.37 L56.48 156.10 L54.69 154.77 L52.95 153.37 L51.26 151.91 L49.62 150.38 L48.04 148.79 L46.53 147.14 L45.07 145.44 L43.69 143.68 L42.37 141.87 L41.12 140.02 L39.93 138.12 L38.82 136.18 L37.77 134.21 L36.79 132.21 L35.87 130.18 L35.02 128.12 L34.24 126.04 L33.52 123.93 L32.87 121.81 L32.28 119.68 L31.75 117.52 L31.28 115.36 L30.88 113.19 L30.54 111.00 L30.26 108.81 L30.06 106.61 L29.91 104.41 L29.83 102.21 L29.82 100.00 L29.88 97.80 L30.00 95.60 L30.20 93.40 L30.46 91.21 L30.78 89.04 L31.18 86.87 L31.64 84.72 L32.17 82.58 L32.76 80.47 L33.42 78.37 L34.13 76.29 L34.91 74.23 L35.75 72.20 L36.65 70.19 L37.60 68.20 L38.61 66.25 L39.67 64.32 L40.79 62.43 L41.97 60.56 L43.20 58.73 L44.49 56.94 L45.83 55.18 L47.22 53.47 L48.67 51.80 L50.17 50.17 L51.72 48.59 L53.33 47.06 L54.99 45.59 L56.69 44.17 L58.45 42.81 L60.25 41.50 L62.09 40.26 L63.98 39.09 L65.90 37.97 L67.86 36.92 L69.86 35.94 L71.88 35.02 L73.93 34.17 L76.01 33.38 L78.12 32.66 L80.24 32.00 L82.39 31.40 L84.55 30.87 L86.73 30.41 L88.91 30.01 L91.12 29.68 L93.33 29.41 L95.55 29.22 L97.77 29.09 L100.00 29.03 L102.23 29.05 L104.46 29.14 L106.68 29.31 L108.90 29.56 L111.11 29.88 L113.30 30.28 L115.48 30.76 L117.63 31.32 L119.77 31.96 L121.87 32.68 L123.95 33.47 L126.00 34.33 L128.01 35.27 L129.99 36.27 L131.93 37.34 L133.83 38.46 L135.69 39.64 L137.52 40.88 L139.30 42.16 L141.05 43.50 L142.76 44.87 L144.43 46.29 L146.07 47.75 L147.66 49.24 L149.23 50.77 L150.75 52.34 L152.24 53.95 L153.68 55.59 L155.09 57.27 L156.46 58.98 L157.78 60.73 L159.06 62.52 L160.28 64.35 L161.46 66.21 L162.57 68.12 L163.63 70.06 L164.63 72.03 L165.56 74.04 L166.42 76.09 L167.21 78.16 L167.93 80.26 L168.57 82.39 L169.14 84.55 L169.63 86.72 L170.04 88.91 L170.38 91.11 L170.64 93.32 L170.82 95.54 L170.93 97.77 L170.96 100.00 Z" fill="none" stroke="#111214" stroke-width="1.3"/><path d="M161.03 100.00 L160.99 101.92 L160.89 103.83 L160.74 105.74 L160.52 107.65 L160.25 109.54 L159.93 111.43 L159.54 113.31 L159.10 115.17 L158.60 117.03 L158.05 118.86 L157.44 120.68 L156.77 122.48 L156.04 124.25 L155.25 126.00 L154.41 127.72 L153.50 129.41 L152.55 131.08 L151.53 132.70 L150.46 134.29 L149.34 135.85 L148.17 137.36 L146.94 138.83 L145.67 140.26 L144.36 141.65 L143.00 143.00 L141.60 144.30 L140.16 145.55 L138.68 146.76 L137.17 147.92 L135.63 149.04 L134.05 150.11 L132.45 151.13 L130.81 152.10 L129.15 153.03 L127.46 153.90 L125.75 154.72 L124.01 155.49 L122.25 156.20 L120.47 156.86 L118.67 157.46 L116.85 158.00 L115.02 158.49 L113.17 158.91 L111.31 159.27 L109.44 159.57 L107.56 159.81 L105.67 159.99 L103.78 160.11 L101.89 160.18 L100.00 160.18 L98.11 160.14 L96.22 160.03 L94.34 159.88 L92.46 159.68 L90.59 159.42 L88.72 159.12 L86.86 158.78 L85.01 158.38 L83.17 157.94 L81.33 157.45 L79.51 156.92 L77.70 156.33 L75.90 155.69 L74.12 155.00 L72.36 154.26 L70.61 153.46 L68.89 152.60 L67.20 151.68 L65.55 150.70 L63.92 149.66 L62.34 148.56 L60.79 147.39 L59.30 146.17 L57.85 144.88 L56.46 143.54 L55.12 142.15 L53.83 140.70 L52.61 139.20 L51.44 137.66 L50.34 136.08 L49.29 134.46 L48.31 132.80 L47.38 131.12 L46.51 129.41 L45.69 127.67 L44.93 125.91 L44.22 124.14 L43.57 122.34 L42.96 120.54 L42.40 118.71 L41.89 116.88 L41.43 115.04 L41.02 113.18 L40.66 111.32 L40.35 109.45 L40.10 107.57 L39.89 105.68 L39.74 103.79 L39.65 101.90 L39.61 100.00 L39.63 98.10 L39.72 96.21 L39.86 94.32 L40.06 92.43 L40.33 90.55 L40.66 88.68 L41.05 86.82 L41.50 84.98 L42.01 83.15 L42.57 81.34 L43.20 79.55 L43.88 77.78 L44.61 76.03 L45.39 74.30 L46.22 72.60 L47.11 70.92 L48.04 69.27 L49.02 67.64 L50.04 66.05 L51.11 64.48 L52.23 62.94 L53.39 61.44 L54.60 59.97 L55.85 58.54 L57.14 57.14 L58.48 55.79 L59.86 54.47 L61.29 53.21 L62.75 51.98 L64.26 50.81 L65.81 49.69 L67.39 48.61 L69.01 47.59 L70.66 46.63 L72.34 45.72 L74.05 44.86 L75.79 44.06 L77.56 43.31 L79.34 42.62 L81.15 41.99 L82.98 41.41 L84.82 40.88 L86.68 40.42 L88.56 40.00 L90.44 39.65 L92.34 39.35 L94.24 39.11 L96.16 38.94 L98.08 38.82 L100.00 38.77 L101.92 38.78 L103.85 38.86 L105.77 39.00 L107.68 39.22 L109.58 39.50 L111.47 39.86 L113.35 40.28 L115.21 40.78 L117.04 41.35 L118.85 41.98 L120.64 42.68 L122.39 43.44 L124.12 44.26 L125.82 45.14 L127.48 46.07 L129.11 47.06 L130.70 48.09 L132.26 49.16 L133.79 50.28 L135.29 51.43 L136.75 52.62 L138.19 53.84 L139.59 55.09 L140.97 56.38 L142.31 57.69 L143.63 59.03 L144.91 60.41 L146.16 61.81 L147.38 63.25 L148.57 64.71 L149.72 66.21 L150.82 67.75 L151.89 69.31 L152.91 70.91 L153.88 72.55 L154.79 74.22 L155.65 75.92 L156.46 77.65 L157.20 79.41 L157.88 81.20 L158.49 83.01 L159.04 84.84 L159.52 86.70 L159.93 88.57 L160.27 90.45 L160.55 92.35 L160.77 94.26 L160.92 96.17 L161.00 98.08 L161.03 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><path d="M150.19 100.00 L150.18 101.58 L150.13 103.15 L150.03 104.73 L149.88 106.30 L149.68 107.87 L149.43 109.43 L149.13 110.98 L148.78 112.52 L148.38 114.06 L147.93 115.57 L147.42 117.07 L146.86 118.56 L146.25 120.02 L145.59 121.45 L144.88 122.87 L144.11 124.25 L143.29 125.60 L142.43 126.93 L141.52 128.22 L140.57 129.48 L139.58 130.70 L138.55 131.89 L137.48 133.04 L136.38 134.16 L135.25 135.25 L134.08 136.30 L132.90 137.31 L131.68 138.30 L130.44 139.25 L129.18 140.17 L127.90 141.05 L126.59 141.91 L125.27 142.72 L123.92 143.51 L122.55 144.25 L121.16 144.96 L119.74 145.62 L118.31 146.25 L116.86 146.83 L115.39 147.35 L113.90 147.83 L112.39 148.26 L110.87 148.63 L109.34 148.95 L107.79 149.21 L106.24 149.42 L104.69 149.57 L103.12 149.66 L101.56 149.70 L100.00 149.68 L98.44 149.61 L96.89 149.50 L95.34 149.33 L93.79 149.13 L92.26 148.88 L90.73 148.59 L89.21 148.27 L87.70 147.91 L86.20 147.51 L84.70 147.09 L83.21 146.62 L81.74 146.13 L80.27 145.60 L78.81 145.03 L77.37 144.42 L75.93 143.78 L74.52 143.09 L73.12 142.36 L71.74 141.58 L70.39 140.76 L69.07 139.88 L67.77 138.96 L66.52 137.98 L65.30 136.96 L64.12 135.88 L62.99 134.76 L61.91 133.58 L60.87 132.37 L59.89 131.11 L58.96 129.81 L58.09 128.48 L57.27 127.12 L56.51 125.72 L55.80 124.30 L55.14 122.86 L54.53 121.40 L53.97 119.92 L53.45 118.43 L52.99 116.93 L52.56 115.41 L52.18 113.89 L51.84 112.37 L51.54 110.83 L51.28 109.29 L51.05 107.75 L50.87 106.21 L50.72 104.66 L50.62 103.11 L50.55 101.55 L50.53 100.00 L50.54 98.45 L50.61 96.89 L50.71 95.34 L50.87 93.79 L51.07 92.25 L51.31 90.71 L51.61 89.18 L51.95 87.66 L52.34 86.15 L52.78 84.66 L53.26 83.17 L53.80 81.71 L54.38 80.26 L55.00 78.83 L55.67 77.41 L56.39 76.03 L57.15 74.66 L57.95 73.32 L58.80 72.00 L59.68 70.71 L60.61 69.45 L61.58 68.21 L62.58 67.01 L63.62 65.84 L64.70 64.70 L65.82 63.60 L66.97 62.53 L68.15 61.50 L69.37 60.51 L70.62 59.56 L71.90 58.65 L73.20 57.78 L74.54 56.95 L75.90 56.16 L77.28 55.41 L78.69 54.71 L80.12 54.05 L81.56 53.43 L83.03 52.86 L84.51 52.33 L86.01 51.84 L87.52 51.40 L89.05 51.01 L90.59 50.66 L92.14 50.35 L93.70 50.10 L95.26 49.89 L96.84 49.74 L98.42 49.64 L100.00 49.59 L101.58 49.60 L103.17 49.66 L104.75 49.78 L106.32 49.96 L107.89 50.20 L109.44 50.50 L110.99 50.85 L112.51 51.27 L114.02 51.74 L115.51 52.26 L116.98 52.84 L118.42 53.47 L119.84 54.15 L121.23 54.88 L122.60 55.65 L123.94 56.45 L125.25 57.30 L126.54 58.18 L127.80 59.10 L129.03 60.04 L130.24 61.01 L131.42 62.02 L132.58 63.04 L133.71 64.10 L134.82 65.18 L135.90 66.28 L136.96 67.41 L137.99 68.57 L138.99 69.76 L139.96 70.97 L140.90 72.21 L141.80 73.47 L142.66 74.77 L143.49 76.09 L144.28 77.44 L145.02 78.82 L145.71 80.22 L146.36 81.64 L146.96 83.09 L147.51 84.56 L148.01 86.05 L148.45 87.56 L148.85 89.08 L149.19 90.62 L149.48 92.16 L149.72 93.72 L149.91 95.28 L150.05 96.85 L150.15 98.42 L150.19 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><path d="M139.49 100.00 L139.50 101.24 L139.47 102.48 L139.39 103.72 L139.27 104.96 L139.10 106.19 L138.89 107.42 L138.64 108.64 L138.34 109.84 L138.00 111.04 L137.62 112.22 L137.19 113.39 L136.73 114.54 L136.22 115.67 L135.68 116.79 L135.10 117.88 L134.49 118.96 L133.84 120.01 L133.16 121.04 L132.45 122.05 L131.71 123.04 L130.95 124.00 L130.16 124.95 L129.34 125.87 L128.50 126.76 L127.63 127.63 L126.75 128.48 L125.83 129.30 L124.90 130.10 L123.95 130.87 L122.97 131.61 L121.97 132.32 L120.95 133.01 L119.90 133.65 L118.84 134.27 L117.75 134.85 L116.65 135.39 L115.53 135.89 L114.39 136.35 L113.24 136.77 L112.07 137.15 L110.89 137.49 L109.70 137.79 L108.50 138.04 L107.30 138.26 L106.09 138.43 L104.87 138.57 L103.66 138.67 L102.44 138.73 L101.22 138.76 L100.00 138.75 L98.78 138.72 L97.57 138.65 L96.36 138.55 L95.15 138.42 L93.94 138.27 L92.74 138.08 L91.54 137.87 L90.34 137.62 L89.15 137.35 L87.96 137.05 L86.78 136.71 L85.61 136.34 L84.45 135.93 L83.30 135.49 L82.16 135.01 L81.04 134.50 L79.93 133.94 L78.84 133.34 L77.77 132.71 L76.73 132.03 L75.71 131.32 L74.71 130.57 L73.75 129.78 L72.82 128.95 L71.91 128.09 L71.05 127.19 L70.21 126.26 L69.41 125.30 L68.65 124.32 L67.93 123.30 L67.24 122.27 L66.58 121.21 L65.97 120.13 L65.39 119.03 L64.85 117.91 L64.34 116.78 L63.87 115.63 L63.44 114.47 L63.05 113.30 L62.69 112.12 L62.37 110.93 L62.09 109.73 L61.84 108.53 L61.64 107.32 L61.47 106.10 L61.33 104.88 L61.23 103.66 L61.17 102.44 L61.15 101.22 L61.16 100.00 L61.21 98.78 L61.29 97.56 L61.40 96.35 L61.55 95.14 L61.73 93.94 L61.95 92.74 L62.19 91.55 L62.47 90.36 L62.78 89.19 L63.12 88.02 L63.49 86.86 L63.89 85.70 L64.33 84.56 L64.80 83.44 L65.30 82.32 L65.84 81.22 L66.41 80.14 L67.02 79.07 L67.66 78.02 L68.34 77.00 L69.05 75.99 L69.80 75.02 L70.58 74.06 L71.40 73.14 L72.24 72.24 L73.12 71.38 L74.03 70.55 L74.97 69.74 L75.93 68.98 L76.92 68.24 L77.94 67.54 L78.97 66.87 L80.03 66.23 L81.10 65.62 L82.19 65.05 L83.30 64.51 L84.42 64.00 L85.56 63.52 L86.70 63.07 L87.87 62.65 L89.04 62.27 L90.22 61.92 L91.42 61.60 L92.62 61.31 L93.83 61.07 L95.05 60.85 L96.28 60.68 L97.52 60.55 L98.76 60.46 L100.00 60.42 L101.24 60.42 L102.49 60.47 L103.73 60.56 L104.96 60.71 L106.19 60.90 L107.41 61.14 L108.62 61.42 L109.82 61.75 L111.00 62.13 L112.17 62.55 L113.32 63.01 L114.45 63.51 L115.56 64.04 L116.65 64.61 L117.72 65.22 L118.77 65.85 L119.80 66.52 L120.81 67.21 L121.80 67.92 L122.77 68.66 L123.72 69.43 L124.64 70.21 L125.55 71.02 L126.44 71.85 L127.30 72.70 L128.15 73.57 L128.97 74.46 L129.77 75.37 L130.55 76.31 L131.30 77.26 L132.02 78.24 L132.72 79.23 L133.39 80.25 L134.03 81.29 L134.64 82.35 L135.22 83.43 L135.76 84.52 L136.27 85.64 L136.75 86.77 L137.19 87.92 L137.59 89.08 L137.96 90.25 L138.29 91.44 L138.58 92.64 L138.83 93.85 L139.05 95.07 L139.22 96.29 L139.35 97.52 L139.44 98.76 L139.49 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><circle cx="100" cy="100" r="31.3" fill="url(#osg-ob0)"/></svg>
        <span style="font-family:Newsreader,serif;font-weight:400;font-style:normal;font-size:1.6rem;color:#111214;letter-spacing:-0.02em;">
          OneSattva
        </span>
      </div>
      <p style="font-family:Newsreader,serif;font-style:italic;color:#B6744A;font-size:0.9rem;margin:0;">Health, understood.</p>
      <p style="font-family:Inter,sans-serif;font-size:0.95rem;color:#6B6864;margin-top:12px;">Let's build your health profile — takes about 5 minutes.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Step progress bar ────────────────────────────────────────────────────────
    steps = ["Basic Info", "Health Profile", "Lifestyle & Goals", "Lab Reports", "Ready"]
    done_steps = sum([
        ob.get("step1_done", False),
        ob.get("step2_done", False),
        ob.get("step3_done", False),
        ob.get("step4_done", False),
    ]) if ob else 0
    progress_pct = int((done_steps / 4) * 100)

    step_html = "<div style='display:flex;gap:6px;margin-bottom:8px;'>"
    for i, s in enumerate(steps):
        is_done = (i + 1) < current_step
        is_current = (i + 1) == current_step
        bg = "#111214" if is_done else ("#B6744A" if is_current else "#E8E8E4")
        color = "#F7F5F2" if (is_done or is_current) else "#9B9B92"
        step_html += f"<div style='flex:1;text-align:center;background:{bg};color:{color};border-radius:8px;padding:8px 4px;font-family:Inter,sans-serif;font-size:11px;font-weight:500;'>{s}</div>"
    step_html += "</div>"
    st.markdown(step_html, unsafe_allow_html=True)
    st.progress(max(progress_pct, 5))
    st.caption(f"Step {current_step} of 5 · {progress_pct}% complete")
    st.divider()

    col_main, col_r = st.columns([2, 1])
    with col_main:

        # ── STEP 1 — Basic Info ─────────────────────────────────────────────────
        if current_step == 1:
            st.markdown("### Your basic information")
            st.caption("This helps us personalise every recommendation from day one.")
            with st.form("ob_step1"):
                c1, c2 = st.columns(2)
                with c1:
                    p_name = st.text_input("Full name *", value=profile.get("full_name","") if profile else "")
                    p_dob = st.date_input("Date of birth *",
                        value=date.fromisoformat(profile["date_of_birth"]) if profile and profile.get("date_of_birth") else date(1990, 1, 1),
                        min_value=date(1940,1,1), max_value=date.today())
                    p_sex = st.selectbox("Sex assigned at birth *", ["","Female","Male","Intersex"],
                        index=["","Female","Male","Intersex"].index(profile.get("sex","")) if profile and profile.get("sex") in ["Female","Male","Intersex"] else 0)
                    p_blood = st.selectbox("Blood group", ["","A+","A-","B+","B-","O+","O-","AB+","AB-"],
                        index=["","A+","A-","B+","B-","O+","O-","AB+","AB-"].index(profile.get("blood_group","")) if profile and profile.get("blood_group","") in ["A+","A-","B+","B-","O+","O-","AB+","AB-"] else 0)
                with c2:
                    p_height = st.number_input("Height (cm) *", 100, 220, value=int(profile.get("height_cm",165)) if profile and profile.get("height_cm") else 165)
                    p_weight = st.number_input("Weight (kg) *", 30, 200, value=int(profile.get("weight_kg",60)) if profile and profile.get("weight_kg") else 60)
                    p_location = st.text_input("City / Location *", value=profile.get("location","") if profile else "")
                    p_diet = st.selectbox("Diet *", ["Vegetarian (no eggs)","Vegetarian (with eggs)","Non-vegetarian","Vegan","Pescatarian"],
                        index=0)

                st.markdown("**Lifestyle factors**")
                lc1, lc2, lc3 = st.columns(3)
                with lc1:
                    p_alcohol = st.selectbox("Alcohol", ["None","Occasional","Weekly","Daily"])
                with lc2:
                    p_smoking = st.selectbox("Smoking / Vaping", ["None","Occasional","Daily"])
                with lc3:
                    p_allergies = st.text_input("Known allergies", placeholder="e.g. gluten, nuts")

                submitted1 = st.form_submit_button("Save & Continue →", type="primary", use_container_width=True)
                if submitted1:
                    if not p_name or not p_sex or not p_location:
                        st.error("Please fill in all required fields (marked with *)")
                    else:
                        age = (date.today() - p_dob).days // 365
                        db_upsert("profiles", {
                            "id": user_id, "full_name": p_name,
                            "age": age, "date_of_birth": p_dob.isoformat(),
                            "sex": p_sex, "height_cm": p_height,
                            "weight_kg": p_weight, "location": p_location,
                            "diet": p_diet, "blood_group": p_blood,
                            "alcohol": p_alcohol, "smoking": p_smoking,
                            "allergies": p_allergies
                        })
                        save_onboarding_state(user_id, {"current_step": 2, "step1_done": True})
                        st.rerun()

        # ── STEP 2 — Health Profile ──────────────────────────────────────────────
        elif current_step == 2:
            st.markdown("### Your health profile")
            st.caption("Medical history and current medications. Share what you're comfortable with — more context means better recommendations.")

            st.markdown("##### 🩺 Medical conditions & challenges")
            conditions = db_get("medical_history", user_id)
            for c in conditions:
                cc1, cc2 = st.columns([5,1])
                cc1.write(f"**{c['condition']}** — {c.get('notes','')[:60]}")
                if cc2.button("✕", key=f"del_cond_ob_{c['id']}"):
                    db_delete("medical_history", c["id"])
                    st.rerun()

            with st.form("add_cond_ob"):
                nc1, nc2 = st.columns([3,2])
                with nc1:
                    new_cond = st.text_input("Add a condition or known challenge", placeholder="e.g. Hypothyroidism, PCOS, IBS")
                with nc2:
                    new_cond_notes = st.text_input("Notes", placeholder="e.g. diagnosed 2020")
                if st.form_submit_button("+ Add", use_container_width=True) and new_cond:
                    db_upsert("medical_history", {"user_id": user_id, "condition": new_cond, "notes": new_cond_notes})
                    st.rerun()

            st.divider()
            st.markdown("##### 💊 Current medications")
            meds = db_get("medications", user_id)
            for m in meds:
                mc1, mc2 = st.columns([5,1])
                mc1.write(f"**{m['name']}** — {m.get('dose','')} {m.get('frequency','')}")
                if mc2.button("✕", key=f"del_med_ob_{m['id']}"):
                    db_delete("medications", m["id"])
                    st.rerun()

            with st.form("add_med_ob"):
                mm1, mm2, mm3 = st.columns(3)
                with mm1:
                    new_med = st.text_input("Medication name", placeholder="e.g. Thyronorm")
                with mm2:
                    new_dose = st.text_input("Dose", placeholder="e.g. 50mcg")
                with mm3:
                    new_freq = st.text_input("Frequency", placeholder="e.g. Daily on waking")
                if st.form_submit_button("+ Add medication", use_container_width=True) and new_med:
                    db_upsert("medications", {"user_id": user_id, "name": new_med, "dose": new_dose, "frequency": new_freq, "active": True})
                    st.rerun()

            st.divider()
            st.markdown("##### 🌿 Current supplements")
            supps = db_get("supplements", user_id)
            for s in supps:
                sc1, sc2 = st.columns([5,1])
                sc1.write(f"**{s['name']}** — {s.get('dose','')} ({s.get('timing','')})")
                if sc2.button("✕", key=f"del_supp_ob_{s['id']}"):
                    db_delete("supplements", s["id"])
                    st.rerun()

            with st.form("add_supp_ob"):
                ss1, ss2, ss3 = st.columns(3)
                with ss1:
                    new_supp = st.text_input("Supplement name", placeholder="e.g. Magnesium Glycinate")
                with ss2:
                    new_supp_dose = st.text_input("Dose", placeholder="e.g. 400mg")
                with ss3:
                    new_supp_timing = st.text_input("Timing", placeholder="e.g. Before bed")
                if st.form_submit_button("+ Add supplement", use_container_width=True) and new_supp:
                    db_upsert("supplements", {"user_id": user_id, "name": new_supp, "dose": new_supp_dose, "timing": new_supp_timing, "active": True})
                    st.rerun()

            st.divider()
            nav1, nav2 = st.columns(2)
            with nav1:
                if st.button("← Back", use_container_width=True):
                    save_onboarding_state(user_id, {"current_step": 1})
                    st.rerun()
            with nav2:
                if st.button("Save & Continue →", type="primary", use_container_width=True):
                    save_onboarding_state(user_id, {"current_step": 3, "step2_done": True})
                    st.rerun()

        # ── STEP 3 — Lifestyle & Goals ───────────────────────────────────────────
        elif current_step == 3:
            st.markdown("### Your lifestyle & goals")
            st.caption("Daily routine, sleep, exercise, and what you want to achieve.")

            with st.form("ob_step3"):
                st.markdown("##### ⏰ Daily schedule")
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    wake_time = st.text_input("Wake time", value=profile.get("wake_time","7:00 AM") if profile and profile.get("wake_time") else "7:00 AM")
                with sc2:
                    first_meal = st.text_input("First meal time", placeholder="e.g. 9:00 AM")
                with sc3:
                    sleep_time = st.text_input("Bedtime target", value=profile.get("sleep_time","10:30 PM") if profile and profile.get("sleep_time") else "10:30 PM")

                st.markdown("##### 🏋️ Exercise routine")
                ex1, ex2 = st.columns(2)
                with ex1:
                    workout_freq = st.selectbox("How often do you exercise?", ["Not currently","1-2x per week","3-4x per week","5+ per week"])
                    workout_types = st.multiselect("Types of exercise", ["Strength training","Cardio","Yoga/Pilates","Swimming","Cycling","Team sports","Walking","Other"])
                with ex2:
                    workout_time = st.text_input("Preferred workout time", placeholder="e.g. 7:00 AM or 6:00 PM")
                    sleep_hours = st.number_input("Average sleep hours", 3.0, 12.0, 7.0, step=0.5)

                st.markdown("##### 🎯 Your goals")
                st.caption("Add goals with a timeframe — your roadmap and protocols will be built around these.")

            goals_list = db_get("goals", user_id)
            for g in goals_list:
                gc1, gc2 = st.columns([5,1])
                gc1.write(f"**{g['goal']}** — {g.get('timeframe','')}")
                if gc2.button("✕", key=f"del_goal_ob_{g['id']}"):
                    db_delete("goals", g["id"])
                    st.rerun()

            with st.form("add_goal_ob"):
                gg1, gg2 = st.columns([3,1])
                with gg1:
                    new_goal = st.text_input("Add a goal", placeholder="e.g. Resolve bloating and digestive issues")
                with gg2:
                    new_timeframe = st.selectbox("Timeframe", ["3 months","6 months","12 months","12 months+"])
                if st.form_submit_button("+ Add goal", use_container_width=True) and new_goal:
                    db_upsert("goals", {"user_id": user_id, "goal": new_goal, "timeframe": new_timeframe})
                    st.rerun()

            st.markdown("##### 🔄 Cycle tracking (for females)")
            ob_cd = db_get_single("cycle_data", user_id)
            with st.form("cycle_ob_form"):
                cyc1, cyc2 = st.columns(2)
                with cyc1:
                    default_date = date.fromisoformat(ob_cd["last_period_start"]) if ob_cd and ob_cd.get("last_period_start") else date.today()
                    lp_date = st.date_input("Last period start date", value=default_date)
                with cyc2:
                    avg_len = st.number_input("Average cycle length (days)", 21, 40, value=ob_cd.get("avg_cycle_length",28) if ob_cd else 28)
                if st.form_submit_button("Save cycle data", use_container_width=True):
                    db_upsert("cycle_data", {"user_id": user_id, "last_period_start": lp_date.isoformat(), "avg_cycle_length": int(avg_len)})
                    st.success("Saved!")

            st.divider()
            nav1, nav2 = st.columns(2)
            with nav1:
                if st.button("← Back", use_container_width=True, key="back3"):
                    save_onboarding_state(user_id, {"current_step": 2})
                    st.rerun()
            with nav2:
                if st.button("Save & Continue →", type="primary", use_container_width=True, key="next3"):
                    notes_val = f"Wake: {wake_time} | First meal: {first_meal} | Sleep: {sleep_time} | Exercise: {workout_freq} {', '.join(workout_types)} at {workout_time} | Sleep hrs: {sleep_hours}"
                    db_upsert("profiles", {"id": user_id, "wake_time": wake_time, "sleep_time": sleep_time})
                    db_upsert("profile_notes", {"user_id": user_id, "notes": notes_val})
                    save_onboarding_state(user_id, {"current_step": 4, "step3_done": True})
                    st.rerun()

        # ── STEP 4 — Lab Reports ─────────────────────────────────────────────────
        elif current_step == 4:
            st.markdown("### Lab reports")
            st.info("Lab reports are the foundation of your treatment roadmap. Without them, recommendations will be generic. Upload what you have — even a partial report helps.")

            with st.expander("📋 What to get tested — recommended markers", expanded=False):
                st.markdown(MARKERS_INFO)

            existing_labs = db_get("lab_reports", user_id, order_col="report_date")
            if existing_labs:
                st.success(f"✅ {len(existing_labs)} lab report(s) uploaded. You can add more or continue.")
                for lab in existing_labs:
                    st.markdown(f"- **{lab['report_date']}** — {lab.get('lab_name','')} · {lab.get('summary','')[:80]}")

            st.divider()
            st.markdown("##### Upload a lab report")
            report_date_ob = st.date_input("Report date", value=date.today(), key="ob_lab_date")
            lab_name_ob = st.text_input("Lab name", placeholder="e.g. Thyrocare, SRL, Apollo", key="ob_lab_name")
            raw_values_ob = st.text_area("Paste your lab values here", height=200, key="ob_lab_values",
                placeholder="TSH: 2.1\nFT3: 2.8\nFT4: 1.2\nProlactin: 18.5\nFerritin: 42\nVitamin D: 38\n...")

            if st.button("🔍 Analyse & Save Report", type="primary", use_container_width=True):
                if raw_values_ob.strip():
                    with st.spinner("Analysing your labs against functional medicine ranges..."):
                        analysis_prompt = f"""New lab report — date: {report_date_ob.isoformat()}, lab: {lab_name_ob}

VALUES:
{raw_values_ob}

Analyse against functional medicine optimal ranges (not just conventional). Structure as:

## Key Findings
Table: Marker | Value | Functional Status | Priority

## What This Tells Us
2-3 sentences on the overall picture

## Most Urgent
Top 2-3 things to address first

Keep it concise — this is an onboarding summary, not a full consultation."""

                        try:
                            resp = ai_client.messages.create(
                                model="claude-sonnet-4-6",
                                max_tokens=2000,
                                system="You are an expert integrative medicine practitioner. Analyse lab reports against functional medicine optimal ranges, not just conventional ranges. Be direct and specific.",
                                messages=[{"role": "user", "content": analysis_prompt}]
                            )
                            analysis = resp.content[0].text
                            st.divider()
                            st.markdown(analysis)

                            summary_resp = ai_client.messages.create(
                                model="claude-sonnet-4-6", max_tokens=150,
                                messages=[{"role": "user", "content": f"Summarise in one line (max 120 chars): {raw_values_ob}"}]
                            )
                            summary = summary_resp.content[0].text[:500]
                            db_upsert("lab_reports", {
                                "user_id": user_id,
                                "report_date": report_date_ob.isoformat(),
                                "lab_name": lab_name_ob,
                                "raw_values": raw_values_ob,
                                "summary": summary
                            })
                            save_onboarding_state(user_id, {"step4_done": True, "lab_upload_acknowledged": True})
                            st.success("✅ Report saved.")
                        except Exception as e:
                            st.error(f"Analysis error: {e}")
                else:
                    st.warning("Paste your lab values above to continue.")

            st.divider()

            # Grace period option
            ob_state_fresh = get_onboarding_state(user_id)
            already_has_labs = bool(existing_labs)
            already_acknowledged = ob_state_fresh and ob_state_fresh.get("lab_upload_acknowledged")

            if not already_has_labs:
                st.markdown("**Don't have lab reports yet?**")
                st.caption("You can still continue — your roadmap will be provisional until labs are added. We'll remind you to upload within 2 weeks.")
                if st.button("I'll upload labs within 2 weeks — continue for now", use_container_width=True):
                    save_onboarding_state(user_id, {
                        "current_step": 5,
                        "step4_done": True,
                        "lab_upload_acknowledged": True,
                        "lab_acknowledged_at": datetime.now().isoformat()
                    })
                    st.rerun()

            nav1, nav2 = st.columns(2)
            with nav1:
                if st.button("← Back", use_container_width=True, key="back4"):
                    save_onboarding_state(user_id, {"current_step": 3})
                    st.rerun()
            with nav2:
                if already_has_labs or already_acknowledged:
                    if st.button("Continue →", type="primary", use_container_width=True, key="next4"):
                        save_onboarding_state(user_id, {"current_step": 5, "step4_done": True})
                        st.rerun()

        # ── STEP 5 — Ready ───────────────────────────────────────────────────────
        elif current_step == 5:
            ob_final = get_onboarding_state(user_id)
            completeness = calculate_completeness(user_id, ob_final)
            labs_exist = bool(db_get("lab_reports", user_id))
            lab_acknowledged = ob_final and ob_final.get("lab_upload_acknowledged")

            st.markdown("### You're ready")

            # Completeness card
            if completeness >= 70:
                st.success(f"✅ Profile {completeness}% complete — enough to generate your treatment roadmap.")
            else:
                st.warning(f"⚠️ Profile {completeness}% complete — add more details for a more precise roadmap.")

            st.progress(completeness)

            # Status checklist
            st.markdown("##### What we have:")
            checks = [
                ("Basic information", ob_final.get("step1_done", False) if ob_final else False),
                ("Health profile & medications", ob_final.get("step2_done", False) if ob_final else False),
                ("Lifestyle & goals", ob_final.get("step3_done", False) if ob_final else False),
                ("Lab reports", labs_exist),
            ]
            for label, done in checks:
                icon = "✅" if done else ("⏳" if label == "Lab reports" and lab_acknowledged else "⬜")
                st.markdown(f"{icon} {label}")

            if not labs_exist and lab_acknowledged:
                days_since = 0
                if ob_final and ob_final.get("lab_acknowledged_at"):
                    try:
                        ack_dt = datetime.fromisoformat(ob_final["lab_acknowledged_at"].replace("Z",""))
                        days_since = (datetime.now() - ack_dt).days
                    except:
                        pass
                days_remaining = max(0, 14 - days_since)
                st.info(f"📋 Lab upload: {days_remaining} days remaining in your grace period. Your roadmap will be provisional until labs are added.")

            st.divider()
            st.markdown("##### What happens next:")
            st.markdown("""
- **Your treatment roadmap** generates immediately — a 12-month strategic plan built around your profile, goals, and labs
- **Monthly protocols** follow from the roadmap — what changes each month, what milestones to hit
- **Weekly protocols** give you the day-by-day detail — supplements, nutrition, training, sleep
- **Your Sattva** (chat) is always available for questions, adjustments, and guidance
""")

            if completeness >= 50:
                if st.button("✦ Generate my treatment roadmap", type="primary", use_container_width=True):
                    save_onboarding_state(user_id, {
                        "completed": True,
                        "completed_at": datetime.now().isoformat()
                    })
                    db_upsert("profiles", {"id": user_id, "onboarding_complete": True})
                    st.balloons()
                    st.rerun()
            else:
                st.button("Complete your profile to generate your roadmap", disabled=True, use_container_width=True)
                st.caption("Go back and complete Steps 1-3 to unlock roadmap generation.")

            st.divider()
            nav_back = st.columns([1,3])
            with nav_back[0]:
                if st.button("← Back", use_container_width=True, key="back5"):
                    save_onboarding_state(user_id, {"current_step": 4})
                    st.rerun()

    with col_r:
        if current_step == 1:
            st.markdown("""
            <div style='background:#F7F5F2;border-radius:12px;padding:16px;font-family:Inter,sans-serif;font-size:13px;color:#6B6864;'>
            <p style='font-weight:600;color:#111214;margin:0 0 8px;'>Why we ask</p>
            <p style='margin:0 0 6px;'>Your age, sex, height and weight affect how we interpret your labs and calibrate your nutrition and training recommendations.</p>
            <p style='margin:0 0 6px;'>Location helps us suggest locally available foods and brands.</p>
            <p style='margin:0;'>Alcohol and smoking directly influence hormone metabolism and gut health — we need to know to factor this in.</p>
            </div>
            """, unsafe_allow_html=True)
        elif current_step == 2:
            st.markdown("""
            <div style='background:#F7F5F2;border-radius:12px;padding:16px;font-family:Inter,sans-serif;font-size:13px;color:#6B6864;'>
            <p style='font-weight:600;color:#111214;margin:0 0 8px;'>Your data is private</p>
            <p style='margin:0 0 6px;'>Only you can see your health information. No one else — including practitioners — can access your data unless you explicitly grant them permission.</p>
            <p style='margin:0;'>Add as little or as much as you're comfortable with. You can always update this later.</p>
            </div>
            """, unsafe_allow_html=True)
        elif current_step == 3:
            st.markdown("""
            <div style='background:#F7F5F2;border-radius:12px;padding:16px;font-family:Inter,sans-serif;font-size:13px;color:#6B6864;'>
            <p style='font-weight:600;color:#111214;margin:0 0 8px;'>Goals shape everything</p>
            <p style='margin:0 0 6px;'>Your roadmap is built around your goals and their timeframes. Be specific — "lose weight" is less useful than "reach 58kg by September."</p>
            <p style='margin:0;'>You can have multiple goals with different timeframes. After each goal is achieved, we build a maintenance guide so you keep the results.</p>
            </div>
            """, unsafe_allow_html=True)
        elif current_step == 4:
            st.markdown("""
            <div style='background:#F7F5F2;border-radius:12px;padding:16px;font-family:Inter,sans-serif;font-size:13px;color:#6B6864;'>
            <p style='font-weight:600;color:#111214;margin:0 0 8px;'>Why labs matter</p>
            <p style='margin:0 0 6px;'>Functional medicine reads lab values differently from conventional medicine. A TSH of 2.5 might look "normal" but mask a T3 conversion problem.</p>
            <p style='margin:0 0 6px;'>Your coach interprets values against functional ranges, not just lab reference ranges.</p>
            <p style='margin:0;'>Reports older than 3 months are used for trend context only. Recent labs get priority.</p>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# ONBOARDING WIZARD
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

**Extended panel — add if you have a specific concern:**
Zonulin · Calprotectin · H. pylori antibody · ANA · Morning Cortisol · MTHFR · APOE

In India, Thyrocare's Aarogyam or Wellness packages cover most of the core panel at reasonable cost.
"""

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
        <svg width="40" height="40" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><defs><radialGradient id="osg-ob1" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#B1643A"/><stop offset="40%" stop-color="#B1643A"/><stop offset="54%" stop-color="#BE7C58" stop-opacity="0.72"/><stop offset="70%" stop-color="#D2A084" stop-opacity="0.4"/><stop offset="86%" stop-color="#E6CCB8" stop-opacity="0.14"/><stop offset="100%" stop-color="#E6CCB8" stop-opacity="0"/></radialGradient></defs><path d="M194.49 100.00 L194.46 102.97 L194.34 105.94 L194.12 108.90 L193.81 111.85 L193.40 114.79 L192.90 117.72 L192.31 120.63 L191.62 123.52 L190.84 126.39 L189.97 129.23 L189.01 132.05 L187.96 134.82 L186.81 137.57 L185.57 140.27 L184.25 142.93 L182.84 145.54 L181.34 148.10 L179.76 150.61 L178.09 153.07 L176.35 155.47 L174.53 157.81 L172.64 160.09 L170.67 162.31 L168.64 164.46 L166.55 166.55 L164.39 168.57 L162.18 170.53 L159.91 172.42 L157.58 174.24 L155.21 175.99 L152.78 177.67 L150.31 179.28 L147.79 180.81 L145.23 182.27 L142.62 183.64 L139.97 184.94 L137.28 186.16 L134.56 187.28 L131.80 188.33 L129.01 189.27 L126.19 190.13 L123.34 190.89 L120.47 191.56 L117.57 192.13 L114.67 192.60 L111.74 192.97 L108.81 193.24 L105.88 193.42 L102.94 193.51 L100.00 193.50 L97.06 193.40 L94.14 193.22 L91.21 192.95 L88.30 192.60 L85.40 192.16 L82.52 191.65 L79.64 191.07 L76.79 190.41 L73.95 189.67 L71.13 188.86 L68.33 187.98 L65.55 187.02 L62.79 185.99 L60.06 184.87 L57.36 183.68 L54.70 182.41 L52.07 181.05 L49.48 179.61 L46.94 178.08 L44.45 176.46 L42.01 174.76 L39.64 172.97 L37.33 171.09 L35.09 169.12 L32.92 167.08 L30.84 164.95 L28.84 162.74 L26.92 160.46 L25.09 158.11 L23.34 155.69 L21.69 153.22 L20.12 150.69 L18.65 148.11 L17.26 145.49 L15.96 142.82 L14.75 140.12 L13.62 137.38 L12.58 134.61 L11.62 131.82 L10.74 129.00 L9.95 126.16 L9.23 123.31 L8.60 120.43 L8.04 117.54 L7.57 114.64 L7.19 111.73 L6.88 108.80 L6.66 105.87 L6.53 102.94 L6.49 100.00 L6.53 97.06 L6.67 94.13 L6.89 91.20 L7.21 88.28 L7.61 85.37 L8.11 82.47 L8.70 79.59 L9.37 76.73 L10.14 73.89 L10.99 71.08 L11.93 68.29 L12.95 65.53 L14.05 62.81 L15.24 60.11 L16.50 57.46 L17.85 54.84 L19.27 52.26 L20.77 49.72 L22.35 47.23 L24.00 44.78 L25.73 42.39 L27.53 40.05 L29.41 37.76 L31.36 35.54 L33.38 33.38 L35.47 31.29 L37.64 29.26 L39.87 27.31 L42.16 25.44 L44.52 23.64 L46.94 21.92 L49.41 20.29 L51.94 18.74 L54.52 17.27 L57.15 15.90 L59.82 14.60 L62.52 13.40 L65.27 12.28 L68.04 11.24 L70.85 10.29 L73.69 9.43 L76.54 8.64 L79.42 7.95 L82.32 7.34 L85.24 6.81 L88.17 6.37 L91.12 6.02 L94.07 5.75 L97.03 5.58 L100.00 5.50 L102.97 5.52 L105.94 5.63 L108.90 5.84 L111.85 6.16 L114.80 6.58 L117.72 7.10 L120.62 7.73 L123.50 8.47 L126.35 9.31 L129.16 10.25 L131.94 11.29 L134.67 12.43 L137.36 13.67 L140.00 15.00 L142.59 16.41 L145.13 17.91 L147.62 19.48 L150.05 21.13 L152.43 22.84 L154.76 24.62 L157.04 26.46 L159.26 28.36 L161.44 30.31 L163.56 32.32 L165.63 34.37 L167.65 36.48 L169.61 38.63 L171.52 40.83 L173.38 43.08 L175.18 45.38 L176.93 47.72 L178.61 50.12 L180.22 52.56 L181.76 55.05 L183.23 57.59 L184.63 60.18 L185.94 62.81 L187.17 65.49 L188.31 68.21 L189.36 70.97 L190.31 73.76 L191.17 76.59 L191.93 79.45 L192.59 82.34 L193.16 85.25 L193.62 88.17 L193.99 91.12 L194.25 94.07 L194.42 97.03 L194.49 100.00 Z" fill="none" stroke="#111214" stroke-width="1.3"/><path d="M183.80 100.00 L183.77 102.63 L183.66 105.26 L183.45 107.89 L183.17 110.51 L182.80 113.11 L182.34 115.71 L181.80 118.29 L181.18 120.84 L180.48 123.38 L179.69 125.89 L178.82 128.38 L177.87 130.83 L176.84 133.25 L175.73 135.64 L174.54 137.98 L173.28 140.29 L171.94 142.54 L170.52 144.76 L169.04 146.92 L167.48 149.03 L165.86 151.09 L164.18 153.09 L162.43 155.04 L160.63 156.93 L158.77 158.77 L156.86 160.55 L154.90 162.27 L152.89 163.93 L150.83 165.53 L148.73 167.07 L146.59 168.55 L144.40 169.97 L142.18 171.32 L139.91 172.61 L137.62 173.82 L135.28 174.97 L132.91 176.05 L130.51 177.06 L128.08 177.98 L125.61 178.83 L123.13 179.60 L120.61 180.29 L118.08 180.89 L115.53 181.41 L112.96 181.84 L110.38 182.19 L107.79 182.46 L105.20 182.64 L102.60 182.73 L100.00 182.75 L97.40 182.68 L94.81 182.54 L92.22 182.33 L89.64 182.04 L87.06 181.68 L84.50 181.25 L81.95 180.75 L79.41 180.18 L76.89 179.55 L74.38 178.85 L71.89 178.08 L69.42 177.25 L66.96 176.34 L64.54 175.37 L62.13 174.32 L59.76 173.20 L57.42 172.00 L55.12 170.72 L52.86 169.37 L50.64 167.93 L48.48 166.42 L46.37 164.83 L44.32 163.16 L42.33 161.41 L40.42 159.58 L38.57 157.69 L36.80 155.72 L35.10 153.69 L33.49 151.59 L31.95 149.44 L30.49 147.24 L29.12 144.98 L27.82 142.69 L26.61 140.35 L25.47 137.97 L24.41 135.57 L23.43 133.13 L22.53 130.67 L21.70 128.19 L20.94 125.69 L20.25 123.17 L19.64 120.63 L19.09 118.08 L18.62 115.52 L18.23 112.95 L17.90 110.37 L17.65 107.78 L17.47 105.19 L17.37 102.60 L17.34 100.00 L17.40 97.40 L17.53 94.81 L17.73 92.22 L18.02 89.64 L18.39 87.07 L18.83 84.52 L19.35 81.97 L19.95 79.45 L20.63 76.94 L21.38 74.45 L22.21 71.99 L23.10 69.55 L24.08 67.14 L25.12 64.76 L26.23 62.41 L27.41 60.09 L28.66 57.81 L29.98 55.56 L31.36 53.35 L32.81 51.19 L34.33 49.06 L35.92 46.99 L37.57 44.96 L39.29 42.99 L41.07 41.07 L42.91 39.20 L44.82 37.41 L46.78 35.67 L48.81 34.00 L50.89 32.40 L53.02 30.87 L55.21 29.42 L57.44 28.04 L59.72 26.74 L62.04 25.51 L64.41 24.36 L66.80 23.28 L69.23 22.29 L71.69 21.37 L74.18 20.52 L76.69 19.75 L79.22 19.06 L81.77 18.44 L84.34 17.90 L86.92 17.44 L89.52 17.05 L92.13 16.74 L94.75 16.51 L97.37 16.36 L100.00 16.29 L102.63 16.31 L105.26 16.41 L107.88 16.61 L110.50 16.89 L113.10 17.27 L115.69 17.74 L118.26 18.30 L120.81 18.95 L123.33 19.70 L125.82 20.54 L128.27 21.46 L130.69 22.48 L133.07 23.57 L135.41 24.75 L137.70 26.00 L139.95 27.33 L142.15 28.72 L144.31 30.18 L146.42 31.69 L148.48 33.27 L150.50 34.89 L152.47 36.57 L154.40 38.29 L156.28 40.06 L158.12 41.88 L159.91 43.74 L161.66 45.64 L163.36 47.58 L165.01 49.57 L166.62 51.60 L168.17 53.67 L169.66 55.79 L171.10 57.95 L172.48 60.16 L173.79 62.40 L175.03 64.69 L176.20 67.03 L177.30 69.40 L178.31 71.81 L179.25 74.25 L180.10 76.73 L180.87 79.24 L181.54 81.77 L182.13 84.33 L182.64 86.91 L183.05 89.51 L183.37 92.12 L183.60 94.74 L183.75 97.37 L183.80 100.00 Z" fill="none" stroke="#111214" stroke-width="1.3"/><path d="M170.96 100.00 L170.92 102.23 L170.80 104.45 L170.61 106.67 L170.35 108.89 L170.03 111.09 L169.63 113.28 L169.16 115.46 L168.63 117.62 L168.02 119.76 L167.35 121.88 L166.61 123.98 L165.81 126.06 L164.94 128.10 L164.00 130.12 L163.00 132.10 L161.94 134.05 L160.81 135.96 L159.62 137.84 L158.38 139.67 L157.08 141.47 L155.72 143.22 L154.31 144.93 L152.84 146.59 L151.33 148.21 L149.77 149.77 L148.17 151.30 L146.52 152.77 L144.84 154.20 L143.11 155.57 L141.34 156.90 L139.53 158.17 L137.69 159.39 L135.81 160.55 L133.90 161.66 L131.95 162.71 L129.97 163.70 L127.96 164.62 L125.93 165.48 L123.86 166.28 L121.77 167.00 L119.65 167.65 L117.52 168.23 L115.36 168.73 L113.19 169.16 L111.01 169.52 L108.82 169.79 L106.62 170.00 L104.41 170.13 L102.21 170.18 L100.00 170.17 L97.80 170.09 L95.60 169.94 L93.41 169.73 L91.23 169.45 L89.05 169.12 L86.89 168.73 L84.74 168.28 L82.60 167.78 L80.47 167.22 L78.36 166.61 L76.26 165.95 L74.17 165.23 L72.11 164.46 L70.06 163.63 L68.03 162.74 L66.03 161.79 L64.05 160.78 L62.11 159.71 L60.19 158.57 L58.32 157.37 L56.48 156.10 L54.69 154.77 L52.95 153.37 L51.26 151.91 L49.62 150.38 L48.04 148.79 L46.53 147.14 L45.07 145.44 L43.69 143.68 L42.37 141.87 L41.12 140.02 L39.93 138.12 L38.82 136.18 L37.77 134.21 L36.79 132.21 L35.87 130.18 L35.02 128.12 L34.24 126.04 L33.52 123.93 L32.87 121.81 L32.28 119.68 L31.75 117.52 L31.28 115.36 L30.88 113.19 L30.54 111.00 L30.26 108.81 L30.06 106.61 L29.91 104.41 L29.83 102.21 L29.82 100.00 L29.88 97.80 L30.00 95.60 L30.20 93.40 L30.46 91.21 L30.78 89.04 L31.18 86.87 L31.64 84.72 L32.17 82.58 L32.76 80.47 L33.42 78.37 L34.13 76.29 L34.91 74.23 L35.75 72.20 L36.65 70.19 L37.60 68.20 L38.61 66.25 L39.67 64.32 L40.79 62.43 L41.97 60.56 L43.20 58.73 L44.49 56.94 L45.83 55.18 L47.22 53.47 L48.67 51.80 L50.17 50.17 L51.72 48.59 L53.33 47.06 L54.99 45.59 L56.69 44.17 L58.45 42.81 L60.25 41.50 L62.09 40.26 L63.98 39.09 L65.90 37.97 L67.86 36.92 L69.86 35.94 L71.88 35.02 L73.93 34.17 L76.01 33.38 L78.12 32.66 L80.24 32.00 L82.39 31.40 L84.55 30.87 L86.73 30.41 L88.91 30.01 L91.12 29.68 L93.33 29.41 L95.55 29.22 L97.77 29.09 L100.00 29.03 L102.23 29.05 L104.46 29.14 L106.68 29.31 L108.90 29.56 L111.11 29.88 L113.30 30.28 L115.48 30.76 L117.63 31.32 L119.77 31.96 L121.87 32.68 L123.95 33.47 L126.00 34.33 L128.01 35.27 L129.99 36.27 L131.93 37.34 L133.83 38.46 L135.69 39.64 L137.52 40.88 L139.30 42.16 L141.05 43.50 L142.76 44.87 L144.43 46.29 L146.07 47.75 L147.66 49.24 L149.23 50.77 L150.75 52.34 L152.24 53.95 L153.68 55.59 L155.09 57.27 L156.46 58.98 L157.78 60.73 L159.06 62.52 L160.28 64.35 L161.46 66.21 L162.57 68.12 L163.63 70.06 L164.63 72.03 L165.56 74.04 L166.42 76.09 L167.21 78.16 L167.93 80.26 L168.57 82.39 L169.14 84.55 L169.63 86.72 L170.04 88.91 L170.38 91.11 L170.64 93.32 L170.82 95.54 L170.93 97.77 L170.96 100.00 Z" fill="none" stroke="#111214" stroke-width="1.3"/><path d="M161.03 100.00 L160.99 101.92 L160.89 103.83 L160.74 105.74 L160.52 107.65 L160.25 109.54 L159.93 111.43 L159.54 113.31 L159.10 115.17 L158.60 117.03 L158.05 118.86 L157.44 120.68 L156.77 122.48 L156.04 124.25 L155.25 126.00 L154.41 127.72 L153.50 129.41 L152.55 131.08 L151.53 132.70 L150.46 134.29 L149.34 135.85 L148.17 137.36 L146.94 138.83 L145.67 140.26 L144.36 141.65 L143.00 143.00 L141.60 144.30 L140.16 145.55 L138.68 146.76 L137.17 147.92 L135.63 149.04 L134.05 150.11 L132.45 151.13 L130.81 152.10 L129.15 153.03 L127.46 153.90 L125.75 154.72 L124.01 155.49 L122.25 156.20 L120.47 156.86 L118.67 157.46 L116.85 158.00 L115.02 158.49 L113.17 158.91 L111.31 159.27 L109.44 159.57 L107.56 159.81 L105.67 159.99 L103.78 160.11 L101.89 160.18 L100.00 160.18 L98.11 160.14 L96.22 160.03 L94.34 159.88 L92.46 159.68 L90.59 159.42 L88.72 159.12 L86.86 158.78 L85.01 158.38 L83.17 157.94 L81.33 157.45 L79.51 156.92 L77.70 156.33 L75.90 155.69 L74.12 155.00 L72.36 154.26 L70.61 153.46 L68.89 152.60 L67.20 151.68 L65.55 150.70 L63.92 149.66 L62.34 148.56 L60.79 147.39 L59.30 146.17 L57.85 144.88 L56.46 143.54 L55.12 142.15 L53.83 140.70 L52.61 139.20 L51.44 137.66 L50.34 136.08 L49.29 134.46 L48.31 132.80 L47.38 131.12 L46.51 129.41 L45.69 127.67 L44.93 125.91 L44.22 124.14 L43.57 122.34 L42.96 120.54 L42.40 118.71 L41.89 116.88 L41.43 115.04 L41.02 113.18 L40.66 111.32 L40.35 109.45 L40.10 107.57 L39.89 105.68 L39.74 103.79 L39.65 101.90 L39.61 100.00 L39.63 98.10 L39.72 96.21 L39.86 94.32 L40.06 92.43 L40.33 90.55 L40.66 88.68 L41.05 86.82 L41.50 84.98 L42.01 83.15 L42.57 81.34 L43.20 79.55 L43.88 77.78 L44.61 76.03 L45.39 74.30 L46.22 72.60 L47.11 70.92 L48.04 69.27 L49.02 67.64 L50.04 66.05 L51.11 64.48 L52.23 62.94 L53.39 61.44 L54.60 59.97 L55.85 58.54 L57.14 57.14 L58.48 55.79 L59.86 54.47 L61.29 53.21 L62.75 51.98 L64.26 50.81 L65.81 49.69 L67.39 48.61 L69.01 47.59 L70.66 46.63 L72.34 45.72 L74.05 44.86 L75.79 44.06 L77.56 43.31 L79.34 42.62 L81.15 41.99 L82.98 41.41 L84.82 40.88 L86.68 40.42 L88.56 40.00 L90.44 39.65 L92.34 39.35 L94.24 39.11 L96.16 38.94 L98.08 38.82 L100.00 38.77 L101.92 38.78 L103.85 38.86 L105.77 39.00 L107.68 39.22 L109.58 39.50 L111.47 39.86 L113.35 40.28 L115.21 40.78 L117.04 41.35 L118.85 41.98 L120.64 42.68 L122.39 43.44 L124.12 44.26 L125.82 45.14 L127.48 46.07 L129.11 47.06 L130.70 48.09 L132.26 49.16 L133.79 50.28 L135.29 51.43 L136.75 52.62 L138.19 53.84 L139.59 55.09 L140.97 56.38 L142.31 57.69 L143.63 59.03 L144.91 60.41 L146.16 61.81 L147.38 63.25 L148.57 64.71 L149.72 66.21 L150.82 67.75 L151.89 69.31 L152.91 70.91 L153.88 72.55 L154.79 74.22 L155.65 75.92 L156.46 77.65 L157.20 79.41 L157.88 81.20 L158.49 83.01 L159.04 84.84 L159.52 86.70 L159.93 88.57 L160.27 90.45 L160.55 92.35 L160.77 94.26 L160.92 96.17 L161.00 98.08 L161.03 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><path d="M150.19 100.00 L150.18 101.58 L150.13 103.15 L150.03 104.73 L149.88 106.30 L149.68 107.87 L149.43 109.43 L149.13 110.98 L148.78 112.52 L148.38 114.06 L147.93 115.57 L147.42 117.07 L146.86 118.56 L146.25 120.02 L145.59 121.45 L144.88 122.87 L144.11 124.25 L143.29 125.60 L142.43 126.93 L141.52 128.22 L140.57 129.48 L139.58 130.70 L138.55 131.89 L137.48 133.04 L136.38 134.16 L135.25 135.25 L134.08 136.30 L132.90 137.31 L131.68 138.30 L130.44 139.25 L129.18 140.17 L127.90 141.05 L126.59 141.91 L125.27 142.72 L123.92 143.51 L122.55 144.25 L121.16 144.96 L119.74 145.62 L118.31 146.25 L116.86 146.83 L115.39 147.35 L113.90 147.83 L112.39 148.26 L110.87 148.63 L109.34 148.95 L107.79 149.21 L106.24 149.42 L104.69 149.57 L103.12 149.66 L101.56 149.70 L100.00 149.68 L98.44 149.61 L96.89 149.50 L95.34 149.33 L93.79 149.13 L92.26 148.88 L90.73 148.59 L89.21 148.27 L87.70 147.91 L86.20 147.51 L84.70 147.09 L83.21 146.62 L81.74 146.13 L80.27 145.60 L78.81 145.03 L77.37 144.42 L75.93 143.78 L74.52 143.09 L73.12 142.36 L71.74 141.58 L70.39 140.76 L69.07 139.88 L67.77 138.96 L66.52 137.98 L65.30 136.96 L64.12 135.88 L62.99 134.76 L61.91 133.58 L60.87 132.37 L59.89 131.11 L58.96 129.81 L58.09 128.48 L57.27 127.12 L56.51 125.72 L55.80 124.30 L55.14 122.86 L54.53 121.40 L53.97 119.92 L53.45 118.43 L52.99 116.93 L52.56 115.41 L52.18 113.89 L51.84 112.37 L51.54 110.83 L51.28 109.29 L51.05 107.75 L50.87 106.21 L50.72 104.66 L50.62 103.11 L50.55 101.55 L50.53 100.00 L50.54 98.45 L50.61 96.89 L50.71 95.34 L50.87 93.79 L51.07 92.25 L51.31 90.71 L51.61 89.18 L51.95 87.66 L52.34 86.15 L52.78 84.66 L53.26 83.17 L53.80 81.71 L54.38 80.26 L55.00 78.83 L55.67 77.41 L56.39 76.03 L57.15 74.66 L57.95 73.32 L58.80 72.00 L59.68 70.71 L60.61 69.45 L61.58 68.21 L62.58 67.01 L63.62 65.84 L64.70 64.70 L65.82 63.60 L66.97 62.53 L68.15 61.50 L69.37 60.51 L70.62 59.56 L71.90 58.65 L73.20 57.78 L74.54 56.95 L75.90 56.16 L77.28 55.41 L78.69 54.71 L80.12 54.05 L81.56 53.43 L83.03 52.86 L84.51 52.33 L86.01 51.84 L87.52 51.40 L89.05 51.01 L90.59 50.66 L92.14 50.35 L93.70 50.10 L95.26 49.89 L96.84 49.74 L98.42 49.64 L100.00 49.59 L101.58 49.60 L103.17 49.66 L104.75 49.78 L106.32 49.96 L107.89 50.20 L109.44 50.50 L110.99 50.85 L112.51 51.27 L114.02 51.74 L115.51 52.26 L116.98 52.84 L118.42 53.47 L119.84 54.15 L121.23 54.88 L122.60 55.65 L123.94 56.45 L125.25 57.30 L126.54 58.18 L127.80 59.10 L129.03 60.04 L130.24 61.01 L131.42 62.02 L132.58 63.04 L133.71 64.10 L134.82 65.18 L135.90 66.28 L136.96 67.41 L137.99 68.57 L138.99 69.76 L139.96 70.97 L140.90 72.21 L141.80 73.47 L142.66 74.77 L143.49 76.09 L144.28 77.44 L145.02 78.82 L145.71 80.22 L146.36 81.64 L146.96 83.09 L147.51 84.56 L148.01 86.05 L148.45 87.56 L148.85 89.08 L149.19 90.62 L149.48 92.16 L149.72 93.72 L149.91 95.28 L150.05 96.85 L150.15 98.42 L150.19 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><path d="M139.49 100.00 L139.50 101.24 L139.47 102.48 L139.39 103.72 L139.27 104.96 L139.10 106.19 L138.89 107.42 L138.64 108.64 L138.34 109.84 L138.00 111.04 L137.62 112.22 L137.19 113.39 L136.73 114.54 L136.22 115.67 L135.68 116.79 L135.10 117.88 L134.49 118.96 L133.84 120.01 L133.16 121.04 L132.45 122.05 L131.71 123.04 L130.95 124.00 L130.16 124.95 L129.34 125.87 L128.50 126.76 L127.63 127.63 L126.75 128.48 L125.83 129.30 L124.90 130.10 L123.95 130.87 L122.97 131.61 L121.97 132.32 L120.95 133.01 L119.90 133.65 L118.84 134.27 L117.75 134.85 L116.65 135.39 L115.53 135.89 L114.39 136.35 L113.24 136.77 L112.07 137.15 L110.89 137.49 L109.70 137.79 L108.50 138.04 L107.30 138.26 L106.09 138.43 L104.87 138.57 L103.66 138.67 L102.44 138.73 L101.22 138.76 L100.00 138.75 L98.78 138.72 L97.57 138.65 L96.36 138.55 L95.15 138.42 L93.94 138.27 L92.74 138.08 L91.54 137.87 L90.34 137.62 L89.15 137.35 L87.96 137.05 L86.78 136.71 L85.61 136.34 L84.45 135.93 L83.30 135.49 L82.16 135.01 L81.04 134.50 L79.93 133.94 L78.84 133.34 L77.77 132.71 L76.73 132.03 L75.71 131.32 L74.71 130.57 L73.75 129.78 L72.82 128.95 L71.91 128.09 L71.05 127.19 L70.21 126.26 L69.41 125.30 L68.65 124.32 L67.93 123.30 L67.24 122.27 L66.58 121.21 L65.97 120.13 L65.39 119.03 L64.85 117.91 L64.34 116.78 L63.87 115.63 L63.44 114.47 L63.05 113.30 L62.69 112.12 L62.37 110.93 L62.09 109.73 L61.84 108.53 L61.64 107.32 L61.47 106.10 L61.33 104.88 L61.23 103.66 L61.17 102.44 L61.15 101.22 L61.16 100.00 L61.21 98.78 L61.29 97.56 L61.40 96.35 L61.55 95.14 L61.73 93.94 L61.95 92.74 L62.19 91.55 L62.47 90.36 L62.78 89.19 L63.12 88.02 L63.49 86.86 L63.89 85.70 L64.33 84.56 L64.80 83.44 L65.30 82.32 L65.84 81.22 L66.41 80.14 L67.02 79.07 L67.66 78.02 L68.34 77.00 L69.05 75.99 L69.80 75.02 L70.58 74.06 L71.40 73.14 L72.24 72.24 L73.12 71.38 L74.03 70.55 L74.97 69.74 L75.93 68.98 L76.92 68.24 L77.94 67.54 L78.97 66.87 L80.03 66.23 L81.10 65.62 L82.19 65.05 L83.30 64.51 L84.42 64.00 L85.56 63.52 L86.70 63.07 L87.87 62.65 L89.04 62.27 L90.22 61.92 L91.42 61.60 L92.62 61.31 L93.83 61.07 L95.05 60.85 L96.28 60.68 L97.52 60.55 L98.76 60.46 L100.00 60.42 L101.24 60.42 L102.49 60.47 L103.73 60.56 L104.96 60.71 L106.19 60.90 L107.41 61.14 L108.62 61.42 L109.82 61.75 L111.00 62.13 L112.17 62.55 L113.32 63.01 L114.45 63.51 L115.56 64.04 L116.65 64.61 L117.72 65.22 L118.77 65.85 L119.80 66.52 L120.81 67.21 L121.80 67.92 L122.77 68.66 L123.72 69.43 L124.64 70.21 L125.55 71.02 L126.44 71.85 L127.30 72.70 L128.15 73.57 L128.97 74.46 L129.77 75.37 L130.55 76.31 L131.30 77.26 L132.02 78.24 L132.72 79.23 L133.39 80.25 L134.03 81.29 L134.64 82.35 L135.22 83.43 L135.76 84.52 L136.27 85.64 L136.75 86.77 L137.19 87.92 L137.59 89.08 L137.96 90.25 L138.29 91.44 L138.58 92.64 L138.83 93.85 L139.05 95.07 L139.22 96.29 L139.35 97.52 L139.44 98.76 L139.49 100.00 Z" fill="none" stroke="#B6744A" stroke-width="1.6"/><circle cx="100" cy="100" r="31.3" fill="url(#osg-ob1)"/></svg>
        <span style="font-family:Newsreader,serif;font-weight:400;font-style:normal;font-size:1.6rem;color:#111214;letter-spacing:-0.02em;">
          OneSattva
        </span>
      </div>
      <p style="font-family:Newsreader,serif;font-style:italic;color:#B6744A;font-size:0.9rem;margin:4px 0 0;">Health, understood.</p>
      <p style="font-family:Inter,sans-serif;font-size:0.9rem;color:#6B6864;margin-top:10px;">Let's build your health profile — takes about 5 minutes.</p>
    </div>
    """, unsafe_allow_html=True)

    # Progress
    steps = ["Basic Info", "Health", "Lifestyle", "Labs", "Ready"]
    step_html = "<div style='display:flex;gap:5px;margin-bottom:10px;'>"
    for i, s in enumerate(steps):
        is_done = (i + 1) < current_step
        is_current = (i + 1) == current_step
        bg = "#111214" if is_done else ("#B6744A" if is_current else "#E8E8E4")
        color = "#F7F5F2" if (is_done or is_current) else "#9B9B92"
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
            <div style='background:#F7F5F2;border-radius:12px;padding:16px;margin-top:48px;'>
            <p style='font-family:Inter,sans-serif;font-weight:600;color:#111214;font-size:13px;margin:0 0 8px;'>{title}</p>
            <p style='font-family:Inter,sans-serif;color:#6B6864;font-size:13px;margin:0;line-height:1.5;'>{body}</p>
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
