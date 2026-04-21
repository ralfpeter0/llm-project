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

MENU_ITEMS = [
    "LLM Chat",
    "Daten Import",
    "nach Mieter",
    "nach Einheit",
    "nach Objekt",
]


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

        [data-testid="stChatInput"] {
            position: sticky;
            bottom: 0;
            background: var(--background-color);
            padding-top: 0.7rem;
            padding-bottom: 0.2rem;
            z-index: 999;
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
    menu = st.radio("Menü", MENU_ITEMS)


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


def is_import_request(text: str) -> bool:
    text = text.lower()
    return any(w in text for w in [
        "import", "daten", "buchhaltung", "lade daten"
    ])


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
            if message.get("table") is not None:
                st.dataframe(message["table"])


def render_placeholder() -> None:
    st.markdown("## Bereich")
    st.info("Funktion noch nicht implementiert")


init_state()

if menu in ["LLM Chat", "Daten Import"]:
    st.markdown("## Chat")
    render_chat_history()

    if user_input := st.chat_input("Schreibe deine Nachricht..."):
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Denke nach..."):
                if menu == "Daten Import" or is_import_request(user_input):
                    result = st.session_state.datenimport_agent.run({
                        "file_path": "data/raw/BB_Buchungsstapel - 2026-04-17T184137.857.csv"
                    })

                    assistant_response = result.get("text", "")
                    assistant_table = result.get("table")
                else:
                    assistant_response = llm_response()
                    assistant_table = None

            st.write(assistant_response)
            if assistant_table is not None:
                st.dataframe(assistant_table)

        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_response, "table": assistant_table}
        )
else:
    render_placeholder()
