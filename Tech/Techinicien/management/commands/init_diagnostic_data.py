from django.core.management.base import BaseCommand
from django.db import transaction
from Techinicien.models import (
    Departement, CustomUser, Categorie, Equipement,
    QuestionDiagnostic, ChoixReponse, TemplateDiagnostic,
    TemplateQuestion, RegleDiagnostic
)
import json


class Command(BaseCommand):
    help = 'Initialise les données nécessaires pour le système de diagnostic intelligent'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la recréation des données (supprime les existantes)',
        )

    def handle(self, *args, **options):
        force = options['force']

        self.stdout.write(
            self.style.SUCCESS('🚀 Initialisation des données pour le diagnostic intelligent...')
        )

        try:
            with transaction.atomic():
                # 1. Créer les départements
                self.create_departments(force)

                # 2. Créer les catégories
                self.create_categories(force)

                # 3. Créer des équipements
                self.create_equipments(force)

                # 4. Créer les questions de diagnostic
                self.create_diagnostic_questions(force)

                # 5. Créer les templates de diagnostic
                self.create_diagnostic_templates(force)

                # 6. Créer les règles de diagnostic
                self.create_diagnostic_rules(force)

                # 7. Créer un utilisateur de test si nécessaire
                self.create_test_users(force)

            self.stdout.write(
                self.style.SUCCESS('✅ Données initialisées avec succès!')
            )
            self.stdout.write(
                self.style.WARNING('📝 Vous pouvez maintenant tester le diagnostic intelligent')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de l\'initialisation: {str(e)}')
            )
            raise

    def create_departments(self, force):
        """Créer les départements de base"""
        departments_data = [
            {
                'nom_departement': 'Informatique',
                'responsable': 'Admin IT',
                'localisation': 'Bâtiment A - 1er étage'
            },
            {
                'nom_departement': 'Ressources Humaines',
                'responsable': 'Manager RH',
                'localisation': 'Bâtiment B - 2ème étage'
            },
            {
                'nom_departement': 'Comptabilité',
                'responsable': 'Chef Comptable',
                'localisation': 'Bâtiment A - Rez-de-chaussée'
            },
            {
                'nom_departement': 'Commercial',
                'responsable': 'Directeur Commercial',
                'localisation': 'Bâtiment C - 3ème étage'
            },
            {
                'nom_departement': 'Non spécifié',
                'responsable': 'À définir',
                'localisation': 'Non spécifiée'
            }
        ]

        if force:
            Departement.objects.all().delete()

        for dept_data in departments_data:
            dept, created = Departement.objects.get_or_create(
                nom_departement=dept_data['nom_departement'],
                defaults=dept_data
            )
            if created:
                self.stdout.write(f'✓ Département créé: {dept.nom_departement}')

    def create_categories(self, force):
        """Créer les catégories de diagnostic"""
        categories_data = [
            {
                'nom_categorie': 'Matériel informatique',
                'description_categorie': 'Problèmes liés aux ordinateurs, imprimantes, périphériques',
                'couleur_affichage': '#4F46E5'  # Indigo
            },
            {
                'nom_categorie': 'Réseau et Internet',
                'description_categorie': 'Connectivité, Wi-Fi, accès aux serveurs',
                'couleur_affichage': '#059669'  # Emerald
            },
            {
                'nom_categorie': 'Logiciels et Applications',
                'description_categorie': 'Problèmes avec les programmes, Office, navigateurs',
                'couleur_affichage': '#DC2626'  # Red
            },
            {
                'nom_categorie': 'Email et Messagerie',
                'description_categorie': 'Outlook, webmail, problèmes d\'envoi/réception',
                'couleur_affichage': '#7C2D12'  # Orange
            },
            {
                'nom_categorie': 'Sécurité informatique',
                'description_categorie': 'Antivirus, mots de passe, accès aux systèmes',
                'couleur_affichage': '#B91C1C'  # Red-700
            },
            {
                'nom_categorie': 'Performance système',
                'description_categorie': 'Lenteur, plantages, optimisation',
                'couleur_affichage': '#7C3AED'  # Violet
            }
        ]

        if force:
            Categorie.objects.all().delete()

        for cat_data in categories_data:
            cat, created = Categorie.objects.get_or_create(
                nom_categorie=cat_data['nom_categorie'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'✓ Catégorie créée: {cat.nom_categorie}')

    def create_equipments(self, force):
        """Créer des équipements d'exemple"""
        equipments_data = [
            {
                'nom_modele': 'Dell OptiPlex 7090',
                'type_equipement': 'Ordinateur de bureau',
                'numero_serie': 'DL001',
                'departement_nom': 'Informatique',
                'statut_equipement': 'fonctionnel',
                'date_achat': '2023-01-15'
            },
            {
                'nom_modele': 'HP LaserJet Pro 404dn',
                'type_equipement': 'Imprimante',
                'numero_serie': 'HP001',
                'departement_nom': 'Informatique',
                'statut_equipement': 'fonctionnel',
                'date_achat': '2023-03-20'
            },
            {
                'nom_modele': 'Lenovo ThinkPad E15',
                'type_equipement': 'Ordinateur portable',
                'numero_serie': 'LN001',
                'departement_nom': 'Commercial',
                'statut_equipement': 'fonctionnel',
                'date_achat': '2023-06-10'
            }
        ]

        if force:
            Equipement.objects.all().delete()

        for eq_data in equipments_data:
            departement = Departement.objects.get(nom_departement=eq_data['departement_nom'])
            eq_data_clean = eq_data.copy()
            eq_data_clean.pop('departement_nom')
            eq_data_clean['departement'] = departement

            eq, created = Equipement.objects.get_or_create(
                numero_serie=eq_data['numero_serie'],
                defaults=eq_data_clean
            )
            if created:
                self.stdout.write(f'✓ Équipement créé: {eq.nom_modele}')

    def create_diagnostic_questions(self, force):
        """Créer les questions de diagnostic pour chaque catégorie"""

        if force:
            QuestionDiagnostic.objects.all().delete()
            ChoixReponse.objects.all().delete()

        # Questions pour Matériel informatique
        self.create_hardware_questions()

        # Questions pour Réseau et Internet
        self.create_network_questions()

        # Questions pour Logiciels et Applications
        self.create_software_questions()

        # Questions pour Email et Messagerie
        self.create_email_questions()

        # Questions pour Sécurité informatique
        self.create_security_questions()

        # Questions pour Performance système
        self.create_performance_questions()

    def create_hardware_questions(self):
        """Questions pour le matériel informatique"""
        categorie = Categorie.objects.get(nom_categorie='Matériel informatique')

        questions_data = [
            {
                'titre': 'Votre ordinateur s\'allume-t-il correctement ?',
                'description': 'Vérifiez si l\'ordinateur démarre normalement',
                'type_question': 'choix_unique',
                'ordre': 1,
                'est_critique': True,
                'temps_moyen': 30,
                'niveau_difficulte': 'facile',
                'tags': ['demarrage', 'alimentation'],
                'choix': [
                    {'texte': 'Oui, il démarre normalement', 'valeur': 'ok', 'score_criticite': 0},
                    {'texte': 'Il démarre mais très lentement', 'valeur': 'lent', 'score_criticite': 3},
                    {'texte': 'Il démarre parfois seulement', 'valeur': 'intermittent', 'score_criticite': 6},
                    {'texte': 'Non, il ne s\'allume pas du tout', 'valeur': 'non', 'score_criticite': 10}
                ]
            },
            {
                'titre': 'Y a-t-il des bruits inhabituels provenant de l\'ordinateur ?',
                'description': 'Écoutez attentivement les ventilateurs et le disque dur',
                'type_question': 'choix_unique',
                'ordre': 2,
                'est_critique': True,
                'temps_moyen': 45,
                'niveau_difficulte': 'moyen',
                'tags': ['bruit', 'ventilateur', 'disque'],
                'choix': [
                    {'texte': 'Aucun bruit anormal', 'valeur': 'normal', 'score_criticite': 0},
                    {'texte': 'Ventilateur un peu bruyant', 'valeur': 'ventilateur_bruyant', 'score_criticite': 2},
                    {'texte': 'Clics ou grincements du disque dur', 'valeur': 'disque_bruit', 'score_criticite': 8},
                    {'texte': 'Bruits très forts et inhabituel', 'valeur': 'bruit_fort', 'score_criticite': 9}
                ]
            },
            {
                'titre': 'L\'écran affiche-t-il correctement ?',
                'description': 'Vérifiez la qualité de l\'affichage',
                'type_question': 'choix_unique',
                'ordre': 3,
                'est_critique': True,
                'temps_moyen': 30,
                'niveau_difficulte': 'facile',
                'tags': ['ecran', 'affichage'],
                'choix': [
                    {'texte': 'Affichage parfait', 'valeur': 'ok', 'score_criticite': 0},
                    {'texte': 'Légèrement flou ou pixelisé', 'valeur': 'flou', 'score_criticite': 2},
                    {'texte': 'Lignes ou taches sur l\'écran', 'valeur': 'lignes', 'score_criticite': 6},
                    {'texte': 'Écran noir ou ne s\'allume pas', 'valeur': 'noir', 'score_criticite': 9}
                ]
            },
            {
                'titre': 'Décrivez le problème matériel en détail',
                'description': 'Expliquez précisément ce qui ne fonctionne pas',
                'type_question': 'texte',
                'ordre': 4,
                'est_critique': False,
                'temps_moyen': 120,
                'niveau_difficulte': 'facile',
                'tags': ['description', 'details']
            }
        ]

        self.create_questions_for_category(categorie, questions_data)

    def create_network_questions(self):
        """Questions pour le réseau et Internet"""
        categorie = Categorie.objects.get(nom_categorie='Réseau et Internet')

        questions_data = [
            {
                'titre': 'Avez-vous accès à Internet ?',
                'description': 'Testez en ouvrant un site web',
                'type_question': 'choix_unique',
                'ordre': 1,
                'est_critique': True,
                'temps_moyen': 30,
                'niveau_difficulte': 'facile',
                'tags': ['internet', 'connectivite'],
                'choix': [
                    {'texte': 'Oui, Internet fonctionne normalement', 'valeur': 'ok', 'score_criticite': 0},
                    {'texte': 'Internet très lent', 'valeur': 'lent', 'score_criticite': 4},
                    {'texte': 'Connexion intermittente', 'valeur': 'intermittent', 'score_criticite': 7},
                    {'texte': 'Aucun accès Internet', 'valeur': 'non', 'score_criticite': 10}
                ]
            },
            {
                'titre': 'Êtes-vous connecté au Wi-Fi de l\'entreprise ?',
                'description': 'Vérifiez l\'icône Wi-Fi dans la barre des tâches',
                'type_question': 'choix_unique',
                'ordre': 2,
                'est_critique': True,
                'temps_moyen': 20,
                'niveau_difficulte': 'facile',
                'tags': ['wifi', 'connexion'],
                'choix': [
                    {'texte': 'Oui, connecté avec signal fort', 'valeur': 'connecte_fort', 'score_criticite': 0},
                    {'texte': 'Oui, mais signal faible', 'valeur': 'connecte_faible', 'score_criticite': 3},
                    {'texte': 'Connecté mais avec des déconnexions', 'valeur': 'instable', 'score_criticite': 6},
                    {'texte': 'Non, impossible de se connecter', 'valeur': 'non_connecte', 'score_criticite': 8}
                ]
            },
            {
                'titre': 'Pouvez-vous accéder aux dossiers partagés du serveur ?',
                'description': 'Testez l\'accès aux ressources réseau de l\'entreprise',
                'type_question': 'choix_unique',
                'ordre': 3,
                'est_critique': False,
                'temps_moyen': 45,
                'niveau_difficulte': 'moyen',
                'tags': ['serveur', 'partage', 'reseau_local'],
                'choix': [
                    {'texte': 'Oui, accès normal aux dossiers', 'valeur': 'ok', 'score_criticite': 0},
                    {'texte': 'Accès lent aux dossiers', 'valeur': 'lent', 'score_criticite': 3},
                    {'texte': 'Certains dossiers inaccessibles', 'valeur': 'partiel', 'score_criticite': 5},
                    {'texte': 'Aucun accès aux dossiers partagés', 'valeur': 'aucun', 'score_criticite': 7}
                ]
            }
        ]

        self.create_questions_for_category(categorie, questions_data)

    def create_software_questions(self):
        """Questions pour les logiciels et applications"""
        categorie = Categorie.objects.get(nom_categorie='Logiciels et Applications')

        questions_data = [
            {
                'titre': 'Quel logiciel pose problème ?',
                'description': 'Sélectionnez le logiciel concerné',
                'type_question': 'choix_unique',
                'ordre': 1,
                'est_critique': True,
                'temps_moyen': 20,
                'niveau_difficulte': 'facile',
                'tags': ['logiciel', 'application'],
                'choix': [
                    {'texte': 'Microsoft Office (Word, Excel, PowerPoint)', 'valeur': 'office', 'score_criticite': 5},
                    {'texte': 'Navigateur web (Chrome, Firefox, Edge)', 'valeur': 'navigateur', 'score_criticite': 4},
                    {'texte': 'Logiciel métier spécifique', 'valeur': 'metier', 'score_criticite': 8},
                    {'texte': 'Système d\'exploitation Windows', 'valeur': 'windows', 'score_criticite': 9},
                    {'texte': 'Autre logiciel', 'valeur': 'autre', 'score_criticite': 3}
                ]
            },
            {
                'titre': 'Le logiciel se lance-t-il ?',
                'description': 'Testez l\'ouverture du logiciel',
                'type_question': 'choix_unique',
                'ordre': 2,
                'est_critique': True,
                'temps_moyen': 30,
                'niveau_difficulte': 'facile',
                'tags': ['lancement', 'demarrage'],
                'choix': [
                    {'texte': 'Oui, il se lance normalement', 'valeur': 'ok', 'score_criticite': 0},
                    {'texte': 'Il se lance mais très lentement', 'valeur': 'lent', 'score_criticite': 3},
                    {'texte': 'Il se lance puis se ferme', 'valeur': 'crash', 'score_criticite': 7},
                    {'texte': 'Il ne se lance pas du tout', 'valeur': 'non', 'score_criticite': 8}
                ]
            },
            {
                'titre': 'Recevez-vous des messages d\'erreur ?',
                'description': 'Notez exactement le message affiché',
                'type_question': 'choix_unique',
                'ordre': 3,
                'est_critique': False,
                'temps_moyen': 40,
                'niveau_difficulte': 'moyen',
                'tags': ['erreur', 'message'],
                'choix': [
                    {'texte': 'Aucun message d\'erreur', 'valeur': 'aucun', 'score_criticite': 0},
                    {'texte': 'Messages d\'avertissement occasionnels', 'valeur': 'avertissement', 'score_criticite': 2},
                    {'texte': 'Messages d\'erreur fréquents', 'valeur': 'frequent', 'score_criticite': 6},
                    {'texte': 'Message d\'erreur critique bloquant', 'valeur': 'critique', 'score_criticite': 9}
                ]
            }
        ]

        self.create_questions_for_category(categorie, questions_data)

    def create_email_questions(self):
        """Questions pour email et messagerie"""
        categorie = Categorie.objects.get(nom_categorie='Email et Messagerie')

        questions_data = [
            {
                'titre': 'Pouvez-vous envoyer des emails ?',
                'description': 'Testez l\'envoi d\'un email de test',
                'type_question': 'choix_unique',
                'ordre': 1,
                'est_critique': True,
                'temps_moyen': 45,
                'niveau_difficulte': 'facile',
                'tags': ['email', 'envoi'],
                'choix': [
                    {'texte': 'Oui, l\'envoi fonctionne normalement', 'valeur': 'ok', 'score_criticite': 0},
                    {'texte': 'Envoi possible mais lent', 'valeur': 'lent', 'score_criticite': 3},
                    {'texte': 'Envoi échoue parfois', 'valeur': 'intermittent', 'score_criticite': 6},
                    {'texte': 'Impossible d\'envoyer des emails', 'valeur': 'impossible', 'score_criticite': 9}
                ]
            },
            {
                'titre': 'Recevez-vous vos emails ?',
                'description': 'Vérifiez la réception de nouveaux messages',
                'type_question': 'choix_unique',
                'ordre': 2,
                'est_critique': True,
                'temps_moyen': 30,
                'niveau_difficulte': 'facile',
                'tags': ['email', 'reception'],
                'choix': [
                    {'texte': 'Oui, réception normale', 'valeur': 'ok', 'score_criticite': 0},
                    {'texte': 'Réception avec retard', 'valeur': 'retard', 'score_criticite': 4},
                    {'texte': 'Je ne reçois que certains emails', 'valeur': 'partiel', 'score_criticite': 7},
                    {'texte': 'Aucun email reçu', 'valeur': 'aucun', 'score_criticite': 10}
                ]
            },
            {
                'titre': 'Quel client email utilisez-vous ?',
                'description': 'Précisez votre application de messagerie',
                'type_question': 'choix_unique',
                'ordre': 3,
                'est_critique': False,
                'temps_moyen': 15,
                'niveau_difficulte': 'facile',
                'tags': ['client', 'application'],
                'choix': [
                    {'texte': 'Microsoft Outlook (application)', 'valeur': 'outlook_app', 'score_criticite': 0},
                    {'texte': 'Webmail dans le navigateur', 'valeur': 'webmail', 'score_criticite': 0},
                    {'texte': 'Thunderbird', 'valeur': 'thunderbird', 'score_criticite': 0},
                    {'texte': 'Autre client email', 'valeur': 'autre', 'score_criticite': 1}
                ]
            }
        ]

        self.create_questions_for_category(categorie, questions_data)

    def create_security_questions(self):
        """Questions pour la sécurité informatique"""
        categorie = Categorie.objects.get(nom_categorie='Sécurité informatique')

        questions_data = [
            {
                'titre': 'Votre antivirus est-il actif et à jour ?',
                'description': 'Vérifiez l\'état de votre protection antivirus',
                'type_question': 'choix_unique',
                'ordre': 1,
                'est_critique': True,
                'temps_moyen': 60,
                'niveau_difficulte': 'moyen',
                'tags': ['antivirus', 'securite'],
                'choix': [
                    {'texte': 'Oui, antivirus actif et à jour', 'valeur': 'ok', 'score_criticite': 0},
                    {'texte': 'Antivirus actif mais pas à jour', 'valeur': 'pas_a_jour', 'score_criticite': 5},
                    {'texte': 'Antivirus désactivé', 'valeur': 'desactive', 'score_criticite': 8},
                    {'texte': 'Je ne sais pas', 'valeur': 'inconnu', 'score_criticite': 6}
                ]
            },
            {
                'titre': 'Avez-vous des difficultés d\'accès à certains systèmes ?',
                'description': 'Problèmes de connexion ou de mots de passe',
                'type_question': 'choix_unique',
                'ordre': 2,
                'est_critique': False,
                'temps_moyen': 30,
                'niveau_difficulte': 'facile',
                'tags': ['acces', 'authentification'],
                'choix': [
                    {'texte': 'Aucun problème d\'accès', 'valeur': 'ok', 'score_criticite': 0},
                    {'texte': 'Oubli fréquent de mots de passe', 'valeur': 'mot_de_passe', 'score_criticite': 2},
                    {'texte': 'Accès refusé à certains systèmes', 'valeur': 'refuse', 'score_criticite': 6},
                    {'texte': 'Compte bloqué ou suspendu', 'valeur': 'bloque', 'score_criticite': 8}
                ]
            }
        ]

        self.create_questions_for_category(categorie, questions_data)

    def create_performance_questions(self):
        """Questions pour la performance système"""
        categorie = Categorie.objects.get(nom_categorie='Performance système')

        questions_data = [
            {
                'titre': 'Comment évaluez-vous la vitesse générale de votre ordinateur ?',
                'description': 'Considérez le démarrage, l\'ouverture des programmes, etc.',
                'type_question': 'choix_unique',
                'ordre': 1,
                'est_critique': True,
                'temps_moyen': 30,
                'niveau_difficulte': 'facile',
                'tags': ['performance', 'vitesse'],
                'choix': [
                    {'texte': 'Très rapide, aucun problème', 'valeur': 'rapide', 'score_criticite': 0},
                    {'texte': 'Correct, parfois un peu lent', 'valeur': 'correct', 'score_criticite': 2},
                    {'texte': 'Lent, mais utilisable', 'valeur': 'lent', 'score_criticite': 5},
                    {'texte': 'Très lent, difficile à utiliser', 'valeur': 'tres_lent', 'score_criticite': 8}
                ]
            },
            {
                'titre': 'Votre ordinateur se bloque-t-il ou redémarre-t-il de façon inattendue ?',
                'description': 'Écrans bleus, blocages complets, redémarrages',
                'type_question': 'choix_unique',
                'ordre': 2,
                'est_critique': True,
                'temps_moyen': 30,
                'niveau_difficulte': 'facile',
                'tags': ['stabilite', 'blocage', 'crash'],
                'choix': [
                    {'texte': 'Non, très stable', 'valeur': 'stable', 'score_criticite': 0},
                    {'texte': 'Blocages occasionnels (moins d\'1 fois par semaine)', 'valeur': 'occasionnel', 'score_criticite': 4},
                    {'texte': 'Blocages fréquents (plusieurs fois par semaine)', 'valeur': 'frequent', 'score_criticite': 7},
                    {'texte': 'Blocages très fréquents (quotidiens)', 'valeur': 'quotidien', 'score_criticite': 10}
                ]
            },
            {
                'titre': 'À quand remonte le dernier nettoyage/maintenance de votre PC ?',
                'description': 'Nettoyage des fichiers temporaires, défragmentation, etc.',
                'type_question': 'choix_unique',
                'ordre': 3,
                'est_critique': False,
                'temps_moyen': 20,
                'niveau_difficulte': 'facile',
                'tags': ['maintenance', 'nettoyage'],
                'choix': [
                    {'texte': 'Moins d\'un mois', 'valeur': 'recent', 'score_criticite': 0},
                    {'texte': 'Il y a 1-3 mois', 'valeur': 'moyen', 'score_criticite': 1},
                    {'texte': 'Il y a plus de 6 mois', 'valeur': 'ancien', 'score_criticite': 3},
                    {'texte': 'Jamais ou je ne sais pas', 'valeur': 'jamais', 'score_criticite': 5}
                ]
            }
        ]

        self.create_questions_for_category(categorie, questions_data)

    def create_questions_for_category(self, categorie, questions_data):
        """Utilitaire pour créer les questions d'une catégorie"""
        for q_data in questions_data:
            question = QuestionDiagnostic.objects.create(
                titre=q_data['titre'],
                description=q_data['description'],
                type_question=q_data['type_question'],
                ordre=q_data['ordre'],
                categorie=categorie,
                est_critique=q_data['est_critique'],
                temps_moyen=q_data['temps_moyen'],
                niveau_difficulte=q_data['niveau_difficulte'],
                tags=q_data['tags']
            )

            # Créer les choix de réponse s'il y en a
            if 'choix' in q_data:
                for ordre, choix_data in enumerate(q_data['choix']):
                    ChoixReponse.objects.create(
                        question=question,
                        texte=choix_data['texte'],
                        valeur=choix_data['valeur'],
                        score_criticite=choix_data['score_criticite'],
                        ordre=ordre
                    )

            self.stdout.write(f'  ✓ Question créée: {question.titre}')

    def create_diagnostic_templates(self, force):
        """Créer des templates de diagnostic"""
        if force:
            TemplateDiagnostic.objects.all().delete()
            TemplateQuestion.objects.all().delete()

        # Template pour diagnostic rapide matériel
        template_materiel, created = TemplateDiagnostic.objects.get_or_create(
            nom='Diagnostic rapide matériel',
            defaults={
                'description': 'Diagnostic express pour les problèmes matériels courants',
                'categorie': Categorie.objects.get(nom_categorie='Matériel informatique'),
                'est_lineaire': True,
                'permettre_saut': False,
                'afficher_progression': True,
                'afficher_temps_estime': True,
                'couleur_principale': '#4F46E5'
            }
        )

        if created:
            self.stdout.write(f'✓ Template créé: {template_materiel.nom}')

    def create_diagnostic_rules(self, force):
        """Créer des règles de diagnostic automatique"""
        if force:
            RegleDiagnostic.objects.all().delete()

        rules_data = [
            {
                'nom': 'Problème critique matériel',
                'description': 'Crée automatiquement un ticket si problème matériel critique',
                'categorie': Categorie.objects.get(nom_categorie='Matériel informatique'),
                'type_declencheur': 'session_fin',
                'conditions': {'score_total': {'>=': 8}},
                'type_action': 'creer_ticket',
                'parametres_action': {'priorite': 'urgent', 'assigner_auto': True},
                'priorite': 1
            },
            {
                'nom': 'Réseau inaccessible',
                'description': 'Alerte si aucun accès réseau détecté',
                'categorie': Categorie.objects.get(nom_categorie='Réseau et Internet'),
                'type_declencheur': 'session_fin',
                'conditions': {'score_total': {'>=': 9}},
                'type_action': 'creer_ticket',
                'parametres_action': {'priorite': 'critique', 'notifier_admin': True},
                'priorite': 1
            }
        ]

        for rule_data in rules_data:
            rule, created = RegleDiagnostic.objects.get_or_create(
                nom=rule_data['nom'],
                defaults=rule_data
            )
            if created:
                self.stdout.write(f'✓ Règle créée: {rule.nom}')

    def create_test_users(self, force):
        """Créer des utilisateurs de test"""
        # Créer un utilisateur employé de test
        if not CustomUser.objects.filter(email='employe.test@entreprise.com').exists():
            user = CustomUser.objects.create_user(
                email='employe.test@entreprise.com',
                password='test123',
                first_name='Employé',
                last_name='Test',
                role='employe',
                departement=Departement.objects.get(nom_departement='Informatique')
            )
            self.stdout.write(f'✓ Utilisateur test créé: {user.email}')

        # Créer un technicien de test
        if not CustomUser.objects.filter(email='technicien.test@entreprise.com').exists():
            user = CustomUser.objects.create_user(
                email='technicien.test@entreprise.com',
                password='test123',
                first_name='Technicien',
                last_name='Test',
                role='technicien',
                departement=Departement.objects.get(nom_departement='Informatique')
            )
            self.stdout.write(f'✓ Technicien test créé: {user.email}')
