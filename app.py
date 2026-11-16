
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types
import uuid
from flask import session
import sqlite3
from database import (
    initialize_database,
    save_message,
    get_history,
    clear_history,
    save_preference,
    get_preferences,
    delete_preference,
    clear_preferences,
    get_chat_sessions,
    delete_chat_session
)# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "personal-ai-assistant-secret-key")

initialize_database()

# Connect to Gemini
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from .env file")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=30000)
)


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Chat API


@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json()

    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Create a unique session ID for each browser
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    session_id = session["session_id"]

    # Detect personal memory instructions
    lower_message = user_message.lower()

    memory_triggers = [
        "remember that ",
        "remember ",
        "please remember that "
    ]

    for trigger in memory_triggers:
        if lower_message.startswith(trigger):
            preference = user_message[len(trigger):].strip()

            if preference:
                save_preference(session_id, preference)
            break
        
    # Retrieve saved personal preferences
    preferences = get_preferences(session_id)

    preferences_text = "\n".join(
        f"- {preference}" for preference in preferences
    )
    

    # Save the user's message
    save_message(session_id, "user", user_message)

    # Retrieve previous conversation from database
    saved_history = get_history(session_id)

    contents = []

    for item in saved_history[:-1]:
        contents.append({
            "role": item["role"],
            "parts": [{"text": item["text"]}]
        })

    # Add current message
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contents,
            config=types.GenerateContentConfig(
                
                system_instruction=f"""
        You are Candy, a friendly personal AI assistant.

        Your personality:
        - Be friendly, warm, and conversational.
        - Be helpful, patient, and supportive.
        - Explain difficult concepts in simple language.
        - Help with programming, studies, productivity, and everyday questions.
        - Give clear, organized answers.
        - Avoid unnecessarily long responses.

        User's saved preferences:
        {preferences_text}

        Always consider these saved preferences when responding.
        Do not invent additional personal preferences.
        """,

                max_output_tokens=300,
                temperature=0.7
            )
        )

        reply = response.text or "I couldn't generate a response."

        # Save assistant's reply
        save_message(session_id, "model", reply)

        return jsonify({"reply": reply})

    except Exception as e:
        print("Chat error:", e)

        return jsonify({
            "error": "Something went wrong. Please try again."
        }), 500


@app.route("/api/clear", methods=["POST"])
def clear_chat():

    session.pop("session_id", None)

    return jsonify({
        "success": True,
        "message": "New chat started successfully!"
    })
@app.route("/api/chats", methods=["GET"])
def get_chats():

    chats = get_chat_sessions()

    return jsonify({
        "chats": [
            {
                "session_id": chat[0],
                "title": chat[1],
                "last_message": chat[2]
            }
            for chat in chats
        ]
    })
@app.route("/api/chats/<session_id>", methods=["GET"])
def open_chat(session_id):

    messages = get_history(session_id)

    if not messages:
        return jsonify({
            "success": False,
            "message": "Chat not found."
        }), 404

    session["session_id"] = session_id

    return jsonify({
        "success": True,
        "messages": messages
    })
# Delete a saved conversation
@app.route("/api/chats/<session_id>", methods=["DELETE"])
def delete_chat(session_id):

    delete_chat_session(session_id)

    if session.get("session_id") == session_id:
        session.pop("session_id", None)

    return jsonify({
        "success": True,
        "message": "Conversation deleted successfully."
    })

@app.route("/api/memories", methods=["GET"])
def get_memories():

    if "session_id" not in session:
        return jsonify({"memories": []})

    session_id = session["session_id"]
    connection = sqlite3.connect("chat_history.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, preference
        FROM preferences
        WHERE session_id = ?
        ORDER BY id ASC
    """, (session_id,))

    memories = cursor.fetchall()
    connection.close()

    return jsonify({
        "memories": [
            {"id": item[0], "preference": item[1]}
            for item in memories
        ]
    })
@app.route("/api/memories/delete/<int:preference_id>", methods=["DELETE"])
def delete_memory(preference_id):

    if "session_id" not in session:
        return jsonify({"success": False}), 401

    session_id = session["session_id"]

    delete_preference(session_id, preference_id)

    return jsonify({
        "success": True,
        "message": "Memory deleted successfully."
    })
@app.route("/api/memories/clear", methods=["DELETE"])
def clear_all_memories():

    if "session_id" not in session:
        return jsonify({"success": False}), 401

    session_id = session["session_id"]

    clear_preferences(session_id)

    return jsonify({
        "success": True,
        "message": "All memories cleared successfully."
    })


if __name__ == "__main__":
    app.run(debug=True)
