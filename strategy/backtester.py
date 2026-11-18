import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from analysis.technical import calculer_indicateurs, analyser_signal
from strategy.risk_manager import RiskManager


class Backtester:
    def __init__(self, symbole="BTC/USD", capital_initial=10000, frais_transaction=0.001):
        """
        Initialise le backtester.
        
        Args:
            symbole: Paire de trading (ex: "BTC/USD")
            capital_initial: Capital de départ en USD
            frais_transaction: Frais par transaction (0.001 = 0.1%)
        """
        self.symbole = symbole
        self.capital_initial = capital_initial
        self.frais_transaction = frais_transaction
        self.trades = []
        self.equity_curve = []
        
    def recuperer_donnees_historiques(self, mois=6, timeframe='1h'):
        """
        Récupère les données historiques depuis Binance.
        
        Args:
            mois: Nombre de mois de données à récupérer
            timeframe: Intervalle de temps (1h, 4h, 1d)
        
        Returns:
            DataFrame avec les données OHLCV
        """
        print(f"📥 Récupération de {mois} mois de données pour {self.symbole}...")
        
        exchange = ccxt.binance()
        
        # Calculer le timestamp de début (en millisecondes)
        depuis = int((datetime.now() - timedelta(days=mois*30)).timestamp() * 1000)
        
        toutes_bougies = []
        limite = 1000  # Binance limite à 1000 bougies par requête
        
        while True:
            try:
                bougies = exchange.fetch_ohlcv(
                    self.symbole, 
                    timeframe=timeframe, 
                    since=depuis, 
                    limit=limite
                )
                
                if not bougies:
                    break
                
                toutes_bougies.extend(bougies)
                
                # Mettre à jour le timestamp pour la prochaine requête
                depuis = bougies[-1][0] + 1
                
                # Si on a récupéré moins que la limite, on a atteint la fin
                if len(bougies) < limite:
                    break
                    
            except Exception as e:
                print(f"❌ Erreur lors de la récupération : {e}")
                break
        
        # Convertir en DataFrame
        df = pd.DataFrame(toutes_bougies, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        print(f"✅ {len(df)} bougies récupérées ({df['timestamp'].min()} à {df['timestamp'].max()})")
        
        return df
    
    def simuler_strategie(self, df: pd.DataFrame):
        """
        Simule la stratégie sur les données historiques.
        Utilise uniquement les données disponibles à chaque moment (pas de look-ahead bias).
        """
         # Initialiser le gestionnaire de risque
        risk_manager = RiskManager(
            stop_loss_pct=0.02,      # -2%
            take_profit_pct=0.04,    # +4%
            max_daily_loss_pct=0.05, # -5% max par jour
            max_position_size=0.95
        )

        print(f"\n🔄 Simulation de la stratégie sur {len(df)} bougies...")
        
        capital = self.capital_initial
        position = 0  # Quantité d'actif détenu
        prix_achat = 0
        trading_suspendu = False
        
        # On a besoin d'au moins 50 bougies pour calculer les indicateurs
        debut_simulation = 50
        
        for i in range(debut_simulation, len(df)):
            # Données disponibles jusqu'à ce moment (pas de futur !)
            df_historique = df.iloc[:i+1]
            
            # Calculer les indicateurs
            df_ind = calculer_indicateurs(df_historique)
            
            # Analyser le signal
            analyse = analyser_signal(df_ind)
            
            signal = analyse['signal']
            force = analyse['force']
            prix_actuel = df.iloc[i]['close']
            timestamp = df.iloc[i]['timestamp']
            
            # Enregistrer l'équity (valeur totale du portefeuille)
            equity = capital + (position * prix_actuel)
            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': equity,
                'prix': prix_actuel,
                'signal': signal,
                'force': force
            })
            
            # Logique de trading avec risk management
            # Si on a une position ouverte
            if position > 0:
                # Vérifier Stop-Loss
                if risk_manager.verifier_stop_loss(prix_actuel, prix_achat):
                    # Stop-Loss touché → Vendre immédiatement
                    montant_vente = position * prix_actuel
                    frais = montant_vente * self.frais_transaction
                    profit = montant_vente - (position * prix_achat)
                    capital += (montant_vente - frais)
                    
                    self.trades.append({
                        'timestamp': timestamp,
                        'type': 'VENTE (STOP-LOSS)',
                        'prix': prix_actuel,
                        'quantite': position,
                        'frais': frais,
                        'profit': profit,
                        'force': force
                    })
                    
                    # Vérifier limite quotidienne
                    if not risk_manager.verifier_limite_quotidienne(profit, timestamp, capital):
                        trading_suspendu = True
                    
                    position = 0
                    prix_achat = 0
                
                # Vérifier Take-Profit
                elif risk_manager.verifier_take_profit(prix_actuel, prix_achat):
                    # Take-Profit touché → Vendre et sécuriser le gain
                    montant_vente = position * prix_actuel
                    frais = montant_vente * self.frais_transaction
                    profit = montant_vente - (position * prix_achat)
                    capital += (montant_vente - frais)
                    
                    self.trades.append({
                        'timestamp': timestamp,
                        'type': 'VENTE (TAKE-PROFIT)',
                        'prix': prix_actuel,
                        'quantite': position,
                        'frais': frais,
                        'profit': profit,
                        'force': force
                    })
                    
                    # Vérifier limite quotidienne
                    if not risk_manager.verifier_limite_quotidienne(profit, timestamp, capital):
                        trading_suspendu = True
                    
                    position = 0
                    prix_achat = 0
                
                # Signal de VENTE (stratégie)
                elif signal == 'VENTE':
                    montant_vente = position * prix_actuel
                    frais = montant_vente * self.frais_transaction
                    profit = montant_vente - (position * prix_achat)
                    capital += (montant_vente - frais)
                    
                    self.trades.append({
                        'timestamp': timestamp,
                        'type': 'VENTE (SIGNAL)',
                        'prix': prix_actuel,
                        'quantite': position,
                        'frais': frais,
                        'profit': profit,
                        'force': force
                    })
                    
                    if not risk_manager.verifier_limite_quotidienne(profit, timestamp, capital):
                        trading_suspendu = True
                    
                    position = 0
                    prix_achat = 0
            
            # Si on n'a pas de position
            else:
                # Reset trading_suspendu si nouveau jour
                if self.trades:
                    dernier_trade_date = self.trades[-1]['timestamp'].date()
                    if timestamp.date() != dernier_trade_date:
                        trading_suspendu = False
                
                # Signal d'ACHAT et trading autorisé
                if signal == 'ACHAT' and not trading_suspendu:
                    quantite = risk_manager.calculer_taille_position(capital, prix_actuel)
                    montant_achat = quantite * prix_actuel
                    frais = montant_achat * self.frais_transaction
                    
                    capital -= (montant_achat + frais)
                    position = quantite
                    prix_achat = prix_actuel
                    
                    self.trades.append({
                        'timestamp': timestamp,
                        'type': 'ACHAT',
                        'prix': prix_actuel,
                        'quantite': quantite,
                        'frais': frais,
                        'force': force
                    })
        
        # Si on a encore une position à la fin, la clôturer au dernier prix
        if position > 0:
            dernier_prix = df.iloc[-1]['close']
            montant_vente = position * dernier_prix
            frais = montant_vente * self.frais_transaction
            capital += (montant_vente - frais)
            
            self.trades.append({
                'timestamp': df.iloc[-1]['timestamp'],
                'type': 'VENTE (FIN)',
                'prix': dernier_prix,
                'quantite': position,
                'frais': frais,
                'profit': montant_vente - (position * prix_achat),
                'force': 0
            })
        
        print(f"✅ Simulation terminée : {len(self.trades)} trades effectués")
        
        return capital
    
    def calculer_metriques(self, capital_final: float):
        """
        Calcule les métriques de performance.
        """
        if not self.equity_curve:
            return {}
        
        df_equity = pd.DataFrame(self.equity_curve)
        
        # Profit total
        profit_total = capital_final - self.capital_initial
        rendement_pct = (profit_total / self.capital_initial) * 100
        
        # Séparer les trades ACHAT et VENTE (tous types de VENTE)
        trades_achat = [t for t in self.trades if 'ACHAT' in t['type']]
        trades_vente = [t for t in self.trades if 'VENTE' in t['type']]  
        
        # Win rate (pourcentage de trades gagnants)
        trades_gagnants = [t for t in trades_vente if t.get('profit', 0) > 0]
        trades_perdants = [t for t in trades_vente if t.get('profit', 0) < 0]
        trades_neutres = [t for t in trades_vente if t.get('profit', 0) == 0]

        win_rate = (len(trades_gagnants) / len(trades_vente) * 100) if trades_vente else 0
        
        # Statistiques par type de vente
        stop_loss_count = len([t for t in trades_vente if 'STOP-LOSS' in t['type']])
        take_profit_count = len([t for t in trades_vente if 'TAKE-PROFIT' in t['type']])
        signal_count = len([t for t in trades_vente if 'SIGNAL' in t['type']])

        # Drawdown maximum (pire perte depuis un sommet)
        df_equity['peak'] = df_equity['equity'].cummax()
        df_equity['drawdown'] = (df_equity['equity'] - df_equity['peak']) / df_equity['peak'] * 100
        drawdown_max = df_equity['drawdown'].min()
        
        # Sharpe Ratio (simplifié)
        df_equity['returns'] = df_equity['equity'].pct_change()
        sharpe_ratio = (df_equity['returns'].mean() / df_equity['returns'].std() * np.sqrt(252)) if df_equity['returns'].std() > 0 else 0
        
        # Profit factor (ratio profit/perte)
        profits = [t['profit'] for t in trades_gagnants]
        pertes = [abs(t['profit']) for t in trades_perdants]
        
        profit_moyen = np.mean(profits) if profits else 0
        perte_moyenne = np.mean(pertes) if pertes else 0
        profit_factor = profit_moyen / perte_moyenne if perte_moyenne > 0 else 0
        
        return {
            'capital_initial': self.capital_initial,
            'capital_final': capital_final,
            'profit_total': profit_total,
            'rendement_pct': rendement_pct,
            'nombre_trades': len(trades_achat),
            'trades_gagnants': len(trades_gagnants),
            'trades_perdants': len(trades_vente) - len(trades_gagnants),
            'win_rate': win_rate,
            'drawdown_max': drawdown_max,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor,
            'profit_moyen': profit_moyen,
            'perte_moyenne': perte_moyenne,
            'stop_loss_count': stop_loss_count,
            'take_profit_count': take_profit_count,
            'signal_count': signal_count
        }
    
    def afficher_rapport(self, metriques: dict):
        """
        Affiche un rapport détaillé des performances (version améliorée).
        """
        print("\n" + "="*70)
        print("📊 RAPPORT DE BACKTESTING")
        print("="*70)
        
        print(f"\n💰 CAPITAL :")
        print(f"   Initial : ${metriques['capital_initial']:,.2f}")
        print(f"   Final : ${metriques['capital_final']:,.2f}")
        print(f"   Profit/Perte : ${metriques['profit_total']:,.2f} ({metriques['rendement_pct']:+.2f}%)")
        
        print(f"\n📈 TRADES :")
        print(f"   Nombre total : {metriques['nombre_trades']}")
        print(f"   Gagnants : {metriques['trades_gagnants']}")
        print(f"   Perdants : {metriques['trades_perdants']}")
        print(f"   Neutres : {metriques.get('trades_neutres', 0)}")
        print(f"   Win Rate : {metriques['win_rate']:.1f}%")
        
        # NOUVEAU : Répartition des sorties
        print(f"\n🚪 SORTIES DE POSITION :")
        print(f"   🛑 Stop-Loss : {metriques.get('stop_loss_count', 0)}")
        print(f"   🎯 Take-Profit : {metriques.get('take_profit_count', 0)}")
        print(f"   📊 Signal : {metriques.get('signal_count', 0)}")
        
        print(f"\n⚖️ RISQUE :")
        print(f"   Drawdown Maximum : {metriques['drawdown_max']:.2f}%")
        print(f"   Sharpe Ratio : {metriques['sharpe_ratio']:.2f}")
        
        print(f"\n📊 QUALITÉ :")
        print(f"   Profit Moyen (gagnants) : ${metriques['profit_moyen']:,.2f}")
        print(f"   Perte Moyenne (perdants) : ${metriques['perte_moyenne']:,.2f}")
        
        # Gérer le cas où profit_factor = inf
        pf = metriques['profit_factor']
        pf_str = f"{pf:.2f}" if pf != float('inf') else "∞ (parfait)"
        print(f"   Profit Factor : {pf_str}")
        
        # Interprétation
        print(f"\n💡 INTERPRÉTATION :")
        
        if metriques['rendement_pct'] > 0:
            print(f"   ✅ Stratégie RENTABLE")
        elif metriques['rendement_pct'] > -2:
            print(f"   ⚠️ Stratégie PRESQUE à l'équilibre ({metriques['rendement_pct']:.2f}%)")
        else:
            print(f"   ❌ Stratégie DÉFICITAIRE")
        
        if metriques['win_rate'] >= 50:
            print(f"   ✅ Win Rate correct ({metriques['win_rate']:.1f}%)")
        else:
            print(f"   ⚠️ Win Rate faible ({metriques['win_rate']:.1f}%)")
        
        if metriques['drawdown_max'] > -20:
            print(f"   ✅ Drawdown acceptable ({metriques['drawdown_max']:.2f}%)")
        else:
            print(f"   ❌ Drawdown trop élevé ({metriques['drawdown_max']:.2f}%)")
        
        if metriques['sharpe_ratio'] > 1:
            print(f"   ✅ Sharpe Ratio excellent ({metriques['sharpe_ratio']:.2f})")
        elif metriques['sharpe_ratio'] > 0:
            print(f"   ⚠️ Sharpe Ratio moyen ({metriques['sharpe_ratio']:.2f})")
        else:
            print(f"   ❌ Sharpe Ratio négatif ({metriques['sharpe_ratio']:.2f})")
        
        if pf == float('inf'):
            print(f"   ✅ Profit Factor parfait (aucune perte)")
        elif pf > 1.5:
            print(f"   ✅ Profit Factor excellent ({pf:.2f})")
        elif pf > 1:
            print(f"   ⚠️ Profit Factor acceptable ({pf:.2f})")
        else:
            print(f"   ❌ Profit Factor insuffisant ({pf:.2f})")
    
    print("="*70)
def lancer_backtest():
    """
    Fonction principale pour lancer le backtest.
    """
    # Configuration
    SYMBOLE = "BTC/USD"
    MOIS = 6  # Tester sur 6 mois
    CAPITAL_INITIAL = 10000  # 10 000 $
    FRAIS = 0.001  # 0.1% par transaction (frais Binance standard)
    
    print("🚀 LANCEMENT DU BACKTEST")
    print(f"   Symbole : {SYMBOLE}")
    print(f"   Période : {MOIS} mois")
    print(f"   Capital initial : ${CAPITAL_INITIAL:,.2f}")
    print(f"   Frais : {FRAIS*100}%")
    
    # Créer le backtester
    backtester = Backtester(
        symbole=SYMBOLE,
        capital_initial=CAPITAL_INITIAL,
        frais_transaction=FRAIS
    )
    
    # Récupérer les données historiques
    df = backtester.recuperer_donnees_historiques(mois=MOIS, timeframe='1h')
    
    if len(df) < 100:
        print("❌ Pas assez de données pour un backtest fiable")
        return
    
    # Simuler la stratégie
    capital_final = backtester.simuler_strategie(df)
    
    # Calculer les métriques
    metriques = backtester.calculer_metriques(capital_final)
    
    # Afficher le rapport
    backtester.afficher_rapport(metriques)
    
    # Sauvegarder les résultats
    df_equity = pd.DataFrame(backtester.equity_curve)
    df_trades = pd.DataFrame(backtester.trades)
    
    df_equity.to_csv('backtest_equity_curve.csv', index=False)
    df_trades.to_csv('backtest_trades.csv', index=False)
    
    print(f"\n💾 Résultats sauvegardés :")
    print(f"   - backtest_equity_curve.csv (courbe d'équity)")
    print(f"   - backtest_trades.csv (liste des trades)")


if __name__ == "__main__":
    lancer_backtest()