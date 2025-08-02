class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectTimeout = null;
    this.isConnected = false; // Ajouter un flag de connexion interne

    // Nouvelle propriété pour les notifications globales
    this.globalSocket = null;
    this.globalListeners = new Map();
    this.isGlobalConnected = false;
  }

  connect(ticketId, token) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('WebSocket déjà connecté');
      return;
    }

    const wsUrl = `ws://localhost:8000/ws/ticket/${ticketId}/?token=${token}`;

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = (event) => {
        console.log('WebSocket connecté pour le ticket:', ticketId);
        this.reconnectAttempts = 0;
        this.isConnected = true;
        // Ajouter un délai pour s'assurer que l'événement est bien traité
        setTimeout(() => {
          this.notifyListeners('open', event);
        }, 100);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Message WebSocket reçu:', data);

          if (data.type === 'comment' && data.comment) {
            this.notifyListeners('comment', data.comment);
          } else if (data.type === 'instruction_updated' && data.instruction) {
            this.notifyListeners('instruction_updated', data.instruction);
          } else if (data.type === 'error' && data.message) {
            this.notifyListeners('error', data.message);
          }
        } catch (error) {
          console.error('Erreur parsing message WebSocket:', error);
        }
      };

      this.socket.onclose = (event) => {
        console.log('WebSocket fermé:', event.code, event.reason);
        this.isConnected = false;
        this.notifyListeners('close', event);

        // Tentative de reconnexion automatique
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect(ticketId, token);
        }
      };

      this.socket.onerror = (error) => {
        console.error('Erreur WebSocket:', error);
        this.isConnected = false;
        this.notifyListeners('error', error);
      };

    } catch (error) {
      console.error('Erreur lors de la création du WebSocket:', error);
    }
  }

  scheduleReconnect(ticketId, token) {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000); // Backoff exponentiel jusqu'à 30s

    console.log(`Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts} dans ${delay}ms`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect(ticketId, token);
    }, delay);
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    this.isConnected = false;
    this.listeners.clear();
    console.log('WebSocket déconnecté');
  }

  sendMessage(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const messageData = {
        type: 'comment',
        message: message
      };
      this.socket.send(JSON.stringify(messageData));
      console.log('Message envoyé via WebSocket:', messageData);
      return true; // Retourner true si le message a été envoyé
    } else {
      console.warn('WebSocket non connecté, impossible d\'envoyer le message');
      return false; // Retourner false si le message n'a pas été envoyé
    }
  }

  // Méthode pour vérifier si le WebSocket est connecté
  isWebSocketConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN && this.isConnected;
  }

  // Système d'écoute d'événements
  addEventListener(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }

  removeEventListener(eventType, callback) {
    if (this.listeners.has(eventType)) {
      const callbacks = this.listeners.get(eventType);
      const index = callbacks.indexOf(callback);
      if (index !== -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  notifyListeners(eventType, data) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Erreur dans le callback WebSocket:', error);
        }
      });
    }
  }

  // Nouvelle méthode pour se connecter aux notifications globales
  connectGlobal(token) {
    if (this.globalSocket && this.globalSocket.readyState === WebSocket.OPEN) {
      console.log('WebSocket global déjà connecté');
      return;
    }

    const wsUrl = `ws://localhost:8000/ws/notifications/?token=${token}`;
    console.log('Tentative de connexion WebSocket global vers:', wsUrl);

    try {
      this.globalSocket = new WebSocket(wsUrl);

      this.globalSocket.onopen = (event) => {
        console.log('WebSocket global connecté avec succès');
        this.isGlobalConnected = true;
        this.notifyGlobalListeners('open', event);
      };

      this.globalSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Notification globale reçue:', data);

          if (data.type === 'new_ticket' && data.ticket) {
            console.log('Traitement nouveau ticket:', data.ticket.id);
            this.notifyGlobalListeners('new_ticket', data.ticket);
          } else if (data.type === 'ticket_updated' && data.ticket) {
            console.log('Traitement ticket mis à jour:', data.ticket.id);
            this.notifyGlobalListeners('ticket_updated', data.ticket);
          } else if (data.type === 'ticket_assigned' && data.ticket) {
            console.log('Traitement ticket assigné:', data.ticket.id);
            this.notifyGlobalListeners('ticket_assigned', data.ticket);
          } else {
            console.log('Message WebSocket global non reconnu:', data);
          }
        } catch (error) {
          console.error('Erreur parsing message WebSocket global:', error);
        }
      };

      this.globalSocket.onclose = (event) => {
        console.log('WebSocket global fermé:', event.code, event.reason);
        this.isGlobalConnected = false;
        this.notifyGlobalListeners('close', event);
      };

      this.globalSocket.onerror = (error) => {
        console.error('Erreur WebSocket global:', error);
        this.isGlobalConnected = false;
        this.notifyGlobalListeners('error', error);
      };

    } catch (error) {
      console.error('Erreur lors de la création du WebSocket global:', error);
    }
  }

  disconnectGlobal() {
    if (this.globalSocket) {
      this.globalSocket.close();
      this.globalSocket = null;
    }
    this.isGlobalConnected = false;
    this.globalListeners.clear();
    console.log('WebSocket global déconnecté');
  }

  // Méthodes pour les listeners globaux
  addGlobalEventListener(eventType, callback) {
    if (!this.globalListeners.has(eventType)) {
      this.globalListeners.set(eventType, []);
    }
    this.globalListeners.get(eventType).push(callback);
  }

  removeGlobalEventListener(eventType, callback) {
    if (this.globalListeners.has(eventType)) {
      const callbacks = this.globalListeners.get(eventType);
      const index = callbacks.indexOf(callback);
      if (index !== -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  notifyGlobalListeners(eventType, data) {
    if (this.globalListeners.has(eventType)) {
      this.globalListeners.get(eventType).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Erreur dans le callback WebSocket global:', error);
        }
      });
    }
  }
}

// Instance singleton
const webSocketService = new WebSocketService();

export default webSocketService;
