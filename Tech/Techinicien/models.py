from datetime import timezone

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from model_utils import FieldTracker
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


class QuestionDiagnostic(models.Model):
    """Représente une question dans l'arbre de décision du diagnostic"""
    TYPE_QUESTION_CHOICES = [
        ('choix_unique', 'Choix unique'),
        ('choix_multiple', 'Choix multiple'),
        ('texte', 'Texte libre'),
        ('booleen', 'Oui/Non'),
        ('echelle', 'Échelle de 1 à 5'),
    ]
    
    DIFFICULTE_CHOICES = [
        ('facile', 'Facile'),
        ('moyen', 'Moyen'),
        ('difficile', 'Difficile'),
    ]

    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type_question = models.CharField(max_length=20, choices=TYPE_QUESTION_CHOICES)
    ordre = models.PositiveIntegerField(default=0)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='questions_diagnostic')
    question_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sous_questions')
    condition_affichage = models.JSONField(default=dict, blank=True, help_text="Conditions pour afficher cette question (format JSON)")
    est_critique = models.BooleanField(default=False, help_text="Question critique pour déterminer la priorit��")
    temps_moyen = models.PositiveIntegerField(default=60, help_text="Temps moyen estimé pour répondre (en secondes)")
    niveau_difficulte = models.CharField(max_length=10, choices=DIFFICULTE_CHOICES, default='moyen', help_text="Niveau de difficulté de la question")
    tags = models.JSONField(default=list, blank=True, help_text="Tags pour catégoriser la question")
    actif = models.BooleanField(default=True, help_text="Indique si la question est active")

    class Meta:
        ordering = ['ordre']
        verbose_name = "Question de diagnostic"
        verbose_name_plural = "Questions de diagnostic"
        indexes = [
            models.Index(fields=['categorie', 'actif']),
            models.Index(fields=['est_critique']),
        ]

    def __str__(self):
        return f"{self.titre} ({self.get_type_question_display()})"

    def save(self, *args, **kwargs):
        # Validation des conditions d'affichage
        if self.condition_affichage and not isinstance(self.condition_affichage, dict):
            raise ValueError("Les conditions d'affichage doivent être un dictionnaire JSON valide")
        super().save(*args, **kwargs)


class SessionDiagnostic(models.Model):
    """Représente une session de diagnostic pour un utilisateur"""
    STATUT_SESSION_CHOICES = [
        ('en_cours', 'En cours'),
        ('complete', 'Complète'),
        ('abandonnee', 'Abandonnée'),
        ('en_pause', 'En pause'),
    ]

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions_diagnostic')
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='sessions_diagnostic')
    statut = models.CharField(max_length=20, choices=STATUT_SESSION_CHOICES, default='en_cours')
    score_criticite_total = models.IntegerField(default=0)
    priorite_estimee = models.CharField(max_length=10, choices=Ticket.PRIORITE_CHOICES, default='normal')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_debut = models.DateTimeField(null=True, blank=True)
    date_derniere_activite = models.DateTimeField(auto_now=True)
    date_completion = models.DateTimeField(null=True, blank=True)
    temps_total_passe = models.PositiveIntegerField(default=0, help_text="Temps total passé sur le diagnostic (en secondes)")
    diagnostic_automatique = models.JSONField(default=dict, blank=True)
    recommandations = models.TextField(blank=True)
    score_confiance = models.FloatField(default=1.0, help_text="Score de confiance dans les réponses (0-1)")
    donnees_supplementaires = models.JSONField(default=dict, blank=True, help_text="Données supplémentaires de la session")
    equipement = models.ForeignKey(Equipement, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions_diagnostic')

    # Ajouter le FieldTracker directement dans la classe
    tracker = FieldTracker()

    class Meta:
        verbose_name = "Session de diagnostic"
        verbose_name_plural = "Sessions de diagnostic"
        ordering = ['-date_derniere_activite']
        indexes = [
            models.Index(fields=['utilisateur', 'statut']),
            models.Index(fields=['categorie', 'statut']),
            models.Index(fields=['priorite_estimee']),
        ]

    def __str__(self):
        return f"Session {self.id} - {self.utilisateur.email} - {self.categorie.nom_categorie}"

    def calculer_score_confiance(self):
        """Calcule le score de confiance basé sur les réponses"""
        reponses = self.reponses.all()
        if not reponses.exists():
            return 1.0
            
        # Calculer un score basé sur la cohérence des réponses
        # (à implémenter selon la logique métier)
        return 0.9  # Valeur par défaut

    def mettre_a_jour_statut(self, nouveau_statut):
        """Met à jour le statut de la session et déclenche les actions nécessaires"""
        ancien_statut = self.statut
        self.statut = nouveau_statut
        
        if nouveau_statut == 'complete' and ancien_statut != 'complete':
            self.date_completion = timezone.now()
            self.score_confiance = self.calculer_score_confiance()
            
            # Créer un historique de la session
            HistoriqueDiagnostic.objects.create(
                session=self,
                action='completion',
                details={
                    'score_confiance': self.score_confiance,
                    'recommandations': self.recommandations,
                }
            )
            
        self.save(update_fields=['statut', 'date_completion', 'score_confiance'])


class HistoriqueDiagnostic(models.Model):
    """Historique des actions et changements d'état d'une session de diagnostic"""
    TYPE_ACTION = [
        ('debut', 'Début de session'),
        ('reponse', 'Réponse à une question'),
        ('reprise', 'Reprise de session'),
        ('pause', 'Mise en pause'),
        ('abandon', 'Abandon'),
        ('completion', 'Diagnostic terminé'),
        ('recommandation', 'Génération de recommandation'),
        ('systeme', 'Action système'),
    ]
    
    session = models.ForeignKey(SessionDiagnostic, on_delete=models.CASCADE, related_name='historique')
    action = models.CharField(max_length=20, choices=TYPE_ACTION)
    date_action = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_action']
        verbose_name = "Entrée d'historique de diagnostic"
        verbose_name_plural = "Historique des diagnostics"

    def __str__(self):
        return f"{self.get_action_display()} - {self.session} - {self.date_action}"


class TemplateDiagnostic(models.Model):
    """Modèle pour les modèles de diagnostics réutilisables"""
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='templates_diagnostic')
    questions = models.ManyToManyField(QuestionDiagnostic, through='TemplateQuestion')
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Configuration du flux de questions
    est_lineaire = models.BooleanField(default=True, help_text="Si vrai, les questions sont posées dans l'ordre défini")
    permettre_saut = models.BooleanField(default=True, help_text="Permet de sauter des questions")
    permettre_revenir_arriere = models.BooleanField(default=True, help_text="Permet de revenir aux questions précédentes")
    
    # Paramètres d'expérience utilisateur
    afficher_progression = models.BooleanField(default=True, help_text="Affiche la barre de progression")
    afficher_temps_estime = models.BooleanField(default=True, help_text="Affiche le temps estimé restant")
    
    # Personnalisation
    couleur_principale = models.CharField(max_length=7, default='#4a6da7', help_text="Couleur principale du thème (format hexadécimal)")
    logo = models.ImageField(upload_to='diagnostic_templates/logos/', null=True, blank=True)
    
    class Meta:
        ordering = ['nom']
        verbose_name = "Modèle de diagnostic"
        verbose_name_plural = "Modèles de diagnostic"

    def __str__(self):
        return self.nom

    def dupliquer(self, nouveau_nom, auteur=None):
        """Crée une copie du modèle avec toutes ses questions"""
        from django.db import transaction
        
        with transaction.atomic():
            # Créer une copie du template
            nouveau_template = TemplateDiagnostic.objects.create(
                nom=nouveau_nom,
                description=self.description,
                categorie=self.categorie,
                est_actif=self.est_actif,
                auteur=auteur or self.auteur,
                tags=self.tags.copy(),
                est_lineaire=self.est_lineaire,
                permettre_saut=self.permettre_saut,
                permettre_revenir_arriere=self.permettre_revenir_arriere,
                afficher_progression=self.afficher_progression,
                afficher_temps_estime=self.afficher_temps_estime,
                couleur_principale=self.couleur_principale,
            )
            
            # Copier les associations de questions
            for template_question in self.template_questions.all():
                TemplateQuestion.objects.create(
                    template=nouveau_template,
                    question=template_question.question,
                    ordre=template_question.ordre,
                    condition_affichage=template_question.condition_affichage,
                )
            
            return nouveau_template


class TemplateQuestion(models.Model):
    """Relation entre TemplateDiagnostic et QuestionDiagnostic avec ordre et conditions spécifiques"""
    template = models.ForeignKey(TemplateDiagnostic, on_delete=models.CASCADE, related_name='template_questions')
    question = models.ForeignKey(QuestionDiagnostic, on_delete=models.CASCADE, related_name='templates')
    ordre = models.PositiveIntegerField(default=0)
    condition_affichage = models.JSONField(default=dict, blank=True, 
                                         help_text="Conditions spécifiques pour ce template (écrase celles de la question)")
    
    class Meta:
        ordering = ['template', 'ordre']
        unique_together = [('template', 'question'), ('template', 'ordre')]
        verbose_name = "Question du modèle"
        verbose_name_plural = "Questions des modèles"
    
    def __str__(self):
        return f"{self.template.nom} - {self.ordre}. {self.question.titre}"


# Mise à jour du modèle ChoixReponse existant
class ChoixReponse(models.Model):
    """Représente un choix de réponse pour une question de diagnostic"""
    question = models.ForeignKey(QuestionDiagnostic, on_delete=models.CASCADE, related_name='choix_reponses')
    texte = models.CharField(max_length=255)
    valeur = models.CharField(max_length=100)
    score_criticite = models.IntegerField(default=0, help_text="Score de criticité (0-10)")
    action_suivante = models.JSONField(default=dict, blank=True, help_text="Action à effectuer après cette réponse")
    ordre = models.PositiveIntegerField(default=0, help_text="Ordre d'affichage des choix")
    couleur = models.CharField(max_length=7, default='#4a6da7', help_text="Couleur du bouton (format hexadécimal)")
    est_par_defaut = models.BooleanField(default=False, help_text="Sélectionné par défaut")
    declenche_suite = models.BooleanField(default=True, help_text="Passe à la question suivante après sélection")

    class Meta:
        ordering = ['question', 'ordre', 'id']
        verbose_name = "Choix de réponse"
        verbose_name_plural = "Choix de réponses"
        unique_together = [('question', 'valeur')]

    def __str__(self):
        return f"{self.question.titre} - {self.texte}"


# Mise à jour du modèle ReponseDiagnostic existant
class ReponseDiagnostic(models.Model):
    """Représente la réponse d'un utilisateur à une question de diagnostic"""
    session = models.ForeignKey(SessionDiagnostic, on_delete=models.CASCADE, related_name='reponses')
    question = models.ForeignKey(QuestionDiagnostic, on_delete=models.CASCADE, related_name='reponses')
    reponse_texte = models.TextField(blank=True)
    score_criticite = models.IntegerField(default=0)
    date_reponse = models.DateTimeField(auto_now_add=True)
    temps_passe = models.PositiveIntegerField(default=0, help_text="Temps passé sur la question (en secondes)")
    est_incertain = models.BooleanField(default=False, help_text="L'utilisateur a indiqué être incertain de sa réponse")
    commentaire = models.TextField(blank=True, null=True, help_text="Commentaire facultatif sur la réponse")
    donnees_supplementaires = models.JSONField(default=dict, blank=True, help_text="Données supplémentaires de la réponse")

    class Meta:
        unique_together = ['session', 'question']
        verbose_name = "Réponse de diagnostic"
        verbose_name_plural = "Réponses de diagnostic"
        ordering = ['date_reponse']
        indexes = [
            models.Index(fields=['session', 'question']),
        ]

    def __str__(self):
        return f"{self.session} - {self.question.titre}"

    @property
    def choix_selectionnes(self):
        """Propriété pour accéder aux choix sélectionnés"""
        return ChoixReponse.objects.filter(selections__reponse=self)

    def ajouter_choix(self, choix):
        """Ajoute un choix sélectionné"""
        ChoixSelectionne.objects.get_or_create(reponse=self, choix=choix)
        self._recalculer_score()

    def supprimer_choix(self, choix):
        """Supprime un choix sélectionné"""
        ChoixSelectionne.objects.filter(reponse=self, choix=choix).delete()
        self._recalculer_score()

    def vider_choix(self):
        """Supprime tous les choix sélectionnés"""
        ChoixSelectionne.objects.filter(reponse=self).delete()
        self.score_criticite = 0
        self.save(update_fields=['score_criticite'])

    def _recalculer_score(self):
        """Recalcule le score de criticité basé sur les choix sélectionnés"""
        score_total = sum(
            selection.choix.score_criticite
            for selection in self.choix_selectionnes_list.all()
        )
        self.score_criticite = score_total
        self.save(update_fields=['score_criticite'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Mettre à jour le score de confiance de la session
        if hasattr(self, 'session'):
            self.session.score_confiance = self.session.calculer_score_confiance()
            self.session.save(update_fields=['score_confiance', 'date_derniere_activite'])


# Mise à jour du modèle RegleDiagnostic existant
class RegleDiagnostic(models.Model):
    """Règles pour l'analyse automatique et les recommandations"""
    TYPE_DECLENCHEUR = [
        ('reponse', 'Après une réponse'),
        ('session_debut', 'Au début de la session'),
        ('session_fin', 'À la fin de la session'),
        ('changement_etat', 'Changement d\'état de session'),
    ]
    
    TYPE_ACTION = [
        ('afficher_message', 'Afficher un message'),
        ('changer_etat', 'Changer l\'état de la session'),
        ('definir_priorite', 'Définir la priorité'),
        ('generer_recommandation', 'Générer une recommandation'),
        ('creer_ticket', 'Créer un ticket'),
        ('rediriger', 'Rediriger vers une autre question'),
        ('executer_script', 'Exécuter un script personnalisé'),
    ]
    
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='regles_diagnostic', null=True, blank=True)
    question = models.ForeignKey(QuestionDiagnostic, on_delete=models.CASCADE, related_name='regles', null=True, blank=True)
    
    # Déclencheur
    type_declencheur = models.CharField(max_length=20, choices=TYPE_DECLENCHEUR, default='reponse')
    conditions = models.JSONField(help_text="Conditions pour déclencher cette règle (format JSON)")
    
    # Action
    type_action = models.CharField(max_length=30, choices=TYPE_ACTION)
    parametres_action = models.JSONField(help_text="Paramètres de l'action (format JSON)")
    
    # Priorité et statut
    priorite = models.PositiveIntegerField(default=0, help_text="Ordre d'exécution des règles (plus le chiffre est bas, plus la règle est prioritaire)")
    est_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    
    # Journalisation et débogage
    derniere_execution = models.DateTimeField(null=True, blank=True)
    dernier_resultat = models.BooleanField(null=True, blank=True)
    dernier_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['priorite', 'nom']
        verbose_name = "Règle de diagnostic"
        verbose_name_plural = "Règles de diagnostic"
        indexes = [
            models.Index(fields=['est_active', 'type_declencheur']),
            models.Index(fields=['categorie', 'est_active']),
        ]

    def __str__(self):
        return f"{self.nom} ({self.get_type_declencheur_display()} → {self.get_type_action_display()})"

    def executer(self, session, reponse=None, contexte=None):
        """Exécute la règle avec le contexte donné"""
        from django.utils import timezone
        from .services.regles_service import executer_regle
        
        try:
            contexte = contexte or {}
            if reponse:
                contexte['reponse'] = reponse
                
            resultat, message = executer_regle(self, session, contexte)
            
            # Mettre à jour les informations de suivi
            self.derniere_execution = timezone.now()
            self.dernier_resultat = resultat
            self.dernier_message = str(message)[:500]  # Limiter la taille du message
            self.save(update_fields=['derniere_execution', 'dernier_resultat', 'dernier_message'])
            
            return resultat, message
            
        except Exception as e:
            self.derniere_execution = timezone.now()
            self.dernier_resultat = False
            self.dernier_message = f"Erreur: {str(e)}"
            self.save(update_fields=['derniere_execution', 'dernier_resultat', 'dernier_message'])
            raise


class DiagnosticSysteme(models.Model):
    """Stocke les résultats de diagnostic automatique du système"""
    TYPE_DIAGNOSTIC_CHOICES = [
        ('memoire', 'Mémoire'),
        ('disque', 'Espace disque'),
        ('reseau', 'Réseau'),
        ('cpu', 'Processeur'),
        ('services', 'Services Windows'),
        ('logiciels', 'Logiciels installés'),
        ('securite', 'Sécurité'),
        ('performance', 'Performances'),
        ('reseau_avance', 'Analyse réseau avancée'),
        ('systeme', 'Système d\'exploitation'),
    ]

    session = models.ForeignKey(SessionDiagnostic, on_delete=models.CASCADE, related_name='diagnostics_systeme')
    type_diagnostic = models.CharField(max_length=20, choices=TYPE_DIAGNOSTIC_CHOICES)
    resultat = models.JSONField()
    statut = models.CharField(max_length=20, choices=[
        ('ok', 'OK'),
        ('avertissement', 'Avertissement'),
        ('erreur', 'Erreur'),
        ('informatif', 'Informatif'),
    ])
    message = models.TextField()
    date_diagnostic = models.DateTimeField(auto_now_add=True)
    duree_execution = models.FloatField(help_text="Durée d'exécution en secondes", null=True, blank=True)
    niveau_impact = models.PositiveIntegerField(default=1, help_text="Niveau d'impact sur le diagnostic global (1-10)")
    balises = models.JSONField(default=list, blank=True, help_text="Balises pour catégoriser le diagnostic")
    recommandation = models.TextField(blank=True, null=True, help_text="Recommandation associée à ce diagnostic")
    
    class Meta:
        verbose_name = "Diagnostic système"
        verbose_name_plural = "Diagnostics système"
        ordering = ['-date_diagnostic']
        indexes = [
            models.Index(fields=['session', 'type_diagnostic']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"{self.get_type_diagnostic_display()} - {self.statut} - {self.session}"


# Signal pour créer automatiquement un ticket si le diagnostic est critique
@receiver(post_save, sender=SessionDiagnostic)
def creer_ticket_automatique(sender, instance, created, **kwargs):
    """Crée automatiquement un ticket si le diagnostic indique un problème critique"""
    if instance.statut == 'complete' and instance.priorite_estimee in ['urgent', 'critique']:
        # Vérifier si un ticket n'existe pas déjà pour cette session
        if not Ticket.objects.filter(
            titre__icontains=f"Diagnostic automatique - Session {instance.id}"
        ).exists():
            # Créer le ticket
            ticket = Ticket.objects.create(
                titre=f"Diagnostic automatique - Session {instance.id}",
                description=f"Un diagnostic automatique a détecté un problème {instance.priorite_estimee}.\n\n"
                          f"**Catégorie:** {instance.categorie.nom_categorie}\n"
                          f"**Score de criticité:** {instance.score_criticite_total}/100\n"
                          f"**Recommandations:**\n{instance.recommandations}\n\n"
                          f"_Ce ticket a été généré automatiquement à partir d'une session de diagnostic._",
                priorite=instance.priorite_estimee,
                categorie=instance.categorie,
                utilisateur_createur=instance.utilisateur,
                statut_ticket='ouvert',
                equipement=instance.equipement
            )
            
            # Ajouter les données supplémentaires sans l'URL qui pose problème
            ticket.donnees_supplementaires = {
                'session_diagnostic_id': instance.id,
                'score_confiance': float(instance.score_confiance) if instance.score_confiance else 1.0,
                'date_completion': instance.date_completion.isoformat() if instance.date_completion else None,
                'type': 'creation_automatique',
                'source': 'diagnostic_automatique'
            }
            ticket.save()
            
            # Créer un commentaire avec les détails du diagnostic
            Commentaire.objects.create(
                ticket=ticket,
                utilisateur_auteur=instance.utilisateur,
                contenu=f"Ce ticket a été généré automatiquement à partir d'une session de diagnostic.\n\n"
                       f"**Détails du diagnostic:**\n"
                       f"- Priorité estimée: {instance.get_priorite_estimee_display()}\n"
                       f"- Score de confiance: {instance.score_confiance:.1%}\n"
                       f"- Date du diagnostic: {instance.date_completion.strftime('%d/%m/%Y %H:%M') if instance.date_completion else 'N/A'}\n"
                       f"- Équipement concerné: {instance.equipement if instance.equipement else 'Aucun équipement spécifié'}",
                type_action='creation',
                donnees_supplementaires={
                    'type': 'creation_automatique',
                    'source': 'diagnostic_automatique',
                    'session_id': instance.id,
                }
            )
            
            logger.info(f"Ticket automatique créé pour la session de diagnostic {instance.id} (ticket #{ticket.id})")
            
            # Mettre à jour la session avec une référence vers le ticket créé
            instance.donnees_supplementaires = instance.donnees_supplementaires or {}
            instance.donnees_supplementaires['ticket_automatique_id'] = ticket.id
            instance.save(update_fields=['donnees_supplementaires'])
            
            return ticket
    return None


# Signal pour enregistrer l'historique des sessions
@receiver(post_save, sender=SessionDiagnostic)
def enregistrer_historique_session(sender, instance, created, **kwargs):
    """Enregistre une entrée d'historique lors de la création ou de la mise à jour d'une session"""
    from django.utils import timezone
    
    if created:
        # Enregistrer le début de la session
        HistoriqueDiagnostic.objects.create(
            session=instance,
            action='debut',
            utilisateur=instance.utilisateur,
            details={
                'categorie': instance.categorie.nom_categorie,
                'priorite_estimee': instance.priorite_estimee,
            }
        )
    else:
        # Vérifier si le statut a changé en utilisant le tracker si disponible
        try:
            if hasattr(instance, 'tracker') and hasattr(instance.tracker, 'has_changed'):
                if instance.tracker.has_changed('statut'):
                    ancien_statut = instance.tracker.previous('statut')
                    HistoriqueDiagnostic.objects.create(
                        session=instance,
                        action='changement_statut',
                        utilisateur=instance.utilisateur,
                        details={
                            'ancien_statut': ancien_statut,
                            'nouveau_statut': instance.statut,
                        }
                    )
        except Exception as e:
            # En cas d'erreur avec le tracker, on ignore silencieusement
            logger.error(f"Erreur lors du suivi des changements pour la session {instance.id}: {e}")
            pass


# Modèle pour les sélections de choix (remplace la relation many-to-many)
class ChoixSelectionne(models.Model):
    """Représente un choix sélectionné pour une réponse de diagnostic"""
    reponse = models.ForeignKey('ReponseDiagnostic', on_delete=models.CASCADE, related_name='choix_selectionnes_list')
    choix = models.ForeignKey(ChoixReponse, on_delete=models.CASCADE, related_name='selections')
    date_selection = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['reponse', 'choix']
        verbose_name = "Choix sélectionné"
        verbose_name_plural = "Choix sélectionnés"
    
    def __str__(self):
        return f"{self.reponse} - {self.choix.texte}"
