"""
OneSattva — Integrative Health Coach
Streamlit app with Supabase backend and Anthropic Claude AI
"""
import streamlit as st
import json, statistics, re
from datetime import date, datetime, timedelta
from supabase import create_client

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="OneSattva", page_icon="◎", layout="wide", initial_sidebar_state="expanded")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ANTHROPIC_KEY = st.secrets["ANTHROPIC_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

MAX_HISTORY = 20

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
"""

# ── SVG Mark ──────────────────────────────────────────────────────────────────
def mark_svg(size=46, dark=False):
    outer = "#F7F5F2" if dark else "rgba(17,18,20,0.15)"
    inner = "#B6744A"
    r_vals = [size*0.48, size*0.40, size*0.33, size*0.26, size*0.20, size*0.14]
    cx = size/2
    rings = ""
    for i, r in enumerate(r_vals):
        color = outer if i < 3 else inner
        rings += f'<circle cx="{cx}" cy="{cx}" r="{r}" fill="none" stroke="{color}" stroke-width="1"/>'
    rings += f'<circle cx="{cx}" cy="{cx}" r="{size*0.07}" fill="{inner}"/>'
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">{rings}</svg>'

# ── Global CSS ────────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bone: #F7F5F2;
    --graphite: #111214;
    --copper: #B6744A;
    --stone: #E6E3DF;
    --forest: #1F2F2A;
    --mid: #6B6358;
    --white: #FFFFFF;
    --line: rgba(17,18,20,0.09);
    --linem: rgba(17,18,20,0.14);
    --cu-bg: rgba(182,116,74,0.08);
    --cu-bd: rgba(182,116,74,0.22);
}

.stApp { background-color: var(--bone) !important; }
[data-testid="stSidebar"] { background-color: #111214 !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { margin: 0; }

.sl { font-size:10px; font-weight:600; letter-spacing:0.09em; text-transform:uppercase; color:var(--mid); margin-top:18px; margin-bottom:8px; }
.sl.first { margin-top:0; }
.plan-banner { background:var(--forest); border-radius:10px; padding:12px 16px; }
.prio-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.prio-card { background:var(--white); border:1px solid var(--line); border-radius:12px; padding:14px 15px; }
.triage { display:inline-block; font-size:10px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; padding:3px 9px; border-radius:20px; margin-bottom:8px; }
.t-now { background:rgba(182,116,74,0.10); color:var(--copper); border:1px solid var(--cu-bd); }
.t-watch { background:rgba(230,227,223,0.7); color:#5A5248; border:1px solid var(--stone); }
.t-bg { background:transparent; color:var(--mid); font-style:italic; padding-left:0; }
.pc-title { font-size:13px; font-weight:500; color:var(--graphite); margin-bottom:4px; }
.pc-body { font-size:11.5px; color:var(--mid); line-height:1.55; }
.snap-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
.snap-box { background:var(--white); border:1px solid var(--line); border-radius:10px; padding:13px 14px; }
.snap-lbl { font-size:10px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:var(--mid); }
.snap-val { font-family:'JetBrains Mono',monospace; font-size:21px; color:var(--graphite); }
.snap-sub { font-size:11px; color:var(--mid); margin-top:3px; }
.snap-flag { color:var(--copper); font-size:11px; margin-top:2px; }
.trends-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.trend-card { background:var(--white); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }
.tc-title { font-size:12px; font-weight:500; color:var(--graphite); margin-bottom:3px; }
.tc-insight { font-size:11.5px; color:var(--mid); line-height:1.5; margin-bottom:10px; }
.tc-bars { height:40px; background:rgba(230,227,223,0.4); display:flex; align-items:flex-end; padding:0 4px 3px; gap:3px; border-radius:6px; }
.tb { border-radius:2px 2px 0 0; background:var(--copper); opacity:0.55; flex:1; }
.insight-box { background:var(--forest); border-radius:12px; padding:15px 18px; margin-bottom:14px; }
.ib-lbl { font-size:10px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:rgba(247,245,242,0.34); margin-bottom:7px; }
.ib-txt { font-family:'Newsreader',serif; font-style:italic; font-size:14px; color:#F7F5F2; line-height:1.6; }
.sb-name { font-size:13px; color:#F7F5F2; font-weight:500; }
.sb-meta { font-size:11px; color:rgba(247,245,242,0.36); margin-top:2px; }
.sb-tag { font-family:'Newsreader',serif; font-style:italic; font-size:11px; color:var(--copper); margin-top:4px; }
.sb-foot-t { font-size:10.5px; color:rgba(247,245,242,0.2); line-height:1.5; }
.plan-pill { background:rgba(182,116,74,0.14); border:1px solid rgba(182,116,74,0.26); border-radius:20px; padding:3px 9px; font-size:11px; color:var(--copper); font-family:'JetBrains Mono',monospace; display:inline-flex; margin-top:7px; }
.prof-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.prof-card { background:var(--white); border:1px solid var(--line); border-radius:12px; padding:14px 16px; }
.prof-card-hd h4 { font-size:10px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:var(--mid); }
.pr { display:flex; justify-content:space-between; padding:5px 0; font-size:13px; border-bottom:1px solid rgba(17,18,20,0.04); }
.pr-k { color:var(--mid); }
.pr-v { color:var(--graphite); font-weight:500; }
.ci-lbl { font-size:10px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:var(--mid); margin-bottom:4px; display:block; }
.ch-hd { font-size:10px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:var(--copper); margin-bottom:5px; }
.whoop-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.wc { background:var(--white); border:1px solid var(--line); border-radius:10px; padding:13px; }
.wc-lbl { font-size:10px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; color:var(--mid); }
.wc-val { font-family:'JetBrains Mono',monospace; font-size:20px; color:var(--graphite); }
.wc-sub { font-size:11px; color:var(--mid); margin-top:2px; }
.wc-d { font-size:11px; color:var(--copper); margin-top:2px; }
.stTabs [data-baseweb="tab-list"] { gap:5px; background:transparent; padding:0; }
.stTabs [data-baseweb="tab"] { border-radius:20px; color:var(--mid); font-weight:500; padding:6px 13px; font-size:12px; border:1.5px solid var(--line); background:transparent; }
.stTabs [aria-selected="true"] { background:var(--graphite)!important; border-color:var(--graphite)!important; color:var(--bone)!important; }
.stTabs [data-baseweb="tab-border"], .stTabs [data-baseweb="tab-highlight"] { display:none; }
.pg-title { font-family:'Newsreader',serif; font-size:23px; color:var(--graphite); font-weight:400; margin-bottom:3px; }
.pg-sub { font-size:12.5px; color:var(--mid); margin-bottom:20px; line-height:1.5; }
.cp-banner { background:var(--cu-bg); border:1px solid var(--cu-bd); border-radius:10px; padding:12px 16px; display:flex; gap:12px; }
.file-row { display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:rgba(230,227,223,0.3); border-radius:8px; font-size:12.5px; margin-bottom:6px; }
.fn { color:var(--graphite); font-weight:500; }
.fok { color:#3A6B4A; font-size:11px; font-weight:600; }

/* Auth dark page */
.auth-page .stApp { background-color: #111214 !important; }
.auth-card { background:var(--bone); border-radius:16px; padding:40px 36px; max-width:420px; margin:60px auto; box-shadow:0 8px 32px rgba(0,0,0,0.3); }
.auth-card h1 { font-family:'Newsreader',serif; font-size:22px; color:var(--graphite); margin:12px 0 2px; font-weight:400; }
.auth-card .tagline { font-family:'Newsreader',serif; font-style:italic; font-size:13px; color:var(--copper); margin-bottom:20px; }
.mode-card { background:var(--white); border:2px solid var(--line); border-radius:12px; padding:16px; cursor:pointer; transition:border-color 0.2s; }
.mode-card.selected { border-color:var(--graphite); }
.mode-dur { font-size:10px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:var(--mid); }
.mode-name { font-family:'Newsreader',serif; font-size:19px; color:var(--graphite); margin:4px 0 2px; }
.mode-sub { font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--copper); margin-bottom:6px; }
.mode-desc { font-size:12px; color:var(--mid); line-height:1.5; }
.ob-progress { display:flex; justify-content:center; gap:32px; margin:20px 0 30px; }
.ob-dot { text-align:center; font-size:10px; color:var(--mid); }
.ob-dot.active { color:var(--copper); font-weight:600; }
.ob-dot-circle { width:10px; height:10px; border-radius:50%; background:var(--stone); margin:0 auto 5px; }
.ob-dot.active .ob-dot-circle { background:var(--copper); }
.ob-dot.done .ob-dot-circle { background:var(--copper); }
</style>
"""

AUTH_CSS = """
<style>
.stApp { background-color: #111214 !important; }
</style>
"""
# ── DB Helpers ─────────────────────────────────────────────────────────────────

def db_get(table, user_id, order_col=None, limit=None):
    try:
        q = supabase.table(table).select("*").eq("user_id", user_id)
        if order_col:
            q = q.order(order_col, desc=True)
        if limit:
            q = q.limit(limit)
        res = q.execute()
        return res.data if res.data else []
    except:
        return []

def db_get_single(table, user_id):
    try:
        col = "id" if table == "profiles" else "user_id"
        res = supabase.table(table).select("*").eq(col, user_id).limit(1).execute()
        return res.data[0] if res.data else None
    except:
        return None

def db_upsert(table, data):
    try:
        supabase.table(table).upsert(data).execute()
        return True
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def db_insert(table, data):
    try:
        supabase.table(table).insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def db_delete(table, row_id):
    try:
        supabase.table(table).delete().eq("id", row_id).execute()
        return True
    except:
        return False

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
    except:
        return None

def save_onboarding_state(user_id, data):
    try:
        data["user_id"] = user_id
        supabase.table("onboarding").upsert(data).execute()
    except Exception as e:
        st.error(f"Save error: {e}")

# ── Cycle Calculation ────────────────────────────────────────────────────────

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

# ── WHOOP CSV Helpers ─────────────────────────────────────────────────────────

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

# ── AI Helper ─────────────────────────────────────────────────────────────────

def ai_generate(system_prompt, user_prompt, max_tokens=4096):
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return msg.content[0].text

def ai_chat(system_prompt, messages, max_tokens=4096):
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages
    )
    return msg.content[0].text
# ── System Prompt Builder ─────────────────────────────────────────────────────

def build_system_prompt(user_id, profile):
    today = date.today()
    three_months_ago = date(today.year, today.month - 3 if today.month > 3 else today.month + 9,
                            today.day) if today.month > 3 else date(today.year - 1, today.month + 9, today.day)

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
If the gap is 1-2 weeks: ask a brief re-calibration question before making recommendations.
If the gap is 2+ weeks: do not continue the old protocol. Generate a fresh re-entry assessment before resuming.

RULE 6 — SPECIFIC, NOT GENERIC:
Always recommend exact brands (available in the patient's location), exact doses, exact timing. Never give generic supplement or food advice when the patient's labs, conditions, and goals give you enough context to be specific.

RULE 7 — NEVER DEFLECT:
Never say "consult a nutritionist" or "ask your doctor" without first giving a complete, specific answer yourself. You are their nutritionist and functional medicine coach.

═══════════════════════════════════════════════════════
FUNCTIONAL NUTRITIONIST VOICE
═══════════════════════════════════════════════════════

When giving nutrition guidance:
- Specific foods with exact portions, preparation methods, and timing
- Reason through gut status, absorption capacity, and digestive fire (Agni)
- Consider cycle phase, time of day, workout timing, and medication interactions
- Favour cooked, warm, easily digestible proteins over raw
- No raw salads as main meals for patients with gut issues
- Foods as medicine: specific therapeutic choices
- Gut-healing foods: bone broth, cooked moong dal, ghee, fermented foods as appropriate
- Diet must respect the patient's stated dietary preferences

═══════════════════════════════════════════════════════
FITNESS TRAINER VOICE
═══════════════════════════════════════════════════════

When giving training guidance:
- Specific exercises, not categories. "3 sets of 8 Romanian deadlifts at RPE 7" not "do some leg work"
- Cycle-phase periodisation for female patients
- Recovery awareness: modify if HRV below baseline or recovery < 50%
- Warm-up and cool-down as non-negotiable
- Progressive overload with specific targets
- Training around health conditions

═══════════════════════════════════════════════════════
INTEGRATIVE CROSS-SYSTEM REASONING
═══════════════════════════════════════════════════════

Always reason across all three systems simultaneously:
- FUNCTIONAL MEDICINE: root cause focus, lab interpretation against functional ranges
- AYURVEDA: constitutional type, Agni, seasonal recommendations, Dinacharya
- TCM: organ system patterns, Five Element theory, Qi and Blood

═══════════════════════════════════════════════════════
GEOGRAPHY AND BRAND GUIDANCE
═══════════════════════════════════════════════════════

Default guidance is for India unless location specifies otherwise.

INDIA SUPPLEMENT BRANDS (preference order):
- General: Thorne, Himalayan Organics, Miduty, Wellbeing Nutrition, Carbamide Forte, Now Foods, Jarrow, Solgar
- Ayurvedic: Kottakkal, Organic India, Kerala Ayurveda, Baidyanath
- Testing: Thyrocare, SRL Diagnostics, Apollo Diagnostics, Redcliffe Labs

"""

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

    goals = db_get("goals", user_id)
    if goals:
        base += "\n\nGOALS:\n"
        for g in goals:
            tf = f" [{g['timeframe']}]" if g.get("timeframe") else ""
            base += f"- {g['goal']}{tf}\n"

    conditions = db_get("medical_history", user_id)
    if conditions:
        base += "\nMEDICAL CONDITIONS:\n"
        for c in conditions:
            base += f"- {c['condition']}: {c.get('notes','')}\n"

    meds = db_get("medications", user_id)
    active_meds = [m for m in meds if m.get("active", True)] if meds else []
    if active_meds:
        base += "\nCURRENT MEDICATIONS:\n"
        for m in active_meds:
            base += f"- {m['name']} {m.get('dose','')} {m.get('frequency','')}\n"

    supps = db_get("supplements", user_id)
    active_supps = [s for s in supps if s.get("active", True)] if supps else []
    if active_supps:
        base += "\nCURRENT SUPPLEMENTS:\n"
        for s in active_supps:
            base += f"- {s['name']} {s.get('dose','')} ({s.get('timing','')})\n"

    notes = db_get_single("profile_notes", user_id)
    if notes and notes.get("notes"):
        base += f"\nPROFILE UPDATES / RECENT CHANGES:\n{notes['notes']}\n"

    labs = db_get("lab_reports", user_id, order_col="report_date", limit=10)
    if labs:
        base += "\n═══════════════════════════════════════════════════════\nLAB REPORTS\n═══════════════════════════════════════════════════════\n"
        current_labs = []
        historical_labs = []
        for l in labs:
            try:
                rep_date = date.fromisoformat(l.get("report_date",""))
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
            base += "⚠️ NO CURRENT LABS (all reports older than 3 months). Flag this to the patient.\n"
        if historical_labs:
            base += "\nHISTORICAL LABS (older than 3 months — trend analysis only):\n"
            for l in historical_labs:
                base += f"- {l.get('report_date','')}: {l.get('summary','')}\n"
    else:
        base += "\n⚠️ NO LAB REPORTS UPLOADED. Recommendations will be general until labs are provided.\n"

    wearable_all = db_get("wearable_data", user_id, order_col="data_date", limit=90)
    if wearable_all:
        base += "\n═══════════════════════════════════════════════════════\nWEARABLE DATA\n═══════════════════════════════════════════════════════\n"
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=30)
        ninety_days_ago = today - timedelta(days=90)
        current_w, recent_w, trend_w = [], [], []
        for w in wearable_all:
            try:
                wd = date.fromisoformat(w.get("data_date",""))
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
            def avg_field(rows, field):
                vals = [float(r[field]) for r in rows if r.get(field) is not None]
                return round(statistics.mean(vals), 1) if vals else None
            r_avg = {f: avg_field(recent_w, f) for f in ["recovery_score","hrv","resting_hr","strain","sleep_performance"]}
            r_str = " | ".join([f"{k.replace('_',' ')}: {v}" for k, v in r_avg.items() if v is not None])
            base += f"RECENT AVERAGE (last 30 days, {len(recent_w)} days of data): {r_str}\n"
        if not current_w and not recent_w:
            base += "⚠️ No recent wearable data.\n"

    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=14)
    if checkins:
        latest_checkin = checkins[0]
        try:
            latest_date = date.fromisoformat(latest_checkin.get("checkin_date",""))
            gap_days = (today - latest_date).days
        except:
            gap_days = 0
        base += "\n═══════════════════════════════════════════════════════\nCHECK-IN DATA\n═══════════════════════════════════════════════════════\n"
        if gap_days >= 14:
            base += f"⚠️ GAP ALERT: Last check-in was {gap_days} days ago. Do NOT continue with the old protocol. First ask a re-entry question.\n"
        elif gap_days >= 7:
            base += f"⚠️ CHECK-IN GAP: {gap_days} days since last log. Ask if anything changed.\n"
        elif gap_days >= 3:
            base += f"Note: {gap_days}-day gap in check-ins. Continue with protocol but note the gap.\n"
        base += f"RECENT CHECK-INS (last 14 days):\n"
        for c in reversed(checkins[:14]):
            base += f"- {c.get('checkin_date','')}: Energy {c.get('energy','?')}/10 · Mood {c.get('mood','?')}/10 · Sleep {c.get('sleep_hours','?')}hrs (quality {c.get('sleep_quality','?')}/10) · Bloating: {c.get('bloating','?')} · Digestion: {c.get('digestion','?')} · Workout: {c.get('workout','?')} · Notes: {c.get('notes','')}\n"
    else:
        base += "\nNo check-in data yet.\n"

    return base
# ── Auth Screen ───────────────────────────────────────────────────────────────

def show_auth():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    mode = st.session_state.get("auth_mode", "login")

    if mode == "reset":
        show_password_reset()
        return

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(f'<div style="text-align:center;margin-top:60px;">{mark_svg(46, dark=True)}</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-family:Newsreader,serif;font-size:22px;color:#F7F5F2;margin:12px 0 2px;">OneSattva</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-family:Newsreader,serif;font-style:italic;font-size:13px;color:#B6744A;margin-bottom:24px;">Health, understood.</div>', unsafe_allow_html=True)

        if mode == "login":
            with st.container():
                st.markdown('<div style="background:#F7F5F2;border-radius:16px;padding:32px 28px;box-shadow:0 8px 32px rgba(0,0,0,0.3);">', unsafe_allow_html=True)
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                if st.button("Forgot password?", type="tertiary"):
                    st.session_state["auth_mode"] = "reset"
                    st.rerun()
                if st.button("Sign in", type="primary", use_container_width=True):
                    if email and password:
                        user, session, err = sign_in(email, password)
                        if err:
                            st.error(err)
                        else:
                            st.session_state["user"] = user
                            st.session_state["session"] = session
                            st.rerun()
                    else:
                        st.warning("Please enter email and password.")
                st.markdown('</div>', unsafe_allow_html=True)
                if st.button("New to OneSattva? Create an account →", type="tertiary", use_container_width=True):
                    st.session_state["auth_mode"] = "signup"
                    st.rerun()

        elif mode == "signup":
            with st.container():
                st.markdown('<div style="background:#F7F5F2;border-radius:16px;padding:32px 28px;box-shadow:0 8px 32px rgba(0,0,0,0.3);">', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    first_name = st.text_input("First name", key="su_first")
                with c2:
                    last_name = st.text_input("Last name", key="su_last")
                email = st.text_input("Email", key="su_email")
                password = st.text_input("Create password", type="password", key="su_pass", help="Minimum 8 characters")
                st.divider()
                tos = st.checkbox("I agree to the **Terms of Service** and **Privacy Policy**", key="su_tos")
                health_consent = st.checkbox("I explicitly consent to OneSattva collecting, storing, and processing my personal health data — including lab results, wearable data, and symptom logs — solely for personalised health coaching.", key="su_health")
                if st.button("Create account →", type="primary", use_container_width=True):
                    if not first_name or not last_name:
                        st.error("Please enter your full name.")
                    elif not email:
                        st.error("Please enter your email.")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters.")
                    elif not tos:
                        st.error("You must agree to the Terms of Service and Privacy Policy.")
                    elif not health_consent:
                        st.error("You must consent to health data processing to use OneSattva.")
                    else:
                        full_name = f"{first_name} {last_name}"
                        user, err = sign_up(email, password, full_name)
                        if err:
                            st.error(err)
                        else:
                            st.success("Account created! Please check your email to verify, then sign in.")
                st.markdown('</div>', unsafe_allow_html=True)
                if st.button("Already have an account? Sign in", type="tertiary", use_container_width=True):
                    st.session_state["auth_mode"] = "login"
                    st.rerun()

def show_password_reset():
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(f'<div style="text-align:center;margin-top:60px;">{mark_svg(38, dark=True)}</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-family:Newsreader,serif;font-size:22px;color:#F7F5F2;margin:12px 0 20px;">Reset password</div>', unsafe_allow_html=True)
        st.markdown('<div style="background:#F7F5F2;border-radius:16px;padding:32px 28px;box-shadow:0 8px 32px rgba(0,0,0,0.3);">', unsafe_allow_html=True)
        email = st.text_input("Email", key="reset_email")
        if st.button("Send reset link", type="primary", use_container_width=True):
            if email:
                try:
                    supabase.auth.reset_password_email(email, {"redirect_to": "https://wellness-coach-app-f2ssjkdxdey8vm2c287mnz.streamlit.app"})
                    st.success("Reset link sent! Check your email.")
                except Exception as e:
                    st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("← Back to sign in", type="tertiary"):
            st.session_state["auth_mode"] = "login"
            st.rerun()
# ── Onboarding ────────────────────────────────────────────────────────────────

PLAN_MODES = [
    {"name": "Reset", "duration": "30 days", "subtitle": "Foundation · 1 month", "desc": "Break a pattern. Build a baseline. Understand your body for the first time. The coach is investigative — high-frequency check-ins, establishing rhythms, calibrating your picture."},
    {"name": "Restore", "duration": "90 days", "subtitle": "Active correction · 3 months", "desc": "Address a specific deficit or condition actively. The minimum meaningful intervention window in functional medicine. Labs should reflect measurable change by the end of this mode."},
    {"name": "Transform", "duration": "6 months", "subtitle": "Systemic change · 6 months", "desc": "Multiple systems shifting simultaneously. Sustainable habit formation and deeper pattern resolution. The coach reasons across functional medicine, Ayurveda, and TCM together."},
    {"name": "Sustain", "duration": "Ongoing", "subtitle": "Long-term partner · 12m+", "desc": "Acute issues resolved. Long-term optimisation and longevity. The coach references years of history. No fixed end — the horizon keeps extending as you evolve."},
]

def onboarding_progress(current_step):
    steps = ["Your plan", "About you", "Health history", "Lifestyle & goals", "Data sources"]
    html = '<div class="ob-progress">'
    for i, s in enumerate(steps):
        cls = "ob-dot"
        if i + 1 == current_step:
            cls += " active"
        elif i + 1 < current_step:
            cls += " done"
        html += f'<div class="{cls}"><div class="ob-dot-circle"></div>{s}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def show_onboarding(user_id, profile):
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    ob_state = get_onboarding_state(user_id)
    step = st.session_state.get("ob_step", ob_state.get("current_step", 1) if ob_state else 1)

    if step <= 5:
        onboarding_progress(step)

    tip_texts = {
        1: "Your plan mode shapes how your coach works — frequency, depth, and timeline. You can change it anytime.",
        2: "We use your demographics to calibrate recommendations — supplement doses, nutrition targets, and metabolic calculations.",
        3: "Medical history helps your coach avoid contraindications and understand your baseline.",
        4: "Lifestyle context lets your coach give specific, practical advice that fits your actual day.",
        5: "Lab data and wearable data give your coach hard numbers to work with. Both are optional but highly recommended."
    }

    if step <= 5:
        main_col, tip_col = st.columns([10, 3])
    else:
        main_col = st.container()
        tip_col = None

    with main_col:
        if step == 1:
            onboarding_step1(user_id, ob_state)
        elif step == 2:
            onboarding_step2(user_id, profile)
        elif step == 3:
            onboarding_step3(user_id)
        elif step == 4:
            onboarding_step4(user_id, profile)
        elif step == 5:
            onboarding_step5(user_id)
        elif step == 6:
            onboarding_step6(user_id, profile, ob_state)

    if tip_col and step <= 5:
        with tip_col:
            st.markdown(f"""<div style="background:var(--cu-bg);border:1px solid var(--cu-bd);border-radius:10px;padding:14px 16px;margin-top:40px;">
<div style="font-size:10px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:var(--copper);margin-bottom:6px;">Tip</div>
<div style="font-size:12px;color:var(--mid);line-height:1.5;">{tip_texts.get(step, "")}</div>
</div>""", unsafe_allow_html=True)

def onboarding_step1(user_id, ob_state):
    st.markdown('<div class="pg-title">What are you here for?</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Choose your plan mode. This shapes how your coach works with you. You can change it at any time from Profile & Data — your data always carries forward.</div>', unsafe_allow_html=True)

    selected = st.session_state.get("selected_plan_mode", ob_state.get("plan_mode") if ob_state else None)

    c1, c2 = st.columns(2)
    for i, mode in enumerate(PLAN_MODES):
        col = c1 if i % 2 == 0 else c2
        with col:
            border = "var(--graphite)" if selected == mode["name"] else "var(--line)"
            check = ' <span style="color:var(--copper);float:right;">✓</span>' if selected == mode["name"] else ""
            st.markdown(f"""<div style="background:var(--white);border:2px solid {border};border-radius:12px;padding:16px;margin-bottom:10px;">
<div class="mode-dur">{mode["duration"]}{check}</div>
<div class="mode-name">{mode["name"]}</div>
<div class="mode-sub">{mode["subtitle"]}</div>
<div class="mode-desc">{mode["desc"]}</div>
</div>""", unsafe_allow_html=True)
            if st.button(f"Select {mode['name']}", key=f"sel_{mode['name']}", use_container_width=True):
                st.session_state["selected_plan_mode"] = mode["name"]
                st.rerun()

    if st.button("Continue →", type="primary"):
        if not st.session_state.get("selected_plan_mode"):
            st.error("Please select a plan mode.")
        else:
            save_onboarding_state(user_id, {"current_step": 2, "plan_mode": st.session_state["selected_plan_mode"]})
            st.session_state["ob_step"] = 2
            st.rerun()

def onboarding_step2(user_id, profile):
    st.markdown('<div class="pg-title">Tell us about yourself</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Basic information to calibrate your coaching.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        dob = st.date_input("Date of birth", value=None, min_value=date(1930,1,1), max_value=date.today(), key="ob_dob")
        location = st.text_input("Location", value=profile.get("location","") if profile else "", key="ob_location")
        height = st.number_input("Height (cm)", min_value=100, max_value=250, value=int(profile.get("height_cm", 165)) if profile and profile.get("height_cm") else 165, key="ob_height")
        weight = st.number_input("Weight (kg)", min_value=30, max_value=200, value=int(profile.get("weight_kg", 65)) if profile and profile.get("weight_kg") else 65, key="ob_weight")
    with c2:
        sex_options = ["Female", "Male", "Prefer not to say"]
        sex = st.selectbox("Biological sex", sex_options, key="ob_sex")
        blood_group = st.selectbox("Blood group", ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], key="ob_blood")
        diet = st.selectbox("Eating pattern", ["Vegetarian", "Non-vegetarian", "Vegan", "Eggetarian", "Pescatarian", "Flexitarian"], key="ob_diet")
        occupation = st.text_input("Occupation (optional)", key="ob_occupation")

    if sex == "Female":
        st.info("Cycle tracking available. OneSattva can calibrate nutrition, supplements, and movement to your cycle phase.")

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("← Back"):
            st.session_state["ob_step"] = 1
            st.rerun()
    with bc2:
        if st.button("Continue →", type="primary"):
            age = None
            if dob:
                age = (date.today() - dob).days // 365
            update_data = {
                "id": user_id,
                "date_of_birth": dob.isoformat() if dob else None,
                "age": age,
                "location": location,
                "height_cm": height,
                "weight_kg": weight,
                "sex": sex,
                "blood_group": blood_group,
                "diet": diet,
                "occupation": occupation,
            }
            db_upsert("profiles", update_data)
            save_onboarding_state(user_id, {"current_step": 3})
            st.session_state["ob_step"] = 3
            st.rerun()

def onboarding_step3(user_id):
    st.markdown('<div class="pg-title">Your health history</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Current conditions, medications, and supplements.</div>', unsafe_allow_html=True)

    # Conditions
    st.markdown('<p class="ci-lbl">Diagnosed conditions</p>', unsafe_allow_html=True)
    if "ob_conditions" not in st.session_state:
        existing = db_get("medical_history", user_id)
        st.session_state["ob_conditions"] = existing if existing else [{"condition": "", "notes": ""}]

    conditions_to_delete = []
    for i, cond in enumerate(st.session_state["ob_conditions"]):
        cc1, cc2, cc3 = st.columns([4, 4, 1])
        with cc1:
            st.session_state["ob_conditions"][i]["condition"] = st.text_input("Condition", value=cond.get("condition",""), key=f"cond_{i}")
        with cc2:
            st.session_state["ob_conditions"][i]["notes"] = st.text_input("Since / notes", value=cond.get("notes",""), key=f"cond_n_{i}")
        with cc3:
            if st.button("✕", key=f"del_cond_{i}"):
                conditions_to_delete.append(i)
    for i in reversed(conditions_to_delete):
        st.session_state["ob_conditions"].pop(i)
        st.rerun()
    if st.button("+ Add condition"):
        st.session_state["ob_conditions"].append({"condition": "", "notes": ""})
        st.rerun()

    # Medications
    st.markdown('<p class="ci-lbl">Current medications</p>', unsafe_allow_html=True)
    if "ob_medications" not in st.session_state:
        existing = db_get("medications", user_id)
        st.session_state["ob_medications"] = existing if existing else [{"name": "", "dose": "", "frequency": ""}]

    meds_to_delete = []
    for i, med in enumerate(st.session_state["ob_medications"]):
        mc1, mc2, mc3, mc4 = st.columns([3, 3, 3, 1])
        with mc1:
            st.session_state["ob_medications"][i]["name"] = st.text_input("Medication", value=med.get("name",""), key=f"med_{i}")
        with mc2:
            st.session_state["ob_medications"][i]["dose"] = st.text_input("Dose", value=med.get("dose",""), key=f"med_d_{i}")
        with mc3:
            st.session_state["ob_medications"][i]["frequency"] = st.text_input("Timing", value=med.get("frequency",""), key=f"med_t_{i}")
        with mc4:
            if st.button("✕", key=f"del_med_{i}"):
                meds_to_delete.append(i)
    for i in reversed(meds_to_delete):
        st.session_state["ob_medications"].pop(i)
        st.rerun()
    if st.button("+ Add medication"):
        st.session_state["ob_medications"].append({"name": "", "dose": "", "frequency": ""})
        st.rerun()

    # Supplements
    st.markdown('<p class="ci-lbl">Current supplements</p>', unsafe_allow_html=True)
    if "ob_supplements" not in st.session_state:
        existing = db_get("supplements", user_id)
        st.session_state["ob_supplements"] = existing if existing else [{"name": "", "dose": "", "timing": ""}]

    supps_to_delete = []
    for i, supp in enumerate(st.session_state["ob_supplements"]):
        sc1, sc2, sc3, sc4 = st.columns([3, 3, 3, 1])
        with sc1:
            st.session_state["ob_supplements"][i]["name"] = st.text_input("Supplement", value=supp.get("name",""), key=f"sup_{i}")
        with sc2:
            st.session_state["ob_supplements"][i]["dose"] = st.text_input("Dose", value=supp.get("dose",""), key=f"sup_d_{i}")
        with sc3:
            st.session_state["ob_supplements"][i]["timing"] = st.text_input("Timing", value=supp.get("timing",""), key=f"sup_t_{i}")
        with sc4:
            if st.button("✕", key=f"del_sup_{i}"):
                supps_to_delete.append(i)
    for i in reversed(supps_to_delete):
        st.session_state["ob_supplements"].pop(i)
        st.rerun()
    if st.button("+ Add supplement"):
        st.session_state["ob_supplements"].append({"name": "", "dose": "", "timing": ""})
        st.rerun()

    # Family history + past events
    st.markdown('<p class="ci-lbl">Additional history</p>', unsafe_allow_html=True)
    family_history = st.text_area("Family history (optional)", key="ob_family_history")
    past_events = st.text_area("Past surgeries or significant events (optional)", key="ob_past_events")

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("← Back"):
            st.session_state["ob_step"] = 2
            st.rerun()
    with bc2:
        if st.button("Continue →", type="primary"):
            # Save conditions
            for c in st.session_state["ob_conditions"]:
                if c.get("condition"):
                    db_upsert("medical_history", {"user_id": user_id, "condition": c["condition"], "notes": c.get("notes","")})
            # Save medications
            for m in st.session_state["ob_medications"]:
                if m.get("name"):
                    db_upsert("medications", {"user_id": user_id, "name": m["name"], "dose": m.get("dose",""), "frequency": m.get("frequency",""), "active": True})
            # Save supplements
            for s in st.session_state["ob_supplements"]:
                if s.get("name"):
                    db_upsert("supplements", {"user_id": user_id, "name": s["name"], "dose": s.get("dose",""), "timing": s.get("timing",""), "active": True})
            # Save notes
            notes_text = ""
            if family_history:
                notes_text += f"Family history: {family_history}\n"
            if past_events:
                notes_text += f"Past events: {past_events}\n"
            if notes_text:
                db_upsert("profile_notes", {"user_id": user_id, "notes": notes_text})
            save_onboarding_state(user_id, {"current_step": 4})
            st.session_state["ob_step"] = 4
            st.rerun()
def onboarding_step4(user_id, profile):
    st.markdown('<div class="pg-title">Your lifestyle and goals</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Help your coach understand your daily patterns and what you want to achieve.</div>', unsafe_allow_html=True)

    # Primary health goal
    st.markdown('<p class="ci-lbl">Primary health goal</p>', unsafe_allow_html=True)
    primary_goal = st.text_area("What is your main health goal?", height=100, key="ob_primary_goal")

    # Diet & activity
    st.markdown('<p class="ci-lbl">Diet & activity</p>', unsafe_allow_html=True)
    da1, da2 = st.columns(2)
    with da1:
        eating_pattern = st.selectbox("Eating pattern", ["Vegetarian", "Non-vegetarian", "Vegan", "Eggetarian", "Pescatarian", "Flexitarian"], key="ob_eat_pattern")
        activity_level = st.selectbox("Activity level", ["Sedentary", "Lightly active", "Moderately active", "Very active", "Athlete"], key="ob_activity")
        dietary_restrictions = st.text_input("Dietary restrictions / allergies", key="ob_restrictions")
    with da2:
        alcohol = st.selectbox("Alcohol consumption", ["None", "Occasional (1-2/week)", "Moderate (3-5/week)", "Regular (daily)"], key="ob_alcohol")
        smoking = st.selectbox("Smoking", ["None", "Occasional", "Regular", "Former smoker"], key="ob_smoking")
        exercise_routine = st.text_input("Current exercise routine", key="ob_exercise")

    # Sleep
    st.markdown('<p class="ci-lbl">Sleep</p>', unsafe_allow_html=True)
    sl1, sl2 = st.columns(2)
    with sl1:
        bedtime = st.text_input("Typical bedtime", value="22:30", key="ob_bedtime")
        wake_time = st.text_input("Typical wake time", value="06:30", key="ob_waketime")
        sleep_duration = st.number_input("Average sleep duration (hours)", min_value=3.0, max_value=12.0, value=7.0, step=0.5, key="ob_sleep_dur")
    with sl2:
        sleep_quality = st.slider("Sleep quality", 1, 10, 6, key="ob_sleep_qual")
        sleep_challenges = st.text_area("Sleep challenges", key="ob_sleep_challenges")

    # Eating schedule
    st.markdown('<p class="ci-lbl">Eating schedule & patterns</p>', unsafe_allow_html=True)
    es1, es2 = st.columns(2)
    with es1:
        first_meal = st.text_input("First meal time", value="08:00", key="ob_first_meal")
        last_meal = st.text_input("Last meal time", value="20:00", key="ob_last_meal")
        meals_per_day = st.selectbox("Meals per day", ["2", "3", "4", "5+"], key="ob_meals")
    with es2:
        eating_out = st.selectbox("Eating out frequency", ["Rarely", "1-2 times/week", "3-4 times/week", "Daily"], key="ob_eating_out")
        food_prefs = st.text_area("Food preferences", key="ob_food_prefs")

    # Stress & wellbeing
    st.markdown('<p class="ci-lbl">Stress & wellbeing</p>', unsafe_allow_html=True)
    sw1, sw2 = st.columns(2)
    with sw1:
        stress_level = st.slider("Current stress level", 1, 10, 5, key="ob_stress")
        stressors = st.text_input("Primary stressors", key="ob_stressors")
    with sw2:
        symptoms = st.text_area("Current symptoms or main concerns", key="ob_symptoms")
        anything_else = st.text_area("Anything else your coach should know", key="ob_anything")

    # Additional goals
    st.markdown('<p class="ci-lbl">Additional goals</p>', unsafe_allow_html=True)
    if "ob_extra_goals" not in st.session_state:
        st.session_state["ob_extra_goals"] = []
    for i, g in enumerate(st.session_state["ob_extra_goals"]):
        gc1, gc2, gc3 = st.columns([5, 3, 1])
        with gc1:
            st.session_state["ob_extra_goals"][i]["goal"] = st.text_input("Goal", value=g.get("goal",""), key=f"eg_{i}")
        with gc2:
            st.session_state["ob_extra_goals"][i]["timeframe"] = st.selectbox("Timeframe", ["1 month", "3 months", "6 months", "12 months", "Ongoing"], key=f"eg_tf_{i}")
        with gc3:
            if st.button("✕", key=f"del_eg_{i}"):
                st.session_state["ob_extra_goals"].pop(i)
                st.rerun()
    ag1, ag2 = st.columns([4, 1])
    with ag1:
        new_goal = st.text_input("Add a goal", key="ob_new_goal")
    with ag2:
        new_tf = st.selectbox("Timeframe", ["3 months", "1 month", "6 months", "12 months", "Ongoing"], key="ob_new_tf")
    if st.button("+ Add goal"):
        if new_goal:
            st.session_state["ob_extra_goals"].append({"goal": new_goal, "timeframe": new_tf})
            st.rerun()

    # Cycle tracking for females
    sex = profile.get("sex") if profile else None
    if sex == "Female":
        st.markdown('<p class="ci-lbl">Cycle tracking</p>', unsafe_allow_html=True)
        cy1, cy2 = st.columns(2)
        with cy1:
            last_period = st.date_input("Last period start date", value=None, key="ob_last_period")
        with cy2:
            avg_cycle = st.number_input("Average cycle length (days)", min_value=20, max_value=40, value=28, key="ob_avg_cycle")

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("← Back"):
            st.session_state["ob_step"] = 3
            st.rerun()
    with bc2:
        if st.button("Continue →", type="primary"):
            # Save profile lifestyle data
            profile_update = {
                "id": user_id,
                "diet": eating_pattern,
                "activity_level": activity_level,
                "allergies": dietary_restrictions,
                "alcohol": alcohol,
                "smoking": smoking,
                "exercise_routine": exercise_routine,
                "sleep_time": bedtime,
                "wake_time": wake_time,
                "avg_sleep_hours": sleep_duration,
            }
            db_upsert("profiles", profile_update)

            # Save lifestyle notes
            lifestyle_notes = []
            if sleep_challenges: lifestyle_notes.append(f"Sleep challenges: {sleep_challenges}")
            if stressors: lifestyle_notes.append(f"Primary stressors: {stressors}")
            if symptoms: lifestyle_notes.append(f"Current symptoms: {symptoms}")
            if anything_else: lifestyle_notes.append(f"Additional notes: {anything_else}")
            if food_prefs: lifestyle_notes.append(f"Food preferences: {food_prefs}")
            if exercise_routine: lifestyle_notes.append(f"Exercise routine: {exercise_routine}")

            existing_notes = db_get_single("profile_notes", user_id)
            old_notes = existing_notes.get("notes", "") if existing_notes else ""
            combined = old_notes + "\n" + "\n".join(lifestyle_notes) if old_notes else "\n".join(lifestyle_notes)
            db_upsert("profile_notes", {"user_id": user_id, "notes": combined})

            # Save primary goal
            if primary_goal:
                db_insert("goals", {"user_id": user_id, "goal": primary_goal, "timeframe": "Primary"})
            for g in st.session_state.get("ob_extra_goals", []):
                if g.get("goal"):
                    db_insert("goals", {"user_id": user_id, "goal": g["goal"], "timeframe": g.get("timeframe","")})

            # Save cycle data
            if sex == "Female" and st.session_state.get("ob_last_period"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": st.session_state["ob_last_period"].isoformat(), "avg_cycle_length": avg_cycle})

            save_onboarding_state(user_id, {"current_step": 5})
            st.session_state["ob_step"] = 5
            st.rerun()

def onboarding_step5(user_id):
    st.markdown('<div class="pg-title">Connect your data</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Both optional. You can upload lab reports or connect wearable data at any time from Profile & Data inside the app.</div>', unsafe_allow_html=True)

    # Lab Reports card
    labs_exist = len(db_get("lab_reports", user_id)) > 0
    lab_status = "✓ Lab report uploaded" if labs_exist else "Not yet uploaded"
    st.markdown(f"""<div style="background:var(--white);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:10px;">
<div style="font-size:16px;margin-bottom:4px;">🧪 <b>Lab Reports</b></div>
<div style="font-size:12px;color:var(--mid);line-height:1.5;margin-bottom:8px;">Upload PDF lab reports from any Indian or international diagnostic lab. OneSattva reads and interprets them against functional ranges — not conventional population reference ranges.</div>
<div style="font-size:12px;color:{'#3A6B4A' if labs_exist else 'var(--mid)'};">{lab_status}</div>
</div>""", unsafe_allow_html=True)

    # WHOOP card
    whoop_exist = len(db_get("wearable_data", user_id, limit=1)) > 0
    whoop_status = "✓ WHOOP data imported" if whoop_exist else "Not yet connected"
    st.markdown(f"""<div style="background:var(--white);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:10px;">
<div style="font-size:16px;margin-bottom:4px;">⌚ <b>WHOOP</b></div>
<div style="font-size:12px;color:var(--mid);line-height:1.5;margin-bottom:8px;">Export 4 CSV files from your WHOOP dashboard and upload them here.</div>
<div style="font-size:12px;color:{'#3A6B4A' if whoop_exist else 'var(--mid)'};">{whoop_status}</div>
</div>""", unsafe_allow_html=True)

    # Other wearables
    st.markdown("""<div style="background:var(--white);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:10px;opacity:0.6;">
<div style="font-size:16px;margin-bottom:4px;">🍎 <b>Other wearables</b></div>
<div style="font-size:12px;color:var(--mid);line-height:1.5;">Oura Ring, Garmin, Apple Watch, and others</div>
<div style="font-size:12px;color:var(--mid);font-style:italic;">Coming soon — join waitlist</div>
</div>""", unsafe_allow_html=True)

    st.caption("Your data is encrypted and stored securely. Used solely to personalise your coaching. Never sold or shared with third parties.")

    # Lab upload expandable
    with st.expander("Paste lab values to analyse & save"):
        st.markdown(f"<details><summary>Recommended markers</summary>{MARKERS_INFO}</details>", unsafe_allow_html=True)
        lab_date = st.date_input("Report date", value=date.today(), key="ob_lab_date")
        lab_name = st.text_input("Lab name (e.g. Thyrocare, SRL)", key="ob_lab_name")
        lab_values = st.text_area("Paste your lab values here", height=150, key="ob_lab_values")
        if st.button("🔍 Analyse & Save Report"):
            if lab_values:
                with st.spinner("Analysing lab values..."):
                    analysis = ai_generate(
                        "You are a functional medicine lab analyst. Analyse these lab values against functional (not conventional) reference ranges. Flag anything outside functional ranges. Be specific about what each value means clinically.",
                        f"Lab report from {lab_name} dated {lab_date}:\n\n{lab_values}"
                    )
                    db_insert("lab_reports", {
                        "user_id": user_id,
                        "report_date": lab_date.isoformat(),
                        "lab_name": lab_name,
                        "raw_values": lab_values,
                        "summary": analysis[:500],
                        "analysis": analysis,
                        "source": "manual_entry"
                    })
                    st.success("Lab report saved!")
                    st.markdown(analysis)

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("← Back"):
            st.session_state["ob_step"] = 4
            st.rerun()
    with bc2:
        btn_label = "Build my roadmap →" if labs_exist else "I'll upload labs later — continue"
        if st.button(btn_label, type="primary"):
            save_onboarding_state(user_id, {"current_step": 6})
            st.session_state["ob_step"] = 6
            st.rerun()
def onboarding_step6(user_id, profile, ob_state):
    plan_mode = ob_state.get("plan_mode", "Restore") if ob_state else "Restore"
    duration_map = {"Reset": "30 days", "Restore": "90 days", "Transform": "6 months", "Sustain": "Ongoing"}
    duration = duration_map.get(plan_mode, "90 days")
    first_name = (profile.get("full_name") or "").split()[0] if profile else "there"
    today_str = date.today().strftime("%d %B %Y")

    # Check if roadmap already generated
    existing_roadmap = st.session_state.get("generated_roadmap")
    if not existing_roadmap:
        # Check DB
        roadmaps = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
        if roadmaps and roadmaps[0].get("roadmap_text"):
            existing_roadmap = roadmaps[0]["roadmap_text"]
            st.session_state["generated_roadmap"] = existing_roadmap
            st.session_state["roadmap_id"] = roadmaps[0].get("id")

    if not existing_roadmap:
        # S9 — Generating screen
        st.markdown(f'<div style="text-align:center;margin:40px 0 20px;">{mark_svg(56)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center;font-family:Newsreader,serif;font-size:23px;color:var(--graphite);margin-bottom:8px;">Building your roadmap</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center;font-size:13px;color:var(--mid);max-width:500px;margin:0 auto 24px;line-height:1.6;">Your coach is reading your full profile — conditions, medications, labs, lifestyle — and building a phased programme tailored to your {plan_mode} plan.</div>', unsafe_allow_html=True)

        checklist = ["Reading your profile", "Analysing health history", "Reviewing lab data", "Building phase timeline", "Generating protocol"]
        for i, item in enumerate(checklist):
            icon = "✓" if i < 2 else ("◈" if i == 2 else "◦")
            st.markdown(f'<div style="text-align:center;font-size:13px;color:var(--mid);margin:4px 0;">{icon} {item}</div>', unsafe_allow_html=True)

        with st.spinner("Generating your roadmap..."):
            sys_prompt = build_system_prompt(user_id, profile)
            cycle_day, phase, _ = calculate_cycle_status(user_id)
            cycle_ctx = f"\nCycle: Day {cycle_day}, {phase}" if cycle_day else ""

            roadmap_prompt = f"""Generate a comprehensive {plan_mode} programme roadmap.

FORMAT:
## Your {plan_mode} Programme — Generated {today_str}
One sentence on what this programme addresses.

## Phase Timeline
Table: Phase | Focus | Key milestones | Checkpoint
[phases matching the plan duration — 4 phases for Restore, 2 for Reset, etc.]

## Phase 1 — [Title]: [weeks]
What changes. Specific supplements/nutrition/training with exact doses.
**Retest at checkpoint:** [markers]
**What success looks like:** [outcomes]

[Repeat per phase]

## If Phase 1 Shows No Progress
[Escalation]

**Start today:** [one immediate action]
{cycle_ctx}"""

            roadmap_text = ai_generate(sys_prompt, roadmap_prompt, max_tokens=4096)
            st.session_state["generated_roadmap"] = roadmap_text

            # Save draft to DB
            result = supabase.table("roadmaps").insert({
                "user_id": user_id,
                "roadmap_text": roadmap_text,
                "committed": False,
                "priority_focus": plan_mode,
                "intensity": "Standard",
                "generated_at": datetime.now().isoformat()
            }).execute()
            if result.data:
                st.session_state["roadmap_id"] = result.data[0]["id"]
            st.rerun()

    else:
        # S10 — Review screen
        st.markdown(f"""<div style="background:var(--forest);border-radius:12px;padding:20px 24px;margin-bottom:20px;">
<div style="font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:rgba(247,245,242,0.4);margin-bottom:6px;">Your personalised {plan_mode} programme · {duration} · Generated {today_str}</div>
<div style="font-family:Newsreader,serif;font-style:italic;font-size:18px;color:#F7F5F2;line-height:1.5;">Here's what OneSattva has built for you, {first_name}.</div>
<div style="font-size:12px;color:rgba(247,245,242,0.5);margin-top:6px;">Your roadmap is a living document. It recalibrates as new data comes in — labs, check-ins, and wearable metrics all feed back into your protocol.</div>
</div>""", unsafe_allow_html=True)

        st.markdown(existing_roadmap)

        st.markdown(f"""<div class="cp-banner" style="margin-top:20px;">
<div>
<div style="font-size:12px;font-weight:600;color:var(--copper);margin-bottom:4px;">What committing means</div>
<div style="font-size:12px;color:var(--mid);line-height:1.5;">Your roadmap locks in as your active plan. Your coach will reference it in every conversation. It recalibrates automatically when you upload new labs or submit check-ins — but the structure stays unless you explicitly update it from Protocol.</div>
</div>
</div>""", unsafe_allow_html=True)

        st.caption(f"Generated from your profile on {today_str}. A starting point — your coach refines this as more data comes in.")

        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("← Revise my inputs"):
                st.session_state["ob_step"] = 4
                st.rerun()
        with bc2:
            if st.button("Commit to this plan →", type="primary"):
                # Mark roadmap as committed
                if st.session_state.get("roadmap_id"):
                    supabase.table("roadmaps").update({"committed": True}).eq("id", st.session_state["roadmap_id"]).execute()
                # Mark onboarding complete
                db_upsert("profiles", {"id": user_id, "onboarding_complete": True})
                save_onboarding_state(user_id, {"current_step": 7, "completed": True})
                st.session_state["onboarding_complete"] = True
                st.rerun()
# ── Sidebar ───────────────────────────────────────────────────────────────────

def get_plan_info(user_id, profile):
    ob = get_onboarding_state(user_id)
    plan_mode = ob.get("plan_mode", "Restore") if ob else "Restore"
    duration_map = {"Reset": 30, "Restore": 90, "Transform": 180, "Sustain": 365}
    total_days = duration_map.get(plan_mode, 90)
    total_weeks = total_days // 7

    start_date_str = profile.get("plan_start_date") if profile else None
    if start_date_str:
        try:
            start = date.fromisoformat(start_date_str)
        except:
            start = date.today()
    else:
        start = date.today()

    elapsed = (date.today() - start).days
    current_week = max(1, elapsed // 7 + 1)
    if plan_mode != "Sustain":
        current_week = min(current_week, total_weeks)
    checkpoint_week = min(8, total_weeks)

    return plan_mode, total_weeks, current_week, checkpoint_week, start

def show_sidebar(user_id, profile):
    with st.sidebar:
        # Header
        st.markdown(f"""<div style="margin-bottom:16px;">
{mark_svg(22, dark=True)}
<span style="font-family:Newsreader,serif;font-size:19px;color:#F7F5F2;margin-left:8px;vertical-align:middle;">OneSattva</span>
<div class="sb-tag">Health, understood.</div>
</div>""", unsafe_allow_html=True)

        # User block
        name = profile.get("full_name", "User") if profile else "User"
        location = profile.get("location", "") if profile else ""
        age = profile.get("age", "") if profile else ""
        sex = profile.get("sex", "") if profile else ""
        meta_parts = [x for x in [location, f"{age}y" if age else "", sex] if x]
        meta = " · ".join(meta_parts)

        plan_mode, total_weeks, current_week, checkpoint_week, _ = get_plan_info(user_id, profile)

        st.markdown(f"""<div style="margin-bottom:14px;">
<div class="sb-name">{name}</div>
<div class="sb-meta">{meta}</div>
<div class="plan-pill">{plan_mode} · Wk {current_week} / {total_weeks}</div>
</div>""", unsafe_allow_html=True)

        # Nav
        st.markdown('<div style="font-size:10px;font-weight:600;letter-spacing:0.09em;text-transform:uppercase;color:rgba(247,245,242,0.24);margin:10px 0 6px;">Navigation</div>', unsafe_allow_html=True)

        nav_items = [
            ("⌂", "Home"),
            ("◈", "Protocol"),
            ("✓", "Check-In"),
            ("✦", "Coach"),
            ("◎", "Profile & Data"),
        ]
        current_page = st.session_state.get("page", "Home")
        for icon, label in nav_items:
            is_active = current_page == label
            bg = "rgba(182,116,74,0.11)" if is_active else "transparent"
            color = "#F7F5F2" if is_active else "rgba(247,245,242,0.55)"
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
                st.session_state["page"] = label
                st.rerun()

        # Divider
        st.markdown('<hr style="border:none;border-top:1px solid rgba(247,245,242,0.08);margin:12px 0;">', unsafe_allow_html=True)

        # Footer
        duration_label_map = {"Reset": "30-day", "Restore": "90-day", "Transform": "6-month", "Sustain": "Ongoing"}
        dur_label = duration_label_map.get(plan_mode, "90-day")
        st.markdown(f"""<div class="sb-foot-t">{plan_mode} · {dur_label} programme<br>Week {current_week} of {total_weeks} · Checkpoint Wk {checkpoint_week}</div>""", unsafe_allow_html=True)

        # Sign out
        if st.button("Sign out", key="sign_out"):
            sign_out()

# ── Home Page ─────────────────────────────────────────────────────────────────

def greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"

def show_home(user_id, profile):
    plan_mode, total_weeks, current_week, checkpoint_week, plan_start = get_plan_info(user_id, profile)
    first_name = (profile.get("full_name") or "").split()[0] if profile else "there"
    today = date.today()

    # Plan banner
    roadmaps = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
    committed_roadmap = roadmaps[0] if roadmaps and roadmaps[0].get("committed") else None

    if committed_roadmap:
        progress_pct = min(100, int((current_week / max(total_weeks, 1)) * 100))
        st.markdown(f"""<div class="plan-banner">
<div style="display:flex;justify-content:space-between;align-items:start;">
<div style="flex:1;">
<div style="font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:rgba(247,245,242,0.4);margin-bottom:4px;">Plan mode</div>
<div style="font-family:Newsreader,serif;font-style:italic;font-size:16px;color:#F7F5F2;margin-bottom:8px;">{plan_mode} programme</div>
<div style="background:rgba(247,245,242,0.15);border-radius:4px;height:4px;margin-bottom:4px;"><div style="background:var(--copper);border-radius:4px;height:4px;width:{progress_pct}%;"></div></div>
<div style="font-size:11px;color:rgba(247,245,242,0.5);">Wk {current_week} / {total_weeks}</div>
</div>
<div style="margin-left:20px;"><a href="#" style="font-size:12px;color:var(--copper);opacity:0.7;text-decoration:none;">View roadmap →</a></div>
</div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:var(--stone);border:2px dashed var(--linem);border-radius:10px;padding:20px;text-align:center;">
<div style="font-size:13px;color:var(--mid);">No active roadmap yet. Generate one from Protocol.</div>
</div>""", unsafe_allow_html=True)

    # Greeting
    st.markdown(f'<div class="pg-title">{greeting()}, {first_name}.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pg-sub">{today.strftime("%A, %d %B %Y")} · Here\'s what matters today.</div>', unsafe_allow_html=True)

    # Today's priorities
    st.markdown('<div class="sl first">Today\'s priorities</div>', unsafe_allow_html=True)

    if "home_priorities" not in st.session_state:
        with st.spinner("Generating today's priorities..."):
            sys_prompt = build_system_prompt(user_id, profile)
            cycle_day, phase, _ = calculate_cycle_status(user_id)
            roadmap_excerpt = committed_roadmap["roadmap_text"][:1000] if committed_roadmap else "No roadmap yet."
            labs = db_get("lab_reports", user_id, order_col="report_date", limit=1)
            lab_summary = labs[0].get("summary", "")[:300] if labs else "No labs."
            wearable = db_get("wearable_data", user_id, order_col="data_date", limit=1)
            w_summary = f"HRV: {wearable[0].get('hrv','?')}, Recovery: {wearable[0].get('recovery_score','?')}%" if wearable else "No wearable data."
            checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)
            ci_summary = f"Energy: {checkins[0].get('energy','?')}/10, Mood: {checkins[0].get('mood','?')}/10" if checkins else "No check-ins."
            cycle_ctx = f"Cycle Day {cycle_day}, {phase}" if cycle_day else "No cycle data."

            prio_prompt = f"""Based on this patient's data, generate exactly 3 priority cards for today.

Roadmap: {roadmap_excerpt}
Latest labs: {lab_summary}
Wearable: {w_summary}
Check-in: {ci_summary}
Cycle: {cycle_ctx}
Date: {today.strftime("%A, %d %B %Y")}

Return ONLY valid JSON array:
[
  {{"triage": "act_today", "title": "...", "body": "..."}},
  {{"triage": "watch", "title": "...", "body": "..."}},
  {{"triage": "background", "title": "...", "body": "..."}}
]"""
            try:
                result = ai_generate(sys_prompt, prio_prompt, max_tokens=800)
                match = re.search(r'\[.*\]', result, re.DOTALL)
                if match:
                    st.session_state["home_priorities"] = json.loads(match.group())
                else:
                    st.session_state["home_priorities"] = [
                        {"triage": "act_today", "title": "Log your check-in", "body": "Start tracking to build your baseline."},
                        {"triage": "watch", "title": "Review your protocol", "body": "Check Protocol tab for your weekly plan."},
                        {"triage": "background", "title": "Upload labs", "body": "More data means better coaching."},
                    ]
            except:
                st.session_state["home_priorities"] = [
                    {"triage": "act_today", "title": "Log your check-in", "body": "Start tracking to build your baseline."},
                    {"triage": "watch", "title": "Review your protocol", "body": "Check Protocol tab for your weekly plan."},
                    {"triage": "background", "title": "Upload labs", "body": "More data means better coaching."},
                ]

    priorities = st.session_state["home_priorities"]
    triage_class = {"act_today": "t-now", "watch": "t-watch", "background": "t-bg"}
    triage_label = {"act_today": "Act today", "watch": "Watch", "background": "Background"}
    cards_html = '<div class="prio-grid">'
    for p in priorities:
        tc = triage_class.get(p["triage"], "t-watch")
        tl = triage_label.get(p["triage"], "Watch")
        cards_html += f'<div class="prio-card"><div class="triage {tc}">{tl}</div><div class="pc-title">{p["title"]}</div><div class="pc-body">{p["body"]}</div></div>'
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

    # Today's snapshot
    st.markdown('<div class="sl">Today\'s snapshot</div>', unsafe_allow_html=True)
    wearable = db_get("wearable_data", user_id, order_col="data_date", limit=1)
    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)

    hrv_val = wearable[0].get("hrv", "—") if wearable else "—"
    recovery_val = f"{wearable[0].get('recovery_score', '—')}%" if wearable and wearable[0].get("recovery_score") else "—"
    sleep_val = f"{wearable[0].get('sleep_performance', '—')}%" if wearable and wearable[0].get("sleep_performance") else "—"
    energy_val = f"{checkins[0].get('energy', '—')}/10" if checkins and checkins[0].get("energy") else "—"

    w_source = f"WHOOP · {wearable[0].get('data_date','')}" if wearable else "No data"
    ci_source = f"Check-in · {checkins[0].get('checkin_date','')}" if checkins else "No data"

    st.markdown(f"""<div class="snap-grid">
<div class="snap-box"><div class="snap-lbl">HRV</div><div class="snap-val">{hrv_val}</div><div class="snap-sub">ms</div><div class="snap-sub">{w_source}</div></div>
<div class="snap-box"><div class="snap-lbl">Recovery</div><div class="snap-val">{recovery_val}</div><div class="snap-sub">{w_source}</div></div>
<div class="snap-box"><div class="snap-lbl">Sleep</div><div class="snap-val">{sleep_val}</div><div class="snap-sub">{w_source}</div></div>
<div class="snap-box"><div class="snap-lbl">Energy</div><div class="snap-val">{energy_val}</div><div class="snap-sub">{ci_source}</div></div>
</div>""", unsafe_allow_html=True)

    # Trends
    st.markdown('<div class="sl">Trends</div>', unsafe_allow_html=True)
    recent_checkins = db_get("checkins", user_id, order_col="checkin_date", limit=30)
    recent_wearable = db_get("wearable_data", user_id, order_col="data_date", limit=30)

    def make_bars(values, max_val=10):
        if not values:
            return '<div class="tc-bars"><div class="tb" style="height:50%;"></div></div>'
        bars = ""
        for v in values[-14:]:
            h = max(5, int((v / max(max_val, 1)) * 100))
            bars += f'<div class="tb" style="height:{h}%;"></div>'
        return f'<div class="tc-bars">{bars}</div>'

    energy_vals = [c.get("energy", 5) for c in reversed(recent_checkins) if c.get("energy")]
    sleep_vals = [c.get("sleep_quality", 5) for c in reversed(recent_checkins) if c.get("sleep_quality")]
    hrv_vals = [w.get("hrv", 50) for w in reversed(recent_wearable) if w.get("hrv")]

    energy_insight = f"Avg energy: {round(statistics.mean(energy_vals), 1)}/10 over {len(energy_vals)} days" if energy_vals else "No data yet"
    hrv_insight = f"Avg HRV: {round(statistics.mean(hrv_vals), 1)}ms over {len(hrv_vals)} days" if hrv_vals else "No data yet"

    st.markdown(f"""<div class="trends-grid">
<div class="trend-card">
<div class="tc-title">Energy vs Sleep quality · 30 days</div>
<div class="tc-insight">{energy_insight}</div>
{make_bars(energy_vals)}
</div>
<div class="trend-card">
<div class="tc-title">HRV trajectory · 30 days</div>
<div class="tc-insight">{hrv_insight}</div>
{make_bars(hrv_vals, max_val=150)}
</div>
</div>""", unsafe_allow_html=True)
# ── Protocol Page ─────────────────────────────────────────────────────────────

def show_protocol(user_id, profile):
    st.markdown('<div class="pg-title">Protocol</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Your personalised treatment plan, supplements, nutrition, and training.</div>', unsafe_allow_html=True)

    # Gap detection
    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)
    if checkins:
        try:
            latest_date = date.fromisoformat(checkins[0].get("checkin_date",""))
            gap_days = (date.today() - latest_date).days
        except:
            gap_days = 0

        if gap_days >= 14:
            st.markdown(f"""<div class="cp-banner" style="margin-bottom:16px;">
<div>
<div style="font-size:12px;font-weight:600;color:var(--copper);margin-bottom:4px;">It's been {gap_days} days since your last check-in</div>
<div style="font-size:12px;color:var(--mid);line-height:1.5;">A lot can change in {gap_days} days. Tell your coach what's different before generating this week's protocol.</div>
</div>
</div>""", unsafe_allow_html=True)
            reentry = st.text_area("What's changed in the last few weeks?", key="reentry_note")
            if st.button("Update my coach and continue"):
                if reentry:
                    existing = db_get_single("profile_notes", user_id)
                    old = existing.get("notes", "") if existing else ""
                    new_notes = old + f"\n\n[Re-entry {date.today().isoformat()}]: {reentry}"
                    db_upsert("profile_notes", {"user_id": user_id, "notes": new_notes})
                    for k in ["protocol_supplements", "protocol_nutrition", "protocol_workouts", "protocol_monthly"]:
                        st.session_state.pop(k, None)
                    st.rerun()
            return
        elif gap_days >= 7:
            st.info(f"It's been {gap_days} days since your last check-in. Has anything changed? If so, update your profile notes before generating this week's protocol.")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Treatment Roadmap", "Monthly Goal", "Supplements", "Nutrition", "Workouts"])

    with tab1:
        show_protocol_roadmap(user_id, profile)
    with tab2:
        show_protocol_monthly(user_id, profile)
    with tab3:
        show_protocol_supplements(user_id, profile)
    with tab4:
        show_protocol_nutrition(user_id, profile)
    with tab5:
        show_protocol_workouts(user_id, profile)

def show_protocol_roadmap(user_id, profile):
    roadmaps = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
    if not roadmaps:
        st.markdown("No roadmap yet.")
        focus = st.selectbox("Priority focus", ["Overall health", "Thyroid optimisation", "Gut healing", "Hormonal balance", "Energy & recovery", "Weight management"], key="rm_focus")
        intensity = st.selectbox("Change intensity", ["Standard", "Aggressive", "Conservative"], key="rm_intensity")
        if st.button("Generate My Treatment Roadmap", type="primary"):
            with st.spinner("Generating roadmap..."):
                sys_prompt = build_system_prompt(user_id, profile)
                ob = get_onboarding_state(user_id)
                plan_mode = ob.get("plan_mode", "Restore") if ob else "Restore"
                today_str = date.today().strftime("%d %B %Y")
                roadmap_text = ai_generate(sys_prompt, f"Generate a comprehensive {plan_mode} programme roadmap with focus on {focus} at {intensity} intensity.\n\nFORMAT:\n## Your {plan_mode} Programme — Generated {today_str}\n[full roadmap]", max_tokens=4096)
                supabase.table("roadmaps").insert({
                    "user_id": user_id, "roadmap_text": roadmap_text, "committed": False,
                    "priority_focus": focus, "intensity": intensity, "generated_at": datetime.now().isoformat()
                }).execute()
                st.rerun()
        return

    roadmap = roadmaps[0]
    if roadmap.get("committed"):
        st.success("Your roadmap is committed and active. Your coach references this in every conversation.")
        st.markdown(roadmap["roadmap_text"])
        st.download_button("Download roadmap", roadmap["roadmap_text"], file_name="onesattva_roadmap.md")

        with st.expander("Significant new information — update my roadmap"):
            reason = st.text_area("What has changed? (required)", key="rm_update_reason")
            if st.button("Update roadmap"):
                if reason:
                    with st.spinner("Regenerating..."):
                        sys_prompt = build_system_prompt(user_id, profile)
                        ob = get_onboarding_state(user_id)
                        plan_mode = ob.get("plan_mode", "Restore") if ob else "Restore"
                        new_text = ai_generate(sys_prompt, f"The patient's roadmap needs updating. Reason: {reason}\n\nRegenerate the {plan_mode} roadmap incorporating this change.", max_tokens=4096)
                        supabase.table("roadmaps").update({"roadmap_text": new_text, "committed": False, "generated_at": datetime.now().isoformat()}).eq("id", roadmap["id"]).execute()
                        st.rerun()
                else:
                    st.error("Please provide a reason for updating.")
    else:
        st.info("This roadmap is in draft. Review and commit when ready.")
        st.markdown(roadmap["roadmap_text"])
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("Commit to this roadmap", type="primary"):
                supabase.table("roadmaps").update({"committed": True}).eq("id", roadmap["id"]).execute()
                st.rerun()
        with bc2:
            if st.button("Regenerate instead"):
                supabase.table("roadmaps").delete().eq("id", roadmap["id"]).execute()
                st.rerun()

def show_protocol_monthly(user_id, profile):
    month_key = date.today().strftime("%Y-%m")
    cache_key = f"protocol_monthly_{month_key}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = None

    if not st.session_state[cache_key]:
        with st.spinner(f"Generating {date.today().strftime('%B')} overview..."):
            sys_prompt = build_system_prompt(user_id, profile)
            cycle_day, phase, _ = calculate_cycle_status(user_id)
            cycle_ctx = f"Cycle Day {cycle_day}, {phase}" if cycle_day else ""
            roadmaps = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
            roadmap_ctx = roadmaps[0]["roadmap_text"][:800] if roadmaps else ""
            prompt = f"""Generate a monthly overview for {date.today().strftime('%B %Y')}.

Roadmap context: {roadmap_ctx}
{cycle_ctx}

FORMAT:
## {date.today().strftime('%B %Y')} — Monthly Focus
One sentence focus.

### Milestones this month
Table: Week | Target | Metric

### What changes this month
Table: Area | This month | Why

### Monitoring
- Key markers to watch

### End-of-month check
What success looks like by month end."""
            result = ai_generate(sys_prompt, prompt, max_tokens=2000)
            st.session_state[cache_key] = result

    st.markdown(st.session_state[cache_key])
    if st.session_state[cache_key]:
        if st.button("↻ Regenerate", key="regen_monthly"):
            st.session_state[cache_key] = None
            st.rerun()

def show_protocol_supplements(user_id, profile):
    if "protocol_supplements" not in st.session_state:
        st.session_state["protocol_supplements"] = None

    if not st.session_state["protocol_supplements"]:
        if st.button("Generate Supplement Schedule", type="primary"):
            with st.spinner("Generating supplement schedule..."):
                sys_prompt = build_system_prompt(user_id, profile)
                cycle_day, phase, _ = calculate_cycle_status(user_id)
                cycle_ctx = f"Cycle Day {cycle_day}, {phase}" if cycle_day else ""
                prompt = f"""Generate a complete daily supplement schedule for this patient.

{cycle_ctx}

RULES:
- If Thyronorm/Levothyroxine is prescribed, it MUST be the first row at exact wake time, water only, 45-60 min before anything else
- Exact brand names available in India
- Exact doses with clinical reasoning
- Time-specific: wake, breakfast, lunch, dinner, bedtime

FORMAT: Markdown table with columns: Time | Supplement | Dose | Clinical notes"""
                result = ai_generate(sys_prompt, prompt, max_tokens=2000)
                st.session_state["protocol_supplements"] = result
                st.rerun()
    else:
        st.markdown(st.session_state["protocol_supplements"])
        adjust = st.text_input("Want to adjust anything?", key="supp_adjust")
        if st.button("↻ Regenerate with changes", key="regen_supps"):
            with st.spinner("Regenerating..."):
                sys_prompt = build_system_prompt(user_id, profile)
                extra = f"\n\nAdjustments requested: {adjust}" if adjust else ""
                result = ai_generate(sys_prompt, f"Regenerate the supplement schedule.{extra}", max_tokens=2000)
                st.session_state["protocol_supplements"] = result
                st.rerun()

def show_protocol_nutrition(user_id, profile):
    if "protocol_nutrition" not in st.session_state:
        st.session_state["protocol_nutrition"] = None

    if not st.session_state["protocol_nutrition"]:
        focus = st.selectbox("Priority focus", ["Balanced nutrition", "Gut healing", "Anti-inflammatory", "Energy optimisation", "Hormonal support", "Weight management"], key="nut_focus")
        if st.button("Generate Nutrition Plan", type="primary"):
            with st.spinner("Generating nutrition plan..."):
                sys_prompt = build_system_prompt(user_id, profile)
                cycle_day, phase, _ = calculate_cycle_status(user_id)
                cycle_ctx = f"Cycle Day {cycle_day}, {phase}" if cycle_day else ""
                prompt = f"Generate a 7-day nutrition plan with focus on {focus}. {cycle_ctx}\n\nFORMAT: Markdown table: Day | Breakfast | Lunch | Snack | Dinner | Notes\nInclude specific foods, portions, and preparation methods."
                result = ai_generate(sys_prompt, prompt, max_tokens=3000)
                st.session_state["protocol_nutrition"] = result
                st.rerun()
    else:
        st.markdown(st.session_state["protocol_nutrition"])
        adjust = st.text_input("Want to adjust anything?", key="nut_adjust")
        if st.button("↻ Regenerate with changes", key="regen_nutrition"):
            with st.spinner("Regenerating..."):
                sys_prompt = build_system_prompt(user_id, profile)
                extra = f"\n\nAdjustments: {adjust}" if adjust else ""
                result = ai_generate(sys_prompt, f"Regenerate the 7-day nutrition plan.{extra}", max_tokens=3000)
                st.session_state["protocol_nutrition"] = result
                st.rerun()

def show_protocol_workouts(user_id, profile):
    if "protocol_workouts" not in st.session_state:
        st.session_state["protocol_workouts"] = None

    if not st.session_state["protocol_workouts"]:
        focus = st.selectbox("Priority focus", ["General fitness", "Strength", "Recovery", "Cardio endurance", "Flexibility"], key="work_focus")
        if st.button("Generate Workout Plan", type="primary"):
            with st.spinner("Generating workout plan..."):
                sys_prompt = build_system_prompt(user_id, profile)
                cycle_day, phase, _ = calculate_cycle_status(user_id)
                cycle_ctx = f"Cycle Day {cycle_day}, {phase}" if cycle_day else ""
                wearable = db_get("wearable_data", user_id, order_col="data_date", limit=1)
                recovery_ctx = f"Recovery: {wearable[0].get('recovery_score','?')}%, HRV: {wearable[0].get('hrv','?')}ms" if wearable else ""
                prompt = f"Generate a 7-day training plan with focus on {focus}. {cycle_ctx} {recovery_ctx}\n\nFORMAT: Markdown table: Day | Session | Detail | Duration | Notes\nInclude specific exercises, sets, reps, RPE."
                result = ai_generate(sys_prompt, prompt, max_tokens=3000)
                st.session_state["protocol_workouts"] = result
                st.rerun()
    else:
        st.markdown(st.session_state["protocol_workouts"])
        adjust = st.text_input("Want to adjust anything?", key="work_adjust")
        if st.button("↻ Regenerate with changes", key="regen_workouts"):
            with st.spinner("Regenerating..."):
                sys_prompt = build_system_prompt(user_id, profile)
                extra = f"\n\nAdjustments: {adjust}" if adjust else ""
                result = ai_generate(sys_prompt, f"Regenerate the 7-day workout plan.{extra}", max_tokens=3000)
                st.session_state["protocol_workouts"] = result
                st.rerun()
# ── Check-In Page ─────────────────────────────────────────────────────────────

def show_checkin(user_id, profile):
    today = date.today()
    cycle_day, phase, _ = calculate_cycle_status(user_id)
    hour = datetime.now().hour
    time_of_day = "Morning" if hour < 12 else ("Afternoon" if hour < 17 else "Evening")
    cycle_text = f" · Cycle Day {cycle_day}" if cycle_day else ""

    st.markdown('<div class="pg-title">Daily Check-In</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pg-sub">{time_of_day} check-in · {today.strftime("%A, %d %B %Y")}{cycle_text}. Pre-filled from yesterday. Edit anything that has changed today. Takes less than 2 minutes.</div>', unsafe_allow_html=True)

    # Check if already logged today
    existing = None
    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)
    if checkins and checkins[0].get("checkin_date") == today.isoformat():
        existing = checkins[0]

    editing = st.session_state.get("editing_checkin", False)

    if existing and not editing:
        # Show insight
        if "checkin_insight" not in st.session_state:
            with st.spinner("Generating insight..."):
                sys_prompt = build_system_prompt(user_id, profile)
                prompt = f"Based on this patient's latest check-in data, provide ONE sharp clinical observation in 1-2 sentences. Be specific to their data, not generic."
                try:
                    st.session_state["checkin_insight"] = ai_generate(sys_prompt, prompt, max_tokens=200)
                except:
                    st.session_state["checkin_insight"] = "Keep tracking daily — patterns emerge over time."

        st.markdown(f"""<div class="insight-box">
<div class="ib-lbl">✦ Coach · Yesterday's insight</div>
<div class="ib-txt">{st.session_state["checkin_insight"]}</div>
</div>""", unsafe_allow_html=True)

        # Success banner
        st.success("Today's check-in logged!")
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.metric("Energy", f"{existing.get('energy','—')}/10")
        with sc2:
            st.metric("Mood", f"{existing.get('mood','—')}/10")
        with sc3:
            st.metric("Sleep", f"{existing.get('sleep_hours','—')}hrs")
        with sc4:
            st.metric("Sleep quality", f"{existing.get('sleep_quality','—')}/10")
        if existing.get("notes"):
            st.caption(f"Notes: {existing['notes']}")

        if st.button("✏️ Edit today's check-in"):
            st.session_state["editing_checkin"] = True
            st.rerun()
        return

    # Show form
    # Pre-fill from yesterday if not editing existing
    prefill = existing if existing else (checkins[0] if checkins else {})

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<p class="ci-lbl">Energy</p>', unsafe_allow_html=True)
        energy = st.slider("Energy (1-10)", 1, 10, int(prefill.get("energy", 5)), key="ci_energy", label_visibility="collapsed")
        st.markdown('<p class="ci-lbl">Sleep quality</p>', unsafe_allow_html=True)
        sleep_quality = st.slider("Sleep quality (1-10)", 1, 10, int(prefill.get("sleep_quality", 6)), key="ci_sleep_q", label_visibility="collapsed")
        st.markdown('<p class="ci-lbl">Gut / digestion</p>', unsafe_allow_html=True)
        bloating = st.selectbox("Gut/digestion", ["None", "Mild", "Moderate", "Severe"], index=["None","Mild","Moderate","Severe"].index(prefill.get("bloating","None")) if prefill.get("bloating") in ["None","Mild","Moderate","Severe"] else 0, key="ci_bloating", label_visibility="collapsed")
    with c2:
        st.markdown('<p class="ci-lbl">Mental clarity</p>', unsafe_allow_html=True)
        clarity = st.slider("Mental clarity (1-10)", 1, 10, int(prefill.get("stress", 5)), key="ci_clarity", label_visibility="collapsed")
        st.markdown('<p class="ci-lbl">Mood</p>', unsafe_allow_html=True)
        mood = st.slider("Mood (1-10)", 1, 10, int(prefill.get("mood", 5)), key="ci_mood", label_visibility="collapsed")
        st.markdown('<p class="ci-lbl">Libido</p>', unsafe_allow_html=True)
        libido = st.selectbox("Libido", ["Good", "Average", "Poor"], index=["Good","Average","Poor"].index(prefill.get("digestion","Average")) if prefill.get("digestion") in ["Good","Average","Poor"] else 1, key="ci_libido", label_visibility="collapsed")

    st.markdown('<p class="ci-lbl">Sleep hours last night</p>', unsafe_allow_html=True)
    sleep_hours = st.number_input("Sleep hours", min_value=0.0, max_value=14.0, value=float(prefill.get("sleep_hours", 7.0)), step=0.5, key="ci_sleep_h", label_visibility="collapsed")

    st.markdown('<p class="ci-lbl">Today\'s workout</p>', unsafe_allow_html=True)
    workout_options = ["Strength Training", "Padel", "Cardio", "Pilates", "Walk/Steps only", "Rest day", "Other"]
    workout = st.selectbox("Workout", workout_options, key="ci_workout", label_visibility="collapsed")

    notes = st.text_area("Anything notable today?", value=prefill.get("notes",""), key="ci_notes")

    if st.button("Save today's check-in →", type="primary"):
        checkin_data = {
            "user_id": user_id,
            "checkin_date": today.isoformat(),
            "cycle_day": cycle_day,
            "cycle_phase": phase,
            "energy": energy,
            "mood": mood,
            "stress": clarity,
            "sleep_hours": sleep_hours,
            "sleep_quality": sleep_quality,
            "bloating": bloating,
            "digestion": libido,
            "workout": workout,
            "notes": notes,
        }
        if existing:
            checkin_data["id"] = existing["id"]
        db_upsert("checkins", checkin_data)
        st.session_state.pop("checkin_insight", None)
        st.session_state.pop("editing_checkin", None)
        st.session_state.pop("home_priorities", None)
        st.rerun()
# ── Coach Page ────────────────────────────────────────────────────────────────

def show_coach(user_id, profile):
    st.markdown('<div class="pg-title">Coach</div>', unsafe_allow_html=True)

    first_name = (profile.get("full_name") or "").split()[0] if profile else "there"
    cycle_day, phase, _ = calculate_cycle_status(user_id)

    # Build system prompt with extras
    sys_prompt = build_system_prompt(user_id, profile)
    if cycle_day:
        sys_prompt += f"\nCurrent cycle: Day {cycle_day}, {phase}"
    roadmaps = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
    if roadmaps and roadmaps[0].get("committed"):
        sys_prompt += f"\n\nACTIVE ROADMAP (first 1500 chars):\n{roadmaps[0]['roadmap_text'][:1500]}"

    # Initialize chat
    if "coach_messages" not in st.session_state:
        st.session_state["coach_messages"] = []

    # Welcome state
    if not st.session_state["coach_messages"]:
        greet = greeting()
        checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        context_parts = []
        if cycle_day:
            context_parts.append(f"Day {cycle_day} · {phase.split('(')[0].strip()}")
        if checkins:
            ci = checkins[0]
            if ci.get("energy"):
                context_parts.append(f"Energy {ci['energy']}/10 on last check-in")
        context_line = " · ".join(context_parts) if context_parts else ""

        st.markdown(f"""<div class="insight-box">
<div class="ib-lbl">✦ OneSattva Coach</div>
<div class="ib-txt">{greet}, {first_name}. I have your full profile, labs, and goals. Ask me anything.</div>
{f'<div style="font-size:11px;color:var(--copper);margin-top:8px;">{context_line}</div>' if context_line else ''}
</div>""", unsafe_allow_html=True)

        # Quick prompts
        phase_short = phase.split("(")[0].strip() if phase else ""
        phase_prompts = {
            "Luteal": "🌙 Luteal phase — what should I adjust?",
            "Follicular": "🌱 Follicular phase — what to prioritise?",
            "Ovulation": "✨ Ovulation phase — how to optimise?",
            "Menstruation": "🩸 Menstruation — what to modify?",
        }
        phase_prompt = ""
        for key, val in phase_prompts.items():
            if key in (phase_short or ""):
                phase_prompt = val
                break
        if not phase_prompt:
            phase_prompt = "📊 How am I tracking overall?"

        quick_prompts = [
            "💊 My supplement protocol today",
            "🍽️ What to eat today",
            phase_prompt,
            "⚡ Why is my energy low?",
        ]

        qc1, qc2 = st.columns(2)
        for i, qp in enumerate(quick_prompts):
            col = qc1 if i % 2 == 0 else qc2
            with col:
                if st.button(qp, key=f"qp_{i}", use_container_width=True):
                    st.session_state["coach_messages"].append({"role": "user", "content": qp})
                    with st.spinner("Thinking..."):
                        response = ai_chat(sys_prompt, st.session_state["coach_messages"][-MAX_HISTORY:])
                        st.session_state["coach_messages"].append({"role": "assistant", "content": response})
                    st.rerun()

    else:
        # Clear chat button
        if st.button("Clear chat", key="clear_chat"):
            st.session_state["coach_messages"] = []
            st.rerun()

        # Show messages
        for msg in st.session_state["coach_messages"]:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown('<div class="ch-hd">✦ OneSattva Coach</div>', unsafe_allow_html=True)
                    st.write(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask your coach anything…")
    if user_input:
        st.session_state["coach_messages"].append({"role": "user", "content": user_input})
        with st.spinner("Thinking..."):
            response = ai_chat(sys_prompt, st.session_state["coach_messages"][-MAX_HISTORY:])
            st.session_state["coach_messages"].append({"role": "assistant", "content": response})
        st.rerun()
# ── Profile & Data Page ───────────────────────────────────────────────────────

def show_profile(user_id, profile):
    st.markdown('<div class="pg-title">Profile & Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Your health profile, lab reports, and wearable data.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["User Profile", "Lab Reports & Documents", "Wearable Data"])

    with tab1:
        show_profile_user(user_id, profile)
    with tab2:
        show_profile_labs(user_id, profile)
    with tab3:
        show_profile_wearable(user_id, profile)

def show_profile_user(user_id, profile):
    # Coach notice for old labs
    labs = db_get("lab_reports", user_id, order_col="report_date", limit=1)
    if labs:
        try:
            lab_date = date.fromisoformat(labs[0].get("report_date",""))
            days_old = (date.today() - lab_date).days
            if days_old > 90:
                st.markdown(f"""<div class="cp-banner" style="margin-bottom:16px;">
<div>
<div style="font-size:12px;font-weight:600;color:var(--copper);">Coach notice</div>
<div style="font-size:12px;color:var(--mid);">Your {lab_date.strftime('%d %b %Y')} lab report is {days_old} days old — outside the 3-month active window. New labs would enable more precise protocol calibration.</div>
</div>
</div>""", unsafe_allow_html=True)
        except:
            pass

    # Demographics + Medical History cards
    name = profile.get("full_name","") if profile else ""
    dob = profile.get("date_of_birth","") if profile else ""
    age = profile.get("age","") if profile else ""
    sex = profile.get("sex","") if profile else ""
    location = profile.get("location","") if profile else ""
    height = profile.get("height_cm","") if profile else ""
    weight = profile.get("weight_kg","") if profile else ""

    conditions = db_get("medical_history", user_id)
    meds = db_get("medications", user_id)

    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown(f"""<div class="prof-card">
<div class="prof-card-hd"><h4>Demographics</h4></div>
<div class="pr"><span class="pr-k">Name</span><span class="pr-v">{name}</span></div>
<div class="pr"><span class="pr-k">Date of birth</span><span class="pr-v">{dob} ({age}y)</span></div>
<div class="pr"><span class="pr-k">Biological sex</span><span class="pr-v">{sex}</span></div>
<div class="pr"><span class="pr-k">Location</span><span class="pr-v">{location}</span></div>
<div class="pr"><span class="pr-k">Height</span><span class="pr-v">{height} cm</span></div>
<div class="pr"><span class="pr-k">Weight</span><span class="pr-v">{weight} kg</span></div>
</div>""", unsafe_allow_html=True)
        with st.expander("✏️ Edit demographics"):
            with st.form("edit_demo"):
                new_name = st.text_input("Full name", value=name)
                new_location = st.text_input("Location", value=location)
                new_height = st.number_input("Height (cm)", value=int(height) if height else 165)
                new_weight = st.number_input("Weight (kg)", value=int(weight) if weight else 65)
                new_sex = st.selectbox("Biological sex", ["Female","Male","Prefer not to say"], index=["Female","Male","Prefer not to say"].index(sex) if sex in ["Female","Male","Prefer not to say"] else 0)
                if st.form_submit_button("Save"):
                    db_upsert("profiles", {"id": user_id, "full_name": new_name, "location": new_location, "height_cm": new_height, "weight_kg": new_weight, "sex": new_sex})
                    st.rerun()

    with dc2:
        cond_html = "".join([f'<div class="pr"><span class="pr-k">{c["condition"]}</span><span class="pr-v">{c.get("notes","")}</span></div>' for c in (conditions or [])])
        med_html = "".join([f'<div class="pr"><span class="pr-k">{m["name"]}</span><span class="pr-v">{m.get("dose","")} {m.get("frequency","")}</span></div>' for m in (meds or [])])
        st.markdown(f"""<div class="prof-card">
<div class="prof-card-hd"><h4>Medical History</h4></div>
{cond_html if cond_html else '<div style="font-size:12px;color:var(--mid);">No conditions recorded</div>'}
<div style="margin-top:8px;"><div class="prof-card-hd"><h4>Medications</h4></div></div>
{med_html if med_html else '<div style="font-size:12px;color:var(--mid);">No medications recorded</div>'}
</div>""", unsafe_allow_html=True)
        with st.expander("✏️ Edit medical history"):
            new_cond = st.text_input("Add condition", key="add_cond")
            new_cond_notes = st.text_input("Notes", key="add_cond_notes")
            if st.button("Add condition", key="btn_add_cond"):
                if new_cond:
                    db_insert("medical_history", {"user_id": user_id, "condition": new_cond, "notes": new_cond_notes})
                    st.rerun()
            for c in (conditions or []):
                if st.button(f"Delete: {c['condition']}", key=f"del_cond_p_{c['id']}"):
                    db_delete("medical_history", c["id"])
                    st.rerun()

    # Accordions
    # 1. Goals
    goals = db_get("goals", user_id)
    with st.expander("Goals", expanded=True):
        if goals:
            goal_list = ", ".join([g["goal"] for g in goals])
            st.write(goal_list)
        for g in (goals or []):
            gc1, gc2 = st.columns([8, 1])
            with gc1:
                tf = f" [{g.get('timeframe','')}]" if g.get("timeframe") else ""
                st.write(f"• {g['goal']}{tf}")
            with gc2:
                if st.button("✕", key=f"del_goal_{g['id']}"):
                    db_delete("goals", g["id"])
                    st.rerun()
        with st.form("add_goal_form"):
            new_goal = st.text_input("New goal")
            new_tf = st.selectbox("Timeframe", ["3 months","1 month","6 months","12 months","Ongoing"])
            if st.form_submit_button("Add goal"):
                if new_goal:
                    db_insert("goals", {"user_id": user_id, "goal": new_goal, "timeframe": new_tf})
                    st.rerun()

    # 2. Supplements
    supps = db_get("supplements", user_id)
    with st.expander("Current supplements"):
        for s in (supps or []):
            sc1, sc2 = st.columns([8, 1])
            with sc1:
                st.write(f"• {s['name']} — {s.get('dose','')} ({s.get('timing','')})")
            with sc2:
                if st.button("✕", key=f"del_sup_p_{s['id']}"):
                    db_delete("supplements", s["id"])
                    st.rerun()
        with st.form("add_supp_form"):
            sn = st.text_input("Supplement name")
            sd = st.text_input("Dose")
            st2 = st.text_input("Timing")
            if st.form_submit_button("Add supplement"):
                if sn:
                    db_insert("supplements", {"user_id": user_id, "name": sn, "dose": sd, "timing": st2, "active": True})
                    st.rerun()

    # 3. Medications
    with st.expander("Medications"):
        for m in (meds or []):
            mc1, mc2 = st.columns([8, 1])
            with mc1:
                st.write(f"• {m['name']} — {m.get('dose','')} {m.get('frequency','')}")
            with mc2:
                if st.button("✕", key=f"del_med_p_{m['id']}"):
                    db_delete("medications", m["id"])
                    st.rerun()
        with st.form("add_med_form"):
            mn = st.text_input("Medication name")
            md = st.text_input("Dose")
            mf = st.text_input("Frequency")
            if st.form_submit_button("Add medication"):
                if mn:
                    db_insert("medications", {"user_id": user_id, "name": mn, "dose": md, "frequency": mf, "active": True})
                    st.rerun()

    # 4. Dietary profile
    with st.expander("Dietary profile & restrictions"):
        diet = profile.get("diet","") if profile else ""
        allergies = profile.get("allergies","") if profile else ""
        st.write(f"Eating pattern: {diet}")
        st.write(f"Allergies/intolerances: {allergies}")
        with st.form("edit_diet"):
            new_diet = st.selectbox("Eating pattern", ["Vegetarian","Non-vegetarian","Vegan","Eggetarian","Pescatarian","Flexitarian"], index=0)
            new_allergies = st.text_input("Allergies / intolerances", value=allergies)
            if st.form_submit_button("Save"):
                db_upsert("profiles", {"id": user_id, "diet": new_diet, "allergies": new_allergies})
                st.rerun()

    # 5. Lifestyle
    with st.expander("Lifestyle — activity, sleep, stress"):
        pn = db_get_single("profile_notes", user_id)
        current_notes = pn.get("notes","") if pn else ""
        st.write(current_notes if current_notes else "No notes yet.")
        new_notes = st.text_area("Edit notes", value=current_notes, key="edit_lifestyle_notes")
        if st.button("Save notes", key="save_lifestyle"):
            db_upsert("profile_notes", {"user_id": user_id, "notes": new_notes})
            st.rerun()

    # 6. Cycle tracking
    sex = profile.get("sex","") if profile else ""
    if sex == "Female":
        with st.expander("Cycle tracking"):
            cycle_day, phase, days_until = calculate_cycle_status(user_id)
            if cycle_day:
                st.write(f"Day {cycle_day} · {phase}")
                if days_until:
                    st.write(f"~{days_until} days until next cycle")
            cd = db_get_single("cycle_data", user_id)
            with st.form("cycle_form"):
                lps = st.date_input("Last period start", value=date.fromisoformat(cd["last_period_start"]) if cd and cd.get("last_period_start") else None)
                acl = st.number_input("Avg cycle length", min_value=20, max_value=40, value=cd.get("avg_cycle_length",28) if cd else 28)
                if st.form_submit_button("Update"):
                    db_upsert("cycle_data", {"user_id": user_id, "last_period_start": lps.isoformat(), "avg_cycle_length": acl})
                    st.rerun()
            if st.button("New period started today"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": date.today().isoformat()})
                st.session_state.pop("home_priorities", None)
                st.rerun()

    # 7. Plan mode
    with st.expander("Plan mode"):
        ob = get_onboarding_state(user_id)
        plan_mode = ob.get("plan_mode","Restore") if ob else "Restore"
        plan_mode_info, total_weeks, current_week, checkpoint_week, plan_start = get_plan_info(user_id, profile)
        duration_map = {"Reset": "30 days", "Restore": "90 days", "Transform": "6 months", "Sustain": "Ongoing"}
        st.write(f"{plan_mode} · {duration_map.get(plan_mode,'90 days')} · Started {plan_start.strftime('%d %b %Y')} · Week {current_week} of {total_weeks}")
def show_profile_labs(user_id, profile):
    labs = db_get("lab_reports", user_id, order_col="report_date", limit=20)

    # Freshness banner
    if labs:
        try:
            latest_date = date.fromisoformat(labs[0].get("report_date",""))
            days_old = (date.today() - latest_date).days
            if days_old <= 90:
                st.success(f"✅ Current — latest report is {days_old} days old")
            elif days_old <= 180:
                st.warning(f"⚠️ Consider retesting — latest report is {days_old} days old")
            else:
                st.error(f"🚨 Too old — latest report is {days_old} days old. Please upload new labs.")
        except:
            pass

    # Upload zone
    st.markdown("""<div style="border:2px dashed var(--linem);border-radius:12px;padding:24px;text-align:center;margin-bottom:16px;">
<div style="font-size:14px;color:var(--graphite);margin-bottom:4px;">Drop your lab report here, or click to browse</div>
<div style="font-size:11px;color:var(--mid);">PDF or image · Thyrocare, SRL, Metropolis, Apollo...</div>
</div>""", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload lab report", type=["pdf","png","jpg","jpeg"], label_visibility="collapsed")
    if uploaded:
        st.info(f"File uploaded: {uploaded.name}. Use the paste section below to enter values for analysis.")

    # Paste lab values
    with st.expander("Paste lab values to analyse & save"):
        with st.expander("Recommended markers"):
            st.markdown(MARKERS_INFO)
        lab_date = st.date_input("Report date", value=date.today(), key="prof_lab_date")
        lab_name = st.text_input("Lab name", key="prof_lab_name")
        lab_values = st.text_area("Paste your lab values", height=150, key="prof_lab_vals")
        if st.button("🔍 Analyse & Save Report", key="analyse_labs"):
            if lab_values:
                with st.spinner("Analysing..."):
                    analysis = ai_generate(
                        "You are a functional medicine lab analyst. Analyse these lab values against functional (not conventional) reference ranges. Flag anything outside functional ranges. Format as a table with: Marker | Value | Functional Range | Status | Notes.",
                        f"Lab report from {lab_name} dated {lab_date}:\n\n{lab_values}"
                    )
                    db_insert("lab_reports", {
                        "user_id": user_id, "report_date": lab_date.isoformat(),
                        "lab_name": lab_name, "raw_values": lab_values,
                        "summary": analysis[:500], "analysis": analysis, "source": "manual_entry"
                    })
                    st.success("Report saved!")
                    st.markdown(analysis)
                    st.session_state.pop("home_priorities", None)

    # Existing reports
    if labs:
        st.markdown('<div class="sl">Your reports</div>', unsafe_allow_html=True)
        for l in labs:
            status = "Interpreted" if l.get("analysis") else "Historical"
            st.markdown(f"""<div class="file-row">
<span class="fn">{l.get('report_date','')} · {l.get('lab_name','Unknown lab')}</span>
<span class="fok">{status}</span>
</div>""", unsafe_allow_html=True)
            with st.expander(f"View: {l.get('report_date','')}"):
                if l.get("analysis"):
                    st.markdown(l["analysis"])
                if l.get("raw_values"):
                    st.text(l["raw_values"][:500])
                if st.button(f"Delete report", key=f"del_lab_{l['id']}"):
                    db_delete("lab_reports", l["id"])
                    st.rerun()

def show_profile_wearable(user_id, profile):
    wearable = db_get("wearable_data", user_id, order_col="data_date", limit=90)

    if wearable:
        latest = wearable[0]
        st.markdown(f"""<div class="prof-card" style="margin-bottom:16px;">
<div style="display:flex;justify-content:space-between;align-items:center;">
<div>
<div style="font-size:12px;font-weight:600;color:var(--graphite);">WHOOP Data</div>
<div style="font-size:11px;color:var(--mid);">Last import: {latest.get('data_date','')} · {len(wearable)} days of data</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

        # This week vs 30-day avg
        st.markdown('<div class="sl">This week vs 30-day average</div>', unsafe_allow_html=True)
        seven_days_ago = date.today() - timedelta(days=7)
        thirty_days_ago = date.today() - timedelta(days=30)
        week_data = [w for w in wearable if w.get("data_date","") >= seven_days_ago.isoformat()]
        month_data = [w for w in wearable if w.get("data_date","") >= thirty_days_ago.isoformat()]

        def avg_f(rows, field):
            vals = [float(r[field]) for r in rows if r.get(field) is not None]
            return round(statistics.mean(vals), 1) if vals else None

        metrics = [
            ("HRV", "hrv", "ms"),
            ("Recovery", "recovery_score", "%"),
            ("Sleep duration", "sleep_duration", "min"),
            ("Sleep efficiency", "sleep_efficiency", "%"),
            ("Resting HR", "resting_hr", "bpm"),
            ("Avg strain", "strain", ""),
        ]
        grid_html = '<div class="whoop-grid">'
        for label, field, unit in metrics:
            wk_avg = avg_f(week_data, field)
            mo_avg = avg_f(month_data, field)
            delta = ""
            if wk_avg is not None and mo_avg is not None:
                diff = round(wk_avg - mo_avg, 1)
                arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
                delta = f'<div class="wc-d">{arrow} {abs(diff)}{unit}</div>'
            grid_html += f"""<div class="wc">
<div class="wc-lbl">{label}</div>
<div class="wc-val">{wk_avg if wk_avg is not None else '—'}</div>
<div class="wc-sub">{unit} · 30d avg: {mo_avg if mo_avg is not None else '—'}</div>
{delta}
</div>"""
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)

    # Import section
    with st.expander("📤 Import / Re-import WHOOP data"):
        import pandas as pd
        cycles_file = st.file_uploader("cycles.csv", type="csv", key="whoop_cycles")
        sleep_file = st.file_uploader("sleep.csv", type="csv", key="whoop_sleep")
        workout_file = st.file_uploader("workout.csv", type="csv", key="whoop_workout")
        journal_file = st.file_uploader("journal_entries.csv (optional)", type="csv", key="whoop_journal")

        if st.button("💾 Process & Save WHOOP Data"):
            if not cycles_file:
                st.error("At least cycles.csv is required.")
            else:
                with st.spinner("Processing WHOOP data..."):
                    merged = {}

                    def process_csv(file, fields_wanted):
                        df = pd.read_csv(file)
                        cols = list(df.columns)
                        date_col = find_col(cols, COL_MAP["date"])
                        if not date_col:
                            st.warning(f"Could not find date column in {file.name}")
                            return
                        for _, row in df.iterrows():
                            raw_date = str(row[date_col])[:10]
                            try:
                                d = pd.to_datetime(raw_date).strftime("%Y-%m-%d")
                            except:
                                continue
                            if d not in merged:
                                merged[d] = {"user_id": user_id, "data_date": d}
                            for our_field, candidates in fields_wanted.items():
                                col = find_col(cols, candidates)
                                if col and pd.notna(row.get(col)):
                                    try:
                                        merged[d][our_field] = float(row[col])
                                    except:
                                        merged[d][our_field] = str(row[col])

                    process_csv(cycles_file, {k: v for k, v in COL_MAP.items() if k in ["recovery_score","hrv","resting_hr","strain"]})
                    if sleep_file:
                        process_csv(sleep_file, {k: v for k, v in COL_MAP.items() if k in ["sleep_performance","sleep_efficiency","sleep_duration"]})
                    if workout_file:
                        process_csv(workout_file, {k: v for k, v in COL_MAP.items() if k in ["workout_name","workout_strain"]})

                    saved = 0
                    for d, row in merged.items():
                        if db_upsert("wearable_data", row):
                            saved += 1
                    st.success(f"Saved {saved} days of WHOOP data!")
                    st.session_state.pop("home_priorities", None)
                    st.rerun()

    # Manual entry
    with st.expander("Manual entry"):
        with st.form("manual_wearable"):
            wd = st.date_input("Date", value=date.today())
            wc1, wc2, wc3 = st.columns(3)
            with wc1:
                m_hrv = st.number_input("HRV (ms)", min_value=0, value=0)
                m_recovery = st.number_input("Recovery %", min_value=0, max_value=100, value=0)
            with wc2:
                m_rhr = st.number_input("Resting HR", min_value=0, value=0)
                m_strain = st.number_input("Strain", min_value=0.0, value=0.0, step=0.1)
            with wc3:
                m_sleep_perf = st.number_input("Sleep %", min_value=0, max_value=100, value=0)
                m_sleep_dur = st.number_input("Sleep (min)", min_value=0, value=0)
            if st.form_submit_button("Save"):
                data = {"user_id": user_id, "data_date": wd.isoformat()}
                if m_hrv: data["hrv"] = m_hrv
                if m_recovery: data["recovery_score"] = m_recovery
                if m_rhr: data["resting_hr"] = m_rhr
                if m_strain: data["strain"] = m_strain
                if m_sleep_perf: data["sleep_performance"] = m_sleep_perf
                if m_sleep_dur: data["sleep_duration"] = m_sleep_dur
                db_upsert("wearable_data", data)
                st.rerun()

    st.info("WHOOP data is imported manually via CSV export from your WHOOP dashboard. Re-import weekly or after any significant event. The coach reads your full 90-day history on every conversation.")
# ── Main Entry Point ──────────────────────────────────────────────────────────

def main():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # Check auth
    if "user" not in st.session_state:
        show_auth()
        return

    user = st.session_state["user"]
    user_id = user.id

    # Re-attach session token
    session = st.session_state.get("session")
    if session:
        try:
            supabase.postgrest.auth(session.access_token)
        except:
            pass

    # Get profile
    profile = db_get_single("profiles", user_id)

    # Check onboarding
    ob_state = get_onboarding_state(user_id)
    onboarding_done = (profile and profile.get("onboarding_complete")) or st.session_state.get("onboarding_complete")

    if not onboarding_done:
        show_onboarding(user_id, profile)
        return

    # Main app
    show_sidebar(user_id, profile)

    page = st.session_state.get("page", "Home")
    if page == "Home":
        show_home(user_id, profile)
    elif page == "Protocol":
        show_protocol(user_id, profile)
    elif page == "Check-In":
        show_checkin(user_id, profile)
    elif page == "Coach":
        show_coach(user_id, profile)
    elif page == "Profile & Data":
        show_profile(user_id, profile)

if __name__ == "__main__":
    main()
