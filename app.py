import os
import streamlit as st
import ollama
from datetime import datetime
import urllib.request
import json

# Ensure local directories exist
WORKSPACE_DIR = "/mnt/storage/Buddy"
NOTES_DIR = os.path.join(WORKSPACE_DIR, "notes")
ARCHIVE_DIR = os.path.join(WORKSPACE_DIR, "archives")
os.makedirs(NOTES_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Configure page layout
st.set_page_config(
    page_title="Buddy AI (Advanced Workspace & Dark Mode)",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- PURE BLACK BACKGROUND & WHITE TEXT THEME (Claude Style Dark Mode) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a;
        color: #ffffff;
        border-right: 1px solid #222222;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 10px;
        color: #ffffff;
    }
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #161616;
        border: 1px solid #282828;
    }
    div[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #000000;
        border: 1px solid #333333;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: #121212 !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
    }
    p, h1, h2, h3, h4, h5, h6, span, label {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function for live internet search
def web_search(query):
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json"
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            results = []
            if data.get("AbstractText"):
                results.append(data.get("AbstractText"))
            for topic in data.get("RelatedTopics", []):
                if "Text" in topic:
                    results.append(topic.get("Text"))
            return "\n".join(results[:3]) if results else "No direct web summary found."
    except Exception as e:
        return f"Web search error: {e}"

def build_structured_prompt(system_rules, context_data, user_query):
    return f"""
<instructions>
{system_rules}
</instructions>

<context>
{context_data}
</context>

<user_input>
{user_query}
</user_input>
"""

# Initialize session state
if "sessions" not in st.session_state:
    st.session_state.sessions = {"New Chat": []}
if "current_session" not in st.session_state:
    st.session_state.current_session = "New Chat"

# --- Sidebar (Claude Style Navigation & Notes Manager / File Actions) ---
with st.sidebar:
    st.title("🗂️ Buddy Workspace")
    
    if st.button("✨ Start New Chat", use_container_width=True):
        new_title = f"Chat {len(st.session_state.sessions) + 1}"
        st.session_state.sessions[new_title] = []
        st.session_state.current_session = new_title
        st.rerun()

    st.divider()
    st.markdown("### 💬 Recent Conversations")
    for session_name in list(st.session_state.sessions.keys()):
        if st.button(session_name, use_container_width=True, key=f"btn_{session_name}"):
            st.session_state.current_session = session_name
            st.rerun()

    st.divider()
    st.markdown("### 📁 Notes Manager & File Actions")
    
    # Advanced Tool: Session Archiving
    if st.button("📦 Archive Current Session", use_container_width=True):
        current_chat = st.session_state.current_session
        messages = st.session_state.sessions[current_chat]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() else "_" for c in current_chat)
        archive_filename = f"archive_{safe_title}_{timestamp}.json"
        archive_path = os.path.join(ARCHIVE_DIR, archive_filename)
        with open(archive_path, "w") as f:
            json.dump(messages, f, indent=2)
        st.success(f"Archived to `{archive_filename}`")

    # Local File Reading & Notes Manager Selector
    saved_notes = os.listdir(NOTES_DIR) if os.path.exists(NOTES_DIR) else []
    if saved_notes:
        selected_note = st.selectbox("📖 Read Local Note", ["-- Select a note --"] + saved_notes)
        if selected_note != "-- Select a note --":
            note_path = os.path.join(NOTES_DIR, selected_note)
            with open(note_path, "r") as f:
                note_content = f.read()
            st.text_area("Note Content", note_content, height=180)
    else:
        st.caption("No notes saved yet in `notes/`.")

import streamlit as st

# Create tabbed artifact layout
chat_tab, artifact_tab = st.tabs(["💬 Chat", "📄 Code Artifact"])

with chat_tab:
    st.write("Conversation stream goes here...")
    user_input = st.text_input("Ask Buddy...")

with artifact_tab:
    st.subheader("Generated Output Preview")
    sample_code = "def greet(name):\n    return f'Hello, {name}!'"
    
    # Clean container mimicking an artifact card
    with st.container(border=True):
        st.code(sample_code, language="python")
        # Streamlit's st.code() natively provides a built-in copy-to-clipboard button in the top right corner

# --- Main Chat Window ---
st.title("🤖 Buddy")
st.caption("Local AI Assistant • Dark Mode • Internet Search • File Actions & Tool Simulation")

current_chat = st.session_state.current_session
messages = st.session_state.sessions[current_chat]

# Display conversation history
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Persistent chat input at the bottom
if prompt := st.chat_input("Ask Buddy or command tools (e.g., 'search: ...', 'save note: ...'):"):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Auto-name chat session
    if current_chat.startswith("Chat ") and len(messages) == 2:
        new_title = prompt[:25] + "..." if len(prompt) > 25 else prompt
        st.session_state.sessions[new_title] = messages
        del st.session_state.sessions[current_chat]
        st.session_state.current_session = new_title
        current_chat = new_title

    # Generate response and handle advanced tool/file execution
    with st.chat_message("assistant"):
        with st.spinner("Thinking, searching & executing tools..."):
            try:
                search_context = ""
                # Trigger live web search automatically or via prefix
                if prompt.lower().startswith("search:") or "latest" in prompt.lower() or "news" in prompt.lower() or "current" in prompt.lower():
                    search_query = prompt.replace("search:", "").strip()
                    web_results = web_search(search_query)
                    search_context = f"\n\n[Live Web Search Results for '{search_query}':\n{web_results}]\n"

                system_prompt = (
                    "You are Buddy, an advanced local AI assistant with dark mode styling, internet search capability, "
                    "and structured file action tools. Incorporate search context when relevant."
                )
                
                chat_messages = [{"role": "system", "content": system_prompt + search_context}] + messages
                response = ollama.chat(model='gemma:2b', messages=chat_messages)
                reply = response['message']['content']
                
                # --- ADVANCED STRUCTURED TOOL SIMULATION & FILE ACTIONS ---
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # File Writing / Note Saving Tool
                if "save" in prompt.lower() or "note" in prompt.lower():
                    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"note_{file_timestamp}.md"
                    filepath = os.path.join(NOTES_DIR, filename)
                    note_body = f"# Note saved at {timestamp_str}\n\n**Prompt:** {prompt}\n\n{reply}"
                    with open(filepath, "w") as f:
                        f.write(note_body)
                    reply += f"\n\n*(📁 [File Action]: Response automatically written & saved to `notes/{filename}`)*"

                # Timestamp Logging Tool simulation
                if "log" in prompt.lower() or "time" in prompt.lower():
                    reply += f"\n\n*(⏱️ [Timestamp Tool Log]: Action recorded at {timestamp_str})*"

                st.markdown(reply)
                messages.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                st.error(f"Error: {e}")