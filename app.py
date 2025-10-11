from flask import Flask, request, jsonify, render_template
from datetime import datetime
from agent_core import chiedi_all_agente, esegui_azione

app = Flask(__name__)

def salva_prenotazione(messaggio_utente, risposta_agente):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("prenotazioni.txt", "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] Utente: {messaggio_utente} | Agente: {risposta_agente}\n")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/chat", methods=["POST"])
def chat():
    messaggio = request.json.get("messaggio", "")
    risposta_json = chiedi_all_agente(messaggio)
    risposta_testuale = esegui_azione(risposta_json)

    salva_prenotazione(messaggio, risposta_json)

    return jsonify({"risposta": risposta_testuale})

if __name__ == "__main__":
    app.run(debug=True)
