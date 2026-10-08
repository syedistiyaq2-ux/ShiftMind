import base64
import html
import os
import re
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()


def clean(value):
    return (value or "").strip().strip('"').strip("'")


GROQ_API_KEY = clean(os.getenv("GROQ_API_KEY"))

HINDSIGHT_API_URL = clean(
    os.getenv("HINDSIGHT_API_URL")
).rstrip("/")

HINDSIGHT_API_KEY = clean(
    os.getenv("HINDSIGHT_API_KEY")
)

BANK_ID = (
    clean(os.getenv("HINDSIGHT_BANK_ID"))
    or clean(os.getenv("BANK_ID"))
    or "shiftmind-demo"
)

GROQ_MODELS = [
    clean(os.getenv("GROQ_MODEL"))
    or "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="ShiftMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# STYLING
# ------------------------------------------------------------
# Dark page with an indigo glow, spotlight and fine grid.
# Content sits on white cards so every form stays readable.
# Optional: put bg.jpg / bg.png / background.jpg next to this
# file and it is used as a photo layer under the glow.
# ============================================================

def load_background_uri():
    base = os.path.dirname(os.path.abspath(__file__))
    for name in ("bg.jpg", "bg.jpeg", "bg.png", "background.jpg", "background.png"):
        path = os.path.join(base, name)
        if os.path.exists(path):
            mime = "image/png" if name.endswith(".png") else "image/jpeg"
            with open(path, "rb") as f:
                return f"data:{mime};base64," + base64.b64encode(f.read()).decode()
    return None


_glow_layers = (
    "radial-gradient(ellipse 60% 45% at 88% 0%, rgba(255,255,255,0.14), transparent 62%), "
    "radial-gradient(ellipse 85% 40% at 50% 104%, rgba(79,70,229,0.75), transparent 72%), "
    "radial-gradient(ellipse 45% 35% at 0% 100%, rgba(99,102,241,0.30), transparent 70%), "
    "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), "
    "linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)"
)
_glow_sizes = "auto, auto, auto, 72px 72px, 72px 72px"

_bg_uri = load_background_uri()
if _bg_uri:
    _bg_image = (
        _glow_layers
        + ", linear-gradient(rgba(11,10,20,0.72), rgba(11,10,20,0.88)), "
        + f'url("{_bg_uri}")'
    )
    _bg_sizes = _glow_sizes + ", auto, cover"
else:
    _bg_image = _glow_layers
    _bg_sizes = _glow_sizes

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: #0b0a14;
        background-image: {_bg_image};
        background-size: {_bg_sizes};
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,700&display=swap');

    :root {
        --ink: #16192e;
        --muted: #5d6280;
        --line: #dcdff0;
        --accent: #4338ca;
        --accent-dark: #3730a3;
        --accent-tint: #eceafd;
    }

    html, body, [class*="css"], .stApp, .stMarkdown, p, label, input, textarea, button {
        font-family: 'Plus Jakarta Sans', -apple-system, 'Segoe UI', sans-serif !important;
    }

    /* Streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
    /* Keep the toolbar: the sidebar reopen button lives inside it.
       Hide only the right-side items (deploy button, menu). */
    [data-testid="stToolbar"] {
        visibility: visible !important;
        display: flex !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        z-index: 999999 !important;
    }
    [data-testid="stToolbarActions"],
    [data-testid="stMainMenu"],
    [data-testid="stAppDeployButton"],
    .stDeployButton { display: none !important; }

    /* Sidebar reopen button (different test IDs across Streamlit versions) */
    [data-testid="collapsedControl"],
    [data-testid="stExpandSidebarButton"] {
        visibility: visible !important;
        display: flex !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        position: relative !important;
        z-index: 999999 !important;
        color: #e5e7ff !important;
        background: rgba(255, 255, 255, 0.10) !important;
        border-radius: 8px !important;
        cursor: pointer !important;
    }
    [data-testid="collapsedControl"] button,
    [data-testid="stExpandSidebarButton"] button {
        visibility: visible !important;
        display: flex !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        cursor: pointer !important;
    }
    [data-testid="collapsedControl"] svg,
    [data-testid="stExpandSidebarButton"] svg {
        visibility: visible !important;
        display: block !important;
        fill: #e5e7ff !important;
        color: #e5e7ff !important;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1.5rem !important;
        max-width: 1320px !important;
    }

    /* Sidebar (light) */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--line);
    }
    section[data-testid="stSidebar"] .block-container { padding-top: 1.2rem !important; }

    h1, h2, h3, h4 { color: var(--ink) !important; letter-spacing: -0.01em; }

    /* ---------- Top bar ---------- */
    .topbar {
        display: flex; align-items: center; justify-content: space-between; gap: 1rem;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.14);
        backdrop-filter: blur(8px);
        border-radius: 12px;
        padding: 0.65rem 1.1rem;
    }
    .brand { display: flex; align-items: center; gap: 0.7rem; }
    .brand-mark {
        width: 34px; height: 34px; border-radius: 9px;
        background: var(--accent); color: #fff;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 1.05rem;
    }
    .brand-name { font-weight: 800; font-size: 1.1rem; line-height: 1.1; color: var(--ink); }
    .brand-tag { font-size: 0.8rem; color: var(--muted); }
    .topbar .brand-name { color: #ffffff; }
    .topbar .brand-tag { color: #a9a8cc; }
    .top-right { display: flex; align-items: center; gap: 0.9rem; }
    .bank { font-size: 0.8rem; color: #a9a8cc; }
    .bank b { color: #ffffff; font-weight: 600; }
    .pill {
        display: inline-flex; align-items: center; gap: 0.45rem;
        padding: 0.3rem 0.85rem; border-radius: 999px;
        font-size: 0.82rem; font-weight: 700; background: #fff;
    }
    .pill::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
    .pill-on  { color: #137a46; }
    .pill-off { color: #b42323; }

    /* ---------- Hero ---------- */
    .hero {
        display: grid; grid-template-columns: 1.35fr 1fr; gap: 1rem;
        align-items: center; padding: 1.4rem 0.3rem 1.3rem 0.3rem;
    }
    .hero-title {
        font-size: clamp(2.3rem, 5.2vw, 4.4rem);
        font-weight: 800; line-height: 1.0; letter-spacing: -0.03em;
        background: linear-gradient(180deg, #ffffff 35%, #a7a5cf 100%);
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent; color: transparent;
    }
    .hero-sub {
        color: #b9b8d6; font-size: 0.98rem; line-height: 1.55;
        max-width: 34rem; margin: 0.8rem 0 1.2rem 0;
    }
    .hero-stats { display: flex; gap: 2.2rem; flex-wrap: wrap; }
    .hs-val { font-style: italic; font-weight: 700; font-size: 1.8rem; color: #ebeaf9; line-height: 1.1; }
    .hs-val.ok { color: #6ee7a8; }
    .hs-label { font-size: 0.8rem; color: #9c9bc2; margin-top: 0.1rem; }
    .orbit { width: 100%; max-width: 380px; justify-self: end; }
    @media (max-width: 900px) {
        .hero { grid-template-columns: 1fr; }
        .orbit { display: none; }
    }

    /* ---------- Cards ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border: 1px solid rgba(255,255,255,0.35) !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 30px rgba(5, 4, 20, 0.35);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown,
    div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown p,
    div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown li { color: var(--ink); }
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] { color: var(--muted); }

    .card-title { font-size: 1.02rem; font-weight: 800; color: var(--ink); margin: 0 0 0.15rem 0; }
    .card-sub { font-size: 0.85rem; color: var(--muted); margin: 0 0 0.6rem 0; }

    /* ---------- Inputs ---------- */
    div[data-testid="stTextInput"] label p,
    div[data-testid="stTextArea"] label p,
    div[data-testid="stSelectbox"] label p {
        font-size: 0.85rem !important; font-weight: 600 !important; color: #2b3050 !important;
    }
    div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1.5px solid #9da3c4 !important;
        border-radius: 9px !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within {
        border: 1.5px solid var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(67, 56, 202, 0.18) !important;
    }
    input, textarea { background-color: #ffffff !important; color: var(--ink) !important; }

    /* ---------- Buttons ---------- */
    .stButton > button, .stDownloadButton > button {
        border-radius: 999px !important; font-weight: 600 !important; min-height: 40px !important;
        border: 1px solid #b4b9d6 !important; background: #fff !important; color: var(--ink) !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: var(--accent) !important; color: var(--accent) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--accent) !important; border: 1px solid var(--accent) !important; color: #fff !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--accent-dark) !important; border-color: var(--accent-dark) !important; color: #fff !important;
    }

    /* ---------- Brief ---------- */
    .brief-head {
        display: flex; justify-content: space-between; align-items: center;
        background: #14122a; color: #fff; border-radius: 10px;
        padding: 0.7rem 1rem; margin-bottom: 0.4rem;
    }
    .brief-head .t { font-weight: 700; font-size: 0.95rem; }
    .brief-head .m { font-size: 0.8rem; color: #aeb0d6; }

    .sec {
        display: flex; align-items: center;
        border-left: 4px solid var(--c); background: var(--bg); color: var(--c);
        font-weight: 700; font-size: 0.92rem;
        padding: 0.45rem 0.8rem; border-radius: 0 8px 8px 0; margin: 0.95rem 0 0.35rem 0;
    }
    .sec-history { --c: #2a4fd0; --bg: #edf1fe; }
    .sec-failed  { --c: #c0292b; --bg: #fdeeee; }
    .sec-worked  { --c: #17794a; --bg: #e8f6ee; }
    .sec-check   { --c: #a86300; --bg: #fff5e2; }
    .sec-safety  { --c: #b4410f; --bg: #fdeee5; }
    .sec-plain   { --c: var(--accent); --bg: var(--accent-tint); }

    .note {
        border-radius: 10px; padding: 0.65rem 0.9rem; font-size: 0.88rem;
        line-height: 1.5; margin-top: 0.6rem; border: 1px solid;
    }
    .note b { font-weight: 700; }
    .note-info { background: #edf1fe; border-color: #cbd5f6; color: #26397a; }
    .note-warn { background: #fff5e2; border-color: #f2d9a4; color: #6e4300; }

    /* ---------- Workflow steps ---------- */
    .steps { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.7rem; margin-top: 0.4rem; }
    .step { border: 1px solid var(--line); border-radius: 10px; padding: 0.8rem 0.9rem; background: #f8f8fe; }
    .step .n { font-weight: 800; color: var(--accent); font-size: 0.95rem; }
    .step .d { font-size: 0.86rem; color: var(--muted); margin-top: 0.15rem; line-height: 1.45; }

    details { border-radius: 10px !important; border: 1px solid var(--line) !important; background: #fff; }
    details summary p { font-size: 0.88rem !important; font-weight: 500 !important; }

    hr { border-color: var(--line) !important; margin: 0.8rem 0 !important; }

    .foot { text-align: center; color: #8f8eb6; font-size: 0.8rem; margin-top: 0.8rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Fix: dark readable text inside the white cards ----
# (text colour only, nothing else is changed)
st.markdown(
    """
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] li,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] ol,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] ul,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] strong,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] em,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h1,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h2,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h3,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h4,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] td,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] th,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stText"],
    div[data-testid="stVerticalBlockBorderWrapper"] label p {
        color: #16192e !important;
    }

    /* Inline code in the brief */
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] code {
        color: #3730a3 !important;
        background: #eceafd !important;
    }

    /* Recalled-memory expanders */
    div[data-testid="stVerticalBlockBorderWrapper"] details,
    div[data-testid="stVerticalBlockBorderWrapper"] details summary,
    div[data-testid="stVerticalBlockBorderWrapper"] details summary p,
    div[data-testid="stVerticalBlockBorderWrapper"] details [data-testid="stExpanderDetails"] p {
        color: #16192e !important;
    }

    /* Captions */
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"],
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p {
        color: #5d6280 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---- Fix 2: white cards + dark text (works on newer Streamlit) ----
st.markdown(
    """
    <style>
    [class*="st-key-card_"] {
        background: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.35) !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 30px rgba(5, 4, 20, 0.35);
        padding: 1rem 1.1rem !important;
    }
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] p,
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] li,
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] ol,
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] ul,
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] strong,
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] em,
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] h1,
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] h2,
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] h3,
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] h4,
    [class*="st-key-card_"] [data-testid="stText"],
    [class*="st-key-card_"] label p,
    [class*="st-key-card_"] label,
    [class*="st-key-card_"] details,
    [class*="st-key-card_"] details summary,
    [class*="st-key-card_"] details summary p,
    [class*="st-key-card_"] details p {
        color: #16192e !important;
    }
    [class*="st-key-card_"] li::marker { color: #16192e !important; }
    [class*="st-key-card_"] [data-testid="stCaptionContainer"],
    [class*="st-key-card_"] [data-testid="stCaptionContainer"] p {
        color: #5d6280 !important;
    }
    [class*="st-key-card_"] .card-title { color: #16192e !important; }
    [class*="st-key-card_"] .card-sub { color: #5d6280 !important; }
    [class*="st-key-card_"] [data-testid="stMarkdownContainer"] code {
        color: #3730a3 !important; background: #eceafd !important;
    }

    /* Primary buttons (Recall & analyze, Save outcome): white text on indigo */
    [class*="st-key-card_"] button[kind="primary"],
    [class*="st-key-card_"] button[data-testid="stBaseButton-primary"] {
        background: #4338ca !important;
        border: 1px solid #4338ca !important;
    }
    [class*="st-key-card_"] button[kind="primary"] *,
    [class*="st-key-card_"] button[data-testid="stBaseButton-primary"] *,
    [class*="st-key-card_"] button[kind="primary"] [data-testid="stMarkdownContainer"] p,
    [class*="st-key-card_"] button[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
    [class*="st-key-card_"] button[kind="primary"]:hover,
    [class*="st-key-card_"] button[data-testid="stBaseButton-primary"]:hover {
        background: #3730a3 !important;
        border-color: #3730a3 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "machine" not in st.session_state:
    st.session_state.machine = "M-204"

if "problem" not in st.session_state:
    st.session_state.problem = (
        "Machine M-204 is showing E17 sensor error again."
    )

if "memories" not in st.session_state:
    st.session_state.memories = []

if "answer" not in st.session_state:
    st.session_state.answer = ""

if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

if "saved" not in st.session_state:
    st.session_state.saved = False


# ============================================================
# DEMO SCENARIOS
# ============================================================

EXAMPLES = [
    (
        "M-204",
        "Machine M-204 is showing E17 sensor error again.",
    ),
    (
        "Conveyor C-12",
        "Conveyor C-12 keeps stopping every few minutes during the night shift.",
    ),
    (
        "Forklift F-07",
        "Forklift F-07 loses hydraulic pressure when lifting heavy pallets.",
    ),
]


# ============================================================
# CONNECT TO GROQ + HINDSIGHT
# ============================================================

@st.cache_resource
def get_clients():

    missing = []

    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")

    if not HINDSIGHT_API_URL:
        missing.append("HINDSIGHT_API_URL")

    if not HINDSIGHT_API_KEY:
        missing.append("HINDSIGHT_API_KEY")

    if missing:
        raise Exception(
            "Missing in .env: "
            + ", ".join(missing)
        )

    if not HINDSIGHT_API_URL.startswith("http"):
        raise Exception(
            "HINDSIGHT_API_URL must start with "
            "http:// or https://"
        )

    groq = Groq(
        api_key=GROQ_API_KEY
    )

    hindsight = Hindsight(
        base_url=HINDSIGHT_API_URL,
        api_key=HINDSIGHT_API_KEY,
    )

    return groq, hindsight


try:

    groq_client, memory = get_clients()

    services_ready = True
    connection_error = ""

except Exception as e:

    services_ready = False
    connection_error = str(e)


# ============================================================
# HINDSIGHT RECALL
# ============================================================

def recall_memories(problem):

    def worker():

        local_memory = Hindsight(
            base_url=HINDSIGHT_API_URL,
            api_key=HINDSIGHT_API_KEY,
        )

        response = local_memory.recall(
            bank_id=BANK_ID,
            query=problem,
        )

        results = getattr(
            response,
            "results",
            None,
        ) or []

        memories = []

        for item in results[:6]:

            text = getattr(
                item,
                "text",
                None,
            )

            if text:
                memories.append(text)

            else:
                memories.append(str(item))

        return memories

    # IMPORTANT:
    # Hindsight recall runs in a worker thread
    # because direct calls previously caused
    # Streamlit async-loop problems.

    with ThreadPoolExecutor(
        max_workers=1
    ) as executor:

        future = executor.submit(
            worker
        )

        return future.result()


# ============================================================
# AI PROMPT
# ============================================================

def build_prompt(
    machine,
    problem,
    memories,
):

    if memories:

        memory_text = "\n\n".join(
            [
                f"MEMORY {i + 1}:\n{item}"
                for i, item in enumerate(memories)
            ]
        )

    else:

        memory_text = (
            "No relevant historical memories were found."
        )

    return f"""
You are ShiftMind, an AI institutional handover
assistant for 24/7 operational teams.

Your job is to help the current shift learn
from previous operational experience.

CURRENT MACHINE:
{machine}

CURRENT PROBLEM:
{problem}

HISTORICAL MEMORIES:
{memory_text}

IMPORTANT RULES:

1. Do not invent historical facts.
2. Do not claim something worked unless the
   historical memories support it.
3. Clearly distinguish historical evidence
   from recommendations.
4. If there is insufficient evidence,
   say so.
5. Safety comes before speed.
6. The human operator makes the final decision.

Use exactly these sections:

### 📜 What happened before

Summarize relevant historical incidents.

### ❌ What failed

Explain approaches that failed or did not
fully resolve the issue.

### ✅ What worked

Explain successful approaches only when
supported by the memories.

### 🔍 What to check now

Give practical next checks based on the
historical evidence.

### ⚠️ Safety / escalation

Mention when the operator should stop,
escalate, or follow approved procedures.

Keep the response concise and easy for a
shift operator to understand.
"""


# ============================================================
# GROQ
# ============================================================

def ask_groq(prompt):

    last_error = ""

    for model in GROQ_MODELS:

        try:

            response = (
                groq_client
                .chat
                .completions
                .create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are ShiftMind, a "
                                "professional operational "
                                "handover assistant."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.2,
                    timeout=30,
                )
            )

            return response.choices[0].message.content

        except Exception as e:

            last_error = str(e)

            if "401" in last_error:
                raise Exception(
                    "Invalid Groq API key. "
                    "Check GROQ_API_KEY in .env."
                )

            if "429" in last_error:
                raise Exception(
                    "Groq rate limit reached. "
                    "Please wait and try again."
                )

            if (
                "404" in last_error
                or "model" in last_error.lower()
            ):
                continue

            raise

    raise Exception(
        "No Groq model worked.\n\n"
        + last_error
    )


# ============================================================
# UI HELPERS (presentation only)
# ============================================================

def card_title(title, sub=None):
    st.markdown(
        f'<div class="card-title">{html.escape(title)}</div>'
        + (f'<div class="card-sub">{html.escape(sub)}</div>' if sub else ""),
        unsafe_allow_html=True,
    )


def section_class(title):
    t = title.lower()
    if "safety" in t or "escalat" in t:
        return "sec-safety"
    if "fail" in t:
        return "sec-failed"
    if "worked" in t:
        return "sec-worked"
    if "check" in t:
        return "sec-check"
    if "before" in t or "happen" in t:
        return "sec-history"
    return "sec-plain"


def render_brief(answer):
    """Split the model answer on '###' headings and show colour-coded sections."""
    parts = [p for p in answer.split("###") if p.strip()]
    has_headings = "###" in answer

    if not has_headings:
        st.markdown(answer)
        return

    for part in parts:
        lines = part.strip().split("\n")
        # drop leading emoji / symbols from the heading
        title = re.sub(r"^[^\w]+", "", lines[0].strip(), flags=re.UNICODE)
        body = "\n".join(lines[1:]).strip()
        st.markdown(
            f'<div class="sec {section_class(title)}">{html.escape(title)}</div>',
            unsafe_allow_html=True,
        )
        if body:
            st.markdown(body)


ORBIT_SVG = """
<svg class="orbit" viewBox="0 0 380 250" xmlns="http://www.w3.org/2000/svg"
     style="font-family:'Plus Jakarta Sans',sans-serif">
  <defs>
    <radialGradient id="smglow" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#6366f1" stop-opacity="0.75"/>
      <stop offset="1" stop-color="#6366f1" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <circle cx="190" cy="125" r="100" fill="url(#smglow)"/>
  <ellipse cx="190" cy="125" rx="150" ry="72" fill="none" stroke="rgba(255,255,255,0.45)" stroke-width="1.2"/>
  <ellipse cx="190" cy="125" rx="110" ry="50" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1" stroke-dasharray="3 6"/>
  <rect x="164" y="99" width="52" height="52" rx="14" fill="#4338ca" stroke="rgba(255,255,255,0.55)"/>
  <text x="190" y="135" text-anchor="middle" font-size="26" font-weight="800" fill="#ffffff">S</text>
  <rect x="2"   y="112" width="76" height="26" rx="13" fill="#ffffff"/>
  <text x="40"  y="129" text-anchor="middle" font-size="12" font-weight="700" fill="#16192e">Recall</text>
  <rect x="152" y="40"  width="76" height="26" rx="13" fill="#ffffff"/>
  <text x="190" y="57"  text-anchor="middle" font-size="12" font-weight="700" fill="#16192e">Reason</text>
  <rect x="302" y="112" width="76" height="26" rx="13" fill="#ffffff"/>
  <text x="340" y="129" text-anchor="middle" font-size="12" font-weight="700" fill="#16192e">Resolve</text>
  <rect x="152" y="184" width="76" height="26" rx="13" fill="#ffffff"/>
  <text x="190" y="201" text-anchor="middle" font-size="12" font-weight="700" fill="#16192e">Retain</text>
</svg>
"""


def render_stats(slot):
    machine_val = html.escape(st.session_state.machine or "—")
    recalled = len(st.session_state.memories)
    analysis = "Complete" if st.session_state.answer else "Ready"
    loop = "Recorded" if st.session_state.saved else "Active"

    hero_html = f"""
        <div class="hero">
            <div>
                <div class="hero-title">EVERY SHIFT<br>REMEMBERS.</div>
                <div class="hero-sub">
                    Recall similar past incidents, see what failed and what
                    worked, and hand the next shift a clear brief.
                </div>
                <div class="hero-stats">
                    <div>
                        <div class="hs-val">{machine_val}</div>
                        <div class="hs-label">Current asset</div>
                    </div>
                    <div>
                        <div class="hs-val">{recalled}</div>
                        <div class="hs-label">Memories recalled</div>
                    </div>
                    <div>
                        <div class="hs-val {'ok' if st.session_state.answer else ''}">{analysis}</div>
                        <div class="hs-label">AI analysis</div>
                    </div>
                    <div>
                        <div class="hs-val {'ok' if st.session_state.saved else ''}">{loop}</div>
                        <div class="hs-label">Learning loop</div>
                    </div>
                </div>
            </div>
            {ORBIT_SVG}
        </div>
        """
    hero_html = " ".join(
        line.strip() for line in hero_html.splitlines() if line.strip()
    )
    slot.markdown(hero_html, unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand" style="margin-bottom:0.2rem;">
            <div class="brand-mark">S</div>
            <div>
                <div class="brand-name">ShiftMind</div>
                <div class="brand-tag">Institutional memory</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("**System status**")

    if services_ready:

        st.success("Hindsight connected")
        st.success("AI engine connected")

    else:

        st.error("Services unavailable")

        st.code(
            connection_error
        )

    st.divider()

    st.markdown("**Workflow**")

    st.markdown(
        """
        1. **Recall** – retrieve relevant operational history  
        2. **Reason** – analyze the current problem  
        3. **Resolve** – the operator takes action  
        4. **Retain** – save the outcome for future shifts
        """
    )

    st.divider()

    if services_ready:

        if st.button(
            "Test connections",
            use_container_width=True,
        ):

            with st.spinner(
                "Testing Hindsight..."
            ):

                try:

                    recall_memories(
                        "ShiftMind connection test"
                    )

                    st.success(
                        "Hindsight connection working."
                    )

                except Exception as e:

                    st.error(
                        f"Hindsight error: {e}"
                    )

            try:

                groq_client.models.list()

                st.success(
                    "Groq connection working."
                )

            except Exception as e:

                st.error(
                    f"Groq error: {e}"
                )

        st.markdown("**Demo data**")

        if st.button(
            "Load demo incidents (M-204, C-12, F-07)",
            use_container_width=True,
        ):

            demo_incidents = [
                (
                    "Warehouse incident.\n"
                    "Machine: M-204\n"
                    "Error: E17 sensor error.\n"
                    "What was tried: restarted the "
                    "machine and cleaned the sensor, "
                    "but the error returned.\n"
                    "What resolved the issue: "
                    "sensor cable replacement.\n"
                    "Outcome: Resolved."
                ),
                (
                    "Warehouse incident.\n"
                    "Machine: Conveyor C-12\n"
                    "Problem: stopped every few minutes "
                    "during the night shift.\n"
                    "What was tried: reset the controller "
                    "and cleared the belt, but it kept "
                    "stopping.\n"
                    "What resolved the issue: realigned "
                    "the belt and replaced the worn "
                    "tracking sensor.\n"
                    "Outcome: Resolved."
                ),
                (
                    "Warehouse incident.\n"
                    "Machine: Forklift F-07\n"
                    "Problem: lost hydraulic pressure "
                    "when lifting heavy pallets.\n"
                    "What was tried: topped up hydraulic "
                    "fluid, but pressure dropped again.\n"
                    "What resolved the issue: replaced "
                    "a leaking hydraulic hose.\n"
                    "Outcome: Resolved."
                ),
            ]

            try:

                for incident in demo_incidents:

                    memory.retain(
                        bank_id=BANK_ID,
                        content=incident,
                        context="Warehouse shift incident",
                    )

                st.success(
                    "3 demo incidents stored. "
                    "They may take a short time to "
                    "become searchable."
                )

            except Exception as e:

                st.error(
                    f"Could not store demo: {e}"
                )

    st.divider()

    st.caption(
        "Human operators remain responsible "
        "for final operational decisions."
    )


# ============================================================
# TOP BAR
# ============================================================

st.markdown(
    f"""
    <div class="topbar">
        <div class="brand">
            <div class="brand-mark">S</div>
            <div>
                <div class="brand-name">ShiftMind</div>
                <div class="brand-tag">Institutional memory for 24/7 operational teams</div>
            </div>
        </div>
        <div class="top-right">
            <span class="bank">Memory bank: <b>{html.escape(BANK_ID)}</b></span>
            <span class="pill {'pill-on' if services_ready else 'pill-off'}">{'System online' if services_ready else 'System offline'}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Filled at the end of the script so it always shows the latest state
stats_slot = st.empty()


# ============================================================
# MAIN WORKSPACE
# ============================================================

left, right = st.columns([5, 7], gap="medium")


# ------------------------------------------------------------
# LEFT: INCIDENT INPUT + RECALLED MEMORY
# ------------------------------------------------------------

with left:

    with st.container(border=True, key="card_incident"):

        card_title(
            "Current incident",
            "Describe the problem the shift is handling.",
        )

        machine = st.text_input(
            "Machine / asset",
            value=st.session_state.machine,
            placeholder="Example: M-204",
        )

        problem = st.text_area(
            "Current problem",
            value=st.session_state.problem,
            height=120,
            placeholder=(
                "Example: Machine M-204 is showing "
                "E17 sensor error again."
            ),
        )

        st.session_state.machine = machine
        st.session_state.problem = problem

        st.markdown("**⚡ Quick Scenarios**")

        q1, q2, q3 = st.columns(3)

        with q1:

            if st.button(
                "🏭 M-204",
                use_container_width=True,
            ):

                st.session_state.machine = (
                    EXAMPLES[0][0]
                )

                st.session_state.problem = (
                    EXAMPLES[0][1]
                )

                st.rerun()

        with q2:

            if st.button(
                "⚙️ C-12",
                use_container_width=True,
            ):

                st.session_state.machine = (
                    EXAMPLES[1][0]
                )

                st.session_state.problem = (
                    EXAMPLES[1][1]
                )

                st.rerun()

        with q3:

            if st.button(
                "🚜 F-07",
                use_container_width=True,
            ):

                st.session_state.machine = (
                    EXAMPLES[2][0]
                )

                st.session_state.problem = (
                    EXAMPLES[2][1]
                )

                st.rerun()

        analyze_button = st.button(
            "Recall & analyze",
            type="primary",
            use_container_width=True,
        )

        if analyze_button:

            if not machine.strip():

                st.warning(
                    "Please enter a machine or asset."
                )

            elif not problem.strip():

                st.warning(
                    "Please describe the current problem."
                )

            else:

                st.session_state.answer = ""
                st.session_state.saved = False
                st.session_state.analyzed = False

                # ----------------------------------------
                # RECALL
                # ----------------------------------------

                with st.spinner(
                    "Searching Hindsight memory..."
                ):

                    try:

                        memories = recall_memories(
                            problem
                        )

                        st.session_state.memories = (
                            memories
                        )

                        st.session_state.analyzed = True

                    except Exception as e:

                        st.session_state.memories = []

                        st.error(
                            "Could not retrieve historical "
                            "memory."
                        )

                        with st.expander(
                            "Technical details"
                        ):

                            st.code(str(e))

                # ----------------------------------------
                # REASON
                # ----------------------------------------

                if st.session_state.analyzed:

                    with st.spinner(
                        "Analyzing historical experience..."
                    ):

                        try:

                            prompt = build_prompt(
                                machine,
                                problem,
                                st.session_state.memories,
                            )

                            answer = ask_groq(
                                prompt
                            )

                            st.session_state.answer = (
                                answer
                            )

                        except Exception as e:

                            st.error(
                                "Could not generate the "
                                "AI handover brief."
                            )

                            with st.expander(
                                "Technical details"
                            ):

                                st.code(str(e))

    # --------------------------------------------------------
    # INSTITUTIONAL MEMORY
    # --------------------------------------------------------

    with st.container(border=True, key="card_memory"):

        card_title(
            "Recalled memory",
            "Operational history retrieved from Hindsight.",
        )

        if st.session_state.memories:

            st.caption(
                f"{len(st.session_state.memories)} relevant "
                "memory item(s) were supplied to the AI."
            )

            for index, memory_text in enumerate(
                st.session_state.memories,
                1,
            ):

                preview = " ".join(memory_text.split())[:70]

                with st.expander(
                    f"Memory {index}: {preview}…",
                    expanded=False,
                ):

                    st.write(
                        memory_text
                    )

        else:

            st.caption(
                "Nothing recalled yet. Run an analysis "
                "to see matching incidents here."
            )


# ------------------------------------------------------------
# RIGHT: HANDOVER BRIEF + RECORD OUTCOME
# ------------------------------------------------------------

with right:

    with st.container(border=True, key="card_brief"):

        if st.session_state.answer:

            st.markdown(
                f"""
                <div class="brief-head">
                    <span class="t">Shift handover brief · {html.escape(st.session_state.machine or '')}</span>
                    <span class="m">Decision support from historical memory</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            render_brief(st.session_state.answer)

            if st.session_state.memories:

                st.markdown(
                    f"""
                    <div class="note note-info">
                        <b>Evidence:</b> Hindsight contributed
                        {len(st.session_state.memories)} historical memory item(s).
                        Review them before acting. ShiftMind does not assume a
                        pattern unless the evidence supports it.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    """
                    <div class="note note-warn">
                        <b>No evidence found:</b> no relevant historical memories
                        were found, so no historical pattern can be established.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                """
                <div class="note note-warn">
                    <b>Human decision required:</b> ShiftMind provides decision
                    support, not autonomous control. Follow approved procedures
                    and use professional judgment before taking action.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")

            st.download_button(
                "Download brief (.txt)",
                data=st.session_state.answer,
                file_name="shiftmind_brief.txt",
                use_container_width=True,
            )

        else:

            card_title(
                "How ShiftMind works",
                "Enter an incident and select Recall & analyze to "
                "generate the handover brief.",
            )

            st.markdown(
                """
                <div class="steps">
                    <div class="step">
                        <div class="n">Recall</div>
                        <div class="d">Finds similar past incidents stored in Hindsight.</div>
                    </div>
                    <div class="step">
                        <div class="n">Reason</div>
                        <div class="d">Separates what failed from what worked, using only recorded evidence.</div>
                    </div>
                    <div class="step">
                        <div class="n">Resolve</div>
                        <div class="d">The operator decides and acts, following approved procedures.</div>
                    </div>
                    <div class="step">
                        <div class="n">Retain</div>
                        <div class="d">The outcome is saved so the next shift starts with more knowledge.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # RECORD OUTCOME
    # --------------------------------------------------------

    with st.container(border=True, key="card_outcome"):

        card_title(
            "Record the outcome",
            "Close the learning loop by recording what happened "
            "after the action.",
        )

        if not st.session_state.analyzed:

            st.caption(
                "Available after an incident has been analyzed."
            )

        else:

            action_taken = st.text_input(
                "Action taken",
                placeholder=(
                    "Example: Sensor cable was inspected "
                    "and replaced."
                ),
            )

            outcome = st.selectbox(
                "Outcome",
                [
                    "Resolved",
                    "Partially resolved",
                    "Not resolved",
                    "Escalated to maintenance",
                ],
            )

            save_button = st.button(
                "Save outcome to Hindsight",
                type="primary",
                use_container_width=True,
            )

            if save_button:

                if not action_taken.strip():

                    st.warning(
                        "Please describe the action taken."
                    )

                else:

                    content = f"""
Warehouse shift outcome.

Machine:
{st.session_state.machine}

Problem:
{st.session_state.problem}

Action taken:
{action_taken}

Outcome:
{outcome}

This outcome is part of ShiftMind's
organizational learning and may help
future shifts handle similar incidents.
"""

                    try:

                        with st.spinner(
                            "Saving outcome to Hindsight..."
                        ):

                            memory.retain(
                                bank_id=BANK_ID,
                                content=content.strip(),
                                context=(
                                    "Warehouse shift outcome "
                                    "and institutional learning"
                                ),
                            )

                        st.session_state.saved = True

                        st.success(
                            "Outcome saved to Hindsight."
                        )

                        st.info(
                            "The new learning may take "
                            "a short time to become searchable."
                        )

                    except Exception as e:

                        st.error(
                            "Could not save the outcome."
                        )

                        with st.expander(
                            "Technical details"
                        ):

                            st.code(str(e))

            if st.session_state.saved:

                st.success(
                    "Learning loop complete: "
                    "Recall → Reason → Resolve → Retain"
                )

                st.info(
                    "The outcome has been stored in Hindsight "
                    "for future incident analysis."
                )


# ============================================================
# STATS (rendered last so values reflect this run)
# ============================================================

render_stats(stats_slot)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    '<div class="foot">ShiftMind · AI provides decision support. '
    'Human operators remain responsible for final decisions.</div>',
    unsafe_allow_html=True,
)