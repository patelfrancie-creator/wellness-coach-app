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
    base = """You are an expert integrative medicine practitioner and personal wellness coach specializing in functional medicine, Ayurveda, and Traditional Chinese Medicine (TCM). You are the patient's personal doctor-friend — someone with the knowledge of a specialist and the honesty of a close friend.

NON-NEGOTIABLE RESPONSE RULES:
1. ALWAYS COMPLETE YOUR RESPONSE — never cut off. Use tables and bullets to compress if needed, but always finish.
2. DATA ANOMALY PROTOCOL — if data looks unusual, flag it and ask one clarifying question before making recommendations.
3. EXPERT VOICE — you are the expert. If something in the current routine is suboptimal, say so clearly. State non-negotiables explicitly.
4. BE SPECIFIC — exact brands available in India, exact dosages, exact timing.
5. NEVER DEFLECT to "consult a nutritionist" without first giving the full specific answer yourself.
6. NO EGGS — patient is lacto-vegetarian, no eggs ever.
7. GUT-FRIENDLY FOODS — always cooked, warm, easy-to-digest. No raw proteins.
8. THYRONORM RULE — always first on waking with plain water only. Nothing else for 45-60 mins including lemon water, herbal tea, or supplements.

BRAND GUIDANCE FOR INDIA: Thorne, Himalayan Organics, Miduty, Wellbeing Nutrition, Carbamide Forte, Now Foods, Jarrow, Solgar (iHerb India/Amazon). For Ayurvedic: Kottakkal, Organic India, Kerala Ayurveda.

AYURVEDIC CONSTITUTION: Kapha-Vata with Kapha excess — sluggish metabolism, water retention, slow digestion. Recommend warm cooked spiced foods, morning movement, consistent meal times.

TCM PATTERN: Kidney Yang Deficiency + Liver Qi Stagnation — warming foods, bitter greens for liver, consistent routine.

For complex questions use this structure:
1. What is happening (mechanism)
2. What it means for this patient specifically
3. Exact protocol — brand, dose, timing, duration
4. What to expect and when
5. One priority action to start today
"""
    if profile:
        name = profile.get("full_name", "the patient")
        base += f"\n\nPATIENT: {name}"
        if profile.get("age"): base += f", {profile['age']} years old"
        if profile.get("height_cm") and profile.get("weight_kg"):
            base += f", {profile['height_cm']}cm, {profile['weight_kg']}kg"
        if profile.get("blood_group"): base += f", Blood group {profile['blood_group']}"
        if profile.get("location"): base += f", {profile['location']}"
        if profile.get("diet"): base += f", Diet: {profile['diet']}"

    # Goals
    goals = db_get("goals", user_id)
    if goals:
        base += "\n\nGOALS:\n" + "\n".join([f"- {g['goal']}" for g in goals])

    # Medical history
    conditions = db_get("medical_history", user_id)
    if conditions:
        base += "\n\nMEDICAL CONDITIONS:\n" + "\n".join([f"- {c['condition']}: {c.get('notes','')}" for c in conditions])

    # Medications
    meds = db_get("medications", user_id)
    if meds:
        active_meds = [m for m in meds if m.get("active", True)]
        if active_meds:
            base += "\n\nCURRENT MEDICATIONS:\n" + "\n".join([f"- {m['name']} {m.get('dose','')} {m.get('frequency','')}" for m in active_meds])

    # Supplements
    supps = db_get("supplements", user_id)
    if supps:
        active_supps = [s for s in supps if s.get("active", True)]
        if active_supps:
            base += "\n\nCURRENT SUPPLEMENTS:\n" + "\n".join([f"- {s['name']} {s.get('dose','')} ({s.get('timing','')})" for s in active_supps])

    # Recent check-ins
    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=7)
    if checkins:
        base += "\n\nRECENT 7-DAY CHECK-IN DATA:\n"
        for c in reversed(checkins):
            base += f"- {c.get('checkin_date','')}: Energy {c.get('energy','?')}/10, Sleep {c.get('sleep_hours','?')}hrs (quality {c.get('sleep_quality','?')}/10), Bloating: {c.get('bloating','?')}, Mood: {c.get('mood','?')}/10, Workout: {c.get('workout','?')}, Notes: {c.get('notes','')}\n"

    # Recent wearable data
    wearable = db_get("wearable_data", user_id, order_col="data_date", limit=7)
    if wearable:
        base += "\n\nRECENT WEARABLE DATA (WHOOP):\n"
        for w in reversed(wearable):
            parts = [f"- {w.get('data_date','')}"]
            for field in ["recovery_score","hrv","resting_hr","strain","sleep_performance"]:
                if w.get(field): parts.append(f"{field}: {w[field]}")
            base += ", ".join(parts) + "\n"

    # Profile notes
    notes = db_get_single("profile_notes", user_id)
    if notes and notes.get("notes"):
        base += f"\n\nPROFILE UPDATES FROM PATIENT:\n{notes['notes']}"

    # Lab reports
    labs = db_get("lab_reports", user_id, order_col="report_date", limit=5)
    if labs:
        base += "\n\nUPLOADED LAB REPORTS:\n"
        for l in labs:
            base += f"- {l.get('report_date','')}: {l.get('summary','')}\n"

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
            <svg width="20" height="20" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
              <defs><radialGradient id="sg" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#F2F3EF"/>
                <stop offset="62%" stop-color="#B68A3D"/>
                <stop offset="100%" stop-color="#1C2330" stop-opacity="0"/>
              </radialGradient></defs>
              <circle cx="50" cy="50" r="32" fill="url(#sg)"/>
              <circle cx="50" cy="50" r="6" fill="#F2F3EF"/>
            </svg>
            <span style="font-family:Newsreader,serif;font-style:italic;font-size:18px;color:#F2F3EF;line-height:1;">
              <span style="font-style:normal;opacity:0.45;font-size:0.55em;vertical-align:0.3em;margin-right:0.02em;">one</span>Sattva
            </span>
          </div>
          <div style="font-family:Inter,sans-serif;font-size:13px;color:#F2F3EF;opacity:0.7;">{name}</div>
          {f"<div style='font-family:Inter,sans-serif;font-size:11px;color:#F2F3EF;opacity:0.45;margin-top:2px;'>{profile.get('age','')}{'yr' if profile.get('age') else ''} · {profile.get('location','')}</div>" if profile else ""}
        </div>
        """, unsafe_allow_html=True)

        # ── Cycle status ──
        st.markdown("""<p style='font-family:Inter,sans-serif;font-size:11px;font-weight:600;letter-spacing:0.08em;color:#F2F3EF;opacity:0.45;margin:0 0 8px;text-transform:uppercase;'>Cycle</p>""", unsafe_allow_html=True)
        if cycle_day:
            st.markdown(f"""
            <div style='background:rgba(242,243,239,0.07);border-radius:10px;padding:12px 14px;margin-bottom:8px;'>
              <div style='font-family:JetBrains Mono,monospace;font-size:22px;color:#F2F3EF;font-weight:500;line-height:1;'>Day {cycle_day}</div>
              <div style='font-family:Inter,sans-serif;font-size:12px;color:#F2F3EF;opacity:0.6;margin-top:4px;'>{cycle_phase.split(' (')[0]}</div>
              {f"<div style='font-family:Inter,sans-serif;font-size:11px;color:#B68A3D;margin-top:6px;'>~{days_to_next}d until next period</div>" if days_to_next else ""}
            </div>
            """, unsafe_allow_html=True)
            if st.button("New period started today", use_container_width=True, key="new_period"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": date.today().isoformat()})
                st.session_state.system_prompt = build_system_prompt(user_id, profile)
                st.rerun()
        else:
            st.markdown("""<div style='font-family:Inter,sans-serif;font-size:12px;color:#F2F3EF;opacity:0.5;'>Set period date in Profile tab</div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # ── Goals ──
        goals = db_get("goals", user_id)
        if goals:
            st.markdown("""<p style='font-family:Inter,sans-serif;font-size:11px;font-weight:600;letter-spacing:0.08em;color:#F2F3EF;opacity:0.45;margin:0 0 8px;text-transform:uppercase;'>Goals</p>""", unsafe_allow_html=True)
            for g in goals[:3]:
                st.markdown(f"""<div style='font-family:Inter,sans-serif;font-size:12px;color:#F2F3EF;opacity:0.7;padding:4px 0;border-bottom:1px solid rgba(242,243,239,0.07);'>{g['goal'][:45]}</div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # ── Sign out ──
        st.markdown(f"""<div style='font-family:Inter,sans-serif;font-size:11px;color:#F2F3EF;opacity:0.35;margin-bottom:8px;'>{user.email}</div>""", unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True, key="signout_btn"):
            sign_out()

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab0, tab_profile, tab5, tab6, tab2, tab4b, tab4, tab3, tab1 = st.tabs([
        "🏡 Home", "👤 My Profile", "🧪 Lab Reports", "⌚ Wearable Data",
        "📋 Daily Check-In", "🗺️ Treatment Roadmap", "📅 Weekly Protocol",
        "📊 My Trends", "✦ Your Coach"
    ])

    # ════════════════════════════
    # HOME
    # ════════════════════════════
    with tab0:
        st.markdown(f"""
        <div style='padding:8px 0 4px;'>
        <h1 style='border:none; margin-bottom:4px !important; padding-bottom:0 !important; font-family:Newsreader,serif;'>Good to see you, {name}.</h1>
        <p style='color:#8A9485; font-size:1.05rem; margin-top:0;'>Here's where things stand today.</p>
        </div>
        """, unsafe_allow_html=True)

        checkins_today = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        today_logged = checkins_today and checkins_today[0].get("checkin_date") == date.today().isoformat()

        hcol1, hcol2, hcol3 = st.columns(3)
        with hcol1:
            st.markdown("##### 📅 Today")
            st.write(date.today().strftime("%A, %d %B %Y"))
            st.write(f"Cycle phase: **{cycle_phase.split(' (')[0]}**")
        with hcol2:
            st.markdown("##### ✅ Check-In")
            if today_logged:
                st.success("Logged for today")
            else:
                st.warning("Not logged yet")
        with hcol3:
            wearable_recent = db_get("wearable_data", user_id, order_col="data_date", limit=1)
            st.markdown("##### ⌚ Recovery")
            if wearable_recent and wearable_recent[0].get("recovery_score"):
                st.metric("", f"{wearable_recent[0]['recovery_score']:.0f}%")
            else:
                st.info("No wearable data yet")

        st.divider()
        st.markdown("##### 🎯 Your Goals")
        goals = db_get("goals", user_id)
        if goals:
            gcols = st.columns(min(len(goals), 5))
            for i, g in enumerate(goals[:5]):
                with gcols[i]:
                    st.markdown(f"""
                    <div style='background:#FFFFFF;border:1px solid #E8DFD0;border-radius:12px;padding:16px;text-align:center;'>
                    <div style='font-size:0.85rem;color:#6B7A65;'>{g['goal'][:50]}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Add your goals in the 👤 Profile tab to see them here.")

        st.divider()
        st.markdown("##### ⚡ Quick Actions")
        qcol1, qcol2, qcol3 = st.columns(3)
        with qcol1:
            st.button("💬 Ask your coach", use_container_width=True)
        with qcol2:
            st.button("📋 Today's check-in", use_container_width=True)
        with qcol3:
            st.button("📅 View weekly protocol", use_container_width=True)

        recent_checkins = db_get("checkins", user_id, order_col="checkin_date", limit=7)
        if recent_checkins:
            st.divider()
            st.markdown("##### 📊 Last 7 Days")
            df_r = pd.DataFrame(recent_checkins)
            mcol1, mcol2, mcol3 = st.columns(3)
            if "energy" in df_r.columns:
                mcol1.metric("Avg Energy", f"{df_r['energy'].mean():.1f}/10")
            if "sleep_hours" in df_r.columns:
                mcol2.metric("Avg Sleep", f"{df_r['sleep_hours'].mean():.1f} hrs")
            if "mood" in df_r.columns:
                mcol3.metric("Avg Mood", f"{df_r['mood'].mean():.1f}/10")

    # ════════════════════════════
    # PROFILE
    # ════════════════════════════
    with tab_profile:
        st.title("👤 My Profile")
        st.caption("Your health profile — the foundation your coach reasons from.")

        with st.expander("✏️ Personal Details", expanded=not bool(profile and profile.get("age"))):
            with st.form("profile_form"):
                pc1, pc2 = st.columns(2)
                with pc1:
                    p_name = st.text_input("Full Name", value=profile.get("full_name","") if profile else "")
                    p_age = st.number_input("Age", min_value=0, max_value=120, value=int(profile.get("age",0)) if profile and profile.get("age") else 0)
                    p_height = st.number_input("Height (cm)", value=float(profile.get("height_cm",0)) if profile and profile.get("height_cm") else 0.0)
                with pc2:
                    p_weight = st.number_input("Weight (kg)", value=float(profile.get("weight_kg",0)) if profile and profile.get("weight_kg") else 0.0)
                    p_blood = st.selectbox("Blood Group", ["","A+","A-","B+","B-","O+","O-","AB+","AB-"],
                        index=["","A+","A-","B+","B-","O+","O-","AB+","AB-"].index(profile.get("blood_group","")) if profile and profile.get("blood_group") in ["A+","A-","B+","B-","O+","O-","AB+","AB-"] else 0)
                    p_location = st.text_input("Location", value=profile.get("location","") if profile else "")
                p_diet = st.text_input("Diet (e.g. Vegetarian, no eggs)", value=profile.get("diet","Vegetarian, no eggs") if profile else "Vegetarian, no eggs")
                if st.form_submit_button("💾 Save Personal Details", type="primary"):
                    success = db_upsert("profiles", {"id": user_id, "full_name": p_name, "age": p_age, "height_cm": p_height, "weight_kg": p_weight, "blood_group": p_blood, "location": p_location, "diet": p_diet})
                    if success:
                        st.success("Saved!")
                        st.session_state.system_prompt = build_system_prompt(user_id, {"full_name":p_name,"age":p_age,"height_cm":p_height,"weight_kg":p_weight,"blood_group":p_blood,"location":p_location,"diet":p_diet})
                        st.rerun()

        st.divider()
        st.markdown("##### 🔄 Cycle Tracking")
        cd = db_get_single("cycle_data", user_id)
        cyc1, cyc2, cyc3 = st.columns(3)
        with cyc1:
            default_date = date.fromisoformat(cd["last_period_start"]) if cd and cd.get("last_period_start") else date.today()
            new_period_date = st.date_input("Last period start", value=default_date, key="profile_cycle_date")
        with cyc2:
            new_avg_len = st.number_input("Avg cycle length (days)", min_value=21, max_value=40, value=cd.get("avg_cycle_length",27) if cd else 27, key="profile_avg_len")
        with cyc3:
            if cycle_day:
                st.metric("Today", f"Day {cycle_day}")
                st.caption(cycle_phase.split(" (")[0])
        if st.button("💾 Update Cycle Data"):
            db_upsert("cycle_data", {"user_id": user_id, "last_period_start": new_period_date.isoformat(), "avg_cycle_length": new_avg_len})
            st.success("Cycle data updated!")
            st.rerun()

        st.divider()

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("##### 🎯 Goals")
            goals = db_get("goals", user_id)
            for g in goals:
                gcol1, gcol2 = st.columns([4,1])
                gcol1.write(g["goal"])
                if gcol2.button("🗑️", key=f"del_goal_{g['id']}"):
                    db_delete("goals", g["id"])
                    st.rerun()
            new_goal = st.text_input("Add a goal", key="new_goal_input")
            if st.button("+ Add Goal") and new_goal:
                db_upsert("goals", {"user_id": user_id, "goal": new_goal})
                st.rerun()

            st.markdown("##### 🩺 Medical Conditions")
            conditions = db_get("medical_history", user_id)
            for c in conditions:
                ccol1, ccol2 = st.columns([4,1])
                ccol1.write(f"**{c['condition']}** — {c.get('notes','')[:60]}")
                if ccol2.button("🗑️", key=f"del_cond_{c['id']}"):
                    db_delete("medical_history", c["id"])
                    st.rerun()
            with st.form("add_condition_form"):
                new_cond = st.text_input("Condition name")
                new_cond_notes = st.text_input("Notes (optional)")
                if st.form_submit_button("+ Add Condition") and new_cond:
                    db_upsert("medical_history", {"user_id": user_id, "condition": new_cond, "notes": new_cond_notes})
                    st.rerun()

        with col_right:
            st.markdown("##### 💊 Medications")
            meds = db_get("medications", user_id)
            for m in meds:
                mcol1, mcol2 = st.columns([4,1])
                mcol1.write(f"**{m['name']}** — {m.get('dose','')} {m.get('frequency','')}")
                if mcol2.button("🗑️", key=f"del_med_{m['id']}"):
                    db_delete("medications", m["id"])
                    st.rerun()
            with st.form("add_med_form"):
                m_name = st.text_input("Medication name")
                m_dose = st.text_input("Dose")
                m_freq = st.text_input("Frequency")
                if st.form_submit_button("+ Add Medication") and m_name:
                    db_upsert("medications", {"user_id": user_id, "name": m_name, "dose": m_dose, "frequency": m_freq})
                    st.rerun()

            st.markdown("##### 🌿 Supplements")
            supps = db_get("supplements", user_id)
            for s in supps:
                scol1, scol2 = st.columns([4,1])
                scol1.write(f"**{s['name']}** — {s.get('dose','')} ({s.get('timing','')})")
                if scol2.button("🗑️", key=f"del_supp_{s['id']}"):
                    db_delete("supplements", s["id"])
                    st.rerun()
            with st.form("add_supp_form"):
                s_name = st.text_input("Supplement name")
                s_dose = st.text_input("Dose")
                s_timing = st.text_input("Timing (e.g. with breakfast)")
                if st.form_submit_button("+ Add Supplement") and s_name:
                    db_upsert("supplements", {"user_id": user_id, "name": s_name, "dose": s_dose, "timing": s_timing})
                    st.rerun()

        st.divider()
        st.markdown("##### ✏️ Profile Notes & Updates")
        st.caption("New medication, stopped something, new symptom — your coach will factor this in.")
        notes_rec = db_get_single("profile_notes", user_id)
        current_notes = notes_rec.get("notes","") if notes_rec else ""
        new_notes = st.text_area("Notes", value=current_notes, height=120, placeholder="e.g. Started Thorne B-Complex on 15 June. Stopped Sampraz last week.")
        if st.button("💾 Save Notes", type="primary"):
            db_upsert("profile_notes", {"user_id": user_id, "notes": new_notes})
            st.session_state.system_prompt = build_system_prompt(user_id, profile)
            st.success("Saved — your coach will use this in future responses.")

    # ════════════════════════════
    # LAB REPORTS
    # ════════════════════════════
    with tab5:
        st.title("🧪 Lab Reports")
        st.caption("Upload new lab results — the AI compares against your history and flags changes.")

        report_date = st.date_input("Report Date", value=date.today())
        lab_name = st.text_input("Lab name (e.g. Thyrocare, SRL)")
        raw_values = st.text_area("Paste lab values here", height=180, placeholder="TSH: 1.83\nFT3: 2.2\nProlactin: 43.6\n...")

        if st.button("🔍 Analyse This Report", type="primary"):
            if raw_values.strip():
                existing_labs = db_get("lab_reports", user_id, order_col="report_date", limit=5)
                history_context = ""
                if existing_labs:
                    history_context = "\n\nPREVIOUS LAB REPORTS FOR CONTEXT:\n" + "\n".join([f"- {l['report_date']}: {l.get('summary','')}" for l in existing_labs])

                analysis_prompt = f"""New lab report uploaded — date: {report_date.isoformat()}, lab: {lab_name}

NEW VALUES:
{raw_values}
{history_context}

Compare against functional medicine optimal ranges (not just conventional). Structure your response as:

## What Changed
Table: Marker | Previous | New | Direction | Functional Status

## Key Wins
What's improving and why

## Still Needs Attention
What's still off and what to adjust

## Updated Priority
Has the priority order changed?

**Start today:** [one specific action]"""

                with st.spinner("Analysing your labs..."):
                    response = ai_client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=3000,
                        system=st.session_state.system_prompt,
                        messages=[{"role": "user", "content": analysis_prompt}]
                    )
                    analysis = response.content[0].text

                st.divider()
                st.markdown(analysis)

                # Save summary
                summary_res = ai_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=200,
                    messages=[{"role": "user", "content": f"Summarise in one dense line (max 150 chars): {raw_values}"}]
                )
                summary = summary_res.content[0].text[:500]
                db_upsert("lab_reports", {"user_id": user_id, "report_date": report_date.isoformat(), "lab_name": lab_name, "raw_values": raw_values, "summary": summary})
                st.success("✅ Report saved.")
                st.session_state.system_prompt = build_system_prompt(user_id, profile)
            else:
                st.warning("Paste some lab values to analyse.")

        st.divider()
        st.subheader("📚 Lab Report History")
        labs = db_get("lab_reports", user_id, order_col="report_date")
        if not labs:
            st.info("No reports uploaded yet.")
        else:
            if st.button("🗑️ Clear All Lab History"):
                for l in labs:
                    db_delete("lab_reports", l["id"])
                st.rerun()
            for lab in labs:
                with st.expander(f"📅 {lab['report_date']} — {lab.get('lab_name','')}"):
                    st.write(lab.get("summary",""))
                    st.text_area("Raw values", value=lab.get("raw_values",""), key=f"lab_raw_{lab['id']}", height=100)
                    if st.button("🗑️ Delete", key=f"del_lab_{lab['id']}"):
                        db_delete("lab_reports", lab["id"])
                        st.rerun()

    # ════════════════════════════
    # WEARABLE DATA
    # ════════════════════════════
    with tab6:
        st.title("⌚ Wearable Data")
        st.caption("Import WHOOP exports — all 4 CSV files supported.")

        import_method = st.radio("Import method", ["Upload WHOOP CSVs", "Manual entry for today"], horizontal=True)

        COL_MAP = {
            "date": ["Cycle start time","Cycle Start Time","Wake onset","Date"],
            "recovery_score": ["Recovery score %","Recovery Score %"],
            "hrv": ["Heart rate variability (ms)","HRV (ms)"],
            "resting_hr": ["Resting heart rate (bpm)","Resting Heart Rate (bpm)"],
            "strain": ["Day Strain","Strain"],
            "sleep_performance": ["Sleep performance %","Sleep Performance %"],
            "sleep_efficiency": ["Sleep efficiency %","Sleep Efficiency %"],
            "sleep_duration": ["Asleep duration (min)","Total sleep duration (min)"],
            "workout_name": ["Activity name","Activity Name","Sport"],
            "workout_strain": ["Activity Strain","Workout Strain"],
        }

        def find_col(cols, candidates):
            for c in candidates:
                if c in cols:
                    return c
            return None

        if import_method == "Upload WHOOP CSVs":
            wc1, wc2 = st.columns(2)
            with wc1:
                cycles_file = st.file_uploader("📊 cycles.csv", type=["csv"], key="cycles_up")
                sleep_file = st.file_uploader("😴 sleep.csv", type=["csv"], key="sleep_up")
            with wc2:
                workout_file = st.file_uploader("🏋️ workout.csv", type=["csv"], key="workout_up")
                journal_file = st.file_uploader("📓 journal_entries.csv", type=["csv"], key="journal_up")

            if st.button("💾 Process & Save WHOOP Data", type="primary"):
                merged = {}

                for f, fields in [
                    (cycles_file, ["recovery_score","hrv","resting_hr","strain"]),
                    (sleep_file, ["sleep_performance","sleep_efficiency","sleep_duration"]),
                ]:
                    if f:
                        try:
                            df = pd.read_csv(f)
                            date_col = find_col(df.columns.tolist(), COL_MAP["date"])
                            if date_col:
                                dates = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
                                for field in fields:
                                    col = find_col(df.columns.tolist(), COL_MAP[field])
                                    if col:
                                        for d, v in zip(dates, df[col]):
                                            if pd.notna(d):
                                                merged.setdefault(d, {})[field] = v
                                st.success(f"✅ {f.name}: {len(df)} rows processed")
                        except Exception as e:
                            st.error(f"{f.name} error: {e}")

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
                                        merged.setdefault(d, {})["workout_name"] = str(wdf[name_col].iloc[i])
                                    if strain_col:
                                        merged.setdefault(d, {})["workout_strain"] = wdf[strain_col].iloc[i]
                            st.success(f"✅ workout.csv: {len(wdf)} rows processed")
                    except Exception as e:
                        st.error(f"workout.csv error: {e}")

                if merged:
                    for d, vals in merged.items():
                        row = {"user_id": user_id, "data_date": d}
                        row.update(vals)
                        db_upsert("wearable_data", row)
                    st.success(f"✅ Saved {len(merged)} days of data.")
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.rerun()

        else:
            with st.form("manual_wearable"):
                wc1, wc2 = st.columns(2)
                with wc1:
                    w_date = st.date_input("Date", value=date.today())
                    w_recovery = st.number_input("Recovery Score (%)", 0, 100, 50)
                    w_hrv = st.number_input("HRV (ms)", 0, 200, 40)
                with wc2:
                    w_sleep = st.number_input("Sleep Performance (%)", 0, 100, 70)
                    w_strain = st.number_input("Strain", 0.0, 21.0, 10.0, step=0.1)
                    w_rhr = st.number_input("Resting HR (bpm)", 30, 120, 65)
                if st.form_submit_button("💾 Save", type="primary"):
                    db_upsert("wearable_data", {"user_id": user_id, "data_date": w_date.isoformat(), "recovery_score": w_recovery, "hrv": w_hrv, "sleep_performance": w_sleep, "strain": w_strain, "resting_hr": w_rhr})
                    st.success("Saved!")
                    st.rerun()

        st.divider()
        st.subheader("📈 Wearable Trends")
        wearable_all = db_get("wearable_data", user_id, order_col="data_date")
        if not wearable_all:
            st.info("No wearable data yet.")
        else:
            if st.button("🗑️ Clear All Wearable Data"):
                for w in wearable_all:
                    db_delete("wearable_data", w["id"])
                st.rerun()
            wdf = pd.DataFrame(wearable_all)
            wdf["data_date"] = pd.to_datetime(wdf["data_date"])
            wdf = wdf.sort_values("data_date")
            recent_w = wdf.tail(7)
            metrics = [c for c in ["recovery_score","hrv","sleep_performance","strain","resting_hr"] if c in wdf.columns]
            if metrics:
                wcols = st.columns(len(metrics))
                for i, m in enumerate(metrics):
                    valid = pd.to_numeric(recent_w[m], errors="coerce").dropna()
                    if len(valid):
                        wcols[i].metric(m.replace("_"," ").title(), f"{valid.mean():.1f}")
            plot_cols = [c for c in ["recovery_score","sleep_performance","strain"] if c in wdf.columns]
            if plot_cols:
                st.line_chart(wdf[["data_date"] + plot_cols].set_index("data_date"))
            if "hrv" in wdf.columns:
                st.subheader("HRV")
                st.line_chart(wdf[["data_date","hrv"]].set_index("data_date"))

            # Delete by date
            dates_list = wdf["data_date"].dt.strftime("%Y-%m-%d").tolist()
            del_date = st.selectbox("Delete a specific date", ["-- none --"] + dates_list)
            if del_date != "-- none --":
                if st.button(f"🗑️ Delete {del_date}"):
                    match = [w for w in wearable_all if w["data_date"] == del_date]
                    for w in match:
                        db_delete("wearable_data", w["id"])
                    st.rerun()

    # ════════════════════════════
    # DAILY CHECK-IN
    # ════════════════════════════
    with tab2:
        st.title("📋 Daily Check-In")
        st.caption("Takes 60 seconds. The AI uses this to personalise your advice.")

        today_checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)
        already_logged = today_checkins and today_checkins[0].get("checkin_date") == date.today().isoformat()

        if already_logged:
            st.success(f"✅ Already logged today. Come back tomorrow!")
            row = today_checkins[0]
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Energy", f"{row.get('energy','?')}/10")
            c2.metric("Sleep", f"{row.get('sleep_hours','?')} hrs")
            c3.metric("Sleep Quality", f"{row.get('sleep_quality','?')}/10")
            c4.metric("Mood", f"{row.get('mood','?')}/10")
        else:
            with st.form("checkin_form"):
                fc1, fc2 = st.columns(2)
                with fc1:
                    c_date = st.date_input("Date", value=date.today())
                    c_cycle_day = st.number_input("Cycle Day", 1, 35, value=cycle_day if cycle_day else 1)
                    c_phase = st.selectbox("Cycle Phase", ["Follicular","Ovulation","Luteal","Menstruation"])
                    c_energy = st.slider("⚡ Energy", 1, 10, 5)
                    c_mood = st.slider("😊 Mood", 1, 10, 5)
                    c_stress = st.slider("😤 Stress", 1, 10, 3)
                with fc2:
                    c_sleep_hrs = st.number_input("😴 Sleep Hours", 0.0, 12.0, 7.0, step=0.5)
                    c_sleep_q = st.slider("🌙 Sleep Quality", 1, 10, 5)
                    c_bloating = st.selectbox("🫧 Bloating", ["None","Mild","Moderate","Severe"])
                    c_digestion = st.selectbox("🌿 Digestion", ["Good","Average","Poor"])
                    c_bowel = st.selectbox("💧 Bowel", ["Normal","Loose","Constipated","None today"])
                    c_workout = st.selectbox("🏋️ Workout", ["Strength Training","Padel","Cardio","Pilates","Walk/Steps only","Rest day"])
                c_rumination = st.selectbox("🔄 Rumination", ["None","Mild (1-2)","Moderate (3-5)","Frequent (5+)"])
                c_notes = st.text_area("📝 Notes", placeholder="Anything unusual today...")
                if st.form_submit_button("✅ Save Check-In", type="primary"):
                    db_upsert("checkins", {
                        "user_id": user_id, "checkin_date": c_date.isoformat(),
                        "cycle_day": c_cycle_day, "cycle_phase": c_phase,
                        "energy": c_energy, "mood": c_mood, "stress": c_stress,
                        "sleep_hours": c_sleep_hrs, "sleep_quality": c_sleep_q,
                        "bloating": c_bloating, "digestion": c_digestion,
                        "bowel": c_bowel, "workout": c_workout,
                        "rumination": c_rumination, "notes": c_notes
                    })
                    st.session_state.system_prompt = build_system_prompt(user_id, profile)
                    st.success("✅ Check-in saved!")
                    st.balloons()
                    st.rerun()

    # ════════════════════════════
    # TREATMENT ROADMAP
    # ════════════════════════════
    with tab4b:
        st.title("🗺️ Treatment Roadmap")
        st.caption("Strategic 3-6-12 month plan based on your labs, data, and goals.")

        rm_col1, rm_col2 = st.columns(2)
        with rm_col1:
            rm_priority = st.selectbox("Priority focus", ["Balanced — all areas","Fastest path to natural conception","Fastest path to fat loss","Fastest path off thyroid medication","Gut/digestion first"], key="rm_priority")
        with rm_col2:
            rm_intensity = st.selectbox("Change intensity", ["Moderate — sustainable, gradual","Aggressive — willing to make bigger changes faster"], key="rm_intensity")

        if "treatment_roadmap" not in st.session_state:
            st.session_state.treatment_roadmap = None
        if "roadmap_date" not in st.session_state:
            st.session_state.roadmap_date = None

        if st.session_state.treatment_roadmap:
            st.success(f"🗺️ Roadmap generated {st.session_state.roadmap_date}")

        if st.button("🗺️ Generate Treatment Roadmap", type="primary", use_container_width=True):
            roadmap_prompt = f"""Generate a strategic 3-6-12 month treatment roadmap.

Priority: {rm_priority}
Intensity: {rm_intensity}

Use the patient's full profile, labs, check-ins, and wearable data already in your context.

FORMAT — use this exact structure:

## Where Things Stand
2-3 sentences: what is NOT working and why incremental tweaks alone won't be enough.

## Phase 1 — Months 0-3: [title]
Markdown table: Change | From → To | Why It Matters (4-6 rows, concise)
**Retest at end of Phase 1:** [3-4 specific markers]
**Success looks like:** [1-2 sentences, measurable]

## Phase 2 — Months 3-6: [title]
Same table format, 3-5 rows
**Retest:** [markers]
**Success:** [sentences]

## Phase 3 — Months 6-12: [title]
Same table format
**Retest:** [markers]
**Success:** [sentences]

## If Things Aren't Moving
2-3 sentences: what it means if Phase 1 shows no improvement and what the next escalation would be.

**Start today:** [one specific action]"""

            with st.spinner("Mapping your treatment roadmap..."):
                response = ai_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=4096,
                    system=st.session_state.system_prompt,
                    messages=[{"role": "user", "content": roadmap_prompt}]
                )
                st.session_state.treatment_roadmap = response.content[0].text
                st.session_state.roadmap_date = date.today().strftime("%d %b %Y")
                # Save to DB
                db_upsert("roadmaps", {"user_id": user_id, "priority_focus": rm_priority, "intensity": rm_intensity, "roadmap_text": st.session_state.treatment_roadmap})

        if st.session_state.treatment_roadmap:
            st.divider()
            st.markdown(st.session_state.treatment_roadmap)
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Regenerate", use_container_width=True):
                    st.session_state.treatment_roadmap = None
                    st.rerun()
            with col2:
                st.download_button("⬇️ Download", data=st.session_state.treatment_roadmap, file_name=f"roadmap_{date.today()}.txt", use_container_width=True)

        # Load saved roadmap if none in session
        if not st.session_state.treatment_roadmap:
            saved = db_get("roadmaps", user_id, order_col="generated_at", limit=1)
            if saved:
                st.info("You have a previously generated roadmap. Click Generate to create a new one, or it will be used automatically in your Weekly Protocol.")
                if st.button("📂 Load Previous Roadmap"):
                    st.session_state.treatment_roadmap = saved[0]["roadmap_text"]
                    st.rerun()

    # ════════════════════════════
    # WEEKLY PROTOCOL
    # ════════════════════════════
    with tab4:
        st.title("📅 Weekly Protocol")
        st.caption("Your personalised week — synced to your roadmap and cycle phase.")

        if st.session_state.get("treatment_roadmap"):
            st.success(f"🗺️ Synced with Treatment Roadmap ({st.session_state.get('roadmap_date','')})")
        else:
            st.info("💡 Generate a Treatment Roadmap first for a plan that builds toward your 3-6-12 month goals.")

        wp1, wp2, wp3 = st.columns(3)
        with wp1:
            default_phase_idx = 0
            if cycle_phase:
                phases = ["Follicular (Day 1–14)","Ovulation (Day 14–16)","Luteal (Day 16–28)","Menstruation (Day 1–5)"]
                for i, p in enumerate(phases):
                    if cycle_phase.startswith(p.split(" (")[0]):
                        default_phase_idx = i
                        break
            wp_phase = st.selectbox("Cycle phase", ["Follicular (Day 1–14)","Ovulation (Day 14–16)","Luteal (Day 16–28)","Menstruation (Day 1–5)"], index=default_phase_idx)
        with wp2:
            st.metric("Cycle Day", cycle_day if cycle_day else "?")
        with wp3:
            wp_focus = st.selectbox("Priority focus", ["Balanced","Fat loss","Fertility & conception","Gut healing","Energy & thyroid","Sleep & recovery"])

        if st.session_state.get("treatment_roadmap"):
            wp_week = st.selectbox("Which week of the roadmap?", ["Phase 1 — Week 1","Phase 1 — Week 2","Phase 1 — Week 3","Phase 1 — Week 4","Phase 2 — Week 5","Phase 2 — Week 6","Phase 2 — Week 7","Phase 2 — Week 8","Phase 3 — Later"])
        else:
            wp_week = "Week 1"

        if "weekly_protocol" not in st.session_state:
            st.session_state.weekly_protocol = None

        if st.button("🔄 Generate Weekly Protocol", type="primary", use_container_width=True):
            today_dt = datetime.now()
            day_names = [(today_dt + timedelta(days=i)).strftime("%A") for i in range(7)]
            days_str = ", ".join(day_names)

            roadmap_ctx = ""
            if st.session_state.get("treatment_roadmap"):
                roadmap_ctx = f"\n\nROADMAP CONTEXT — this is {wp_week}. Implement the relevant phase changes as the new baseline:\n{st.session_state.treatment_roadmap[:2000]}"

            base_ctx = f"""Weekly protocol for cycle day {cycle_day or '?'}, phase {wp_phase}, focus: {wp_focus}.
Days in order: {days_str}{roadmap_ctx}

CRITICAL: Output ONLY markdown tables. No explanations. Never cut off — complete all tables fully.
Never include eggs. Gut-friendly foods only (cooked, warm).
Thyronorm always first on waking with plain water, nothing else for 45-60 mins."""

            with st.spinner("Building supplement schedule..."):
                r1 = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=2000, system=st.session_state.system_prompt,
                    messages=[{"role":"user","content":base_ctx+"\n\nGenerate ONLY: Daily Routine & Supplement Schedule as a markdown table (Time | Item | Dose | Notes). Thyronorm first row."}])
                part1 = r1.content[0].text

            with st.spinner("Building nutrition plan..."):
                r2 = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=4096, system=st.session_state.system_prompt,
                    messages=[{"role":"user","content":base_ctx+f"\n\nGenerate ONLY: 7-Day Nutrition Plan as a markdown table. Rows: Pre-Workout | First Meal (10-11am) | Lunch (2-3pm) | Evening Snack (6-7pm) | Dinner (8-9pm) | Seed Cycling. Columns: Meal | {days_str}. One specific food per cell, max 8 words, vary slightly day to day. Complete the full table."}])
                part2 = r2.content[0].text

            with st.spinner("Building training and lifestyle plan..."):
                r3 = ai_client.messages.create(model="claude-sonnet-4-6", max_tokens=2500, system=st.session_state.system_prompt,
                    messages=[{"role":"user","content":base_ctx+f"\n\nGenerate ONLY: (1) 7-Day Training Plan table (Day | Session | Focus), days starting from {day_names[0]}. Include Padel Tue/Thu, Gym 11:30am, Pilates, rest day, 10k steps. (2) This Week's Focus — exactly 3 bullets (sleep target, lifestyle practice, thing to monitor). End with bold: **Start today:** [action]"}])
                part3 = r3.content[0].text

            st.session_state.weekly_protocol = part1 + "\n\n---\n\n" + part2 + "\n\n---\n\n" + part3

        if st.session_state.weekly_protocol:
            st.divider()
            st.markdown(st.session_state.weekly_protocol)
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Regenerate", use_container_width=True):
                    st.session_state.weekly_protocol = None
                    st.rerun()
            with col2:
                st.download_button("⬇️ Download", data=st.session_state.weekly_protocol, file_name=f"protocol_{date.today()}.txt", use_container_width=True)

    # ════════════════════════════
    # TRENDS
    # ════════════════════════════
    with tab3:
        st.title("📊 My Trends")
        all_checkins = db_get("checkins", user_id, order_col="checkin_date")
        if not all_checkins:
            st.info("No check-ins yet. Complete your first daily check-in to see trends here.")
        else:
            df_t = pd.DataFrame(all_checkins)
            df_t["checkin_date"] = pd.to_datetime(df_t["checkin_date"])
            df_t = df_t.sort_values("checkin_date")
            recent_t = df_t.tail(7)

            st.subheader("Last 7 Days")
            tc1,tc2,tc3,tc4 = st.columns(4)
            for col, field, label in [(tc1,"energy","Avg Energy"),(tc2,"sleep_hours","Avg Sleep"),(tc3,"mood","Avg Mood"),(tc4,"stress","Avg Stress")]:
                if field in recent_t.columns:
                    col.metric(label, f"{pd.to_numeric(recent_t[field], errors='coerce').mean():.1f}")

            st.divider()
            plot_fields = [f for f in ["energy","mood","sleep_quality"] if f in df_t.columns]
            if plot_fields:
                st.subheader("Energy, Mood & Sleep Quality")
                st.line_chart(df_t[["checkin_date"]+plot_fields].set_index("checkin_date"))
            if "sleep_hours" in df_t.columns:
                st.subheader("Sleep Hours")
                st.line_chart(df_t[["checkin_date","sleep_hours"]].set_index("checkin_date"))
            if "bloating" in df_t.columns:
                st.divider()
                st.subheader("Bloating Frequency")
                st.bar_chart(df_t["bloating"].value_counts())
            st.divider()
            display_cols = [c for c in ["checkin_date","cycle_phase","energy","mood","stress","sleep_hours","sleep_quality","bloating","digestion","workout","notes"] if c in df_t.columns]
            st.dataframe(df_t[display_cols].sort_values("checkin_date", ascending=False), use_container_width=True)

    # ════════════════════════════
    # WELLNESS COACH CHAT
    # ════════════════════════════
    with tab1:
        st.title("✦ Your Coach")
        st.caption("OneSattva · Integrative Medicine · Functional Labs · Ayurveda · TCM")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        if not st.session_state.messages:
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#F0EBE2,#FAF6F0);padding:22px;border-radius:14px;border-left:4px solid #7C9070;margin-bottom:20px;'>
            <h4 style='margin:0;color:#2D3B2D;font-family:"Fraunces",serif;'>Good to see you, {name} 🌿</h4>
            <p style='margin:8px 0 0;color:#6B7A65;'>I know your full health profile, labs, and goals. Ask me anything.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Quick questions:**")
            qc1, qc2 = st.columns(2)
            with qc1:
                if st.button("💊 Full supplement protocol", use_container_width=True):
                    st.session_state.messages.append({"role":"user","content":"Give me my complete supplement protocol with brands, dosages and exact timing"})
                    st.rerun()
                if st.button(f"🍽️ What should I eat today?", use_container_width=True):
                    st.session_state.messages.append({"role":"user","content":f"Based on my current cycle phase ({cycle_phase}) and labs, what should I eat today? Specific portions and timing."})
                    st.rerun()
            with qc2:
                if st.button("⚖️ Why am I not losing weight?", use_container_width=True):
                    st.session_state.messages.append({"role":"user","content":"Why am I not losing weight despite training consistently? What are the specific biological blockers based on my labs?"})
                    st.rerun()
                if st.button("😴 How do I fix my sleep?", use_container_width=True):
                    st.session_state.messages.append({"role":"user","content":"Based on my labs and routine, what specific changes should I make to fix my sleep?"})
                    st.rerun()

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        _, clear_col = st.columns([6,1])
        with clear_col:
            if st.button("🗑️ Clear"):
                st.session_state.messages = []
                st.rerun()

        if prompt := st.chat_input("Ask your wellness coach..."):
            cycle_ctx = f"\n\nCURRENT CYCLE PHASE: {cycle_phase}"
            if cycle_day:
                cycle_ctx += f", Day {cycle_day}"
            if days_to_next:
                cycle_ctx += f", ~{days_to_next} days until next period"
            cycle_ctx += ". Factor this into all recommendations."

            full_system = st.session_state.system_prompt + cycle_ctx

            st.session_state.messages.append({"role":"user","content":prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = ai_client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=2000,
                        system=full_system,
                        messages=st.session_state.messages
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
      <p style="font-family:Newsreader,serif;font-style:italic;color:#B68A3D;font-size:0.9rem;margin:0;">With you. For you.</p>
      <p style="font-family:Inter,sans-serif;font-size:0.95rem;color:#5B6270;margin-top:12px;">Let's build your health profile — takes about 5 minutes.</p>
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
        bg = "#1C2330" if is_done else ("#B68A3D" if is_current else "#E8E8E4")
        color = "#F2F3EF" if (is_done or is_current) else "#9B9B92"
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
            <div style='background:#F2F3EF;border-radius:12px;padding:16px;font-family:Inter,sans-serif;font-size:13px;color:#5B6270;'>
            <p style='font-weight:600;color:#1C2330;margin:0 0 8px;'>Why we ask</p>
            <p style='margin:0 0 6px;'>Your age, sex, height and weight affect how we interpret your labs and calibrate your nutrition and training recommendations.</p>
            <p style='margin:0 0 6px;'>Location helps us suggest locally available foods and brands.</p>
            <p style='margin:0;'>Alcohol and smoking directly influence hormone metabolism and gut health — we need to know to factor this in.</p>
            </div>
            """, unsafe_allow_html=True)
        elif current_step == 2:
            st.markdown("""
            <div style='background:#F2F3EF;border-radius:12px;padding:16px;font-family:Inter,sans-serif;font-size:13px;color:#5B6270;'>
            <p style='font-weight:600;color:#1C2330;margin:0 0 8px;'>Your data is private</p>
            <p style='margin:0 0 6px;'>Only you can see your health information. No one else — including practitioners — can access your data unless you explicitly grant them permission.</p>
            <p style='margin:0;'>Add as little or as much as you're comfortable with. You can always update this later.</p>
            </div>
            """, unsafe_allow_html=True)
        elif current_step == 3:
            st.markdown("""
            <div style='background:#F2F3EF;border-radius:12px;padding:16px;font-family:Inter,sans-serif;font-size:13px;color:#5B6270;'>
            <p style='font-weight:600;color:#1C2330;margin:0 0 8px;'>Goals shape everything</p>
            <p style='margin:0 0 6px;'>Your roadmap is built around your goals and their timeframes. Be specific — "lose weight" is less useful than "reach 58kg by September."</p>
            <p style='margin:0;'>You can have multiple goals with different timeframes. After each goal is achieved, we build a maintenance guide so you keep the results.</p>
            </div>
            """, unsafe_allow_html=True)
        elif current_step == 4:
            st.markdown("""
            <div style='background:#F2F3EF;border-radius:12px;padding:16px;font-family:Inter,sans-serif;font-size:13px;color:#5B6270;'>
            <p style='font-weight:600;color:#1C2330;margin:0 0 8px;'>Why labs matter</p>
            <p style='margin:0 0 6px;'>Functional medicine reads lab values differently from conventional medicine. A TSH of 2.5 might look "normal" but mask a T3 conversion problem.</p>
            <p style='margin:0 0 6px;'>Your coach interprets values against functional ranges, not just lab reference ranges.</p>
            <p style='margin:0;'>Reports older than 3 months are used for trend context only. Recent labs get priority.</p>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
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
