import pandas as pd
import numpy as np

class RiskManager:
    def __init__(self, 
                 stop_loss_pct=0.02,      # Stop-Loss à -2%
                 take_profit_pct=0.04,    # Take-Profit à +4%
                 max_daily_loss_pct=0.05, # Perte max journalière : 5%
                 max_position_size=0.95): # 95% max du capital par position
        
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_position_size = max_position_size
        
        # Tracking pour la gestion quotidienne
        self.daily_pnl = 0
        self.last_trade_date = None
    
    def calculer_stop_loss(self, prix_achat: float) -> float:
        """Calcule le prix de Stop-Loss."""
        return prix_achat * (1 - self.stop_loss_pct)
    
    def calculer_take_profit(self, prix_achat: float) -> float:
        """Calcule le prix de Take-Profit."""
        return prix_achat * (1 + self.take_profit_pct)
    
    def verifier_stop_loss(self, prix_actuel: float, prix_achat: float) -> bool:
        """Vérifie si le Stop-Loss a été touché."""
        if prix_achat == 0:
            return False
        return prix_actuel <= prix_achat * (1 - self.stop_loss_pct)
    
    def verifier_take_profit(self, prix_actuel: float, prix_achat: float) -> bool:
        """Vérifie si le Take-Profit a été touché."""
        if prix_achat == 0:
            return False
        return prix_actuel >= prix_achat * (1 + self.take_profit_pct)
    
    def calculer_taille_position(self, capital: float, prix_actuel: float) -> float:
        """
        Calcule la taille optimale de position.
        Utilise 95% du capital maximum.
        """
        capital_utilise = capital * self.max_position_size
        return capital_utilise / prix_actuel
    
    def verifier_limite_quotidienne(self, profit: float, timestamp: pd.Timestamp, capital_actuel: float) -> bool:
        """
        Vérifie si on a atteint la limite de perte quotidienne.
        Retourne True si on peut encore trader, False sinon.
        """
        date_actuelle = timestamp.date()
        
        # Nouveau jour → reset du PnL quotidien
        if self.last_trade_date != date_actuelle:
            self.daily_pnl = 0
            self.last_trade_date = date_actuelle
        
        # Ajouter le profit/perte du trade
        self.daily_pnl += profit
        
        # Vérifier la limite
        perte_max = capital_actuel * self.max_daily_loss_pct
        if self.daily_pnl < -perte_max:
            return False
        
        return True
    
    def get_parametres(self) -> dict:
        """Retourne les paramètres actuels pour affichage."""
        return {
            'stop_loss_pct': f"{self.stop_loss_pct*100:.1f}%",
            'take_profit_pct': f"{self.take_profit_pct*100:.1f}%",
            'max_daily_loss_pct': f"{self.max_daily_loss_pct*100:.1f}%",
            'max_position_size': f"{self.max_position_size*100:.0f}%"
        }