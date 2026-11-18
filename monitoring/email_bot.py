import smtplib
from email.message import EmailMessage
import os

# À configurer avec vos infos
EMAIL_EXPEDITEUR = "votre_email@gmail.com"
MOT_DE_PASSE_APP = "votre_mot_de_passe_application_16_caracteres" # Pas votre mot de passe normal !
EMAIL_DESTINATAIRE = "votre_email@gmail.com" # Peut être le même

def envoyer_alerte_email(message: str) -> bool:
    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = "🤖 Alerte Agent Trading"
    msg['From'] = EMAIL_EXPEDITEUR
    msg['To'] = EMAIL_DESTINATAIRE

    try:
        # Connexion sécurisée au serveur SMTP de Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_APP)
            server.send_message(msg)
        print("✅ Email d'alerte envoyé avec succès !")
        return True
    except Exception as e:
        print(f"❌ Erreur d'envoi d'email : {e}")
        return False