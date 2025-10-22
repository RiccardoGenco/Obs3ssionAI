import requests
import json
import os
from dotenv import load_dotenv
import gestione_file
import gestione_db

# Inizializza il database
gestione_db.inizializza_db()

# Variabili globali e inizializzazione
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "anthropic/claude-3-haiku")

# Carica SYSTEM_PROMPT una volta sola all'avvio del modulo
try:
    with open("SYSTEM_PROMPT.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except Exception as e:
    print(f"Errore nel caricamento del SYSTEM_PROMPT: {e}")
    SYSTEM_PROMPT = "Sei un assistente AI utile e cordiale."

# Cache per memorizzare le risposte precedenti (opzionale)
response_cache = {}

# Endpoint 
API_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


def chiedi_all_agente(messaggio_utente, temperature=0.7, max_retries=3):
    """
    Invia una richiesta all'API con il messaggio utente e restituisce la risposta JSON.
    Implementa caching e retry in caso di errori.
    """
    if temperature == 0 and messaggio_utente in response_cache:
        return response_cache[messaggio_utente]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Python Chat Application"
    }
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": messaggio_utente}
        ],
        "temperature": temperature,
        "max_tokens": 4096
    }

    for tentativo in range(max_retries):
        try:
            response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
            print(f"[DEBUG] Tentativo {tentativo+1} - Stato HTTP: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            risposta = data["choices"][0]["message"]["content"]
            if temperature == 0:
                response_cache[messaggio_utente] = risposta
            return risposta
        except requests.RequestException as e:
            if hasattr(response, "status_code") and response.status_code == 404:
                return json.dumps({
                    "azione": "rispondi",
                    "risposta_testuale": f"ERRORE: Endpoint non trovato. Verifica l'URL: {API_ENDPOINT}"
                })
            if tentativo < max_retries - 1:
                print(f"Errore rete, ritentando... ({tentativo+1}/{max_retries})")
                continue
            else:
                return json.dumps({
                    "azione": "rispondi",
                    "risposta_testuale": f"Errore API: {str(e)} - Status: {getattr(response, 'status_code', 'N/A')}"
                })
        except (KeyError, json.JSONDecodeError) as e:
            return json.dumps({
                "azione": "rispondi",
                "risposta_testuale": f"Errore nel parsing della risposta: {str(e)}"
            })


def esegui_azione(risposta_agente):
    """
    Interpreta la risposta JSON dell'agente e chiama la funzione corretta di gestione_file o gestione_db.
    Ritorna sempre una stringa da mostrare all'utente.
    Supporta azioni atomiche e piani multi-step (Hybrid Planner).
    """
    # Se la risposta è una stringa JSON, convertila
    if isinstance(risposta_agente, str):
        try:
            dati = json.loads(risposta_agente)
        except json.JSONDecodeError:
            return risposta_agente
    else:
        dati = risposta_agente

    # Se è un piano, esegui tutti gli step
    if dati.get("azione") == "pianifica":
        return esegui_piano(dati)

    azione = dati.get("azione", "")
    nome_file = dati.get("file", "")
    contenuto = dati.get("contenuto", "")
    risposta_testuale = dati.get("risposta_testuale", "")
    percorso_origine = dati.get("file_origine", "") or dati.get("percorso_origine", "")
    percorso_destinazione = dati.get("file_destinazione", "") or dati.get("percorso_destinazione", "")

    # Parametri specifici per il database
    nome_tabella = dati.get("nome_tabella", "")
    colonne = dati.get("colonne", "*")
    condizione = dati.get("condizione", None)
    dati_db = dati.get("dati", {})

    try:
        # Gestione opzioni multiple proposte dall'agente
        if azione == "scegli_opzione":
            opzioni = dati.get("opzioni", [])
            testo = dati.get("risposta_testuale", "La tua richiesta può significare più cose. Scegli un'opzione:")

            if not opzioni:
                return "Errore: nessuna opzione disponibile per la scelta."

            # Filtra le opzioni per tabelle esistenti
            from gestione_db import elenca_tabelle
            tabelle_esistenti = [t['name'] for t in elenca_tabelle()["data"] if 'name' in t]
            
            for op in opzioni:
                nome_tabella = op.get("azione_proposta", {}).get("nome_tabella")
                if nome_tabella and nome_tabella not in tabelle_esistenti:
                    op["azione_proposta"] = None  # Rimuove azioni su tabelle inesistenti

            output = [testo, ""]
            for i, op in enumerate(opzioni, start=1):
                output.append(f"{i}. {op.get('descrizione', 'Opzione senza descrizione')}")
            output.append("")
            output.append("Rispondi con: scegli <numero> o solo il numero per procedere.")

            response_cache["opzioni_correnti"] = opzioni
            return "\n".join(output)


        # Azioni su file e cartelle
        if azione == "scrivi_registro":
            return gestione_file.scrivi_registro_chat(nome_file or "registro.txt", contenuto)
        elif azione == "crea_file":
            return gestione_file.crea_file(nome_file)
        elif azione == "crea_cartella":
            return gestione_file.crea_cartella(nome_file)
        elif azione == "scrivi":
            return gestione_file.scrivi_file(nome_file, contenuto)
        elif azione == "aggiungi":
            return gestione_file.aggiungi_al_file(nome_file, contenuto)
        elif azione == "svuota":
            return gestione_file.cancella_contenuto_file(nome_file)
        elif azione == "cancella_file":
            return gestione_file.cancella_file(nome_file)
        elif azione == "cancella_cartella":
            return gestione_file.cancella_cartella(nome_file)
        elif azione == "sposta_file":
            if percorso_origine and percorso_destinazione:
                return gestione_file.sposta_file(percorso_origine, percorso_destinazione)
            return "Errore: percorso_origine o percorso_destinazione non specificati per lo spostamento del file."
        elif azione == "sposta_cartella":
            if percorso_origine and percorso_destinazione:
                return gestione_file.sposta_cartella(percorso_origine, percorso_destinazione)
            return "Errore: percorso_origine o percorso_destinazione non specificati per lo spostamento della cartella."
        elif azione == "rispondi":
            return risposta_testuale or "OK"

        # Azioni database
        elif azione == "crea_tabella":
            risultato = gestione_db.crea_tabella(nome_tabella, colonne)
            return risposta_testuale if risultato["success"] else f"Errore: {risultato['error']}"
        elif azione == "inserisci_dati":
            risultato = gestione_db.inserisci_dati(nome_tabella, dati_db)
            return risposta_testuale if risultato["success"] else f"Errore: {risultato['error']}"
        elif azione == "aggiorna_dati":
            risultato = gestione_db.aggiorna_dati(nome_tabella, dati_db, condizione)
            return risposta_testuale if risultato["success"] else f"Errore: {risultato['error']}"
        elif azione == "elimina_dati":
            risultato = gestione_db.elimina_dati(nome_tabella, condizione)
            return risposta_testuale if risultato["success"] else f"Errore: {risultato['error']}"
        elif azione == "elimina_tabella":
            risultato = gestione_db.elimina_tabella(nome_tabella)
            return risposta_testuale if risultato["success"] else f"Errore: {risultato['error']}"
        elif azione == "consulta_tabella":
            risultato = gestione_db.consulta_tabella(nome_tabella, colonne, condizione)
            if not risultato["success"]:
                return f"Errore: {risultato['error']}"
            dati = risultato["data"]
            if not dati:
                return "Nessun risultato trovato."
            colonne = list(dati[0].keys())
            output = [risposta_testuale] if risposta_testuale else []
            header = " - ".join(colonne)
            output.append(header)
            for riga in dati:
                row_data = " - ".join(str(riga.get(col, "")) for col in colonne)
                output.append(row_data)
            return "\n".join(output)

        elif azione == "elenca_tabelle":
            risultato = gestione_db.elenca_tabelle()
            if risultato["success"]:
                tabelle = [t['name'] for t in risultato['data']]
                testo = risposta_testuale or "Ecco l'elenco delle tabelle presenti nel database:"
                return f"{testo}\n" + "\n".join(tabelle)
            return f"Errore: {risultato['error']}"

        elif azione == "descrivi_tabella":
            risultato = gestione_db.descrivi_tabella(nome_tabella)
            if risultato["success"]:
                testo = risposta_testuale or f"Struttura della tabella '{nome_tabella}':"
                righe = [f"{col['name']} ({col['type']})" for col in risultato['data']]
                return f"{testo}\n" + "\n".join(righe)
            return f"Errore: {risultato['error']}"

        elif azione == "esporta_tabella":
            file_destinazione = dati.get("file_destinazione", "")
            formato = dati.get("formato", "csv")
            risultato = gestione_db.esporta_tabella(nome_tabella, file_destinazione, formato)
            return risultato["message"] if risultato["success"] else f"Errore durante l'esportazione: {risultato['error']}"

        elif azione == "modifica_tabella":
            operazione = dati.get("operazione", "")
            if operazione == "aggiungi_colonna":
                definizione_colonna = dati.get("definizione_colonna", "")
                risultato = gestione_db.modifica_tabella(nome_tabella, operazione, definizione_colonna=definizione_colonna)
            elif operazione == "rimuovi_colonna":
                nome_colonna = dati.get("nome_colonna", "")
                risultato = gestione_db.modifica_tabella(nome_tabella, operazione, nome_colonna=nome_colonna)
            else:
                return f"Operazione '{operazione}' non supportata per la modifica della tabella"
            return risposta_testuale if risultato["success"] else f"Errore durante la modifica della tabella: {risultato['error']}"

        else:
            return risposta_testuale or f"Azione '{azione}' non riconosciuta."

    except Exception as e:
        return f"Errore durante l'esecuzione dell'azione '{azione}': {e}"



def esegui_piano(piano_json):
    """
    Esegue un piano complesso (Hybrid Planner).
    Ogni step viene passato a esegui_azione.
    """
    risultati = []
    for step in piano_json.get("steps", []):
        risultati.append(esegui_azione(step))
    return "\n".join(risultati)


