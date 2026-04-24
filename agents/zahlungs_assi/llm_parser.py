import json
from typing import Any

from openai import OpenAI

from tools.llm_context_loader import load_context


MODEL = "gpt-4o-mini"


def build_system_prompt(ctx: dict[str, Any]) -> str:
    p = ctx["planner"]
    return (
        "Domain:\n"
        f"{p.get('domain', '')}\n\n"
        "Konzepte:\n"
        f"{json.dumps(p.get('concepts', {}), ensure_ascii=False, indent=2)}\n\n"
        "Entitäten:\n"
        f"{json.dumps(p.get('core_entities', {}), ensure_ascii=False, indent=2)}\n\n"
        "Regeln:\n"
        f"{json.dumps(p.get('rules', []), ensure_ascii=False, indent=2)}\n\n"
        "Wichtige Felder:\n"
        f"{json.dumps(p.get('wichtige_felder', []), ensure_ascii=False, indent=2)}\n\n"
        "Gib IMMER ein JSON zurück mit:\n"
        "intent, name, rolle, richtung, konto_zweck\n\n"
        "TASK:\n"
        "Extract the following fields:\n"
        "- intent (always \"zahlung\")\n"
        "- operation (summe, liste, check)\n"
        "- rolle (mieter, partner, unknown)\n"
        "- richtung (einnahme, ausgabe, unknown)\n"
        "- name (person or company or null)\n"
        "- jahr (integer or null)\n"
        "- monat (1-12 or null)\n"
        "- von (YYYY-MM-DD or null)\n"
        "- bis (YYYY-MM-DD or null)\n"
        "- konto_zweck (miete, nebenkosten, betriebskostenabrechnung, kosten or null)\n"
        "- betrag (number or null)\n"
        "- betrag_min (number or null)\n"
        "- betrag_max (number or null)\n"
        "- buchungstext (string or null)\n"
        "- kostenstelle (string or null)\n\n"
        "RULES:\n"
        "- Always return JSON only\n"
        "- Do not include explanations or extra text\n"
        "- intent must always be \"zahlung\"\n"
        "- Missing fields must be null\n"
        "- Output must be a valid JSON object\n\n"
        "OPERATION:\n"
        "- \"wie viel\", \"summe\", \"gesamt\" -> operation = \"summe\"\n"
        "- \"zeige\", \"liste\", \"alle\" -> operation = \"liste\"\n"
        "- \"hat\", \"existiert\", \"gibt es\" -> operation = \"check\"\n"
        "- default -> operation = \"summe\"\n\n"
        "ROLLE:\n"
        "- tenant names -> rolle = \"mieter\"\n"
        "- companies/vendors -> rolle = \"partner\"\n"
        "- otherwise -> rolle = \"unknown\"\n\n"
        "RICHTUNG:\n"
        "- If rolle is \"mieter\" and question contains \"gezahlt\" or \"bezahlt\" -> richtung = \"einnahme\"\n"
        "- If rolle is \"partner\" and question contains \"gezahlt\" or \"überwiesen\" -> richtung = \"ausgabe\"\n"
        "- \"erhalten\", \"bekommen\", \"zurückerhalten\" -> richtung = \"einnahme\"\n"
        "- otherwise -> richtung = \"unknown\"\n\n"
        "TIME:\n"
        "- detect jahr (example: 2025)\n"
        "- detect monat (example: mai -> 5)\n"
        "- detect von/bis when explicit dates are present\n\n"
        "AMOUNT:\n"
        "- exact amount -> betrag\n"
        "- \"über\" or \">\" -> betrag_min\n"
        "- \"unter\" or \"<\" -> betrag_max\n\n"
        "TEXT:\n"
        "- unknown terms or quoted text -> buchungstext\n\n"
        "OBJECT:\n"
        "- detect identifiers (vol20, h3, addresses) -> kostenstelle\n\n"
        "EXAMPLES:\n"
        "Question: was hat flury 2025 an miete gezahlt\n"
        "Answer:\n"
        "{\n"
        "  \"intent\": \"zahlung\",\n"
        "  \"operation\": \"summe\",\n"
        "  \"rolle\": \"mieter\",\n"
        "  \"richtung\": \"einnahme\",\n"
        "  \"name\": \"flury\",\n"
        "  \"jahr\": 2025,\n"
        "  \"monat\": null,\n"
        "  \"von\": null,\n"
        "  \"bis\": null,\n"
        "  \"konto_zweck\": \"miete\",\n"
        "  \"betrag\": null,\n"
        "  \"betrag_min\": null,\n"
        "  \"betrag_max\": null,\n"
        "  \"buchungstext\": null,\n"
        "  \"kostenstelle\": null\n"
        "}\n\n"
        "Question: zeige alle zahlungen von hausmeister meier im mai 2025\n"
        "Answer:\n"
        "{\n"
        "  \"intent\": \"zahlung\",\n"
        "  \"operation\": \"liste\",\n"
        "  \"rolle\": \"partner\",\n"
        "  \"richtung\": \"unknown\",\n"
        "  \"name\": \"hausmeister meier\",\n"
        "  \"jahr\": 2025,\n"
        "  \"monat\": 5,\n"
        "  \"von\": null,\n"
        "  \"bis\": null,\n"
        "  \"konto_zweck\": null,\n"
        "  \"betrag\": null,\n"
        "  \"betrag_min\": null,\n"
        "  \"betrag_max\": null,\n"
        "  \"buchungstext\": null,\n"
        "  \"kostenstelle\": null\n"
        "}\n\n"
        "Question: gibt es eine zahlung über 500 für vol20 zwischen 2025-01-01 und 2025-03-31\n"
        "Answer:\n"
        "{\n"
        "  \"intent\": \"zahlung\",\n"
        "  \"operation\": \"check\",\n"
        "  \"rolle\": \"unknown\",\n"
        "  \"richtung\": \"unknown\",\n"
        "  \"name\": null,\n"
        "  \"jahr\": null,\n"
        "  \"monat\": null,\n"
        "  \"von\": \"2025-01-01\",\n"
        "  \"bis\": \"2025-03-31\",\n"
        "  \"konto_zweck\": null,\n"
        "  \"betrag\": null,\n"
        "  \"betrag_min\": 500,\n"
        "  \"betrag_max\": null,\n"
        "  \"buchungstext\": null,\n"
        "  \"kostenstelle\": \"vol20\"\n"
        "}\n\n"
        "Question: hat flury nebenkosten bezahlt\n"
        "Answer:\n"
        "{\n"
        "  \"intent\": \"zahlung\",\n"
        "  \"operation\": \"check\",\n"
        "  \"rolle\": \"mieter\",\n"
        "  \"richtung\": \"einnahme\",\n"
        "  \"name\": \"flury\",\n"
        "  \"jahr\": null,\n"
        "  \"monat\": null,\n"
        "  \"von\": null,\n"
        "  \"bis\": null,\n"
        "  \"konto_zweck\": \"nebenkosten\",\n"
        "  \"betrag\": null,\n"
        "  \"betrag_min\": null,\n"
        "  \"betrag_max\": null,\n"
        "  \"buchungstext\": null,\n"
        "  \"kostenstelle\": null\n"
        "}\n"
    )


def create_plan(user_input: str) -> dict[str, Any]:
    ctx = load_context()
    system_prompt = build_system_prompt(ctx)

    client = OpenAI()
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        response_format={"type": "json_object"},
    )

    response_text = response.choices[0].message.content or "{}"
    print("PLAN RAW:", response_text)

    try:
        plan = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON from LLM: " + response_text) from exc

    operation = plan.get("operation")
    if operation not in {"summe", "liste", "check"}:
        plan["operation"] = "summe"

    return plan


def parse_query(user_input: str) -> dict[str, Any]:
    return create_plan(user_input)
