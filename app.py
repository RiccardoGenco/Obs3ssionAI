from flask import Flask, request, jsonify, render_template
from datetime import datetime
from agent_core import chiedi_all_agente, esegui_azione
import whisper
import os
from werkzeug.utils import secure_filename

# --- Percorso completo del binario ffmpeg su Windows ---
FFMPEG_PATH = "C:/ffmpeg/ffmpeg-8.0-full_build/ffmpeg-8.0-full_build/bin/ffmpeg.exe"



# --- Flask app ---
app = Flask(__name__)

# Cartella per salvare gli audio caricati
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Modello Whisper (scegli "small" o "base")
model = whisper.load_model("small")

# --- Funzione per salvare log chat ---
def salva_log(messaggio_utente, risposta_agente):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("registro.txt", "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] Utente: {messaggio_utente} | Agente: {risposta_agente}\n")

# --- Rotte Flask ---
@app.route("/")
def home():
    return render_template("index.html")  # punta al tuo frontend

@app.route("/chat", methods=["POST"])
def chat():
    messaggio = request.json.get("messaggio", "")
    risposta_json = chiedi_all_agente(messaggio)
    risposta_testuale = esegui_azione(risposta_json)

    salva_log(messaggio, risposta_testuale)
    return jsonify({"risposta": risposta_testuale})

@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if "file" not in request.files:
        return jsonify({"error": "Nessun file ricevuto"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # DEBUG: verifica dove viene salvato il file
    print(f"[DEBUG] Salvo file in: {filepath}")
    file.save(filepath)
    print(f"[DEBUG] File esiste ora? {os.path.exists(filepath)}")

    try:
        result = model.transcribe(
    filepath,
    fp16=False
)
        text = result.get("text", "").strip()
        print(f"[Trascrizione vocale] {text}")
        return jsonify({"text": text})
    except Exception as e:
        print("Errore trascrizione:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

# --- Avvio server ---
if __name__ == "__main__":
    app.run(debug=True)
