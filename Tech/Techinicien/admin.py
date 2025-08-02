from django.contrib import admin
from .models import CustomUser, Departement, Equipement, Categorie, Ticket, Commentaire, Notification

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'statut', 'departement')
    list_filter = ('role', 'statut', 'departement')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

class DepartementAdmin(admin.ModelAdmin):
    list_display = ('nom_departement', 'responsable', 'localisation')
    search_fields = ('nom_departement', 'responsable')

class EquipementAdmin(admin.ModelAdmin):
    list_display = ('nom_modele', 'type_equipement', 'numero_serie', 'departement', 'statut_equipement', 'date_achat')
    list_filter = ('statut_equipement', 'departement')
    search_fields = ('nom_modele', 'numero_serie')

class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom_categorie', 'description_categorie', 'couleur_affichage')
    search_fields = ('nom_categorie',)

class TicketAdmin(admin.ModelAdmin):
    list_display = ('titre', 'statut_ticket', 'priorite', 'categorie', 'utilisateur_createur', 'technicien_assigne', 'equipement', 'date_creation')
    list_filter = ('statut_ticket', 'priorite', 'categorie', 'technicien_assigne')
    search_fields = ('titre', 'description')
    date_hierarchy = 'date_creation'

class CommentaireAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'utilisateur_auteur', 'date_commentaire', 'type_action', 'est_instruction', 'numero_etape', 'est_confirme')
    list_filter = ('type_action', 'est_instruction', 'est_confirme')
    search_fields = ('contenu',)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'destinataire', 'type_notification', 'sujet', 'date_envoi', 'statut_notification')
    list_filter = ('type_notification', 'statut_notification')
    search_fields = ('sujet', 'message')
    date_hierarchy = 'date_envoi'

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Departement, DepartementAdmin)
admin.site.register(Equipement, EquipementAdmin)
admin.site.register(Categorie, CategorieAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Commentaire, CommentaireAdmin)
admin.site.register(Notification, NotificationAdmin)
