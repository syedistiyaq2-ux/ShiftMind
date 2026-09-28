import os
import sys

try:
    from dotenv import load_dotenv
    from hindsight_client import Hindsight
except ImportError as e:
    print(f"❌ Missing package: {e.name}")
    print("Fix: pip install -U hindsight-client python-dotenv")
    sys.exit(1)


def clean(value):
    return (value or "").strip().strip('"').strip("'")


load_dotenv()

HINDSIGHT_API_URL = clean(os.getenv("HINDSIGHT_API_URL")).rstrip("/")
HINDSIGHT_API_KEY = clean(os.getenv("HINDSIGHT_API_KEY"))
BANK_ID = clean(os.getenv("HINDSIGHT_BANK_ID")) or "shiftmind-demo"


DEMO_INCIDENTS = [
    {
        "date": "2026-09-20", "shift": "Night", "machine": "M-204",
        "problem": "E17 sensor error",
        "attempted": "Machine restart and sensor cleaning",
        "action": "Sensor cable replacement",
        "outcome": "Resolved",
    },
    {
        "date": "2026-09-22", "shift": "Day", "machine": "M-204",
        "problem": "E17 sensor error",
        "attempted": "Restarted machine; error returned",
        "action": "Inspected connector and re-seated it",
        "outcome": "Resolved",
    },
    {
        "date": "2026-09-24", "shift": "Night", "machine": "M-204",
        "problem": "E17 sensor error",
        "attempted": "Sensor cleaning did not clear the error",
        "action": "Found damaged cable and replaced it",
        "outcome": "Resolved",
    },
    {
        "date": "2026-09-21", "shift": "Day", "machine": "C-12",
        "problem": "Repeated conveyor stoppage",
        "attempted": "Restarted conveyor",
        "action": "Inspected proximity sensor and corrected its position",
        "outcome": "Resolved",
    },
    {
        "date": "2026-09-23", "shift": "Night", "machine": "C-12",
        "problem": "Conveyor stopped unexpectedly",
        "attempted": "Restarted conveyor",
        "action": "Removed material buildup and checked sensor alignment",
        "outcome": "Resolved",
    },
    {
        "date": "2026-09-25", "shift": "Day", "machine": "F-07",
        "problem": "Hydraulic pressure warning",
        "attempted": "Restarted equipment",
        "action": "Inspection found low fluid level; corrected according to site procedure",
        "outcome": "Resolved",
    },
    {
        "date": "2026-09-26", "shift": "Night", "machine": "F-07",
        "problem": "Hydraulic pressure dropping",
        "attempted": "Pressure returned briefly after restart",
        "action": "Inspection identified a hose leak; maintenance replaced the hose",
        "outcome": "Resolved",
    },
    {
        "date": "2026-09-27", "shift": "Day", "machine": "P-11",
        "problem": "Label printer repeatedly jamming",
        "attempted": "Cleaning did not permanently solve the issue",
        "action": "Worn roller was replaced",
        "outcome": "Resolved",
    },
    {
        "date": "2026-09-28", "shift": "Night", "machine": "D-03",
        "problem": "Barcode scanner intermittently failing",
        "attempted": "Restarted scanner",
        "action": "Scanner lens was cleaned and alignment was checked",
        "outcome": "Resolved",
    },
]


def build_content(incident):
    return (
        "Warehouse shift incident.\n\n"
        f"Date: {incident['date']}\n"
        f"Shift: {incident['shift']}\n"
        f"Machine: {incident['machine']}\n"
        f"Problem: {incident['problem']}\n\n"
        f"What was attempted: {incident['attempted']}\n"
        f"What action worked: {incident['action']}\n"
        f"Outcome: {incident['outcome']}"
    )


def seed_demo_data():
    missing = [
        name
        for name, value in [
            ("HINDSIGHT_API_URL", HINDSIGHT_API_URL),
            ("HINDSIGHT_API_KEY", HINDSIGHT_API_KEY),
        ]
        if not value
    ]
    if missing:
        print(f"❌ Missing in .env: {', '.join(missing)}")
        sys.exit(1)

    if not HINDSIGHT_API_URL.startswith("http"):
        print("❌ HINDSIGHT_API_URL must start with http:// or https://")
        sys.exit(1)

    # Running this twice stores every incident twice, so ask first.
    if sys.stdin.isatty():
        answer = input(
            f"This will add {len(DEMO_INCIDENTS)} incidents to bank '{BANK_ID}'.\n"
            "If you already ran it, they will be duplicated. Continue? (y/n): "
        ).strip().lower()
        if answer not in ("y", "yes"):
            print("Cancelled.")
            return

    print("🔌 Connecting to Hindsight...")
    try:
        memory = Hindsight(base_url=HINDSIGHT_API_URL, api_key=HINDSIGHT_API_KEY)
    except Exception as e:
        print(f"❌ Could not create client: {e}")
        sys.exit(1)

    stored, failed = 0, 0
    print(f"📦 Loading {len(DEMO_INCIDENTS)} historical incidents...\n")

    for incident in DEMO_INCIDENTS:
        label = f"{incident['machine']} - {incident['problem']} ({incident['date']})"
        try:
            memory.retain(
                bank_id=BANK_ID,
                content=build_content(incident),
                context=(
                    "Historical warehouse shift incident used by ShiftMind "
                    "for operational handover and learning."
                ),
            )
            stored += 1
            print(f"✅ Stored: {label}")
        except Exception as e:
            failed += 1
            msg = str(e)
            print(f"❌ Failed: {label}")
            if "401" in msg or "403" in msg or "unauthorized" in msg.lower():
                print("   Hindsight rejected your API key. Check HINDSIGHT_API_KEY in .env.")
                break
            print(f"   {msg[:200]}")

    print(f"\n🧠 Bank: {BANK_ID}")
    print(f"✅ Stored: {stored}   ❌ Failed: {failed}")
    if stored:
        print("⏳ Give Hindsight a minute to index before searching.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    try:
        seed_demo_data()
    except KeyboardInterrupt:
        print("\nCancelled.")