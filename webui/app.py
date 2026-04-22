import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from agents.datenimport_agent.datenimport_agent import DatenimportAgent


st.set_page_config(page_title="Immo Agent", layout="wide")

st.markdown("""
<style>

/* Sidebar button styling */
section[data-testid="stSidebar"] button {
    font-size: 12px !important;
    padding: 4px 8px !important;
    border-radius: 6px !important;
    margin-bottom: 6px !important;
}

/* Make buttons slightly narrower */
section[data-testid="stSidebar"] button[kind="secondary"] {
    width: 90%;
}

/* Optional hover effect for better UX */
section[data-testid="stSidebar"] button:hover {
    background-color: #f0f2f6;
    border: 1px solid #d0d4d9;
}

</style>
""", unsafe_allow_html=True)

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
            width: 240px !important;
            min-width: 240px !important;
            max-width: 240px !important;
            background-color: #f5f5f5;
        }

        section[data-testid="stSidebar"] > div {
            width: 240px !important;
            min-width: 240px !important;
            max-width: 240px !important;
            padding-left: 14px;
            padding-right: 14px;
        }

        section[data-testid="stSidebar"] .sidebar-title {
            font-size: 22px;
            font-weight: 700;
            margin: 0;
            text-align: left;
        }

        section[data-testid="stSidebar"] .stButton > button {
            width: 200px !important;
            min-width: 200px !important;
            max-width: 200px !important;
            text-align: left !important;
            justify-content: flex-start !important;
            white-space: nowrap !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            padding: 4px 8px !important;
            border-radius: 6px !important;
            margin: 0 0 6px 0 !important;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            background-color: #f0f2f6;
            border: 1px solid #d0d4d9;
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

if "messages" not in st.session_state:
    st.session_state.messages = []

if "trigger_import" not in st.session_state:
    st.session_state.trigger_import = False

if "datenimport_agent" not in st.session_state:
    st.session_state.datenimport_agent = DatenimportAgent()

with st.sidebar:
    st.markdown('<p class="sidebar-title">IMMO-Agent</p>', unsafe_allow_html=True)
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    if st.button("Daten Import"):
        st.session_state.messages.append({
            "role": "user",
            "content": "Ich möchte die Buchhaltungsdaten importieren. Die Datei liegt im bekannten Pfad."
        })
        st.session_state.trigger_import = True

    st.button("Mieter")
    st.button("Einheit")
    st.button("Objekt")

if st.session_state.trigger_import:
    st.session_state.trigger_import = False

    with st.status("Import läuft..."):
        result = st.session_state.datenimport_agent.run({
            "file_path": "data/raw/DEINE_DATEI.csv"
        })

    st.session_state.messages.append({
        "role": "assistant",
        "content": "Der Datenimport wurde erfolgreich durchgeführt. Die Daten sind unten dargestellt.",
        "table": result.get("table")
    })

st.markdown("## Chat")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("table") is not None:
            st.write(message["content"])
            st.dataframe(message["table"])
        else:
            st.markdown(message["content"])

prompt = st.chat_input("Eingabe")
if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
