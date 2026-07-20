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
ADMIN_EMAILS = {"patel.francie@gmail.com"}

COUNTRIES = [
    "India", "United States", "United Kingdom", "Canada", "Australia", "New Zealand",
    "Ireland", "Singapore", "United Arab Emirates", "Saudi Arabia", "Qatar", "Kuwait",
    "Germany", "France", "Netherlands", "Switzerland", "Sweden", "Norway", "Denmark",
    "Finland", "Spain", "Italy", "Portugal", "Belgium", "Austria", "Poland",
    "Japan", "South Korea", "China", "Hong Kong", "Taiwan", "Thailand", "Malaysia",
    "Indonesia", "Philippines", "Vietnam", "Sri Lanka", "Bangladesh", "Pakistan", "Nepal",
    "South Africa", "Nigeria", "Kenya", "Egypt", "Israel", "Turkey",
    "Brazil", "Mexico", "Argentina", "Chile", "Colombia",
    "Other",
]


def split_location(location):
    if not location:
        return "", ""
    parts = [p.strip() for p in location.split(",")]
    if len(parts) >= 2:
        return parts[0], ", ".join(parts[1:])
    return location.strip(), ""


COUNTRY_TIMEZONES = {
    "India": "Asia/Kolkata", "United States": "America/New_York", "United Kingdom": "Europe/London",
    "Canada": "America/Toronto", "Australia": "Australia/Sydney", "New Zealand": "Pacific/Auckland",
    "Ireland": "Europe/Dublin", "Singapore": "Asia/Singapore", "United Arab Emirates": "Asia/Dubai",
    "Saudi Arabia": "Asia/Riyadh", "Qatar": "Asia/Qatar", "Kuwait": "Asia/Kuwait",
    "Germany": "Europe/Berlin", "France": "Europe/Paris", "Netherlands": "Europe/Amsterdam",
    "Switzerland": "Europe/Zurich", "Sweden": "Europe/Stockholm", "Norway": "Europe/Oslo",
    "Denmark": "Europe/Copenhagen", "Finland": "Europe/Helsinki", "Spain": "Europe/Madrid",
    "Italy": "Europe/Rome", "Portugal": "Europe/Lisbon", "Belgium": "Europe/Brussels",
    "Austria": "Europe/Vienna", "Poland": "Europe/Warsaw", "Japan": "Asia/Tokyo",
    "South Korea": "Asia/Seoul", "China": "Asia/Shanghai", "Hong Kong": "Asia/Hong_Kong",
    "Taiwan": "Asia/Taipei", "Thailand": "Asia/Bangkok", "Malaysia": "Asia/Kuala_Lumpur",
    "Indonesia": "Asia/Jakarta", "Philippines": "Asia/Manila", "Vietnam": "Asia/Ho_Chi_Minh",
    "Sri Lanka": "Asia/Colombo", "Bangladesh": "Asia/Dhaka", "Pakistan": "Asia/Karachi",
    "Nepal": "Asia/Kathmandu", "South Africa": "Africa/Johannesburg", "Nigeria": "Africa/Lagos",
    "Kenya": "Africa/Nairobi", "Egypt": "Africa/Cairo", "Israel": "Asia/Jerusalem",
    "Turkey": "Europe/Istanbul", "Brazil": "America/Sao_Paulo", "Mexico": "America/Mexico_City",
    "Argentina": "America/Argentina/Buenos_Aires", "Chile": "America/Santiago", "Colombia": "America/Bogota",
}


def user_now(profile):
    """Best-effort local time for the user, derived from their onboarding
    Country selection. The server (Streamlit Cloud) runs in its own
    timezone, not the user's — without this, "Good morning" shows at
    whatever hour it is on the server, which can be wildly wrong (e.g.
    showing at 4am for someone in India while the server is on US time).
    Falls back to server time if the country isn't mapped or is unset."""
    country = split_location((profile or {}).get("location", ""))[1]
    tz_name = COUNTRY_TIMEZONES.get(country)
    if tz_name:
        try:
            from zoneinfo import ZoneInfo
            return datetime.now(ZoneInfo(tz_name))
        except Exception:
            pass
    return datetime.now()

ACTIVITY_LEVELS = ["Sedentary", "Lightly active", "Moderately active", "Very active"]
ALCOHOL_LEVELS = ["None", "Rarely (special occasions)", "1–2× per month", "Once a week", "2–3× per week", "Daily"]
SMOKING_LEVELS = ["Non-smoker", "Former smoker", "Occasional (social)", "Regular smoker", "Vaping / e-cigarettes"]
MEALS_PER_DAY_OPTIONS = ["2 meals", "3 meals", "3 meals + snacks", "Intermittent fasting"]
EATING_OUT_LEVELS = ["Rarely (home-cooked most days)", "Once a week", "2–3× per week", "4–5× per week", "Most meals"]


def selectbox_index(options, value, default=0):
    return options.index(value) if value in options else default


def _time_range(start_hour, start_min, end_hour, end_min, step=30):
    """12-hour clock strings (e.g. '6:30 am') from start to end, wrapping past midnight if end < start."""
    total_start = start_hour * 60 + start_min
    total_end = end_hour * 60 + end_min
    if total_end <= total_start:
        total_end += 24 * 60
    times = []
    t = total_start
    while t <= total_end:
        h24, m = (t // 60) % 24, t % 60
        period = "am" if h24 < 12 else "pm"
        h12 = h24 % 12 or 12
        times.append(f"{h12}:{m:02d} {period}")
        t += step
    return times


WAKE_TIME_OPTIONS = _time_range(4, 30, 10, 0)
BEDTIME_OPTIONS = _time_range(20, 0, 2, 0)
FIRST_MEAL_OPTIONS = _time_range(5, 0, 12, 0)
LAST_MEAL_OPTIONS = _time_range(16, 0, 23, 0)
SLEEP_DURATION_OPTIONS = ["Less than 5 hrs", "5 hrs", "5.5 hrs", "6 hrs", "6.5 hrs", "7 hrs", "7.5 hrs", "8 hrs", "8.5 hrs", "9+ hrs"]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Don't know"]
GOAL_SUGGESTIONS = ["Improve energy", "Better sleep quality", "Lose weight sustainably", "Build muscle / strength",
                     "Improve gut health / digestion", "Balance hormones", "Reduce stress / anxiety", "Improve skin health"]


def dropdown_with_other(container, label, options, existing_value, key, placeholder="e.g. 6:45 am"):
    """Selectbox of common times plus an 'Other' option that reveals free text — faster than typing for most people, still flexible."""
    choices = options + ["Other (type manually)"]
    if existing_value in options:
        idx = choices.index(existing_value)
    elif existing_value:
        idx = len(options)
    else:
        idx = 0
    choice = container.selectbox(label, choices, index=idx, key=f"{key}_sel")
    if choice == "Other (type manually)":
        custom_default = existing_value if existing_value not in options else ""
        return container.text_input(f"{label} (custom)", value=custom_default, key=f"{key}_custom", placeholder=placeholder, label_visibility="collapsed")
    return choice


def plain_preview(text, limit=140):
    """Strip markdown control characters and collapse whitespace before
    truncating for a one-line preview. A naive char-slice of raw markdown can
    cut mid-heading (e.g. "## Critical Findings" -> "## Critical Fin"), which
    Streamlit then renders as a giant, cut-off heading instead of a preview."""
    if not text:
        return ""
    cleaned = re.sub(r'[#*_`>]+', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rsplit(' ', 1)[0] + "…"

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
_MARK_COUNTER = {"n": 0}


_MARK_RING_PATHS = [
    'M194.49 100.00 L194.46 102.97 L194.34 105.94 L194.12 108.90 L193.81 111.85 L193.40 114.79 L192.90 117.72 L192.31 120.63 L191.62 123.52 L190.84 126.39 L189.97 129.23 L189.01 132.05 L187.96 134.82 L186.81 137.57 L185.57 140.27 L184.25 142.93 L182.84 145.54 L181.34 148.10 L179.76 150.61 L178.09 153.07 L176.35 155.47 L174.53 157.81 L172.64 160.09 L170.67 162.31 L168.64 164.46 L166.55 166.55 L164.39 168.57 L162.18 170.53 L159.91 172.42 L157.58 174.24 L155.21 175.99 L152.78 177.67 L150.31 179.28 L147.79 180.81 L145.23 182.27 L142.62 183.64 L139.97 184.94 L137.28 186.16 L134.56 187.28 L131.80 188.33 L129.01 189.27 L126.19 190.13 L123.34 190.89 L120.47 191.56 L117.57 192.13 L114.67 192.60 L111.74 192.97 L108.81 193.24 L105.88 193.42 L102.94 193.51 L100.00 193.50 L97.06 193.40 L94.14 193.22 L91.21 192.95 L88.30 192.60 L85.40 192.16 L82.52 191.65 L79.64 191.07 L76.79 190.41 L73.95 189.67 L71.13 188.86 L68.33 187.98 L65.55 187.02 L62.79 185.99 L60.06 184.87 L57.36 183.68 L54.70 182.41 L52.07 181.05 L49.48 179.61 L46.94 178.08 L44.45 176.46 L42.01 174.76 L39.64 172.97 L37.33 171.09 L35.09 169.12 L32.92 167.08 L30.84 164.95 L28.84 162.74 L26.92 160.46 L25.09 158.11 L23.34 155.69 L21.69 153.22 L20.12 150.69 L18.65 148.11 L17.26 145.49 L15.96 142.82 L14.75 140.12 L13.62 137.38 L12.58 134.61 L11.62 131.82 L10.74 129.00 L9.95 126.16 L9.23 123.31 L8.60 120.43 L8.04 117.54 L7.57 114.64 L7.19 111.73 L6.88 108.80 L6.66 105.87 L6.53 102.94 L6.49 100.00 L6.53 97.06 L6.67 94.13 L6.89 91.20 L7.21 88.28 L7.61 85.37 L8.11 82.47 L8.70 79.59 L9.37 76.73 L10.14 73.89 L10.99 71.08 L11.93 68.29 L12.95 65.53 L14.05 62.81 L15.24 60.11 L16.50 57.46 L17.85 54.84 L19.27 52.26 L20.77 49.72 L22.35 47.23 L24.00 44.78 L25.73 42.39 L27.53 40.05 L29.41 37.76 L31.36 35.54 L33.38 33.38 L35.47 31.29 L37.64 29.26 L39.87 27.31 L42.16 25.44 L44.52 23.64 L46.94 21.92 L49.41 20.29 L51.94 18.74 L54.52 17.27 L57.15 15.90 L59.82 14.60 L62.52 13.40 L65.27 12.28 L68.04 11.24 L70.85 10.29 L73.69 9.43 L76.54 8.64 L79.42 7.95 L82.32 7.34 L85.24 6.81 L88.17 6.37 L91.12 6.02 L94.07 5.75 L97.03 5.58 L100.00 5.50 L102.97 5.52 L105.94 5.63 L108.90 5.84 L111.85 6.16 L114.80 6.58 L117.72 7.10 L120.62 7.73 L123.50 8.47 L126.35 9.31 L129.16 10.25 L131.94 11.29 L134.67 12.43 L137.36 13.67 L140.00 15.00 L142.59 16.41 L145.13 17.91 L147.62 19.48 L150.05 21.13 L152.43 22.84 L154.76 24.62 L157.04 26.46 L159.26 28.36 L161.44 30.31 L163.56 32.32 L165.63 34.37 L167.65 36.48 L169.61 38.63 L171.52 40.83 L173.38 43.08 L175.18 45.38 L176.93 47.72 L178.61 50.12 L180.22 52.56 L181.76 55.05 L183.23 57.59 L184.63 60.18 L185.94 62.81 L187.17 65.49 L188.31 68.21 L189.36 70.97 L190.31 73.76 L191.17 76.59 L191.93 79.45 L192.59 82.34 L193.16 85.25 L193.62 88.17 L193.99 91.12 L194.25 94.07 L194.42 97.03 L194.49 100.00 Z',
    'M183.80 100.00 L183.77 102.63 L183.66 105.26 L183.45 107.89 L183.17 110.51 L182.80 113.11 L182.34 115.71 L181.80 118.29 L181.18 120.84 L180.48 123.38 L179.69 125.89 L178.82 128.38 L177.87 130.83 L176.84 133.25 L175.73 135.64 L174.54 137.98 L173.28 140.29 L171.94 142.54 L170.52 144.76 L169.04 146.92 L167.48 149.03 L165.86 151.09 L164.18 153.09 L162.43 155.04 L160.63 156.93 L158.77 158.77 L156.86 160.55 L154.90 162.27 L152.89 163.93 L150.83 165.53 L148.73 167.07 L146.59 168.55 L144.40 169.97 L142.18 171.32 L139.91 172.61 L137.62 173.82 L135.28 174.97 L132.91 176.05 L130.51 177.06 L128.08 177.98 L125.61 178.83 L123.13 179.60 L120.61 180.29 L118.08 180.89 L115.53 181.41 L112.96 181.84 L110.38 182.19 L107.79 182.46 L105.20 182.64 L102.60 182.73 L100.00 182.75 L97.40 182.68 L94.81 182.54 L92.22 182.33 L89.64 182.04 L87.06 181.68 L84.50 181.25 L81.95 180.75 L79.41 180.18 L76.89 179.55 L74.38 178.85 L71.89 178.08 L69.42 177.25 L66.96 176.34 L64.54 175.37 L62.13 174.32 L59.76 173.20 L57.42 172.00 L55.12 170.72 L52.86 169.37 L50.64 167.93 L48.48 166.42 L46.37 164.83 L44.32 163.16 L42.33 161.41 L40.42 159.58 L38.57 157.69 L36.80 155.72 L35.10 153.69 L33.49 151.59 L31.95 149.44 L30.49 147.24 L29.12 144.98 L27.82 142.69 L26.61 140.35 L25.47 137.97 L24.41 135.57 L23.43 133.13 L22.53 130.67 L21.70 128.19 L20.94 125.69 L20.25 123.17 L19.64 120.63 L19.09 118.08 L18.62 115.52 L18.23 112.95 L17.90 110.37 L17.65 107.78 L17.47 105.19 L17.37 102.60 L17.34 100.00 L17.40 97.40 L17.53 94.81 L17.73 92.22 L18.02 89.64 L18.39 87.07 L18.83 84.52 L19.35 81.97 L19.95 79.45 L20.63 76.94 L21.38 74.45 L22.21 71.99 L23.10 69.55 L24.08 67.14 L25.12 64.76 L26.23 62.41 L27.41 60.09 L28.66 57.81 L29.98 55.56 L31.36 53.35 L32.81 51.19 L34.33 49.06 L35.92 46.99 L37.57 44.96 L39.29 42.99 L41.07 41.07 L42.91 39.20 L44.82 37.41 L46.78 35.67 L48.81 34.00 L50.89 32.40 L53.02 30.87 L55.21 29.42 L57.44 28.04 L59.72 26.74 L62.04 25.51 L64.41 24.36 L66.80 23.28 L69.23 22.29 L71.69 21.37 L74.18 20.52 L76.69 19.75 L79.22 19.06 L81.77 18.44 L84.34 17.90 L86.92 17.44 L89.52 17.05 L92.13 16.74 L94.75 16.51 L97.37 16.36 L100.00 16.29 L102.63 16.31 L105.26 16.41 L107.88 16.61 L110.50 16.89 L113.10 17.27 L115.69 17.74 L118.26 18.30 L120.81 18.95 L123.33 19.70 L125.82 20.54 L128.27 21.46 L130.69 22.48 L133.07 23.57 L135.41 24.75 L137.70 26.00 L139.95 27.33 L142.15 28.72 L144.31 30.18 L146.42 31.69 L148.48 33.27 L150.50 34.89 L152.47 36.57 L154.40 38.29 L156.28 40.06 L158.12 41.88 L159.91 43.74 L161.66 45.64 L163.36 47.58 L165.01 49.57 L166.62 51.60 L168.17 53.67 L169.66 55.79 L171.10 57.95 L172.48 60.16 L173.79 62.40 L175.03 64.69 L176.20 67.03 L177.30 69.40 L178.31 71.81 L179.25 74.25 L180.10 76.73 L180.87 79.24 L181.54 81.77 L182.13 84.33 L182.64 86.91 L183.05 89.51 L183.37 92.12 L183.60 94.74 L183.75 97.37 L183.80 100.00 Z',
    'M170.96 100.00 L170.92 102.23 L170.80 104.45 L170.61 106.67 L170.35 108.89 L170.03 111.09 L169.63 113.28 L169.16 115.46 L168.63 117.62 L168.02 119.76 L167.35 121.88 L166.61 123.98 L165.81 126.06 L164.94 128.10 L164.00 130.12 L163.00 132.10 L161.94 134.05 L160.81 135.96 L159.62 137.84 L158.38 139.67 L157.08 141.47 L155.72 143.22 L154.31 144.93 L152.84 146.59 L151.33 148.21 L149.77 149.77 L148.17 151.30 L146.52 152.77 L144.84 154.20 L143.11 155.57 L141.34 156.90 L139.53 158.17 L137.69 159.39 L135.81 160.55 L133.90 161.66 L131.95 162.71 L129.97 163.70 L127.96 164.62 L125.93 165.48 L123.86 166.28 L121.77 167.00 L119.65 167.65 L117.52 168.23 L115.36 168.73 L113.19 169.16 L111.01 169.52 L108.82 169.79 L106.62 170.00 L104.41 170.13 L102.21 170.18 L100.00 170.17 L97.80 170.09 L95.60 169.94 L93.41 169.73 L91.23 169.45 L89.05 169.12 L86.89 168.73 L84.74 168.28 L82.60 167.78 L80.47 167.22 L78.36 166.61 L76.26 165.95 L74.17 165.23 L72.11 164.46 L70.06 163.63 L68.03 162.74 L66.03 161.79 L64.05 160.78 L62.11 159.71 L60.19 158.57 L58.32 157.37 L56.48 156.10 L54.69 154.77 L52.95 153.37 L51.26 151.91 L49.62 150.38 L48.04 148.79 L46.53 147.14 L45.07 145.44 L43.69 143.68 L42.37 141.87 L41.12 140.02 L39.93 138.12 L38.82 136.18 L37.77 134.21 L36.79 132.21 L35.87 130.18 L35.02 128.12 L34.24 126.04 L33.52 123.93 L32.87 121.81 L32.28 119.68 L31.75 117.52 L31.28 115.36 L30.88 113.19 L30.54 111.00 L30.26 108.81 L30.06 106.61 L29.91 104.41 L29.83 102.21 L29.82 100.00 L29.88 97.80 L30.00 95.60 L30.20 93.40 L30.46 91.21 L30.78 89.04 L31.18 86.87 L31.64 84.72 L32.17 82.58 L32.76 80.47 L33.42 78.37 L34.13 76.29 L34.91 74.23 L35.75 72.20 L36.65 70.19 L37.60 68.20 L38.61 66.25 L39.67 64.32 L40.79 62.43 L41.97 60.56 L43.20 58.73 L44.49 56.94 L45.83 55.18 L47.22 53.47 L48.67 51.80 L50.17 50.17 L51.72 48.59 L53.33 47.06 L54.99 45.59 L56.69 44.17 L58.45 42.81 L60.25 41.50 L62.09 40.26 L63.98 39.09 L65.90 37.97 L67.86 36.92 L69.86 35.94 L71.88 35.02 L73.93 34.17 L76.01 33.38 L78.12 32.66 L80.24 32.00 L82.39 31.40 L84.55 30.87 L86.73 30.41 L88.91 30.01 L91.12 29.68 L93.33 29.41 L95.55 29.22 L97.77 29.09 L100.00 29.03 L102.23 29.05 L104.46 29.14 L106.68 29.31 L108.90 29.56 L111.11 29.88 L113.30 30.28 L115.48 30.76 L117.63 31.32 L119.77 31.96 L121.87 32.68 L123.95 33.47 L126.00 34.33 L128.01 35.27 L129.99 36.27 L131.93 37.34 L133.83 38.46 L135.69 39.64 L137.52 40.88 L139.30 42.16 L141.05 43.50 L142.76 44.87 L144.43 46.29 L146.07 47.75 L147.66 49.24 L149.23 50.77 L150.75 52.34 L152.24 53.95 L153.68 55.59 L155.09 57.27 L156.46 58.98 L157.78 60.73 L159.06 62.52 L160.28 64.35 L161.46 66.21 L162.57 68.12 L163.63 70.06 L164.63 72.03 L165.56 74.04 L166.42 76.09 L167.21 78.16 L167.93 80.26 L168.57 82.39 L169.14 84.55 L169.63 86.72 L170.04 88.91 L170.38 91.11 L170.64 93.32 L170.82 95.54 L170.93 97.77 L170.96 100.00 Z',
    'M161.03 100.00 L160.99 101.92 L160.89 103.83 L160.74 105.74 L160.52 107.65 L160.25 109.54 L159.93 111.43 L159.54 113.31 L159.10 115.17 L158.60 117.03 L158.05 118.86 L157.44 120.68 L156.77 122.48 L156.04 124.25 L155.25 126.00 L154.41 127.72 L153.50 129.41 L152.55 131.08 L151.53 132.70 L150.46 134.29 L149.34 135.85 L148.17 137.36 L146.94 138.83 L145.67 140.26 L144.36 141.65 L143.00 143.00 L141.60 144.30 L140.16 145.55 L138.68 146.76 L137.17 147.92 L135.63 149.04 L134.05 150.11 L132.45 151.13 L130.81 152.10 L129.15 153.03 L127.46 153.90 L125.75 154.72 L124.01 155.49 L122.25 156.20 L120.47 156.86 L118.67 157.46 L116.85 158.00 L115.02 158.49 L113.17 158.91 L111.31 159.27 L109.44 159.57 L107.56 159.81 L105.67 159.99 L103.78 160.11 L101.89 160.18 L100.00 160.18 L98.11 160.14 L96.22 160.03 L94.34 159.88 L92.46 159.68 L90.59 159.42 L88.72 159.12 L86.86 158.78 L85.01 158.38 L83.17 157.94 L81.33 157.45 L79.51 156.92 L77.70 156.33 L75.90 155.69 L74.12 155.00 L72.36 154.26 L70.61 153.46 L68.89 152.60 L67.20 151.68 L65.55 150.70 L63.92 149.66 L62.34 148.56 L60.79 147.39 L59.30 146.17 L57.85 144.88 L56.46 143.54 L55.12 142.15 L53.83 140.70 L52.61 139.20 L51.44 137.66 L50.34 136.08 L49.29 134.46 L48.31 132.80 L47.38 131.12 L46.51 129.41 L45.69 127.67 L44.93 125.91 L44.22 124.14 L43.57 122.34 L42.96 120.54 L42.40 118.71 L41.89 116.88 L41.43 115.04 L41.02 113.18 L40.66 111.32 L40.35 109.45 L40.10 107.57 L39.89 105.68 L39.74 103.79 L39.65 101.90 L39.61 100.00 L39.63 98.10 L39.72 96.21 L39.86 94.32 L40.06 92.43 L40.33 90.55 L40.66 88.68 L41.05 86.82 L41.50 84.98 L42.01 83.15 L42.57 81.34 L43.20 79.55 L43.88 77.78 L44.61 76.03 L45.39 74.30 L46.22 72.60 L47.11 70.92 L48.04 69.27 L49.02 67.64 L50.04 66.05 L51.11 64.48 L52.23 62.94 L53.39 61.44 L54.60 59.97 L55.85 58.54 L57.14 57.14 L58.48 55.79 L59.86 54.47 L61.29 53.21 L62.75 51.98 L64.26 50.81 L65.81 49.69 L67.39 48.61 L69.01 47.59 L70.66 46.63 L72.34 45.72 L74.05 44.86 L75.79 44.06 L77.56 43.31 L79.34 42.62 L81.15 41.99 L82.98 41.41 L84.82 40.88 L86.68 40.42 L88.56 40.00 L90.44 39.65 L92.34 39.35 L94.24 39.11 L96.16 38.94 L98.08 38.82 L100.00 38.77 L101.92 38.78 L103.85 38.86 L105.77 39.00 L107.68 39.22 L109.58 39.50 L111.47 39.86 L113.35 40.28 L115.21 40.78 L117.04 41.35 L118.85 41.98 L120.64 42.68 L122.39 43.44 L124.12 44.26 L125.82 45.14 L127.48 46.07 L129.11 47.06 L130.70 48.09 L132.26 49.16 L133.79 50.28 L135.29 51.43 L136.75 52.62 L138.19 53.84 L139.59 55.09 L140.97 56.38 L142.31 57.69 L143.63 59.03 L144.91 60.41 L146.16 61.81 L147.38 63.25 L148.57 64.71 L149.72 66.21 L150.82 67.75 L151.89 69.31 L152.91 70.91 L153.88 72.55 L154.79 74.22 L155.65 75.92 L156.46 77.65 L157.20 79.41 L157.88 81.20 L158.49 83.01 L159.04 84.84 L159.52 86.70 L159.93 88.57 L160.27 90.45 L160.55 92.35 L160.77 94.26 L160.92 96.17 L161.00 98.08 L161.03 100.00 Z',
    'M150.19 100.00 L150.18 101.58 L150.13 103.15 L150.03 104.73 L149.88 106.30 L149.68 107.87 L149.43 109.43 L149.13 110.98 L148.78 112.52 L148.38 114.06 L147.93 115.57 L147.42 117.07 L146.86 118.56 L146.25 120.02 L145.59 121.45 L144.88 122.87 L144.11 124.25 L143.29 125.60 L142.43 126.93 L141.52 128.22 L140.57 129.48 L139.58 130.70 L138.55 131.89 L137.48 133.04 L136.38 134.16 L135.25 135.25 L134.08 136.30 L132.90 137.31 L131.68 138.30 L130.44 139.25 L129.18 140.17 L127.90 141.05 L126.59 141.91 L125.27 142.72 L123.92 143.51 L122.55 144.25 L121.16 144.96 L119.74 145.62 L118.31 146.25 L116.86 146.83 L115.39 147.35 L113.90 147.83 L112.39 148.26 L110.87 148.63 L109.34 148.95 L107.79 149.21 L106.24 149.42 L104.69 149.57 L103.12 149.66 L101.56 149.70 L100.00 149.68 L98.44 149.61 L96.89 149.50 L95.34 149.33 L93.79 149.13 L92.26 148.88 L90.73 148.59 L89.21 148.27 L87.70 147.91 L86.20 147.51 L84.70 147.09 L83.21 146.62 L81.74 146.13 L80.27 145.60 L78.81 145.03 L77.37 144.42 L75.93 143.78 L74.52 143.09 L73.12 142.36 L71.74 141.58 L70.39 140.76 L69.07 139.88 L67.77 138.96 L66.52 137.98 L65.30 136.96 L64.12 135.88 L62.99 134.76 L61.91 133.58 L60.87 132.37 L59.89 131.11 L58.96 129.81 L58.09 128.48 L57.27 127.12 L56.51 125.72 L55.80 124.30 L55.14 122.86 L54.53 121.40 L53.97 119.92 L53.45 118.43 L52.99 116.93 L52.56 115.41 L52.18 113.89 L51.84 112.37 L51.54 110.83 L51.28 109.29 L51.05 107.75 L50.87 106.21 L50.72 104.66 L50.62 103.11 L50.55 101.55 L50.53 100.00 L50.54 98.45 L50.61 96.89 L50.71 95.34 L50.87 93.79 L51.07 92.25 L51.31 90.71 L51.61 89.18 L51.95 87.66 L52.34 86.15 L52.78 84.66 L53.26 83.17 L53.80 81.71 L54.38 80.26 L55.00 78.83 L55.67 77.41 L56.39 76.03 L57.15 74.66 L57.95 73.32 L58.80 72.00 L59.68 70.71 L60.61 69.45 L61.58 68.21 L62.58 67.01 L63.62 65.84 L64.70 64.70 L65.82 63.60 L66.97 62.53 L68.15 61.50 L69.37 60.51 L70.62 59.56 L71.90 58.65 L73.20 57.78 L74.54 56.95 L75.90 56.16 L77.28 55.41 L78.69 54.71 L80.12 54.05 L81.56 53.43 L83.03 52.86 L84.51 52.33 L86.01 51.84 L87.52 51.40 L89.05 51.01 L90.59 50.66 L92.14 50.35 L93.70 50.10 L95.26 49.89 L96.84 49.74 L98.42 49.64 L100.00 49.59 L101.58 49.60 L103.17 49.66 L104.75 49.78 L106.32 49.96 L107.89 50.20 L109.44 50.50 L110.99 50.85 L112.51 51.27 L114.02 51.74 L115.51 52.26 L116.98 52.84 L118.42 53.47 L119.84 54.15 L121.23 54.88 L122.60 55.65 L123.94 56.45 L125.25 57.30 L126.54 58.18 L127.80 59.10 L129.03 60.04 L130.24 61.01 L131.42 62.02 L132.58 63.04 L133.71 64.10 L134.82 65.18 L135.90 66.28 L136.96 67.41 L137.99 68.57 L138.99 69.76 L139.96 70.97 L140.90 72.21 L141.80 73.47 L142.66 74.77 L143.49 76.09 L144.28 77.44 L145.02 78.82 L145.71 80.22 L146.36 81.64 L146.96 83.09 L147.51 84.56 L148.01 86.05 L148.45 87.56 L148.85 89.08 L149.19 90.62 L149.48 92.16 L149.72 93.72 L149.91 95.28 L150.05 96.85 L150.15 98.42 L150.19 100.00 Z',
    'M139.49 100.00 L139.50 101.24 L139.47 102.48 L139.39 103.72 L139.27 104.96 L139.10 106.19 L138.89 107.42 L138.64 108.64 L138.34 109.84 L138.00 111.04 L137.62 112.22 L137.19 113.39 L136.73 114.54 L136.22 115.67 L135.68 116.79 L135.10 117.88 L134.49 118.96 L133.84 120.01 L133.16 121.04 L132.45 122.05 L131.71 123.04 L130.95 124.00 L130.16 124.95 L129.34 125.87 L128.50 126.76 L127.63 127.63 L126.75 128.48 L125.83 129.30 L124.90 130.10 L123.95 130.87 L122.97 131.61 L121.97 132.32 L120.95 133.01 L119.90 133.65 L118.84 134.27 L117.75 134.85 L116.65 135.39 L115.53 135.89 L114.39 136.35 L113.24 136.77 L112.07 137.15 L110.89 137.49 L109.70 137.79 L108.50 138.04 L107.30 138.26 L106.09 138.43 L104.87 138.57 L103.66 138.67 L102.44 138.73 L101.22 138.76 L100.00 138.75 L98.78 138.72 L97.57 138.65 L96.36 138.55 L95.15 138.42 L93.94 138.27 L92.74 138.08 L91.54 137.87 L90.34 137.62 L89.15 137.35 L87.96 137.05 L86.78 136.71 L85.61 136.34 L84.45 135.93 L83.30 135.49 L82.16 135.01 L81.04 134.50 L79.93 133.94 L78.84 133.34 L77.77 132.71 L76.73 132.03 L75.71 131.32 L74.71 130.57 L73.75 129.78 L72.82 128.95 L71.91 128.09 L71.05 127.19 L70.21 126.26 L69.41 125.30 L68.65 124.32 L67.93 123.30 L67.24 122.27 L66.58 121.21 L65.97 120.13 L65.39 119.03 L64.85 117.91 L64.34 116.78 L63.87 115.63 L63.44 114.47 L63.05 113.30 L62.69 112.12 L62.37 110.93 L62.09 109.73 L61.84 108.53 L61.64 107.32 L61.47 106.10 L61.33 104.88 L61.23 103.66 L61.17 102.44 L61.15 101.22 L61.16 100.00 L61.21 98.78 L61.29 97.56 L61.40 96.35 L61.55 95.14 L61.73 93.94 L61.95 92.74 L62.19 91.55 L62.47 90.36 L62.78 89.19 L63.12 88.02 L63.49 86.86 L63.89 85.70 L64.33 84.56 L64.80 83.44 L65.30 82.32 L65.84 81.22 L66.41 80.14 L67.02 79.07 L67.66 78.02 L68.34 77.00 L69.05 75.99 L69.80 75.02 L70.58 74.06 L71.40 73.14 L72.24 72.24 L73.12 71.38 L74.03 70.55 L74.97 69.74 L75.93 68.98 L76.92 68.24 L77.94 67.54 L78.97 66.87 L80.03 66.23 L81.10 65.62 L82.19 65.05 L83.30 64.51 L84.42 64.00 L85.56 63.52 L86.70 63.07 L87.87 62.65 L89.04 62.27 L90.22 61.92 L91.42 61.60 L92.62 61.31 L93.83 61.07 L95.05 60.85 L96.28 60.68 L97.52 60.55 L98.76 60.46 L100.00 60.42 L101.24 60.42 L102.49 60.47 L103.73 60.56 L104.96 60.71 L106.19 60.90 L107.41 61.14 L108.62 61.42 L109.82 61.75 L111.00 62.13 L112.17 62.55 L113.32 63.01 L114.45 63.51 L115.56 64.04 L116.65 64.61 L117.72 65.22 L118.77 65.85 L119.80 66.52 L120.81 67.21 L121.80 67.92 L122.77 68.66 L123.72 69.43 L124.64 70.21 L125.55 71.02 L126.44 71.85 L127.30 72.70 L128.15 73.57 L128.97 74.46 L129.77 75.37 L130.55 76.31 L131.30 77.26 L132.02 78.24 L132.72 79.23 L133.39 80.25 L134.03 81.29 L134.64 82.35 L135.22 83.43 L135.76 84.52 L136.27 85.64 L136.75 86.77 L137.19 87.92 L137.59 89.08 L137.96 90.25 L138.29 91.44 L138.58 92.64 L138.83 93.85 L139.05 95.07 L139.22 96.29 L139.35 97.52 L139.44 98.76 L139.49 100.00 Z',
]


def mark_svg(size=46, dark=False):
    """OneSattva mark — the literal organic ring paths traced from
    OneSattva Brand Identity.html (the canonical cover-slide mark): each
    ring is a hand-drawn ~200-point path with a slight radius wobble
    (tree-bark texture), not a mathematically perfect circle. Earlier
    versions of this function used plain <circle> elements, which read
    as too uniform/"smooth" compared to the real mark. Geometry: 200x200
    viewBox, 3 outer rings (graphite, swapped to bone on dark backgrounds)
    + 3 inner copper rings + a radial-gradient centre glow (r=31.3)."""
    _MARK_COUNTER["n"] += 1
    gid = f"gMark{_MARK_COUNTER['n']}"
    outer = "#F7F5F2" if dark else "#111214"
    colors = [outer, outer, outer, "#B6744A", "#B6744A", "#B6744A"]
    widths = [1.3, 1.3, 1.3, 1.6, 1.6, 1.6]
    rings = ''.join(
        '<path d="' + d + '" fill="none" stroke="' + c + '" stroke-width="' + str(w) + '"/>'
        for d, c, w in zip(_MARK_RING_PATHS, colors, widths)
    )
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
<defs><radialGradient id="{gid}" cx="50%" cy="50%" r="50%">
<stop offset="0%" stop-color="#B1643A"/><stop offset="40%" stop-color="#B1643A"/>
<stop offset="54%" stop-color="#BE7C58" stop-opacity="0.72"/><stop offset="70%" stop-color="#D2A084" stop-opacity="0.4"/>
<stop offset="86%" stop-color="#E6CCB8" stop-opacity="0.14"/><stop offset="100%" stop-color="#E6CCB8" stop-opacity="0"/>
</radialGradient></defs>{rings}
<circle cx="100" cy="100" r="31.3" fill="url(#{gid})"/></svg>"""


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
[data-testid="stSidebar"] button {{ background-color: rgba(247,245,242,0.06) !important; border: 1px solid rgba(247,245,242,0.14) !important; color: #F7F5F2 !important; }}
[data-testid="stSidebar"] button:hover {{ background-color: rgba(247,245,242,0.12) !important; border-color: rgba(247,245,242,0.24) !important; }}
[data-testid="stSidebar"] button[kind="primary"] {{ background-color: var(--copper) !important; border-color: var(--copper) !important; color: #111214 !important; }}
[data-testid="stSidebar"] button[kind="primary"] * {{ color: #111214 !important; }}
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
.pc-title.done {{ text-decoration:line-through; text-decoration-color:var(--stone); }}
.consist-dot {{ width:30px; height:30px; border-radius:50%; border:1.5px solid var(--stone); display:flex; align-items:center; justify-content:center; font-size:10px; color:var(--mid); }}
.consist-dot.on {{ background:var(--copper); border-color:var(--copper); color:var(--bone); }}
.consist-dot.today {{ box-shadow:0 0 0 2.5px rgba(182,116,74,0.30); }}
.adh-bar-track {{ background:var(--stone); border-radius:20px; height:7px; overflow:hidden; }}
.adh-bar-fill {{ background:var(--copper); height:100%; border-radius:20px; }}

.goal-card {{ background:var(--forest); border-radius:12px; padding:16px 20px; margin-bottom:14px; }}
.gc-lbl {{ font-size:10px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:rgba(247,245,242,0.36); margin-bottom:5px; }}
.gc-goal {{ font-family:'Newsreader',serif; font-style:italic; font-size:15px; color:#F7F5F2; margin-bottom:14px; line-height:1.5; }}
.gc-weeks {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }}
.gc-wk {{ background:rgba(247,245,242,0.06); border-radius:8px; padding:10px; font-size:11.5px; }}
.gc-wkn {{ font-family:'JetBrains Mono',monospace; font-size:10px; color:rgba(247,245,242,0.36); margin-bottom:4px; }}
.gc-wkf {{ color:rgba(247,245,242,0.7); line-height:1.4; }}
.gc-wk.now {{ background:rgba(182,116,74,0.14); border:1px solid rgba(182,116,74,0.2); }}

.phase-timeline {{ display:flex; gap:10px; overflow-x:auto; padding-bottom:4px; margin-bottom:16px; }}
.phase-card {{ background:var(--white); border:1px solid var(--line); border-radius:12px; padding:14px 15px; min-width:190px; flex:1; }}
.phase-card.current {{ background:var(--cu-bg); border:1px solid var(--cu-bd); }}
.phase-num {{ font-family:'JetBrains Mono',monospace; font-size:10px; color:var(--mid); text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px; }}
.phase-card.current .phase-num {{ color:var(--copper); font-weight:600; }}
.phase-focus {{ font-size:13px; font-weight:500; color:var(--graphite); margin-bottom:8px; line-height:1.35; }}
.phase-meta {{ font-size:11px; color:var(--mid); line-height:1.5; }}
.phase-meta strong {{ color:var(--graphite); font-weight:500; }}

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
.tc-dots     {{ display:flex; gap:5px; }}
.tc-dot      {{ width:16px; height:16px; border-radius:50%; background:var(--copper); flex:1; max-width:20px; }}
.tc-dot-legend {{ display:flex; justify-content:space-between; font-size:10px; color:var(--stone-dk,#B4B2A9); margin-top:6px; }}
.wk-row      {{ display:flex; gap:14px; align-items:flex-end; height:90px; }}
.wk-col      {{ display:flex; flex-direction:column; align-items:center; gap:5px; flex:1; }}
.wk-bars     {{ display:flex; gap:3px; align-items:flex-end; height:66px; width:100%; justify-content:center; }}
.bar-a       {{ width:9px; border-radius:2px 2px 0 0; background:var(--copper); }}
.bar-b       {{ width:9px; border-radius:2px 2px 0 0; background:var(--stone); }}
.wk-lbl      {{ font-size:10px; color:var(--mid); }}
.wk-legend   {{ display:flex; gap:16px; margin-top:12px; font-size:11px; color:var(--mid); }}
.wk-legend .leg-dot {{ display:inline-block; width:9px; height:9px; border-radius:2px; margin-right:6px; }}

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


def db_upsert(table, data, on_conflict=None):
    """on_conflict must name the table's actual unique constraint columns —
    without it, postgrest upserts against the primary key only, so a table
    keyed by user_id (no id in `data`) silently inserts a duplicate row
    instead of updating, or errors against a unique constraint it didn't
    know to target."""
    try:
        q = supabase.table(table)
        if on_conflict:
            return q.upsert(data, on_conflict=on_conflict).execute()
        return q.upsert(data).execute()
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


# ── Knowledge admin CMS (early-tester feedback #4, Piece 1) ─────────────────
def is_admin():
    return st.session_state.get("user_email") in ADMIN_EMAILS


def get_active_knowledge_rules(user_id):
    """Global rules (user_id null) plus this specific user's practitioner-scoped
    rules, if any exist — the latter is Piece 2 territory and will just start
    returning rows once that's built, no prompt-side change needed then."""
    try:
        global_rules = supabase.table("knowledge_rules").select("*").is_("user_id", "null").eq("active", True).execute().data or []
        user_rules = supabase.table("knowledge_rules").select("*").eq("user_id", user_id).eq("active", True).execute().data or []
        return global_rules + user_rules
    except Exception:
        return []


def get_all_global_knowledge_rules():
    try:
        return supabase.table("knowledge_rules").select("*").is_("user_id", "null").order("category").order("created_at", desc=True).execute().data or []
    except Exception:
        return []


def save_knowledge_rule(category, title, content, rule_id=None):
    admin_email = st.session_state.get("user_email", "")
    if rule_id:
        existing = supabase.table("knowledge_rules").select("*").eq("id", rule_id).limit(1).execute().data
        if existing:
            e = existing[0]
            supabase.table("knowledge_rule_versions").insert({
                "rule_id": rule_id, "title": e["title"], "content": e["content"],
                "category": e["category"], "edited_by": admin_email,
            }).execute()
        supabase.table("knowledge_rules").update({
            "category": category, "title": title, "content": content, "updated_at": datetime.now().isoformat(),
        }).eq("id", rule_id).execute()
    else:
        supabase.table("knowledge_rules").insert({
            "category": category, "title": title, "content": content, "created_by": admin_email,
        }).execute()


def set_knowledge_rule_active(rule_id, active):
    supabase.table("knowledge_rules").update({"active": active}).eq("id", rule_id).execute()


def get_knowledge_rule_versions(rule_id):
    try:
        return supabase.table("knowledge_rule_versions").select("*").eq("rule_id", rule_id).order("edited_at", desc=True).execute().data or []
    except Exception:
        return []


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
        st.session_state.access_token = res.session.access_token
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
        supabase.table("onboarding").upsert(data, on_conflict="user_id").execute()
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


def import_whoop_csvs(user_id, files):
    """Shared by onboarding Step 4 (optional) and Profile & Data > Wearable Data.
    Returns (days_imported, file_results) — file_results lets the caller show
    per-file diagnostics instead of a silent "Uploaded 0 days" with no
    explanation of why a file wasn't recognized."""
    import pandas as pd
    merged = {}
    file_results = []
    for f in files:
        try:
            df = pd.read_csv(f)
        except Exception:
            file_results.append({"name": f.name, "status": "Couldn't read this as a CSV file.", "rows": 0})
            continue
        date_col = find_col(df.columns, COL_MAP["date"])
        if not date_col:
            file_results.append({"name": f.name, "status": "No recognizable date column — is this a WHOOP export?", "rows": 0})
            continue
        rows_matched = 0
        for _, row in df.iterrows():
            if pd.isna(row[date_col]):
                continue  # a blank/NaN date cell would otherwise become the literal string "nan", which Postgres rejects as an invalid date
            try:
                d = str(row[date_col])[:10]
            except Exception:
                continue
            merged.setdefault(d, {"user_id": user_id, "data_date": d})
            matched_any = False
            for field in ["recovery_score", "hrv", "resting_hr", "strain", "sleep_performance", "sleep_efficiency", "sleep_duration", "workout_strain"]:
                col = find_col(df.columns, COL_MAP[field])
                if col and col in row and pd.notna(row[col]):
                    merged[d][field] = float(row[col])
                    matched_any = True
            name_col = find_col(df.columns, COL_MAP["workout_name"])
            if name_col and name_col in row and pd.notna(row[name_col]):
                merged[d]["workout_name"] = str(row[name_col])
                matched_any = True
            if matched_any:
                rows_matched += 1
        if rows_matched:
            status = "ok"
        elif "journal" in f.name.lower():
            status = "This is your WHOOP journal (subjective daily logs) — not imported as structured data, no action needed."
        else:
            status = "Date column found, but no recognizable metric columns."
        file_results.append({"name": f.name, "status": status, "rows": rows_matched})
    for d, rec in merged.items():
        db_upsert("wearable_data", rec, on_conflict="user_id,data_date")
    return len(merged), file_results


def show_whoop_import_result(imported, file_results):
    """Shared by onboarding Step 4 and Profile & Data > Wearable Data — shows
    per-file diagnostics instead of a silent 'Uploaded 0 days' with no
    explanation of why a file wasn't recognized."""
    if imported:
        st.success(f"Uploaded {imported} day{'s' if imported != 1 else ''} of data.")
    else:
        st.warning("No importable data found in the uploaded file(s) — see details below.")
    for r in file_results:
        if r["status"] == "ok":
            st.caption(f"✓ {r['name']} — {r['rows']} day(s) recognized")
        else:
            st.caption(f"✗ {r['name']} — {r['status']}")

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


def lab_file_to_content_block(lab_file):
    """Build a proper Claude document/image content block from an uploaded lab
    file. A base64 string embedded in plain text is NOT a document Claude can
    read — it just sees a wall of characters — so this must go through the
    API's document/image content-block types instead."""
    import base64
    file_bytes = lab_file.read()
    b64 = base64.b64encode(file_bytes).decode()
    ext = lab_file.name.split(".")[-1].lower()
    if ext == "pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}}
    media_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/jpeg")
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}}


def extract_structured_lab_values(raw_values):
    """Parallel, normalized JSON representation of a report's raw_values text,
    for display (key-number cards, trend charts) — raw_values stays the
    coach's actual reasoning source, this is display-only. Canonical naming
    is the load-bearing instruction here: the same marker must get the same
    name every time or cross-report trend matching silently breaks."""
    prompt = f"""Extract every lab marker below into a structured JSON array. For each marker, output:
{{"marker": "...", "value": <number>, "unit": "...", "flag": "low"|"normal"|"high"}}

Use a stable, canonical name for each marker every time you see it — e.g. always "Vitamin D" (never "Vitamin D3" or "25-OH Vitamin D"), always "TSH" (never "Thyroid Stimulating Hormone"), always "Ferritin", always "HS-CRP" (never "hs-CRP" or "High Sensitivity CRP"). This consistency matters because these names get matched across different reports over time to build trend charts — an inconsistent name breaks that matching silently.

Only include markers with a genuine numeric value — skip anything qualitative or missing a number. Judge "flag" using functional (optimal) ranges, not just whether it falls inside the lab's own reference range.

Respond with ONLY the JSON array, nothing else.

LAB TEXT:
{raw_values}"""
    raw = ai_generate("You are OneSattva, extracting structured lab data for a patient's records.", prompt, max_tokens=1500)
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        return json.loads(match.group(0) if match else raw)
    except Exception:
        return []


def get_structured_lab_values(lab_report):
    """Lazily backfills structured_values for reports saved before this
    column existed — self-heals from the already-stored raw_values instead
    of needing a bulk migration script. Only treats a NON-empty prior result
    as "already done" — an empty/failed extraction (e.g. a parsing hiccup on
    one specific document) must retry on next view, not get stuck forever."""
    existing = lab_report.get("structured_values")
    if existing:
        try:
            parsed_existing = json.loads(existing)
            if parsed_existing:
                return parsed_existing
        except Exception:
            pass
    raw_values = lab_report.get("raw_values", "")
    if not raw_values.strip():
        return []
    parsed = extract_structured_lab_values(raw_values)
    if parsed:
        db_upsert("lab_reports", {"id": lab_report["id"], "structured_values": json.dumps(parsed)})
    return parsed


def render_lab_key_numbers(structured):
    if not structured:
        return
    cols = st.columns(4)
    for i, m in enumerate(structured):
        flag = (m.get("flag") or "normal").lower()
        flag_html = f'<div class="snap-flag">{flag}</div>' if flag != "normal" else ""
        with cols[i % 4]:
            st.markdown(f"""
<div class="snap-box" style="margin-bottom:10px">
<div class="snap-lbl">{m.get('marker','')}</div>
<div class="snap-val">{m.get('value','—')}<span style="font-size:13px;color:var(--mid)"> {m.get('unit','')}</span></div>
{flag_html}
</div>""", unsafe_allow_html=True)


def save_lab_report(user_id, report_date, text=None, file_block=None, file_label=None):
    """Shared by onboarding Step 4 and Profile & Data > Lab Reports & Documents.
    Pass either `text` (pasted values) or `file_block` + `file_label` (an uploaded
    file, built with lab_file_to_content_block).

    For file uploads this runs two passes: first extract every marker/value/range
    as plain text (stored as raw_values — this is what the coach actually reasons
    from later), then a short interpretive summary for the list preview. Storing
    only the summary would leave no real numbers anywhere for the coach to cite."""
    label = file_label or "your pasted values"
    date_note = ""
    if file_block:
        with st.spinner(f"Extracting lab values from {label}..."):
            raw_output = ai_generate(
                "You are OneSattva extracting lab data from an uploaded document/image. "
                "On the FIRST line, output the report/collection date printed on the document in the exact format "
                "'REPORT_DATE: YYYY-MM-DD' — if no date is visible anywhere on the document, output 'REPORT_DATE: UNKNOWN'. "
                "Then, starting on the next line, list every lab marker you can identify, one per line, "
                "in the format 'Marker: value unit (reference range if shown)'. Be exhaustive and precise — include every marker present, "
                "even ones without an obvious flag. Output nothing else: no commentary, no headers, no markdown.",
                [file_block, {"type": "text", "text": "Extract the report date and every lab marker/value from this document/image."}],
                max_tokens=1500)
        if raw_output.startswith("_Coach is temporarily unavailable"):
            st.error(f"Couldn't extract values from {label} — the AI service had an error. Try again in a moment.")
            return None
        first_line, _, rest = raw_output.partition("\n")
        date_match = re.match(r"REPORT_DATE:\s*(\d{4}-\d{2}-\d{2})", first_line.strip())
        raw_values = rest.strip() if date_match else raw_output.strip()
        if date_match:
            try:
                detected_date = date.fromisoformat(date_match.group(1))
                if detected_date != report_date:
                    date_note = f" — report dated {detected_date.isoformat()} (detected from the document)"
                report_date = detected_date
            except Exception:
                pass
        else:
            date_note = f" — no date found on the document, using {report_date.isoformat()}"
        interpret_input = raw_values
    else:
        raw_values = text
        interpret_input = text
    with st.spinner(f"Interpreting {label} against functional ranges..."):
        summary = ai_generate(
            "You are OneSattva, interpreting lab values against functional (optimal) ranges, not conventional population reference ranges. "
            "Respond with exactly 2-4 sentences of plain prose — no headers, no markdown formatting (no #, *, bullet points, section titles), "
            "no restating the patient's name or demographics. Just the clinical interpretation itself: what's notable and why it matters. "
            "This is a short list-preview summary, not a full report — the full protocol reasoning happens elsewhere.",
            interpret_input, max_tokens=400)
    structured = extract_structured_lab_values(raw_values)
    result = db_insert("lab_reports", {"user_id": user_id, "report_date": report_date.isoformat(), "raw_values": raw_values[:4000], "summary": summary, "structured_values": json.dumps(structured)})
    if result is None:
        st.error(f"{label} was analyzed but failed to save — please try uploading it again.")
        return None
    refresh_lab_trends(user_id)
    st.success(f"✓ {label} uploaded and analyzed{date_note}.")
    return summary


def build_lab_trends(user_id):
    labs = db_get("lab_reports", user_id, order_col="report_date")
    if len(labs) < 2:
        return ""
    labs_desc = "\n\n".join(
        f"Report dated {l.get('report_date','?')}:\n{l.get('raw_values','')}"
        for l in reversed(labs)  # oldest first, chronological
    )
    # Use the full system prompt (not a narrow one-off) so this is a genuine
    # coach's-perspective read — reasoned against this person's actual
    # symptoms, goals, and current protocol — not just a bare number diff.
    profile = db_get_single("profiles", user_id) or {}
    sys_prompt = build_system_prompt(user_id, profile, has_cycle=profile.get("has_cycle", False))
    prompt = f"""Here are this patient's lab reports across time, oldest first:

{labs_desc}

Write two things, in this order:

1. **Coach's take** — 2-4 sentences in your own voice synthesizing the overall pattern across these reports: what's genuinely improving, worsening, or stable, and what that means for this person specifically given their symptoms, goals, and current protocol. Interpret, don't just restate numbers — this is the most important part.

2. A markdown table: Marker | Direction — one tight clause per marker on whether it's improving, worsening, or stable, reasoned against functional (optimal) ranges, not just raw numeric direction. Identify every marker that appears in 2 or more of these reports (match markers by meaning even if the exact wording differs slightly across reports — e.g. "Vitamin D" and "25-OH Vitamin D" are the same marker). Only include markers that genuinely appear in 2+ reports — skip markers unique to a single report. Do NOT include the actual values/dates in this table — those are shown separately as a proper table elsewhere on the page; just the marker name and your direction judgment.

If no marker repeats across reports, skip the table entirely and write only: "No overlapping markers to compare yet — your reports test different panels.\""""
    return ai_generate(sys_prompt, prompt, max_tokens=1800)


def refresh_lab_trends(user_id):
    """Called after any lab report is saved or deleted — a changed set of
    reports is inherently something the trend view should reflect, so this
    refreshes eagerly rather than waiting on a materiality judgment (this is
    a factual comparison, not a protocol recommendation)."""
    content = build_lab_trends(user_id)
    if content:
        db_upsert("lab_trends", {"user_id": user_id, "content": content, "generated_at": date.today().isoformat()}, on_conflict="user_id")
    else:
        supabase.table("lab_trends").delete().eq("user_id", user_id).execute()

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
# NOTE ON A CONFLICT FOUND IN OneSattva_AI_Coach_KB_v3.docx (Branding folder):
# Section 05 of that doc gives a fixed "Menstrual / Follicular / Ovulatory / Luteal"
# supplement-and-food table and calls cycle-phase calibration "non-negotiable" for
# every female user. That is the same hard-coded-template problem the product
# brief's bio-individuality principle was written to eliminate (Brief Section 8:
# "the coach reasons from first principles... it does not apply a template";
# Section 13 explicitly lists "cycle phase rules applied to all females" as a
# resolved anti-pattern). Per the established rule that the product brief wins on
# conflicts, this prompt treats cycle phase as physiological context the coach
# reasons WITH, never a fixed phase->protocol lookup table — see the explicit
# line in GOVERNING PRINCIPLE below and the CYCLE DATA section further down.
# If OneSattva_AI_Coach_KB_v3.docx is ever uploaded as a live knowledge-base
# attachment, its cycle-phase table should be stripped or reframed before upload.
def build_system_prompt(user_id, profile, has_cycle=False):
    today = date.today()
    ninety_days_ago = today - timedelta(days=90)
    one_eighty_days_ago = today - timedelta(days=180)

    base = f"""You are OneSattva — a senior integrative medicine practitioner, functional nutritionist, and personal wellness coach. Today's date is {today.strftime("%A, %d %B %Y")}.

═══════════════════════════════════════════════════════
GOVERNING PRINCIPLE — BIO-INDIVIDUALITY
═══════════════════════════════════════════════════════
There is no universal rule for what this person should eat, supplement, or do. The right answer emerges only from THEIR data below — labs, check-ins, wearable trends, history, goals, location. You do not apply population defaults, fixed doses, brand lists, or templates. You reason from this individual's data to the individual answer, and you state the reasoning, not just the conclusion. If their gut data shows no issue, raw food may be exactly right for them; if it shows bloating and poor digestion, cooked food may be right — but only their data tells you which. Never assume a 28-day menstrual cycle. Never assume a location-specific brand list — derive brand and food suggestions from their actual location and what is realistically available there, asking if location is unclear. Cycle phase (where applicable) is physiological context to reason with — not a fixed phase-by-phase supplement or food template. Two people in the same phase can need different things depending on their actual labs, symptoms, and history; conclude from their data, not from a lookup table.

This prompt deliberately contains no fixed table of "functional optimal" lab ranges, no fixed dosing tables, and no static research citations — none of that is hard-coded here, by design. Draw on your own current knowledge of functional medicine, Ayurveda, TCM and clinical research — continuously, as your training and knowledge evolve — to judge what "optimal" looks like for a given marker or mechanism. But that general knowledge is a starting orientation, never the answer: bio-individuality always supersedes it. Apply what you know of current research through the lens of this specific person's actual data, never as a substitute for it.

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
RULE 8 — Every clinical or protocol-level response reasons across at least two independent lines — root-cause physiology, constitutional pattern, organ-system dynamics — and finds where they converge; single-system reasoning is a failure mode. Write the conclusion as one synthesized voice, in plain English by default: never preface, structure, or LABEL any part of a response by which tradition it came from. This means both the obvious list format ("Functional medicine says X, Ayurveda says Y, TCM says Z") AND the subtler inline version — never write "the Ayurvedic Agni impairment" or "the TCM Spleen Qi deficiency pattern"; write "digestive fire impairment" or "poor nutrient transformation and low energy reserve" instead. A bare traditional term (Agni, Qi stagnation) may be used, without its school name attached, only if it's genuinely the clearest way to say something and plain English would lose precision — even then, never pair the term with its tradition's name in the same breath. Always close with one specific, concrete next step for today or this week.
RULE 9 — When new data (a lab, a wearable import, an uploaded document) reveals something that contradicts or meaningfully updates what's in their stored profile (a new value, an implied diagnosis or medication change), say so explicitly and ask them to update their profile before you treat it as settled — e.g. "Your latest report shows X has shifted significantly since your last reading — can you confirm/update your profile so I'm working from the correct current picture?" Proceed with your interpretation, but flag that it's based on the profile as currently recorded.
RULE 10 — Be concise by default. Give the correct, most useful information in the fewest words that fully answer the question — this is not a research paper. Skip detail the person hasn't asked for; they can always ask a follow-up in Coach chat if they want more depth. Never pad with restatement, hedging, or filler. But conciseness never means stopping early: a roadmap, protocol, or answer must always cover everything it structurally needs to (every phase, every section) — cut verbosity within each part, never cut a part out. Prefer short paragraphs and tight tables over long prose.

═══════════════════════════════════════════════════════
LANGUAGE AND SAFETY STANDARDS — NON-NEGOTIABLE
═══════════════════════════════════════════════════════
You adjust wellness protocols. You do not make medical decisions, diagnose, or prescribe.
- Urgency/triage: say "adjusts your plan," "flags for attention," "worth watching," "I'm noting this for our next checkpoint." Never say "urgent," "dangerous," "seek immediate care," "this is an emergency," or otherwise make a clinical urgency determination.
- Medical advice (PRESCRIPTION MEDICATION ONLY): say "discuss this with your physician — here is the mechanism and why this conversation is worth having." Never say "change your medication," "stop taking X," "increase your dose," or make any prescription-level decision. This rule applies to prescription drugs only — it does NOT apply to supplements. Supplements are your domain: recommend them directly, with exact dose, form, and timing, the way a functional nutritionist or integrative practitioner would. Do not defer supplement dosing to "discuss with your physician" — that hedge is reserved for prescription medication changes.
- Diagnosis: say "this pattern is consistent with...", "your functional picture suggests...", "the data points toward...". Never say "you have X condition" or assert a diagnosis as settled.
- Outcomes: say "supports," "may help," "research associates X with Y." Never say "cures," "treats," "eliminates," "reverses," or claim a guaranteed therapeutic outcome.
- Research: describe mechanism and established clinical consensus; state plainly when evidence is emerging vs well-established. Never cite a specific study you aren't certain exists and says what you claim.
- Never withhold a genuine safety concern to maintain a positive tone — always state it, and always state why it matters.
- Never sound like a chatbot: no "Great question!", "Certainly!", "Absolutely!", or hollow affirmations.
- Never suggest reducing exercise or movement for a motivated, consistent user without first ruling out a metabolic or hormonal driver — work with their routine, not against it.
- Never ask a clarifying question whose answer already exists in their history.
- Never alarm without pairing it to a specific, actionable next step.

═══════════════════════════════════════════════════════
THREE FRAMEWORKS — READ SIMULTANEOUSLY, FIND THE CONVERGENCE
═══════════════════════════════════════════════════════
FUNCTIONAL MEDICINE — root cause, lab interpretation against functional (optimal) ranges not conventional population ranges, HPA axis, gut-brain-thyroid axis, microbiome, order of operations (gut before hormones, HPA before sleep supplements).
AYURVEDA — Prakriti (constitution), Agni (digestive fire — assess from check-in bloating/digestion/post-meal energy before any food recommendation), Dinacharya (daily rhythm), Ojas (the endpoint state protocols build toward).
TCM — organ system patterns (Liver Qi stagnation, Kidney Yang deficiency, Spleen Qi deficiency), Qi and Blood as functional currency, the 24-hour organ clock for supplement/activity timing, Five Element clustering.
Do not answer framework-by-framework. Find where they converge — that convergence is the most robust recommendation.

For complex questions, structure as: (1) what is happening — mechanism across frameworks, (2) what it means for this person specifically — cite their actual data, (3) the specific recommendation with rationale, (4) realistic timeline, (5) what to watch for.

"""

    rules = get_active_knowledge_rules(user_id)
    if rules:
        base += "═══════════════════════════════════════════════════════\nCURATED CLINICAL GUIDANCE\n═══════════════════════════════════════════════════════\n"
        base += "Notes curated by OneSattva's clinical team. Treat these as expert context to reason WITH — same status as your own training knowledge — never as a population default that overrides what this specific person's own data shows. Bio-individuality above always wins if the two conflict.\n"
        for r in rules:
            base += f"- [{r.get('category','')}] {r.get('title','')}: {r.get('content','')}\n"
        base += "\n"

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

    if profile:
        lifestyle_lines = []
        if profile.get("activity_level") or profile.get("exercise_routine") or profile.get("alcohol") or profile.get("smoking"):
            lifestyle_lines.append(f"Activity: {profile.get('activity_level','?')} | Alcohol: {profile.get('alcohol','?')} | Smoking: {profile.get('smoking','?')} | Exercise: {profile.get('exercise_routine','') or 'not stated'}")
        if profile.get("sleep_bedtime") or profile.get("sleep_quality"):
            lifestyle_lines.append(f"Sleep: bedtime {profile.get('sleep_bedtime','?')}, wake {profile.get('sleep_wake_time','?')}, duration {profile.get('sleep_duration','?')}, quality {profile.get('sleep_quality','?')}/10. Challenges: {profile.get('sleep_challenges','') or 'none stated'}")
        if profile.get("first_meal") or profile.get("food_prefs") or profile.get("meals_per_day"):
            lifestyle_lines.append(f"Eating schedule: first meal {profile.get('first_meal','?')}, last meal {profile.get('last_meal','?')}, {profile.get('meals_per_day','?')}, eating out {profile.get('eating_out','?')}. Food preferences: {profile.get('food_prefs','') or 'not stated'}")
        if profile.get("stress_level") or profile.get("stressors") or profile.get("symptoms"):
            lifestyle_lines.append(f"Stress: {profile.get('stress_level','?')}/10. Stressors: {profile.get('stressors','') or 'none stated'}. Symptoms: {profile.get('symptoms','') or 'none stated'}. Other: {profile.get('anything_else','') or 'none'}")
        if lifestyle_lines:
            base += "\nLIFESTYLE:\n" + "\n".join(lifestyle_lines) + "\n"

    notes = db_get_single("profile_notes", user_id)
    if notes and notes.get("notes"):
        base += f"\nFAMILY HISTORY / PAST SURGERIES:\n{notes['notes']}\n"

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
                base += f"- {l.get('report_date','')}: {l.get('summary','')}\n  Values: {str(l.get('raw_values',''))[:1200]}\n"
        else:
            base += "⚠️ NO CURRENT LABS. Flag this to the patient explicitly — do not treat older values as current status.\n"
        if recent_labs:
            base += "RECENT (91-180 days — trend only):\n"
            for l in recent_labs:
                base += f"- {l.get('report_date','')}: {l.get('summary','')}\n  Values: {str(l.get('raw_values',''))[:800]}\n"
        if historical_labs:
            base += "HISTORICAL (>180 days — context only, retest needed):\n"
            for l in historical_labs:
                base += f"- {l.get('report_date','')}: {l.get('summary','')}\n  Values: {str(l.get('raw_values',''))[:800]}\n"
        if len(current_labs) + len(recent_labs) + len(historical_labs) > 1:
            base += "When the same marker appears in more than one report above, explicitly compare the values and state the direction of change (improving/worsening/stable) — don't just describe each report in isolation.\n"
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
        metric_labels = {m["metric_key"]: m["label"] for m in db_get("checkin_metric_defs", user_id)}
        for c in reversed(checkins[:14]):
            custom = json.loads(c.get("custom_metrics") or "{}")
            custom_str = " · ".join(f"{metric_labels.get(k, k)} {v}" for k, v in custom.items())
            base += (f"- {c.get('checkin_date','')}: Energy {c.get('energy','?')}/10 · Clarity {c.get('mental_clarity','?')}/10 · "
                     f"Sleep quality {c.get('sleep_quality','?')}/10 ({c.get('sleep_hours','?')}hrs) · Mood {c.get('mood','?')}/10"
                     + (f" · {custom_str}" if custom_str else "") +
                     f" · Workout: {c.get('workout','?')} · Notes: {c.get('notes','')}\n")
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
            base += "Reason from this phase as physiological context alongside their actual labs, check-ins and symptoms — do not apply a fixed per-phase supplement/food template regardless of their individual data.\n"

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
    flash = st.session_state.pop("auth_flash", None)

    # st.container(key=...) emits a real DOM node with a stable class
    # (.st-key-auth_card) — this lets the bone card background wrap the
    # logo AND the actual widgets together. Splitting an st.markdown() HTML
    # div open/close around widgets does NOT work in Streamlit: widgets
    # always render outside the markdown block, which is why the card used
    # to show as an empty box with the form floating below it.
    st.markdown("""
<style>
.st-key-auth_card {
  background: var(--bone); border-radius: 18px; padding: 44px;
  box-shadow: 0 8px 48px rgba(17,18,20,0.18);
  max-width: 460px; margin: 48px auto 0;
}
.st-key-auth_card label, .st-key-auth_card p, .st-key-auth_card span { color: var(--graphite) !important; }
</style>
""", unsafe_allow_html=True)

    with st.container(key="auth_card"):
        st.markdown(f"""
<div style="display:flex;flex-direction:column;align-items:center;margin-bottom:28px;gap:8px">
{mark_svg(44 if mode=='login' else 36)}
<span style="font-family:'Newsreader',serif;font-weight:400;font-size:{26 if mode=='login' else 22}px;letter-spacing:-0.02em;color:#111214;line-height:1">OneSattva</span>
<div style="font-family:'Newsreader',serif;font-style:italic;font-size:12.5px;color:var(--copper)">Health, understood.</div>
</div>
""", unsafe_allow_html=True)

        if flash:
            st.success(flash)

        if True:
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
                            if "not confirmed" in err.lower() or "not_confirmed" in err.lower():
                                st.error("Check your inbox to confirm your email before signing in. Check spam if you don't see it within a minute.")
                            elif "invalid" in err.lower() or "credentials" in err.lower():
                                st.error("Couldn't sign in — wrong email or password. If you haven't signed up yet, use 'Create an account' below.")
                            else:
                                st.error(f"Couldn't sign in: {err}")
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
                            st.session_state.auth_flash = "Account created! Check your inbox to verify your email before signing in. Check your spam folder if you don't see it within a minute."
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
def set_ob_step(user_id, step):
    """Advance the onboarding step and persist it, so a forced logout or a
    server restart mid-onboarding resumes here instead of restarting at step 1."""
    st.session_state.ob_step = step
    save_onboarding_state(user_id, {"current_step": step})


def show_onboarding(user_id, profile):
    inject_css(auth_mode=False)
    if "ob_step" not in st.session_state:
        ob_state = get_onboarding_state(user_id)
        st.session_state.ob_step = (ob_state or {}).get("current_step") or 1
        # Only true once, right when a session is restored from a previous
        # visit — not on every step transition within one sitting — so the
        # "welcome back" framing doesn't show up after every normal Continue click.
        st.session_state.ob_just_resumed = st.session_state.ob_step > 1
    step = st.session_state.ob_step
    st.markdown('<div style="max-width:820px;margin:0 auto;padding-top:18px">', unsafe_allow_html=True)
    onboarding_progress(step)

    if st.session_state.get("ob_just_resumed"):
        st.markdown(f'<div class="cp-banner" style="margin-bottom:16px"><strong>Welcome back.</strong> You\'re right where you left off — Step {step} of {len(ONBOARDING_STEPS)}.</div>', unsafe_allow_html=True)
    else:
        st.caption("Your progress saves automatically as you go — pause anytime and pick up right where you left off.")

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
                set_ob_step(st.session_state.user_id, back_step)
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
    existing_city, existing_country = split_location((p.get("location") or ""))
    c1, c2 = st.columns(2)
    with c1:
        dob = st.date_input("Date of birth", value=date.fromisoformat(p["dob"]) if p.get("dob") else date(1990, 1, 1), min_value=date(1920, 1, 1), max_value=date.today())
        cc1, cc2 = st.columns(2)
        country = cc1.selectbox("Country", COUNTRIES, index=COUNTRIES.index(existing_country) if existing_country in COUNTRIES else len(COUNTRIES) - 1)
        city = cc2.text_input("City", value=existing_city, placeholder="e.g. Mumbai")
        height_cm = st.number_input("Height (cm)", min_value=100, max_value=230, value=int(p.get("height_cm") or 170))
        weight_kg = st.number_input("Weight (kg)", min_value=30, max_value=250, value=int(p.get("weight_kg") or 70))
    with c2:
        sex = st.selectbox("Biological sex", ["Male", "Female", "Intersex", "Prefer not to say"], index=["Male", "Female", "Intersex", "Prefer not to say"].index(p.get("sex")) if p.get("sex") in ["Male", "Female", "Intersex", "Prefer not to say"] else 0)
        blood_group = st.selectbox("Blood group (optional)", BLOOD_GROUPS, index=selectbox_index(BLOOD_GROUPS, p.get("blood_group"), default=len(BLOOD_GROUPS) - 1))
        eating_pattern = st.selectbox("Eating pattern", ["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"], index=["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"].index(p.get("eating_pattern")) if p.get("eating_pattern") in ["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"] else 0)
        occupation = st.text_input("Occupation (optional)", value=(p.get("occupation") or ""), placeholder="e.g. Software engineer, teacher, homemaker")

    has_cycle = None
    if sex in ("Female", "Intersex"):
        st.markdown('<div class="sl">Cycle tracking</div>', unsafe_allow_html=True)
        cycle_answer = st.radio("Do you currently have a menstrual cycle to track?", ["Yes", "No", "Not sure"], horizontal=True,
                                 index={"Yes": 0, "No": 1, "Not sure": 2}.get(st.session_state.get("ob_cycle_answer"), None))
        has_cycle = cycle_answer == "Yes"
        st.session_state.ob_cycle_answer = cycle_answer
        if not has_cycle:
            st.caption("No cycle-related UI, prompts, or coaching will be shown anywhere in the app. You can change this later in Profile & Data.")

    def go_next():
        location = ", ".join(x for x in [city.strip(), country] if x)
        db_upsert("profiles", {
            "id": user_id, "dob": dob.isoformat(), "location": location,
            "height_cm": height_cm, "weight_kg": weight_kg, "sex": sex,
            "blood_group": blood_group, "eating_pattern": eating_pattern, "occupation": occupation,
            "has_cycle": bool(has_cycle) if has_cycle is not None else False,
            "full_name": p.get("full_name") or st.session_state.get("user_email", ""),
        })
        set_ob_step(user_id, 2)
        st.rerun()

    ob_nav(back_step=None, on_continue=go_next)


# ── Step 2 — Health history ───────────────────────────────────────────────
def onboarding_step2(user_id):
    st.markdown('<div class="pg-title">Your health history</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Nothing here is mandatory — skip anything you\'re unsure about. Just the names for now; your coach will ask about dose and timing when it\'s actually relevant, so this doesn\'t turn into a form marathon.</div>', unsafe_allow_html=True)

    row_placeholders = {
        ("ob_conditions", "Condition"): "e.g. Hypothyroidism",
        ("ob_meds", "Medication"): "e.g. Metformin",
        ("ob_supps", "Supplement"): "e.g. Vitamin D3",
    }
    for key, label, cols in [("ob_conditions", "Diagnosed conditions", ["Condition"]),
                              ("ob_meds", "Current medications", ["Medication"]),
                              ("ob_supps", "Current supplements", ["Supplement"])]:
        if key not in st.session_state:
            st.session_state[key] = [{c: "" for c in cols}]
        st.markdown(f'<div class="sl">{label}</div>', unsafe_allow_html=True)
        for i, row in enumerate(st.session_state[key]):
            rcols = st.columns(len(cols))
            for j, c in enumerate(cols):
                row[c] = rcols[j].text_input(c, value=row.get(c, ""), key=f"{key}_{i}_{j}", label_visibility="collapsed" if i > 0 else "visible", placeholder=row_placeholders.get((key, c), c))
        if st.button(f"+ Add another", key=f"add_{key}"):
            st.session_state[key].append({c: "" for c in cols})
            st.rerun()

    c1, c2 = st.columns(2)
    family_history = c1.text_area("Family history (optional)", value=st.session_state.get("ob_family_history", ""), placeholder="e.g. Mother: hypothyroidism · Father: type 2 diabetes")
    surgeries = c2.text_area("Past surgeries or significant events (optional)", value=st.session_state.get("ob_surgeries", ""), placeholder="e.g. Appendectomy (2015), C-section (2019)")

    def go_next():
        st.session_state.ob_family_history = family_history
        st.session_state.ob_surgeries = surgeries
        # Re-visiting this step (e.g. after a forced logout mid-onboarding) must not
        # re-insert rows already saved from a prior pass — check by name first.
        existing_conditions = {c.get("condition", "").strip().lower() for c in db_get("medical_history", user_id)}
        existing_meds = {m.get("name", "").strip().lower() for m in db_get("medications", user_id)}
        existing_supps = {s.get("name", "").strip().lower() for s in db_get("supplements", user_id)}
        for row in st.session_state.ob_conditions:
            if row.get("Condition", "").strip() and row["Condition"].strip().lower() not in existing_conditions:
                db_insert("medical_history", {"user_id": user_id, "condition": row["Condition"], "notes": row.get("Since / notes", "")})
        for row in st.session_state.ob_meds:
            if row.get("Medication", "").strip() and row["Medication"].strip().lower() not in existing_meds:
                db_insert("medications", {"user_id": user_id, "name": row["Medication"], "dose": row.get("Dose", ""), "frequency": row.get("Timing", ""), "active": True})
        for row in st.session_state.ob_supps:
            if row.get("Supplement", "").strip() and row["Supplement"].strip().lower() not in existing_supps:
                db_insert("supplements", {"user_id": user_id, "name": row["Supplement"], "dose": row.get("Dose", ""), "timing": row.get("Timing", ""), "active": True})
        notes_text = f"Family history: {family_history}\nPast surgeries/events: {surgeries}" if (family_history or surgeries) else ""
        if notes_text:
            db_upsert("profile_notes", {"user_id": user_id, "notes": notes_text}, on_conflict="user_id")
        set_ob_step(user_id, 3)
        st.rerun()

    ob_nav(back_step=1, on_continue=go_next)


def _render_ob_reflection(cache_key, sig, has_content, build_prompt, spinner_text):
    """Coach-voice reaction to what the person just entered on the previous step,
    cached against a signature of that step's inputs so Back + edit regenerates it."""
    if st.session_state.get(f"{cache_key}_sig") != sig:
        if has_content:
            with st.spinner(spinner_text):
                st.session_state[cache_key] = ai_generate(
                    "You are OneSattva, a warm, direct integrative health coach reacting briefly to a new "
                    "patient's intake data mid-onboarding. This is not advice or a plan — just a short, "
                    "specific reaction showing you're actually reading what they wrote before continuing "
                    "the intake.",
                    build_prompt(), max_tokens=150)
        else:
            st.session_state[cache_key] = None
        st.session_state[f"{cache_key}_sig"] = sig
    reflection = st.session_state.get(cache_key)
    if reflection:
        st.markdown(f"""
<div class="insight-box">
<div class="ib-lbl">✦ OneSattva Coach</div>
<div class="ib-txt">{reflection}</div>
</div>""", unsafe_allow_html=True)


# ── Step 3 — Lifestyle and goals ──────────────────────────────────────────
def onboarding_step3(user_id):
    st.markdown('<div class="pg-title">Your lifestyle and goals</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">The more specific you are here, the more precisely the coach can build your protocol.</div>', unsafe_allow_html=True)

    conditions = [r.get("Condition", "").strip() for r in st.session_state.get("ob_conditions", []) if r.get("Condition", "").strip()]
    meds = [r.get("Medication", "").strip() for r in st.session_state.get("ob_meds", []) if r.get("Medication", "").strip()]
    supps = [r.get("Supplement", "").strip() for r in st.session_state.get("ob_supps", []) if r.get("Supplement", "").strip()]
    family_history = st.session_state.get("ob_family_history", "")
    surgeries = st.session_state.get("ob_surgeries", "")
    step2_sig = repr((conditions, meds, supps, family_history, surgeries))

    def build_step3_prompt():
        parts = []
        if conditions: parts.append(f"Diagnosed conditions: {', '.join(conditions)}")
        if meds: parts.append(f"Current medications: {', '.join(meds)}")
        if supps: parts.append(f"Current supplements: {', '.join(supps)}")
        if family_history.strip(): parts.append(f"Family history: {family_history}")
        if surgeries.strip(): parts.append(f"Past surgeries/events: {surgeries}")
        return ("A new patient just shared this health history during onboarding: " + "; ".join(parts) +
                ". In 1-2 sentences, in your own voice, briefly note what stands out to you and why it's "
                "relevant — no advice or plan yet, you're about to ask about their lifestyle and goals next.")

    _render_ob_reflection("ob_step3_reflection", step2_sig, bool(conditions or meds or supps or family_history.strip() or surgeries.strip()),
                           build_step3_prompt, "Coach is reading your history...")

    primary_goal = st.text_area("Primary health goal — in your own words", value=st.session_state.get("ob_primary_goal", ""), height=80, placeholder="e.g. Improve energy and fix chronic bloating")

    lp = db_get_single("profiles", user_id) or {}

    st.markdown('<div class="sl">Diet & activity</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    activity_level = c1.selectbox("Activity level", ACTIVITY_LEVELS, index=selectbox_index(ACTIVITY_LEVELS, lp.get("activity_level")))
    restrictions = c2.text_input("Dietary restrictions or intolerances", value=(lp.get("allergies") or ""), placeholder="e.g. Lactose intolerant, gluten-free, tree nut allergy")
    alcohol = c1.selectbox("Alcohol consumption", ALCOHOL_LEVELS, index=selectbox_index(ALCOHOL_LEVELS, lp.get("alcohol")))
    smoking = c2.selectbox("Smoking / tobacco", SMOKING_LEVELS, index=selectbox_index(SMOKING_LEVELS, lp.get("smoking")))
    exercise_routine = st.text_area("Exercise routine", value=(lp.get("exercise_routine") or ""), height=60, placeholder="e.g. Weight training 4x/week, occasional running")

    st.markdown('<div class="sl">Sleep</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    bedtime = dropdown_with_other(c1, "Typical bedtime", BEDTIME_OPTIONS, (lp.get("sleep_bedtime") or ""), key="ob_bedtime")
    wake_time = dropdown_with_other(c2, "Typical wake time", WAKE_TIME_OPTIONS, (lp.get("sleep_wake_time") or ""), key="ob_wake_time")
    sleep_duration = dropdown_with_other(c3, "Average sleep duration", SLEEP_DURATION_OPTIONS, (lp.get("sleep_duration") or ""), key="ob_sleep_duration", placeholder="e.g. 6.5 hrs")
    sleep_quality = st.slider("Sleep quality (self-rated)", 1, 10, int(lp.get("sleep_quality") or 5))
    sleep_challenges = st.text_area("Sleep challenges (optional)", value=(lp.get("sleep_challenges") or ""), height=50, placeholder="e.g. Wake around 3am and struggle to fall back asleep")

    st.markdown('<div class="sl">Eating schedule</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    first_meal = dropdown_with_other(c1, "First meal time", FIRST_MEAL_OPTIONS, (lp.get("first_meal") or ""), key="ob_first_meal")
    last_meal = dropdown_with_other(c2, "Last meal time", LAST_MEAL_OPTIONS, (lp.get("last_meal") or ""), key="ob_last_meal")
    meals_per_day = c1.selectbox("Meals per day", MEALS_PER_DAY_OPTIONS, index=selectbox_index(MEALS_PER_DAY_OPTIONS, lp.get("meals_per_day")))
    eating_out = c2.selectbox("Eating out / ordering in", EATING_OUT_LEVELS, index=selectbox_index(EATING_OUT_LEVELS, lp.get("eating_out")))
    food_prefs = st.text_area("Food preferences or patterns the coach should know about (optional)", value=(lp.get("food_prefs") or ""), height=60, placeholder="e.g. Prefer home-cooked meals, avoid processed sugar, love spicy food")

    st.markdown('<div class="sl">Stress & wellbeing</div>', unsafe_allow_html=True)
    stress_level = st.slider("Current stress level", 1, 10, int(lp.get("stress_level") or 5))
    stressors = st.text_input("Primary stressors", value=(lp.get("stressors") or ""), placeholder="e.g. Work deadlines, financial pressure, caregiving")
    symptoms = st.text_area("Current symptoms or main concerns — in your own words", value=(lp.get("symptoms") or ""), height=70, placeholder="e.g. Afternoon energy crashes, bloating after meals, brain fog")
    anything_else = st.text_area("Anything else you'd like your coach to know (optional)", value=(lp.get("anything_else") or ""), height=50, placeholder="e.g. Upcoming travel, a recent life event, a specific worry")

    st.markdown('<div class="sl">Additional goals</div>', unsafe_allow_html=True)
    if "ob_extra_goals" not in st.session_state:
        st.session_state.ob_extra_goals = []
    existing_goal_texts = {g.get("goal", "") for g in st.session_state.ob_extra_goals}
    st.caption("Tap a suggestion to add it, or write your own below.")
    sugg_cols = st.columns(4)
    for i, sug in enumerate(GOAL_SUGGESTIONS):
        with sugg_cols[i % 4]:
            if sug not in existing_goal_texts and st.button(sug, key=f"goalsugg_{i}", use_container_width=True):
                st.session_state.ob_extra_goals.append({"goal": sug, "timeframe": "3 months"})
                st.rerun()
    for i, g in enumerate(st.session_state.ob_extra_goals):
        gc1, gc2 = st.columns([3, 1])
        g["goal"] = gc1.text_input("Goal", value=g.get("goal", ""), key=f"eg_{i}", label_visibility="collapsed", placeholder="e.g. Run a 10k by June")
        g["timeframe"] = gc2.selectbox("Timeframe", ["1 month", "3 months", "6 months", "Ongoing"], key=f"egt_{i}", label_visibility="collapsed")
    if st.button("+ Add goal"):
        st.session_state.ob_extra_goals.append({"goal": "", "timeframe": "3 months"})
        st.rerun()

    has_cycle = lp.get("has_cycle", False)
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
        db_upsert("profiles", {
            "id": user_id, "activity_level": activity_level, "alcohol": alcohol, "smoking": smoking,
            "exercise_routine": exercise_routine, "sleep_bedtime": bedtime, "sleep_wake_time": wake_time,
            "sleep_duration": sleep_duration, "sleep_quality": int(sleep_quality), "sleep_challenges": sleep_challenges,
            "first_meal": first_meal, "last_meal": last_meal, "meals_per_day": meals_per_day, "eating_out": eating_out,
            "food_prefs": food_prefs, "stress_level": int(stress_level), "stressors": stressors,
            "symptoms": symptoms, "anything_else": anything_else, "allergies": restrictions.strip(),
        })
        if has_cycle and cycle_last_start and cycle_avg_len:
            db_upsert("cycle_data", {"user_id": user_id, "last_period_start": cycle_last_start.isoformat(),
                                      "avg_cycle_length": int(cycle_avg_len), "period_duration": int(cycle_period_dur or 5)}, on_conflict="user_id")
        set_ob_step(user_id, 4)
        st.rerun()

    ob_nav(back_step=2, on_continue=go_next)


# ── Step 4 — Labs ──────────────────────────────────────────────────────────
def onboarding_step4(user_id):
    st.markdown('<div class="pg-title">Your labs</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Labs are not optional — they\'re the foundation of a precise assessment. We need them to give you specific guidance rather than general recommendations. You have 7 days to upload your first report — your plan recommendation will be provisional until then.</div>', unsafe_allow_html=True)

    lp = db_get_single("profiles", user_id) or {}
    primary_goal = st.session_state.get("ob_primary_goal", "")
    symptoms = lp.get("symptoms", "") or ""
    step3_sig = repr((primary_goal, symptoms))

    def build_step4_prompt():
        return (f"A new patient's primary goal is: {primary_goal or 'not stated'}. "
                f"Their current symptoms/concerns: {symptoms or 'not stated'}. "
                "In 1-2 sentences, in your own voice, tell them specifically why labs matter for THIS "
                "goal/symptom picture — name the kind of thing you'd expect labs to reveal for someone "
                "with exactly this profile. No generic 'labs are important' filler, no plan yet.")

    _render_ob_reflection("ob_step4_reflection", step3_sig, bool(primary_goal.strip() or symptoms.strip()),
                           build_step4_prompt, "Coach is connecting the dots...")

    if st.session_state.get("ob_show_panel"):
        if "ob_recommended_panel" not in st.session_state:
            conditions = ", ".join(r.get("Condition", "") for r in st.session_state.get("ob_conditions", []) if r.get("Condition"))
            goal = st.session_state.get("ob_primary_goal", "")
            prompt = f"Patient's stated conditions: {conditions or 'none stated'}. Primary goal: {goal or 'not yet stated'}. Suggest the 12-20 most clinically relevant lab markers for this specific person to test first, grouped by category, in a short markdown table. Be specific to their picture — not a generic panel."
            with st.spinner("Coach is selecting the most relevant markers for you..."):
                st.session_state.ob_recommended_panel = ai_generate(
                    "You are OneSattva, a functional medicine practitioner selecting a lab panel for a specific new patient based on what little is known so far.",
                    prompt, max_tokens=1200)
        st.markdown(st.session_state.ob_recommended_panel)
    elif st.button("Confused about which tests to get? Let OneSattva guide you →"):
        st.session_state.ob_show_panel = True
        st.rerun()

    with st.expander("Upload or paste your lab values", expanded=True):
        report_date = st.date_input("Report date", value=date.today(), help="For uploaded files, we'll try to read the actual date off the document and use that instead — this is only the fallback if we can't find one, or if you're pasting values instead of uploading a file.")
        lab_files = st.file_uploader("Upload lab report(s) (PDF or image)", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True, help="We'll extract and interpret the values automatically. You can upload more than one file.")
        raw_values = st.text_area("Or paste values directly (marker: value, one per line, or freeform)", height=120,
                                   placeholder="e.g.\nVitamin D: 28 ng/mL\nTSH: 3.2 mIU/L\nFerritin: 45 ng/mL")

        if st.button("Upload & analyse"):
            attempted = 0
            saved = 0
            if raw_values.strip():
                attempted += 1
                if save_lab_report(user_id, report_date, text=raw_values.strip()) is not None:
                    saved += 1
            for lab_file in (lab_files or []):
                attempted += 1
                if save_lab_report(user_id, report_date, file_block=lab_file_to_content_block(lab_file), file_label=lab_file.name) is not None:
                    saved += 1
            if attempted == 0:
                st.warning("Upload a file or paste your values first.")
            elif saved:
                st.session_state.ob_labs_uploaded = True

    with st.expander("Optional: add wearable data (WHOOP CSV export)"):
        st.caption("Not required to continue — you can also add this later from Profile & Data.")
        wearable_files = st.file_uploader("Upload your WHOOP export CSVs", accept_multiple_files=True, type="csv", key="ob_wearable_files",
                                           help="Typically named physiological_cycles.csv, sleeps.csv, workouts.csv, journal_entries.csv — these are just examples of what WHOOP usually calls them, the filenames don't need to match exactly. We match by column headers inside each file, not the filename.")
        if wearable_files and st.button("Upload files", key="ob_wearable_upload_btn"):
            imported, file_results = import_whoop_csvs(user_id, wearable_files)
            show_whoop_import_result(imported, file_results)

    skipped = not st.session_state.get("ob_labs_uploaded", False)
    if skipped:
        st.caption("No labs yet — that's fine. You have 7 days. Your assessment will be marked provisional until labs are in.")

    def go_next():
        set_ob_step(user_id, 5)
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

Write a short, direct, first-person clinical read in your voice, covering:
1. What you see in the picture — the likely root drivers. Reason across root-cause physiology, constitution, and organ-system patterns in your head, then write the conclusion as ONE synthesized read, not a list of separate systems. Do not open by naming or cataloguing the frameworks you're drawing from (e.g. "functional medicine says... Ayurveda says... TCM says...") — this is the very first thing this person will ever read from you, and it should sound like one voice, not three. A traditional term (Agni, Qi stagnation, HPA axis) can surface in passing if it sharpens a specific point, never as the framing device.
{"2. Explicitly connect what your labs show to the specific symptoms you described — for each notable/flagged marker, say plainly what it likely explains about how you've been feeling, not just that the marker is off. This correlation is the most important part of this read." if labs_present else "2. What your symptoms suggest is likely happening even without labs yet, and which specific markers would confirm it."}
3. Which ONE plan mode you recommend with explicit reasoning.

{"220-320" if labs_present else "180-280"} words. End with one line stating the recommended mode name clearly, e.g. "I'd recommend Restore, our 90-day programme."
"""
        with st.spinner("Your coach is reading your full picture..."):
            analysis = ai_generate(sys_prompt, prompt, max_tokens=1100)
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
        set_ob_step(user_id, 6)
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
        db_upsert("roadmaps", {"user_id": user_id, "plan_mode": st.session_state.get("ob_plan_mode", recommended), "committed": False}, on_conflict="user_id")
        set_ob_step(user_id, 7)
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
        phase_count = {"Reset": 2, "Restore": 3, "Transform": 4, "Sustain": 3}.get(plan_mode, 3)
        prompt = f"""Generate a {plan_mode} programme roadmap, duration {dur_label}, in exactly {phase_count} phases.
{'Labs are not yet available — generate this roadmap clearly marked PROVISIONAL, with a note it becomes definitive once labs are analysed.' if not labs_present else ''}

Be concise and systematic — this must cover all {phase_count} phases completely within the length budget. Favour short paragraphs and tight bullet points over prose. Do not let earlier phases run long at the expense of later ones: budget roughly equal space per phase and stop elaborating once the essential change, mechanism, and action are stated.

FORMAT (keep to this structure exactly, {phase_count} phases total):
## Your {plan_mode} Programme — Generated {date.today().strftime('%-d %B %Y')}
One sentence on what this programme addresses, grounded in this specific person's data — not generic.

## Phase Timeline
Table: Phase | Focus | Key milestones | Checkpoint — one row per phase, all {phase_count} phases, terse.

## Phase 1 — [Title]: [duration]
3-5 bullet points max: what changes, why (root mechanism in one clause), specific supplement/nutrition/training changes with exact doses where the data supports it.
**Retest at checkpoint:** [markers chosen for this person, comma-separated]
**What success looks like:** [one line, specific to their stated goals]

[Repeat this exact structure for every phase up to Phase {phase_count} — do not skip or truncate any phase]

## If Progress Stalls
[Escalation path, 2-3 sentences]

**Start today:** [one specific immediate action]
"""
        with st.spinner(f"Building your {plan_mode} roadmap..."):
            st.session_state.ob_roadmap_text = ai_generate(sys_prompt, prompt, max_tokens=8000)

    first_name = ((profile or {}).get("full_name") or "").split(" ")[0] or "there"
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
        set_ob_step(user_id, 6)
        st.session_state.pop("ob_roadmap_text", None)
        st.rerun()

    def commit():
        labs_present = bool(db_get("lab_reports", user_id))
        db_upsert("roadmaps", {
            "user_id": user_id, "plan_mode": plan_mode, "roadmap_text": st.session_state.ob_roadmap_text,
            "committed": True, "generated_at": date.today().isoformat(), "phase_start_date": date.today().isoformat(),
            "provisional": not labs_present, "start_confirmed": False,
        }, on_conflict="user_id")
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

        name = (profile.get("full_name") or "") if profile else ""
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
        if is_admin():
            nav_items.append(("admin", "⚙ Knowledge admin"))
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
TRIAGE_WEIGHT = {"now": 3, "watch": 2, "background": 1}


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
    for p in priorities:
        p["done"] = False
    supabase.table("daily_priorities").upsert({"user_id": user_id, "for_date": today_str, "priorities_json": json.dumps(priorities)}, on_conflict="user_id,for_date").execute()
    return priorities


def toggle_priority_done(user_id, for_date_str, priorities, index):
    priorities[index]["done"] = not priorities[index].get("done", False)
    supabase.table("daily_priorities").upsert({"user_id": user_id, "for_date": for_date_str, "priorities_json": json.dumps(priorities)}, on_conflict="user_id,for_date").execute()


def compute_priority_adherence(user_id, today):
    """Weighted completion this week vs the person's own trailing baseline — 'off track' is a
    real drop from their norm, not a universal number, so someone who's always around 50% doesn't
    get nudged for being themselves. Falls back to a flat 50% floor for their first weeks, before
    there's enough history to know what's normal for them."""
    rows = db_get("daily_priorities", user_id, order_col="for_date", limit=28)
    week_start = today - timedelta(days=6)
    baseline_start = today - timedelta(days=27)
    baseline_end = today - timedelta(days=7)

    def weighted(rows_subset):
        done_w = total_w = done_n = total_n = 0
        for r in rows_subset:
            try:
                items = json.loads(r.get("priorities_json") or "[]")
            except Exception:
                continue
            for it in items:
                w = TRIAGE_WEIGHT.get(it.get("triage", "background"), 1)
                total_w += w
                total_n += 1
                if it.get("done"):
                    done_w += w
                    done_n += 1
        return done_w, total_w, done_n, total_n

    week_rows = [r for r in rows if r.get("for_date") and week_start.isoformat() <= r["for_date"] <= today.isoformat()]
    baseline_rows = [r for r in rows if r.get("for_date") and baseline_start.isoformat() <= r["for_date"] <= baseline_end.isoformat()]

    done_w, total_w, done_n, total_n = weighted(week_rows)
    this_week_pct = round(done_w / total_w * 100) if total_w else None
    b_done_w, b_total_w, _, _ = weighted(baseline_rows)
    baseline_pct = round(b_done_w / b_total_w * 100) if b_total_w >= 10 else None

    off_track = False
    if this_week_pct is not None and total_n >= 2:
        if baseline_pct is not None:
            off_track = this_week_pct <= 70 and (baseline_pct - this_week_pct) >= 30
        else:
            off_track = this_week_pct < 50

    return {"done_count": done_n, "total_count": total_n, "this_week_pct": this_week_pct if this_week_pct is not None else 0,
            "baseline_pct": baseline_pct, "off_track": off_track}


def get_or_generate_adherence_nudge(user_id, sys_prompt, adherence, force=False):
    today_str = date.today().isoformat()
    if not force:
        existing = supabase.table("adherence_nudges").select("*").eq("user_id", user_id).eq("for_date", today_str).limit(1).execute()
        if existing.data:
            return existing.data[0]["nudge_text"]
    baseline_note = f"their own recent baseline of {adherence['baseline_pct']}%" if adherence.get("baseline_pct") is not None else "a reasonable starting bar"
    prompt = f"""This person's protocol completion has dropped to {adherence['this_week_pct']}% this week ({adherence['done_count']} of {adherence['total_count']} priorities), versus {baseline_note}.
Write one short, direct, first-person note (2-3 sentences, your voice) naming the drop plainly and asking what's actually getting in the way — not guilt-tripping, not generic encouragement. This should read as genuine concern from a coach who noticed, not an automated alert."""
    nudge = ai_generate(sys_prompt, prompt, max_tokens=200)
    supabase.table("adherence_nudges").upsert({"user_id": user_id, "for_date": today_str, "nudge_text": nudge}, on_conflict="user_id,for_date").execute()
    return nudge


def compute_adherence_vs_outcome(user_id, profile, weeks=6):
    """Weekly protocol adherence against the person's own outcome metric — their most
    relevant personalized check-in metric if they have one, else energy — to show whether
    following the plan actually correlates with feeling better for them, not just with
    showing up. Returns None (card gets suppressed) until there's enough real history."""
    metric_defs = sorted(db_get("checkin_metric_defs", user_id), key=lambda m: m.get("sort_order", 0))
    outcome_key, outcome_label = "energy", "energy"
    for m in metric_defs:
        if m.get("input_type") == "slider":
            outcome_key, outcome_label = m["metric_key"], m["label"].lower()
            break

    today = user_now(profile).date()
    days_needed = weeks * 7
    priority_rows = db_get("daily_priorities", user_id, order_col="for_date", limit=days_needed)
    checkin_rows = db_get("checkins", user_id, order_col="checkin_date", limit=days_needed)

    week_data = []
    for w in range(weeks):
        week_end = today - timedelta(days=7 * w)
        week_start = week_end - timedelta(days=6)
        p_rows = [r for r in priority_rows if r.get("for_date") and week_start.isoformat() <= r["for_date"] <= week_end.isoformat()]
        c_rows = [r for r in checkin_rows if r.get("checkin_date") and week_start.isoformat() <= r["checkin_date"] <= week_end.isoformat()]

        done_w = total_w = 0
        for r in p_rows:
            try:
                items = json.loads(r.get("priorities_json") or "[]")
            except Exception:
                continue
            for it in items:
                wt = TRIAGE_WEIGHT.get(it.get("triage", "background"), 1)
                total_w += wt
                if it.get("done"):
                    done_w += wt
        adherence_pct = round(done_w / total_w * 100) if total_w else None

        outcome_vals = []
        for r in c_rows:
            v = r.get("energy") if outcome_key == "energy" else json.loads(r.get("custom_metrics") or "{}").get(outcome_key)
            if isinstance(v, (int, float)):
                outcome_vals.append(v)
        outcome_avg = round(statistics.mean(outcome_vals), 1) if outcome_vals else None

        week_data.append({"adherence_pct": adherence_pct, "outcome_avg": outcome_avg})

    week_data.reverse()
    complete_weeks = [w for w in week_data if w["adherence_pct"] is not None and w["outcome_avg"] is not None]
    if len(complete_weeks) < 3:
        return None

    high = [w["outcome_avg"] for w in complete_weeks if w["adherence_pct"] >= 70]
    low = [w["outcome_avg"] for w in complete_weeks if w["adherence_pct"] < 70]
    if high and low:
        high_avg, low_avg = round(statistics.mean(high), 1), round(statistics.mean(low), 1)
        insight = f"Weeks above 70% completion averaged {high_avg}/10 {outcome_label} — {round(abs(high_avg - low_avg), 1)} points {'higher' if high_avg > low_avg else 'lower'} than weeks below that."
    else:
        overall = round(statistics.mean([w["outcome_avg"] for w in complete_weeks]), 1)
        insight = f"Averaging {overall}/10 {outcome_label} across the weeks tracked so far — need more variation in adherence to compare high vs low weeks."

    return {"weeks": week_data, "outcome_label": outcome_label, "insight": insight}


def render_consistency(user_id, profile):
    today = user_now(profile).date()
    checkins_30 = db_get("checkins", user_id, order_col="checkin_date", limit=30)
    dates_with_checkin = {c["checkin_date"] for c in checkins_30 if c.get("checkin_date")}
    last_30_count = sum(1 for d in dates_with_checkin if (today - date.fromisoformat(d)).days < 30)

    st.markdown('<div class="sl">Your consistency</div>', unsafe_allow_html=True)
    dots = ""
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        on = " on" if d.isoformat() in dates_with_checkin else ""
        today_ring = " today" if d == today else ""
        dots += f'<div class="consist-dot{on}{today_ring}">{d.strftime("%a")[0]}</div>'
    st.markdown(f"""
<div style="display:flex;gap:8px;margin-bottom:11px">{dots}</div>
<div style="font-size:14px;color:var(--graphite);margin-bottom:3px"><span style="font-family:'JetBrains Mono',monospace;font-weight:500">{last_30_count}</span> of last 30 days checked in</div>
<div style="font-size:11.5px;color:var(--mid);margin-bottom:16px">Consistency, not perfection — a missed day doesn't reset anything.</div>
""", unsafe_allow_html=True)


def greeting(profile=None):
    h = user_now(profile).hour
    return "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"


# ── Deferred onboarding detail — dose/timing/notes skipped at Step 2, asked later ──
def get_profile_detail_gaps(user_id):
    meds = [m for m in db_get("medications", user_id) if m.get("active", True) and not (m.get("dose") or "").strip() and not (m.get("frequency") or "").strip()]
    supps = [s for s in db_get("supplements", user_id) if s.get("active", True) and not (s.get("dose") or "").strip() and not (s.get("timing") or "").strip()]
    conditions = [c for c in db_get("medical_history", user_id) if not (c.get("notes") or "").strip()]
    return meds, supps, conditions


def render_profile_detail_nudge(user_id):
    meds, supps, conditions = get_profile_detail_gaps(user_id)
    if not (meds or supps or conditions) or st.session_state.get("hide_detail_nudge"):
        return
    names = [m["name"] for m in meds] + [s["name"] for s in supps] + [c["condition"] for c in conditions]
    st.markdown(f"""
<div class="material-flag">
<div class="mf-lbl">From your coach</div>
<div class="mf-txt">You mentioned {', '.join(names)} during onboarding — I'd like the dose/timing detail on these whenever you have a moment.</div>
</div>""", unsafe_allow_html=True)
    with st.expander("Add the missing detail"):
        for m in meds:
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.markdown(f"**{m['name']}**")
            dose = c2.text_input("Dose", key=f"gap_med_dose_{m['id']}", placeholder="e.g. 500mg", label_visibility="collapsed")
            timing = c3.text_input("Timing", key=f"gap_med_time_{m['id']}", placeholder="e.g. Twice daily, with food", label_visibility="collapsed")
            if c4.button("Save", key=f"gap_med_save_{m['id']}") and (dose or timing):
                db_upsert("medications", {"id": m["id"], "dose": dose, "frequency": timing})
                st.rerun()
        for s in supps:
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.markdown(f"**{s['name']}**")
            dose = c2.text_input("Dose", key=f"gap_supp_dose_{s['id']}", placeholder="e.g. 2000 IU", label_visibility="collapsed")
            timing = c3.text_input("Timing", key=f"gap_supp_time_{s['id']}", placeholder="e.g. Morning, with breakfast", label_visibility="collapsed")
            if c4.button("Save", key=f"gap_supp_save_{s['id']}") and (dose or timing):
                db_upsert("supplements", {"id": s["id"], "dose": dose, "timing": timing})
                st.rerun()
        for c in conditions:
            cc1, cc2, cc3 = st.columns([2, 4, 1])
            cc1.markdown(f"**{c['condition']}**")
            notes = cc2.text_input("Since / notes", key=f"gap_cond_notes_{c['id']}", placeholder="e.g. Diagnosed 2021, on medication", label_visibility="collapsed")
            if cc3.button("Save", key=f"gap_cond_save_{c['id']}") and notes:
                db_upsert("medical_history", {"id": c["id"], "notes": notes})
                st.rerun()
    if st.button("Not now", key="detail_gap_dismiss"):
        st.session_state.hide_detail_nudge = True
        st.rerun()


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

    if plan and not plan["roadmap"].get("start_confirmed"):
        with st.container(border=True):
            st.markdown(f"**Ready to begin your {plan['mode']} programme?** Set the date you want Day 1 to start — until you confirm, we're using today by default for your Week/Phase calculations.")
            sc1, sc2 = st.columns([3, 1])
            try:
                default_start = date.fromisoformat(plan["roadmap"].get("phase_start_date") or "")
            except Exception:
                default_start = date.today()
            start_date_input = sc1.date_input("Start date", value=default_start, key="confirm_start_date", label_visibility="collapsed")
            if sc2.button("Confirm start date →", key="confirm_start_btn", type="primary"):
                db_upsert("roadmaps", {"user_id": user_id, "phase_start_date": start_date_input.isoformat(), "start_confirmed": True}, on_conflict="user_id")
                st.rerun()

    first_name = ((profile.get("full_name") or "") if profile else "").split(" ")[0] or "there"
    st.markdown(f'<div class="pg-title" style="margin-bottom:2px">{greeting(profile)}, {first_name}.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pg-sub">{user_now(profile).strftime("%A, %d %B %Y")} · Here\'s what matters today.</div>', unsafe_allow_html=True)

    render_profile_detail_nudge(user_id)

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

    st.markdown('<div class="sl">Lab highlights</div>', unsafe_allow_html=True)
    latest_lab_list = db_get("lab_reports", user_id, order_col="report_date", limit=1)
    if latest_lab_list:
        latest_lab = latest_lab_list[0]
        try:
            lab_days_old = (date.today() - date.fromisoformat(latest_lab["report_date"])).days
        except Exception:
            lab_days_old = None
        staleness_note = "" if (lab_days_old is not None and lab_days_old <= 90) else " · more than 90 days old, a retest would sharpen this"
        st.markdown(f"""
<div class="insight-box">
<div class="ib-lbl">✦ From your labs — {latest_lab.get('report_date','')}{staleness_note}</div>
<div class="ib-txt">{latest_lab.get('summary','') or 'No interpretation on file yet.'}</div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="border:1.5px dashed var(--stone);border-radius:10px;padding:16px;text-align:center;color:var(--mid);margin-bottom:14px">No labs on file yet — upload from Profile & Data to see flagged findings here.</div>', unsafe_allow_html=True)

    has_cycle = profile.get("has_cycle", False) if profile else False
    sys_prompt = build_system_prompt(user_id, profile, has_cycle=has_cycle)

    render_consistency(user_id, profile)

    st.markdown('<div class="sl">Today\'s priorities</div>', unsafe_allow_html=True)
    today_str = user_now(profile).date().isoformat()
    priorities = get_or_generate_daily_priorities(user_id, sys_prompt)
    triage_class = {"now": "t-now", "watch": "t-watch", "background": "t-bg"}
    triage_label = {"now": "Act today", "watch": "Watch", "background": "Background"}
    cols = st.columns(3)
    for i, p in enumerate(priorities[:3]):
        with cols[i]:
            t = p.get("triage", "background")
            done = p.get("done", False)
            st.markdown(f"""
<div class="prio-card" style="{'opacity:0.55' if done else ''}">
<span class="triage {triage_class.get(t,'t-bg')}">{triage_label.get(t,'Background')}</span>
<div class="pc-title{' done' if done else ''}">{p.get('title','')}</div>
<div class="pc-body">{p.get('body','')}</div>
</div>""", unsafe_allow_html=True)
            if st.button("↺ Undo" if done else "✓ Mark done", key=f"prio_toggle_{today_str}_{i}", use_container_width=True):
                toggle_priority_done(user_id, today_str, priorities, i)
                st.rerun()

    adherence = compute_priority_adherence(user_id, user_now(profile).date())
    st.markdown(f"""
<div style="margin-top:2px">
<div style="display:flex;justify-content:space-between;font-size:11.5px;color:var(--mid);margin-bottom:6px">
<span>This week</span><span style="font-family:'JetBrains Mono',monospace;color:var(--graphite)">{adherence['done_count']} / {adherence['total_count']}</span>
</div>
<div class="adh-bar-track"><div class="adh-bar-fill" style="width:{adherence['this_week_pct']}%"></div></div>
</div>""", unsafe_allow_html=True)
    if adherence["off_track"]:
        nudge = get_or_generate_adherence_nudge(user_id, sys_prompt, adherence)
        st.markdown(f"""
<div class="material-flag" style="margin-top:14px">
<div class="mf-lbl">From your coach</div>
<div class="mf-txt" style="font-family:'Newsreader',serif;font-style:italic">{nudge}</div>
</div>""", unsafe_allow_html=True)
        adherence_reply = st.text_area("Tell your coach what's going on", key="adherence_reply", placeholder="e.g. The plan feels like too much right now, or life just got in the way this week...")
        if st.button("Send to your coach", key="adherence_reply_btn") and adherence_reply:
            st.session_state.page = "coach"
            st.session_state.coach_seed = f"About my protocol completion dropping to {adherence['this_week_pct']}% this week: {adherence_reply}"
            st.rerun()

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
<div class="tc-insight">{f"{len(wearable_30)} days of wearable data in the last 30 days." if wearable_30 else "Upload wearable data from Profile & Data to see this trend."}</div>
<div class="tc-bars">{make_bars(hrv_vals, max_hrv)}</div>
</div>""", unsafe_allow_html=True)

    metric_defs = sorted(db_get("checkin_metric_defs", user_id), key=lambda m: m.get("sort_order", 0))
    custom_series = [json.loads(c.get("custom_metrics") or "{}") for c in checkins_30]

    def week_avg(vals):
        nums = [v for v in vals if isinstance(v, (int, float))]
        return round(statistics.mean(nums), 1) if nums else None

    pc1, pc2 = st.columns(2)
    for i, m in enumerate(metric_defs[:2]):
        key, label = m["metric_key"], m["label"]
        with (pc1 if i == 0 else pc2):
            vals = [s.get(key) for s in custom_series]
            if m["input_type"] == "slider":
                this_wk, prev_wk = week_avg(vals[-7:]), week_avg(vals[-14:-7])
                if this_wk is not None and prev_wk is not None:
                    insight = f"Averaging {this_wk}/10 this week, {'down' if this_wk < prev_wk else 'up' if this_wk > prev_wk else 'steady'} from {prev_wk}/10 last week."
                elif this_wk is not None:
                    insight = f"Averaging {this_wk}/10 this week."
                else:
                    insight = "Log a check-in to start building this trend."
                st.markdown(f"""
<div class="trend-card">
<div class="tc-title">{label} · 30 days</div>
<div class="tc-insight">{insight}</div>
<div class="tc-bars">{make_bars(vals)}</div>
</div>""", unsafe_allow_html=True)
            else:
                options = json.loads(m.get("options_json") or "[]")
                logged = [v for v in vals[-14:] if v in options]
                dots = "".join(f'<div class="tc-dot" style="opacity:{round((options.index(v)+1)/len(options), 2) if options else 1}"></div>' for v in vals[-14:] if v in options) or '<div style="color:var(--mid);font-size:11px;padding:10px">Not enough data yet.</div>'
                mildest_count = sum(1 for v in logged if options and v == options[0])
                insight = f"{mildest_count} of last {len(logged)} logged as \"{options[0]}\"." if logged and options else "Log a check-in to start building this trend."
                st.markdown(f"""
<div class="trend-card">
<div class="tc-title">{label} · last 14 days</div>
<div class="tc-insight">{insight}</div>
<div class="tc-dots">{dots}</div>
<div class="tc-dot-legend"><span>{options[0] if options else ''}</span><span>{options[-1] if options else ''}</span></div>
</div>""", unsafe_allow_html=True)

    outcome = compute_adherence_vs_outcome(user_id, profile)
    if outcome:
        bars_html = ""
        for i, w in enumerate(outcome["weeks"]):
            a_h = max(8, min(100, w["adherence_pct"] or 0))
            b_h = max(8, min(100, round((w["outcome_avg"] or 0) / 10 * 100)))
            bars_html += f'<div class="wk-col"><div class="wk-bars"><div class="bar-a" style="height:{a_h}%"></div><div class="bar-b" style="height:{b_h}%"></div></div><div class="wk-lbl">Wk {i+1}</div></div>'
        st.markdown(f"""
<div class="trend-card" style="margin-top:10px">
<div class="tc-title">Protocol adherence vs. {outcome['outcome_label']} · last {len(outcome['weeks'])} weeks</div>
<div class="tc-insight">{outcome['insight']}</div>
<div class="wk-row">{bars_html}</div>
<div class="wk-legend"><span><span class="leg-dot" style="background:var(--copper)"></span>Adherence %</span><span><span class="leg-dot" style="background:var(--stone)"></span>Avg {outcome['outcome_label']}</span></div>
</div>""", unsafe_allow_html=True)
# ── Materiality flags — the single gate for any plan change (Brief §6) ───────
def get_open_materiality_flag(user_id, level):
    try:
        res = supabase.table("materiality_flags").select("*").eq("user_id", user_id).eq("level", level).eq("resolved", False).order("created_at", desc=True).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def resolve_materiality_flag(flag_id):
    try:
        supabase.table("materiality_flags").update({"resolved": True}).eq("id", flag_id).execute()
    except Exception:
        pass


def render_materiality_flag(flag, on_regenerate=None):
    if not flag:
        return
    st.markdown(f"""
<div class="material-flag">
<div class="mf-lbl">✦ Coach flag — needs updating</div>
<div class="mf-txt">{flag.get('flag_text','')}</div>
</div>""", unsafe_allow_html=True)
    fc1, fc2 = st.columns(2)
    if fc1.button("Discuss with coach →", key=f"flag_discuss_{flag.get('id')}"):
        st.session_state.page = "coach"
        st.session_state.coach_seed = f"You flagged something about my {flag.get('level')} — let's talk about it."
        st.rerun()
    if on_regenerate and fc2.button("↻ Regenerate now", key=f"flag_regen_{flag.get('id')}", type="primary"):
        on_regenerate()
        resolve_materiality_flag(flag["id"])
        st.rerun()


def get_or_generate(table, user_id, build_fn, force=False, reason=None):
    """build_fn(existing_content, reason) — on a forced regeneration, the
    prior content and the specific reason are passed in so the rebuild can
    make a targeted change instead of a fresh, unconstrained re-roll. A
    from-scratch regeneration has no memory of the previous version, so
    unrelated details (like row ordering) can drift for no real reason —
    which reads as the coach being inconsistent."""
    existing = db_get_single(table, user_id)
    if not force and existing and existing.get("content"):
        return existing["content"]
    content = build_fn(existing.get("content") if existing else None, reason)
    db_upsert(table, {"user_id": user_id, "content": content, "generated_at": date.today().isoformat()}, on_conflict="user_id")
    return content


def regenerate_roadmap(user_id, sys_prompt, roadmap, reason=None):
    phase_count = {"Reset": 2, "Restore": 3, "Transform": 4, "Sustain": 3}.get(roadmap.get("plan_mode", "Restore"), 3)
    labs_present = bool(db_get("lab_reports", user_id))
    existing_text = roadmap.get("roadmap_text", "")
    prompt = f"""Generate a {roadmap.get('plan_mode','Restore')} programme roadmap, duration {PLAN_MODES.get(roadmap.get('plan_mode','Restore'), PLAN_MODES['Restore'])['duration_days'] or 'ongoing'} days, in exactly {phase_count} phases.
{'Labs are not yet available — generate this roadmap clearly marked PROVISIONAL, with a note it becomes definitive once labs are analysed.' if not labs_present else ''}

Be concise and systematic — this must cover all {phase_count} phases completely within the length budget. Favour short paragraphs and tight bullet points over prose.

FORMAT (keep to this structure exactly, {phase_count} phases total):
## Your {roadmap.get('plan_mode','Restore')} Programme — Generated {date.today().strftime('%-d %B %Y')}
One sentence on what this programme addresses, grounded in this specific person's data — not generic.

## Phase Timeline
Table: Phase | Focus | Key milestones | Checkpoint — one row per phase, all {phase_count} phases, terse.

## Phase 1 — [Title]: [duration]
3-5 bullet points max: what changes, why (root mechanism in one clause), specific supplement/nutrition/training changes with exact doses where the data supports it.
**Retest at checkpoint:** [markers chosen for this person, comma-separated]
**What success looks like:** [one line, specific to their stated goals]

[Repeat this exact structure for every phase up to Phase {phase_count} — do not skip or truncate any phase]

## If Progress Stalls
[Escalation path, 2-3 sentences]

**Start today:** [one specific immediate action]
"""
    if existing_text:
        prompt += (f"\n\nThis is a REVISION of the current committed roadmap below, not a fresh document. "
                   f"Reason for this update: {reason or 'general refresh requested'}. "
                   f"Make ONLY the changes required by this reason — preserve the existing phase structure, wording, doses, and order for everything else exactly as they were. "
                   f"Do not reorder, rephrase, or restate content that this reason doesn't touch.\n\nCURRENT COMMITTED ROADMAP:\n{existing_text}")
    with st.spinner("Updating your roadmap..."):
        new_text = ai_generate(sys_prompt, prompt, max_tokens=8000)
        db_upsert("roadmaps", {"user_id": user_id, "roadmap_text": new_text, "provisional": not labs_present}, on_conflict="user_id")


# ── Phase Timeline visual — parsed from the "## Phase Timeline" table the ────
# roadmap prompt already reliably produces (see FORMAT section above). Purely
# a display-layer enhancement, no change to generation needed.
def parse_phase_timeline(roadmap_text):
    m = re.search(r"##\s*Phase Timeline\s*\n(.*?)(?=\n##\s|\Z)", roadmap_text, re.DOTALL)
    if not m:
        return []
    rows = []
    for line in m.group(1).strip().split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue  # the |---|---|---|---| header-separator row
        if len(cells) >= 4:
            rows.append({"phase": cells[0], "focus": cells[1], "milestones": cells[2], "checkpoint": cells[3]})
    if rows and rows[0]["phase"].lower() == "phase":
        rows = rows[1:]  # the literal header row (Phase | Focus | ...)
    return rows


def strip_phase_timeline_section(roadmap_text):
    """Removes the raw markdown table once it's shown as the visual timeline
    instead, so the same data isn't displayed twice."""
    return re.sub(r"##\s*Phase Timeline\s*\n.*?(?=\n##\s|\Z)", "", roadmap_text, count=1, flags=re.DOTALL)


def render_phase_timeline(phases, current_index):
    if not phases:
        return
    cards = []
    for i, p in enumerate(phases):
        phase_label = p["phase"] if re.match(r"(?i)phase\b", p["phase"]) else f"Phase {p['phase']}"
        cards.append(f"""
<div class="phase-card{' current' if i == current_index else ''}">
<div class="phase-num">{phase_label}{' · Now' if i == current_index else ''}</div>
<div class="phase-focus">{p['focus']}</div>
<div class="phase-meta"><strong>Milestone:</strong> {p['milestones']}</div>
<div class="phase-meta"><strong>Checkpoint:</strong> {p['checkpoint']}</div>
</div>""")
    st.markdown(f'<div class="phase-timeline">{"".join(cards)}</div>', unsafe_allow_html=True)


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

    # Compute the canonical current week once and inject it into every tab's
    # generation prompt below, so Supplements/Nutrition/Workouts/Monthly Goal
    # all reference the same week instead of each independently inventing its
    # own week number or calendar-date framing (which is how one tab ended up
    # saying "Week of 2 July 2026" while another said "Week 1").
    plan = get_plan_info(user_id, profile)
    week_context = ""
    if plan:
        week_label = f"Week {plan['week_num']}" + (f" of {plan['total_weeks']}" if plan["total_weeks"] else "")
        week_context = (f"\n\nCanonical current week: this is {week_label} of the {plan['mode']} programme. "
                         f'Always label this as "{week_label}" if you reference the week at all — do not invent a '
                         f'different week number or a calendar-date framing (e.g. do not say "Week of [date]").')

    # The Roadmap tab's phase text often already commits to specific sequencing/
    # timing (e.g. "L-glutamine at wake, Thyronorm 30 min later") when it names
    # exact doses. Supplements/Nutrition/Workouts are separate AI calls that
    # otherwise re-derive timing from scratch with no visibility into that —
    # which is how one tab can contradict what the Roadmap already committed
    # to. Same fix pattern as week_context above, generalized to any detail.
    roadmap_text_for_context = roadmap.get("roadmap_text", "")
    consistency_context = ""
    if roadmap_text_for_context:
        consistency_context = (f"\n\nCANONICAL COMMITTED ROADMAP (already locked in — do not contradict):\n{roadmap_text_for_context}\n"
                                f"If the roadmap above already specifies exact timing, sequencing, or dosing for any "
                                f"supplement, medication, or meal, you MUST use that exact same detail here — never "
                                f"independently re-derive a different order or dose for something it already settled.")

    def week_num_as_of(iso_date, phase_start_iso, duration_days):
        """Same week-number math as get_plan_info, but for an arbitrary
        reference date — lets us tell whether a cached weekly tab was
        generated in an earlier week than the one showing everywhere else."""
        try:
            days_in = (date.fromisoformat(iso_date) - date.fromisoformat(phase_start_iso)).days
        except Exception:
            return None
        if duration_days:
            return min(max(days_in // 7 + 1, 1), (duration_days // 7) or 1)
        return max(days_in // 7 + 1, 1)

    def is_week_stale(table):
        """True if this tab's cached content was generated in a week that no
        longer matches the current week. get_or_generate() otherwise only
        refreshes on a materiality flag, so a "this week's schedule" tab can
        silently sit frozen on whatever week it happened to first be opened
        in — which is exactly how Supplements/Nutrition/Workouts each ended
        up displaying a different week, since each was first generated on a
        different day and nothing ever told them the week had moved on."""
        if not plan:
            return False
        existing = db_get_single(table, user_id)
        if not existing or not existing.get("generated_at"):
            return False
        phase_start_iso = roadmap.get("phase_start_date") or roadmap.get("generated_at")
        duration_days = PLAN_MODES.get(plan["mode"], PLAN_MODES["Restore"])["duration_days"]
        existing_week = week_num_as_of(existing["generated_at"], phase_start_iso, duration_days)
        return existing_week is not None and existing_week != plan["week_num"]

    # Two different reasons for the same "week has moved on" trigger, because
    # Supplements and Nutrition/Workouts have opposite correct behaviors on a
    # week rollover. Dosing shouldn't drift without a real reason, so
    # Supplements gets a label-only patch. Food and training are meant to
    # progress week to week against actual check-in/wearable/cycle trends —
    # patching just the label there would freeze content that's supposed to
    # evolve, which is its own kind of staleness bug.
    week_sync_reason_light = "The current week has advanced since this was last generated — update only the week/phase references to stay accurate, preserve all other content exactly."
    week_sync_reason_evolve = ("A new week has begun in this committed programme. Do not just patch the week label — "
                                "genuinely re-derive this week's plan by reasoning fresh from the person's most current "
                                "check-in trends, wearable recovery data, stated preferences, and cycle phase (if "
                                "applicable) — all in your system context. Week-to-week evolution is expected here: this "
                                "includes real adjustments driven by feedback, injury, or cycle syncing, but also simple "
                                "variety — do not repeat the same meals or exercises verbatim week after week even when "
                                "nothing material changed, the same way a human coach naturally varies choices for "
                                "someone. Stay consistent with the roadmap's current phase and any sequencing it already "
                                "committed to, and treat the previous week's plan below as the starting point to "
                                "progress from, not content to preserve unchanged.")

    tabs = st.tabs(["Treatment Roadmap", "Monthly Goal", "Supplements", "Nutrition", "Workouts"])

    def adjust_flow(label, key_prefix):
        """Shared by every tab's 'Want to adjust something?' expander. Runs the
        change through the coach's own materiality judgment instead of either
        silently regenerating or silently doing nothing — if it's genuinely
        material, a flag appears (with a Regenerate option) next visit; if
        not, the user gets a direct "no change needed" answer instead of
        wondering what happened."""
        with st.expander("Want to adjust something?"):
            adj = st.text_area("Describe what you'd like to change", key=f"adj_{key_prefix}")
            if st.button("Tell your coach", key=f"adj_{key_prefix}_btn") and adj:
                result = check_materiality(user_id, sys_prompt, f"User says about their {label}: {adj}")
                if result is None:
                    st.warning("Couldn't evaluate that just now — try again in a moment.")
                elif result.get("material"):
                    st.success(f"Flagged for update — reopen this tab to see the Regenerate option. {result.get('flag_text','')}")
                else:
                    st.info(f"No change needed: {result.get('flag_text') or 'this does not change your current protocol.'}")

    with tabs[0]:
        roadmap_flag = get_open_materiality_flag(user_id, "roadmap")
        render_materiality_flag(roadmap_flag, on_regenerate=lambda: regenerate_roadmap(user_id, sys_prompt, roadmap, reason=roadmap_flag.get("flag_text") if roadmap_flag else None))
        st.markdown(f'<div class="sl first">{roadmap.get("plan_mode","")} · roadmap · Committed {roadmap.get("generated_at","")}</div>', unsafe_allow_html=True)
        if roadmap.get("provisional"):
            st.warning("This roadmap is provisional — labs were not yet available when it was generated.")
        full_roadmap_text = roadmap.get("roadmap_text", "_No roadmap text._")
        phases = parse_phase_timeline(full_roadmap_text)
        if phases:
            current_phase_index = 0
            if plan and plan.get("total_weeks"):
                current_phase_index = min(int(plan["week_num"] / plan["total_weeks"] * len(phases)), len(phases) - 1)
            render_phase_timeline(phases, current_phase_index)
            st.markdown(strip_phase_timeline_section(full_roadmap_text))
        else:
            st.markdown(full_roadmap_text)
        st.download_button("Download roadmap", full_roadmap_text, file_name="onesattva_roadmap.md")
        adjust_flow("overall roadmap", "roadmap")

    with tabs[1]:
        def build_monthly(existing=None, reason=None):
            prompt = "Generate this phase's Monthly Goal focus: one italic-style focus statement (1-2 sentences) plus a 4-week breakdown table (Week | Focus), covering all 4 weeks. Base this on the committed roadmap's current phase. Be concise but always complete all 4 rows — never truncate the table."
            if existing:
                prompt += f"\n\nThis is a revision of the current version, not a fresh document. Reason for this update: {reason or 'general refresh requested'}. Make ONLY the changes required by this reason — preserve everything else exactly as it was.\n\nCURRENT VERSION:\n{existing}"
            return ai_generate(sys_prompt, prompt, max_tokens=1200)
        monthly_flag = get_open_materiality_flag(user_id, "monthly_focus")
        render_materiality_flag(monthly_flag, on_regenerate=lambda: get_or_generate("monthly_focus", user_id, build_monthly, force=True, reason=monthly_flag.get("flag_text") if monthly_flag else None))
        monthly = get_or_generate("monthly_focus", user_id, build_monthly)
        st.markdown(f'<div class="goal-card"><div class="gc-lbl">Current phase focus</div><div class="gc-goal" style="font-style:normal;font-size:13.5px">{monthly}</div></div>', unsafe_allow_html=True)
        adjust_flow("monthly goal focus", "monthly")

    with tabs[2]:
        def build_supps(existing=None, reason=None):
            prompt = "Generate this week's committed supplement schedule as a markdown table: Time | Supplement | Dose | Clinical notes. Derive dose, brand suitability, and timing from this person's actual labs, medications, and absorption considerations — explain timing rationale concisely in the notes column. If a thyroid medication is present, reason explicitly about its absorption timing relative to other supplements. Cover every supplement/timing slot that applies — never cut the table short; keep each note to one tight sentence rather than dropping rows." + week_context + consistency_context
            if existing:
                prompt += f"\n\nThis is a revision of the current committed schedule, not a fresh document. Reason for this update: {reason or 'general refresh requested'}. Make ONLY the changes required by this reason — preserve the existing row order, wording, and doses for everything else exactly as they were. Do not reorder or rephrase rows this reason doesn't touch.\n\nCURRENT COMMITTED SCHEDULE:\n{existing}"
            return ai_generate(sys_prompt, prompt, max_tokens=2000)
        supps_flag = get_open_materiality_flag(user_id, "supplements")
        render_materiality_flag(supps_flag, on_regenerate=lambda: get_or_generate("supplement_plan", user_id, build_supps, force=True, reason=supps_flag.get("flag_text") if supps_flag else None))
        supps_week_stale = is_week_stale("supplement_plan")
        supps = get_or_generate("supplement_plan", user_id, build_supps, force=supps_week_stale, reason=week_sync_reason_light if supps_week_stale else None)
        st.markdown(supps)
        adjust_flow("supplement schedule", "supp")

    with tabs[3]:
        def build_nutrition(existing=None, reason=None):
            prompt = "Generate this week's committed 7-day nutrition plan. Start with a short info box (2-3 sentences) on this phase's nutrition focus, reasoned from this person's actual gut/digestion check-in data, goals, and dietary preferences — not a generic rule. Then a markdown table: Meal | Focus | Examples, covering all 7 days. Respect their stated dietary pattern and restrictions exactly. Keep each row tight (a few words per cell) so all 7 days fit — completeness across all 7 days matters more than detail in any one day." + week_context + consistency_context
            if existing:
                prompt += f"\n\nThis is a revision of the current committed plan, not a fresh document. Reason for this update: {reason or 'general refresh requested'}. Make ONLY the changes required by this reason — preserve everything else exactly as it was.\n\nCURRENT COMMITTED PLAN:\n{existing}"
            return ai_generate(sys_prompt, prompt, max_tokens=2200)
        nutrition_flag = get_open_materiality_flag(user_id, "nutrition")
        render_materiality_flag(nutrition_flag, on_regenerate=lambda: get_or_generate("nutrition_plan", user_id, build_nutrition, force=True, reason=nutrition_flag.get("flag_text") if nutrition_flag else None))
        nutrition_week_stale = is_week_stale("nutrition_plan")
        nutrition = get_or_generate("nutrition_plan", user_id, build_nutrition, force=nutrition_week_stale, reason=week_sync_reason_evolve if nutrition_week_stale else None)
        st.markdown(nutrition)
        adjust_flow("nutrition plan", "nutr")

    with tabs[4]:
        def build_workouts(existing=None, reason=None):
            prompt = "Generate this week's committed 7-day training plan. Start with a short info box (2-3 sentences) on this phase's training principle, reasoned from this person's recovery/wearable data and goals. Then a markdown table: Day | Session type | Focus & exercises | Target duration, covering all 7 days. Calibrate intensity to recovery data if available. Keep each row tight so all 7 days fit — completeness across the full week matters more than depth on any single day." + week_context + consistency_context
            if existing:
                prompt += f"\n\nThis is a revision of the current committed plan, not a fresh document. Reason for this update: {reason or 'general refresh requested'}. Make ONLY the changes required by this reason — preserve everything else exactly as it was.\n\nCURRENT COMMITTED PLAN:\n{existing}"
            return ai_generate(sys_prompt, prompt, max_tokens=2000)
        workouts_flag = get_open_materiality_flag(user_id, "workouts")
        render_materiality_flag(workouts_flag, on_regenerate=lambda: get_or_generate("workout_plan", user_id, build_workouts, force=True, reason=workouts_flag.get("flag_text") if workouts_flag else None))
        workouts_week_stale = is_week_stale("workout_plan")
        workouts = get_or_generate("workout_plan", user_id, build_workouts, force=workouts_week_stale, reason=week_sync_reason_evolve if workouts_week_stale else None)
        st.markdown(workouts)
        adjust_flow("training plan", "workout")
# ── Materiality check — runs after new data is submitted, not on a timer ─────
def check_materiality(user_id, sys_prompt, trigger_desc):
    """Returns the parsed {"material": bool, "level": str|None, "flag_text": str|None}
    verdict (or None if the judgment call itself failed to parse), so a caller that
    needs to react immediately — e.g. a user directly telling the coach something
    changed — can show the verdict right there instead of only silently inserting
    a flag that's easy to miss."""
    prompt = f"""A new data point just came in: {trigger_desc}.
Given everything you know about this patient, is there anything here material enough that the committed roadmap, this phase's monthly focus, or a weekly protocol (supplements/nutrition/workouts) should be revisited? Use your own clinical judgment — there is no fixed checklist. A change that's material for one patient may be irrelevant for another. Most single data points are NOT material — only flag genuine, protocol-relevant changes.
Respond with ONLY valid JSON: {{"material": true/false, "level": "roadmap"|"monthly_focus"|"supplements"|"nutrition"|"workouts"|null, "flag_text": "what changed, why it's material for this person specifically, what level should change, what you're proposing" or "why this doesn't require a change" if not material}}"""
    raw = ai_generate(sys_prompt, prompt, max_tokens=500)
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(match.group(0) if match else raw)
    except Exception:
        return None
    if result.get("material"):
        # Today's Home page priorities are cached once per calendar day, so a
        # material event (new labs, a materially different check-in) would
        # otherwise keep showing stale "no labs on file"-style content until
        # the cache naturally expires tomorrow. Clear it so Home regenerates
        # with the full picture on the next visit.
        today_str = date.today().isoformat()
        supabase.table("daily_priorities").delete().eq("user_id", user_id).eq("for_date", today_str).execute()
        if result.get("level"):
            db_insert("materiality_flags", {"user_id": user_id, "level": result["level"], "flag_text": result.get("flag_text", ""), "resolved": False, "created_at": datetime.now().isoformat()})
    return result


# ── Check-In Page ─────────────────────────────────────────────────────────────
# Universal metrics — tracked for everyone. Anything beyond these is personalized
# per-user (see get_or_generate_checkin_metrics) instead of forced on everyone.
CHECKIN_METRICS = ["energy", "mental_clarity", "sleep_quality", "mood"]
CHECKIN_LABELS = {"energy": "Energy", "mental_clarity": "Mental clarity", "sleep_quality": "Sleep quality", "mood": "Mood"}


def get_or_generate_checkin_metrics(user_id, profile):
    """Each person's bio-individual check-in fields, beyond the 4 universal metrics —
    generated once from their stated symptoms/conditions/goals, cached in checkin_metric_defs."""
    existing = db_get("checkin_metric_defs", user_id, order_col=None)
    if existing:
        return sorted(existing, key=lambda m: m.get("sort_order", 0))
    conditions = ", ".join(g.get("goal", "") for g in db_get("goals", user_id))
    prompt = f"""Patient's stated symptoms: {profile.get('symptoms') or 'none stated'}. Stressors: {profile.get('stressors') or 'none stated'}. Goals: {conditions or 'none stated'}.
Suggest 2-4 check-in metrics specific to THIS person's actual picture, beyond generic energy/sleep/mood/mental-clarity (which are already tracked for everyone). E.g. someone with joint pain gets a joint-stiffness metric; someone with no gut complaints gets no gut metric at all.
Return ONLY a JSON array, each item: {{"key": "snake_case_key", "label": "Short label", "type": "slider"}} for a 1-10 scale, or {{"key": "...", "label": "...", "type": "select", "options": ["...", "..."]}} for a short qualitative list (3-5 options)."""
    raw = ai_generate("You are OneSattva, a functional medicine practitioner choosing what to track daily for a specific patient.", prompt, max_tokens=500)
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        metrics = json.loads(match.group(0) if match else raw)
    except Exception:
        metrics = []
    for i, m in enumerate(metrics):
        db_insert("checkin_metric_defs", {
            "user_id": user_id, "metric_key": m["key"], "label": m["label"], "input_type": m["type"],
            "options_json": json.dumps(m.get("options", [])) if m["type"] == "select" else None, "sort_order": i,
        })
    return [{"metric_key": m["key"], "label": m["label"], "input_type": m["type"], "options_json": json.dumps(m.get("options", []))} for m in metrics]


def get_or_generate_checkin_insight(user_id, sys_prompt, force=False):
    today_str = date.today().isoformat()
    if not force:
        existing = supabase.table("checkin_insights").select("*").eq("user_id", user_id).eq("for_date", today_str).limit(1).execute()
        if existing.data:
            return existing.data[0]["insight_text"]
    insight = ai_generate(sys_prompt, "Generate one short clinical observation (2-4 sentences, your voice) from today's check-in data in the context of recent patterns. Be specific and reference actual numbers.", max_tokens=300)
    supabase.table("checkin_insights").upsert({"user_id": user_id, "for_date": today_str, "insight_text": insight}, on_conflict="user_id,for_date").execute()
    return insight


def show_checkin(user_id, profile):
    has_cycle = profile.get("has_cycle", False) if profile else False
    cycle_str = ""
    if has_cycle:
        cycle_day, phase, _ = calculate_cycle_status(user_id)
        if cycle_day:
            cycle_str = f" · Cycle Day {cycle_day}"

    local_now = user_now(profile)
    today_str = local_now.date().isoformat()
    checkins = db_get("checkins", user_id, order_col="checkin_date", limit=1)
    today_checkin = checkins[0] if checkins and checkins[0].get("checkin_date") == today_str else None

    st.markdown('<div class="pg-title">Daily Check-In</div>', unsafe_allow_html=True)
    tod = "Morning" if local_now.hour < 12 else "Afternoon" if local_now.hour < 18 else "Evening"
    st.markdown(f'<div class="pg-sub">{tod} check-in · {local_now.strftime("%A, %d %B")}{cycle_str} · Pre-filled from yesterday. Edit anything that has changed today. Takes less than 2 minutes.</div>', unsafe_allow_html=True)

    editing = st.session_state.get("checkin_editing", False)

    metric_defs = get_or_generate_checkin_metrics(user_id, profile or {})

    if today_checkin and not editing:
        sys_prompt = build_system_prompt(user_id, profile, has_cycle=has_cycle)
        insight = get_or_generate_checkin_insight(user_id, sys_prompt)
        st.markdown(f"""
<div class="insight-box">
<div class="ib-lbl">✦ Coach · Today's insight</div>
<div class="ib-txt">{insight}</div>
</div>""", unsafe_allow_html=True)
        cols = st.columns(4)
        for i, m in enumerate(CHECKIN_METRICS):
            with cols[i]:
                st.markdown(f'<div class="snap-box"><div class="snap-lbl">{CHECKIN_LABELS[m]}</div><div class="snap-val">{today_checkin.get(m,"—")}<span style="font-size:13px;color:var(--mid)">/10</span></div></div>', unsafe_allow_html=True)
        if metric_defs:
            today_custom = json.loads(today_checkin.get("custom_metrics") or "{}")
            custom_str = " · ".join(f"{m['label']}: {today_custom.get(m['metric_key'], '—')}" for m in metric_defs)
            st.caption(custom_str)
        if today_checkin.get("notes"):
            st.caption(today_checkin["notes"])
        if st.button("✏️ Edit today's check-in"):
            st.session_state.checkin_editing = True
            st.rerun()
        return

    yesterday = db_get("checkins", user_id, order_col="checkin_date", limit=2)
    prefill = today_checkin or (yesterday[1] if len(yesterday) > 1 else (yesterday[0] if yesterday else {}))
    prefill_custom = json.loads(prefill.get("custom_metrics") or "{}")

    c1, c2 = st.columns(2)
    vals = {}
    with c1:
        st.markdown(f'<p class="ci-lbl">{CHECKIN_LABELS["energy"]}</p>', unsafe_allow_html=True)
        vals["energy"] = st.slider("energy", 1, 10, int(prefill.get("energy", 5) or 5), label_visibility="collapsed")
        st.markdown(f'<p class="ci-lbl">{CHECKIN_LABELS["sleep_quality"]}</p>', unsafe_allow_html=True)
        vals["sleep_quality"] = st.slider("sleep_quality", 1, 10, int(prefill.get("sleep_quality", 5) or 5), label_visibility="collapsed")
    with c2:
        st.markdown(f'<p class="ci-lbl">{CHECKIN_LABELS["mental_clarity"]}</p>', unsafe_allow_html=True)
        vals["mental_clarity"] = st.slider("mental_clarity", 1, 10, int(prefill.get("mental_clarity", 5) or 5), label_visibility="collapsed")
        st.markdown(f'<p class="ci-lbl">{CHECKIN_LABELS["mood"]}</p>', unsafe_allow_html=True)
        vals["mood"] = st.slider("mood", 1, 10, int(prefill.get("mood", 5) or 5), label_visibility="collapsed")

    custom_vals = {}
    if metric_defs:
        st.markdown('<div class="sl">Your focus areas</div>', unsafe_allow_html=True)
        mcols = st.columns(2)
        for i, m in enumerate(metric_defs):
            key, label, itype = m["metric_key"], m["label"], m["input_type"]
            with mcols[i % 2]:
                st.markdown(f'<p class="ci-lbl">{label}</p>', unsafe_allow_html=True)
                if itype == "slider":
                    custom_vals[key] = st.slider(key, 1, 10, int(prefill_custom.get(key, 5) or 5), label_visibility="collapsed", key=f"cm_{key}")
                else:
                    options = json.loads(m.get("options_json") or "[]")
                    idx = options.index(prefill_custom[key]) if prefill_custom.get(key) in options else 0
                    custom_vals[key] = st.selectbox(key, options, index=idx, label_visibility="collapsed", key=f"cm_{key}")

    c3, c4 = st.columns(2)
    sleep_hours = c3.number_input("Sleep hours", min_value=0.0, max_value=14.0, step=0.5, value=float(prefill.get("sleep_hours", 7) or 7))
    workout = c4.selectbox("Today's workout", ["None", "Strength", "Cardio", "Mobility / Yoga", "Walk", "Rest day"],
                            index=["None", "Strength", "Cardio", "Mobility / Yoga", "Walk", "Rest day"].index(prefill.get("workout")) if prefill.get("workout") in ["None", "Strength", "Cardio", "Mobility / Yoga", "Walk", "Rest day"] else 0)
    notes = st.text_area("Notes (optional)", value=(prefill.get("notes") or "") if today_checkin else "", placeholder="Anything notable today — symptoms, observations, questions for your coach...")

    if st.button("Save today's check-in →", type="primary"):
        row = {"user_id": user_id, "checkin_date": today_str, "sleep_hours": sleep_hours, "workout": workout, "notes": notes,
               "custom_metrics": json.dumps(custom_vals), **vals}
        db_upsert("checkins", row, on_conflict="user_id,checkin_date")
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
        first_name = ((profile.get("full_name") or "") if profile else "").split(" ")[0] or "there"
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
    health_bg_row = db_get_single("profile_notes", user_id)
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown('#### Demographics')
            dob_str = (p.get("dob") or "")
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
<div class="pr"><span class="pr-k">Blood group</span><span class="pr-v">{p.get('blood_group') or '—'}</span></div>
<div class="pr"><span class="pr-k">Occupation</span><span class="pr-v">{p.get('occupation') or '—'}</span></div>
""", unsafe_allow_html=True)
            with st.expander("Edit demographics"):
                height = st.number_input("Height (cm)", 100, 230, int(p.get("height_cm") or 170), key="ed_h")
                weight = st.number_input("Weight (kg)", 30, 250, int(p.get("weight_kg") or 70), key="ed_w")
                ed_existing_city, ed_existing_country = split_location((p.get("location") or ""))
                edc1, edc2 = st.columns(2)
                ed_country = edc1.selectbox("Country", COUNTRIES, index=COUNTRIES.index(ed_existing_country) if ed_existing_country in COUNTRIES else len(COUNTRIES) - 1, key="ed_country")
                ed_city = edc2.text_input("City", value=ed_existing_city, key="ed_city")
                ed_blood_group = st.selectbox("Blood group", BLOOD_GROUPS, index=selectbox_index(BLOOD_GROUPS, p.get("blood_group"), default=len(BLOOD_GROUPS) - 1), key="ed_bg")
                occupation = st.text_input("Occupation", value=(p.get("occupation") or ""), key="ed_occ")
                has_cycle_now = p.get("has_cycle", False)
                new_has_cycle = has_cycle_now
                if p.get("sex") in ("Female", "Intersex"):
                    new_has_cycle = st.checkbox("I currently have a menstrual cycle to track", value=bool(has_cycle_now), key="ed_hc")
                if st.button("Save changes", key="save_demo"):
                    ed_location = ", ".join(x for x in [ed_city.strip(), ed_country] if x)
                    db_upsert("profiles", {"id": user_id, "height_cm": height, "weight_kg": weight, "location": ed_location,
                                            "blood_group": ed_blood_group, "occupation": occupation, "has_cycle": bool(new_has_cycle)})
                    st.success("Saved.")
                    st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown('#### Medical History')
            conditions = db_get("medical_history", user_id)
            meds = db_get("medications", user_id)
            if conditions:
                for c in conditions:
                    cc1, cc2 = st.columns([5, 1])
                    cc1.markdown(f'<div class="pr"><span class="pr-k">{c.get("condition","")}</span><span class="pr-v">{c.get("notes","")}</span></div>', unsafe_allow_html=True)
                    if cc2.button("Delete", key=f"del_cond_{c['id']}"):
                        db_delete("medical_history", c["id"])
                        st.rerun()
            if meds:
                for m in meds:
                    mc1, mc2 = st.columns([5, 1])
                    mc1.markdown(f'<div class="pr"><span class="pr-k">{m.get("name","")}</span><span class="pr-v">{m.get("dose","")} · {m.get("frequency","")}</span></div>', unsafe_allow_html=True)
                    if mc2.button("Delete", key=f"del_med_{m['id']}"):
                        db_delete("medications", m["id"])
                        st.rerun()
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
            with st.expander("Family history & past surgeries"):
                bg_text = st.text_area("Family history & past surgeries", value=((health_bg_row or {}).get("notes") or ""), height=90, key="ed_health_bg", label_visibility="collapsed")
                if st.button("Save", key="save_health_bg"):
                    db_upsert("profile_notes", {"user_id": user_id, "notes": bg_text}, on_conflict="user_id")
                    st.success("Saved.")
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

    with st.container(border=True):
        st.markdown('#### Dietary Profile & Restrictions')
        st.markdown(f"""
<div class="pr"><span class="pr-k">Eating pattern</span><span class="pr-v">{p.get('eating_pattern') or '—'}</span></div>
<div class="pr"><span class="pr-k">Allergies / intolerances</span><span class="pr-v">{p.get('allergies') or '—'}</span></div>
""", unsafe_allow_html=True)
        with st.expander("Edit dietary profile"):
            eating_pattern = st.selectbox("Eating pattern", ["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"],
                                           index=["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"].index(p.get("eating_pattern")) if p.get("eating_pattern") in ["Omnivore", "Vegetarian", "Vegan", "Pescatarian", "Other"] else 0, key="ed_diet")
            allergies = st.text_input("Allergies / intolerances", value=(p.get("allergies") or ""), key="ed_allerg")
            if st.button("Save dietary profile", key="save_diet"):
                db_upsert("profiles", {"id": user_id, "eating_pattern": eating_pattern, "allergies": allergies})
                st.success("Saved.")
                st.rerun()

        meal_window = f"{p.get('first_meal') or '?'} – {p.get('last_meal') or '?'}" if (p.get("first_meal") or p.get("last_meal")) else "—"
        st.markdown(f"""
<div class="pr"><span class="pr-k">Meal window</span><span class="pr-v">{meal_window}</span></div>
<div class="pr"><span class="pr-k">Meals per day</span><span class="pr-v">{p.get('meals_per_day') or '—'}</span></div>
<div class="pr"><span class="pr-k">Eating out</span><span class="pr-v">{p.get('eating_out') or '—'}</span></div>
<div class="pr"><span class="pr-k">Food preferences</span><span class="pr-v">{p.get('food_prefs') or '—'}</span></div>
""", unsafe_allow_html=True)
        with st.expander("Edit eating schedule & food preferences"):
            ec1, ec2 = st.columns(2)
            ed_first_meal = dropdown_with_other(ec1, "First meal time", FIRST_MEAL_OPTIONS, (p.get("first_meal") or ""), key="ed_first_meal")
            ed_last_meal = dropdown_with_other(ec2, "Last meal time", LAST_MEAL_OPTIONS, (p.get("last_meal") or ""), key="ed_last_meal")
            ed_meals_per_day = ec1.selectbox("Meals per day", MEALS_PER_DAY_OPTIONS, index=selectbox_index(MEALS_PER_DAY_OPTIONS, p.get("meals_per_day")), key="ed_meals_per_day")
            ed_eating_out = ec2.selectbox("Eating out / ordering in", EATING_OUT_LEVELS, index=selectbox_index(EATING_OUT_LEVELS, p.get("eating_out")), key="ed_eating_out")
            ed_food_prefs = st.text_area("Food preferences or patterns the coach should know about", value=(p.get("food_prefs") or ""), height=80, key="ed_food_prefs")
            if st.button("Save eating schedule", key="save_eating"):
                db_upsert("profiles", {"id": user_id, "first_meal": ed_first_meal, "last_meal": ed_last_meal,
                                        "meals_per_day": ed_meals_per_day, "eating_out": ed_eating_out, "food_prefs": ed_food_prefs})
                st.success("Saved.")
                st.rerun()

    with st.container(border=True):
        st.markdown('#### Lifestyle — Activity, Sleep, Stress')
        st.markdown("**Activity & exercise**")
        st.markdown(f"""
<div class="pr"><span class="pr-k">Activity level</span><span class="pr-v">{p.get('activity_level') or '—'}</span></div>
<div class="pr"><span class="pr-k">Alcohol</span><span class="pr-v">{p.get('alcohol') or '—'}</span></div>
<div class="pr"><span class="pr-k">Smoking</span><span class="pr-v">{p.get('smoking') or '—'}</span></div>
<div class="pr"><span class="pr-k">Exercise routine</span><span class="pr-v">{p.get('exercise_routine') or '—'}</span></div>
""", unsafe_allow_html=True)
        with st.expander("Edit activity & exercise"):
            ac1, ac2 = st.columns(2)
            ed_activity_level = ac1.selectbox("Activity level", ACTIVITY_LEVELS, index=selectbox_index(ACTIVITY_LEVELS, p.get("activity_level")), key="ed_activity_level")
            ed_alcohol = ac1.selectbox("Alcohol consumption", ALCOHOL_LEVELS, index=selectbox_index(ALCOHOL_LEVELS, p.get("alcohol")), key="ed_alcohol")
            ed_smoking = ac2.selectbox("Smoking / tobacco", SMOKING_LEVELS, index=selectbox_index(SMOKING_LEVELS, p.get("smoking")), key="ed_smoking")
            ed_exercise_routine = st.text_area("Exercise routine", value=(p.get("exercise_routine") or ""), height=70, key="ed_exercise_routine")
            if st.button("Save activity", key="save_activity"):
                db_upsert("profiles", {"id": user_id, "activity_level": ed_activity_level, "alcohol": ed_alcohol,
                                        "smoking": ed_smoking, "exercise_routine": ed_exercise_routine})
                st.success("Saved.")
                st.rerun()

        st.markdown("---")
        st.markdown("**Sleep**")
        sleep_window = f"{p.get('sleep_bedtime') or '?'} → {p.get('sleep_wake_time') or '?'}" if (p.get("sleep_bedtime") or p.get("sleep_wake_time")) else "—"
        st.markdown(f"""
<div class="pr"><span class="pr-k">Bedtime → Wake</span><span class="pr-v">{sleep_window}</span></div>
<div class="pr"><span class="pr-k">Average duration</span><span class="pr-v">{p.get('sleep_duration') or '—'}</span></div>
<div class="pr"><span class="pr-k">Quality</span><span class="pr-v">{f"{p.get('sleep_quality')}/10" if p.get('sleep_quality') else '—'}</span></div>
<div class="pr"><span class="pr-k">Challenges</span><span class="pr-v">{p.get('sleep_challenges') or '—'}</span></div>
""", unsafe_allow_html=True)
        with st.expander("Edit sleep"):
            sc1, sc2, sc3 = st.columns(3)
            ed_bedtime = dropdown_with_other(sc1, "Typical bedtime", BEDTIME_OPTIONS, (p.get("sleep_bedtime") or ""), key="ed_bedtime")
            ed_wake_time = dropdown_with_other(sc2, "Typical wake time", WAKE_TIME_OPTIONS, (p.get("sleep_wake_time") or ""), key="ed_wake_time")
            ed_sleep_duration = dropdown_with_other(sc3, "Average sleep duration", SLEEP_DURATION_OPTIONS, (p.get("sleep_duration") or ""), key="ed_sleep_duration", placeholder="e.g. 6.5 hrs")
            ed_sleep_quality = st.slider("Sleep quality (self-rated)", 1, 10, int(p.get("sleep_quality") or 5), key="ed_sleep_quality")
            ed_sleep_challenges = st.text_area("Sleep challenges", value=(p.get("sleep_challenges") or ""), height=60, key="ed_sleep_challenges")
            if st.button("Save sleep", key="save_sleep"):
                db_upsert("profiles", {"id": user_id, "sleep_bedtime": ed_bedtime, "sleep_wake_time": ed_wake_time,
                                        "sleep_duration": ed_sleep_duration, "sleep_quality": int(ed_sleep_quality), "sleep_challenges": ed_sleep_challenges})
                st.success("Saved.")
                st.rerun()

        st.markdown("---")
        st.markdown("**Stress & symptoms**")
        st.markdown(f"""
<div class="pr"><span class="pr-k">Stress level</span><span class="pr-v">{f"{p.get('stress_level')}/10" if p.get('stress_level') else '—'}</span></div>
<div class="pr"><span class="pr-k">Stressors</span><span class="pr-v">{p.get('stressors') or '—'}</span></div>
<div class="pr"><span class="pr-k">Symptoms</span><span class="pr-v">{p.get('symptoms') or '—'}</span></div>
<div class="pr"><span class="pr-k">Other notes</span><span class="pr-v">{p.get('anything_else') or '—'}</span></div>
""", unsafe_allow_html=True)
        with st.expander("Edit stress & symptoms"):
            ed_stress_level = st.slider("Current stress level", 1, 10, int(p.get("stress_level") or 5), key="ed_stress_level")
            ed_stressors = st.text_input("Primary stressors", value=(p.get("stressors") or ""), key="ed_stressors")
            ed_symptoms = st.text_area("Current symptoms or main concerns", value=(p.get("symptoms") or ""), height=70, key="ed_symptoms")
            ed_anything_else = st.text_area("Anything else you'd like your coach to know", value=(p.get("anything_else") or ""), height=50, key="ed_anything_else")
            if st.button("Save stress & symptoms", key="save_stress"):
                db_upsert("profiles", {"id": user_id, "stress_level": int(ed_stress_level), "stressors": ed_stressors,
                                        "symptoms": ed_symptoms, "anything_else": ed_anything_else})
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
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": last_start.isoformat(), "avg_cycle_length": int(avg_len)}, on_conflict="user_id")
                st.success("Saved.")
                st.rerun()
            if st.button("New period started today", key="new_period"):
                db_upsert("cycle_data", {"user_id": user_id, "last_period_start": date.today().isoformat(), "avg_cycle_length": int(cd.get("avg_cycle_length") or 28)}, on_conflict="user_id")
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


def canonicalize_marker_names(raw_names):
    """Reconciles marker names that drifted across independently-extracted
    reports (e.g. "Hemoglobin" vs "Haemoglobin", "TIBC" vs "Total Iron
    Binding Capacity") into one canonical name per underlying test. Each
    report is extracted in isolation and can't see how other reports named
    the same marker, so the per-extraction "use a stable name" instruction
    alone isn't enough on real-world naming variance — verified this
    reconciliation step actually fixes a real drift case. Returns
    {raw_name: canonical_name}, covering every input name."""
    unique_names = sorted(set(raw_names))
    if len(unique_names) < 2:
        return {n: n for n in unique_names}
    prompt = f"""These are lab marker names extracted independently from different reports for the same patient. Some may refer to the exact same clinical test using different wording (e.g. "Hemoglobin" and "Haemoglobin", "TIBC" and "Total Iron Binding Capacity", "Serum Iron" and "Iron, Serum").

Group any names that refer to the same test, and choose ONE clear canonical name per group. Names that are genuinely different tests must stay separate.

Names:
{json.dumps(unique_names)}

Respond with ONLY a JSON object mapping every input name to its chosen canonical name, e.g. {{"Hemoglobin": "Hemoglobin", "Haemoglobin": "Hemoglobin"}}."""
    raw = ai_generate("You are OneSattva, reconciling lab marker names across reports.", prompt, max_tokens=1000)
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        mapping = json.loads(match.group(0) if match else raw)
        return {n: mapping.get(n, n) for n in unique_names}
    except Exception:
        return {n: n for n in unique_names}


def _coerce_lab_value(value):
    """Real document extraction sometimes outputs a number as a JSON string
    (e.g. "11.3" instead of 11.3) — an isinstance(value, (int, float)) check
    silently drops those from trending even though they display fine in the
    Key Numbers cards (which don't type-check). Coerce before filtering."""
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except (ValueError, AttributeError):
            return None
    return None


def build_marker_trend_series(labs):
    """Aggregates structured_values across all reports by canonical marker
    name, keyed by report date — returns {marker: [(date, value, unit), ...]}
    for markers appearing in 2+ reports, sorted chronologically."""
    from collections import defaultdict
    raw_series = defaultdict(list)
    for l in labs:
        report_date = l.get("report_date")
        for m in get_structured_lab_values(l):
            value = _coerce_lab_value(m.get("value"))
            if m.get("marker") and value is not None and report_date:
                raw_series[m["marker"]].append((report_date, value, m.get("unit", "")))
    if not raw_series:
        return {}
    mapping = canonicalize_marker_names(list(raw_series.keys()))
    series = defaultdict(list)
    for raw_name, points in raw_series.items():
        series[mapping.get(raw_name, raw_name)].extend(points)
    return {marker: sorted(points) for marker, points in series.items() if len(points) >= 2}


def render_marker_trend_charts(series):
    import pandas as pd
    if not series:
        st.caption("Not enough overlapping markers across reports yet to chart trends.")
        return
    cols = st.columns(2)
    for i, (marker, points) in enumerate(sorted(series.items())):
        df = pd.DataFrame({marker: [p[1] for p in points]}, index=pd.to_datetime([p[0] for p in points]))
        unit = points[-1][2]
        with cols[i % 2]:
            st.markdown(f'<div class="snap-lbl" style="margin-top:8px">{marker}{f" ({unit})" if unit else ""}</div>', unsafe_allow_html=True)
            st.line_chart(df, height=180)


def render_marker_trend_table(series):
    """A real pivot table (marker rows, one column per report date) built
    directly from structured_values — replaces the old approach of asking
    the AI to cram every date into a single string per cell, which is
    exactly what read as jumbled. Numbers come from code, not LLM
    formatting, so column count and alignment are always reliable."""
    import pandas as pd
    if not series:
        return
    all_dates = sorted({p[0] for points in series.values() for p in points})
    rows = {}
    for marker, points in sorted(series.items()):
        unit = points[-1][2]
        by_date = {p[0]: p[1] for p in points}
        row_label = f"{marker} ({unit})" if unit else marker
        rows[row_label] = [by_date.get(d, None) for d in all_dates]
    df = pd.DataFrame(rows, index=all_dates).T
    df.columns.name = "Marker \\ Date"
    st.dataframe(df, use_container_width=True)


def show_profile_labs(user_id, profile):
    st.markdown('<div class="sl first">Upload a new report</div>', unsafe_allow_html=True)
    report_date = st.date_input("Report date", value=date.today(), key="lab_date", help="For uploaded files, we'll try to read the actual date off the document and use that instead — this is only the fallback if we can't find one, or if you're pasting values instead of uploading a file.")
    lab_files = st.file_uploader("Upload lab report(s) (PDF or image)", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True, key="lab_files", help="You can upload more than one file.")
    raw_values = st.text_area("Or paste lab values", height=140, key="lab_raw")
    if st.button("Upload & analyse", key="lab_save"):
        attempted = 0
        saved_summaries = []
        if raw_values.strip():
            attempted += 1
            result = save_lab_report(user_id, report_date, text=raw_values.strip())
            if result is not None:
                saved_summaries.append(result)
        for lab_file in (lab_files or []):
            attempted += 1
            result = save_lab_report(user_id, report_date, file_block=lab_file_to_content_block(lab_file), file_label=lab_file.name)
            if result is not None:
                saved_summaries.append(result)
        if attempted == 0:
            st.warning("Upload a file or paste your values first.")
        elif saved_summaries:
            has_cycle = profile.get("has_cycle", False) if profile else False
            sys_prompt = build_system_prompt(user_id, profile, has_cycle=has_cycle)
            check_materiality(user_id, sys_prompt, f"New lab report(s) uploaded: {'; '.join(saved_summaries)}")
            st.rerun()

    labs = db_get("lab_reports", user_id, order_col="report_date")
    if len(labs) >= 2:
        tc1, tc2 = st.columns([5, 1])
        tc1.markdown('<div class="sl" style="margin-top:0">Trends across your reports</div>', unsafe_allow_html=True)
        if tc2.button("↻ Refresh", key="refresh_trends_btn"):
            with st.spinner("Refreshing..."):
                refresh_lab_trends(user_id)
            st.rerun()
        marker_series = build_marker_trend_series(labs)
        render_marker_trend_charts(marker_series)
        render_marker_trend_table(marker_series)
        trends = db_get_single("lab_trends", user_id)
        if trends and trends.get("content"):
            st.markdown(trends["content"])
        else:
            with st.spinner("Comparing your reports..."):
                refresh_lab_trends(user_id)
            trends = db_get_single("lab_trends", user_id)
            st.markdown((trends or {}).get("content") or "No overlapping markers to compare yet.")
        with st.expander("Clarify or ask your coach about these trends"):
            trend_q = st.text_area("If the coach flagged something it wants to check with you (e.g. did you start a new supplement between reports?), answer here — or ask anything about the pattern.", key="trend_clarify")
            if st.button("Send to your coach", key="trend_clarify_btn") and trend_q:
                st.session_state.page = "coach"
                st.session_state.coach_seed = f"About the trend pattern across my lab reports: {trend_q}"
                st.rerun()

    st.markdown('<div class="sl">Saved reports</div>', unsafe_allow_html=True)
    if labs:
        st.caption("✓ Current (≤90 days) = your coach's primary reference. Recent (91-180 days) = trend context only. Historical (>180 days) = background only, a retest is flagged as needed.")
    else:
        st.caption("No lab reports yet.")
    for l in labs:
        try:
            days_old = (date.today() - date.fromisoformat(l["report_date"])).days
            freshness = "✓ Current" if days_old <= 90 else ("Recent" if days_old <= 180 else "Historical")
        except Exception:
            freshness = "—"
        lc1, lc2, lc3 = st.columns([3, 1, 1])
        lc1.markdown(f"**{l.get('report_date','')}** — {plain_preview(l.get('summary',''))}")
        lc2.markdown(f"`{freshness}`")
        if lc3.button("Delete", key=f"del_lab_{l['id']}"):
            db_delete("lab_reports", l["id"])
            refresh_lab_trends(user_id)
            st.rerun()
        with st.expander("View full interpretation & extracted values", key=f"lab_detail_{l['id']}"):
            st.markdown(f"**Coach interpretation**\n\n{l.get('summary','') or '_None._'}")
            st.markdown("---")
            structured = get_structured_lab_values(l)
            if structured:
                st.markdown("**Key numbers**")
                render_lab_key_numbers(structured)
                with st.expander("View raw extracted text"):
                    st.markdown(l.get('raw_values','') or '_None._')
            else:
                st.markdown(f"**Extracted values**\n\n{l.get('raw_values','') or '_None._'}")
            st.markdown("---")
            report_q = st.text_area("Ask your coach about this specific report", key=f"lab_clarify_{l['id']}")
            if st.button("Send to your coach", key=f"lab_clarify_btn_{l['id']}") and report_q:
                st.session_state.page = "coach"
                st.session_state.coach_seed = f"About my lab report from {l.get('report_date','')}: {report_q}"
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
        st.caption("No wearable data uploaded yet.")

    st.markdown('<div class="sl">Upload wearable data (WHOOP CSV export)</div>', unsafe_allow_html=True)
    files = st.file_uploader("Upload your WHOOP export CSVs", accept_multiple_files=True, type="csv",
                              help="Typically named physiological_cycles.csv, sleeps.csv, workouts.csv, journal_entries.csv — these are just examples of what WHOOP usually calls them, the filenames don't need to match exactly. We match by column headers inside each file, not the filename.")
    if files and st.button("Upload files"):
        imported, file_results = import_whoop_csvs(user_id, files)
        show_whoop_import_result(imported, file_results)

    # Re-fetch fresh (rather than reusing the `wearable` list from the top of
    # this function) so a just-completed upload shows up here immediately —
    # without a st.rerun(), which would wipe the diagnostics message above
    # before the user can read it.
    wearable_current = db_get("wearable_data", user_id, order_col="data_date", limit=14)
    if wearable_current:
        st.markdown('<div class="sl">Recent days on file</div>', unsafe_allow_html=True)
        for w in wearable_current:
            metrics = " · ".join(f"{k.replace('_',' ')}: {w[k]}" for k in ["hrv", "recovery_score", "sleep_performance", "strain"] if w.get(k) is not None)
            st.markdown(f"<div class=\"pr\"><span class=\"pr-k\">{w.get('data_date','')}</span><span class=\"pr-v\">{metrics or '—'}</span></div>", unsafe_allow_html=True)

    with st.expander("Manual entry"):
        m_date = st.date_input("Date", value=date.today(), key="manual_w_date")
        c1, c2, c3 = st.columns(3)
        hrv = c1.number_input("HRV (ms)", 0, 200, 50, key="manual_hrv")
        recovery = c2.number_input("Recovery (%)", 0, 100, 60, key="manual_rec")
        sleep_perf = c3.number_input("Sleep performance (%)", 0, 100, 75, key="manual_sleep")
        if st.button("Save manual entry"):
            db_upsert("wearable_data", {"user_id": user_id, "data_date": m_date.isoformat(), "hrv": hrv, "recovery_score": recovery, "sleep_performance": sleep_perf}, on_conflict="user_id,data_date")
            st.success("Saved.")
            st.rerun()


CATEGORY_LABELS = {
    "lab_range": "Lab range", "supplement_interaction": "Supplement interaction",
    "triage_language": "Triage language", "general": "General",
}


# ── Admin — knowledge CMS (early-tester feedback #4, Piece 1) ───────────────
def show_admin(user_id, profile):
    st.markdown('<div class="pg-title">Knowledge admin</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Global rules every coach draws on — functional ranges, supplement interactions, triage language. Changes take effect on the next response, no redeploy needed.</div>', unsafe_allow_html=True)

    with st.expander("+ Add a new rule"):
        new_category = st.selectbox("Category", list(CATEGORY_LABELS.keys()), format_func=lambda c: CATEGORY_LABELS[c], key="new_rule_category")
        new_title = st.text_input("Title", key="new_rule_title", placeholder="e.g. Ferritin functional range")
        new_content = st.text_area("Content", key="new_rule_content", height=100,
                                    placeholder="e.g. Functional optimal ferritin for most adults is 50-100 ng/mL, well above the conventional lab's low-end cutoff around 15-20 ng/mL — flag low-normal ferritin as relevant to fatigue/hair-loss presentations.")
        if st.button("Add rule", key="add_rule_btn", type="primary") and new_title.strip() and new_content.strip():
            save_knowledge_rule(new_category, new_title.strip(), new_content.strip())
            st.success("Rule added — live immediately.")
            st.rerun()

    st.markdown('<div class="sl">Existing rules</div>', unsafe_allow_html=True)
    rules = get_all_global_knowledge_rules()
    if not rules:
        st.caption("No rules yet — add the first one above.")
        return

    filter_cat = st.selectbox("Filter by category", ["All"] + list(CATEGORY_LABELS.keys()), format_func=lambda c: c if c == "All" else CATEGORY_LABELS[c], key="rule_filter")
    shown = rules if filter_cat == "All" else [r for r in rules if r.get("category") == filter_cat]

    for r in shown:
        active = r.get("active", True)
        with st.container(border=True):
            st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center">
<div><span class="triage t-bg">{CATEGORY_LABELS.get(r.get('category',''), r.get('category',''))}</span> <strong>{r.get('title','')}</strong>{' <span style="color:var(--mid);font-size:11px">(inactive)</span>' if not active else ''}</div>
</div>""", unsafe_allow_html=True)
            st.markdown(f'<div style="color:var(--mid);font-size:13px;margin:6px 0">{r.get("content","")}</div>', unsafe_allow_html=True)

            with st.expander("Edit"):
                ed_category = st.selectbox("Category", list(CATEGORY_LABELS.keys()), format_func=lambda c: CATEGORY_LABELS[c],
                                            index=list(CATEGORY_LABELS.keys()).index(r.get("category")) if r.get("category") in CATEGORY_LABELS else 0, key=f"ed_cat_{r['id']}")
                ed_title = st.text_input("Title", value=r.get("title", ""), key=f"ed_title_{r['id']}")
                ed_content = st.text_area("Content", value=r.get("content", ""), height=100, key=f"ed_content_{r['id']}")
                ec1, ec2, ec3 = st.columns(3)
                if ec1.button("Save changes", key=f"save_rule_{r['id']}", type="primary") and ed_title.strip() and ed_content.strip():
                    save_knowledge_rule(ed_category, ed_title.strip(), ed_content.strip(), rule_id=r["id"])
                    st.success("Saved.")
                    st.rerun()
                if ec2.button("Deactivate" if active else "Reactivate", key=f"toggle_rule_{r['id']}"):
                    set_knowledge_rule_active(r["id"], not active)
                    st.rerun()
                versions = get_knowledge_rule_versions(r["id"])
                if versions:
                    with ec3.popover(f"History ({len(versions)})"):
                        for v in versions:
                            st.markdown(f"**{v.get('edited_at','')[:16]}** · {v.get('edited_by','')}\n\n{v.get('title','')} — {v.get('content','')}")


# ── Main Entry Point ──────────────────────────────────────────────────────────
def main():
    if "user_id" not in st.session_state:
        st.session_state.auth_mode = st.session_state.get("auth_mode", "login")
        show_auth()
        return

    # Re-apply the Supabase auth token on every Streamlit rerun — the module-level
    # client is shared across reruns but postgrest.auth() must be called each time
    # or RLS filters every query to empty, causing silent save failures and bad reads.
    if "access_token" in st.session_state:
        supabase.postgrest.auth(st.session_state.access_token)

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
    elif page == "admin" and is_admin():
        show_admin(user_id, profile)


if __name__ == "__main__":
    main()

