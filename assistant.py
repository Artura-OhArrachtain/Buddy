import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Load your API key from .env
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 2. Define tools Buddy can use automatically
def save_note_tool(filename: str, content: str) -> str:
    """Saves structured markdown notes to the local notes folder."""
    os.makedirs("notes", exist_ok=True)
    if not filename.endswith(".md"):
        filename += ".md"
    filepath = os.path.join("notes", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully saved note to {filepath}"

# 3. Initialize your stateful chat session (replaces the old single-turn setup)
chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=(
            "You are Buddy, an interactive study partner, personal assistant, and note-taker. "
            "Remember the context of our conversation. When teaching, explain clearly and quiz the user. "
            "When asked to take or save notes, format them cleanly in Markdown and call save_note_tool."
        ),
        tools=[save_note_tool],
    )
)

# 4. Run the continuous back-and-forth loop (replaces the old menu loop)
print("🤖 Buddy is online! Type 'exit' or 'quit' to stop.\n")

# Run the continuous back-and-forth streaming loop
print("🤖 Buddy is online! Type 'exit' or 'quit' to stop.\n")

while True:
    user_msg = input("You: ")
    if user_msg.lower() in ["exit", "quit"]:
        print("Buddy: Goodbye! Keep up the great work.")
        break
    if not user_msg.strip():
        continue

    # Stream the response chunk by chunk
    print("\nBuddy: ", end="", flush=True)
    for chunk in chat.send_message_stream(user_msg):
        print(chunk.text, end="", flush=True)
    print("\n")