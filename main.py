import sys
import os
import time
import datetime
import ccxt
import pandas as pd

# Import de nos modules
from analysis.technical import calculer_indicateurs, analyser_signal
from analysis.sentiment import recuperer_actualites_crypto, analyser_sentiment, integrer_sentiment_signal
from monitoring.discord_bot import envoyer_alerte_discord, formater_alerte

# Configuration
SYMBOL = "BTC/USD"
TIMEFRAME = "1h"
INTERVAL_MINUTES = 60  # Analyse toutes les 60 minutes
SEUIL_ALERTE = 40  # Alerte uniquement si force >= 40 ou <= -40

def analyser_marche() -> dict:
    """
    Effectue une analyse complète du marché (technique + sentiment).
    Retourne un dictionnaire avec tous les résultats.
    """
    print(f"\n{'='*60}")
    print(f"🔍 ANALYSE DU MARCHÉ - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # 1. Récupération des données techniques
    print("📊 Récupération des données techniques...")
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_ind = calculer_indicateurs(df)
        analyse_tech = analyser_signal(df_ind)
        print(f"   ✅ Prix actuel : ${analyse_tech['prix']:,.2f}")
        print(f"   ✅ Signal technique : {analyse_tech['signal']} (force: {analyse_tech['force']})")
    except Exception as e:
        print(f"   ❌ Erreur récupération données : {e}")
        return None
    
    # 2. Récupération des actualités
    print("📰 Récupération des actualités...")
    try:
        titres = recuperer_actualites_crypto("BTC", limit=5)
        print(f"   ✅ {len(titres)} actualités trouvées")
    except Exception as e:
        print(f"   ⚠️ Erreur actualités : {e}")
        titres = []
    
    # 3. Analyse du sentiment
    print("🧠 Analyse du sentiment...")
    try:
        if titres:
            analyse_sent = analyser_sentiment(titres)
            print(f"   ✅ Score sentiment : {analyse_sent['score']:.2f} (confiance: {analyse_sent['confiance']:.2f})")
        else:
            analyse_sent = {"score": 0.0, "raison": "Pas d'actualités", "confiance": 0.0}
    except Exception as e:
        print(f"   ⚠️ Erreur analyse sentiment : {e}")
        analyse_sent = {"score": 0.0, "raison": f"Erreur: {e}", "confiance": 0.0}
    
    # 4. Combinaison des analyses
    print("🎯 Combinaison des analyses...")
    signal_final = integrer_sentiment_signal(analyse_tech, analyse_sent)
    
    # Ajout du prix pour le formatage Discord
    signal_final['prix'] = analyse_tech['prix']
    signal_final['signal_technique'] = analyse_tech['signal']
    
    print(f"   ✅ Signal final : {signal_final['signal']} (force: {signal_final['force']})")
    print(f"{'='*60}\n")
    
    return signal_final


def boucle_principale():
    """
    Boucle principale de l'agent trading.
    Tourne en continu et envoie des alertes Discord sur signaux forts.
    """
    print("🤖 AGENT TRADING DÉMARRÉ")
    print(f"📊 Symbole : {SYMBOL}")
    print(f"⏱️ Intervalle : {INTERVAL_MINUTES} minutes")
    print(f"🎯 Seuil d'alerte : {SEUIL_ALERTE}")
    print(f"💡 Appuyez sur Ctrl+C pour arrêter\n")
    
    # Envoi d'un message de démarrage sur Discord
    message_start = f"""
🤖 **Agent Trading Démarré**

📊 Surveillance de **{SYMBOL}** activée
⏱️ Analyse toutes les **{INTERVAL_MINUTES} minutes**
🎯 Alerte si force ≥ {SEUIL_ALERTE}

⏰ Démarré à : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    envoyer_alerte_discord(message_start.strip())
    
    try:
        while True:
            # Analyse du marché
            resultat = analyser_marche()
            
            if resultat is None:
                print("⚠️ Analyse échouée, on attend le prochain cycle\n")
            else:
                # Vérifier si on doit envoyer une alerte
                force = abs(resultat['force'])
                signal = resultat['signal']
                
                if force >= SEUIL_ALERTE and signal in ['ACHAT', 'VENTE']:
                    print(f"🚨 SIGNAL FORT DÉTECTÉ : {signal} (force: {resultat['force']})")
                    print("📱 Envoi de l'alerte Discord...")
                    
                    message_alerte = formater_alerte(resultat, SYMBOL)
                    envoyer_alerte_discord(message_alerte)
                else:
                    print(f"😴 Signal faible ({signal}, force: {resultat['force']}), pas d'alerte")
            
            # Attente avant le prochain cycle
            print(f"\n💤 Prochaine analyse dans {INTERVAL_MINUTES} minutes...")
            time.sleep(INTERVAL_MINUTES * 60)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt de l'agent trading demandé par l'utilisateur")
        message_stop = f"""
🛑 **Agent Trading Arrêté**

⏰ Arrêté à : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        envoyer_alerte_discord(message_stop.strip())
        print("✅ Agent arrêté proprement")


if __name__ == "__main__":
    boucle_principale()