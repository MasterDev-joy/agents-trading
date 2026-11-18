import optuna
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Chemin vers les modules
from analysis.technical import calculer_indicateurs, analyser_signal
from strategy.risk_manager import RiskManager

def recuperer_donnees(symbole="BTC/USD", mois=6, timeframe='1h'):
    """Récupère les données (version simplifiée pour l'optimisation)"""
    print("📥 Chargement des données...")
    exchange = ccxt.binance()
    depuis = int((datetime.now() - timedelta(days=mois*30)).timestamp() * 1000)
    
    toutes_bougies = []
    while True:
        bougies = exchange.fetch_ohlcv(symbole, timeframe=timeframe, since=depuis, limit=1000)
        if not bougies: break
        toutes_bougies.extend(bougies)
        depuis = bougies[-1][0] + 1
        if len(bougies) < 1000: break
        
    df = pd.DataFrame(toutes_bougies, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def objectif(trial):
    """
    Fonction que Optuna va essayer de maximiser.
    Elle teste une combinaison de paramètres et retourne un score.
    """
    # 1. Optuna propose des valeurs aléatoires pour ce test
    sl_pct = trial.suggest_float('sl_pct', 0.02, 0.06)   # Teste entre 2% et 6%
    tp_pct = trial.suggest_float('tp_pct', 0.03, 0.10)   # Teste entre 3% et 10%
    
    # 2. Initialiser le Risk Manager avec ces valeurs
    risk_manager = RiskManager(
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
        max_daily_loss_pct=0.05,
        max_position_size=0.95
    )
    
    # 3. Simulation rapide
    capital = 10000.0
    position = 0
    prix_achat = 0
    frais = 0.001
    
    for i in range(50, len(df)):
        df_hist = df.iloc[:i+1]
        df_ind = calculer_indicateurs(df_hist)
        analyse = analyser_signal(df_ind)
        signal = analyse['signal']
        prix = df.iloc[i]['close']
        
        # Gestion de la position
        if position > 0:
            if risk_manager.verifier_stop_loss(prix, prix_achat):
                capital += (position * prix) * (1 - frais)
                position = 0
            elif risk_manager.verifier_take_profit(prix, prix_achat):
                capital += (position * prix) * (1 - frais)
                position = 0
            elif signal == 'VENTE':
                capital += (position * prix) * (1 - frais)
                position = 0
        else:
            if signal == 'ACHAT':
                position = (capital * 0.95) / prix
                capital -= (position * prix) * (1 + frais)
                prix_achat = prix

    # Clôturer à la fin si nécessaire
    if position > 0:
        capital += (position * df.iloc[-1]['close']) * (1 - frais)

    # 4. Calculer le score à maximiser
    profit_final = capital - 10000
    
    # Pénalité sévère si le Drawdown est trop élevé (on calcule une version simplifiée ici)
    # Pour faire simple, on maximise le profit, mais on rejette les stratégies qui perdent de l'argent
    if profit_final <= 0:
        return 0.0  # On ne veut pas de stratégies perdantes
    
    return profit_final

# --- LANCEMENT DE L'OPTIMISATION ---
if __name__ == "__main__":
    print("🚀 LANCEMENT DE L'OPTIMISATION DES PARAMÈTRES")
    print("Cela peut prendre 1 à 3 minutes selon votre PC...\n")
    
    # Récupérer les données une seule fois
    df = recuperer_donnees(mois=6, timeframe='1h')
    print(f"✅ {len(df)} bougies chargées. Début des tests...\n")
    
    # Créer une étude Optuna
    study = optuna.create_study(direction='maximize')
    
    # Lancer 100 essais (vous pouvez augmenter à 500 pour plus de précision)
    study.optimize(objectif, n_trials=100, show_progress_bar=True)
    
    print("\n" + "="*60)
    print("🏆 MEILLEURS PARAMÈTRES TROUVÉS")
    print("="*60)
    print(f"Stop-Loss optimal : {study.best_params['sl_pct']*100:.1f}%")
    print(f"Take-Profit optimal : {study.best_params['tp_pct']*100:.1f}%")
    print(f"Profit estimé sur 6 mois : +${study.best_value:,.2f}")
    print("="*60)
    print("\n💡 Copiez ces valeurs dans votre fichier strategy/risk_manager.py !")