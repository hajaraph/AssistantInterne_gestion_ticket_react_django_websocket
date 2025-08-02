from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Departement, CustomUser, Ticket, Categorie, Equipement, Commentaire


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'password2', 'first_name', 'last_name', 'telephone', 'role')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Remove password2 from the data
        validated_data.pop('password2', None)

        # Create user with the validated data
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            telephone=validated_data.get('telephone', ''),
            role=validated_data.get('role', 'employe')
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token obtain pair serializer to include additional user data in the response
    with role-based handling for employe and technicien.
    Uses email for authentication instead of username.
    """
    username_field = 'email'  # Use email instead of username for authentication
    
    def validate(self, attrs: dict) -> dict:
        # Use email as the username field
        attrs['username'] = attrs.get('email', '')
        
        # Validate the credentials
        data = super().validate(attrs)
        refresh = self.get_token(self.user)

        # Get the access token
        access_token = str(refresh.access_token) if hasattr(refresh, 'access_token') else str(refresh)

        # Get user role
        user_role = getattr(self.user, 'role', 'employe')

        # Données de base de l'utilisateur
        user_data = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name or '',
            'last_name': self.user.last_name or '',
            'role': user_role,
            'is_staff': bool(getattr(self.user, 'is_staff', False)),
        }

        # Ajouter des informations spécifiques au rôle
        if user_role == 'technicien':
            # Pour les techniciens, ajouter des informations supplémentaires si nécessaire
            user_data.update({
                'can_assign_tickets': True,
                'can_manage_equipment': True,
            })
        elif user_role == 'employe':
            # Pour les employés, limiter les permissions
            user_data.update({
                'can_assign_tickets': False,
                'can_manage_equipment': False,
            })

        # Mettre à jour la réponse avec les données utilisateur
        data.update({
            'refresh': str(refresh),
            'access': access_token,
            'user': user_data,
            'permissions': self.get_user_permissions(user_role)
        })

        return data

    @staticmethod
    def get_user_permissions(role):
        """Retourne les permissions en fonction du rôle de l'utilisateur."""
        permissions = {
            'ticket': {
                'view': True,
                'create': True,
                'update': role in ['technicien', 'admin'],
                'delete': role == 'admin',
                'assign': role in ['technicien', 'admin'],
            },
            'equipment': {
                'view': True,
                'create': role in ['technicien', 'admin'],
                'update': role in ['technicien', 'admin'],
                'delete': role == 'admin',
            },
            'user': {
                'view_list': role == 'admin',
                'create': role == 'admin',
                'update': role == 'admin',
                'delete': role == 'admin',
            },
            'department': {
                'view': True,
                'manage': role == 'admin',
            },
            'dashboard': {
                'view': True,
                'view_analytics': role in ['technicien', 'admin'],
            }
        }

        # Ajouter des permissions spécifiques aux techniciens
        if role == 'technicien':
            permissions.update({
                'ticket': {
                    **permissions['ticket'],
                    'take_ownership': True,
                    'change_status': True,
                }
            })

        return permissions


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data.
    """

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'telephone',
            'role', 'is_active', 'date_joined', 'departement'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'is_active']

    def to_representation(self, instance):
        """
        Customize the response data.
        """
        representation = super().to_representation(instance)
        if instance.departement:
            representation['departement'] = {
                'id': instance.departement.id,
                'nom_departement': instance.departement.nom_departement
            }
        return representation


class DepartementSerializer(serializers.ModelSerializer):
    """
    Serializer for the Departement model.
    """

    class Meta:
        model = Departement
        fields = ['id', 'nom_departement', 'responsable', 'localisation']
        read_only_fields = ['id']

    def validate_nom_departement(self, value):
        """
        Validate that the department name is unique (case-insensitive).
        """
        queryset = Departement.objects.filter(nom_departement__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Un département avec ce nom existe déjà.")
        return value


class CategorieSerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    class Meta:
        model = Categorie
        fields = ['id', 'nom_categorie', 'description_categorie', 'couleur_affichage']


class EquipementSerializer(serializers.ModelSerializer):
    """Serializer for Equipment model."""
    departement = DepartementSerializer(read_only=True)

    class Meta:
        model = Equipement
        fields = ['id', 'nom_modele', 'type_equipement', 'numero_serie', 'departement', 'statut_equipement']


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tickets (used by employees)."""

    class Meta:
        model = Ticket
        fields = [
            'titre', 'description', 'priorite', 'categorie', 'equipement'
        ]
        extra_kwargs = {
            'titre': {'required': True},
            'description': {'required': True},
            'priorite': {'required': True},
            'categorie': {'required': True},
        }

    @staticmethod
    def validate_titre(value):
        """Validate title is not empty and has minimum length."""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Le titre doit contenir au moins 5 caractères."
            )
        return value.strip()

    @staticmethod
    def validate_description(value):
        """Validate description is not empty and has minimum length."""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "La description doit contenir au moins 10 caractères."
            )
        return value.strip()

    def create(self, validated_data):
        """Create ticket with current user as creator."""
        user = self.context['request'].user

        # Vérifier que l'utilisateur est un employé
        if user.role != 'employe':
            raise serializers.ValidationError(
                "Seuls les employés peuvent créer des tickets."
            )

        validated_data['utilisateur_createur'] = user
        return super().create(validated_data)


class TicketListSerializer(serializers.ModelSerializer):
    """Serializer for listing tickets."""
    categorie = CategorieSerializer(read_only=True)
    equipement = EquipementSerializer(read_only=True)
    utilisateur_createur = serializers.SerializerMethodField()
    technicien_assigne = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'titre', 'description', 'date_creation', 'date_modification',
            'statut_ticket', 'priorite', 'categorie', 'utilisateur_createur',
            'technicien_assigne', 'equipement'
        ]

    @staticmethod
    def get_utilisateur_createur(obj):
        """Get creator user info."""
        if obj.utilisateur_createur:
            return {
                'id': obj.utilisateur_createur.id,
                'email': obj.utilisateur_createur.email,
                'nom_complet': f"{obj.utilisateur_createur.first_name} {obj.utilisateur_createur.last_name}".strip(),
                'role': obj.utilisateur_createur.role
            }
        return None

    @staticmethod
    def get_technicien_assigne(obj):
        """Get assigned technician info."""
        if obj.technicien_assigne:
            return {
                'id': obj.technicien_assigne.id,
                'email': obj.technicien_assigne.email,
                'nom_complet': f"{obj.technicien_assigne.first_name} {obj.technicien_assigne.last_name}".strip(),
                'role': obj.technicien_assigne.role
            }
        return None


class CommentaireSerializer(serializers.ModelSerializer):
    """Serializer for ticket comments."""
    auteur = serializers.SerializerMethodField()
    reponses = serializers.SerializerMethodField()
    piece_jointe_url = serializers.SerializerMethodField()

    class Meta:
        model = Commentaire
        fields = [
            'id', 'contenu', 'date_commentaire', 'type_action', 'auteur',
            'est_instruction', 'numero_etape', 'attendre_confirmation',
            'commentaire_parent', 'est_confirme', 'date_confirmation',
            'piece_jointe', 'piece_jointe_url', 'reponses'
        ]
        read_only_fields = ['date_commentaire', 'date_confirmation', 'auteur']

    @staticmethod
    def get_auteur(obj):
        """Get comment author info."""
        if obj.utilisateur_auteur:
            return {
                'id': obj.utilisateur_auteur.id,
                'email': obj.utilisateur_auteur.email,
                'nom_complet': f"{obj.utilisateur_auteur.first_name} {obj.utilisateur_auteur.last_name}".strip() or obj.utilisateur_auteur.email,
                'role': obj.utilisateur_auteur.role
            }
        return None

    def get_reponses(self, obj):
        """Get direct responses to this comment."""
        reponses = obj.reponses.all()
        if reponses:
            return CommentaireSerializer(reponses, many=True, context=self.context).data
        return []

    def get_piece_jointe_url(self, obj):
        """Get the full URL for the attached file."""
        if obj.piece_jointe:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.piece_jointe.url)
            return obj.piece_jointe.url
        return None


class CommentaireCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments with guidance features."""

    class Meta:
        model = Commentaire
        fields = [
            'contenu', 'type_action', 'est_instruction', 'numero_etape',
            'attendre_confirmation', 'commentaire_parent', 'piece_jointe'
        ]

    def validate(self, data):
        """Validate comment data based on type and user role."""
        user = self.context['request'].user
        type_action = data.get('type_action', 'ajout_commentaire')

        # Vérifier que seuls les techniciens peuvent créer des instructions
        if type_action in ['instruction', 'question_technicien', 'demande_capture'] and user.role != 'technicien':
            raise serializers.ValidationError(
                "Seuls les techniciens peuvent créer des instructions ou poser des questions techniques."
            )

        # Vérifier que seuls les employés peuvent confirmer ou répondre
        if type_action in ['reponse_employe', 'confirmation_etape'] and user.role != 'employe':
            raise serializers.ValidationError(
                "Seuls les employés peuvent répondre ou confirmer des étapes."
            )

        # Si c'est une instruction, vérifier les champs requis
        if data.get('est_instruction', False):
            if not data.get('contenu', '').strip():
                raise serializers.ValidationError(
                    "Le contenu de l'instruction ne peut pas être vide."
                )

        return data

    def create(self, validated_data):
        """Create comment with current user as author."""
        validated_data['utilisateur_auteur'] = self.context['request'].user
        return super().create(validated_data)
