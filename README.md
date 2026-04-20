# llm-project

`llm-project` is a modular LLM + agent system designed for clean growth from a minimal starting point.

## Architecture overview

- `webui/` is the main entry point for interacting with the system.
- `agents/` contains independent agent modules that can evolve separately.
- `tools/` contains shared utilities that can be reused across agents.
- `config/` stores configuration files and environment-specific settings.
- `data/raw/` stores source or unprocessed datasets.
- `data/processed/` stores cleaned or transformed data artifacts.

This repository intentionally starts with only structure and no application logic.
