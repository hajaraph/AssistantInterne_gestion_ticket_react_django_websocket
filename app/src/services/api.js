const API_BASE_URL = 'http://localhost:8000/api';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Méthode pour effectuer les requêtes HTTP
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem('access_token');

    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Ajouter le token d'authentification si disponible
    if (token && !options.skipAuth) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);

      // Si le token a expiré, essayer de le rafraîchir
      if (response.status === 401 && !options.skipAuth) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // Retry la requête avec le nouveau token
          config.headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`;
          return await fetch(url, config);
        } else {
          // Rediriger vers la page de connexion
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/';
          return null;
        }
      }

      return response;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentification
  async login(credentials) {
    const response = await this.request('/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
      skipAuth: true,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Échec de la connexion');
    }

    const data = await response.json();

    // Stocker les tokens et informations utilisateur
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    localStorage.setItem('permissions', JSON.stringify(data.permissions));

    return data;
  }

  // Rafraîchir le token
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      return false;
    }

    try {
      const response = await this.request('/token/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh: refreshToken }),
        skipAuth: true,
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access);
        return true;
      } else {
        return false;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  // Déconnexion
  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('permissions');
  }

  // Vérifier si l'utilisateur est connecté
  isAuthenticated() {
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  }

  // Obtenir les informations de l'utilisateur connecté
  getCurrentUser() {
    const userString = localStorage.getItem('user');
    return userString ? JSON.parse(userString) : null;
  }

  // Obtenir les permissions de l'utilisateur
  getUserPermissions() {
    const permissionsString = localStorage.getItem('permissions');
    return permissionsString ? JSON.parse(permissionsString) : null;
  }

  // Obtenir le profil utilisateur depuis l'API
  async getUserProfile() {
    const response = await this.request('/profile');

    if (!response.ok) {
      throw new Error('Impossible de récupérer le profil utilisateur');
    }

    return await response.json();
  }

  // Mettre à jour le profil utilisateur
  async updateUserProfile(profileData) {
    const response = await this.request('/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Échec de la mise à jour du profil');
    }

    const updatedUser = await response.json();
    localStorage.setItem('user', JSON.stringify(updatedUser));
    return updatedUser;
  }

  // Changer le mot de passe
  async changePassword(passwordData) {
    const response = await this.request('/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Échec du changement de mot de passe');
    }

    return await response.json();
  }

  // Tickets
  async createTicket(ticketData) {
    const response = await this.request('/tickets/create', {
      method: 'POST',
      body: JSON.stringify(ticketData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erreur lors de la création du ticket');
    }

    return await response.json();
  }

  async getMyTickets() {
    const response = await this.request('/tickets/my/');  // Changé de '/tickets/my-tickets' vers '/tickets/my/'

    if (!response.ok) {
      throw new Error('Impossible de récupérer vos tickets');
    }

    return await response.json();
  }

  async getTicketById(ticketId) {
    const response = await this.request(`/tickets/${ticketId}`);

    if (!response.ok) {
      throw new Error('Impossible de récupérer les détails du ticket');
    }

    return await response.json();
  }

  async getTicketStats() {
    const response = await this.request('/tickets/stats');

    if (!response.ok) {
      throw new Error('Impossible de récupérer les statistiques');
    }

    return await response.json();
  }

  // Données de référence
  async getCategories() {
    const response = await this.request('/categories');

    if (!response.ok) {
      throw new Error('Impossible de récupérer les catégories');
    }

    return await response.json();
  }

  async getEquipments() {
    const response = await this.request('/equipments');

    if (!response.ok) {
      throw new Error('Impossible de récupérer les équipements');
    }

    return await response.json();
  }

  async getDepartments() {
    const response = await this.request('/departments');

    if (!response.ok) {
      throw new Error('Impossible de récupérer les départements');
    }

    return await response.json();
  }

  // Tickets pour techniciens
  async getTechnicianTickets() {
    const response = await this.request('/technician/tickets/');  // Changé de '/tickets/technician' vers '/technician/tickets/'

    if (!response.ok) {
      throw new Error('Impossible de récupérer les tickets');
    }

    return await response.json();
  }

  async assignTicketToSelf(ticketId) {
    const response = await this.request(`/technician/tickets/${ticketId}/assign/`, {  // Changé l'URL pour correspondre au backend
      method: 'POST',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erreur lors de l\'assignation');
    }

    return await response.json();
  }

  async updateTicketStatus(ticketId, status) {
    const response = await this.request(`/technician/tickets/${ticketId}/status/`, {  // Changé l'URL pour correspondre au backend
      method: 'PATCH',
      body: JSON.stringify({ statut_ticket: status }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erreur lors de la mise à jour du statut');
    }

    return await response.json();
  }

  // Méthodes pour les commentaires et le guidage
  async getTicketComments(ticketId) {
    const response = await this.request(`/tickets/${ticketId}/comments/`);
    if (!response.ok) {
      throw new Error('Erreur lors de la récupération des commentaires');
    }
    return await response.json();
  }

  async addComment(ticketId, commentData) {
    const response = await this.request(`/tickets/${ticketId}/comments/`, {
      method: 'POST',
      body: JSON.stringify(commentData),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Erreur lors de l\'ajout du commentaire');
    }
    return await response.json();
  }

  // Méthodes pour le guidage à distance
  async startGuidance(ticketId) {
    const response = await this.request(`/tickets/${ticketId}/guidance/start/`, {
      method: 'POST',
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erreur lors du démarrage du guidage');
    }
    return await response.json();
  }

  async sendInstruction(ticketId, instructionData) {
    const response = await this.request(`/tickets/${ticketId}/guidance/instruction/`, {
      method: 'POST',
      body: JSON.stringify(instructionData),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erreur lors de l\'envoi de l\'instruction');
    }
    return await response.json();
  }

  async confirmInstruction(commentId, message = 'Étape confirmée ✅') {
    const response = await this.request(`/comments/${commentId}/confirm/`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erreur lors de la confirmation');
    }
    return await response.json();
  }

  async endGuidance(ticketId, endData = {}) {
    const response = await this.request(`/tickets/${ticketId}/guidance/end/`, {
      method: 'POST',
      body: JSON.stringify({
        message: 'Session de guidage terminée avec succès !',
        resolu: true,
        ...endData
      }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Erreur lors de la fin du guidage');
    }
    return await response.json();
  }
}

// Instance singleton du service API
export const apiService = new ApiService();
export default apiService;
