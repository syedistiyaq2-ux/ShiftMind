# 🧠 ShiftMind

### Every shift leaves knowledge. ShiftMind makes sure the next shift gets it.

ShiftMind is an AI-powered institutional handover agent for 24/7 operations.

It helps teams preserve knowledge between shifts by remembering previous incidents, finding similar situations, reasoning from historical outcomes, and learning from newly recorded results.

---

## 💡 The Problem

In 24/7 operations, important knowledge is often lost when one shift ends and another begins.

Operators may repeatedly face the same problem but not know:

- What happened during previous shifts
- Which troubleshooting attempts failed
- Which actions successfully resolved the issue
- What the next shift should check first

Traditional AI assistants mainly remember conversations.

**ShiftMind remembers what the organization learned.**

---

## 🚀 How ShiftMind Works

ShiftMind follows a continuous learning loop:

**Recall → Reason → Resolve → Retain**

### 1. 🧠 Recall

Hindsight searches organizational memory for relevant previous incidents.

### 2. 🤖 Reason

The AI analyzes the current problem together with historical experience.

### 3. 🛠️ Resolve

The current operator receives a practical next-shift brief based on previous outcomes.

### 4. 🔄 Retain

The operator records what happened and whether the action resolved the problem.

That new experience is stored in Hindsight so future shifts can learn from it.

---

## 🔥 Example

Machine **M-204** repeatedly reports an **E17 sensor error**.

Previous shift records show:

- Restarting alone did not reliably solve the problem.
- Sensor cleaning did not resolve some incidents.
- Connector re-seating resolved one incident.
- Sensor cable replacement repeatedly appeared in successful resolutions.

When another shift reports:

> "M-204 is showing E17 sensor error again."

ShiftMind recalls those previous incidents and highlights the recurring pattern instead of treating the problem as completely new.

After the operator takes action, the result can be recorded back into memory.

This creates a continuous organizational learning loop.

---

## 🧠 Why Hindsight Matters

Hindsight is the memory layer of ShiftMind.

It allows the agent to:

- Store operational experiences
- Recall relevant historical incidents
- Connect the current problem with previous experience
- Learn from newly recorded outcomes

The key idea is:

> **The agent does not just remember what was said. It remembers what the organization learned.**

---

## 🏗️ Architecture

```text
                 Current Shift
                      │
                      ▼
              ┌───────────────┐
              │   ShiftMind   │
              │   Streamlit   │
              └───────┬───────┘
                      │
                      ▼
             ┌─────────────────┐
             │    Hindsight    │
             │ Organizational  │
             │     Memory      │
             └────────┬────────┘
                      │
                Relevant memories
                      │
                      ▼
                ┌───────────┐
                │   Groq    │
                │    LLM     │
                └─────┬─────┘
                      │
                      ▼
              Next Shift Brief
                      │
                      ▼
               Human Operator
                      │
                      ▼
                Record Outcome
                      │
                      ▼
             ┌─────────────────┐
             │    Hindsight    │
             │  learns result  │
             └─────────────────┘