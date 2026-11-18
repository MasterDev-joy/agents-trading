import ccxt
import pandas as pd
from analysis.technical import calculer_indicateurs, analyser_signal
from analysis.sentiment import recuperer_actualites_crypto, analyser_sentiment, integrer_sentiment_signal

print("🔄 Récupération des données techniques...")
exchange = ccxt.binance()
ohlcv = exchange.fetch_ohlcv('BTC/USD', timeframe='1h', limit=100)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df_ind = calculer_indicateurs(df)
analyse_tech = analyser_signal(df_ind)

print("📰 Récupération des actualités...")
titres = recuperer_actualites_crypto("BTC", limit=5)
print(f"   {len(titres)} actualités trouvées")

print("🧠 Analyse du sentiment par l'IA...")
analyse_sent = analyser_sentiment(titres)

print("🎯 Combinaison des analyses...")
signal_final = integrer_sentiment_signal(analyse_tech, analyse_sent)

print("\n" + "=" * 60)
print("📊 ANALYSE COMPLÈTE BTC/USD")
print("=" * 60)
print(f"💰 Prix : {analyse_tech['prix']:.2f} $")
print(f"\n📈 ANALYSE TECHNIQUE :")
print(f"   Signal : {analyse_tech['signal']}")
print(f"   Force : {analyse_tech['force']}")
print(f"   Raisons : {', '.join(analyse_tech['raisons'])}")

print(f"\n📰 ANALYSE DE SENTIMENT :")
print(f"   Score : {analyse_sent['score']:.2f}")
print(f"   Confiance : {analyse_sent['confiance']:.2f}")
print(f"   Raison : {analyse_sent['raison']}")

print(f"\n🎯 SIGNAL FINAL :")
print(f"   Signal : {signal_final['signal']}")
print(f"   Force combinée : {signal_final['force']}")
print(f"   (Technique: {signal_final['force_technique']}, Sentiment: {signal_final['force_sentiment']})")
print("=" * 60)