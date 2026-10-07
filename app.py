import os
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
# SMALL, SAFE UI STYLING
# ============================================================
#
# IMPORTANT:
# No fixed position
# No sticky elements
# No fixed-height containers
# No custom full-screen overlays
# No separate scrolling areas
#
# This only improves the visibility of input fields.
# ============================================================

st.markdown(
    """
    <style>

    /* Visible input fields */

    div[data-baseweb="input"] {
        background-color: white !important;
        border: 1.5px solid #94a3b8 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="textarea"] {
        background-color: white !important;
        border: 1.5px solid #94a3b8 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="input"]:focus-within {
        border: 2px solid #2563eb !important;
    }

    div[data-baseweb="textarea"]:focus-within {
        border: 2px solid #2563eb !important;
    }

    input,
    textarea {
        background-color: white !important;
    }

    /* Buttons */

    .stButton > button {
        border-radius: 9px !important;
        font-weight: 600 !important;
        min-height: 42px !important;
    }

    /* Metrics */

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #dbe4ee;
        border-radius: 12px;
        padding: 14px;
    }

    /* Expanders */

    details {
        border-radius: 10px;
        border: 1px solid #dbe4ee;
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
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🧠 ShiftMind")

    st.caption(
        "Operational Intelligence & "
        "Institutional Memory"
    )

    st.divider()

    st.subheader("🔌 System Status")

    if services_ready:

        st.success("🟢 Hindsight connected")
        st.success("🟢 AI Engine connected")

    else:

        st.error("🔴 Services unavailable")

        st.code(
            connection_error
        )

    st.divider()

    st.subheader("🔄 Workflow")

    st.markdown(
        """
        **1️⃣ Recall**

        Retrieve relevant operational history.

        **2️⃣ Reason**

        Analyze the current problem.

        **3️⃣ Resolve**

        Human operator takes action.

        **4️⃣ Retain**

        Save the outcome for future shifts.
        """
    )

    st.divider()

    if services_ready:

        if st.button(
            "🔌 Test Connections",
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

        st.divider()

        st.subheader("🧪 Demo")

        if st.button(
            "Load M-204 Demo",
            use_container_width=True,
        ):

            try:

                memory.retain(
                    bank_id=BANK_ID,
                    content=(
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
                    context="Warehouse shift incident",
                )

                st.success(
                    "Demo incident stored."
                )

            except Exception as e:

                st.error(
                    f"Could not store demo: {e}"
                )

    st.divider()

    st.caption(
        "👤 Human operators remain responsible "
        "for final operational decisions."
    )


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns(
    [5, 1]
)

with header_left:

    st.title("🧠 ShiftMind")

    st.caption(
        "AI-powered institutional memory for "
        "24/7 operational teams"
    )

with header_right:

    if services_ready:

        st.success(
            "🟢 System Online"
        )

    else:

        st.error(
            "🔴 System Offline"
        )


st.divider()


# ============================================================
# HERO
# ============================================================

st.header(
    "🚀 Turn previous shift experience "
    "into better decisions."
)

st.write(
    """
    ShiftMind remembers operational history,
    recalls similar incidents, identifies what
    worked and what failed, and creates a practical
    handover brief for the current shift.
    """
)

st.info(
    "🔄 Recall → Reason → Resolve → Retain"
)


# ============================================================
# KPI
# ============================================================

st.subheader(
    "📊 Operational Overview"
)

k1, k2, k3, k4 = st.columns(4)

with k1:

    st.metric(
        "🏭 Current Asset",
        st.session_state.machine or "—",
    )

with k2:

    st.metric(
        "🧠 Memories Recalled",
        len(st.session_state.memories),
    )

with k3:

    st.metric(
        "🤖 AI Analysis",
        "Complete"
        if st.session_state.answer
        else "Ready",
    )

with k4:

    st.metric(
        "🔄 Learning Loop",
        "Recorded"
        if st.session_state.saved
        else "Active",
    )


st.divider()


# ============================================================
# MAIN TABS
# ============================================================

tab_analyze, tab_memory, tab_outcome = st.tabs(
    [
        "🔎 Analyze Incident",
        "🧠 Institutional Memory",
        "💾 Record Outcome",
    ]
)


# ============================================================
# ANALYZE INCIDENT
# ============================================================

with tab_analyze:

    st.subheader(
        "🛠️ Current Shift"
    )

    st.caption(
        "Describe the operational problem currently "
        "being handled."
    )

    # --------------------------------------------------------
    # INPUTS
    # --------------------------------------------------------

    machine = st.text_input(
        "🏭 Machine / Asset",
        value=st.session_state.machine,
        placeholder="Example: M-204",
    )

    problem = st.text_area(
        "⚠️ Current Problem",
        value=st.session_state.problem,
        height=140,
        placeholder=(
            "Example: Machine M-204 is showing "
            "E17 sensor error again."
        ),
    )

    st.session_state.machine = machine
    st.session_state.problem = problem

    st.write("")

    # --------------------------------------------------------
    # QUICK SCENARIOS
    # --------------------------------------------------------

    st.markdown(
        "### ⚡ Quick Scenarios"
    )

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

    st.write("")

    # --------------------------------------------------------
    # ANALYZE BUTTON
    # --------------------------------------------------------

    analyze_button = st.button(
        "🔎 Recall & Analyze",
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

            # --------------------------------------------
            # RECALL
            # --------------------------------------------

            with st.spinner(
                "🧠 Searching Hindsight memory..."
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

            # --------------------------------------------
            # REASON
            # --------------------------------------------

            if st.session_state.analyzed:

                with st.spinner(
                    "🤖 Analyzing historical experience..."
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

    # ========================================================
    # AI RESULT
    # ========================================================

    st.divider()

    st.subheader(
        "📋 Shift Handover Brief"
    )

    st.caption(
        "Decision support built from historical "
        "operational memory."
    )

    if st.session_state.answer:

        st.markdown(
            st.session_state.answer
        )

        st.divider()

        if st.session_state.memories:

            st.success(
                "🧠 Hindsight contributed "
                f"{len(st.session_state.memories)} "
                "relevant historical memory item(s)."
            )

        else:

            st.warning(
                "⚠️ No relevant historical memories "
                "were found."
            )

        st.markdown(
            "### 🔍 Historical Pattern Signal"
        )

        if st.session_state.memories:

            st.info(
                """
                Historical evidence was found for
                this incident.

                Review the recalled memories before
                deciding what action to take.

                ShiftMind does not assume a pattern
                unless the historical evidence supports it.
                """
            )

        else:

            st.info(
                "No historical pattern can be established "
                "from the available memory."
            )

        st.markdown(
            "### 👤 Human Decision Required"
        )

        st.warning(
            """
            ShiftMind provides decision support,
            not autonomous control.

            Follow approved procedures and use
            professional judgment before taking
            operational action.
            """
        )

    else:

        st.info(
            "💡 Enter an incident above and click "
            "**Recall & Analyze** to generate the "
            "handover brief."
        )


# ============================================================
# INSTITUTIONAL MEMORY
# ============================================================

with tab_memory:

    st.subheader(
        "🧠 Institutional Memory"
    )

    st.caption(
        "Historical operational experience retrieved "
        "from Hindsight."
    )

    if st.session_state.memories:

        st.success(
            f"Found {len(st.session_state.memories)} "
            "relevant historical memory item(s)."
        )

        for index, memory_text in enumerate(
            st.session_state.memories,
            1,
        ):

            with st.expander(
                f"🧠 Memory {index}",
                expanded=True,
            ):

                st.write(
                    memory_text
                )

        st.info(
            "💡 These memories were supplied to the "
            "AI reasoning layer so previous experience "
            "could influence the current brief."
        )

    else:

        st.info(
            "📭 No memories are currently displayed. "
            "Analyze an incident first."
        )


# ============================================================
# RECORD OUTCOME
# ============================================================

with tab_outcome:

    st.subheader(
        "💾 Record the Outcome"
    )

    st.caption(
        "Close the learning loop by recording "
        "what happened after the action."
    )

    if not st.session_state.analyzed:

        st.info(
            "First analyze an incident, then return "
            "here to record the outcome."
        )

    else:

        action_taken = st.text_input(
            "🛠️ Action Taken",
            placeholder=(
                "Example: Sensor cable was inspected "
                "and replaced."
            ),
        )

        outcome = st.selectbox(
            "📌 Outcome",
            [
                "Resolved",
                "Partially resolved",
                "Not resolved",
                "Escalated to maintenance",
            ],
        )

        st.write("")

        save_button = st.button(
            "💾 Save Outcome to Hindsight",
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
                        "💾 Saving outcome to Hindsight..."
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
                        "✅ Outcome successfully saved "
                        "to Hindsight."
                    )

                    st.info(
                        "🧠 The new learning may take "
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
                "🎯 Learning loop complete: "
                "Recall → Reason → Resolve → Retain"
            )

            st.info(
                "The outcome has been stored in Hindsight "
                "for future incident analysis."
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🧠 ShiftMind • AI Institutional Memory "
    "for Operational Teams"
)

st.caption(
    "🔄 Recall → Reason → Resolve → Retain"
)

st.caption(
    "👤 AI provides decision support. "
    "Human operators remain responsible for final decisions."
)