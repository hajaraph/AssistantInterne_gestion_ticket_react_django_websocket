import React, { useState, useEffect, useRef } from 'react';
import {
  FaTimes,
  FaCheck,
  FaUndo,
  FaCog,
  FaPaperPlane,
  FaComments,
  FaPlay,
  FaStop,
  FaCheckCircle,
  FaUser,
  FaCalendarAlt,
  FaTag,
  FaDesktop
} from 'react-icons/fa';
import StatusBadge from '../badges/StatusBadge';
import PriorityBadge from '../badges/PriorityBadge';
import apiService from '../../services/api';
import webSocketService from '../../services/websocket';
import { useAuth } from '../../contexts/AuthContext';

const TicketDetailsModal = ({ ticket, isOpen, onClose, onTicketUpdated }) => {
  const [updating, setUpdating] = useState(false);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loadingComments, setLoadingComments] = useState(false);
  const [sendingComment, setSendingComment] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [isGuidanceActive, setIsGuidanceActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const { user } = useAuth();
  const commentsEndRef = useRef(null);

  // Charger les commentaires quand le ticket change
  useEffect(() => {
    if (ticket?.id) {
      console.log('Connexion WebSocket pour le ticket:', ticket.id);
      loadComments();

      // Configuration WebSocket pour les commentaires en temps réel
      const token = localStorage.getItem('access_token');
      if (token) {
        // Déconnecter d'abord toute connexion existante
        webSocketService.disconnect();

        // Se connecter au ticket correct
        webSocketService.connect(ticket.id, token);

        const handleNewComment = (comment) => {
          console.log('Nouveau commentaire reçu dans le modal pour ticket', ticket.id, ':', comment);
          setComments(prevComments => {
            const exists = prevComments.some(c => c.id === comment.id);
            if (!exists) {
              return [...prevComments, comment];
            }
            return prevComments;
          });
        };

        const handleInstructionUpdated = (instruction) => {
          console.log('Instruction mise à jour reçue pour ticket', ticket.id, ':', instruction);
          setComments(prevComments => {
            return prevComments.map(comment =>
              comment.id === instruction.id ? instruction : comment
            );
          });
        };

        const handleTicketUpdated = (updatedTicketData) => {
          console.log('Ticket mis à jour reçu via WebSocket pour ticket', ticket.id, ':', updatedTicketData);
          // Mettre à jour les données du ticket dans le modal
          Object.assign(ticket, updatedTicketData);
          // Forcer le re-render du modal si nécessaire
          if (onTicketUpdated) {
            onTicketUpdated(updatedTicketData);
          }
        };

        const handleWebSocketError = (errorMessage) => {
          console.log('Erreur WebSocket reçue pour ticket', ticket.id, ':', errorMessage);
          alert(errorMessage);
        };

        webSocketService.addEventListener('comment', handleNewComment);
        webSocketService.addEventListener('instruction_updated', handleInstructionUpdated);
        webSocketService.addEventListener('ticket_updated', handleTicketUpdated);
        webSocketService.addEventListener('error', handleWebSocketError);

        // Nettoyage lors du changement de ticket ou fermeture du modal
        return () => {
          console.log('Nettoyage WebSocket pour ticket:', ticket.id);
          webSocketService.removeEventListener('comment', handleNewComment);
          webSocketService.removeEventListener('instruction_updated', handleInstructionUpdated);
          webSocketService.removeEventListener('ticket_updated', handleTicketUpdated);
          webSocketService.removeEventListener('error', handleWebSocketError);
          webSocketService.disconnect();
        };
      }
    }
  }, [ticket?.id, onTicketUpdated]); // Ajouter onTicketUpdated aux dépendances

  // Auto-scroll vers le dernier commentaire
  useEffect(() => {
    scrollToBottom();
  }, [comments]);

  // Vérifier si une session de guidage est active
  useEffect(() => {
    console.log('Vérification du mode guidage, commentaires:', comments);

    // Chercher le dernier message de guidage (début ou fin) dans l'ordre chronologique
    let guidanceStart = null;
    let guidanceEnd = null;

    // Parcourir les commentaires pour trouver les derniers événements de guidage
    comments.forEach(comment => {
      if (comment.type_action === 'guidage_debut') {
        guidanceStart = comment;
      } else if (comment.type_action === 'guidage_fin') {
        guidanceEnd = comment;
      }
    });

    // Le guidage est actif s'il y a un début ET que soit :
    // - Il n'y a pas de fin
    // - La fin est antérieure au début (date_commentaire)
    let isActive = false;
    if (guidanceStart) {
      if (!guidanceEnd) {
        isActive = true;
      } else {
        // Comparer les dates pour voir lequel est le plus récent
        const startDate = new Date(guidanceStart.date_commentaire);
        const endDate = new Date(guidanceEnd.date_commentaire);
        isActive = startDate > endDate;
      }
    }

    console.log('Mode guidage actif:', isActive, 'Start:', guidanceStart?.id, 'End:', guidanceEnd?.id);
    setIsGuidanceActive(isActive);
  }, [comments]);

  const scrollToBottom = () => {
    commentsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadComments = async () => {
    if (!ticket?.id) return;

    setLoadingComments(true);
    try {
      const commentsData = await apiService.getTicketComments(ticket.id);
      setComments(commentsData);
    } catch (error) {
      console.error('Erreur lors du chargement des commentaires:', error);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleSendComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim() || !ticket?.id) return;

    setSendingComment(true);
    try {
      // Vérifier que le WebSocket est connecté et envoyer le message
      if (webSocketService.isWebSocketConnected()) {
        console.log('Envoi du message via WebSocket depuis le modal');
        const sent = webSocketService.sendMessage(newComment.trim());
        if (sent) {
          console.log('Message envoyé via WebSocket avec succès depuis le modal');
          setNewComment('');
          // Si en mode guidage et technicien, incrémenter l'étape
          if (user.role === 'technicien' && isGuidanceActive) {
            setCurrentStep(prev => prev + 1);
          }
        } else {
          throw new Error('Échec envoi WebSocket');
        }
      } else {
        console.error('WebSocket non connecté dans le modal');
        alert('Connexion temps réel non disponible. Veuillez actualiser la page.');
      }
    } catch (error) {
      console.error('Erreur lors de l\'envoi du commentaire:', error);
    } finally {
      setSendingComment(false);
    }
  };

  const startGuidance = async () => {
    try {
      await apiService.startGuidance(ticket.id);
      loadComments();
      setCurrentStep(1);
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors du démarrage du guidage');
    }
  };

  const endGuidance = async () => {
    try {
      await apiService.endGuidance(ticket.id, {
        message: 'Session de guidage terminée avec succès !',
        resolu: true
      });
      loadComments();
      setIsGuidanceActive(false);
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la fin du guidage');
    }
  };

  const confirmInstruction = async (commentId) => {
    try {
      // Utiliser l'API pour confirmer l'instruction (pas le WebSocket)
      await apiService.confirmInstruction(commentId, 'Étape terminée ✅');

      // Recharger les commentaires pour voir les changements
      loadComments();
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la confirmation');
    }
  };

  const getMessageIcon = (comment) => {
    const iconMap = {
      'instruction': <FaTag className="text-blue-600" />,
      'question_technicien': <FaTag className="text-orange-600" />,
      'confirmation_etape': <FaCheckCircle className="text-green-600" />,
      'guidage_debut': <FaPlay className="text-blue-600" />,
      'guidage_fin': <FaStop className="text-green-600" />,
      'assignation': <FaUser className="text-gray-600" />,
      'changement_statut': <FaTag className="text-purple-600" />,
      'default': <FaComments className="text-gray-500" />
    };
    return iconMap[comment.type_action] || iconMap.default;
  };

  if (!isOpen || !ticket) return null;

  const handleStatusUpdate = async (newStatus) => {
    setUpdating(true);
    try {
      const updatedTicket = await apiService.updateTicketStatus(ticket.id, newStatus);
      if (onTicketUpdated) {
        onTicketUpdated(updatedTicket);
      }
    } catch (error) {
      console.error('Erreur lors de la mise à jour du statut:', error);
      alert('Erreur lors de la mise à jour du statut');
    } finally {
      setUpdating(false);
    }
  };

  const handleTakeOwnership = async () => {
    setUpdating(true);
    try {
      const updatedTicket = await apiService.assignTicketToSelf(ticket.id);

      // Mettre à jour les données locales du ticket sans fermer le modal
      Object.assign(ticket, updatedTicket);

      // Recharger les commentaires pour voir le commentaire d'assignation automatique
      loadComments();

    } catch (error) {
      console.error('Erreur lors de la prise en charge:', error);
      alert('Erreur lors de la prise en charge du ticket');
    } finally {
      setUpdating(false);
    }
  };

  const getAvailableActions = () => {
    const actions = [];

    if (user.role === 'technicien') {
      // Techinicien peut prendre en charge un ticket non assigné
      if (!ticket.technicien_assigne) {
        actions.push({
          label: 'Prendre en charge',
          icon: FaCog,
          onClick: handleTakeOwnership,
          className: 'bg-blue-500 hover:bg-blue-600 text-white'
        });
      }

      // Techinicien peut marquer comme résolu ses tickets assignés
      if (ticket.technicien_assigne?.id === user.id && ticket.statut_ticket === 'en_cours') {
        actions.push({
          label: 'Marquer résolu',
          icon: FaCheck,
          onClick: () => handleStatusUpdate('resolu'),
          className: 'bg-green-500 hover:bg-green-600 text-white'
        });
      }
    }

    if (user.role === 'employe' && ticket.utilisateur_createur?.id === user.id) {
      // Employé peut fermer un ticket résolu
      if (ticket.statut_ticket === 'resolu') {
        actions.push({
          label: 'Fermer le ticket',
          icon: FaCheck,
          onClick: () => handleStatusUpdate('ferme'),
          className: 'bg-gray-500 hover:bg-gray-600 text-white'
        });
      }

      // Employé peut rouvrir un ticket fermé
      if (ticket.statut_ticket === 'ferme') {
        actions.push({
          label: 'Rouvrir le ticket',
          icon: FaUndo,
          onClick: () => handleStatusUpdate('ouvert'),
          className: 'bg-orange-500 hover:bg-orange-600 text-white'
        });
      }
    }

    return actions;
  };

  const canAccessChat = () => {
    if (user.role === 'employe') {
      // L'employé ne peut accéder au chat que si :
      // 1. C'est son ticket
      // 2. Un technicien a pris en charge le ticket
      return ticket.utilisateur_createur?.id === user.id && ticket.technicien_assigne;
    }
    if (user.role === 'technicien') {
      return ticket.technicien_assigne?.id === user.id;
    }
    return user.role === 'admin';
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-[90vh] flex flex-col border border-gray-200">
        {/* Header simple */}
        <div className="bg-gray-50 p-6 border-b border-gray-200 flex-shrink-0">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Ticket #{ticket.id}
                </h2>
                <p className="text-gray-600 mt-1">{ticket.titre}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex gap-2">
                <StatusBadge status={ticket.statut_ticket} />
                <PriorityBadge priority={ticket.priorite} />
                {isGuidanceActive && (
                  <span className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-full px-3 py-1 text-sm text-blue-800">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    Guidage actif
                  </span>
                )}
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <FaTimes className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Panel principal */}
          <div className={`${showChat ? 'w-1/2' : 'w-full'} flex flex-col transition-all duration-200`}>
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-6">
                {/* Informations principales - Design simple */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <FaUser className="text-gray-500 h-4 w-4" />
                      <span className="font-medium text-gray-700">Créé par</span>
                    </div>
                    <p className="text-gray-900">
                      {ticket.utilisateur_createur?.nom_complet || ticket.utilisateur_createur?.email}
                    </p>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <FaCog className="text-gray-500 h-4 w-4" />
                      <span className="font-medium text-gray-700">Assigné à</span>
                    </div>
                    <p className="text-gray-900">
                      {ticket.technicien_assigne
                        ? ticket.technicien_assigne.nom_complet || ticket.technicien_assigne.email
                        : <span className="text-gray-500 italic">Non assigné</span>
                      }
                    </p>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <FaTag className="text-gray-500 h-4 w-4" />
                      <span className="font-medium text-gray-700">Catégorie</span>
                    </div>
                    <p className="text-gray-900">{ticket.categorie?.nom_categorie}</p>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <FaDesktop className="text-gray-500 h-4 w-4" />
                      <span className="font-medium text-gray-700">Équipement</span>
                    </div>
                    <p className="text-gray-900">
                      {ticket.equipement
                        ? `${ticket.equipement.nom_modele} (${ticket.equipement.numero_serie})`
                        : <span className="text-gray-500 italic">Aucun</span>
                      }
                    </p>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <FaCalendarAlt className="text-gray-500 h-4 w-4" />
                      <span className="font-medium text-gray-700">Créé le</span>
                    </div>
                    <p className="text-gray-900">
                      {new Date(ticket.date_creation).toLocaleDateString('fr-FR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <FaCalendarAlt className="text-gray-500 h-4 w-4" />
                      <span className="font-medium text-gray-700">Modifié le</span>
                    </div>
                    <p className="text-gray-900">
                      {new Date(ticket.date_modification).toLocaleDateString('fr-FR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                </div>

                {/* Description */}
                <div className="bg-white border border-gray-200 rounded-lg">
                  <div className="px-4 py-3 border-b border-gray-200">
                    <h4 className="font-medium text-gray-900">Description du problème</h4>
                  </div>
                  <div className="p-4">
                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{ticket.description}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions - Design simple */}
            <div className="p-6 border-t border-gray-200 bg-gray-50 flex-shrink-0">
              <div className="flex flex-wrap gap-3">
                {getAvailableActions().map((action, index) => {
                  const IconComponent = action.icon;
                  return (
                    <button
                      key={index}
                      onClick={action.onClick}
                      disabled={updating}
                      className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <IconComponent className="h-4 w-4" />
                      {action.label}
                    </button>
                  );
                })}

                {/* Boutons de guidage */}
                {user.role === 'technicien' && ticket.technicien_assigne?.id === user.id && (
                  <>
                    {!isGuidanceActive ? (
                      <button
                        onClick={startGuidance}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <FaPlay className="h-4 w-4" />
                        Démarrer guidage
                      </button>
                    ) : (
                      <button
                        onClick={endGuidance}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        <FaStop className="h-4 w-4" />
                        Terminer guidage
                      </button>
                    )}
                  </>
                )}

                {/* Bouton Discussion */}
                {canAccessChat() && (
                  <button
                    onClick={() => setShowChat(!showChat)}
                    className={`relative flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                      showChat 
                        ? 'bg-gray-600 text-white hover:bg-gray-700' 
                        : 'bg-indigo-600 text-white hover:bg-indigo-700'
                    }`}
                  >
                    <FaComments className="h-4 w-4" />
                    {showChat ? 'Masquer discussion' : 'Discussion'}

                    {/* Badge indicateur de discussion */}
                    {comments.length > 0 && (
                      <span
                        className="absolute -top-2 -right-2 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white rounded-full"
                        style={{ backgroundColor: 'var(--success-color)' }}
                      >
                        {comments.length}
                      </span>
                    )}

                    {/* Point indicateur pour les nouveaux messages non lus */}
                    {!showChat && comments.length > 0 && (
                      <div
                        className="absolute top-1 right-1 w-2 h-2 rounded-full"
                        style={{ backgroundColor: 'var(--success-color)' }}
                      ></div>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Panel Discussion */}
          {showChat && canAccessChat() && (
            <div className="w-1/2 border-l border-gray-200 flex flex-col bg-white">
              {/* En-tête simple */}
              <div className="bg-gray-50 p-4 border-b border-gray-200 flex-shrink-0">
                <div className="flex items-center gap-3">
                  <FaComments className="h-5 w-5 text-gray-600" />
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {isGuidanceActive ? 'Session de guidage active' : 'Discussion'}
                    </h4>
                    {user.role === 'technicien' && isGuidanceActive && (
                      <p className="text-gray-600 text-sm mt-1">
                        Mode guidage : vos messages deviennent des instructions
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Zone des commentaires - Style chat avec hauteur fixe */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50" style={{ minHeight: 0 }}>
                {loadingComments ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-300"></div>
                    <span className="ml-3 text-gray-600">Chargement...</span>
                  </div>
                ) : comments.length === 0 ? (
                  <div className="text-center py-8">
                    <FaComments className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">Aucun commentaire pour le moment</p>
                    <p className="text-gray-400 text-sm mt-1">Commencez la conversation...</p>
                  </div>
                ) : (
                  comments.map((comment) => {
                    const isOwnMessage = comment.auteur?.id === user.id;
                    const isTechnician = comment.auteur?.role === 'technicien';
                    const isSystemMessage = ['guidage_debut', 'guidage_fin', 'assignation', 'changement_statut'].includes(comment.type_action);

                    if (isSystemMessage) {
                      // Messages système centrés
                      return (
                        <div key={comment.id} className="flex justify-center my-4">
                          <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium max-w-xs text-center">
                            <div className="flex items-center justify-center gap-2">
                              {getMessageIcon(comment)}
                              <span>{comment.contenu}</span>
                            </div>
                            <div className="text-xs text-blue-600 mt-1">
                              {new Date(comment.date_commentaire).toLocaleTimeString('fr-FR', {
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </div>
                          </div>
                        </div>
                      );
                    }

                    return (
                      <div key={comment.id} className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'} mb-4`}>
                        <div className={`max-w-xs lg:max-w-md ${isOwnMessage ? 'order-2' : 'order-1'}`}>
                          {/* Avatar et nom (seulement pour les messages des autres) */}
                          {!isOwnMessage && (
                            <div className="flex items-center gap-2 mb-1">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium text-white ${
                                isTechnician ? 'bg-blue-500' : 'bg-gray-500'
                              }`}>
                                {(comment.auteur?.nom_complet || comment.auteur?.email || 'U').charAt(0).toUpperCase()}
                              </div>
                              <span className="text-xs text-gray-600 font-medium">
                                {comment.auteur?.nom_complet || comment.auteur?.email}
                              </span>
                              {isTechnician && (
                                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
                                  Technicien
                                </span>
                              )}
                            </div>
                          )}

                          {/* Bulle de message */}
                          <div className={`relative px-4 py-3 rounded-2xl shadow-sm ${
                            isOwnMessage 
                              ? 'bg-blue-500 text-white' 
                              : comment.est_instruction 
                                ? 'bg-orange-50 border border-orange-200 text-gray-800' 
                                : 'bg-white border border-gray-200 text-gray-800'
                          }`}>
                            {/* Badge d'étape pour les instructions */}
                            {comment.numero_etape && (
                              <div className="flex items-center gap-2 mb-2">
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  isOwnMessage ? 'bg-blue-600 text-blue-100' : 'bg-orange-100 text-orange-800'
                                }`}>
                                  Étape {comment.numero_etape}
                                </span>
                              </div>
                            )}

                            {/* Contenu du message */}
                            <div className={comment.est_instruction ? 'border-l-3 border-orange-400 pl-3' : ''}>
                              <p className="text-sm leading-relaxed whitespace-pre-wrap">{comment.contenu}</p>
                            </div>

                            {/* Heure du message */}
                            <div className={`text-xs mt-2 ${
                              isOwnMessage ? 'text-blue-100' : 'text-gray-500'
                            }`}>
                              {new Date(comment.date_commentaire).toLocaleTimeString('fr-FR', {
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </div>

                            {/* Flèche de la bulle */}
                            <div className={`absolute top-3 ${
                              isOwnMessage 
                                ? 'right-0 transform translate-x-1' 
                                : 'left-0 transform -translate-x-1'
                            }`}>
                              <div className={`w-3 h-3 transform rotate-45 ${
                                isOwnMessage 
                                  ? 'bg-blue-500' 
                                  : comment.est_instruction 
                                    ? 'bg-orange-50 border-l border-b border-orange-200' 
                                    : 'bg-white border-l border-b border-gray-200'
                              }`}></div>
                            </div>
                          </div>

                          {/* Bouton de confirmation pour les instructions */}
                          {comment.est_instruction &&
                           !comment.est_confirme &&
                           user.role === 'employe' &&
                           comment.auteur?.id !== user.id &&
                           isGuidanceActive && (
                            <div className="mt-3">
                              <button
                                onClick={() => confirmInstruction(comment.id)}
                                className="inline-flex items-center gap-2 px-4 py-2 bg-green-500 text-white text-sm rounded-2xl hover:bg-green-600 transition-colors shadow-sm font-medium"
                              >
                                <FaCheckCircle className="h-4 w-4" />
                                Confirmer cette étape
                              </button>
                            </div>
                          )}

                          {/* Statut de confirmation */}
                          {comment.est_confirme && (
                            <div className="mt-2">
                              <div className="inline-flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-200">
                                <FaCheckCircle className="h-4 w-4" />
                                Étape confirmée
                                {comment.date_confirmation && (
                                  <span className="text-xs text-green-500 ml-2">
                                    le {new Date(comment.date_confirmation).toLocaleDateString('fr-FR')} à{' '}
                                    {new Date(comment.date_confirmation).toLocaleTimeString('fr-FR', {
                                      hour: '2-digit',
                                      minute: '2-digit'
                                    })}
                                  </span>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Réponses en chaîne */}
                          {comment.reponses && comment.reponses.length > 0 && (
                            <div className="mt-3 space-y-2">
                              {comment.reponses.map((reply) => {
                                const isOwnReply = reply.auteur?.id === user.id;
                                return (
                                  <div key={reply.id} className={`flex ${isOwnReply ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                                      isOwnReply 
                                        ? 'bg-blue-400 text-white' 
                                        : 'bg-gray-200 text-gray-800'
                                    }`}>
                                      {!isOwnReply && (
                                        <div className="font-medium text-xs mb-1">
                                          {reply.auteur?.nom_complet || reply.auteur?.email}
                                        </div>
                                      )}
                                      <div>{reply.contenu}</div>
                                      <div className={`text-xs mt-1 ${isOwnReply ? 'text-blue-100' : 'text-gray-500'}`}>
                                        {new Date(reply.date_commentaire).toLocaleTimeString('fr-FR', {
                                          hour: '2-digit',
                                          minute: '2-digit'
                                        })}
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={commentsEndRef} />
              </div>

              {/* Zone de saisie */}
              <div className="p-4 bg-white border-t border-gray-200 flex-shrink-0">
                {/* Afficher un message informatif si l'employé ne peut pas envoyer de messages */}
                {user.role === 'employe' && isGuidanceActive ? (
                  <div className="text-center py-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center justify-center gap-2 text-blue-800 mb-2">
                        <FaPlay className="h-4 w-4" />
                        <span className="font-medium">Session de guidage en cours</span>
                      </div>
                      <p className="text-blue-600 text-sm">
                        Le technicien vous guide étape par étape. Suivez ses instructions et confirmez chaque étape terminée.
                      </p>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handleSendComment} className="flex gap-3 items-start">
                    <div className="flex-1">
                      <textarea
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSendComment(e);
                          }
                        }}
                        placeholder={
                          user.role === 'technicien' && isGuidanceActive
                            ? "Tapez votre instruction..."
                            : "Tapez votre message..."
                        }
                        className="w-full border border-gray-300 rounded-2xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                        rows="1"
                        style={{ minHeight: '44px', maxHeight: '120px' }}
                        disabled={sendingComment}
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={sendingComment || !newComment.trim()}
                      className="flex-shrink-0 w-11 h-11 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm flex items-center justify-center"
                      style={{ marginTop: '1px' }}
                    >
                      <FaPaperPlane className="h-4 w-4" />
                    </button>
                  </form>
                )}

                {/* Indicateur de mode guidage pour le technicien */}
                {user.role === 'technicien' && isGuidanceActive && (
                  <div className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                    <span className="w-2 h-2 bg-orange-400 rounded-full"></span>
                    Mode guidage actif - Vos messages deviennent des instructions
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TicketDetailsModal;
