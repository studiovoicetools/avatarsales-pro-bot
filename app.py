from dotenv import load_dotenv
load_dotenv()  # Lädt die .env Datei

from flask import Flask, render_template, request, jsonify, url_for
import requests
import os
import json
from datetime import datetime, timedelta
from openai import OpenAI
import logging
import base64
import time

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CACHE_FILE = 'chat_cache.json'
TTL_HOURS = 24
DEFAULT_SHOP_ID = 'default_shop'

# Cache Initialisierung
def initialize_cache():
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def cleanup_cache():
    now = datetime.now()
    cache = initialize_cache()
    expired_keys = [
        key for key, entry in cache.items()
        if datetime.fromisoformat(entry['timestamp']) < now - timedelta(hours=TTL_HOURS)
    ]
    for key in expired_keys:
        del cache[key]
    if expired_keys:
        save_cache(cache)
    return cache

# OpenAI Client initialisieren mit Error-Handling
try:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    client = OpenAI(api_key=api_key)
    logging.info("OpenAI Client erfolgreich initialisiert")
except Exception as e:
    logging.error(f"Fehler bei OpenAI Initialisierung: {e}")
    client = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/did_video', methods=['POST'])
@app.route('/did_video', methods=['POST'])

@app.route('/did_video', methods=['POST'])
def did_video():
    """D-ID AVATAR INTEGRATION - KORRIGIERT NACH DOKUMENTATION"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'Kein Text provided'}), 400
        
        # D-ID API Konfiguration
        d_id_api_key = os.environ.get('D_ID_API_KEY')
        
        if not d_id_api_key:
            return jsonify({'error': 'D_ID_API_KEY nicht gesetzt'}), 500
        
        print(f"🎬 Starte D-ID Video-Generierung...")
        print(f"Text: {text[:100]}...")
        
        # KORREKTE AUTHENTIFIZIERUNG laut D-ID Dokumentation
        import base64
        auth_string = base64.b64encode(f"{d_id_api_key}:".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json"
        }
        
        # D-ID API Endpoint
        d_id_url = "https://api.d-id.com/talks"
        
        # Payload laut D-ID Dokumentation
        payload = {
            "script": {
                "type": "text",
                "input": text,
                "provider": {
                    "type": "microsoft",
                    "voice_id": "de-DE-KatjaNeural"
                }
            },
            "config": {
                "fluent": "false",
                "pad_audio": "0.0"
            },
            "source_url": "https://cdn.d-id.com/avatars/ao2SpNz3eUf2lwn6/7O5wjLQ3bRoaRrZz.png"
        }
        
        print(f"📤 Sende Request an D-ID API...")
        response = requests.post(d_id_url, json=payload, headers=headers, timeout=30)
        
        print(f"📥 D-ID Response Status: {response.status_code}")
        
        if response.status_code == 201:
            response_data = response.json()
            print(f"📄 D-ID Response Data: {response_data}")
            
            talk_id = response_data.get('id')
            if not talk_id:
                print("❌ Keine Talk ID von D-ID erhalten")
                return jsonify({'error': 'Keine Talk ID von D-ID erhalten'}), 500
            
            print(f"✅ D-ID Video-Generierung gestartet. Talk ID: {talk_id}")
            
            # Auf Video-Fertigstellung warten
            video_url = wait_for_did_video(talk_id, d_id_api_key)
            
            if video_url:
                print(f"✅ D-ID Video fertig: {video_url}")
                return jsonify({
                    'video_url': video_url,
                    'status': 'success', 
                    'talk_id': talk_id,
                    'note': 'D-ID Avatar - Funktioniert!'
                })
            else:
                print("❌ D-ID Video-Generierung fehlgeschlagen")
                return jsonify({
                    'reply': text,
                    'cached': False, 
                    'avatar_status': 'failed',
                    'fallback': 'text_only'
                })
        else:
            error_msg = f"D-ID API Fehler: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            
            # Detaillierte Fehleranalyse
            if response.status_code == 401:
                error_msg += " (Ungültiger API Key oder falsche Authentifizierung)"
            elif response.status_code == 402:
                error_msg += " (Nicht genügend Credits)"
            elif response.status_code == 404:
                error_msg += " (Avatar nicht gefunden)"
                
            return jsonify({
                'reply': text,
                'cached': False,
                'avatar_status': 'failed',
                'fallback': 'text_only',
                'error': error_msg
            })
            
    except requests.exceptions.Timeout:
        print("❌ D-ID API Timeout")
        return jsonify({'error': 'D-ID API Timeout'}), 500
    except Exception as e:
        print(f"❌ D-ID Fehler: {str(e)}")
        return jsonify({
            'reply': text if 'text' in locals() else '',
            'cached': False,
            'avatar_status': 'failed', 
            'fallback': 'text_only'
        })

def wait_for_did_video(talk_id, api_key, max_wait=120, check_interval=3):
    """Wartet auf die Fertigstellung des D-ID Videos"""
    status_url = f"https://api.d-id.com/talks/{talk_id}"
    
    # Korrekte Authentifizierung für Status-Check
    import base64
    auth_string = base64.b64encode(f"{api_key}:".encode()).decode()
    headers = {"Authorization": f"Basic {auth_string}"}
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            current_wait = int(time.time() - start_time)
            print(f"⏳ Prüfe D-ID Video Status... ({current_wait}s)")
            
            response = requests.get(status_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                video_status = status_data.get('status')
                result_url = status_data.get('result_url')
                
                print(f"📊 D-ID Video Status: {video_status}")
                
                if video_status == 'done' and result_url:
                    print(f"✅ D-ID Video fertig: {result_url}")
                    return result_url
                elif video_status == 'error':
                    error_msg = status_data.get('error', 'Unbekannter Fehler')
                    print(f"❌ D-ID Video-Generierung fehlgeschlagen: {error_msg}")
                    return None
            
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"⚠️ D-ID Status check Fehler: {e}")
            time.sleep(check_interval)
    
    print("❌ Timeout beim Warten auf D-ID Video")
    return None


def wait_for_did_video(talk_id, api_key, max_wait=120, check_interval=3):
    """Wartet auf die Fertigstellung des D-ID Videos"""
    status_url = f"https://api.d-id.com/talks/{talk_id}"
    headers = {"Authorization": f"Basic {api_key}"}
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            current_wait = int(time.time() - start_time)
            print(f"⏳ Prüfe D-ID Video Status... ({current_wait}s)")
            
            response = requests.get(status_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                video_status = status_data.get('status')
                result_url = status_data.get('result_url')
                
                print(f"📊 D-ID Video Status: {video_status}")
                
                if video_status == 'done' and result_url:
                    print(f"✅ D-ID Video fertig: {result_url}")
                    return result_url
                elif video_status == 'error':
                    error_msg = status_data.get('error', 'Unbekannter Fehler')
                    print(f"❌ D-ID Video-Generierung fehlgeschlagen: {error_msg}")
                    return None
                # 'created' oder 'started' -> weiter warten
            
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"⚠️ D-ID Status check Fehler: {e}")
            time.sleep(check_interval)
    
    print("❌ Timeout beim Warten auf D-ID Video")
    return None

@app.route('/chat', methods=['POST'])
def chat():
    if not client:
        return jsonify({'reply': 'Fehler: OpenAI Client nicht initialisiert. Bitte API Key überprüfen.'}), 500
    
    user_message = request.json.get('message', '').strip()
    logging.info(f"Empfangene Nachricht: {user_message}")
    
    if not user_message:
        return jsonify({'reply': 'Bitte geben Sie eine Nachricht ein.'}), 400

    try:
        # Cache kontrolü
        cache = cleanup_cache()
        cache_key = f"{DEFAULT_SHOP_ID}:{user_message.lower()}"
        
        if cache_key in cache:
            cache_entry = cache[cache_key]
            cache_entry['usage_count'] += 1
            cache_entry['timestamp'] = datetime.now().isoformat()
            save_cache(cache)
            logging.info(f"Cache treffer für: {user_message}")
            return jsonify({'reply': cache_entry['answer'], 'cached': True})

        # OpenAI API Call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Verkaufsassistent. Antworte in der gleichen Sprache wie der Benutzer. Du sprichst Deutsch und Englisch. Halte Antworten kurz und prägnant (max 2 Sätze)."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=100  # Kürzer für bessere Video-Generierung
        )
        
        bot_reply = response.choices[0].message.content
        logging.info(f"OpenAI Antwort: {bot_reply}")
        
        # Cache entry erstellen
        cache_entry = {
            "question": user_message,
            "answer": bot_reply,
            "timestamp": datetime.now().isoformat(),
            "usage_count": 1,
            "shop_id": DEFAULT_SHOP_ID
        }
        cache[cache_key] = cache_entry
        save_cache(cache)
        
        # D-ID AVATAR VIDEO GENERIEREN
        try:
            video_response = requests.post(
                'http://localhost:5000/did_video',
                json={'text': bot_reply},
                timeout=60  # Mehr Zeit für Video-Generierung
            )
            
            if video_response.status_code == 200:
                video_data = video_response.json()
                video_url = video_data.get('video_url')
                
                if video_url:
                    # Video-URL auch cachen
                    video_cache_key = f"video:{bot_reply}"
                    cache[video_cache_key] = {
                        'video_url': video_url,
                        'timestamp': datetime.now().isoformat(),
                        'talk_id': video_data.get('talk_id')
                    }
                    save_cache(cache)
                    
                    logging.info(f"✅ Avatar Video generiert: {video_url}")
                    return jsonify({
                        'reply': bot_reply, 
                        'cached': False,
                        'video_url': video_url,
                        'avatar_status': 'success'
                    })
            
            logging.warning("❌ Keine Video-URL von D-ID erhalten")
            
        except Exception as e:
            logging.error(f"❌ D-ID Video Fehler: {e}")
        
        # Fallback: Nur Text-Antwort
        return jsonify({
            'reply': bot_reply, 
            'cached': False,
            'avatar_status': 'failed'
        })
    
    except Exception as e:
        logging.error(f"OpenAI API Fehler: {e}")
        return jsonify({'reply': f'Entschuldigung, der KI-Service ist momentan nicht verfügbar. Fehler: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)