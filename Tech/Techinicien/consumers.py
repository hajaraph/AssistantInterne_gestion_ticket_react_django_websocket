import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import Ticket, Commentaire
from .serializers import CommentaireSerializer

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer pour les notifications globales (nouveaux tickets, assignations, etc.)"""

    async def connect(self):
        # Vérifier l'authentification via le token JWT
        token = self.scope['query_string'].decode().split('token=')[-1]
        self.user = await self.get_user_from_token(token)

        if self.user is None:
            await self.close()
            return

        # Vérifier que l'utilisateur est un technicien ou admin
        if self.user.role not in ['technicien', 'admin']:
            await self.close()
            return

        # Rejoindre le groupe des notifications pour techniciens
        self.notification_group_name = 'technician_notifications'
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"Utilisateur {self.user.email} connecté aux notifications globales")

    async def disconnect(self, close_code):
        # Quitter le groupe des notifications
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
        print(f"Utilisateur déconnecté des notifications globales")

    # Gestionnaires pour les différents types de notifications
    async def new_ticket_notification(self, event):
        """Envoyer une notification de nouveau ticket"""
        await self.send(text_data=json.dumps({
            'type': 'new_ticket',
            'ticket': event['ticket']
        }))

    async def ticket_updated_notification(self, event):
        """Envoyer une notification de ticket mis à jour"""
        await self.send(text_data=json.dumps({
            'type': 'ticket_updated',
            'ticket': event['ticket']
        }))

    async def ticket_assigned_notification(self, event):
        """Envoyer une notification d'assignation de ticket"""
        await self.send(text_data=json.dumps({
            'type': 'ticket_assigned',
            'ticket': event['ticket']
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            # Valider le token JWT
            UntypedToken(token)
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None


class TicketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.ticket_id = self.scope['url_route']['kwargs']['ticket_id']
        self.room_group_name = f'ticket_{self.ticket_id}'

        # Vérifier l'authentification via le token JWT
        token = self.scope['query_string'].decode().split('token=')[-1]
        self.user = await self.get_user_from_token(token)

        if self.user is None:
            await self.close()
            return

        # Rejoindre le groupe du ticket
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Quitter le groupe du ticket
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Recevoir un message du WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'comment')
        message = text_data_json.get('message', '')

        if message and message_type in ['comment', 'instruction', 'confirmation']:
            # Vérifier si l'utilisateur peut envoyer ce type de message
            can_send = await self.can_user_send_message(message_type)
            if not can_send:
                # Envoyer un message d'erreur à l'utilisateur
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Vous ne pouvez pas envoyer de messages pendant le mode guidage. Veuillez confirmer les instructions du technicien.'
                }))
                return

            # Sauvegarder le commentaire en base selon le type
            comment = await self.save_comment(text_data_json)

            if comment:
                # Envoyer le message à tous les membres du groupe
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'comment': comment
                    }
                )

                # Si c'est une confirmation, aussi notifier la mise à jour de l'instruction originale
                if message_type == 'confirmation':
                    # Recharger et envoyer l'instruction mise à jour
                    instruction_id = text_data_json.get('instruction_id')
                    if instruction_id:
                        updated_instruction = await self.get_updated_instruction(instruction_id)
                        if updated_instruction:
                            await self.channel_layer.group_send(
                                self.room_group_name,
                                {
                                    'type': 'instruction_updated',
                                    'instruction': updated_instruction
                                }
                            )

    # Recevoir un message du groupe
    async def chat_message(self, event):
        comment = event['comment']

        # Envoyer le message au WebSocket
        await self.send(text_data=json.dumps({
            'type': 'comment',
            'comment': comment
        }))

    # Gestionnaire pour les instructions mises à jour
    async def instruction_updated(self, event):
        instruction = event['instruction']

        # Envoyer la mise à jour de l'instruction au WebSocket
        await self.send(text_data=json.dumps({
            'type': 'instruction_updated',
            'instruction': instruction
        }))

    # Gestionnaire pour les mises à jour de tickets
    async def ticket_updated(self, event):
        ticket = event['ticket']

        # Envoyer la mise à jour du ticket au WebSocket
        await self.send(text_data=json.dumps({
            'type': 'ticket_updated',
            'ticket': ticket
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            # Valider le token JWT
            UntypedToken(token)
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None

    @database_sync_to_async
    def save_comment(self, data):
        try:
            ticket = Ticket.objects.get(id=self.ticket_id)

            # Extraire les données selon le type de message
            message_type = data.get('type', 'comment')
            message_content = data.get('message', '')

            # Déterminer si c'est une session de guidage active
            # Chercher dans TOUS les commentaires du ticket, pas seulement les 10 derniers
            guidage_actif = False
            commentaires = ticket.commentaires.order_by('-date_commentaire')

            for comment in commentaires:
                if comment.type_action == 'guidage_debut':
                    guidage_actif = True
                    break
                elif comment.type_action == 'guidage_fin':
                    guidage_actif = False
                    break

            print(f"DEBUG: Mode guidage actif: {guidage_actif}, User role: {self.user.role}")

            # Déterminer le type d'action selon le type de message et le contexte
            if message_type == 'instruction':
                type_action = 'instruction'
                est_instruction = True
                numero_etape = data.get('numero_etape')
                attendre_confirmation = data.get('attendre_confirmation', True)
            elif message_type == 'confirmation':
                type_action = 'confirmation_etape'
                est_instruction = False
                numero_etape = None
                attendre_confirmation = False
                # Trouver et marquer l'instruction comme confirmée
                commentaire_parent_id = data.get('commentaire_parent_id')
                if commentaire_parent_id:
                    try:
                        parent_comment = Commentaire.objects.get(id=commentaire_parent_id)
                        parent_comment.marquer_comme_confirme()
                    except Commentaire.DoesNotExist:
                        pass
            else:  # message_type == 'comment'
                # Si le guidage est actif et que l'utilisateur est un technicien,
                # traiter le message comme une instruction
                if guidage_actif and self.user.role == 'technicien':
                    type_action = 'instruction'
                    est_instruction = True
                    # Calculer le numéro d'étape suivant
                    derniere_instruction = ticket.commentaires.filter(
                        est_instruction=True
                    ).order_by('-numero_etape').first()
                    numero_etape = (derniere_instruction.numero_etape + 1) if derniere_instruction and derniere_instruction.numero_etape else 1
                    attendre_confirmation = True
                    print(f"DEBUG: Instruction créée - Étape {numero_etape}")
                else:
                    type_action = 'ajout_commentaire'
                    est_instruction = False
                    numero_etape = None
                    attendre_confirmation = False
                    print(f"DEBUG: Commentaire normal créé")

            comment = Commentaire.objects.create(
                ticket=ticket,
                utilisateur_auteur=self.user,
                contenu=message_content,
                type_action=type_action,
                est_instruction=est_instruction,
                numero_etape=numero_etape,
                attendre_confirmation=attendre_confirmation
            )

            print(f"DEBUG: Commentaire créé - ID: {comment.id}, est_instruction: {comment.est_instruction}, numero_etape: {comment.numero_etape}")

            # Sérialiser le commentaire pour l'envoyer
            serializer = CommentaireSerializer(comment)
            return serializer.data
        except Ticket.DoesNotExist:
            return None

    @database_sync_to_async
    def get_updated_instruction(self, instruction_id):
        try:
            commentaire = Commentaire.objects.get(id=instruction_id)
            serializer = CommentaireSerializer(commentaire)
            return serializer.data
        except Commentaire.DoesNotExist:
            return None

    @database_sync_to_async
    def can_user_send_message(self, message_type):
        """Vérifier si l'utilisateur peut envoyer ce type de message"""
        try:
            ticket = Ticket.objects.get(id=self.ticket_id)

            # Vérifier si une session de guidage est active
            # Chercher le dernier événement de guidage dans l'ordre chronologique
            guidage_actif = False

            # Récupérer tous les événements de guidage ordonnés par date
            derniers_guidages = ticket.commentaires.filter(
                type_action__in=['guidage_debut', 'guidage_fin']
            ).order_by('-date_commentaire')

            if derniers_guidages.exists():
                dernier_evenement = derniers_guidages.first()
                # Le guidage est actif si le dernier événement est un début
                guidage_actif = dernier_evenement.type_action == 'guidage_debut'

            print(f"DEBUG: Mode guidage actif (backend): {guidage_actif}, User role: {self.user.role}")

            # Si le guidage est actif et que l'utilisateur est un employé
            if guidage_actif and self.user.role == 'employe':
                # L'employé ne peut envoyer que des confirmations, pas des messages normaux
                if message_type == 'comment':
                    return False

            return True

        except Ticket.DoesNotExist:
            return False