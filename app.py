from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import requests
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app, origins=["https://lcacosta.com", "http://localhost:3000"])

# 📨 Save email to HubSpot CRM
def save_to_hubspot(email):
    hubspot_token = os.getenv("HUBSPOT_TOKEN")
    if not hubspot_token:
        print("⚠️ HUBSPOT_TOKEN not found.")
        return

    headers = {
        "Authorization": f"Bearer {hubspot_token}",
        "Content-Type": "application/json"
    }
    data = {
        "properties": {
            "email": email,
            "firstname": "LC Site Visitor",
            "lifecyclestage": "lead",
            "hs_lead_status": "New"
        }
    }

    try:
        res = requests.post("https://api.hubapi.com/crm/v3/objects/contacts", headers=headers, json=data)
        print("✅ Email saved to HubSpot:", email)
    except Exception as e:
        print("❌ Error saving to HubSpot:", e)

@app.route("/")
def home():
    return "✅ LC's AI Chatbot Backend is running!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

    if not messages:
        return jsonify({"error": "No messages provided."}), 400

    # 🚫 Filter out misuse attempts
    for msg in messages:
        content = msg.get("content", "").lower()
        if any(trigger in content for trigger in [
            "write an essay", "code", "act as", "ignore previous", "jailbreak"
        ]):
            return jsonify({
                "choices": [{
                    "message": {
                        "content": "❌ Sorry, I can’t help with that. This assistant is just for LC’s AI services 😊"
                    }
                }]
            })

    # 🧠 Check if email is being submitted
    last_user_message = messages[-1].get("content", "")
    if "@" in last_user_message and "." in last_user_message:
        save_to_hubspot(last_user_message)

    # 🔐 Call OpenAI GPT-4
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.6,
            max_tokens=400
        )
        return jsonify(response)

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({
            "choices": [{
                "message": {
                    "content": "⚠️ Oops! Something went wrong. Please try again later."
                }
            }]
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
