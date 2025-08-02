Système de gestion de tickets de support technique avec fonctionnalité innovante de **guidage à distance en temps réel**. Cette API Django REST permet aux techniciens de guider les employés étape par étape pour résoudre leurs problèmes techniques via une interface chat interactive.

## ✨ Fonctionnalités Principales

### 🎯 **Système de Ticketing Classique**
- ✅ Création, assignation et suivi de tickets
- ✅ Gestion des priorités (faible, normal, urgent, critique)
- ✅ Catégorisation et liaison avec équipements
- ✅ Workflow complet : Ouvert → En cours → Résolu → Fermé

### 🚀 **Innovation : Guidage à Distance Interactif**
- 🔧 **Sessions de guidage temps réel** entre technicien et employé
- 📝 **Instructions numérotées** avec confirmation obligatoire
- ✅ **Système de validation étape par étape**
- 💬 **Chat bidirectionnel** avec WebSockets
- 🎮 **Mode guidage actif/inactif** avec interface adaptative

### 👥 **Gestion des Utilisateurs**
- 🔐 **Authentification JWT** avec refresh tokens
- 👤 **Système de rôles** : Employé, Technicien, Administrateur
- 🏢 **Gestion des départements** et équipements
- 🛡️ **Permissions granulaires** par rôle

## 🏗️ Architecture Technique

### **Backend Stack**
- **Django 5.2** - Framework web Python
- **Django REST Framework** - API REST
- **Django Channels** - WebSockets temps réel
- **SQLite** - Base de données (développement)
- **JWT** - Authentification sécurisée

### **Structure des Apps**
```
Tech/
├── manage.py
├── requirements.txt
├── Tech/                    # Configuration projet
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py              # Configuration WebSockets
│   └── wsgi.py
└── Techinicien/             # App principale
    ├── models.py            # Modèles de données
    ├── views.py             # Vues API REST
    ├── serializers.py       # Sérialiseurs DRF
    ├── consumers.py         # Consumers WebSocket
    ├── routing.py           # Routage WebSocket
    └── urls.py              # URLs API
```

## 📊 Modèles de Données

### **CustomUser** - Utilisateurs
```python
ROLE_CHOICES = [
    ('employe', 'Employé'),        # Crée des tickets
    ('technicien', 'Technicien'),  # Résout les tickets
    ('admin', 'Administrateur'),   # Gestion complète
]
```

### **Ticket** - Tickets de support
```python
STATUT_TICKET_CHOICES = [
    ('ouvert', 'Ouvert'),
    ('en cours', 'En cours'),
    ('resolu', 'Résolu'),
    ('ferme', 'Fermé'),
    ('annule', 'Annulé'),
]
```

### **Commentaire** - Système de guidage avancé
```python
TYPE_ACTION_CHOICES = [
    # Actions standards
    ('ajout_commentaire', 'Commentaire'),
    ('assignation', 'Assignation'),
    
    # 🎯 Guidage à distance - INNOVATION
    ('instruction', 'Instruction de guidage'),
    ('confirmation_etape', 'Confirmation d\'étape'),
    ('guidage_debut', 'Début du guidage à distance'),
    ('guidage_fin', 'Fin du guidage à distance'),
]
```

## 🔌 API Endpoints

### **Authentification**
```http
POST /api/login                 # Connexion JWT
POST /api/register              # Inscription
GET  /api/profile               # Profil utilisateur
PUT  /api/profile               # Mise à jour profil
```

### **Tickets - Employés**
```http
POST /api/tickets/create        # Créer un ticket
GET  /api/tickets/my/          # Mes tickets
GET  /api/tickets/{id}/        # Détails ticket
GET  /api/tickets/stats/       # Statistiques
```

### **Tickets - Techniciens**
```http
GET  /api/technician/tickets/                    # Tickets disponibles
POST /api/technician/tickets/{id}/assign/       # Prendre en charge
PATCH /api/technician/tickets/{id}/status/      # Changer statut
```

### **🎮 Guidage à Distance - INNOVATION**
```http
POST /api/tickets/{id}/guidance/start/          # Démarrer guidage
POST /api/tickets/{id}/guidance/instruction/    # Envoyer instruction
POST /api/comments/{id}/confirm/                # Confirmer étape
POST /api/tickets/{id}/guidance/end/            # Terminer guidage
```

### **Chat & Commentaires**
```http
GET  /api/tickets/{id}/comments/  # Commentaires ticket
POST /api/tickets/{id}/comments/  # Ajouter commentaire
```

### **WebSocket**
```
ws://localhost:8000/ws/ticket/{ticket_id}/?token={jwt_token}
```

## 🚀 Installation et Configuration

### **Prérequis**
- Python 3.8+
- pip
- Git

### **Installation**
```bash
# 1. Cloner le repository
git clone <your-repo-url>
cd Tech

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer la base de données
python manage.py makemigrations
python manage.py migrate

# 5. Créer un superutilisateur
python manage.py createsuperuser

# 6. Démarrer le serveur
python manage.py runserver
```

### **Configuration WebSocket (ASGI)**
Le serveur utilise ASGI pour supporter les WebSockets :
```python
# Tech/asgi.py
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            Techinicien.routing.websocket_urlpatterns
        )
    ),
})
```

## 🛠️ Installation WebSocket (Django Channels)

1. **Installer Django Channels** :
   ```bash
   pip install channels
   ```
2. **Ajouter 'channels' dans `INSTALLED_APPS`** du fichier `settings.py` :
   ```python
   INSTALLED_APPS = [
       # ...
       'channels',
       # ...
   ]
   ```
3. **Définir le backend ASGI** dans `settings.py` :
   ```python
   ASGI_APPLICATION = 'Tech.asgi.application'
   ```
4. **Configurer le routage WebSocket** dans `Techinicien/routing.py` et lier dans `asgi.py`.
5. **Lancer le serveur ASGI** :
   ```bash
   python manage.py runserver
   ```

Pour plus de détails, consultez la documentation officielle : https://channels.readthedocs.io/fr/latest/

## 🎮 Utilisation du Système de Guidage

### **1. Démarrage d'une Session**
```python
# Technicien démarre le guidage
POST /api/tickets/123/guidance/start/
```

### **2. Envoi d'Instructions**
```python
# Messages du technicien deviennent automatiquement des instructions
# via WebSocket pendant le mode guidage actif
```

### **3. Confirmation par l'Employé**
```python
# Employé confirme chaque étape
POST /api/comments/456/confirm/
{
    "message": "Étape terminée ✅"
}
```

### **4. Fin de Session**
```python
# Technicien termine le guidage
POST /api/tickets/123/guidance/end/
{
    "message": "Problème résolu !",
    "resolu": true
}
```

## 🌐 Communication Temps Réel

### **WebSocket Consumer**
```python
class TicketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Authentification JWT
        # Rejoindre le groupe du ticket
        
    async def receive(self, text_data):
        # Traitement des messages
        # Conversion automatique en instructions si guidage actif
        
    async def chat_message(self, event):
        # Diffusion des messages à tous les participants
```

### **Messages WebSocket**
```json
// Nouveau commentaire
{
    "type": "comment",
    "comment": { /* données commentaire */ }
}

// Instruction mise à jour (confirmée)
{
    "type": "instruction_updated", 
    "instruction": { /* instruction confirmée */ }
}

// Erreur (employé bloqué en mode guidage)
{
    "type": "error",
    "message": "Vous ne pouvez pas envoyer de messages pendant le mode guidage"
}
```

## 🔒 Sécurité

### **Authentification JWT**
- Tokens d'accès (15 min)
- Tokens de rafraîchissement (7 jours)
- Validation automatique des permissions

### **Permissions par Rôle**
```python
# Employé
- Créer ses tickets
- Voir ses tickets uniquement
- Confirmer les instructions de guidage

# Technicien  
- Prendre en charge des tickets
- Démarrer/terminer le guidage
- Envoyer des instructions
- Marquer comme résolu

# Admin
- Accès complet à tous les tickets
- Gestion des utilisateurs
- Administration système
```

## 📈 Fonctionnalités Avancées

### **Workflow Intelligent**
- **Auto-assignation** des techniciens
- **Numérotation automatique** des étapes de guidage
- **Blocage des messages** employés en mode guidage
- **Traçabilité complète** de chaque action

### **Système de Notifications**
- **Temps réel** via WebSockets
- **Historique complet** des actions
- **Statuts de confirmation** visibles

### **Gestion d'État**
- **Mode guidage actif/inactif** détecté automatiquement
- **Synchronisation** entre tous les clients connectés
- **Persistance** de l'état en base de données

## 🧪 Tests et Développement

### **Lancer les Tests**
```bash
python manage.py test
```

### **Mode Debug**
```python
# settings.py
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

### **Logs de Debug**
Le système inclut des logs détaillés pour le développement :
```python
print(f"DEBUG: Mode guidage actif: {guidage_actif}")
print(f"DEBUG: Instruction créée - Étape {numero_etape}")
```

## 🌟 Innovation Technique

Ce projet se distingue par son **système de guidage à distance interactif** :

1. **🎯 Mode Guidage Automatique** : Les messages des techniciens deviennent automatiquement des instructions numérotées
2. **✅ Validation Obligatoire** : Chaque étape doit être confirmée avant de passer à la suivante  
3. **🚫 Blocage Intelligent** : Les employés ne peuvent pas envoyer de messages pendant le guidage
4. **⚡ Temps Réel** : Synchronisation instantanée via WebSockets
5. **🔄 Workflow Adaptatif** : Interface qui s'adapte selon le mode actif/inactif

## 📝 Contributing

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🎯 Roadmap

- [ ] **Système de fichiers joints** pour les captures d'écran
- [ ] **Notifications push** web
- [ ] **Mode vocal** pour le guidage
- [ ] **Analytics** des sessions de guidage
- [ ] **API mobile** pour application smartphone
- [ ] **Intégration Teams/Slack** pour notifications

---

**Développé avec ❤️ pour révolutionner le support technique à distance**
