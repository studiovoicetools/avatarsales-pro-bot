from dotenv import load_dotenv
import os
import requests
import json
import base64

load_dotenv()

print("=== KORREKTER D-ID API TEST ===")

d_id_api_key = os.environ.get('D_ID_API_KEY')
print(f"API Key geladen: ✅ (Länge: {len(d_id_api_key)})")

# Laut D-ID Dokumentation: Basic Authentication mit API Key als Username und leerem Password
# ODER: API Key direkt als Bearer Token

# Test 1: Basic Auth mit API Key als Username
auth_basic = base64.b64encode(f"{d_id_api_key}:".encode()).decode()
headers_basic = {
    "Authorization": f"Basic {auth_basic}",
    "Content-Type": "application/json"
}

# Test 2: Bearer Token
headers_bearer = {
    "Authorization": f"Bearer {d_id_api_key}",
    "Content-Type": "application/json"
}

# Test 3: API Key im Header (alternative Methode)
headers_key = {
    "Authorization": d_id_api_key,
    "Content-Type": "application/json"
}

test_headers = [
    ("Basic Auth", headers_basic),
    ("Bearer Token", headers_bearer), 
    ("Direct API Key", headers_key)
]

payload = {
    "script": {
        "type": "text",
        "input": "Hallo! Das ist ein Test der D-ID API.",
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

for auth_type, headers in test_headers:
    print(f"\n🔍 Teste {auth_type}...")
    try:
        response = requests.post(
            "https://api.d-id.com/talks",
            json=payload,
            headers=headers,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            print("   ✅ ERFOLG! Korrekte Authentifizierung gefunden!")
            data = response.json()
            print(f"   Talk ID: {data.get('id')}")
            break
        elif response.status_code == 401:
            print("   ❌ 401 Unauthorized")
        else:
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Fehler: {e}")