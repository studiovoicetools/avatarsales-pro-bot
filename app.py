import os
from flask import Flask, request, jsonify
import openai
from elevenlabs.client import ElevenLabs
import requests
import json

app = Flask(__name__)

# API Keys aus Umgebungsvariablen laden
openai.api_key = os.getenv('OPENAI_API_KEY')
MASCOTBOT_API_KEY = os.getenv('MASCOTBOT_API_KEY')

@app.route('/')
def index():
    return "AvatarSalesPro API ist live! 🚀"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        print(f"Empfangene Nachricht: {user_message}")
        
               # 1. OpenAI für Text-Antwort (NEUE API)
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Verkaufsassistent für einen E-Commerce Shop. Antworte kurz und freundlich."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150
        )
        
        ai_text = response.choices[0].message.content
        
        # 2. ElevenLabs für Sprachausgabe (NEUE API)
        client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
        
        audio = client.generate(
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