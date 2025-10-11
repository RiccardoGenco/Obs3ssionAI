from datetime import datetime
from agent_core import chiedi_all_agente, esegui_azione

def salva_prenotazione(messaggio_utente, risposta_agente):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("prenotazioni.txt", "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] Utente: {messaggio_utente} | Agente: {risposta_agente}\n")

if __name__ == "__main__":
    print("  - v1.0 OBS3SSION")
    print("Scrivi 'esci' per terminare.")

    while True:
        messaggio = input("Tu > ")
        if messaggio.lower() == "esci":
            break
        risposta = chiedi_all_agente(messaggio)
        risposta_da_mostrare = esegui_azione(risposta)
        print("Agente >", risposta_da_mostrare)
        salva_prenotazione(messaggio, risposta)
