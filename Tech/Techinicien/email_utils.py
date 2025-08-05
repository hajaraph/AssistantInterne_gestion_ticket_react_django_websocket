from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
import logging

# Import SendGrid pour l'API directe (optionnel)
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

logger = logging.getLogger(__name__)
User = get_user_model()

def get_notification_recipients(ticket=None):
    """
    Fonction utilitaire pour récupérer les destinataires des notifications (techniciens et admins)
    Exclut le créateur du ticket pour éviter qu'il reçoive l'email destiné aux techniciens
    """
    # Récupérer tous les techniciens et admins actifs
    techniciens = User.objects.filter(role='technicien', statut='actif')
    admin_users = User.objects.filter(role='admin', statut='actif')

    # Combiner les destinataires
    destinataires = list(techniciens.values_list('email', flat=True)) + list(admin_users.values_list('email', flat=True))

    # Ajouter les emails d'admin configurés
    if hasattr(settings, 'ADMIN_EMAILS'):
        destinataires.extend(settings.ADMIN_EMAILS)

    # Supprimer les doublons et emails vides
    destinataires = list(set(filter(None, destinataires)))

    # Exclure le créateur du ticket s'il est fourni
    if ticket and ticket.utilisateur_createur and ticket.utilisateur_createur.email:
        if ticket.utilisateur_createur.email in destinataires:
            destinataires.remove(ticket.utilisateur_createur.email)
            logger.info(f"Email du créateur {ticket.utilisateur_createur.email} exclu des notifications techniciens")

    return destinataires

def auto_assign_urgent_ticket(ticket):
    """
    Assigne automatiquement un ticket urgent à un technicien disponible
    """
    if ticket.priorite in ['urgent', 'critique']:
        # Trouver un technicien disponible (avec le moins de tickets en cours)
        techniciens_disponibles = User.objects.filter(
            role='technicien',
            statut='actif'
        ).annotate(
            tickets_en_cours=Count('tickets_assignes', filter=Q(tickets_assignes__statut_ticket='en_cours'))
        ).order_by('tickets_en_cours')

        if techniciens_disponibles.exists():
            technicien_assigne = techniciens_disponibles.first()
            ticket.technicien_assigne = technicien_assigne
            ticket.statut_ticket = 'en_cours'
            ticket.save()

            # Créer un commentaire d'assignation automatique
            from .models import Commentaire
            Commentaire.objects.create(
                ticket=ticket,
                utilisateur_auteur=technicien_assigne,
                contenu=f"🚨 Ticket {ticket.get_priorite_display().lower()} assigné automatiquement à {technicien_assigne.get_full_name() or technicien_assigne.email}",
                type_action='assignation'
            )

            # Envoyer un email de notification urgente au technicien
            envoyer_email_urgence_technicien_smtp(ticket, technicien_assigne)

            return technicien_assigne
    return None

def envoyer_email_nouveau_ticket_sendgrid(ticket):
    """
    Envoie un email de notification via l'API SendGrid lors de la création d'un nouveau ticket
    """
    if not SENDGRID_AVAILABLE:
        logger.error("SendGrid n'est pas installé. Utilisez: pip install sendgrid")
        return envoyer_email_nouveau_ticket_smtp(ticket)  # Fallback sur SMTP

    try:
        # Utiliser la fonction utilitaire pour récupérer les destinataires (en excluant le créateur)
        destinataires = get_notification_recipients(ticket)

        if not destinataires:
            logger.warning("Aucun destinataire trouvé pour l'envoi d'email")
            return False

        # Configuration SendGrid
        sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        # Contenu HTML amélioré
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
                .ticket-info {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #007bff; }}
                .priority-{ticket.priorite} {{ border-left-color: {'#dc3545' if ticket.priorite == 'critique' else '#fd7e14' if ticket.priorite == 'urgent' else '#28a745' if ticket.priorite == 'faible' else '#6c757d'}; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎫 Nouveau Ticket de Support</h1>
                </div>
                
                <div class="content">
                    <div class="ticket-info priority-{ticket.priorite}">
                        <h3>Détails du ticket :</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 5px 0; font-weight: bold;">Titre :</td><td>{ticket.titre}</td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Description :</td><td>{ticket.description}</td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Priorité :</td><td><span style="background-color: {'#dc3545' if ticket.priorite == 'critique' else '#fd7e14' if ticket.priorite == 'urgent' else '#28a745' if ticket.priorite == 'faible' else '#6c757d'}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{ticket.get_priorite_display()}</span></td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Catégorie :</td><td>{ticket.categorie.nom_categorie}</td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Créé par :</td><td>{ticket.utilisateur_createur.get_full_name() or ticket.utilisateur_createur.email}</td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Département :</td><td>{ticket.utilisateur_createur.departement.nom_departement if ticket.utilisateur_createur.departement else 'Non spécifié'}</td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Date :</td><td>{ticket.date_creation.strftime('%d/%m/%Y à %H:%M')}</td></tr>
                            {f'<tr><td style="padding: 5px 0; font-weight: bold;">Équipement :</td><td>{ticket.equipement}</td></tr>' if ticket.equipement else ''}
                        </table>
                    </div>
                    
                    <p style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;">
                        ⚡ <strong>Action requise :</strong> Ce ticket nécessite une prise en charge rapide. 
                        Connectez-vous à l'interface d'administration pour l'assigner et commencer le traitement.
                    </p>
                </div>
                
                <div class="footer">
                    <p>Email automatique envoyé par le système de gestion des tickets</p>
                    <p>Système de Support Technique - {ticket.date_creation.strftime('%Y')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Créer le message pour chaque destinataire
        for destinataire in destinataires:
            message = Mail(
                from_email=Email(settings.DEFAULT_FROM_EMAIL, 'Support Technique TechSystem'),
                to_emails=To(destinataire),
                subject=f"🎫 Nouveau ticket #{ticket.id} - {ticket.titre}",
                html_content=Content("text/html", html_content)
            )

            # Envoyer l'email directement sans métadonnées
            response = sg.send(message)
            logger.info(f"Email SendGrid envoyé à {destinataire} - Status: {response.status_code}")

        logger.info(f"Emails SendGrid envoyés avec succès pour le ticket {ticket.id} à {len(destinataires)} destinataires")
        return True

    except Exception as e:
        logger.error(f"Erreur SendGrid pour le ticket {ticket.id}: {str(e)}")
        # Fallback sur la méthode SMTP standard
        return envoyer_email_nouveau_ticket_smtp(ticket)

def envoyer_email_confirmation_employe_sendgrid(ticket):
    """
    Envoie un email de confirmation à l'employé via SendGrid
    """
    if not SENDGRID_AVAILABLE:
        return envoyer_email_confirmation_employe_smtp(ticket)  # Fallback sur SMTP

    try:
        destinataire = ticket.utilisateur_createur.email

        if not destinataire:
            logger.warning(f"Aucun email trouvé pour l'utilisateur {ticket.utilisateur_createur}")
            return False

        sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
                .ticket-summary {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #28a745; }}
                .success-badge {{ background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; text-align: center; margin: 15px 0; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Ticket créé avec succès</h1>
                </div>
                
                <div class="content">
                    <p>Bonjour <strong>{ticket.utilisateur_createur.get_full_name() or ticket.utilisateur_createur.email}</strong>,</p>
                    
                    <div class="success-badge">
                        🎉 Votre demande de support a été enregistrée et sera traitée dans les plus brefs délais.
                    </div>
                    
                    <div class="ticket-summary">
                        <h3>📋 Récapitulatif de votre ticket :</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 8px 0; font-weight: bold; color: #495057;">Numéro :</td><td style="font-family: monospace; background-color: #e9ecef; padding: 4px 8px; border-radius: 3px;">#{ticket.id}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold; color: #495057;">Titre :</td><td>{ticket.titre}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold; color: #495057;">Priorité :</td><td><span style="background-color: {'#dc3545' if ticket.priorite == 'critique' else '#fd7e14' if ticket.priorite == 'urgent' else '#28a745' if ticket.priorite == 'faible' else '#6c757d'}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{ticket.get_priorite_display()}</span></td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold; color: #495057;">Statut :</td><td><span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{ticket.get_statut_ticket_display()}</span></td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold; color: #495057;">Date de création :</td><td>{ticket.date_creation.strftime('%d/%m/%Y à %H:%M')}</td></tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; border-left: 4px solid #17a2b8;">
                        <p><strong>📧 Prochaines étapes :</strong></p>
                        <ul>
                            <li>Vous recevrez une notification lorsqu'un technicien prendra en charge votre demande</li>
                            <li>Le technicien pourra vous contacter pour des informations supplémentaires</li>
                            <li>Vous serez informé de la résolution de votre problème</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Merci de faire confiance à notre service support</p>
                    <p>Service Support Technique - {ticket.date_creation.strftime('%Y')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email=Email(settings.DEFAULT_FROM_EMAIL, 'Support Technique TechSystem'),
            to_emails=To(destinataire),
            subject=f"✅ Confirmation - Ticket #{ticket.id} créé avec succès",
            html_content=Content("text/html", html_content)
        )

        # Envoyer l'email
        response = sg.send(message)
        logger.info(f"Email de confirmation SendGrid envoyé à {destinataire} - Status: {response.status_code}")
        return True

    except Exception as e:
        logger.error(f"Erreur SendGrid confirmation pour le ticket {ticket.id}: {str(e)}")
        return envoyer_email_confirmation_employe_smtp(ticket)

def envoyer_email_urgence_technicien_smtp(ticket, technicien):
    """
    Envoie un email d'urgence au technicien assigné
    """
    try:
        if not SENDGRID_AVAILABLE:
            return envoyer_email_urgence_technicien_smtp(ticket, technicien)

        sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        # Template spécial pour les urgences
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .urgent-banner {{ background-color: #ff6b6b; color: white; padding: 15px; text-align: center; font-weight: bold; font-size: 18px; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
                .ticket-info {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #dc3545; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 20px; }}
                .action-button {{ background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="urgent-banner">
                    🚨 INTERVENTION URGENTE REQUISE 🚨
                </div>
                
                <div class="header">
                    <h1>Ticket {ticket.get_priorite_display().upper()} Assigné</h1>
                </div>
                
                <div class="content">
                    <p><strong>Bonjour {technicien.get_full_name() or technicien.email},</strong></p>
                    
                    <p style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;">
                        ⚡ <strong>Action immédiate requise :</strong> Un ticket {ticket.get_priorite_display().lower()} vous a été automatiquement assigné.
                    </p>
                    
                    <div class="ticket-info">
                        <h3>Détails du ticket :</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 5px 0; font-weight: bold;">Numéro :</td><td>#{ticket.id}</td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Titre :</td><td>{ticket.titre}</td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Description :</td><td>{ticket.description}</td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Priorité :</td><td><span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{ticket.get_priorite_display()}</span></td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Employé :</td><td>{ticket.utilisateur_createur.get_full_name() or ticket.utilisateur_createur.email}</td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Contact :</td><td>{ticket.utilisateur_createur.telephone or 'Non renseigné'}</td></tr>
                            <tr><td style="padding: 5px 0; font-weight: bold;">Département :</td><td>{ticket.utilisateur_createur.departement.nom_departement if ticket.utilisateur_createur.departement else 'Non spécifié'}</td></tr>
                            {f'<tr><td style="padding: 5px 0; font-weight: bold;">Équipement :</td><td>{ticket.equipement}</td></tr>' if ticket.equipement else ''}
                        </table>
                    </div>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <p style="font-size: 16px; font-weight: bold; color: #dc3545;">
                            Temps de réponse attendu : {"Immédiat" if ticket.priorite == "critique" else "Sous 15 minutes"}
                        </p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Ce ticket vous a été automatiquement assigné en raison de sa priorité {ticket.get_priorite_display().lower()}</p>
                    <p>Système de Support Technique TechSystem - {ticket.date_creation.strftime('%Y')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email=Email(settings.DEFAULT_FROM_EMAIL, 'Support Technique TechSystem - URGENT'),
            to_emails=To(technicien.email),
            subject=f"🚨 URGENT - Ticket #{ticket.id} assigné - {ticket.titre}",
            html_content=Content("text/html", html_content)
        )

        response = sg.send(message)
        logger.info(f"Email d'urgence envoyé à {technicien.email} - Status: {response.status_code}")
        return True

    except Exception as e:
        logger.error(f"Erreur envoi email urgence pour ticket {ticket.id}: {str(e)}")
        return envoyer_email_urgence_technicien_smtp(ticket, technicien)

def envoyer_email_confirmation_employe_smtp(ticket):
    """
    Envoie un email de confirmation à l'employé via SMTP (fallback)
    """
    try:
        destinataire = ticket.utilisateur_createur.email

        if not destinataire:
            logger.warning(f"Aucun email trouvé pour l'utilisateur {ticket.utilisateur_createur}")
            return False

        sujet = f"Confirmation de création du ticket - {ticket.titre}"

        message_html = f"""
        <html>
        <body>
            <h2>✅ Votre ticket a été créé avec succès</h2>
            
            <p>Bonjour {ticket.utilisateur_createur.get_full_name() or ticket.utilisateur_createur.email},</p>
            
            <p>Votre demande de support a ét�� enregistrée et sera traitée dans les plus brefs délais.</p>
            
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Récapitulatif de votre ticket :</h3>
                <ul>
                    <li><strong>Numéro :</strong> #{ticket.id}</li>
                    <li><strong>Titre :</strong> {ticket.titre}</li>
                    <li><strong>Priorité :</strong> {ticket.get_priorite_display()}</li>
                    <li><strong>Statut :</strong> {ticket.get_statut_ticket_display()}</li>
                    <li><strong>Date de création :</strong> {ticket.date_creation.strftime('%d/%m/%Y à %H:%M')}</li>
                </ul>
            </div>
            
            <p>Vous recevrez une notification lorsqu'un technicien prendra en charge votre demande.</p>
            
            <hr>
            <p><em>Service Support Technique</em></p>
        </body>
        </html>
        """

        message_text = f"""
        Votre ticket a été créé avec succès

        Bonjour {ticket.utilisateur_createur.get_full_name() or ticket.utilisateur_createur.email},

        Votre demande de support a été enregistrée et sera traitée dans les plus brefs délais.

        Récapitulatif de votre ticket :
        - Numéro : #{ticket.id}
        - Titre : {ticket.titre}
        - Priorité : {ticket.get_priorite_display()}
        - Statut : {ticket.get_statut_ticket_display()}
        - Date de création : {ticket.date_creation.strftime('%d/%m/%Y à %H:%M')}

        Vous recevrez une notification lorsqu'un technicien prendra en charge votre demande.

        Service Support Technique
        """

        send_mail(
            subject=sujet,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinataire],
            html_message=message_html,
            fail_silently=False,
        )

        logger.info(f"Email de confirmation SMTP envoyé à {destinataire} pour le ticket {ticket.id}")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de confirmation SMTP pour le ticket {ticket.id}: {str(e)}")
        return False

# Fonctions SMTP de fallback (nommées différemment pour éviter la duplication)
def envoyer_email_nouveau_ticket_smtp(ticket):
    """
    Envoie un email de notification via SMTP lors de la création d'un nouveau ticket (fallback)
    """
    try:
        # Utiliser la fonction utilitaire pour récupérer les destinataires (en excluant le créateur)
        destinataires = get_notification_recipients(ticket)

        if not destinataires:
            logger.warning("Aucun destinataire trouvé pour l'envoi d'email")
            return False

        # Préparer le contenu de l'email
        sujet = f"Nouveau ticket créé - {ticket.titre}"

        # Contenu HTML de l'email
        message_html = f"""
        <html>
        <body>
            <h2>🎫 Nouveau Ticket de Support</h2>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>Détails du ticket :</h3>
                <ul>
                    <li><strong>Titre :</strong> {ticket.titre}</li>
                    <li><strong>Description :</strong> {ticket.description}</li>
                    <li><strong>Priorité :</strong> {ticket.get_priorite_display()}</li>
                    <li><strong>Catégorie :</strong> {ticket.categorie.nom_categorie}</li>
                    <li><strong>Créé par :</strong> {ticket.utilisateur_createur.get_full_name() or ticket.utilisateur_createur.email}</li>
                    <li><strong>Département :</strong> {ticket.utilisateur_createur.departement.nom_departement if ticket.utilisateur_createur.departement else 'Non spécifié'}</li>
                    <li><strong>Date de création :</strong> {ticket.date_creation.strftime('%d/%m/%Y à %H:%M')}</li>
                </ul>
                
                {f'<p><strong>Équipement concerné :</strong> {ticket.equipement}</p>' if ticket.equipement else ''}
            </div>
            
            <p>Ce ticket nécessite une prise en charge. Connectez-vous à l'interface d'administration pour l'assigner et commencer le traitement.</p>
            
            <hr>
            <p><em>Email automatique envoyé par le système de gestion des tickets</em></p>
        </body>
        </html>
        """

        # Message texte simple (fallback)
        message_text = f"""
        Nouveau Ticket de Support

        Titre: {ticket.titre}
        Description: {ticket.description}
        Priorité: {ticket.get_priorite_display()}
        Catégorie: {ticket.categorie.nom_categorie}
        Créé par: {ticket.utilisateur_createur.get_full_name() or ticket.utilisateur_createur.email}
        Département: {ticket.utilisateur_createur.departement.nom_departement if ticket.utilisateur_createur.departement else 'Non spécifié'}
        Date de création: {ticket.date_creation.strftime('%d/%m/%Y à %H:%M')}
        
        {f'Équipement concerné: {ticket.equipement}' if ticket.equipement else ''}
        
        Ce ticket nécessite une prise en charge.
        """

        # Envoyer l'email
        send_mail(
            subject=sujet,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinataires,
            html_message=message_html,
            fail_silently=False,
        )

        logger.info(f"Email SMTP envoyé avec succès pour le ticket {ticket.id} à {len(destinataires)} destinataires")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email SMTP pour le ticket {ticket.id}: {str(e)}")
        return False

# Fonctions principales utilisées par le signal
def envoyer_email_nouveau_ticket(ticket):
    """
    Fonction principale pour envoyer un email de notification de nouveau ticket
    Essaie SendGrid en premier, puis fallback sur SMTP
    """
    return envoyer_email_nouveau_ticket_sendgrid(ticket)

def envoyer_email_confirmation_employe(ticket):
    """
    Fonction principale pour envoyer un email de confirmation à l'employé
    Essaie SendGrid en premier, puis fallback sur SMTP
    """
    return envoyer_email_confirmation_employe_sendgrid(ticket)
