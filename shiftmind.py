import os
import sys
import time

from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight


# =========================
# 1. LOAD SETTINGS
# =========================

load_dotenv()


def clean(value):
    return (value or "").strip().strip('"').strip("'")


GROQ_API_KEY = clean(os.getenv("GROQ_API_KEY"))
HINDSIGHT_API_URL = clean(os.getenv("HINDSIGHT_API_URL")).rstrip("/")
HINDSIGHT_API_KEY = clean(os.getenv("HINDSIGHT_API_KEY"))
BANK_ID = clean(os.getenv("HINDSIGHT_BANK_ID")) or "shiftmind-demo"

GROQ_MODEL = clean(os.getenv("GROQ_MODEL")) or "openai/gpt-oss-120b"


# Check settings
missing = []

if not GROQ_API_KEY:
    missing.append("GROQ_API_KEY")

if not HINDSIGHT_API_URL:
    missing.append("HINDSIGHT_API_URL")

if not HINDSIGHT_API_KEY:
    missing.append("HINDSIGHT_API_KEY")

if missing:
    print("❌ Missing in .env:")
    print(", ".join(missing))
    sys.exit(1)


# =========================
# 2. CONNECT TO SERVICES
# =========================

print("🔌 Connecting to Groq...")
groq_client = Groq(api_key=GROQ_API_KEY)
print("✅ Groq connected.")

print("🔌 Connecting to Hindsight...")

try:
    memory = Hindsight(
        base_url=HINDSIGHT_API_URL,
        api_key=HINDSIGHT_API_KEY
    )

    print("✅ Hindsight connected.")

except Exception as e:
    print("❌ Could not connect to Hindsight.")
    print(str(e))
    sys.exit(1)


# =========================
# 3. RETAIN MEMORY
# =========================

def store_incident(machine, error, tried, resolution):

    incident = f"""
Warehouse shift incident.

Machine: {machine}

Error: {error}

What was tried:
{tried}

What finally resolved the problem:
{resolution}

Lesson for future shifts:
Remember which actions failed and which action successfully resolved this problem.
"""

    try:

        memory.retain(
            bank_id=BANK_ID,
            content=incident,
            context="Warehouse shift incident"
        )

        return True

    except Exception as e:

        print("❌ Failed to store memory:")
        print(str(e))

        return False


# =========================
# 4. RECALL MEMORY
# =========================

def find_similar(problem):

    try:

        response = memory.recall(
            bank_id=BANK_ID,
            query=problem
        )

        results = getattr(response, "results", None) or []

        memories = []

        for result in results:

            text = getattr(result, "text", None)

            if text:
                memories.append(text)

            else:
                memories.append(str(result))

        return memories

    except Exception as e:

        print("❌ Failed to recall memory:")
        print(str(e))

        return []


# =========================
# 5. GROQ REASONING
# =========================

def suggest_fix(problem, memories):

    if memories:

        memory_text = "\n\n".join(
            f"MEMORY {i + 1}:\n{memory}"
            for i, memory in enumerate(memories)
        )

    else:

        memory_text = "No relevant previous incidents were found."


    prompt = f"""
You are ShiftMind, an AI assistant for warehouse shift operations.

Your job is to help the current shift learn from previous shifts.

Use the historical memories below.

IMPORTANT:
- Prefer solutions that previously worked.
- Clearly mention actions that previously failed.
- Do not pretend the AI is certain if the memories are insufficient.
- The human operator makes the final operational decision.
- Keep the answer practical and easy to understand.

HISTORICAL MEMORY:

{memory_text}


CURRENT SHIFT PROBLEM:

{problem}


Give the operator:

1. What happened before
2. What failed before
3. What worked before
4. Recommended next step
5. A short safety note that the operator should verify the machine according to their normal procedure
"""


    try:

        response = groq_client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": "You are ShiftMind, a warehouse operations memory assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.2,

            timeout=30
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"❌ Groq error: {str(e)}"


# =========================
# 6. DEMO INCIDENT
# =========================

def load_demo():

    print("\n🧠 Storing historical warehouse incident...")

    success = store_incident(

        machine="M-204",

        error="E17 sensor error",

        tried=(
            "Restarted the machine, but E17 returned. "
            "Cleaned the sensor, but E17 returned again."
        ),

        resolution=(
            "Replaced the sensor cable. "
            "The E17 error was resolved."
        )
    )


    if success:

        print("\n✅ Historical incident stored in Hindsight.")

        print("\nThe memory contains:")

        print("Machine: M-204")
        print("Problem: E17 sensor error")
        print("Restart: FAILED")
        print("Sensor cleaning: FAILED")
        print("Sensor cable replacement: WORKED")


# =========================
# 7. ASK SHIFT MIND
# =========================

def ask_shiftmind():

    problem = input(
        "\nDescribe the current shift problem:\n> "
    ).strip()


    if not problem:

        print("⚠️ Please enter a problem.")

        return


    print("\n🔎 Searching organizational memory...")

    memories = find_similar(problem)


    print(
        f"📚 Found {len(memories)} relevant memories."
    )


    if memories:

        print("\n🧠 Relevant past experience:")

        for i, memory_text in enumerate(memories, 1):

            print(f"\n--- Memory {i} ---")
            print(memory_text)


    print("\n🤖 ShiftMind is reasoning...")

    answer = suggest_fix(
        problem,
        memories
    )


    print("\n================================")
    print("        SHIFTMIND ADVICE")
    print("================================\n")

    print(answer)

    print("\n================================")


# =========================
# 8. MANUAL INCIDENT
# =========================

def add_incident():

    print("\n=== Add Resolved Incident ===")

    machine = input(
        "Machine ID: "
    ).strip()

    error = input(
        "Error/problem: "
    ).strip()

    tried = input(
        "What was tried: "
    ).strip()

    resolution = input(
        "What finally fixed it: "
    ).strip()


    if not machine or not error or not resolution:

        print(
            "⚠️ Machine, error and resolution are required."
        )

        return


    if store_incident(
        machine,
        error,
        tried or "Not recorded",
        resolution
    ):

        print(
            "\n✅ Incident successfully saved to organizational memory."
        )


# =========================
# 9. MAIN MENU
# =========================

def main():

    print("\n")
    print("========================================")
    print("          🧠 SHIFTMIND")
    print("   AI Institutional Handover Agent")
    print("========================================")

    print("\nHindsight memory is connected.")
    print("Bank:", BANK_ID)


    while True:

        print("\n")
        print("1. Load demo incident")
        print("2. Ask ShiftMind about a problem")
        print("3. Add a resolved incident")
        print("4. Exit")


        choice = input(
            "\nChoose 1-4: "
        ).strip()


        if choice == "1":

            load_demo()


        elif choice == "2":

            ask_shiftmind()


        elif choice == "3":

            add_incident()


        elif choice == "4":

            print("\nGoodbye 👋")
            break


        else:

            print(
                "⚠️ Please choose 1, 2, 3 or 4."
            )


# =========================
# START
# =========================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print("\n\nGoodbye 👋")