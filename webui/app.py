import sys
from pathlib import Path

import streamlit as st
from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from agents.datenimport_agent.datenimport_agent import DatenimportAgent


MODEL_NAME = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "Du bist ein intelligenter Assistent für Immobilien- und Buchhaltungsfragen. "
    "Du hilfst strukturiert, stellst Rückfragen bei Unklarheit und erklärst verständlich.\n\n"
    "Antworte strukturiert mit:\n"
    "- kurzen Absätzen\n"
    "- Aufzählungen wenn sinnvoll\n"
    "- wichtigen Begriffen fett"
)


st.set_page_config(page_title="Immo Agent", layout="wide")

st.markdown(
    """
    <style>
        html, body, [class*="css"] {
            font-size: 20px;
        }

        .stApp {
            font-size: 20px;
        }

        section[data-testid="stSidebar"] {
            width: 20vw !important;
            min-width: 260px;
            max-width: 360px;
        }

        .main .block-container {
            padding-top: 1.3rem;
            padding-bottom: 6rem;
            max-width: 100%;
        }

        [data-testid="stChatMessage"] {
            margin-bottom: 1rem;
        }

        [data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
            border-radius: 16px;
            padding: 0.9rem 1rem;
            line-height: 1.5;
            font-size: 20px;
            border: 1px solid transparent;
        }

        [data-testid="stChatMessage"][aria-label="user"] [data-testid="stChatMessageContent"] {
            background: #eef2ff;
            border-color: #d5dcff;
        }

        [data-testid="stChatMessage"][aria-label="assistant"] [data-testid="stChatMessageContent"] {
            background: #f1f5f9;
            border-color: #dde5ee;
        }

        [data-testid="stChatInput"] textarea {
            font-size: 18px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.title("Immo Agent")

    if st.button("▶ Daten Import starten"):
        st.session_state.trigger_import = True

    st.button("nach Mieter")
    st.button("nach Einheit")
    st.button("nach Objekt")


def init_state() -> None:
    if "client" not in st.session_state:
        st.session_state.client = OpenAI()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "assistant",
                "content": (
                    "Hallo! Ich unterstütze dich gern bei Immobilien- und Buchhaltungsfragen.\n\n"
                    "- Beschreibe dein Anliegen in 1-2 Sätzen\n"
                    "- Nenne, falls vorhanden, Zahlen oder Zeiträume\n"
                    "- Ich frage nach, wenn etwas unklar ist"
                ),
            },
        ]

    if "datenimport_agent" not in st.session_state:
        st.session_state.datenimport_agent = DatenimportAgent()

    if "trigger_import" not in st.session_state:
        st.session_state.trigger_import = False


def is_import_request(text: str) -> bool:
    text = text.lower()
    return "import" in text or "buchhaltung" in text


def llm_response() -> str:
    response = st.session_state.client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        temperature=0.4,
    )
    return response.choices[0].message.content or "Ich konnte keine Antwort generieren."


def render_chat_history() -> None:
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.write(message["content"])


def render_latest_import_result() -> None:
    latest_import = None
    for message in reversed(st.session_state.messages):
        if message.get("source") == "datenimport_agent":
            latest_import = message
            break

    st.markdown("## Ergebnisse")
    if latest_import:
        st.write(latest_import.get("content", ""))
        if latest_import.get("table") is not None:
            st.dataframe(latest_import["table"])
    else:
        st.info("Noch kein Datenimport ausgeführt.")


init_state()

col_main, col_chat = st.columns([2, 1])

user_input = st.chat_input("Schreibe deine Nachricht...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

run_import = False
if st.session_state.trigger_import:
    run_import = True
    st.session_state.trigger_import = False
elif user_input and is_import_request(user_input):
    run_import = True

if run_import:
    result = st.session_state.datenimport_agent.run({
        "file_path": "data/raw/BB_Buchungsstapel - 2026-04-17T184137.857.csv"
    })

    st.session_state.messages.append({
        "role": "assistant",
        "content": result.get("text", ""),
        "table": result.get("table"),
        "source": "datenimport_agent"
    })
elif user_input:
    st.session_state.messages.append({"role": "assistant", "content": llm_response()})

with col_main:
    render_latest_import_result()

with col_chat:
    st.markdown("## Chat")
    render_chat_history()
