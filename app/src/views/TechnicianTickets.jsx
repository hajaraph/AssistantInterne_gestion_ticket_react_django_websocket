import React, { useState, useEffect, useCallback } from 'react';
import ContentCard from '../components/ContentCard';
import { FaSearch, FaEye, FaUserCheck, FaSync, FaSpinner, FaComments } from 'react-icons/fa';
import TicketDetailsModal from "../components/modals/TicketDetailsModal.jsx";
import StatusBadge from "../components/badges/StatusBadge.jsx";
import PriorityBadge from "../components/badges/PriorityBadge.jsx";
import apiService from '../services/api';
import webSocketService from '../services/websocket';
import { useAuth } from '../contexts/AuthContext';

const TechnicianTickets = () => {
  // États pour la gestion des tickets
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // États pour la recherche et le filtrage
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('Tous');
  const [priorityFilter, setPriorityFilter] = useState('Tous');
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const { user } = useAuth();

  // Setup WebSocket pour les notifications en temps réel
  useEffect(() => {
    if (user) {
      // Récupérer le token depuis le localStorage
      const token = localStorage.getItem('access_token');

      if (token) {
        console.log('Tentative de connexion WebSocket global pour:', user.email);

        // Se connecter aux notifications globales
        webSocketService.connectGlobal(token);

        // Gestionnaire pour les nouveaux tickets
        const handleNewTicket = (newTicket) => {
          console.log('Nouveau ticket reçu via WebSocket:', newTicket);
          setTickets(prevTickets => {
            // Vérifier si le ticket existe déjà
            const ticketExists = prevTickets.some(ticket => ticket.id === newTicket.id);
            if (ticketExists) {
              // Mettre à jour le ticket existant
              console.log('Mise à jour du ticket existant:', newTicket.id);
              return prevTickets.map(ticket =>
                ticket.id === newTicket.id ? newTicket : ticket
              );
            } else {
              // Ajouter le nouveau ticket au début de la liste
              console.log('Ajout du nouveau ticket:', newTicket.id);
              return [newTicket, ...prevTickets];
            }
          });
        };

        // Gestionnaire pour les tickets mis à jour
        const handleTicketUpdated = (updatedTicket) => {
          console.log('Ticket mis à jour via WebSocket:', updatedTicket);
          setTickets(prevTickets =>
            prevTickets.map(ticket =>
              ticket.id === updatedTicket.id ? updatedTicket : ticket
            )
          );
        };

        // Gestionnaire pour les assignations de tickets
        const handleTicketAssigned = (assignedTicket) => {
          console.log('Ticket assigné via WebSocket:', assignedTicket);
          setTickets(prevTickets =>
            prevTickets.map(ticket =>
              ticket.id === assignedTicket.id ? assignedTicket : ticket
            )
          );
        };

        // Gestionnaire de connexion WebSocket
        const handleWebSocketOpen = () => {
          console.log('WebSocket global connecté avec succès');
        };

        const handleWebSocketError = (error) => {
          console.error('Erreur WebSocket global:', error);
        };

        const handleWebSocketClose = () => {
          console.log('WebSocket global fermé');
        };

        // Enregistrer les listeners
        webSocketService.addGlobalEventListener('new_ticket', handleNewTicket);
        webSocketService.addGlobalEventListener('ticket_updated', handleTicketUpdated);
        webSocketService.addGlobalEventListener('ticket_assigned', handleTicketAssigned);
        webSocketService.addGlobalEventListener('open', handleWebSocketOpen);
        webSocketService.addGlobalEventListener('error', handleWebSocketError);
        webSocketService.addGlobalEventListener('close', handleWebSocketClose);

        // Cleanup lors du démontage
        return () => {
          console.log('Nettoyage des listeners WebSocket');
          webSocketService.removeGlobalEventListener('new_ticket', handleNewTicket);
          webSocketService.removeGlobalEventListener('ticket_updated', handleTicketUpdated);
          webSocketService.removeGlobalEventListener('ticket_assigned', handleTicketAssigned);
          webSocketService.removeGlobalEventListener('open', handleWebSocketOpen);
          webSocketService.removeGlobalEventListener('error', handleWebSocketError);
          webSocketService.removeGlobalEventListener('close', handleWebSocketClose);
          webSocketService.disconnectGlobal();
        };
      } else {
        console.log('Token manquant pour WebSocket');
      }
    } else {
      console.log('Utilisateur manquant pour WebSocket');
    }
  }, [user]);

  // Fonction de chargement des tickets assignés ou disponibles
  const loadTickets = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      console.log('Chargement des tickets technicien...'); // Debug
      // Pour les techniciens, on charge les tickets assignés + non assignés
      const ticketsData = await apiService.getTechnicianTickets();
      console.log('Tickets technicien chargés:', ticketsData); // Debug

      setTickets(ticketsData);
    } catch (err) {
      console.error('Erreur lors du chargement des tickets:', err);
      setError(err.message || 'Erreur lors du chargement des tickets');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Charger les tickets au montage du composant
  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  // Fonction de rafraîchissement manuel
  const handleRefresh = () => {
    loadTickets(true);
  };

  // Prendre en charge un ticket
  const handleTakeTicket = async (ticketId) => {
    try {
      console.log('Prise en charge du ticket:', ticketId); // Debug

      // Afficher un feedback immédiat en mettant à jour l'état local
      setTickets(prevTickets =>
        prevTickets.map(ticket =>
          ticket.id === ticketId
            ? {
                ...ticket,
                technicien_assigne: {
                  id: user.id,
                  email: user.email,
                  nom_complet: `${user.first_name} ${user.last_name}`.trim() || user.email
                },
                statut_ticket: 'en_cours'
              }
            : ticket
        )
      );

      // Appeler l'API
      const updatedTicket = await apiService.assignTicketToSelf(ticketId);
      console.log('Ticket pris en charge avec succès:', updatedTicket); // Debug

      // Recharger les données pour être sûr de la cohérence
      setTimeout(() => {
        loadTickets(true);
      }, 500);

    } catch (error) {
      console.error('Erreur lors de la prise en charge:', error);

      // Annuler le changement optimiste en cas d'erreur
      loadTickets(true);

      // Afficher l'erreur à l'utilisateur
      setError(`Erreur lors de la prise en charge: ${error.message}`);

      // Effacer l'erreur après 5 secondes
      setTimeout(() => {
        setError(null);
      }, 5000);
    }
  };

  // Changer le statut d'un ticket
  const handleStatusChange = async (ticketId, newStatus) => {
    try {
      await apiService.updateTicketStatus(ticketId, newStatus);
      loadTickets(true); // Recharger la liste
    } catch (error) {
      console.error('Erreur lors du changement de statut:', error);
    }
  };

  // Fonction pour formater la date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  // Fonction pour mapper les statuts de l'API aux statuts d'affichage
  const mapStatus = (status) => {
    const statusMap = {
      'ouvert': 'Nouveau',
      'en_cours': 'En cours',
      'resolu': 'Résolu',
      'ferme': 'Fermé',
      'annule': 'Annulé'
    };
    return statusMap[status] || status;
  };

  // Fonction pour mapper les priorités de l'API aux priorités d'affichage
  const mapPriority = (priority) => {
    const priorityMap = {
      'faible': 'Basse',
      'normal': 'Normale',
      'urgent': 'Haute',
      'critique': 'Critique'
    };
    return priorityMap[priority] || priority;
  };

  // Filtrer les tickets
  const filteredTickets = tickets.filter(ticket => {
    const matchesSearch = ticket.titre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ticket.id.toString().includes(searchTerm) ||
                         ticket.utilisateur_createur?.email?.toLowerCase().includes(searchTerm.toLowerCase());

    const ticketStatus = mapStatus(ticket.statut_ticket);
    const matchesStatus = statusFilter === 'Tous' || ticketStatus === statusFilter;

    const ticketPriority = mapPriority(ticket.priorite);
    const matchesPriority = priorityFilter === 'Tous' || ticketPriority === priorityFilter;

    return matchesSearch && matchesStatus && matchesPriority;
  });

  // Options de filtres
  const statusOptions = ['Tous', 'Nouveau', 'En cours', 'Résolu', 'Fermé'];
  const priorityOptions = ['Tous', 'Critique', 'Haute', 'Normale', 'Basse'];

  const handleRowClick = (ticket) => {
    setSelectedTicket(ticket);
    setIsDetailModalOpen(true);
  };

  // Affichage du loading
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-800">Tickets - Support technique</h1>
        </div>
        <ContentCard>
          <div className="flex items-center justify-center py-12">
            <FaSpinner className="animate-spin h-8 w-8 text-gray-500 mr-3" />
            <span className="text-gray-500">Chargement des tickets...</span>
          </div>
        </ContentCard>
      </div>
    );
  }

  // Affichage en cas d'erreur
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-800">Tickets - Support technique</h1>
        </div>
        <ContentCard>
          <div className="text-center py-12">
            <div className="text-red-500 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L3.316 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Erreur de chargement</h3>
            <p className="text-gray-500 mb-4">{error}</p>
            <button
              onClick={loadTickets}
              className="px-4 py-2 bg-[var(--primary-color)] text-white rounded-md hover:bg-[var(--primary-dark)] transition-colors"
            >
              Réessayer
            </button>
          </div>
        </ContentCard>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Support technique</h1>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Tickets assignés : {tickets.filter(t => t.technicien_assigne?.id === user?.id).length}</span>
          <span>•</span>
          <span>Non assignés : {tickets.filter(t => !t.technicien_assigne).length}</span>
        </div>
      </div>

      <ContentCard>
        <div className="mb-6 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FaSearch className="text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[var(--primary-color)] focus:border-[var(--primary-light)] sm:text-sm transition-colors"
              placeholder="Rechercher un ticket, utilisateur..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <select
              className="block pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[var(--primary-color)] focus:border-[var(--primary-light)] sm:text-sm rounded-md transition-colors"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>

            <select
              className="block pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[var(--primary-color)] focus:border-[var(--primary-light)] sm:text-sm rounded-md transition-colors"
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
            >
              {priorityOptions.map((priority) => (
                <option key={priority} value={priority}>
                  {priority}
                </option>
              ))}
            </select>

            {/* Bouton de rafraîchissement */}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[var(--primary-color)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Actualiser la liste"
            >
              <FaSync className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Actualisation...' : 'Actualiser'}
            </button>
          </div>
        </div>

        {/* Indicateur de nombre de tickets */}
        {tickets.length > 0 && (
          <div className="mb-4 text-sm text-gray-600">
            {filteredTickets.length} ticket{filteredTickets.length > 1 ? 's' : ''}
            {tickets.length !== filteredTickets.length && ` sur ${tickets.length} au total`}
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ticket
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Demandeur
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Statut
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Priorité
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Assigné à
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTickets.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-sm text-gray-500">
                    {tickets.length === 0 ? (
                      <div className="py-8">
                        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <p className="text-gray-500">Aucun ticket en attente</p>
                      </div>
                    ) : (
                      'Aucun ticket trouvé avec ces critères de recherche'
                    )}
                  </td>
                </tr>
              ) : (
                filteredTickets.map((ticket) => (
                <tr
                  key={ticket.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleRowClick(ticket)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{ticket.titre}</div>
                    <div className="text-sm text-gray-500">#{ticket.id}</div>
                    {ticket.categorie && (
                      <div className="text-xs text-gray-400 mt-1">{ticket.categorie.nom_categorie}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {ticket.utilisateur_createur?.nom_complet || ticket.utilisateur_createur?.email || 'N/A'}
                    </div>
                    {ticket.utilisateur_createur?.departement && (
                      <div className="text-xs text-gray-500">{ticket.utilisateur_createur.departement}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={mapStatus(ticket.statut_ticket)} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <PriorityBadge priority={mapPriority(ticket.priorite)} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {ticket.technicien_assigne ? (
                        <span className={ticket.technicien_assigne.id === user?.id ? 'font-medium text-blue-600' : ''}>
                          {ticket.technicien_assigne.nom_complet || ticket.technicien_assigne.email}
                        </span>
                      ) : (
                        <span className="text-gray-400">Non assigné</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(ticket.date_creation)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      <button
                        className="text-[var(--info-color)] hover:text-[var(--info-dark)] transition-colors"
                        title="Voir les détails"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRowClick(ticket);
                        }}
                      >
                        <FaEye className="h-4 w-4" />
                      </button>

                      {!ticket.technicien_assigne && (
                        <button
                          className="text-green-600 hover:text-green-800 transition-colors"
                          title="Prendre en charge"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleTakeTicket(ticket.id);
                          }}
                        >
                          <FaUserCheck className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
      </ContentCard>

      {/* Modals */}
      <TicketDetailsModal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        ticket={selectedTicket}
        onTicketUpdated={() => {
          loadTickets(true); // Recharger la liste après mise à jour
          setIsDetailModalOpen(false); // Fermer le modal
        }}
      />
    </div>
  );
};

export default TechnicianTickets;
