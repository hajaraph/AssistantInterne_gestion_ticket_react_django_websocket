import React, {useState, useEffect, useCallback} from 'react';
import ContentCard from '../components/ContentCard';
import { FaSearch, FaEye, FaSpinner, FaSync } from 'react-icons/fa';
import {FaPlus} from "react-icons/fa6";
import TicketDetailsModal from "../components/modals/TicketDetailsModal.jsx";
import StatusBadge from "../components/badges/StatusBadge.jsx";
import PriorityBadge from "../components/badges/PriorityBadge.jsx";
import DiagnosticOrTicketModal from "../components/modals/DiagnosticOrTicketModal.jsx";
import DiagnosticEtapes from "../components/DiagnosticEtapes.jsx";
import NewTicketModal from "../components/modals/NewTicketModal.jsx";
import apiService from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const MyTickets = () => {
  // États pour la gestion des tickets
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // États pour la recherche et le filtrage
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('Tous');
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Nouveaux états pour le diagnostic
  const [isDiagnosticOrTicketModalOpen, setIsDiagnosticOrTicketModalOpen] = useState(false);
  const [isDiagnosticEtapesOpen, setIsDiagnosticEtapesOpen] = useState(false);
  const [selectedCategoryForDiagnostic, setSelectedCategoryForDiagnostic] = useState(null);
  const [isNewTicketModalOpen, setIsNewTicketModalOpen] = useState(false);

  const { user } = useAuth();

  // Fonction de chargement des tickets avec useCallback pour éviter les re-renders inutiles
  const loadTickets = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      console.log('Chargement des tickets...'); // Debug
      const ticketsData = await apiService.getMyTickets();
      console.log('Tickets chargés:', ticketsData); // Debug

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

  // Gérer la création d'un nouveau ticket
  const handleCreateTicket = (newTicket) => {
    console.log('Nouveau ticket créé:', newTicket); // Debug
    setTickets(prevTickets => [newTicket, ...prevTickets]);
    // Optionnel : recharger la liste pour s'assurer de la cohérence
    setTimeout(() => {
      loadTickets(true);
    }, 1000);
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
      'normal': 'Moyenne',
      'urgent': 'Haute',
      'critique': 'Critique'
    };
    return priorityMap[priority] || priority;
  };

  // Filtrer les tickets en fonction de la recherche et du filtre
  const filteredTickets = tickets.filter(ticket => {
    const matchesSearch = ticket.titre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ticket.id.toString().includes(searchTerm);
    
    const ticketStatus = mapStatus(ticket.statut_ticket);
    const matchesStatus = statusFilter === 'Tous' || ticketStatus === statusFilter;

    return matchesSearch && matchesStatus;
  });
  
  // Options de statut pour le filtre
  const statusOptions = ['Tous', 'Nouveau', 'En cours', 'Résolu', 'Fermé', 'Annulé'];

  const handleNewTicket = () => {
    setIsNewTicketModalOpen(true);
  };

  const handleRowClick = (ticket) => {
    setSelectedTicket(ticket);
    setIsModalOpen(true);
  };
  // Gérer le clic sur "Nouveau problème". Maintenant avec choix diagnostic/ticket
  const handleNewProblem = () => {
    setIsDiagnosticOrTicketModalOpen(true);
  };

  // Gérer le choix de démarrer un diagnostic
  const handleStartDiagnostic = (categoryId) => {
    setSelectedCategoryForDiagnostic(categoryId);
    setIsDiagnosticOrTicketModalOpen(false);
    setIsDiagnosticEtapesOpen(true);
  };

  // Gérer le choix de créer un ticket directement
  const handleCreateDirectTicket = () => {
    setIsDiagnosticOrTicketModalOpen(false);
    setIsNewTicketModalOpen(true);
  };

  // Gérer la fin du diagnostic
  const handleDiagnosticComplete = async (result) => {
    setIsDiagnosticEtapesOpen(false);

    // Selon la décision finale de l'utilisateur
    if (result?.resultat_etape?.decision === 'creer_ticket_auto') {
      try {
        // Vérifier que session_id existe
        if (!result.session_id) {
          console.error('Session ID manquant dans le résultat du diagnostic');
          setIsNewTicketModalOpen(true);
          return;
        }

        // Créer directement le ticket avec les informations du diagnostic
        await apiService.post(`/diagnostic/session/${result.session_id}/create-ticket`, {});
        // Recharger la liste des tickets
        await loadTickets(true);
        // Afficher un message de succès
        alert('Ticket créé avec succès !');
      } catch (error) {
        console.error('Erreur lors de la création automatique du ticket:', error);
        // En cas d'erreur, ouvrir le modal de création manuelle
        alert('Une erreur est survenue lors de la création automatique du ticket. Vous allez être redirigé vers le formulaire de création manuelle.');
        setIsNewTicketModalOpen(true);
      }
    } else if (result?.resultat_etape?.decision === 'creer_ticket_manuel') {
      // Ouvrir le modal de création manuelle
      setIsNewTicketModalOpen(true);
    } else if (result?.resultat_etape?.decision === 'probleme_resolu') {
      // Afficher un message de succès
      alert('Parfait ! Votre problème a été résolu grâce au diagnostic automatique.');
      // Recharger les tickets pour voir les éventuels tickets automatiques
      loadTickets(true);
    }
  };

  // Créer un ticket automatiquement à partir du diagnostic
  const createTicketFromDiagnostic = async (diagnosticResult) => {
    try {
      if (!diagnosticResult || !diagnosticResult.session_id) {
        console.error('Session ID manquant pour la création du ticket');
        setIsNewTicketModalOpen(true);
        return;
      }

      const response = await apiService.createTicketFromDiagnostic(diagnosticResult.session_id);

      if (response && response.ticket_id) {
        // Recharger les tickets pour inclure le nouveau
        loadTickets(true);
        alert('Ticket créé automatiquement avec les informations du diagnostic !');
      }
    } catch (error) {
      console.error('Erreur lors de la création automatique du ticket:', error);
      // En cas d'erreur, proposer la création manuelle
      setIsNewTicketModalOpen(true);
    }
  };


  // Affichage du loading
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-800">Mes tickets</h1>
          <button
            disabled
            className="flex items-center gap-2 px-4 py-2 bg-gray-300 text-gray-500 rounded-md cursor-not-allowed"
          >
            <FaPlus />
            <span>Nouveau</span>
          </button>
        </div>
        <ContentCard>
          <div className="flex items-center justify-center py-12">
            <FaSpinner className="animate-spin h-8 w-8 text-gray-500 mr-3" />
            <span className="text-gray-500">Chargement de vos tickets...</span>
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
          <h1 className="text-3xl font-bold text-gray-800">Mes tickets</h1>
          <button
            onClick={handleNewTicket}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--primary-color)] text-white rounded-md hover:bg-[var(--primary-dark)] transition-colors"
          >
            <FaPlus />
            <span>Nouveau</span>
          </button>
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

        {/* Modals */}
        <NewTicketModal
          isOpen={isNewTicketModalOpen}
          onClose={() => setIsNewTicketModalOpen(false)}
          onSubmit={handleCreateTicket}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Mes tickets</h1>
        {user?.role === 'employe' && (
          <button
            onClick={handleNewProblem}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--primary-color)] text-white rounded-md hover:bg-[var(--primary-dark)] transition-colors"
          >
            <FaPlus />
            <span>Nouveau problème</span>
          </button>
        )}
      </div>

      <ContentCard>
        <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FaSearch className="text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[var(--primary-color)] focus:border-[var(--primary-light)] sm:text-sm transition-colors"
              placeholder="Rechercher un ticket..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <select 
              className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[var(--primary-color)] focus:border-[var(--primary-light)] sm:text-sm rounded-md transition-colors"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {status}
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
                  Titre
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Catégorie
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Statut
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Priorité
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
                  <td colSpan="6" className="px-6 py-4 text-center text-sm text-gray-500">
                    {tickets.length === 0 ? (
                      <div className="py-8">
                        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <p className="text-gray-500">Vous n'avez encore créé aucun ticket.</p>
                        {user?.role === 'employe' && (
                          <button
                            onClick={handleNewTicket}
                            className="mt-4 px-4 py-2 bg-[var(--primary-color)] text-white rounded-md hover:bg-[var(--primary-dark)] transition-colors"
                          >
                            Créer votre premier ticket
                          </button>
                        )}
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
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {ticket.categorie?.nom_categorie || 'N/A'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={mapStatus(ticket.statut_ticket)} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <PriorityBadge priority={mapPriority(ticket.priorite)} />
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
                    </div>
                  </td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
      </ContentCard>

      {/* Modals */}
      <NewTicketModal
        isOpen={isNewTicketModalOpen}
        onClose={() => setIsNewTicketModalOpen(false)}
        onSubmit={handleCreateTicket}
      />

      <TicketDetailsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        ticket={selectedTicket}
        onTicketUpdated={() => {
          loadTickets(true); // Recharger la liste après mise à jour
          setIsModalOpen(false); // Fermer le modal
        }}
      />

      <DiagnosticOrTicketModal
        isOpen={isDiagnosticOrTicketModalOpen}
        onClose={() => setIsDiagnosticOrTicketModalOpen(false)}
        onStartDiagnostic={handleStartDiagnostic}
        onCreateTicket={handleCreateDirectTicket}
      />

      <DiagnosticEtapes
        isOpen={isDiagnosticEtapesOpen}
        onClose={() => setIsDiagnosticEtapesOpen(false)}
        categoryId={selectedCategoryForDiagnostic}
        onComplete={handleDiagnosticComplete}
      />
    </div>
  );
};

export default MyTickets;
