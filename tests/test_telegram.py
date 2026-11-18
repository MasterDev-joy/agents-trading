import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitoring.telegram_bot import envoyer_message_telegram

# Test simple
message_test = """
🤖 <b>Test Agent Trading</b>

✅ Si vous recevez ce message, votre bot Telegram fonctionne !

💡 Prochaine étape : L'agent vous enverra automatiquement des alertes de trading.
"""

print("📱 Envoi d'un message de test sur Telegram...")
succes = envoyer_message_telegram(message_test)

if succes:
    print("✅ Test réussi ! Vérifiez votre téléphone.")
else:
    print("❌ Test échoué. Vérifiez votre fichier .env")