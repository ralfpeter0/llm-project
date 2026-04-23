import importlib
import inspect
import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[2]
TOOL_REGISTRY_PATH = ROOT / "config" / "tool_registry.json"
DEFAULT_MODEL = "gpt-4o-mini"


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

    def _resolve_tool_callable(self, module: Any, args: dict[str, Any]):
        candidates = []
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_"):
                continue
            signature = inspect.signature(obj)
            params = signature.parameters
            required = {
                p_name
                for p_name, p in params.items()
                if p.default is inspect._empty and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
            }
            if set(args.keys()).issubset(set(params.keys())) or required.issubset(set(args.keys())):
                candidates.append((name, obj))

        if not candidates:
            for fallback_name in ("run", "execute", "main"):
                if hasattr(module, fallback_name) and inspect.isfunction(getattr(module, fallback_name)):
                    return getattr(module, fallback_name)
            raise ToolExecutionError(f"No callable matches args={args} in module={module.__name__}")

        candidates.sort(key=lambda x: len(inspect.signature(x[1]).parameters))
        return candidates[0][1]

    @staticmethod
    def _resolve_arg_value(value: Any, context: dict[str, Any]) -> Any:
        if not isinstance(value, str):
            return value

        if value.startswith("$"):
            path = value[1:].split(".")
            cursor: Any = context
            for part in path:
                if isinstance(cursor, dict) and part in cursor:
                    cursor = cursor[part]
                else:
                    return value
            return cursor
        return value

    def call_tool(self, tool_name: str, args: dict[str, Any], context: dict[str, Any]) -> Any:
        module = importlib.import_module(f"tools.{tool_name}")
        resolved_args = {k: self._resolve_arg_value(v, context) for k, v in (args or {}).items()}
        tool_callable = self._resolve_tool_callable(module, resolved_args)
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
            print(f"step {idx}: execute {tool_name} with args={args}")
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
