import pandas as pd
import pandas_ta as ta

def calculer_indicateurs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute les indicateurs techniques au DataFrame.
    Entrée : DataFrame avec colonnes ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    Sortie : DataFrame enrichi avec RSI, MACD, Bollinger Bands
    """
    # Copie pour ne pas modifier l'original
    df_ind = df.copy()
    
    # 1. RSI (Relative Strength Index) - Détecte surachat/survente
    # RSI < 30 = survendu (potentiel achat)
    # RSI > 70 = suracheté (potentiel vente)
    df_ind['RSI'] = ta.rsi(df_ind['close'], length=14)
    
    # 2. MACD (Moving Average Convergence Divergence) - Confirme la tendance
    macd = ta.macd(df_ind['close'], fast=12, slow=26, signal=9)
    df_ind['MACD'] = macd.iloc[:, 0]  # Ligne MACD
    df_ind['MACD_Signal'] = macd.iloc[:, 1]  # Ligne de signal
    df_ind['MACD_Hist'] = macd.iloc[:, 2]  # Histogramme
    
    # 3. Bandes de Bollinger - Mesure la volatilité
    bbands = ta.bbands(df_ind['close'], length=20, std=2)
    df_ind['BB_Lower'] = bbands.iloc[:, 0]  # Bande supérieure
    df_ind['BB_Middle'] = bbands.iloc[:, 1]  # Moyenne mobile
    df_ind['BB_Upper'] = bbands.iloc[:, 2]  # Bande inférieure
    
    # 4. Moyennes mobiles simples (tendance long terme)
    df_ind['SMA_20'] = ta.sma(df_ind['close'], length=20)
    df_ind['SMA_50'] = ta.sma(df_ind['close'], length=50)
    
    return df_ind

def analyser_signal(df_ind: pd.DataFrame) -> dict:
    """
    Analyse les indicateurs et génère un signal simple.
    Retourne un dictionnaire avec l'analyse complète.
    """
    # Prend la dernière valeur (la plus récente)
    dernier = df_ind.iloc[-1]
    precedent = df_ind.iloc[-2]
    
    analyse = {
        'prix': dernier['close'],
        'indicateurs': {},
        'signal': 'NEUTRE',
        'force': 0,  # Score de -100 à +100
        'raisons': []
    }
    
    # Analyse RSI
    rsi = dernier['RSI']
    analyse['indicateurs']['RSI'] = round(rsi, 2)
    
    if rsi < 30:
        analyse['force'] += 30
        analyse['raisons'].append(f"RSI={rsi:.1f} (survendu)")
    elif rsi > 70:
        analyse['force'] -= 30
        analyse['raisons'].append(f"RSI={rsi:.1f} (suracheté)")
    
    # Analyse MACD
    macd_hist = dernier['MACD_Hist']
    macd_hist_prec = precedent['MACD_Hist']
    analyse['indicateurs']['MACD_Hist'] = round(macd_hist, 2)
    
    # Croisement MACD (signal d'achat/vente)
    if macd_hist > 0 and macd_hist_prec <= 0:
        analyse['force'] += 25
        analyse['raisons'].append("MACD croisement haussier")
    elif macd_hist < 0 and macd_hist_prec >= 0:
        analyse['force'] -= 25
        analyse['raisons'].append("MACD croisement baissier")
    
    # Analyse Bandes de Bollinger
    prix = dernier['close']
    bb_lower = dernier['BB_Lower']
    bb_upper = dernier['BB_Upper']
    
    if prix <= bb_lower:
        analyse['force'] += 20
        analyse['raisons'].append("Prix touche bande Bollinger inférieure")
    elif prix >= bb_upper:
        analyse['force'] -= 20
        analyse['raisons'].append("Prix touche bande Bollinger supérieure")
    
    # Détermination du signal final
    if analyse['force'] >= 40:
        analyse['signal'] = 'ACHAT'
    elif analyse['force'] <= -40:
        analyse['signal'] = 'VENTE'
    
    return analyse