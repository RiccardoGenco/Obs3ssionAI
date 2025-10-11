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
        SYSTEM_PROMPT = f.read().strip()  # Rimuove eventuali spazi bianchi extra
except Exception as e:
    print(f"Errore nel caricamento del SYSTEM_PROMPT: {e}")
    SYSTEM_PROMPT = "Sei un assistente AI utile e cordiale."

# Cache per memorizzare le risposte precedenti (opzionale)
response_cache = {}

# Endpoint 
API_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


def chiedi_all_agente(messaggio_utente, temperature=0.7, max_retries=3):
    """
    Invia una richiesta all'API con il messaggio utente e restituisce la risposta testuale.
    Implementa caching e retry in caso di errori.
    """
    # Verifica se la risposta è già in cache (solo se temperature è 0)
    if temperature == 0 and messaggio_utente in response_cache:
        return response_cache[messaggio_utente]
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",  # Required for OpenRouter
        "X-Title": "Python Chat Application"  # Optional but recommended
    }
    payload = {
        "model": DEFAULT_MODEL 
,
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
            
            # DEBUG: utile per diagnosi errori
            print(f"Tentativo {tentativo+1} - Stato HTTP: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            # Ottieni la risposta
            risposta = data["choices"][0]["message"]["content"]
            
            # Salva in cache se temperature è 0
            if temperature == 0:
                response_cache[messaggio_utente] = risposta
            
            return risposta
            
        except requests.RequestException as e:
            if response.status_code == 404:
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
                    "risposta_testuale": f"Errore API: {str(e)} - Status: {response.status_code}"
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
    """
    # Se la risposta è già una stringa (potrebbe essere un errore)
    if isinstance(risposta_agente, str):
        try:
            # Prova a convertire in JSON
            dati = json.loads(risposta_agente)
        except json.JSONDecodeError:
            # Se non è JSON, restituisci la stringa così com'è
            return risposta_agente
    else:
        dati = risposta_agente

    azione = dati.get("azione", "")
    nome_file = dati.get("file", "")
    contenuto = dati.get("contenuto", "")
    risposta_testuale = dati.get("risposta_testuale", "")
    percorso_origine = dati.get("percorso_origine", "")
    percorso_destinazione = dati.get("percorso_destinazione", "")
    
    # Parametri specifici per il database
    nome_tabella = dati.get("nome_tabella", "")
    colonne = dati.get("colonne", "*")
    condizione = dati.get("condizione", None)
    dati_db = dati.get("dati", {})

    try:
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
            else:
                return "Errore: percorso_origine o percorso_destinazione non specificati per lo spostamento."
            
        elif azione == "sposta_cartella":
            if percorso_origine and percorso_destinazione:
                return gestione_file.sposta_cartella(percorso_origine, percorso_destinazione)
            else:
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
            
        elif azione == "consulta_tabella":
            risultato = gestione_db.consulta_tabella(nome_tabella, colonne, condizione)
            if not risultato["success"]:
                return f"Errore: {risultato['error']}"
                
            if not risultato["data"]:
                return "Nessun risultato trovato."
                
            # Formatta i risultati in un formato semplice con trattini
            dati = risultato["data"]
            if not dati:
                return "Nessun dato trovato."
                
            # Ottieni i nomi delle colonne dal primo record
            colonne = list(dati[0].keys())
            
            # Crea la risposta con il formato desiderato
            output = []
            
            # Aggiungi il messaggio iniziale
            if risposta_testuale:
                output.append(f"{risposta_testuale}\n")
            
            # Crea l'intestazione con le colonne
            header = []
            for col in colonne:
                header.append(str(col))
            output.append(" - ".join(header))  # Prima riga: nomi delle colonne
            output.append("")  # Riga vuota dopo l'intestazione
            
            # Aggiungi ogni riga di dati
            for riga in dati:
                row_data = []
                for col in colonne:
                    val = str(riga.get(col, ""))
                    row_data.append(val)
                output.append(" - ".join(row_data))
                output.append("")  # Riga vuota dopo ogni riga di dati
            
            # Rimuovi l'ultima riga vuota se presente
            if output and output[-1] == "":
                output.pop()
                
            # Unisci tutto con newline
            return "\n".join(output)
            
        elif azione == "elenca_tabelle":
            risultato = gestione_db.elenca_tabelle()
            if risultato["success"]:
                return json.dumps({"risposta": risposta_testuale, "tabelle": risultato["data"]}, indent=2)
            return f"Errore: {risultato['error']}"
            
        elif azione == "descrivi_tabella":
            risultato = gestione_db.descrivi_tabella(nome_tabella)
            if risultato["success"]:
                return json.dumps({"risposta": risposta_testuale, "struttura": risultato["data"]}, indent=2)
            return f"Errore: {risultato['error']}"
            
        elif azione == "esporta_tabella":
            file_destinazione = dati.get("file_destinazione", "")
            formato = dati.get("formato", "csv")
            risultato = gestione_db.esporta_tabella(nome_tabella, file_destinazione, formato)
            if risultato["success"]:
                return risposta_testuale
            return f"Errore durante l'esportazione: {risultato['error']}"

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
            
            if risultato["success"]:
                return risposta_testuale
            return f"Errore durante la modifica della tabella: {risultato['error']}"
            
        else:
            return risposta_testuale or f"Azione '{azione}' non riconosciuta."
        
    except Exception as e:
        return f"Errore durante l'esecuzione dell'azione '{azione}': {e}"


if __name__ == "__main__":
    # Test di funzionamento
    print("=== TEST AGENTE ===")
    print("API Endpoint:", API_ENDPOINT)
    print("Modello:", DEFAULT_MODEL 
)
    
    test_message = "Ciao agente, puoi confermare di funzionare correttamente rispondendo solo con 'OK'?"
    print("\nInvio messaggio di test:", test_message)
    
    risposta = chiedi_all_agente(test_message)
    print("\nRisposta grezza dall'API:", risposta)
    
    risultato = esegui_azione(risposta)
    print("\nRisultato finale:", risultato)