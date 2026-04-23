import json
from pathlib import Path
from typing import Any

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[2]
CONTEXT_PATH = ROOT / "config" / "llm_context.json"
MODEL = "gpt-4o-mini"


def load_context() -> dict[str, Any]:
    with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(context: dict[str, Any], user_input: str) -> str:
    context_json = json.dumps(context, ensure_ascii=False, indent=2)

    return (
        "ROLE:\n"
        "You are a planner for real estate accounting queries.\n\n"

        "CONTEXT:\n"
        f"{context_json}\n\n"

        "TASK:\n"
        "Extract the following fields:\n"
        "- intent (zahlung, soll, info, check)\n"
        "- operation (summe, liste, check or null)\n"
        "- rolle (mieter, partner, unknown)\n"
        "- name (person or company or null)\n"
        "- jahr (integer year or null)\n"
        "- konto_zweck (string or null)\n\n"

        "RULES:\n"
        "- DO NOT return any text except JSON\n"
        "- DO NOT include explanations\n"
        "- DO NOT use account numbers\n"
        "- DO NOT call tools\n"
        "- Missing values must be null\n"
        "- Output must be a valid JSON object\n\n"

        "EXAMPLES:\n"

        "Question: was hat flury 2025 an miete bezahlt\n"
        "Answer:\n"
        "{\n"
        '  "intent": "zahlung",\n'
        '  "operation": "summe",\n'
        '  "rolle": "mieter",\n'
        '  "name": "flury",\n'
        '  "jahr": 2025,\n'
        '  "konto_zweck": "mieteinnahmen wohnung"\n'
        "}\n\n"

        "Question: wie viel nebenkosten hat piehl 2024 bezahlt\n"
        "Answer:\n"
        "{\n"
        '  "intent": "zahlung",\n'
        '  "operation": "summe",\n'
        '  "rolle": "mieter",\n'
        '  "name": "piehl",\n'
        '  "jahr": 2024,\n'
        '  "konto_zweck": "betriebskostenvorauszahlung"\n'
        "}\n\n"

        "Question: habe ich swm 2025 bezahlt\n"
        "Answer:\n"
        "{\n"
        '  "intent": "zahlung",\n'
        '  "operation": "check",\n'
        '  "rolle": "partner",\n'
        '  "name": "swm",\n'
        '  "jahr": 2025,\n'
        '  "konto_zweck": null\n'
        "}\n\n"

        "Question: was habe ich 2025 an heizkosten bezahlt\n"
        "Answer:\n"
        "{\n"
        '  "intent": "zahlung",\n'
        '  "operation": "summe",\n'
        '  "rolle": "unknown",\n'
        '  "name": null,\n'
        '  "jahr": 2025,\n'
        '  "konto_zweck": "heizkosten"\n'
        "}\n\n"

        "USER INPUT:\n"
        f"{user_input}"
    )


def create_plan(user_input: str) -> dict[str, Any]:
    context = load_context()
    prompt = build_prompt(context, user_input)

    client = OpenAI()
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    response_text = response.choices[0].message.content or "{}"
    print("PLAN RAW:", response_text)

    try:
        return json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON from LLM: " + response_text) from exc


def parse_query(user_input: str) -> dict[str, Any]:
    return create_plan(user_input)
