import threading
import webview
from app import app  # Assicurati che 'app' sia la tua Flask app

# --- FUNZIONE PER AVVIARE FLASK ---
def start_flask():
    # debug=False e use_reloader=False per evitare doppio avvio
    app.run(port=5000, debug=False, use_reloader=False)

# --- MAIN: avvio server + finestra desktop ---
if __name__ == "__main__":
    # Avvia Flask in un thread separato
    threading.Thread(target=start_flask, daemon=True).start()
    
    # Crea la finestra desktop che punta al server locale
    webview.create_window("Agent App", "http://127.0.0.1:5000", width=1000, height=700)
    
    # Avvia l'interfaccia PyWebView
    webview.start()
