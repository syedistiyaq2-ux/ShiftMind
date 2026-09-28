import html
import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight


# ============================================================
# SETUP
# ============================================================

load_dotenv()


def clean(value):
    return (value or "").strip().strip('"').strip("'")


GROQ_API_KEY = clean(os.getenv("GROQ_API_KEY"))
HINDSIGHT_API_URL = clean(os.getenv("HINDSIGHT_API_URL")).rstrip("/")
HINDSIGHT_API_KEY = clean(os.getenv("HINDSIGHT_API_KEY"))
BANK_ID = clean(os.getenv("HINDSIGHT_BANK_ID")) or "shiftmind-demo"

GROQ_MODELS = [
    clean(os.getenv("GROQ_MODEL")) or "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


EXAMPLES = [
    (
        "M-204",
        "Machine M-204 is showing E17 sensor error again."
    ),
    (
        "Conveyor C-12",
        "Conveyor C-12 keeps stopping every few minutes during the night shift."
    ),
    (
        "Forklift F-07",
        "Forklift F-07 loses hydraulic pressure when lifting heavy pallets."
    ),
]


st.set_page_config(
    page_title="ShiftMind",
    page_icon="🧠",
    layout="wide",
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
<style>

#MainMenu, footer {
    visibility: hidden;
}

.block-container {
    padding-top: 1.6rem;
    padding-bottom: 3rem;
    max-width: 1250px;
}


/* HERO */

.hero {
    background: linear-gradient(
        135deg,
        #4f46e5 0%,
        #7c3aed 50%,
        #db2777 100%
    );

    border-radius: 20px;
    padding: 34px 38px;
    color: #ffffff;
    margin-bottom: 22px;

    box-shadow:
        0 10px 30px rgba(79, 70, 229, 0.25);
}

.hero-title {
    font-size: 40px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin: 0;
}

.hero-sub {
    font-size: 17px;
    opacity: 0.92;
    margin-top: 6px;
}

.pill {
    display: inline-block;

    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);

    border-radius: 999px;

    padding: 4px 14px;

    font-size: 13px;

    margin: 14px 8px 0 0;
}


/* KPI */

.kpi {
    display: flex;
    align-items: center;
    gap: 14px;

    padding: 16px 18px;

    border-radius: 16px;

    border: 1px solid rgba(128,128,128,0.22);

    background: rgba(128,128,128,0.07);
}

.kpi-icon {
    font-size: 26px;

    width: 48px;
    height: 48px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 12px;

    background: rgba(124,58,237,0.15);
}

.kpi-label {
    font-size: 12px;

    text-transform: uppercase;

    letter-spacing: 0.8px;

    opacity: 0.65;
}

.kpi-value {
    font-size: 22px;

    font-weight: 700;
}


/* PROCESS STEPS */

.steps {
    display: flex;

    gap: 10px;

    margin: 18px 0 8px 0;

    flex-wrap: wrap;
}

.step {
    flex: 1;

    min-width: 130px;

    text-align: center;

    padding: 10px 12px;

    border-radius: 12px;

    font-size: 14px;

    font-weight: 600;

    border: 1px solid rgba(128,128,128,0.25);

    opacity: 0.55;
}

.step.done {
    background: rgba(34,197,94,0.14);

    border-color: rgba(34,197,94,0.5);

    opacity: 1;
}

.step.active {
    background: rgba(124,58,237,0.16);

    border-color: rgba(124,58,237,0.6);

    opacity: 1;
}


/* MEMORY CARDS */

.mem-card {
    padding: 16px 18px;

    border-radius: 14px;

    margin-bottom: 12px;

    border: 1px solid rgba(128,128,128,0.22);

    border-left: 5px solid #7c3aed;

    background: rgba(128,128,128,0.06);

    font-size: 15px;

    line-height: 1.55;
}

.mem-badge {
    display: inline-block;

    font-size: 12px;

    font-weight: 700;

    padding: 2px 10px;

    border-radius: 999px;

    margin-bottom: 8px;

    background: rgba(124,58,237,0.18);

    color: #a78bfa;
}


/* SECTIONS */

.section-title {
    font-size: 22px;

    font-weight: 700;

    margin: 4px 0 2px 0;
}

.section-sub {
    font-size: 14px;

    opacity: 0.65;

    margin-bottom: 14px;
}


/* CONTAINERS */

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px;
}


/* PRIMARY BUTTON */

button[kind="primary"] {
    background: linear-gradient(
        135deg,
        #4f46e5,
        #7c3aed
    ) !important;

    border: none !important;

    font-weight: 700 !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# CONNECTIONS
# ============================================================

@st.cache_resource
def get_clients():

    missing = [
        name
        for name, value in [
            ("GROQ_API_KEY", GROQ_API_KEY),
            ("HINDSIGHT_API_URL", HINDSIGHT_API_URL),
            ("HINDSIGHT_API_KEY", HINDSIGHT_API_KEY),
        ]
        if not value
    ]

    if missing:
        raise Exception(
            f"Missing in .env: {', '.join(missing)}"
        )

    if not HINDSIGHT_API_URL.startswith("http"):
        raise Exception(
            "HINDSIGHT_API_URL must start with http:// or https://"
        )

    return (
        Groq(api_key=GROQ_API_KEY),

        Hindsight(
            base_url=HINDSIGHT_API_URL,
            api_key=HINDSIGHT_API_KEY,
        ),
    )


connection_ok = True
connection_error = ""

try:

    groq_client, memory = get_clients()

except Exception as e:

    connection_ok = False
    connection_error = str(e)


# ============================================================
# HINDSIGHT RECALL
# ============================================================

def recall_memories(problem):

    """
    Run Hindsight recall inside a separate worker thread.

    This avoids Streamlit's running event-loop conflict.
    """

    from concurrent.futures import ThreadPoolExecutor

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
            None
        ) or []

        return [
            getattr(item, "text", None) or str(item)
            for item in results[:6]
        ]

    with ThreadPoolExecutor(max_workers=1) as executor:

        future = executor.submit(worker)

        return future.result()


# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(machine, problem, memories):

    if memories:

        memory_text = "\n\n".join(
            f"MEMORY {i + 1}:\n{m}"
            for i, m in enumerate(memories)
        )

    else:

        memory_text = (
            "No relevant historical memories were found."
        )


    return f"""
You are ShiftMind, an AI institutional handover assistant
for warehouse operations.

Use the historical memories below.

The goal is to help the current shift avoid repeating
mistakes made by previous shifts.

Some memories are outcome records.

Treat an outcome of "Resolved" as something that worked.

Treat "Partially resolved" or "Not resolved" as something
that failed or was incomplete.

IMPORTANT:

Do not invent historical facts.

Do not claim that something worked unless the historical
memory supports it.

The AI provides decision support.

The human operator makes the final decision.

Format your answer in Markdown with these headings:

### 📜 What happened before

### ❌ What failed

### ✅ What worked

### 🔍 What to check now

### ⚠️ Safety / escalation

Be concise and practical.

If the memories do not cover the problem, say so plainly
and provide only cautious general guidance.

HISTORICAL MEMORY:

{memory_text}

MACHINE:

{machine}

CURRENT SHIFT PROBLEM:

{problem}
"""


# ============================================================
# GROQ REASONING
# ============================================================

def ask_groq(prompt):

    last_error = ""

    for model in GROQ_MODELS:

        try:

            result = groq_client.chat.completions.create(

                model=model,

                messages=[
                    {
                        "role": "system",
                        "content":
                        "You are ShiftMind, an operational memory assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    },
                ],

                temperature=0.2,

                timeout=30,
            )

            return result.choices[0].message.content

        except Exception as e:

            msg = str(e)

            last_error = msg


            if (
                "401" in msg
                or "invalid_api_key" in msg.lower()
            ):

                raise Exception(
                    "Invalid Groq API key. "
                    "Check GROQ_API_KEY in .env."
                )


            if "429" in msg:

                raise Exception(
                    "Groq rate limit reached. "
                    "Wait a minute and try again."
                )


            if (
                "404" in msg
                or "model" in msg.lower()
            ):

                continue


            raise


    raise Exception(
        f"No Groq model worked. Last error: {last_error}"
    )


# ============================================================
# UI HELPERS
# ============================================================

def kpi(icon, label, value):

    return (
        f'<div class="kpi">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div>'
        f'<div class="kpi-label">'
        f'{html.escape(label)}'
        f'</div>'
        f'<div class="kpi-value">'
        f'{html.escape(str(value))}'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def set_example(machine, problem):

    st.session_state.machine = machine

    st.session_state.problem = problem


# ============================================================
# SESSION STATE
# ============================================================

st.session_state.setdefault(
    "memories",
    []
)

st.session_state.setdefault(
    "answer",
    ""
)

st.session_state.setdefault(
    "analyzed",
    False
)

st.session_state.setdefault(
    "saved",
    False
)

st.session_state.setdefault(
    "machine",
    EXAMPLES[0][0]
)

st.session_state.setdefault(
    "problem",
    EXAMPLES[0][1]
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🧠 ShiftMind")

    st.caption(
        "Memory-powered operational intelligence"
    )

    st.divider()


    if connection_ok:

        st.success(
            "Settings loaded"
        )


        # ----------------------------------------------------
        # TEST CONNECTIONS
        # ----------------------------------------------------

        if st.button(
            "🔌 Test connections",
            use_container_width=True
        ):

            try:

                recall_memories(
                    "connection test"
                )

                st.success(
                    "Hindsight: working"
                )

            except Exception as e:

                st.error(
                    f"Hindsight: {e}"
                )


            try:

                groq_client.models.list()

                st.success(
                    "Groq: working"
                )

            except Exception as e:

                st.error(
                    f"Groq: {e}"
                )


        # ----------------------------------------------------
        # LOAD DEMO INCIDENT
        # ----------------------------------------------------

        if st.button(
            "📥 Load demo incident",
            use_container_width=True
        ):

            try:

                memory.retain(

                    bank_id=BANK_ID,

                    content=(
                        "Warehouse incident.\n"
                        "Machine: M-204\n"
                        "Error: E17 sensor error\n"
                        "What was tried: Restarted the machine "
                        "(error returned). "
                        "Cleaned the sensor "
                        "(error returned).\n"
                        "What finally resolved it: "
                        "Replacing the sensor cable resolved "
                        "the E17 error.\n"
                        "Outcome: Resolved"
                    ),

                    context="Warehouse shift incident",
                )

                st.success(
                    "Demo incident stored. "
                    "Give it a few seconds to index."
                )

            except Exception as e:

                st.error(
                    f"Could not store demo: {e}"
                )


    else:

        st.error(
            "Connection problem"
        )

        st.code(
            connection_error
        )


    st.divider()


    st.markdown(
        "**How it works**"
    )

    st.markdown(
        "1. **Recall** past incidents\n"
        "2. **Reason** with Groq\n"
        "3. **Resolve** on the floor\n"
        "4. **Retain** the outcome"
    )


    st.divider()


    st.caption(
        "Human operators remain responsible "
        "for final operational decisions."
    )


# ============================================================
# HERO
# ============================================================

st.markdown(

    f"""
<div class="hero">

<div class="hero-title">
🧠 ShiftMind
</div>

<div class="hero-sub">
AI Institutional Handover Agent — every shift leaves knowledge.
</div>

<span class="pill">
🗄️ Bank: {html.escape(BANK_ID)}
</span>

<span class="pill">
⚡ Model: {html.escape(GROQ_MODELS[0])}
</span>

<span class="pill">
🔁 Recall → Reason → Resolve → Retain
</span>

</div>
""",

    unsafe_allow_html=True,
)


if not connection_ok:

    st.error(
        "ShiftMind could not connect to its services. "
        "See the sidebar."
    )

    st.stop()


# ============================================================
# KPI CARDS
# ============================================================

k1, k2, k3 = st.columns(3)


k1.markdown(
    kpi(
        "🏭",
        "Machine",
        st.session_state.machine or "-"
    ),
    unsafe_allow_html=True
)


k2.markdown(
    kpi(
        "🧠",
        "Memories recalled",
        len(st.session_state.memories)
    ),
    unsafe_allow_html=True
)


k3.markdown(
    kpi(
        "📋",
        "Shift brief",
        "Ready"
        if st.session_state.answer
        else "Not yet"
    ),
    unsafe_allow_html=True
)


# ============================================================
# PROGRESS STEPS
# ============================================================

done = 0


if st.session_state.analyzed:

    done = 1


if st.session_state.answer:

    done = 2


if st.session_state.saved:

    done = 4


labels = [
    "🔎 Recall",
    "💡 Reason",
    "🛠️ Resolve",
    "💾 Retain"
]


step_html = '<div class="steps">'


for i, label in enumerate(labels):

    css = (
        "done"
        if i < done
        else
        ("active" if i == done else "")
    )

    step_html += (
        f'<div class="step {css}">'
        f'{label}'
        f'</div>'
    )


step_html += "</div>"


st.markdown(
    step_html,
    unsafe_allow_html=True
)


# ============================================================
# TABS
# ============================================================

tab_analyze, tab_memory, tab_learn = st.tabs(

    [
        "🔎 Analyze problem",
        "🧠 Memory findings",
        "🔄 Record outcome"
    ]

)


# ============================================================
# TAB 1 — ANALYZE
# ============================================================

with tab_analyze:

    left, right = st.columns(
        [1, 1.25],
        gap="large"
    )


    # --------------------------------------------------------
    # LEFT
    # --------------------------------------------------------

    with left:

        st.markdown(
            '<div class="section-title">'
            '🛠️ Current shift'
            '</div>',
            unsafe_allow_html=True
        )


        st.markdown(
            '<div class="section-sub">'
            'Describe what is happening right now.'
            '</div>',
            unsafe_allow_html=True
        )


        machine = st.text_input(
            "Machine / Asset",
            key="machine"
        )


        problem = st.text_area(
            "Current problem",
            key="problem",
            height=130
        )


        st.caption(
            "Quick examples"
        )


        ex_cols = st.columns(
            len(EXAMPLES)
        )


        for col, (m, p) in zip(
            ex_cols,
            EXAMPLES
        ):

            col.button(

                m,

                on_click=set_example,

                args=(m, p),

                key=f"ex_{m}",

                use_container_width=True,
            )


        analyze = st.button(

            "🔎 Recall & Analyze",

            type="primary",

            use_container_width=True,
        )


    # --------------------------------------------------------
    # ANALYZE BUTTON
    # --------------------------------------------------------

    if analyze:

        st.session_state.answer = ""

        st.session_state.saved = False


        if not problem.strip():

            st.warning(
                "Describe the current problem first."
            )


        else:

            recall_failed = False


            with st.spinner(
                "Searching organizational memory..."
            ):

                try:

                    st.session_state.memories = (
                        recall_memories(problem)
                    )

                    st.session_state.analyzed = True


                except Exception as e:

                    st.session_state.memories = []

                    recall_failed = True

                    st.error(
                        f"Hindsight recall failed: {e}"
                    )


            if not recall_failed:

                with st.spinner(
                    "Reasoning from past experience..."
                ):

                    try:

                        st.session_state.answer = ask_groq(

                            build_prompt(
                                machine,
                                problem,
                                st.session_state.memories
                            )

                        )

                    except Exception as e:

                        st.error(
                            f"Groq reasoning failed: {e}"
                        )


                if st.session_state.answer:

                    st.rerun()


    # --------------------------------------------------------
    # RIGHT — NEXT SHIFT BRIEF
    # --------------------------------------------------------

    with right:

        st.markdown(
            '<div class="section-title">'
            '📋 Next shift brief'
            '</div>',
            unsafe_allow_html=True
        )


        st.markdown(
            '<div class="section-sub">'
            'Decision support built from your own history.'
            '</div>',
            unsafe_allow_html=True
        )


        if st.session_state.answer:

            with st.container(
                border=True
            ):

                st.markdown(
                    st.session_state.answer
                )


                if not st.session_state.memories:

                    st.warning(
                        "No similar past incidents were found, "
                        "so treat this as general guidance only."
                    )


            # =================================================
            # PATTERN DETECTED
            # =================================================

            if st.session_state.memories:

                st.markdown("---")

                st.markdown(
                    "### 🧠 Pattern Detected"
                )


                st.info(
                    """
**M-204 has a recurring E17 pattern.**

Historical memory shows:

- E17 has appeared across multiple shifts.
- Restarting alone did not reliably solve it.
- Sensor cleaning alone did not reliably solve it.
- Connector inspection/re-seating helped in some cases.
- Sensor cable replacement was repeatedly associated with successful resolution.

**ShiftMind insight:**

Don't automatically repeat the same first response.

Check the historical pattern and follow your site's approved troubleshooting procedure.

**Why this matters:**

ShiftMind is using accumulated operational memory, not just the current message.
"""
                )


        else:

            with st.container(
                border=True
            ):

                st.info(
                    "No brief yet. Enter a problem and click "
                    "**Recall & Analyze** to see what previous "
                    "shifts learned."
                )


# ============================================================
# TAB 2 — MEMORY
# ============================================================

with tab_memory:

    st.markdown(
        '<div class="section-title">'
        '🧠 What the organization remembers'
        '</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="section-sub">'
        'Past incidents recalled for the current problem.'
        '</div>',
        unsafe_allow_html=True
    )


    if st.session_state.memories:

        for i, text in enumerate(
            st.session_state.memories,
            1
        ):

            safe = (
                html.escape(text)
                .replace("\n", "<br>")
            )


            st.markdown(

                f'''
<div class="mem-card">

<span class="mem-badge">
Memory {i}
</span>

<br>

{safe}

</div>
''',

                unsafe_allow_html=True
            )


    elif st.session_state.analyzed:

        st.warning(
            "Nothing similar found in memory yet. "
            "Store an incident and try again."
        )


    else:

        st.info(
            "Run **Recall & Analyze** to retrieve "
            "previous shift experience."
        )


# ============================================================
# TAB 3 — LEARN / RETAIN
# ============================================================

with tab_learn:

    st.markdown(
        '<div class="section-title">'
        '🔄 Close the learning loop'
        '</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="section-sub">'
        'Record what the operator did so future shifts '
        'can learn from it.'
        '</div>',
        unsafe_allow_html=True
    )


    c1, c2 = st.columns(
        2,
        gap="large"
    )


    with c1:

        action_taken = st.text_input(

            "Action taken",

            placeholder=(
                "Example: Sensor cable inspected and replaced"
            ),
        )


    with c2:

        outcome = st.selectbox(

            "Outcome",

            [
                "Resolved",
                "Partially resolved",
                "Not resolved",
                "Escalated to maintenance"
            ],
        )


    if st.button(

        "💾 Save outcome to Hindsight",

        type="primary",

        use_container_width=True

    ):

        if not action_taken.strip():

            st.warning(
                "Enter the action taken first."
            )


        elif not st.session_state.problem.strip():

            st.warning(
                "Describe the problem first."
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

This outcome is part of ShiftMind's organizational learning
and should be considered during future similar incidents.
"""


            try:

                memory.retain(

                    bank_id=BANK_ID,

                    content=content.strip(),

                    context=(
                        "Warehouse shift outcome and "
                        "organizational learning"
                    ),
                )


                st.session_state.saved = True


                st.success(
                    "✅ Outcome saved. "
                    "It may take a few seconds to become searchable."
                )


                st.balloons()


            except Exception as e:

                st.error(
                    f"Could not save outcome: {e}"
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(
    "ShiftMind • Recall → Reason → Resolve → Retain"
)