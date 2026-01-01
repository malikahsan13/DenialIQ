import streamlit as st
from langgraph_app import app

st.set_page_config(page_title="Denial-IQ", layout="centered")

st.title("🧠 Denial-IQ")
st.caption("AI-powered Claims Denial Intelligence")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_input = st.chat_input("Ask about a denial, CPT, or claim...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    result = app.invoke({"question": user_input})

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"]
    })

    st.chat_message("assistant").write(result["answer"])
