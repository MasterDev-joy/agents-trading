# test_data.py
import ccxt
import pandas as pd

# Connexion à Binance (pas besoin de clé API pour les données publiques)
exchange = ccxt.binance()

# Récupérer les 100 dernières bougies d'1 heure pour BTC/USD
ohlcv = exchange.fetch_ohlcv('BTC/USD', timeframe='1h', limit=100)

# Convertir en DataFrame pandas
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Prix actuel
prix_actuel = df['close'].iloc[-1]
print(f"💰 Prix actuel BTC/USD : {prix_actuel:.2f} $")

# Tendance sur les 10 dernières heures
prix_10h_avant = df['close'].iloc[-10]
variation = ((prix_actuel - prix_10h_avant) / prix_10h_avant) * 100
tendance = "📈 HAUSSE" if variation > 0 else "📉 BAISSE"
print(f"{tendance} de {abs(variation):.2f}% sur les 10 dernières heures")