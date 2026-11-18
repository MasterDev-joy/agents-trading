import ccxt
import pandas as pd
from analysis.technical import calculer_indicateurs, analyser_signal

# 1. Récupérer les données (comme avant)
exchange = ccxt.binance()
ohlcv = exchange.fetch_ohlcv('BTC/USD', timeframe='1h', limit=100)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

# 2. Calculer les indicateurs
df_ind = calculer_indicateurs(df)

# 3. Analyser le signal
analyse = analyser_signal(df_ind)

# 4. Afficher les résultats
print("=" * 60)
print("📊 ANALYSE TECHNIQUE BTC/USD")
print("=" * 60)
print(f"💰 Prix actuel : {analyse['prix']:.2f} $")
print(f"\n📈 INDICATEURS :")
print(f"   RSI (14) : {analyse['indicateurs']['RSI']}")
print(f"   MACD Histogramme : {analyse['indicateurs']['MACD_Hist']}")
print(f"\n🎯 SIGNAL : {analyse['signal']}")
print(f"   Force : {analyse['force']}")
print(f"\n💡 RAISONS :")
for raison in analyse['raisons']:
    print(f"   • {raison}")
print("=" * 60)