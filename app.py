import os
from flask import Flask, request, jsonify
from openai import OpenAI
from elevenlabs.client import ElevenLabs
import requests
import json

app = Flask(__name__)

# API Keys aus Umgebungsvariablen laden
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
elevenlabs_client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
MASCOTBOT_API_KEY = os.getenv('MASCOTBOT_API_KEY')

# CORS ohne flask_cors lösen
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    return "AvatarSalesPro API ist live! 🚀"

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        print(f"Empfangene Nachricht: {user_message}")
        
        # 1. OpenAI für Text-Antwort (NEUE API)
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Verkaufsassistent für einen E-Commerce Shop. Antworte kurz und freundlich."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150
        )
        
        ai_text = response.choices[0].message.content
        print(f"OpenAI Antwort: {ai_text}")
        
        # 2. ElevenLabs für Sprachausgabe (NEUE API)
        audio = elevenlabs_client.generate(
            text=ai_text,
            voice="Bella",
            model="eleven_multilingual_v2"
        )
        
        # Audio temporär speichern (in Production würden wir es in CDN hochladen)
        audio_filename = f"temp_audio_{hash(user_message)}.mp3"
        with open(audio_filename, 'wb') as f:
            f.write(audio)
        
        # 3. MascotBot Integration vorbereiten
        # (Hier würden wir den Avatar mit der Audio-Datei triggern)
        
        return jsonify({
            'text': ai_text,
            'audio_generated': True,
            'message': 'Chat erfolgreich verarbeitet'
        })
        
    except Exception as e:
        print(f"Fehler: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)