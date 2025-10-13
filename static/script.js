console.log("DOM geladen, initialisiere Chat...");

// Elemente
const chatBox = document.getElementById('chatBox');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const micButton = document.getElementById('micButton');
const audioButton = document.getElementById('audioButton');

console.log("ChatBox gefunden:", !!chatBox);
console.log("MessageInput gefunden:", !!messageInput);
console.log("SendButton gefunden:", !!sendButton);
console.log("MicButton gefunden:", !!micButton);
console.log("AudioButton gefunden:", !!audioButton);

// Mikrofon-Implementation
let recognition = null;
let isListening = false;

// Sprachausgabe
let currentSpeech = null;

// Prüfe Browser-Support
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'de-DE';
    
    recognition.onstart = () => {
        console.log("🎤 Mikrofon aktiv");
        isListening = true;
        micButton.textContent = '🔴';
        micButton.style.background = '#ef4444';
    };
    
    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        console.log("Erkannt:", text);
        messageInput.value = text;
        stopListening();
        sendMessage();
    };
    
    recognition.onerror = (event) => {
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
            console.error("Mikrofon Fehler:", event.error);
        }
        stopListening();
    };
    
    recognition.onend = () => {
        stopListening();
    };
} else {
    console.log("❌ Spracherkennung nicht unterstützt");
    if (micButton) micButton.style.display = 'none';
}

// Funktionen
function startListening() {
    if (!recognition) {
        alert("Spracherkennung nicht verfügbar. Bitte Chrome verwenden.");
        return;
    }
    
    try {
        recognition.start();
    } catch (error) {
        console.log("Mikrofon kann nicht starten:", error);
    }
}

function stopListening() {
    isListening = false;
    if (micButton) {
        micButton.textContent = '🎤';
        micButton.style.background = '';
    }
}

// Sprachausgabe Funktionen
function speakText(text) {
    if (currentSpeech) {
        window.speechSynthesis.cancel();
    }
    
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'de-DE';
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        utterance.onstart = function() {
            console.log("🔊 Sprachausgabe gestartet");
            if (audioButton) {
                audioButton.textContent = '🔊';
                audioButton.style.background = '#4F46E5';
            }
        };
        
        utterance.onend = function() {
            console.log("🔇 Sprachausgabe beendet");
            if (audioButton) {
                audioButton.textContent = '🔊';
                audioButton.style.background = '';
            }
            currentSpeech = null;
        };
        
        utterance.onerror = function(event) {
            console.error("❌ Sprachausgabe Fehler:", event.error);
            if (audioButton) {
                audioButton.textContent = '🔊';
                audioButton.style.background = '';
            }
            currentSpeech = null;
        };
        
        window.speechSynthesis.speak(utterance);
        currentSpeech = utterance;
        
    } else {
        console.log("❌ Sprachausgabe nicht unterstützt");
        alert("Sprachausgabe wird in diesem Browser nicht unterstützt.");
    }
}

function toggleAudio() {
    if (window.speechSynthesis.speaking && currentSpeech) {
        window.speechSynthesis.cancel();
        if (audioButton) {
            audioButton.textContent = '🔊';
            audioButton.style.background = '';
        }
        console.log("⏹️ Sprachausgabe gestoppt");
    } else {
        const botMessages = document.querySelectorAll('.bot-message');
        if (botMessages.length > 0) {
            const lastMessage = botMessages[botMessages.length - 1].textContent;
            if (lastMessage && lastMessage.trim() !== '') {
                speakText(lastMessage);
                console.log("🔊 Starte Sprachausgabe:", lastMessage);
            } else {
                console.log("❌ Keine Bot-Nachricht zum Vorlesen");
            }
        } else {
            console.log("❌ Keine Bot-Nachrichten gefunden");
            alert("Keine Nachricht zum Vorlesen vorhanden.");
        }
    }
}

// Event Listener
document.addEventListener('DOMContentLoaded', function() {
    console.log("Initialisiere Event Listener...");
    
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
        console.log("SendButton EventListener hinzugefügt");
    }
    
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    if (micButton) {
        micButton.addEventListener('click', function() {
            if (isListening) {
                stopListening();
            } else {
                startListening();
            }
        });
        console.log("MicButton EventListener hinzugefügt");
    }
    
    if (audioButton) {
        audioButton.addEventListener('click', toggleAudio);
        console.log("AudioButton EventListener hinzugefügt");
    }
    
    console.log("✅ Alle Event Listener initialisiert");
});

// Chat-Funktionen
function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    console.log("Sende Nachricht:", message);

    // User Nachricht anzeigen
    addMessageToChat(message, 'user');
    if (messageInput) messageInput.value = '';

    // Loading anzeigen
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message';
    loadingDiv.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span> Denke nach...</div>';
    if (chatBox) {
        chatBox.appendChild(loadingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // An Server senden
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Server Response:", data);
        
        // Loading entfernen
        if (chatBox && chatBox.contains(loadingDiv)) {
            chatBox.removeChild(loadingDiv);
        }
        
        if (data.reply) {
            addMessageToChat(data.reply, 'bot');
            console.log("Bot Antwort erhalten:", data.reply);
            
            // Avatar Video falls vorhanden
            if (data.video_url) {
                console.log("🎥 Avatar Video URL erhalten:", data.video_url);
                playAvatarVideo(data.video_url);
            } else {
                // Fallback: Sprachausgabe
                console.log("⏭️ Kein Video, verwende Sprachausgabe");
                setTimeout(() => {
                    speakText(data.reply);
                }, 500);
            }
        } else if (data.error) {
            addMessageToChat('Fehler: ' + data.error, 'bot');
        }
    })
    .catch(error => {
        console.error('Fetch Fehler:', error);
        if (chatBox && chatBox.contains(loadingDiv)) {
            chatBox.removeChild(loadingDiv);
        }
        addMessageToChat('Netzwerk-Fehler. Bitte versuche es erneut.', 'bot');
    });
}

function addMessageToChat(message, sender) {
    if (!chatBox) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.textContent = message;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// ⭐⭐⭐ VERBESSERTE AVATAR VIDEO FUNKTION ⭐⭐⭐
function playAvatarVideo(videoUrl) {
    console.log("🎥 Spiele Avatar Video:", videoUrl);
    
    // Existierenden Container finden oder erstellen
    let videoContainer = document.getElementById('avatarVideoContainer');
    if (!videoContainer) {
        videoContainer = document.createElement('div');
        videoContainer.id = 'avatarVideoContainer';
        videoContainer.style.position = 'fixed';
        videoContainer.style.bottom = '80px';
        videoContainer.style.right = '20px';
        videoContainer.style.width = '320px';
        videoContainer.style.height = '400px';
        videoContainer.style.zIndex = '10000';
        videoContainer.style.background = '#000';
        videoContainer.style.borderRadius = '12px';
        videoContainer.style.boxShadow = '0 10px 30px rgba(0,0,0,0.5)';
        videoContainer.style.overflow = 'hidden';
        videoContainer.style.border = '3px solid #4F46E5';
        document.body.appendChild(videoContainer);
        
        console.log("✅ Avatar Video Container erstellt");
    }

    // Video-Player erstellen
    videoContainer.innerHTML = `
        <div style="position: relative; width: 100%; height: 100%;">
            <video 
                id="avatarVideoPlayer"
                src="${videoUrl}" 
                autoplay 
                muted 
                controls
                style="width: 100%; height: 100%; object-fit: cover;"
                onloadeddata="console.log('✅ Video geladen')"
                onerror="console.error('❌ Video Fehler:', this.error)">
                Ihr Browser unterstützt das Video Tag nicht.
            </video>
            <button 
                onclick="document.getElementById('avatarVideoContainer').style.display='none'" 
                style="position: absolute; top: 8px; right: 8px; background: #ef4444; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; z-index: 10001;">
                ×
            </button>
            <div style="position: absolute; bottom: 8px; left: 8px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                🤖 AvatarSalesPro
            </div>
        </div>
    `;
    
    // Container anzeigen
    videoContainer.style.display = 'block';
    console.log("✅ Avatar Video Container angezeigt");
    
    // Video Events überwachen
    const videoElement = document.getElementById('avatarVideoPlayer');
    if (videoElement) {
        videoElement.onloadstart = () => console.log("🎥 Video lädt...");
        videoElement.oncanplay = () => console.log("🎥 Video kann abgespielt werden");
        videoElement.onplay = () => console.log("🎥 Video spielt ab");
        videoElement.onerror = (e) => console.error("❌ Video Fehler:", videoElement.error);
        videoElement.onended = () => {
            console.log("🎥 Video beendet");
            videoContainer.style.display = 'none';
        };
    }
    
    // Sprachausgabe stoppen wenn Video läuft
    if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
    }
    
    // Debug: Prüfe ob Video nach 3 Sekunden läuft
    setTimeout(() => {
        if (videoElement && videoElement.paused) {
            console.log("⚠️ Video ist pausiert - versuche Play");
            videoElement.play().catch(e => console.error("❌ Auto-play fehlgeschlagen:", e));
        }
    }, 3000);
}

console.log("✅ Script.js vollständig geladen und bereit");