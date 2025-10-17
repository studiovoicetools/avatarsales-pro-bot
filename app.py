import os
from flask import Flask, request, jsonify
from openai import OpenAI
from elevenlabs.client import ElevenLabs
import requests
import json
import base64

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
        
        # 2. ElevenLabs für Sprachausgabe (KORRIGIERTE API)
        try:
            audio_response = elevenlabs_client.text_to_speech.convert(
                voice_id="pNInz6obpgDQGcFmaJgB",  # Bella Voice ID
                optimize_streaming_latency=0,
                output_format="mp3_22050_32",
                text=ai_text,
                model_id="eleven_multilingual_v2"
            )
            
            # Audio speichern
            audio_filename = f"temp_audio_{hash(user_message)}.mp3"
            with open(audio_filename, 'wb') as f:
                for chunk in audio_response:
                    f.write(chunk)
            
            audio_generated = True
        except Exception as e:
            print(f"ElevenLabs Fehler: {str(e)}")
            audio_generated = False
        
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

# =============================================================================
# MASCOTBOT INTEGRATION - NEUE ENDPOINTS
# =============================================================================

@app.route('/api/mascot/account', methods=['GET', 'OPTIONS'])
def get_mascot_account():
    """Holt Account-Info von MascotBot"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        response = requests.get(
            'https://api.mascot.bot/v1/account',
            headers={'Authorization': f'Bearer {MASCOTBOT_API_KEY}'}
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mascot/visemes-audio', methods=['POST', 'OPTIONS'])
def generate_visemes_audio():
    """Generiert Audio + Lip-Sync Visemes für Avatar"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        print(f"Generiere Lip-Sync Audio für: {text}")
        
        # MascotBot Visemes-Audio API aufrufen
        payload = {
            "text": text,
            "voice": "Bella",  # Stimme auswählen
            "provider": "elevenlabs",
            "model_id": "eleven_m

@app.route('/api/mascot/simple-speak', methods=['POST', 'OPTIONS'])
def simple_speak():
    """Vereinfachte Speak-Funktion (Fallback)"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        # Verwenden Sie Ihre bestehende ElevenLabs Logik
        audio_response = elevenlabs_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",
            optimize_streaming_latency=0,
            output_format="mp3_22050_32",
            text=text,
            model_id="eleven_multilingual_v2"
        )
        
        # Audio in Memory speichern
        audio_chunks = []
        for chunk in audio_response:
            audio_chunks.append(chunk)
        audio_data = b''.join(audio_chunks)
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return jsonify({
            'success': True,
            'audio': audio_base64,
            'message': 'Audio erfolgreich generiert (ohne Lip-Sync)',
            'text': text
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mascot/health', methods=['GET'])
def mascot_health():
    """Health Check für MascotBot Integration"""
    try:
        response = requests.get(
            'https://api.mascot.bot/v1/account',
            headers={'Authorization': f'Bearer {MASCOTBOT_API_KEY}'}
        )
        return jsonify({
            'mascotbot_status': 'connected' if response.status_code == 200 else 'error',
            'status_code': response.status_code
        })
    except Exception as e:
        return jsonify({'mascotbot_status': 'error', 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)