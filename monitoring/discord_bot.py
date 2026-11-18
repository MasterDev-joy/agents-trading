import requests

WEBHOOK_URL = "https://discord.com/api/webhooks/1572008834501714000/NROKoeokdCrEor-0jPpuaV8G8HdKINm1kdXvkq-7iCOm6-swvinO5jyR8FzY__dezx7y"

def envoyer_alerte_discord(message: str) -> bool:
    """Envoie une alerte formatée sur Discord."""
    payload = {
        "content": message,
        "username": "Agent Trading Bot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712109.png" # Icône robot
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code in [200, 204]:
            print("✅ Alerte Discord envoyée avec succès !")
            return True
        else:
            print(f"❌ Erreur Discord : {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur réseau Discord : {e}")
        return False

def formater_alerte(analyse_complete: dict, symbole: str = "BTC/USD") -> str:
    signal = analyse_complete['signal']
    force = analyse_complete['force']
    prix = analyse_complete.get('prix', 0)
    
    emoji = "🟢" if signal == "ACHAT" else "🔴" if signal == "VENTE" else "⚪"
    
    # Formatage Markdown Discord
    message = f"""
{emoji} **ALERTE TRADING - {symbole}**

💰 **Prix actuel :** ${prix:,.2f}

📊 **Signal :** {signal}
💪 **Force :** {force}

📈 **Analyse Technique :** Force de {analyse_complete.get('force_technique', 0)}
📰 **Sentiment :** Score de {analyse_complete.get('details_sentiment', {}).get('score', 0):.2f} 
   _"{analyse_complete.get('details_sentiment', {}).get('raison', 'N/A')}"_

⏰ **Heure :** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    return message.strip()