# gestione_chat.py
import re
from agent_core import chiedi_all_agente, esegui_azione, response_cache
import json

def gestisci_input_utente(testo_utente):
    testo_utente = testo_utente.strip()
    scelta = None

    # 1️⃣ Controlla se ci sono opzioni pendenti
    if "opzioni_correnti" in response_cache:
        opzioni = response_cache["opzioni_correnti"]

        # Estrai il numero dall'input
        if testo_utente.lower().startswith("scegli "):
            try:
                scelta = int(testo_utente.split()[1])
            except ValueError:
                pass
        elif testo_utente.isdigit():
            scelta = int(testo_utente)

        # Se scelta valida
        if scelta is not None:
            if 1 <= scelta <= len(opzioni):
                azione_scelta = opzioni[scelta - 1].get("azione_proposta")
                # Rimuovi le opzioni solo dopo aver preso la scelta
                response_cache.pop("opzioni_correnti", None)
                if azione_scelta:
                    risultato = esegui_azione(azione_scelta)
                    # Se la funzione restituisce JSON, prendiamo solo risposta_testuale
                    try:
                        dati_risultato = json.loads(risultato)
                        return dati_risultato.get("risposta_testuale", risultato)
                    except Exception:
                        return risultato
                else:
                    return "⚠️ L'opzione selezionata non ha un'azione associata."
            else:
                return "⚠️ Scelta non valida. Inserisci un numero corretto."
        else:
            return "💡 Per favore, scegli un numero tra quelli proposti."

    # 2️⃣ Altrimenti invia la richiesta all’agente
    risposta_agente = chiedi_all_agente(testo_utente)

    # 3️⃣ Prova a decodificare JSON e aggiornare la cache per opzioni multiple
    try:
        dati = json.loads(risposta_agente)
        if isinstance(dati, dict):
            if dati.get("azione") == "scegli_opzione":
                opzioni = dati.get("opzioni", [])
                if opzioni:
                    response_cache["opzioni_correnti"] = opzioni
                # Restituisci sempre solo il campo risposta_testuale
                return dati.get("risposta_testuale", "Ho trovato più possibilità, scegli un'opzione:")
            else:
                # Per azioni normali, restituisci solo il testo umano
                return dati.get("risposta_testuale", risposta_agente)
    except Exception:
        # Se non è JSON, restituisci direttamente la stringa
        return risposta_agente

    # 4️⃣ Se non ci sono ambiguità, esegue direttamente l’azione
    return esegui_azione(risposta_agente)


def loop_chat():
    """
    Avvia una semplice chat testuale con l'agente.
    Utile per debug o interfaccia console.
    """
    print("🤖 Chat attiva! Scrivi 'esci' per terminare.")
    while True:
        testo_utente = input("\n🧑‍💻 Tu: ").strip()
        if testo_utente.lower() in ["esci", "exit", "quit"]:
            print("👋 Arrivederci!")
            break
        risposta = gestisci_input_utente(testo_utente)
        print(f"\n🤖 Agente: {risposta}")


if __name__ == "__main__":
    loop_chat()


# c'è un problema nella funzione scegli opzione, credo che la cache venga svuotata prima del dovuto
