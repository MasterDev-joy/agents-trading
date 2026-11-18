import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitoring.discord_bot import envoyer_alerte_discord

# Test simple
message_test = """
🤖 **Test Agent Trading**

✅ Si vous voyez ce message dans Discord, votre webhook fonctionne !

💡 Prochaine étape : L'agent vous enverra automatiquement des alertes de trading quand il détecte un signal fort.
"""

print("📱 Envoi d'un message de test sur Discord...")
succes = envoyer_alerte_discord(message_test)

if succes:
    print("✅ Test réussi ! Vérifiez votre canal Discord #alertes-trading")
else:
    print("❌ Test échoué. Vérifiez l'URL du webhook dans monitoring/discord_bot.py")