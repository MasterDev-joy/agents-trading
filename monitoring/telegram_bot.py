import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def envoyer_message_telegram(message: str) -> bool:
    """
    Envoie un message via Telegram.
    Retourne True si succès, False sinon.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Erreur : TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID non configuré dans .env")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"  # Permet le formatage (gras, italique, etc.)
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Message Telegram envoyé avec succès")
            return True
        else:
            print(f"❌ Erreur Telegram : {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur réseau Telegram : {e}")
        return False


def formater_alerte(analyse_complete: dict, symbole: str = "BTC/USD") -> str:
    """
    Formate l'analyse complète en un message Telegram lisible.
    """
    signal = analyse_complete['signal']
    force = analyse_complete['force']
    prix = analyse_complete.get('prix', 0)
    
    # Emoji selon le signal
    emoji = "🟢" if signal == "ACHAT" else "🔴" if signal == "VENTE" else "⚪"
    
    message = f"""
{emoji} <b>ALERTE TRADING - {symbole}</b>

💰 <b>Prix actuel :</b> ${prix:,.2f}

📊 <b>Signal :</b> {signal}
💪 <b>Force :</b> {force}

📈 <b>Analyse Technique :</b>
   • Signal : {analyse_complete.get('signal_technique', 'N/A')}
   • Force : {analyse_complete.get('force_technique', 0)}

📰 <b>Analyse de Sentiment :</b>
   • Score : {analyse_complete.get('details_sentiment', {}).get('score', 0):.2f}
   • Confiance : {analyse_complete.get('details_sentiment', {}).get('confiance', 0):.2f}
   • Raison : {analyse_complete.get('details_sentiment', {}).get('raison', 'N/A')}

⏰ <b>Heure :</b> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return message.strip()