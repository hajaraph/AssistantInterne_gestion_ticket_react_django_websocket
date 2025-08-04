from datetime import datetime, timedelta

from django.db.models.aggregates import Count, Avg, Sum
from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Ticket, Categorie, Equipement, Departement, SessionDiagnostic, TemplateDiagnostic, \
    DiagnosticSysteme, HistoriqueDiagnostic, QuestionDiagnostic, Commentaire
from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    TicketCreateSerializer,
    TicketListSerializer,
    CategorieSerializer,
    EquipementSerializer,
    DepartementSerializer, CommentaireSerializer, CommentaireCreateSerializer,
    SessionDiagnosticCreateSerializer, SessionDiagnosticSerializer,
    QuestionDiagnosticSerializer, ReponseDiagnosticCreateSerializer, ReponseDiagnosticAvanceSerializer,
    TemplateDiagnosticSerializer, SessionStatistiquesSerializer,
    SessionDiagnosticDetailSerializer, QuestionDiagnosticAvanceSerializer
)

class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def post(request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': 'User registered successfully',
                    'user_id': user.id,
                    'email': user.email,
                    'role': user.role
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view that uses our custom serializer.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(APIView):
    """
    View to get or update the authenticated user's profile.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        """Get the authenticated user's profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @staticmethod
    def put(request):
        """Update the authenticated user's profile"""
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    View for changing user password.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response(
                {"old_password": ["Wrong password."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        return Response(
            {"message": "Password updated successfully"},
            status=status.HTTP_200_OK
        )


class TicketCreateView(generics.CreateAPIView):
    """
    Vue pour créer un nouveau ticket (réservée aux employés).
    """
    serializer_class = TicketCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Associer l'utilisateur actuel comme créateur du ticket."""
        # Vérifier que l'utilisateur est un employé
        if self.request.user.role != 'employe':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les employés peuvent créer des tickets.")

        serializer.save(utilisateur_createur=self.request.user)


class MyTicketsView(generics.ListAPIView):
    """
    Vue pour lister les tickets créés par l'utilisateur connecté.
    """
    serializer_class = TicketListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retourner seulement les tickets créés par l'utilisateur connecté."""
        return Ticket.objects.filter(
            utilisateur_createur=self.request.user
        ).select_related('categorie', 'equipement', 'utilisateur_createur', 'technicien_assigne')


class TicketDetailView(generics.RetrieveAPIView):
    """
    Vue pour voir les détails d'un ticket.
    Les employés ne peuvent voir que leurs propres tickets.
    """
    serializer_class = TicketListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtrer selon le rôle de l'utilisateur."""
        user = self.request.user
        queryset = Ticket.objects.select_related('categorie', 'equipement', 'utilisateur_createur',
                                                 'technicien_assigne')

        if user.role == 'employe':
            # Les employés ne voient que leurs propres tickets
            return queryset.filter(utilisateur_createur=user)
        elif user.role == 'technicien':
            # Les techniciens voient leurs tickets assignés et ceux qu'ils ont créés
            return queryset.filter(
                Q(technicien_assigne=user) | Q(utilisateur_createur=user)
            )
        elif user.role == 'admin':
            # Les admins voient tous les tickets
            return queryset

        return queryset.none()


class CategorieListView(generics.ListAPIView):
    """
    Vue pour lister toutes les catégories disponibles.
    """
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    permission_classes = [IsAuthenticated]


class EquipementListView(generics.ListAPIView):
    """
    Vue pour lister les équipements disponibles.
    """
    serializer_class = EquipementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtrer les équipements selon le département de l'utilisateur si nécessaire."""
        user = self.request.user
        queryset = Equipement.objects.select_related('departement')

        # Optionnel : filtrer par département de l'utilisateur
        if user.departement:
            return queryset.filter(departement=user.departement)

        return queryset


class DepartementListView(generics.ListAPIView):
    """
    Vue pour lister tous les départements.
    """
    queryset = Departement.objects.all()
    serializer_class = DepartementSerializer
    permission_classes = [IsAuthenticated]


class TicketStatsView(APIView):
    """
    Vue pour obtenir des statistiques sur les tickets de l'utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        """Retourner les statistiques des tickets de l'utilisateur."""
        user = request.user

        if user.role == 'employe':
            # Statistiques pour les employés (leurs propres tickets)
            tickets = Ticket.objects.filter(utilisateur_createur=user)
        elif user.role == 'technicien':
            # Statistiques pour les techniciens (tickets assignés)
            tickets = Ticket.objects.filter(technicien_assigne=user)
        else:
            # Statistiques pour les admins (tous les tickets)
            tickets = Ticket.objects.all()

        stats = {
            'total': tickets.count(),
            'ouvert': tickets.filter(statut_ticket='ouvert').count(),
            'en_cours': tickets.filter(statut_ticket='en cours').count(),
            'resolu': tickets.filter(statut_ticket='resolu').count(),
            'ferme': tickets.filter(statut_ticket='ferme').count(),
            'priorite_critique': tickets.filter(priorite='critique').count(),
            'priorite_urgent': tickets.filter(priorite='urgent').count(),
        }

        return Response(stats)


class TechnicianTicketsView(generics.ListAPIView):
    """
    Vue pour lister tous les tickets disponibles pour les techniciens.
    Inclut les tickets non assignés et ceux assignés au technicien connecté.
    """
    serializer_class = TicketListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retourner les tickets pour les techniciens."""
        user = self.request.user

        if user.role == 'technicien':
            # Techniciens voient : tickets non assignés + leurs tickets assignés
            return Ticket.objects.filter(
                Q(technicien_assigne=None) | Q(technicien_assigne=user)
            ).select_related('categorie', 'equipement', 'utilisateur_createur', 'technicien_assigne')
        elif user.role == 'admin':
            # Admins voient tous les tickets
            return Ticket.objects.all().select_related('categorie', 'equipement', 'utilisateur_createur',
                                                       'technicien_assigne')

        # Autres rôles n'ont pas accès
        return Ticket.objects.none()


class AssignTicketToSelfView(APIView):
    """
    Vue pour qu'un technicien prenne en charge un ticket.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, ticket_id):
        """Assigner le ticket au technicien connecté."""
        user = request.user

        # Vérifier que l'utilisateur est un technicien
        if user.role != 'technicien':
            return Response(
                {'error': 'Seuls les techniciens peuvent prendre en charge des tickets'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            ticket = Ticket.objects.get(id=ticket_id)

            # Vérifier que le ticket n'est pas déjà assigné
            if ticket.technicien_assigne:
                return Response(
                    {'error': 'Ce ticket est déjà assigné à un autre technicien'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Assigner le ticket et changer le statut
            ticket.technicien_assigne = user
            ticket.statut_ticket = 'en_cours'
            ticket.save()

            # Créer un commentaire automatique
            from .models import Commentaire
            Commentaire.objects.create(
                ticket=ticket,
                utilisateur_auteur=user,
                contenu=f"Ticket pris en charge par {user.get_full_name() or user.email}",
                type_action='assignation'
            )

            serializer = TicketListSerializer(ticket)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            return Response(
                {'error': 'Ticket non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )


class UpdateTicketStatusView(APIView):
    """
    Vue pour mettre à jour le statut d'un ticket.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def patch(request, ticket_id):
        """Mettre à jour le statut du ticket."""
        user = request.user
        new_status = request.data.get('statut_ticket')

        if not new_status:
            return Response(
                {'error': 'Le statut est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier que le statut est valide
        valid_statuses = ['ouvert', 'en_cours', 'resolu', 'ferme', 'annule']
        if new_status not in valid_statuses:
            return Response(
                {'error': 'Statut invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ticket = Ticket.objects.get(id=ticket_id)

            # Vérifier les permissions selon le rôle et le changement de statut
            if user.role == 'employe':
                # Les employés peuvent seulement :
                # - Fermer leurs propres tickets qui sont "résolu"
                # - Rouvrir leurs tickets fermés
                if ticket.utilisateur_createur != user:
                    return Response(
                        {'error': 'Vous ne pouvez modifier que vos propres tickets'},
                        status=status.HTTP_403_FORBIDDEN
                    )

                # Vérifier les transitions autorisées pour l'employé
                if new_status == 'ferme' and ticket.statut_ticket != 'resolu':
                    return Response(
                        {'error': 'Vous ne pouvez fermer que des tickets résolus'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif new_status == 'ouvert' and ticket.statut_ticket != 'ferme':
                    return Response(
                        {'error': 'Vous ne pouvez rouvrir que des tickets fermés'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif new_status not in ['ferme', 'ouvert']:
                    return Response(
                        {'error': 'Vous ne pouvez que fermer ou rouvrir vos tickets'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            elif user.role == 'technicien':
                # Les techniciens peuvent modifier leurs tickets assignés
                if ticket.technicien_assigne != user:
                    return Response(
                        {'error': 'Vous ne pouvez modifier que vos tickets assignés'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                # Les techniciens ne peuvent pas fermer directement, seulement marquer comme "résolu"
                if new_status == 'ferme':
                    return Response(
                        {'error': 'Seul l\'employé peut fermer le ticket après vérification'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            elif user.role == 'admin':
                # Les admins peuvent tout faire
                pass
            else:
                return Response(
                    {'error': 'Permissions insuffisantes'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Sauvegarder l'ancien statut pour le commentaire
            old_status = ticket.statut_ticket

            # Logique spéciale pour la réouverture
            if new_status == 'ouvert' and old_status == 'ferme':
                # Quand un ticket est rouvert, on retire l'assignation pour qu'il redevienne disponible
                ticket.technicien_assigne = None

            ticket.statut_ticket = new_status
            ticket.save()

            # Créer un commentaire automatique
            from .models import Commentaire
            status_display = {
                'ouvert': 'Ouvert',
                'en_cours': 'En cours',
                'resolu': 'Résolu',
                'ferme': 'Fermé',
                'annule': 'Annulé'
            }

            Commentaire.objects.create(
                ticket=ticket,
                utilisateur_auteur=user,
                contenu=f"Statut changé de '{status_display.get(old_status, old_status)}' vers '{status_display.get(new_status, new_status)}'",
                type_action='changement_statut'
            )

            serializer = TicketListSerializer(ticket)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            return Response(
                {'error': 'Ticket non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )


class TicketCommentsView(APIView):
    """
    Vue pour gérer les commentaires d'un ticket.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request, ticket_id):
        """Récupérer les commentaires d'un ticket."""
        try:
            ticket = Ticket.objects.get(id=ticket_id)

            # Vérifier les permissions d'accès au ticket
            user = request.user
            if user.role == 'employe':
                # L'employé peut voir les commentaires de ses propres tickets
                if ticket.utilisateur_createur != user:
                    return Response(
                        {'error': 'Accès refusé'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif user.role == 'technicien':
                # Le technicien peut voir les commentaires des tickets qui lui sont assignés OU qu'il a créés
                if ticket.technicien_assigne != user and ticket.utilisateur_createur != user:
                    return Response(
                        {'error': 'Accès refusé'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif user.role != 'admin':
                # Autres rôles n'ont pas accès
                return Response(
                    {'error': 'Accès refusé'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Récupérer seulement les commentaires principaux (sans parent)
            comments = ticket.commentaires.filter(commentaire_parent=None).order_by('date_commentaire')
            serializer = CommentaireSerializer(comments, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            return Response(
                {'error': 'Ticket non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

    @staticmethod
    def post(request, ticket_id):
        """Ajouter un commentaire à un ticket."""
        try:
            ticket = Ticket.objects.get(id=ticket_id)

            # Vérifier les permissions
            user = request.user
            if user.role == 'employe' and ticket.utilisateur_createur != user:
                return Response(
                    {'error': 'Accès refusé'},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif user.role == 'technicien' and ticket.technicien_assigne != user:
                return Response(
                    {'error': 'Vous ne pouvez commenter que vos tickets assignés'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Utiliser le nouveau serializer pour la création
            serializer = CommentaireCreateSerializer(
                data=request.data,
                context={'request': request, 'ticket': ticket}
            )

            if serializer.is_valid():
                comment = serializer.save(ticket=ticket)

                # Retourner le commentaire créé avec toutes les informations
                response_serializer = CommentaireSerializer(comment, context={'request': request})

                # Envoi de la notification WebSocket
                # channel_layer = get_channel_layer()
                # async_to_sync(channel_layer.group_send)(
                #     f"ticket_{ticket.id}",
                #     {
                #         "type": "ticket_update",
                #         "message": f"Nouveau commentaire sur le ticket {ticket.id} : {comment.contenu}",
                #         "ticket_id": ticket.id,
                #         "commentaire": response_serializer.data
                #     }
                # )

                return Response(response_serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Ticket.DoesNotExist:
            return Response(
                {'error': 'Ticket non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )


class StartGuidanceView(APIView):
    """
    Vue pour démarrer une session de guidage à distance.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, ticket_id):
        """Démarrer le guidage à distance pour un ticket."""
        user = request.user

        # Seuls les techniciens peuvent démarrer un guidage
        if user.role != 'technicien':
            return Response(
                {'error': 'Seuls les techniciens peuvent démarrer un guidage'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            ticket = Ticket.objects.get(id=ticket_id)

            # Vérifier que le ticket est assigné au technicien
            if ticket.technicien_assigne != user:
                return Response(
                    {'error': 'Vous devez être assigné à ce ticket pour démarrer un guidage'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Créer un commentaire pour marquer le début du guidage
            from .models import Commentaire
            comment = Commentaire.objects.create(
                ticket=ticket,
                utilisateur_auteur=user,
                contenu="🔧 Session de guidage à distance démarrée. Je vais vous guider étape par étape pour résoudre votre problème.",
                type_action='guidage_debut'
            )

            # Optionnel : changer le statut du ticket si nécessaire
            if ticket.statut_ticket == 'ouvert':
                ticket.statut_ticket = 'en_cours'
                ticket.save()

            serializer = CommentaireSerializer(comment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Ticket.DoesNotExist:
            return Response(
                {'error': 'Ticket non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )


class SendInstructionView(APIView):
    """
    Vue pour envoyer une instruction de guidage.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, ticket_id):
        """Envoyer une instruction étape par étape."""
        user = request.user

        if user.role != 'technicien':
            return Response(
                {'error': 'Seuls les techniciens peuvent envoyer des instructions'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            ticket = Ticket.objects.get(id=ticket_id)

            if ticket.technicien_assigne != user:
                return Response(
                    {'error': 'Vous devez être assigné à ce ticket'},
                    status=status.HTTP_403_FORBIDDEN
                )

            instruction = request.data.get('instruction', '').strip()
            numero_etape = request.data.get('numero_etape')
            attendre_confirmation = request.data.get('attendre_confirmation', True)

            if not instruction:
                return Response(
                    {'error': 'L\'instruction ne peut pas être vide'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Créer l'instruction
            from .models import Commentaire
            comment = Commentaire.objects.create(
                ticket=ticket,
                utilisateur_auteur=user,
                contenu=instruction,
                type_action='instruction',
                est_instruction=True,
                numero_etape=numero_etape,
                attendre_confirmation=attendre_confirmation
            )

            serializer = CommentaireSerializer(comment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Ticket.DoesNotExist:
            return Response(
                {'error': 'Ticket non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )


class ConfirmInstructionView(APIView):
    """
    Vue pour confirmer qu'une instruction a été suivie.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, comment_id):
        """Confirmer qu'une instruction a été suivie."""
        user = request.user

        if user.role != 'employe':
            return Response(
                {'error': 'Seuls les employés peuvent confirmer des instructions'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            comment = Commentaire.objects.get(id=comment_id)

            # Vérifier que l'employé peut confirmer cette instruction
            if comment.ticket.utilisateur_createur != user:
                return Response(
                    {'error': 'Vous ne pouvez confirmer que les instructions de vos propres tickets'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if not comment.est_instruction:
                return Response(
                    {'error': 'Ce commentaire n\'est pas une instruction'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if comment.est_confirme:
                return Response(
                    {'error': 'Cette instruction a déjà été confirmée'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Marquer comme confirmé
            comment.marquer_comme_confirme()

            # Envoyer une notification WebSocket pour mettre à jour l'instruction
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            from .serializers import CommentaireSerializer

            channel_layer = get_channel_layer()
            if channel_layer:
                # Sérialiser l'instruction mise à jour
                updated_instruction_serializer = CommentaireSerializer(comment, context={'request': request})

                # Envoyer la mise à jour de l'instruction à tous les clients connectés
                async_to_sync(channel_layer.group_send)(
                    f"ticket_{comment.ticket.id}",
                    {
                        "type": "instruction_updated",
                        "instruction": updated_instruction_serializer.data
                    }
                )

            # Retourner l'instruction mise à jour au lieu d'un commentaire de confirmation
            serializer = CommentaireSerializer(comment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Commentaire.DoesNotExist:
            return Response(
                {'error': 'Instruction non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class EndGuidanceView(APIView):
    """
    Vue pour terminer une session de guidage.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, ticket_id):
        """Terminer la session de guidage."""
        user = request.user

        if user.role != 'technicien':
            return Response(
                {'error': 'Seuls les techniciens peuvent terminer un guidage'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            ticket = Ticket.objects.get(id=ticket_id)

            if ticket.technicien_assigne != user:
                return Response(
                    {'error': 'Vous devez être assigné à ce ticket'},
                    status=status.HTTP_403_FORBIDDEN
                )

            message_fin = request.data.get('message',
                                           'Session de guidage terminée. Le problème devrait maintenant être résolu.')
            resolu = request.data.get('resolu', False)

            # Créer un commentaire de fin de guidage
            from .models import Commentaire
            comment = Commentaire.objects.create(
                ticket=ticket,
                utilisateur_auteur=user,
                contenu=f"{message_fin}",
                type_action='guidage_fin'
            )

            # Marquer le ticket comme résolu si demandé
            if resolu:
                ticket.statut_ticket = 'resolu'
                ticket.save()

                # Ajouter un commentaire de résolution
                Commentaire.objects.create(
                    ticket=ticket,
                    utilisateur_auteur=user,
                    contenu="Ticket marqué comme résolu suite au guidage à distance.",
                    type_action='resolution'
                )

            serializer = CommentaireSerializer(comment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Ticket.DoesNotExist:
            return Response(
                {'error': 'Ticket non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )


class DiagnosticCategoriesView(APIView):
    """Vue pour obtenir les catégories disponibles pour le diagnostic"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        categories = Categorie.objects.filter(questions_diagnostic__isnull=False).distinct()
        serializer = CategorieSerializer(categories, many=True)
        return Response(serializer.data)


class SessionDiagnosticCreateView(APIView):
    """Vue pour créer une nouvelle session de diagnostic"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):
        serializer = SessionDiagnosticCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            session = serializer.save()

            # Lancer le diagnostic système automatique
            from .diagnostic_engine import DiagnosticSystemeEngine
            diagnostic_engine = DiagnosticSystemeEngine(session)
            diagnostic_engine.executer_diagnostic_complet()

            return Response({
                'session_id': session.id,
                'message': 'Session de diagnostic créée avec succès'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SessionDiagnosticDetailView(APIView):
    """Vue pour obtenir les détails d'une session de diagnostic"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request, session_id):
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user
            )
            serializer = SessionDiagnosticSerializer(session)
            return Response(serializer.data)
        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class ProchaineQuestionView(APIView):
    """Vue pour obtenir la prochaine question du diagnostic"""
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user,
                statut='en_cours'
            )

            from .diagnostic_engine import ArbreDecisionEngine
            arbre_engine = ArbreDecisionEngine(session)
            prochaine_question = arbre_engine.obtenir_prochaine_question()

            if prochaine_question:
                serializer = QuestionDiagnosticSerializer(prochaine_question)
                return Response(serializer.data)
            else:
                # Plus de questions, finaliser la session
                return self.finaliser_session(session, arbre_engine)

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

    @staticmethod
    def finaliser_session(session, arbre_engine):
        """Finalise la session de diagnostic"""
        from django.utils import timezone

        # Calculer la priorité et les recommandations
        priorite, score_total = arbre_engine.calculer_priorite_estimee()
        recommandations = arbre_engine.generer_recommandations()

        # Mettre à jour la session
        session.statut = 'complete'
        session.score_criticite_total = score_total
        session.priorite_estimee = priorite
        session.recommandations = recommandations
        session.date_completion = timezone.now()
        session.save()

        return Response({
            'session_complete': True,
            'priorite_estimee': priorite,
            'score_total': score_total,
            'recommandations': recommandations,
            'message': 'Diagnostic terminé avec succès'
        })


class RepondreDiagnosticView(APIView):
    """Vue pour répondre à une question de diagnostic"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, session_id):
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user,
                statut='en_cours'
            )

            serializer = ReponseDiagnosticCreateSerializer(
                data=request.data,
                context={'session': session}
            )

            if serializer.is_valid():
                reponse = serializer.save()

                # Mettre à jour le score total de la session
                session.score_criticite_total = sum(
                    r.score_criticite for r in session.reponses.all()
                )
                session.save()

                return Response({
                    'reponse_id': reponse.id,
                    'score_criticite': reponse.score_criticite,
                    'message': 'Réponse enregistrée avec succès'
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class DiagnosticSystemeView(APIView):
    """Vue pour relancer le diagnostic système"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, session_id):
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user
            )

            # Supprimer les anciens diagnostics
            session.diagnostics_systeme.all().delete()

            # Relancer le diagnostic
            from .diagnostic_engine import DiagnosticSystemeEngine
            diagnostic_engine = DiagnosticSystemeEngine(session)
            resultats = diagnostic_engine.executer_diagnostic_complet()

            return Response({
                'message': 'Diagnostic système mis à jour',
                'resultats': resultats
            })

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class HistoriqueDiagnosticsView(APIView):
    """Vue pour obtenir l'historique des diagnostics de l'utilisateur"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        sessions = SessionDiagnostic.objects.filter(
            utilisateur=request.user
        ).order_by('-date_creation')[:20]  # 20 dernières sessions

        serializer = SessionDiagnosticSerializer(sessions, many=True)
        return Response(serializer.data)


class CreerTicketDepuisDiagnosticView(APIView):
    """Vue pour créer un ticket à partir d'une session de diagnostic"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, session_id):
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user,
                statut='complete'
            )

            # Vérifier qu'un ticket n'existe pas déjà
            ticket_existant = Ticket.objects.filter(
                titre__icontains=f"Diagnostic - Session {session.id}"
            ).first()

            if ticket_existant:
                return Response({
                    'error': 'Un ticket existe déjà pour cette session de diagnostic',
                    'ticket_id': ticket_existant.id
                }, status=status.HTTP_400_BAD_REQUEST)

            # Créer le ticket
            ticket = Ticket.objects.create(
                titre=f"Diagnostic automatique - Session {session.id}",
                description=f"Diagnostic automatique avec priorité {session.priorite_estimee}.\n\n"
                           f"Score de criticité: {session.score_criticite_total}\n\n"
                           f"Recommandations:\n{session.recommandations}",
                priorite=session.priorite_estimee,
                categorie=session.categorie,
                utilisateur_createur=request.user,
                statut_ticket='ouvert'
            )

            return Response({
                'ticket_id': ticket.id,
                'message': 'Ticket créé avec succès à partir du diagnostic'
            }, status=status.HTTP_201_CREATED)

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


# Nouvelles vues pour les fonctionnalités avancées

class TemplatesDiagnosticView(APIView):
    """Vue pour gérer les templates de diagnostic"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        templates = TemplateDiagnostic.objects.filter(est_actif=True)
        categorie_id = request.query_params.get('categorie')

        if categorie_id:
            templates = templates.filter(categorie_id=categorie_id)

        serializer = TemplateDiagnosticSerializer(templates, many=True)
        return Response(serializer.data)


class SessionStatistiquesView(APIView):
    """Vue pour obtenir les statistiques d'une session"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request, session_id):
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user
            )

            # Calculer les statistiques
            reponses = session.reponses.all()
            diagnostics = session.diagnostics_systeme.all()

            # Questions totales disponibles pour cette catégorie
            questions_totales = QuestionDiagnostic.objects.filter(
                categorie=session.categorie,
                actif=True
            ).count()

            statistiques = {
                'nombre_questions_repondues': reponses.count(),
                'temps_total_passe': session.temps_total_passe,
                'score_moyen': reponses.aggregate(
                    avg_score=Avg('score_criticite')
                )['avg_score'] or 0,
                'nombre_diagnostics_erreur': diagnostics.filter(statut='erreur').count(),
                'nombre_diagnostics_avertissement': diagnostics.filter(statut='avertissement').count(),
                'progression_pourcentage': (reponses.count() / questions_totales * 100) if questions_totales > 0 else 0,
                'questions_critiques_repondues': reponses.filter(
                    question__est_critique=True
                ).count(),
                'derniere_activite': session.date_derniere_activite
            }

            serializer = SessionStatistiquesSerializer(statistiques)
            return Response(serializer.data)

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class SessionReprendreView(APIView):
    """Vue pour reprendre une session en pause ou abandonnée"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, session_id):
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user,
                statut__in=['en_pause', 'abandonnee']
            )

            # Reprendre la session
            session.statut = 'en_cours'
            session.save()

            # Enregistrer dans l'historique
            HistoriqueDiagnostic.objects.create(
                session=session,
                action='reprise',
                utilisateur=request.user,
                details={'ancien_statut': session.statut}
            )

            return Response({
                'message': 'Session reprise avec succès',
                'session_id': session.id
            })

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée ou non reprennable'},
                status=status.HTTP_404_NOT_FOUND
            )


class SessionPauseView(APIView):
    """Vue pour mettre en pause une session"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, session_id):
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user,
                statut='en_cours'
            )

            # Mettre en pause
            session.statut = 'en_pause'
            session.save()

            # Enregistrer dans l'historique
            HistoriqueDiagnostic.objects.create(
                session=session,
                action='pause',
                utilisateur=request.user,
                details={'raison': request.data.get('raison', 'Pause utilisateur')}
            )

            return Response({
                'message': 'Session mise en pause',
                'session_id': session.id
            })

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class ReponseAvanceeView(APIView):
    """Vue pour répondre avec fonctionnalités avancées (temps, incertitude, commentaire)"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, session_id):
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user,
                statut='en_cours'
            )

            serializer = ReponseDiagnosticAvanceSerializer(
                data=request.data,
                context={'session': session}
            )

            if serializer.is_valid():
                reponse = serializer.save()

                # Mettre à jour le score total et le temps de la session
                session.score_criticite_total = sum(
                    r.score_criticite for r in session.reponses.all()
                )
                session.temps_total_passe += request.data.get('temps_passe', 0)
                session.save()

                return Response({
                    'reponse_id': reponse.id,
                    'score_criticite': reponse.score_criticite,
                    'message': 'Réponse enregistrée avec succès'
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class QuestionAvanceeView(APIView):
    """Vue pour obtenir une question avec métadonnées avancées"""
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user,
                statut='en_cours'
            )

            from .diagnostic_engine import ArbreDecisionEngine
            arbre_engine = ArbreDecisionEngine(session)
            prochaine_question = arbre_engine.obtenir_prochaine_question()

            if prochaine_question:
                serializer = QuestionDiagnosticAvanceSerializer(prochaine_question)
                return Response(serializer.data)
            else:
                # Plus de questions, finaliser la session
                return self.finaliser_session(session, arbre_engine)

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

    @staticmethod
    def finaliser_session(session, arbre_engine):
        """Finalise la session avec métadonnées avancées"""
        from django.utils import timezone

        # Calculer la priorité et les recommandations
        priorite, score_total = arbre_engine.calculer_priorite_estimee()
        recommandations = arbre_engine.generer_recommandations()

        # Mettre à jour la session
        session.statut = 'complete'
        session.score_criticite_total = score_total
        session.priorite_estimee = priorite
        session.recommandations = recommandations
        session.date_completion = timezone.now()
        session.score_confiance = session.calculer_score_confiance()
        session.save()

        # Enregistrer dans l'historique
        HistoriqueDiagnostic.objects.create(
            session=session,
            action='completion',
            utilisateur=session.utilisateur,
            details={
                'priorite_finale': priorite,
                'score_final': score_total,
                'score_confiance': float(session.score_confiance)
            }
        )

        return Response({
            'session_complete': True,
            'priorite_estimee': priorite,
            'score_total': score_total,
            'score_confiance': session.score_confiance,
            'recommandations': recommandations,
            'message': 'Diagnostic terminé avec succès'
        })


class DiagnosticAnalyticsView(APIView):
    """Vue pour les analytics des diagnostics (admin/technicien)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['admin', 'technicien']:
            return Response(
                {'error': 'Accès non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Statistiques globales
        analytics = {
            'sessions_totales': SessionDiagnostic.objects.count(),
            'sessions_completes': SessionDiagnostic.objects.filter(statut='complete').count(),
            'sessions_abandonnees': SessionDiagnostic.objects.filter(statut='abandonnee').count(),
            'moyenne_temps_completion': SessionDiagnostic.objects.filter(
                statut='complete'
            ).aggregate(
                avg_temps=models.Avg('temps_total_passe')
            )['avg_temps'] or 0,
            'repartition_priorites': {
                'critique': SessionDiagnostic.objects.filter(priorite_estimee='critique').count(),
                'urgent': SessionDiagnostic.objects.filter(priorite_estimee='urgent').count(),
                'normal': SessionDiagnostic.objects.filter(priorite_estimee='normal').count(),
                'faible': SessionDiagnostic.objects.filter(priorite_estimee='faible').count(),
            },
            'categories_populaires': list(
                SessionDiagnostic.objects.values('categorie__nom_categorie')
                .annotate(count=models.Count('id'))
                .order_by('-count')[:5]
            ),
            'diagnostics_systeme': {
                'erreurs': DiagnosticSysteme.objects.filter(statut='erreur').count(),
                'avertissements': DiagnosticSysteme.objects.filter(statut='avertissement').count(),
                'ok': DiagnosticSysteme.objects.filter(statut='ok').count(),
            }
        }

        return Response(analytics)


class DiagnosticAccueilView(APIView):
    """Vue pour l'écran d'accueil du diagnostic intelligent"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Statistiques personnelles de l'utilisateur
        sessions_utilisateur = SessionDiagnostic.objects.filter(utilisateur=user)

        # Sessions récentes (7 derniers jours)
        from django.utils import timezone
        from datetime import timedelta

        une_semaine = timezone.now() - timedelta(days=7)
        sessions_recentes = sessions_utilisateur.filter(
            date_creation__gte=une_semaine
        )

        # Catégories avec questions de diagnostic disponibles
        categories_disponibles = Categorie.objects.filter(
            questions_diagnostic__actif=True
        ).distinct().values('id', 'nom_categorie', 'description_categorie', 'couleur_affichage')

        # Enrichir les catégories avec le nombre de questions
        categories_enrichies = []
        for cat in categories_disponibles:
            nombre_questions = QuestionDiagnostic.objects.filter(
                categorie_id=cat['id'],
                actif=True
            ).count()

            temps_estime = QuestionDiagnostic.objects.filter(
                categorie_id=cat['id'],
                actif=True
            ).aggregate(
                temps_total=Sum('temps_moyen')
            )['temps_total'] or 0

            categories_enrichies.append({
                **cat,
                'nombre_questions': nombre_questions,
                'temps_estime_minutes': round(temps_estime / 60, 1) if temps_estime else 0,
                'icone': self._obtenir_icone_categorie(cat['nom_categorie'])
            })

        # Sessions en cours ou en pause de l'utilisateur
        sessions_en_cours = sessions_utilisateur.filter(
            statut__in=['en_cours', 'en_pause']
        ).values(
            'id', 'categorie__nom_categorie', 'statut',
            'date_creation', 'score_criticite_total'
        )

        # Statistiques personnelles
        stats_personnelles = {
            'total_sessions': sessions_utilisateur.count(),
            'sessions_completes': sessions_utilisateur.filter(statut='complete').count(),
            'sessions_cette_semaine': sessions_recentes.count(),
            'temps_moyen_session': sessions_utilisateur.filter(
                statut='complete'
            ).aggregate(
                avg_temps=Avg('temps_total_passe')
            )['avg_temps'] or 0,
            'derniere_session': self._serialiser_derniere_session(sessions_utilisateur.order_by('-date_creation').first()),
            'tickets_crees_auto': Ticket.objects.filter(
                utilisateur_createur=user,
                titre__icontains='Diagnostic automatique'
            ).count()
        }

        # Recommandations personnalisées
        recommandations = self._generer_recommandations_personnalisees(user, sessions_utilisateur)

        return Response({
            'utilisateur': {
                'nom_complet': f"{user.first_name} {user.last_name}".strip() or user.email,
                'email': user.email,
                'departement': user.departement.nom_departement if user.departement else 'Non spécifié',
                'role': user.get_role_display(),
            },
            'categories_disponibles': categories_enrichies,
            'sessions_en_cours': list(sessions_en_cours),
            'statistiques_personnelles': stats_personnelles,
            'recommandations': recommandations,
            'aide': {
                'comment_ca_marche': [
                    "1. Sélectionnez la catégorie qui correspond à votre problème",
                    "2. Le système analysera automatiquement votre ordinateur",
                    "3. Répondez aux questions pour affiner le diagnostic",
                    "4. Obtenez des recommandations personnalisées",
                    "5. Un ticket peut être créé automatiquement si nécessaire"
                ],
                'temps_estime_global': "Entre 3 et 10 minutes selon la complexité",
                'support_contact': "En cas de problème urgent, contactez directement le support technique"
            }
        })

    @staticmethod
    def _serialiser_derniere_session(session):
        """Sérialise la dernière session pour éviter l'erreur JSON"""
        if not session:
            return None

        return {
            'id': session.id,
            'categorie': session.categorie.nom_categorie,
            'statut': session.statut,
            'date_creation': session.date_creation.isoformat() if session.date_creation else None,
            'score_criticite_total': session.score_criticite_total,
            'priorite_estimee': session.priorite_estimee
        }

    @staticmethod
    def _obtenir_icone_categorie(nom_categorie: str) -> str:
        """Retourne un identifiant de catégorie pour le frontend"""
        categories_map = {
            'matériel': 'hardware',
            'hardware': 'hardware',
            'réseau': 'network',
            'network': 'network',
            'logiciel': 'software',
            'software': 'software',
            'sécurité': 'security',
            'security': 'security',
            'email': 'email',
            'messagerie': 'email',
            'impression': 'printer',
            'imprimante': 'printer',
            'performance': 'performance',
            'système': 'system',
            'system': 'system'
        }

        nom_lower = nom_categorie.lower()
        for cle, type_cat in categories_map.items():
            if cle in nom_lower:
                return type_cat

        return 'general'  # Type par défaut

    @staticmethod
    def _generer_recommandations_personnalisees(user, sessions) -> list[str]:
        """Génère des recommandations personnalisées pour l'utilisateur"""
        recommandations = []

        # Analyser l'historique de l'utilisateur
        if not sessions.exists():
            recommandations.append("Première utilisation ? Commencez par un diagnostic de performance générale")
        else:
            # Sessions récentes
            sessions_recentes = sessions.filter(
                date_creation__gte=datetime.now() - timedelta(days=30)
            )

            if sessions_recentes.filter(priorite_estimee__in=['urgent', 'critique']).exists():
                recommandations.append("Vous avez eu des problèmes critiques récemment. Surveillez votre système.")

            # Catégories fréquentes
            categorie_frequente = sessions.values('categorie__nom_categorie').annotate(
                count=Count('id')
            ).order_by('-count').first()

            if categorie_frequente and categorie_frequente['count'] >= 3:
                recommandations.append(
                    f"Vous diagnostiquez souvent '{categorie_frequente['categorie__nom_categorie']}'. "
                    f"Consultez les recommandations préventives."
                )

            # Sessions abandonnées
            sessions_abandonnees = sessions.filter(statut='abandonnee').count()
            if sessions_abandonnees >= 2:
                recommandations.append("Besoin d'aide ? N'hésitez pas à contacter le support technique.")

        # Recommandations basées sur le département
        if user.departement:
            # Analyser les problèmes fréquents du département
            problemes_dept = SessionDiagnostic.objects.filter(
                utilisateur__departement=user.departement,
                statut='complete',
                date_creation__gte=datetime.now() - timedelta(days=30)
            ).values('categorie__nom_categorie').annotate(
                count=Count('id')
            ).order_by('-count').first()

            if problemes_dept:
                recommandations.append(
                    f"Dans votre département, les problèmes '{problemes_dept['categorie__nom_categorie']}' "
                    f"sont fréquents. Diagnostic préventif recommandé."
                )

        if not recommandations:
            recommandations.append("Tout semble en ordre ! Un diagnostic préventif mensuel est recommandé.")

        return recommandations


class DiagnosticEtapesView(APIView):
    """Vue pour gérer le diagnostic par étapes"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Démarrer un nouveau diagnostic par étapes"""
        try:
            categorie_id = request.data.get('categorie')
            equipement_id = request.data.get('equipement')
            template_id = request.data.get('template')

            if not categorie_id:
                return Response(
                    {'error': 'La catégorie est requise'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Créer la session de diagnostic
            session_data = {
                'categorie': categorie_id,
                'equipement': equipement_id if equipement_id else None
            }

            serializer = SessionDiagnosticCreateSerializer(
                data=session_data,
                context={'request': request}
            )

            if serializer.is_valid():
                session = serializer.save()

                # Démarrer le diagnostic par étapes
                from .services.diagnostic_etapes_service import DiagnosticEtapesService
                etapes_service = DiagnosticEtapesService(session, template_id)
                plan_etapes = etapes_service.generer_plan_etapes()

                # Mettre à jour la session avec le plan d'étapes
                session.donnees_supplementaires['plan_etapes'] = plan_etapes
                session.donnees_supplementaires['etape_actuelle'] = 0
                session.donnees_supplementaires['etapes_completees'] = []
                session.save()

                return Response({
                    'session_id': session.id,
                    'plan_etapes': plan_etapes,
                    'etape_actuelle': plan_etapes[0] if plan_etapes else None,
                    'progression': {
                        'etape_courante': 1,
                        'total_etapes': len(plan_etapes),
                        'pourcentage': 0
                    }
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Erreur lors du démarrage du diagnostic par étapes: {e}")
            return Response(
                {'error': 'Erreur lors du démarrage du diagnostic'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, session_id):
        """Obtenir l'état actuel du diagnostic par étapes"""
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user
            )

            plan_etapes = session.donnees_supplementaires.get('plan_etapes', [])
            etape_actuelle_idx = session.donnees_supplementaires.get('etape_actuelle', 0)
            etapes_completees = session.donnees_supplementaires.get('etapes_completees', [])

            etape_actuelle = None
            if etape_actuelle_idx < len(plan_etapes):
                etape_actuelle = plan_etapes[etape_actuelle_idx]

            progression = {
                'etape_courante': etape_actuelle_idx + 1,
                'total_etapes': len(plan_etapes),
                'pourcentage': round((len(etapes_completees) / len(plan_etapes)) * 100) if plan_etapes else 0
            }

            return Response({
                'session_id': session.id,
                'statut': session.statut,
                'plan_etapes': plan_etapes,
                'etape_actuelle': etape_actuelle,
                'etapes_completees': etapes_completees,
                'progression': progression,
                'resultats_diagnostics': session.diagnostic_automatique,
                'score_total': session.score_criticite_total
            })

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class ExecuterEtapeView(APIView):
    """Vue pour exécuter une étape du diagnostic"""
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        """Exécuter l'étape actuelle du diagnostic"""
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user,
                statut='en_cours'
            )

            from .services.diagnostic_etapes_service import DiagnosticEtapesService
            etapes_service = DiagnosticEtapesService(session)

            # Exécuter l'étape actuelle
            resultat = etapes_service.executer_etape_actuelle(request.data)

            if resultat['success']:
                return Response({
                    'success': True,
                    'etape_completee': resultat['etape_completee'],
                    'resultat': resultat['resultat'],
                    'prochaine_etape': resultat.get('prochaine_etape'),
                    'progression': resultat['progression'],
                    'diagnostic_termine': resultat.get('diagnostic_termine', False)
                })
            else:
                return Response({
                    'success': False,
                    'error': resultat['error']
                }, status=status.HTTP_400_BAD_REQUEST)

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class PasserEtapeView(APIView):
    """Vue pour passer à l'étape suivante ou précédente"""
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        """Naviguer entre les étapes"""
        try:
            session = SessionDiagnostic.objects.get(
                id=session_id,
                utilisateur=request.user
            )

            direction = request.data.get('direction', 'suivante')  # 'suivante' ou 'precedente'

            plan_etapes = session.donnees_supplementaires.get('plan_etapes', [])
            etape_actuelle_idx = session.donnees_supplementaires.get('etape_actuelle', 0)

            if direction == 'suivante' and etape_actuelle_idx < len(plan_etapes) - 1:
                nouvelle_etape_idx = etape_actuelle_idx + 1
            elif direction == 'precedente' and etape_actuelle_idx > 0:
                nouvelle_etape_idx = etape_actuelle_idx - 1
            else:
                return Response({
                    'error': 'Navigation impossible dans cette direction'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Mettre à jour l'étape actuelle
            session.donnees_supplementaires['etape_actuelle'] = nouvelle_etape_idx
            session.save()

            nouvelle_etape = plan_etapes[nouvelle_etape_idx]

            progression = {
                'etape_courante': nouvelle_etape_idx + 1,
                'total_etapes': len(plan_etapes),
                'pourcentage': round((nouvelle_etape_idx / len(plan_etapes)) * 100)
            }

            return Response({
                'etape_actuelle': nouvelle_etape,
                'progression': progression
            })

        except SessionDiagnostic.DoesNotExist:
            return Response(
                {'error': 'Session de diagnostic non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

