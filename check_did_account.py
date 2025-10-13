from dotenv import load_dotenv
import os
import requests
import base64

load_dotenv()

print("=== D-ID ACCOUNT STATUS CHECK ===")

d_id_api_key = os.environ.get('D_ID_API_KEY')

if not d_id_api_key:
    print("❌ D_ID_API_KEY nicht in .env gefunden")
    exit()

# Teste verschiedene Endpoints um Account-Status zu prüfen
auth_string = base64.b64encode(f"{d_id_api_key}:".encode()).decode()
headers = {"Authorization": f"Basic {auth_string}"}

# 1. Teste Credits Endpoint (falls verfügbar)
print("1. Teste Account Credits...")
try:
    # Dieser Endpoint könnte je nach D-ID API Version variieren
    credits_response = requests.get("https://api.d-id.com/credits", headers=headers, timeout=10)
    print(f"   Credits Status: {credits_response.status_code}")
    if credits_response.status_code == 200:
        print("   ✅ Credits verfügbar")
        print(f"   Response: {credits_response.text}")
except Exception as e:
    print(f"   Credits Endpoint nicht verfügbar: {e}")

# 2. Teste Talks Limit
print("\n2. Teste Talks Limit...")
try:
    talks_response = requests.get("https://api.d-id.com/talks?limit=1", headers=headers, timeout=10)
    print(f"   Talks Status: {talks_response.status_code}")
    if talks_response.status_code == 200:
        print("   ✅ Talks Endpoint verfügbar")
except Exception as e:
    print(f"   Talks Endpoint Fehler: {e}")

# 3. Teste mit minimalem Request
print("\n3. Teste minimale Video-Generierung...")
minimal_payload = {
    "script": {
        "type": "text", 
        "input": "Test",
        "provider": {"type": "microsoft", "voice_id": "de-DE-KatjaNeural"}
    },
    "source_url": "https://cdn.d-id.com/avatars/ao2SpNz3eUf2lwn6/7O5wjLQ3bRoaRrZz.png"
}

try:
    test_response = requests.post(
        "https://api.d-id.com/talks",
        json=minimal_payload,
        headers=headers,
        timeout=30
    )
    print(f"   Test Generierung Status: {test_response.status_code}")
    
    if test_response.status_code == 201:
        print("   ✅ Video-Generierung möglich!")
        talk_data = test_response.json()
        print(f"   Talk ID: {talk_data.get('id')}")
    elif test_response.status_code == 402:
        print("   ❌ Keine Credits verfügbar")
    elif test_response.status_code == 401:
        print("   ❌ Ungültiger API Key")
    else:
        print(f"   Response: {test_response.text}")
        
except Exception as e:
    print(f"   Test Fehler: {e}")