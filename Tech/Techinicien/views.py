from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from .models import Ticket, Categorie, Equipement, Departement
from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    TicketCreateSerializer,
    TicketListSerializer,
    CategorieSerializer,
    EquipementSerializer,
    DepartementSerializer, CommentaireSerializer, CommentaireCreateSerializer
)


class UserRegistrationView(APIView):
    """
    View for user registration.
    Anyone can register a new user account.
    """
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

    def get(self, request):
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

    def post(self, request, ticket_id):
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

    def get(self, request, ticket_id):
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

    def post(self, request, ticket_id):
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

    def post(self, request, ticket_id):
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

    def post(self, request, comment_id):
        """Confirmer qu'une instruction a été suivie."""
        user = request.user

        if user.role != 'employe':
            return Response(
                {'error': 'Seuls les employés peuvent confirmer des instructions'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            from .models import Commentaire
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

    def post(self, request, ticket_id):
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
