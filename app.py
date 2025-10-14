import os
from flask import Flask, request, jsonify
from openai import OpenAI
from elevenlabs.client import ElevenLabs
import requests
import json
import base64  # Diese Zeile hinzufügen, falls nicht vorhanden

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
    
    # =============================================================================
# MASCOTBOT INTEGRATION - NEUE ENDPOINTS (ERGÄNZUNG)
# =============================================================================

@app.route('/api/mascot/avatars', methods=['GET', 'OPTIONS'])
def get_mascot_avatars():
    """Holt verfügbare Avatare von MascotBot API"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        response = requests.get(
            'https://api.mascot.bot/v1/avatars',
            headers={'Authorization': f'Bearer {MASCOTBOT_API_KEY}'}
        )
        
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({'error': 'MascotBot API Fehler', 'status': response.status_code}), 500
            
    except Exception as e:
        print(f"MascotBot Avatare Fehler: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mascot/speak', methods=['POST', 'OPTIONS'])
def mascot_speak():
    """Text zu Speech mit Lip-Sync für Avatar"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        print(f"MascotBot Speak: {text}")
        
        # 1. ElevenLabs Audio generieren (Ihre bestehende Logik)
        try:
            audio_response = elevenlabs_client.text_to_speech.convert(
                voice_id="pNInz6obpgDQGcFmaJgB",  # Bella Voice ID
                optimize_streaming_latency=0,
                output_format="mp3_22050_32",
                text=text,
                model_id="eleven_multilingual_v2"
            )
            
            # Audio in Memory speichern (nicht auf Disk)
            audio_chunks = []
            for chunk in audio_response:
                audio_chunks.append(chunk)
            audio_data = b''.join(audio_chunks)
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
        except Exception as e:
            print(f"ElevenLabs Fehler in MascotBot: {str(e)}")
            return jsonify({'error': f'ElevenLabs Fehler: {str(e)}'}), 500
        
        # 2. Audio zu MascotBot für Visemes/Lip-Sync senden
        try:
            visemes_payload = {
                "audio": audio_base64,
                "sample_rate": 22050  # Entspricht der ElevenLabs Output-Rate
            }
            
            visemes_response = requests.post(
                'https://api.mascot.bot/v1/visemes',
                json=visemes_payload,
                headers={
                    'Authorization': f'Bearer {MASCOTBOT_API_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            if visemes_response.status_code == 200:
                visemes_data = visemes_response.json()
                
                return jsonify({
                    'success': True,
                    'audio': audio_base64,
                    'visemes': visemes_data,
                    'message': 'Audio und Lip-Sync erfolgreich generiert'
                })
            else:
                return jsonify({
                    'error': 'MascotBot Visemes Fehler',
                    'status': visemes_response.status_code,
                    'details': visemes_response.text
                }), 500
                
        except Exception as e:
            print(f"MascotBot Visemes Fehler: {str(e)}")
            return jsonify({'error': f'MascotBot Fehler: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Allgemeiner Speak Fehler: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mascot/health', methods=['GET'])
def mascot_health():
    """Health Check für MascotBot Integration"""
    try:
        response = requests.get(
            'https://api.mascot.bot/v1/avatars',
            headers={'Authorization': f'Bearer {MASCOTBOT_API_KEY}'}
        )
        return jsonify({
            'mascotbot_status': 'connected' if response.status_code == 200 else 'error',
            'status_code': response.status_code
        })
    except Exception as e:
        return jsonify({'mascotbot_status': 'error', 'error': str(e)})

# =============================================================================
# ENDE MASCOTBOT ERGÄNZUNG
# =============================================================================