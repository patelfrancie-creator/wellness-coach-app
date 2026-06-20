import streamlit as st
import anthropic
import os
import json as _json
from datetime import date, datetime, timedelta
import pandas as pd
from supabase import create_client, Client

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wellness Coach",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
h1, h2, h3 { font-family: 'Fraunces', serif !important; color: #2D3B2D !important; font-weight: 600 !important; }
h1 { font-size: 2.2rem !important; border-bottom: 2px solid #E8DFD0; padding-bottom: 12px; margin-bottom: 1.2rem !important; }
.stApp { background-color: #FAF6F0; }
[data-testid="stSidebar"] { background-color: #2D3B2D; }
[data-testid="stSidebar"] * { color: #F0EBE2 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #F0EBE2 !important; font-family: 'Fraunces', serif !important; }
[data-testid="stSidebar"] hr { border-color: #4A5C45 !important; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; background-color: #F0EBE2; padding: 6px; border-radius: 12px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px; color: #6B7A65; font-weight: 500; padding: 10px 18px; }
.stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #2D3B2D !important; box-shadow: 0 1px 3px rgba(45,59,45,0.1); }
.stButton > button { border-radius: 10px; border: 1.5px solid #7C9070; color: #2D3B2D; background-color: #FFFFFF; font-weight: 500; transition: all 0.15s ease; }
.stButton > button:hover { background-color: #7C9070; color: #FFFFFF; }
.stButton > button[kind="primary"] { background-color: #C8755A; border-color: #C8755A; color: #FFFFFF; }
[data-testid="stAlert"] { border-radius: 10px; border-left-width: 4px; }
[data-testid="stMetric"] { background-color: #FFFFFF; padding: 14px; border-radius: 12px; border: 1px solid #E8DFD0; }
[data-testid="stChatMessage"] { background-color: #FFFFFF; border-radius: 14px; border: 1px solid #E8DFD0; }
hr { border-color: #E8DFD0 !important; margin: 1.5rem 0 !important; }
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
    <div style='max-width:420px; margin: 60px auto 0; text-align:center;'>
    <h1 style='border:none; font-size:2.8rem; margin-bottom:4px;'>🌿 Wellness Coach</h1>
    <p style='color:#8A9485; font-size:1.1rem; margin-bottom:2rem;'>Your personal integrative medicine companion</p>
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
        st.markdown(f"### 🌿 {name}")
        if profile:
            st.caption(f"{profile.get('age','?')} · {profile.get('height_cm','?')}cm · {profile.get('weight_kg','?')}kg")

        st.divider()

        st.subheader("🔄 Cycle")
        if cycle_day:
            st.markdown(f"**Day {cycle_day}** · {cycle_phase.split(' (')[0]}")
            if days_to_next:
                st.caption(f"~{days_to_next} days until next period")
            if st.button("🩸 New Period Today", use_container_width=True, key="new_period"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": date.today().isoformat()})
                st.session_state.system_prompt = build_system_prompt(user_id, profile)
                st.rerun()
        else:
            st.caption("Set period date in Profile tab")

        st.divider()
        st.subheader("🎯 Goals")
        goals = db_get("goals", user_id)
        if goals:
            for g in goals[:4]:
                st.markdown(f"- {g['goal'][:40]}")
        else:
            st.caption("Add goals in Profile tab")

        st.divider()
        if st.button("🚪 Sign Out", use_container_width=True):
            sign_out()

        st.caption(f"Logged in as {user.email}")

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab0, tab_profile, tab5, tab6, tab2, tab4b, tab4, tab3, tab1 = st.tabs([
        "🏡 Home", "👤 My Profile", "🧪 Lab Reports", "⌚ Wearable Data",
        "📋 Daily Check-In", "🗺️ Treatment Roadmap", "📅 Weekly Protocol",
        "📊 My Trends", "🌿 Wellness Coach"
    ])

    # ════════════════════════════
    # HOME
    # ════════════════════════════
    with tab0:
        st.markdown(f"""
        <div style='padding:8px 0 4px;'>
        <h1 style='border:none; margin-bottom:4px !important; padding-bottom:0 !important;'>Good to see you, {name} 🌿</h1>
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
        st.title("🌿 Wellness Coach")
        st.caption("Integrative Medicine · Functional Labs · Bio-Individual · Ayurveda · TCM")

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
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════════
if "user" not in st.session_state:
    show_auth_screen()
else:
    # CRITICAL: re-attach this user's session token on every rerun.
    # The supabase client is a shared singleton across all users on the server,
    # so we must set the correct auth token before any table call happens here.
    if "access_token" in st.session_state:
        supabase.postgrest.auth(st.session_state["access_token"])
    show_main_app(st.session_state["user"])
