import importlib
import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[2]
TOOL_REGISTRY_PATH = ROOT / "config" / "tool_registry.json"
DEFAULT_MODEL = "gpt-4o-mini"

TOOL_FUNCTION_MAP = {
    "mieter_mapper": "get_vertragids",
    "mieter_matcher": "match_mieter_to_vertrag",
    "konto_mapper": "map_konten",
    "zahlung_tool": "filter_zahlungen",
    "zeitraum_tool": "get_zeitraum",
    "objekt_mapper": "map_objekt_to_kostenstelle",
    "partner_mapper": "map_partner",
    "partner_matcher": "match_partner",
    "soll_ist_check": "check_soll_ist",
    "anomalie_check": "detect_anomalien",
    "fuzzy_matcher": "best_match",
    "output_formatter": "format_output",
}


TOOL_ARG_MAP = {
    "mieter_mapper": {"name": "mieter"},
}


class ToolExecutionError(RuntimeError):
    """Raised when a configured tool cannot be executed."""


class AutonomousZahlungsAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.client = OpenAI()
        self.tool_registry = self._load_tool_registry()

    def _load_tool_registry(self) -> dict[str, Any]:
        with open(TOOL_REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_system_prompt(self) -> str:
        registry_json = json.dumps(self.tool_registry, ensure_ascii=False, indent=2)
        return (
            "You are an autonomous real estate accounting agent.\n\n"
            "You have access to tools.\n\n"
            "Your job:\n"
            "1. Understand the request\n"
            "2. Identify missing information\n"
            "3. Select the correct tools\n"
            "4. Execute them step by step\n"
            "5. Combine results\n\n"
            "Rules:\n"
            "* NEVER guess data\n"
            "* ALWAYS use tools if data is missing\n"
            "* You may use multiple tools in sequence\n"
            "* Tool outputs must be reused in later steps\n"
            "* Do not stop after creating a plan\n"
            "* Always continue until final result is computed\n\n"
            "Return only valid JSON in this exact structure:\n"
            "{\n"
            '  "intent": "zahlung",\n'
            '  "plan": [{"tool": "tool_name", "args": {}}]\n'
            "}\n\n"
            "Use references like '<output from mieter_mapper>' or '<output from zeitraum_tool.von>' when needed.\n\n"
            "Tool registry:\n"
            f"{registry_json}"
        )

    def create_plan(self, query: str) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": query},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        plan = self._safe_json_load(content)
        if not isinstance(plan, dict) or "plan" not in plan:
            raise ValueError(f"LLM returned invalid plan: {content}")
        return plan

    @staticmethod
    def _safe_json_load(text: str) -> dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return {"intent": "zahlung", "plan": []}
            return json.loads(match.group())

    def _resolve_tool_callable(self, module: Any, tool_name: str):
        if tool_name == "zahlung_tool" and hasattr(module, "filter_zahlungen"):
            return module.filter_zahlungen

        mapped_function_name = TOOL_FUNCTION_MAP.get(tool_name)
        if mapped_function_name and hasattr(module, mapped_function_name):
            return getattr(module, mapped_function_name)

        if hasattr(module, tool_name):
            return getattr(module, tool_name)

        for fallback_name in ("run", "execute", "main"):
            if hasattr(module, fallback_name):
                return getattr(module, fallback_name)

        raise ToolExecutionError(f"No callable found for tool={tool_name} in module={module.__name__}")

    @staticmethod
    def resolve_args(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        resolved: dict[str, Any] = {}

        for key, value in (args or {}).items():
            if isinstance(value, str) and "output from" in value:
                lowered = value.lower()

                if "mieter_mapper" in lowered:
                    resolved[key] = context.get("mieter_mapper")
                elif "konto_mapper" in lowered:
                    resolved[key] = context.get("konto_mapper")
                elif "zeitraum_tool.von" in lowered:
                    resolved[key] = context.get("zeitraum_tool", {}).get("von")
                elif "zeitraum_tool.bis" in lowered:
                    resolved[key] = context.get("zeitraum_tool", {}).get("bis")
                else:
                    resolved[key] = None
                continue

            if isinstance(value, str) and value.startswith("$"):
                path = value[1:].split(".")
                cursor: Any = context
                for part in path:
                    if isinstance(cursor, dict) and part in cursor:
                        cursor = cursor[part]
                    else:
                        cursor = value
                        break
                resolved[key] = cursor
                continue

            resolved[key] = value

        return resolved

    def _remap_args_for_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        arg_map = TOOL_ARG_MAP.get(tool_name, {})
        if not arg_map:
            return args

        remapped: dict[str, Any] = {}
        for key, value in args.items():
            remapped[arg_map.get(key, key)] = value
        return remapped

    def call_tool(self, tool_name: str, args: dict[str, Any], context: dict[str, Any]) -> Any:
        module = importlib.import_module(f"tools.{tool_name}")
        resolved_args = self.resolve_args(args, context)
        resolved_args = self._remap_args_for_tool(tool_name, resolved_args)
        tool_callable = self._resolve_tool_callable(module, tool_name)
        return tool_callable(**resolved_args)

    def _extract_final_params(self, context: dict[str, Any]) -> dict[str, Any]:
        params: dict[str, Any] = {"vertragids": [], "konten": [], "von": None, "bis": None}

        mieter_result = context.get("mieter_mapper")
        if isinstance(mieter_result, list):
            params["vertragids"] = mieter_result
        elif isinstance(mieter_result, dict) and "vertragids" in mieter_result:
            params["vertragids"] = mieter_result["vertragids"]

        konto_result = context.get("konto_mapper")
        if isinstance(konto_result, list):
            params["konten"] = konto_result
        elif isinstance(konto_result, dict) and "konten" in konto_result:
            params["konten"] = konto_result["konten"]

        zeitraum_result = context.get("zeitraum_tool", {})
        if isinstance(zeitraum_result, dict):
            params["von"] = zeitraum_result.get("von")
            params["bis"] = zeitraum_result.get("bis")

        return params

    def execute_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        context: dict[str, Any] = {}
        steps = plan.get("plan", [])

        selected_tools = [step.get("tool") for step in steps]
        print(f"selected tools: {selected_tools}")

        for idx, step in enumerate(steps, start=1):
            tool_name = step["tool"]
            args = step.get("args", {})
            resolved_args = self.resolve_args(args, context)
            resolved_args = self._remap_args_for_tool(tool_name, resolved_args)
            print(f"step {idx}: execute {tool_name} with args={resolved_args}")
            result = self.call_tool(tool_name, args, context)
            context[tool_name] = result
            print(f"step {idx}: result {tool_name}={result}")

        final_params = self._extract_final_params(context)
        print(f"final params for zahlung_tool: {final_params}")

        buchungen = self.call_tool("zahlung_tool", final_params, context)
        summe_module = importlib.import_module("tools.zahlung_tool")
        summe = summe_module.summe_zahlungen(buchungen)

        context["zahlung_tool"] = {"buchungen": buchungen, "summe": summe}
        print(f"zahlung_tool result: {context['zahlung_tool']}")

        return {
            "summe": float(summe),
            "anzahl": len(buchungen),
            "daten": buchungen,
            "context": context,
        }

    def run(self, query: str) -> dict[str, Any]:
        plan = self.create_plan(query)
        return self.execute_plan(plan)


def parse_query(user_input: str) -> dict[str, Any]:
    """Compatibility wrapper: returns the LLM-generated execution plan."""
    agent = AutonomousZahlungsAgent()
    return agent.create_plan(user_input)
