import React, { useState, useEffect, useRef } from 'react';
import {
  FaPaperPlane,
  FaCheckCircle,
  FaTools,
  FaQuestion,
  FaSyncAlt,
  FaWifi,
} from 'react-icons/fa';
import webSocketService from '../services/websocket';

const ChatGuidance = ({ ticket, user, onCommentAdded }) => {
  const [comments, setComments] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [isGuidanceActive, setIsGuidanceActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [connectionStatus, setConnectionStatus] = useState('DISCONNECTED');
  const [hasUnconfirmedInstruction, setHasUnconfirmedInstruction] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Vérifier si une session de guidage est active
  useEffect(() => {
    const hasGuidanceStart = comments.some(c => c.type_action === 'guidage_debut');
    const hasGuidanceEnd = comments.some(c => c.type_action === 'guidage_fin');
    setIsGuidanceActive(hasGuidanceStart && !hasGuidanceEnd);

    // Vérifier s'il y a une instruction non confirmée pour l'employé
    if (user.role === 'employe') {
      const unconfirmedInstruction = comments.some(c =>
        c.est_instruction &&
        c.attendre_confirmation &&
        !c.est_confirme &&
        c.auteur?.id !== user.id
      );
      setHasUnconfirmedInstruction(unconfirmedInstruction);
    }
  }, [comments]);

  // Faire défiler vers le bas automatiquement
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [comments]);

  // Configuration des WebSockets
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token || !ticket?.id) return;

    // Charger les commentaires initiaux
    loadComments();

    console.log('Tentative de connexion WebSocket pour ticket:', ticket.id);
    // Connecter le WebSocket
    webSocketService.connect(ticket.id, token);

    // Écouter les événements WebSocket
    const handleNewComment = (comment) => {
      console.log('Nouveau commentaire reçu via WebSocket:', comment);
      setComments(prevComments => {
        // Vérifier si le commentaire existe déjà pour éviter les doublons
        const exists = prevComments.some(c => c.id === comment.id);
        if (!exists) {
          return [...prevComments, comment];
        }
        return prevComments;
      });
      if (onCommentAdded) onCommentAdded();
    };

    const handleConnectionOpen = () => {
      console.log('WebSocket connecté - événement onopen déclenché');
      setConnectionStatus('CONNECTED');
      console.log('connectionStatus mis à jour vers CONNECTED');
    };

    const handleConnectionClose = () => {
      console.log('WebSocket déconnecté');
      setConnectionStatus('DISCONNECTED');
    };

    const handleConnectionError = (error) => {
      console.error('Erreur WebSocket:', error);
      setConnectionStatus('ERROR');
    };

    // Ajouter les listeners
    webSocketService.addEventListener('comment', handleNewComment);
    webSocketService.addEventListener('open', handleConnectionOpen);
    webSocketService.addEventListener('close', handleConnectionClose);
    webSocketService.addEventListener('error', handleConnectionError);

    // Cleanup
    return () => {
      webSocketService.removeEventListener('comment', handleNewComment);
      webSocketService.removeEventListener('open', handleConnectionOpen);
      webSocketService.removeEventListener('close', handleConnectionClose);
      webSocketService.removeEventListener('error', handleConnectionError);
      webSocketService.disconnect();
    };
  }, [ticket?.id, onCommentAdded]);

  // Charger les commentaires (une seule fois au chargement initial)
  const loadComments = async () => {
    try {
      const response = await fetch(`/api/tickets/${ticket.id}/comments/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setComments(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des commentaires:', error);
    }
  };

  // Fonction pour envoyer un message via WebSocket uniquement
  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    // Empêcher l'employé d'envoyer des messages s'il y a une instruction non confirmée
    if (user.role === 'employe' && isGuidanceActive && hasUnconfirmedInstruction) {
      alert('Veuillez d\'abord confirmer l\'instruction en cours avant d\'envoyer un nouveau message.');
      return;
    }

    console.log('sendMessage appelé - connectionStatus:', connectionStatus);
    console.log('WebSocket isConnected:', webSocketService.isWebSocketConnected());
    setLoading(true);
    try {
      // Vérifier directement si le WebSocket est ouvert
      if (webSocketService.isWebSocketConnected()) {
        // Envoyer via WebSocket pour le temps réel
        const sent = webSocketService.sendMessage(newMessage.trim());
        if (sent) {
          console.log('Message envoyé via WebSocket avec succès');
          // Vider le champ de saisie immédiatement
          setNewMessage('');
        } else {
          console.error('Échec envoi WebSocket - socket non disponible');
        }
      } else {
        console.error('WebSocket non connecté - impossible d\'envoyer le message');
        alert('Connexion WebSocket non disponible. Veuillez actualiser la page.');
       }
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
     } finally {
       setLoading(false);
     }
   };

  // Démarrer une session de guidage (technicien)
  const startGuidance = async () => {
    try {
      const response = await fetch(`/api/tickets/${ticket.id}/guidance/start/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        loadComments();
        setCurrentStep(1);
      }
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  // Envoyer une instruction (technicien)
  const sendInstruction = async () => {
    if (!newMessage.trim()) return;

    setLoading(true);
    try {
      // Envoyer l'instruction via WebSocket avec les métadonnées du guidage
      if (webSocketService.isWebSocketConnected()) {
        const instructionData = {
          type: 'instruction',
          message: newMessage.trim(),
          numero_etape: currentStep,
          attendre_confirmation: true,
          est_instruction: true
        };
        const sent = webSocketService.sendMessage(JSON.stringify(instructionData));
        if (sent) {
          console.log('Instruction envoyée via WebSocket:', instructionData);
          setNewMessage('');
          setCurrentStep(prev => prev + 1);
        } else {
          throw new Error('Échec envoi instruction WebSocket');
        }
      } else {
        console.error('WebSocket non connecté pour l\'instruction');
        alert('Connexion temps réel non disponible. Veuillez actualiser la page.');
      }
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  // Confirmer une instruction (employé)
  const confirmInstruction = async (commentId) => {
    try {
      // Envoyer la confirmation via WebSocket
      if (webSocketService.isWebSocketConnected()) {
        const confirmationData = {
          type: 'confirmation',
          message: 'Étape terminée ✅',
          commentaire_parent_id: commentId,
          type_action: 'confirmation_etape'
        };
        const sent = webSocketService.sendMessage(JSON.stringify(confirmationData));
        if (sent) {
          console.log('Confirmation envoyée via WebSocket');
        } else {
          throw new Error('Échec envoi confirmation WebSocket');
        }
      } else {
        console.error('WebSocket non connecté pour la confirmation');
        alert('Connexion temps réel non disponible. Veuillez actualiser la page.');
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la confirmation');
    }
  };

  // Terminer le guidage (technicien)
  const endGuidance = async () => {
    try {
      const response = await fetch(`/api/tickets/${ticket.id}/guidance/end/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          message: 'Session de guidage terminée avec succès !',
          resolu: true
        }),
      });

      if (response.ok) {
        loadComments();
        setIsGuidanceActive(false);
      }
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  // Obtenir l'icône selon le type de message
  const getMessageIcon = (comment) => {
    switch (comment.type_action) {
      case 'instruction':
        return <FaTools className="text-blue-500" />;
      case 'question_technicien':
        return <FaQuestion className="text-orange-500" />;
      case 'confirmation_etape':
        return <FaCheckCircle className="text-green-500" />;
      case 'guidage_debut':
        return <FaTools className="text-green-600" />;
      case 'guidage_fin':
        return <FaCheckCircle className="text-green-600" />;
      default:
        return null;
    }
  };

  // Obtenir la classe CSS selon le rôle de l'auteur
  const getMessageClass = (comment) => {
    const isOwn = comment.auteur?.id === user.id;
    const baseClass = "flex mb-4 animate-fade-in";
    return isOwn ? `${baseClass} justify-end` : baseClass;
  };

  const getBubbleClass = (comment) => {
    const isOwn = comment.auteur?.id === user.id;
    const isTechnician = comment.auteur?.role === 'technicien';
    const isInstruction = comment.est_instruction;

    let baseClass = "max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow";

    if (isInstruction) {
      baseClass += " border-l-4 border-blue-500 bg-blue-50";
    } else if (isOwn) {
      baseClass += " bg-blue-500 text-white";
    } else if (isTechnician) {
      baseClass += " bg-gray-100 border border-gray-200";
    } else {
      baseClass += " bg-white border border-gray-200";
    }

    return baseClass;
  };

  // Indicateur de statut de connexion
  const ConnectionStatus = () => {
    const getStatusIcon = () => {
      switch (connectionStatus) {
        case 'CONNECTED':
          return <FaWifi className="text-green-500" />;
        case 'CONNECTING':
          return <FaSyncAlt className="text-yellow-500 animate-spin" />;
        case 'ERROR':
          return <FaWifiSlash className="text-red-500" />;
        default:
          return <FaWifiSlash className="text-gray-500" />;
      }
    };

    const getStatusText = () => {
      switch (connectionStatus) {
        case 'CONNECTED':
          return 'Temps réel activé';
        case 'CONNECTING':
          return 'Connexion...';
        case 'ERROR':
          return 'Erreur de connexion';
        default:
          return 'Hors ligne';
      }
    };

    return (
      <div className="flex items-center gap-2 text-sm">
        {getStatusIcon()}
        <span className={`
          ${connectionStatus === 'CONNECTED' ? 'text-green-600' : ''}
          ${connectionStatus === 'CONNECTING' ? 'text-yellow-600' : ''}
          ${connectionStatus === 'ERROR' ? 'text-red-600' : ''}
          ${connectionStatus === 'DISCONNECTED' ? 'text-gray-600' : ''}
        `}>
          {getStatusText()}
        </span>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-96 bg-gray-50 rounded-lg border">
      {/* En-tête du chat */}
      <div className="bg-white px-4 py-3 border-b border-gray-200 rounded-t-lg">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-gray-800">
            {isGuidanceActive ? '🔧 Session de guidage active' : 'Discussion'}
          </h3>
          <div className="flex gap-2">
            <button
              onClick={loadComments}
              className="p-1 text-gray-500 hover:text-gray-700"
              title="Actualiser"
            >
              <FaSyncAlt className="h-4 w-4" />
            </button>
            {user.role === 'technicien' && ticket.technicien_assigne?.id === user.id && (
              <>
                {!isGuidanceActive ? (
                  <button
                    onClick={startGuidance}
                    className="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
                  >
                    Démarrer guidage
                  </button>
                ) : (
                  <button
                    onClick={endGuidance}
                    className="px-3 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600"
                  >
                    Terminer guidage
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Zone des messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {comments.map((comment) => (
          <div key={comment.id} className={getMessageClass(comment)}>
            <div className={getBubbleClass(comment)}>
              <div className="flex items-start gap-2">
                {getMessageIcon(comment)}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium">
                      {comment.auteur?.nom_complet || comment.auteur?.email}
                    </span>
                    {comment.auteur?.role === 'technicien' && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-1 rounded">
                        Technicien
                      </span>
                    )}
                    {comment.numero_etape && (
                      <span className="text-xs bg-gray-100 text-gray-800 px-1 rounded">
                        Étape {comment.numero_etape}
                      </span>
                    )}
                  </div>
                  <p className="text-sm">{comment.contenu}</p>

                  {/* Bouton de confirmation pour les instructions */}
                  {comment.est_instruction &&
                   comment.attendre_confirmation &&
                   !comment.est_confirme &&
                   user.role === 'employe' &&
                   comment.auteur?.id !== user.id && (
                    <button
                      onClick={() => confirmInstruction(comment.id)}
                      className="mt-2 px-3 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600"
                    >
                      ✅ Confirmer l'étape
                    </button>
                  )}

                  {comment.est_confirme && (
                    <div className="mt-1 text-xs text-green-600 flex items-center gap-1">
                      <FaCheckCircle />
                      Confirmé
                    </div>
                  )}
                </div>
              </div>

              <div className="text-xs text-gray-500 mt-1">
                {new Date(comment.date_commentaire).toLocaleTimeString('fr-FR', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>

              {/* Réponses en chaîne */}
              {comment.reponses && comment.reponses.length > 0 && (
                <div className="mt-2 ml-4 border-l-2 border-gray-200 pl-2">
                  {comment.reponses.map((reply) => (
                    <div key={reply.id} className="mb-2 p-2 bg-gray-50 rounded text-sm">
                      <div className="font-medium text-xs">
                        {reply.auteur?.nom_complet || reply.auteur?.email}
                      </div>
                      <div>{reply.contenu}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Zone de saisie */}
      <div className="bg-white border-t border-gray-200 p-4 rounded-b-lg">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (user.role === 'technicien' && isGuidanceActive) {
                  sendInstruction();
                } else {
                  sendMessage();
                }
              }
            }}
            placeholder={
              user.role === 'technicien' && isGuidanceActive
                ? "Tapez votre instruction..."
                : "Tapez votre message..."
            }
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />

          {user.role === 'technicien' && isGuidanceActive ? (
            <button
              onClick={sendInstruction}
              disabled={loading || !newMessage.trim()}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <FaTools className="h-4 w-4" />
              Instruction
            </button>
          ) : (
            <button
              onClick={() => sendMessage()}
              disabled={loading || !newMessage.trim()}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FaPaperPlane className="h-4 w-4" />
            </button>
          )}
        </div>

        {user.role === 'technicien' && isGuidanceActive && (
          <div className="text-xs text-gray-500 mt-2">
            💡 Vous êtes en mode guidage. Vos messages seront envoyés comme des instructions.
          </div>
        )}

        {user.role === 'employe' && isGuidanceActive && hasUnconfirmedInstruction && (
          <div className="text-xs text-orange-600 mt-2 flex items-center gap-1">
            <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
            Veuillez confirmer l'instruction ci-dessus avant de continuer.
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatGuidance;
