
import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

st.set_page_config(
    page_title="WiFi Support Assistant",
    page_icon="📶",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef5ff, #f8faff);
}
.hero {
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    color: white;
    background: linear-gradient(120deg, #123b72, #2478c9);
    margin-bottom: 22px;
}
.hero h1 { margin-bottom: 8px; }
.hero p { margin-bottom: 0; }
div[data-testid="stChatMessage"] {
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>📶 WiFi Support Assistant</h1>
    <p>Your personal AI assistant for internet and WiFi problems.</p>
</div>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """
You are WiFi Support Assistant, a friendly technical support agent.

Help users troubleshoot:
- WiFi connected but no internet
- Slow internet speed
- Incorrect WiFi password
- Laptop or mobile connection problems
- Router lights and basic router issues
- DNS and network connectivity issues

Rules:
1. Ask questions when information is missing.
2. Give numbered, step-by-step instructions.
3. Start with safe and easy troubleshooting steps.
4. Explain technical terms simply.
5. Never ask users to share passwords, OTPs or API keys.
6. Never claim to have checked the actual network.
7. Never suggest unauthorized network access.
8. Recommend contacting the ISP for possible outages.
9. Explain the next step if troubleshooting fails.
10. Be polite, concise and practical.
"""

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key is missing. Check your .env file.")
    st.stop()

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Could not initialize Gemini: {e}")
    st.stop()

with st.sidebar:
    st.title("🛠️ Support Tools")
    st.write("Get help with common WiFi issues.")
    st.markdown("---")
    st.subheader("Quick problems")

    quick_problems = [
        "WiFi connected but no internet",
        "My internet is very slow",
        "My WiFi password is not working",
        "My laptop cannot connect to WiFi",
        "How do I restart my router safely?"
    ]

    for problem in quick_problems:
        if st.button(problem, use_container_width=True):
            st.session_state.pending_question = problem

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_question = None
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

st.info(
    "💡 Tip: Describe your device, the problem, and any "
    "error message. Never share your WiFi password."
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Describe your WiFi problem...")

if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing your WiFi problem..."):
            try:
                history = []

                for message in st.session_state.messages[:-1]:
                    history.append(
                        types.Content(
                            role=(
                                "user"
                                if message["role"] == "user"
                                else "model"
                            ),
                            parts=[
                                types.Part(text=message["content"])
                            ]
                        )
                    )

                response = client.models.generate_content(
                    model="gemini-flash-lite-latest",
                    contents=history + [
                        types.Content(
                            role="user",
                            parts=[types.Part(text=user_input)]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.3,
                        max_output_tokens=800
                    )
                )

                answer = response.text

                if not answer:
                    answer = (
                        "I couldn't generate a response. "
                        "Please try asking in a different way."
                    )

                st.markdown(answer)

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as e:
                st.error("Gemini API Error")
                st.code(f"{type(e).__name__}: {e}")
                print("FULL GEMINI ERROR:", repr(e))
