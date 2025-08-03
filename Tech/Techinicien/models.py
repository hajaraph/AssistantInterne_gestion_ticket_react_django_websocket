from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging

# Use this for foreign key references to User
User = settings.AUTH_USER_MODEL

logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom User model that extends Django's AbstractUser"""
    ROLE_CHOICES = [
        ('employe', 'Employé'),
        ('technicien', 'Techinicien'),
        ('admin', 'Administrateur'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
    ]

    # Remove username field and use email instead
    username = None
    email = models.EmailField(_('email address'), unique=True)

    # Add custom fields
    telephone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employe')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='actif')
    departement = models.ForeignKey('Departement', on_delete=models.PROTECT, related_name='utilisateurs', null=True,
                                    blank=True)

    # Override groups and user_permissions with custom related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_role_display()})"

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


class Departement(models.Model):
    """Represents a department in the organization."""
    nom_departement = models.CharField(max_length=100, unique=True)
    responsable = models.CharField(max_length=200, blank=True, null=True)
    localisation = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nom_departement

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"


class Equipement(models.Model):
    """Represents equipment in the organization."""
    STATUT_EQUIPEMENT_CHOICES = [
        ('fonctionnel', 'Fonctionnel'),
        ('en panne', 'En panne'),
        ('en maintenance', 'En maintenance'),
    ]

    nom_modele = models.CharField(max_length=255)
    type_equipement = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, unique=True)
    departement = models.ForeignKey(Departement, on_delete=models.PROTECT, related_name='equipements')
    statut_equipement = models.CharField(max_length=20, choices=STATUT_EQUIPEMENT_CHOICES, default='fonctionnel')
    date_achat = models.DateField()
    garantie = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.nom_modele} ({self.numero_serie})"

    class Meta:
        verbose_name = "Équipement"
        verbose_name_plural = "Équipements"


class Categorie(models.Model):
    """Represents a ticket category."""
    nom_categorie = models.CharField(max_length=100, unique=True)
    description_categorie = models.TextField(blank=True, null=True)
    couleur_affichage = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return self.nom_categorie

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"


class Ticket(models.Model):
    """Represents a support ticket."""
    STATUT_TICKET_CHOICES = [
        ('ouvert', 'Ouvert'),
        ('en cours', 'En cours'),
        ('resolu', 'Résolu'),
        ('ferme', 'Fermé'),
        ('annule', 'Annulé'),
    ]

    PRIORITE_CHOICES = [
        ('faible', 'Faible'),
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('critique', 'Critique'),
    ]

    titre = models.CharField(max_length=255)
    description = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    statut_ticket = models.CharField(max_length=20, choices=STATUT_TICKET_CHOICES, default='ouvert')
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normal')
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='tickets')
    utilisateur_createur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='tickets_crees'
    )
    technicien_assigne = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_assignes',
        limit_choices_to={'role': 'technicien'}
    )
    equipement = models.ForeignKey(
        Equipement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets'
    )

    def __str__(self):
        return f"{self.titre} ({self.get_statut_ticket_display()})"

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"


class Commentaire(models.Model):
    """Represents a comment on a ticket."""
    TYPE_ACTION_CHOICES = [
        ('creation', 'Création'),
        ('assignation', 'Assignation'),
        ('changement_statut', 'Changement de statut'),
        ('ajout_commentaire', 'Commentaire'),
        ('resolution', 'Résolution'),
        ('fermeture', 'Fermeture'),
        # Nouveaux types pour le guidage à distance
        ('instruction', 'Instruction de guidage'),
        ('question_technicien', 'Question du technicien'),
        ('reponse_employe', 'Réponse de l\'employé'),
        ('confirmation_etape', 'Confirmation d\'étape'),
        ('demande_capture', 'Demande de capture d\'écran'),
        ('guidage_debut', 'Début du guidage à distance'),
        ('guidage_fin', 'Fin du guidage à distance'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='commentaires')
    utilisateur_auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                           related_name='commentaires')
    date_commentaire = models.DateTimeField(auto_now_add=True)
    contenu = models.TextField()
    type_action = models.CharField(max_length=25, choices=TYPE_ACTION_CHOICES, default='ajout_commentaire')

    # Nouveaux champs pour le guidage à distance
    est_instruction = models.BooleanField(default=False, help_text="Indique si c'est une instruction à suivre")
    numero_etape = models.PositiveIntegerField(null=True, blank=True, help_text="Numéro de l'étape")
    attendre_confirmation = models.BooleanField(default=False, help_text="Le technicien attend une confirmation")

    # Champ pour les réponses en chaîne
    commentaire_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                           related_name='reponses', help_text="Commentaire auquel celui-ci répond")

    # Statut de l'instruction
    est_confirme = models.BooleanField(default=False, help_text="Instruction confirmée par l'employé")
    date_confirmation = models.DateTimeField(null=True, blank=True)

    # Pièce jointe (captures d'écran, etc.)
    piece_jointe = models.FileField(upload_to='commentaires/%Y/%m/', null=True, blank=True)

    def __str__(self):
        return f"Commentaire par {self.utilisateur_auteur} sur {self.ticket}"

    def marquer_comme_confirme(self):
        """Marque l'instruction comme confirmée par l'employé"""
        from django.utils import timezone
        self.est_confirme = True
        self.date_confirmation = timezone.now()
        self.save()

    class Meta:
        ordering = ['date_commentaire']
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"


class Notification(models.Model):
    """Represents a notification for a user."""
    TYPE_NOTIFICATION_CHOICES = [
        ('email', 'Email'),
        ('interne', 'Notification Interne'),
    ]

    STATUT_NOTIFICATION_CHOICES = [
        ('envoye', 'Envoyé'),
        ('lu', 'Lu'),
        ('echec', 'Échec d\'envoi'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='notifications')
    destinataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type_notification = models.CharField(max_length=10, choices=TYPE_NOTIFICATION_CHOICES, default='interne')
    sujet = models.CharField(max_length=255)
    message = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    statut_notification = models.CharField(max_length=10, choices=STATUT_NOTIFICATION_CHOICES, default='envoye')

    def __str__(self):
        return f"{self.sujet} - {self.destinataire}"

    class Meta:
        ordering = ['-date_envoi']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"


# Signal to set default department when a new user is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def set_default_department(sender, instance, created, **kwargs):
    if created and not instance.departement_id:
        # Create a default department if none exists
        default_dept, _ = Departement.objects.get_or_create(
            nom_departement='Non spécifié',
            defaults={'responsable': 'À définir', 'localisation': 'Non spécifiée'}
        )
        # Update the user's department
        sender.objects.filter(pk=instance.pk).update(departement=default_dept)
        # Update the instance in memory
        instance.departement = default_dept


# Signal pour envoyer un email lors de la création d'un ticket
@receiver(post_save, sender=Ticket)
def envoyer_email_creation_ticket(sender, instance, created, **kwargs):
    if created:
        from .email_utils import (
            envoyer_email_nouveau_ticket,
            envoyer_email_confirmation_employe,
            auto_assign_urgent_ticket
        )
        from .serializers import TicketListSerializer
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        # Vérifier et assigner automatiquement si c'est un ticket urgent/critique
        technicien_assigne = auto_assign_urgent_ticket(instance)

        # Envoyer les emails (les fonctions principales gèrent déjà SendGrid + fallback SMTP)
        try:
            # Envoyer email aux techniciens et admins
            envoyer_email_nouveau_ticket(instance)

            # Envoyer email de confirmation à l'employé
            envoyer_email_confirmation_employe(instance)

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des emails pour le ticket {instance.id}: {str(e)}")

        # Envoyer notification WebSocket pour les nouveaux tickets
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                # Sérialiser le ticket pour l'envoi WebSocket
                serializer = TicketListSerializer(instance)
                ticket_data = serializer.data

                # Envoyer la notification aux techniciens connectés
                async_to_sync(channel_layer.group_send)(
                    'technician_notifications',
                    {
                        'type': 'new_ticket_notification',
                        'ticket': ticket_data
                    }
                )
                logger.info(f"Notification WebSocket envoyée pour le nouveau ticket {instance.id}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification WebSocket pour le ticket {instance.id}: {str(e)}")

        # Log pour les tickets urgents assignés automatiquement
        if technicien_assigne:
            logger.info(f"Ticket urgent #{instance.id} assigné automatiquement à {technicien_assigne.email}")

            # Envoyer notification d'assignation WebSocket
            try:
                if channel_layer:
                    serializer = TicketListSerializer(instance)
                    ticket_data = serializer.data

                    async_to_sync(channel_layer.group_send)(
                        'technician_notifications',
                        {
                            'type': 'ticket_assigned_notification',
                            'ticket': ticket_data
                        }
                    )
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la notification d'assignation WebSocket: {str(e)}")

    else:
        # Ticket mis à jour (pas créé)
        try:
            from .serializers import TicketListSerializer
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                # Sérialiser le ticket mis à jour
                serializer = TicketListSerializer(instance)
                ticket_data = serializer.data

                # Envoyer la notification de mise à jour aux techniciens
                async_to_sync(channel_layer.group_send)(
                    'technician_notifications',
                    {
                        'type': 'ticket_updated_notification',
                        'ticket': ticket_data
                    }
                )

                # Envoyer aussi aux utilisateurs connectés au ticket spécifique
                async_to_sync(channel_layer.group_send)(
                    f'ticket_{instance.id}',
                    {
                        'type': 'ticket_updated',
                        'ticket': ticket_data
                    }
                )
                logger.info(f"Notification WebSocket de mise à jour envoyée pour le ticket {instance.id}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification WebSocket de mise à jour: {str(e)}")


# Signal pour envoyer des notifications WebSocket lors de la création de commentaires
@receiver(post_save, sender=Commentaire)
def envoyer_notification_commentaire(sender, instance, created, **kwargs):
    if created:
        try:
            from .serializers import CommentaireSerializer
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                # Sérialiser le commentaire
                serializer = CommentaireSerializer(instance)
                comment_data = serializer.data

                # Envoyer la notification aux utilisateurs connectés au ticket
                async_to_sync(channel_layer.group_send)(
                    f'ticket_{instance.ticket.id}',
                    {
                        'type': 'chat_message',
                        'comment': comment_data
                    }
                )
                logger.info(f"Notification WebSocket de commentaire envoyée pour le ticket {instance.ticket.id}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification WebSocket de commentaire: {str(e)}")
    else:
        # Commentaire mis à jour (confirmation d'instruction par exemple)
        try:
            from .serializers import CommentaireSerializer
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                # Sérialiser le commentaire mis à jour
                serializer = CommentaireSerializer(instance)
                comment_data = serializer.data

                # Envoyer la notification de mise à jour d'instruction
                async_to_sync(channel_layer.group_send)(
                    f'ticket_{instance.ticket.id}',
                    {
                        'type': 'instruction_updated',
                        'instruction': comment_data
                    }
                )
                logger.info(f"Notification WebSocket d'instruction mise à jour envoyée pour le ticket {instance.ticket.id}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification WebSocket d'instruction mise à jour: {str(e)}")
