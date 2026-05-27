# streamlit_app.py

import requests
import streamlit as st

# ======================
# API URLs
# ======================

UPLOAD_URL = "http://localhost:8000/api/v1/rag/upload"

QUERY_URL = "http://localhost:8000/api/v1/rag/query"

# ======================
# PAGE CONFIG
# ======================

st.set_page_config(
    page_title="RAG PDF Chat",
    page_icon="📄",
    layout="wide"
)

st.title("📄 PDF Upload + Chatbot")

# ======================
# SESSION CHAT MEMORY
# ======================

if "messages" not in st.session_state:
    st.session_state.messages=[]

# ======================
# PDF UPLOAD
# ======================

st.subheader("Upload PDF")

uploaded_file=st.file_uploader(
    "Choose PDF",
    type=["pdf"]
)

if uploaded_file:

    st.success(
        f"Selected: {uploaded_file.name}"
    )

    if st.button("Upload"):

        try:

            files={
                "file":(
                    uploaded_file.name,
                    uploaded_file,
                    "application/pdf"
                )
            }

            with st.spinner(
                "Uploading..."
            ):

                response=requests.post(
                    UPLOAD_URL,
                    files=files
                )

            if response.status_code==200:

                st.success(
                    "PDF uploaded successfully"
                )

                st.json(
                    response.json()
                )

            else:

                st.error(
                    response.text
                )

        except Exception as e:

            st.error(str(e))


st.divider()

# ======================
# CHATBOT
# ======================

st.subheader("Chat with PDF")

for msg in st.session_state.messages:

    with st.chat_message(
        msg["role"]
    ):

        st.write(
            msg["content"]
        )

query=st.chat_input(
    "Ask question..."
)

if query:

    st.session_state.messages.append(
        {
            "role":"user",
            "content":query
        }
    )

    with st.chat_message(
        "user"
    ):

        st.write(query)

    try:

        with st.spinner(
            "Searching vectors..."
        ):

            response=requests.post(
                QUERY_URL,
                json={
                    "question":query
                }
            )

        if response.status_code==200:

            result=response.json()

            answer=result["answer"]

        else:

            answer=response.text

    except Exception as e:

        answer=str(e)

    with st.chat_message(
        "assistant"
    ):

        st.write(answer)

    st.session_state.messages.append(
        {
            "role":"assistant",
            "content":answer
        }
    )