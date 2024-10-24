from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from groq import Groq
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load API key
working_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(working_dir, "config.json")) as config_file:
    config_data = json.load(config_file)

GROQ_API_KEY = config_data.get("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

client = Groq()

# Rate limiting variables
RATE_LIMIT = 20  # Maximum 20 requests per minute
rate_limit_store = {}

# Premade requests
premade_requests = {
    "What is FARM-FRIEND AI?": (
        "FARM-FRIEND AI is a cutting-edge platform that uses artificial intelligence to improve farming practices. "
        "It helps farmers make better decisions by providing insights based on data, ultimately leading to more efficient and productive agriculture. "
        "To learn more about us, feel free to visit our <a href='https://FARM-FRIEND-AI.vercel.app/aboutus' style='color: blue; text-decoration: underline;'>About Us page</a>."
    ),
    # Additional premade requests...
}

def is_rate_limited(ip):
    current_time = time.time()
    if ip not in rate_limit_store:
        rate_limit_store[ip] = []

    # Filter out requests older than 60 seconds
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if current_time - t < 60]

    if len(rate_limit_store[ip]) >= RATE_LIMIT:
        return True
    rate_limit_store[ip].append(current_time)
    return False

@app.route('/')
def health_check():
    return "Healthy", 200

@app.route('/FARM-FRIEND-ChatBot', methods=['POST'])
def chat():
    ip = request.remote_addr
    if is_rate_limited(ip):
        return jsonify({"error": "Rate limit exceeded. Please wait and try again."}), 429

    data = request.json
    user_prompt = data.get('prompt')

    if user_prompt in premade_requests:
        return jsonify({"response": premade_requests[user_prompt]})

    messages = [
        {'role': "system", "content": "You are an AI assistant for FARM-FRIEND AI. Provide helpful and accurate information about FARM-FRIEND AI's services."},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )
        assistant_response = response.choices[0].message.content
        return jsonify({"response": assistant_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
