import React, { useState, useEffect, useCallback } from 'react';
import {
  FaRobot, FaPause, FaStop, FaTimes,
  FaClock, FaExclamationTriangle, FaInfoCircle,
  FaSpinner, FaCheck, FaMemory, FaHdd, FaMicrochip,
  FaChartBar, FaDesktop
} from 'react-icons/fa';
import apiService from '../../services/api';

const DiagnosticManuelModal = ({ isOpen, onClose, categoryId, onComplete }) => {
  // États pour le diagnostic en cours
  const [currentSession, setCurrentSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [answering, setAnswering] = useState(false);
  const [error, setError] = useState(null);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [finalResults, setFinalResults] = useState(null);

  // Nouveaux états pour les informations système
  const [systemInfo, setSystemInfo] = useState(null);
  const [showSystemInfo, setShowSystemInfo] = useState(false);
  const [systemInfoLoading, setSystemInfoLoading] = useState(false);

  // Charger les informations système détaillées (fallback)
  const loadSystemInfo = useCallback(async (sessionId) => {
    try {
      setSystemInfoLoading(true);

      // Attendre un peu pour que le diagnostic automatique se termine
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Récupérer les détails de la session avec les diagnostics
      const sessionDetails = await apiService.getDiagnosticSession(sessionId);

      if (sessionDetails.diagnostic_automatique) {
        setSystemInfo(sessionDetails.diagnostic_automatique);
      }

    } catch (err) {
      console.error('Erreur lors du chargement des infos système:', err);
      setError('Impossible de charger les informations système');
    } finally {
      setSystemInfoLoading(false);
    }
  }, []);

  // Charger les informations de la catégorie
  const loadCategoryInfo = useCallback(async () => {
    try {
      const categories = await apiService.getCategories();
      const category = categories.find(c => c.id === categoryId);

      // Stocker la catégorie pour déterminer si on doit afficher les infos système
      if (category && (
        category.nom_categorie.toLowerCase().includes('performance') ||
        category.nom_categorie.toLowerCase().includes('système') ||
        category.nom_categorie.toLowerCase().includes('matériel') ||
        category.nom_categorie.toLowerCase().includes('hardware')
      )) {
        setShowSystemInfo(true);
      }
    } catch (err) {
      console.error('Erreur lors du chargement de la catégorie:', err);
    }
  }, [categoryId]);

  // Démarrer un nouveau diagnostic manuel
  const startDiagnostic = useCallback(async () => {
    try {
      setSessionLoading(true);
      setError(null);

      // Si on doit afficher les infos système, commencer le chargement immédiatement
      if (showSystemInfo) {
        setSystemInfoLoading(true);
      }

      const sessionData = { categorie: categoryId };
      const response = await apiService.createDiagnosticSession(sessionData);

      setCurrentSession(response.session_id);

      // Toujours attendre un minimum pour l'effet visuel du chargement
      if (showSystemInfo) {
        // Si les données sont déjà dans la réponse, les utiliser après un délai minimum
        if (response.diagnostic_automatique) {
          // Attendre un minimum de 2 secondes pour l'effet visuel
          await new Promise(resolve => setTimeout(resolve, 2000));
          setSystemInfo(response.diagnostic_automatique);
          setSystemInfoLoading(false);
        } else {
          // Sinon, utiliser le fallback avec loadSystemInfo
          await loadSystemInfo(response.session_id);
        }
      }

      // Charger la première question immédiatement
      await loadNextQuestion(response.session_id);
    } catch (err) {
      console.error('Erreur lors du démarrage du diagnostic:', err);
      setError(err.message);
      setSystemInfoLoading(false);
    } finally {
      setSessionLoading(false);
    }
  }, [categoryId, showSystemInfo, loadSystemInfo]);

  // Charger la catégorie à l'ouverture du modal
  useEffect(() => {
    if (isOpen && categoryId) {
      loadCategoryInfo();
    }
  }, [isOpen, categoryId, loadCategoryInfo]);

  // Démarrer le diagnostic uniquement quand showSystemInfo est prêt
  useEffect(() => {
    if (isOpen && categoryId) {
      startDiagnostic();
    }
  }, [isOpen, categoryId, showSystemInfo, startDiagnostic]);

  useEffect(() => {
    if (!isOpen) {
      // Reset des états quand le modal se ferme
      setCurrentSession(null);
      setCurrentQuestion(null);
      setSessionLoading(false);
      setAnswering(false);
      setError(null);
      setSessionComplete(false);
      setFinalResults(null);
      setSystemInfo(null);
      setShowSystemInfo(false);
      setSystemInfoLoading(false);
    }
  }, [isOpen]);

  // Charger la prochaine question
  const loadNextQuestion = useCallback(async (sessionId) => {
    try {
      const response = await apiService.getNextQuestion(sessionId);

      if (response.session_complete) {
        // Diagnostic terminé
        setCurrentQuestion(null);
        setSessionComplete(true);
        setFinalResults({
          priorite_estimee: response.priorite_estimee,
          score_total: response.score_total,
          recommandations: response.recommandations,
          session_id: sessionId
        });
      } else {
        setCurrentQuestion(response);
      }
    } catch (err) {
      console.error('Erreur lors du chargement de la question:', err);
      setError(err.message);
    }
  }, []);

  // Répondre à une question
  const submitAnswer = useCallback(async (questionId, answerData) => {
    // Éviter les double clics avec un système plus robuste
    if (answering) {
      console.log('Réponse déjà en cours de traitement...');
      return;
    }

    try {
      setAnswering(true);
      setError(null);

      console.log('Envoi de la réponse:', { questionId, answerData, sessionId: currentSession });

      await apiService.submitDiagnosticAnswer(currentSession, {
        question: questionId,
        ...answerData
      });

      console.log('Réponse envoyée avec succès, chargement de la question suivante...');

      // Charger la question suivante
      await loadNextQuestion(currentSession);
    } catch (err) {
      console.error('Erreur lors de l\'envoi de la réponse:', err);
      setError(err.message);
    } finally {
      // S'assurer que answering est remis à false même en cas d'erreur
      setTimeout(() => {
        setAnswering(false);
      }, 100);
    }
  }, [currentSession, loadNextQuestion]);

  // Mettre en pause la session
  const pauseSession = async () => {
    try {
      await apiService.pauseDiagnosticSession(currentSession, 'Pause utilisateur');
      onClose();
    } catch (err) {
      console.error('Erreur lors de la mise en pause:', err);
      setError(err.message);
    }
  };

  // Fermer le modal et compléter le diagnostic
  const handleComplete = () => {
    if (onComplete && finalResults) {
      onComplete(finalResults);
    }
    onClose();
  };

  // Créer un ticket à partir du diagnostic
  const createTicketFromDiagnostic = async () => {
    try {
      const response = await apiService.createTicketFromDiagnostic(currentSession);
      alert(`Ticket créé avec succès ! ID: ${response.ticket_id}`);
      handleComplete();
    } catch (err) {
      console.error('Erreur lors de la création du ticket:', err);
      setError(err.message);
    }
  };

  // Fonction pour rendre les informations système détaillées
  const renderSystemInfo = () => {
    if (!showSystemInfo) return null;

    return (
      <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
        <h4 className="font-medium text-blue-900 mb-3 flex items-center">
          <FaDesktop className="mr-2" />
          Informations système détaillées
        </h4>

        {systemInfoLoading ? (
          <div className="flex items-center justify-center py-4">
            <FaSpinner className="animate-spin text-blue-500 mr-2" />
            <span className="text-blue-700">Analyse du système en cours...</span>
          </div>
        ) : systemInfo ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Informations CPU */}
            {systemInfo.cpu && (
              <div className="bg-white rounded-lg p-3 border border-blue-100">
                <div className="flex items-center mb-2">
                  <FaMicrochip className="text-blue-600 mr-2" />
                  <h5 className="font-medium text-gray-800">Processeur</h5>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Utilisation:</span>
                    <span className={`font-medium ${
                      systemInfo.cpu.details?.utilisation_pourcentage > 80 ? 'text-red-600' :
                      systemInfo.cpu.details?.utilisation_pourcentage > 60 ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {systemInfo.cpu.details?.utilisation_pourcentage || 'N/A'}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Cœurs:</span>
                    <span className="text-gray-800">{systemInfo.cpu.details?.nombre_coeurs || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Fréquence:</span>
                    <span className="text-gray-800">
                      {systemInfo.cpu.details?.frequence_mhz ?
                        `${Math.round(systemInfo.cpu.details.frequence_mhz)} MHz` : 'N/A'}
                    </span>
                  </div>
                  <div className="mt-2 text-xs">
                    <span className={`px-2 py-1 rounded-full ${
                      systemInfo.cpu.statut === 'ok' ? 'bg-green-100 text-green-800' :
                      systemInfo.cpu.statut === 'avertissement' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {systemInfo.cpu.message}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Informations Mémoire */}
            {systemInfo.memoire && (
              <div className="bg-white rounded-lg p-3 border border-blue-100">
                <div className="flex items-center mb-2">
                  <FaMemory className="text-blue-600 mr-2" />
                  <h5 className="font-medium text-gray-800">Mémoire RAM</h5>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Utilisée:</span>
                    <span className={`font-medium ${
                      systemInfo.memoire.details?.utilise_pourcentage > 80 ? 'text-red-600' :
                      systemInfo.memoire.details?.utilise_pourcentage > 60 ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {systemInfo.memoire.details?.utilise_pourcentage || 'N/A'}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total:</span>
                    <span className="text-gray-800">{systemInfo.memoire.details?.total_gb || 'N/A'} GB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Disponible:</span>
                    <span className="text-gray-800">{systemInfo.memoire.details?.disponible_gb || 'N/A'} GB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Libre:</span>
                    <span className="text-gray-800">{systemInfo.memoire.details?.libre_gb || 'N/A'} GB</span>
                  </div>
                  <div className="mt-2 text-xs">
                    <span className={`px-2 py-1 rounded-full ${
                      systemInfo.memoire.statut === 'ok' ? 'bg-green-100 text-green-800' :
                      systemInfo.memoire.statut === 'avertissement' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {systemInfo.memoire.message}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Informations Disque */}
            {systemInfo.disque && (
              <div className="bg-white rounded-lg p-3 border border-blue-100">
                <div className="flex items-center mb-2">
                  <FaHdd className="text-blue-600 mr-2" />
                  <h5 className="font-medium text-gray-800">Stockage</h5>
                </div>
                <div className="space-y-2 text-sm">
                  {systemInfo.disque.details?.disques?.map((disque, index) => (
                    <div key={index} className="border-b border-gray-100 pb-1 last:border-b-0">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600 font-medium">{disque.mountpoint}</span>
                        <span className={`text-xs px-1 py-0.5 rounded ${
                          disque.pourcentage > 90 ? 'bg-red-100 text-red-800' :
                          disque.pourcentage > 80 ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                        }`}>
                          {disque.pourcentage}%
                        </span>
                      </div>
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>{disque.utilise_gb} GB utilisé</span>
                        <span>{disque.libre_gb} GB libre</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                        <div
                          className={`h-1.5 rounded-full ${
                            disque.pourcentage > 90 ? 'bg-red-500' :
                            disque.pourcentage > 80 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${disque.pourcentage}%` }}
                        ></div>
                      </div>
                    </div>
                  )) || (
                    <div className="text-gray-500 text-center">Aucune information de disque disponible</div>
                  )}
                  <div className="mt-2 text-xs">
                    <span className={`px-2 py-1 rounded-full ${
                      systemInfo.disque.statut === 'ok' ? 'bg-green-100 text-green-800' :
                      systemInfo.disque.statut === 'avertissement' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {systemInfo.disque.message}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-4 text-blue-700">
            <FaInfoCircle className="mx-auto text-2xl mb-2" />
            <p>Les informations système seront affichées lors du diagnostic</p>
          </div>
        )}

        {/* Score de performance global */}
        {systemInfo?.performance && (
          <div className="mt-4 p-3 bg-white rounded-lg border border-blue-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <FaChartBar className="text-blue-600 mr-2" />
                <span className="font-medium text-gray-800">Score de performance global</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`text-2xl font-bold ${
                  systemInfo.performance.details?.score_performance >= 80 ? 'text-green-600' :
                  systemInfo.performance.details?.score_performance >= 60 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {systemInfo.performance.details?.score_performance || 'N/A'}
                </span>
                <span className="text-gray-500">/100</span>
              </div>
            </div>
            {systemInfo.performance.details?.uptime_hours && (
              <div className="mt-2 text-sm text-gray-600">
                <span>Temps de fonctionnement: {systemInfo.performance.details.uptime_hours}h</span>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // Fonction pour parser et rendre les recommandations de manière structurée
  const renderRecommandations = (recommandations) => {
    console.log('Recommandations reçues:', recommandations);
    console.log('Type des recommandations:', typeof recommandations);

    if (!recommandations) {
      console.log('Aucune recommandation fournie');
      return (
        <div className="text-gray-500 text-center p-4">
          <FaInfoCircle className="mx-auto text-2xl mb-2" />
          <p>Aucune recommandation disponible pour ce diagnostic.</p>
        </div>
      );
    }

    // Convertir en string si ce n'est pas déjà le cas
    const recommandationsStr = typeof recommandations === 'string' ? recommandations : String(recommandements);
    console.log('Recommandations converties en string:', recommandationsStr);

    if (recommandationsStr.trim().length === 0) {
      console.log('Recommandations vides après conversion');
      return (
        <div className="text-gray-500 text-center p-4">
          <FaInfoCircle className="mx-auto text-2xl mb-2" />
          <p>Aucune recommandation spécifique pour ce diagnostic.</p>
        </div>
      );
    }

    const lignes = recommandationsStr.split('\n').filter(ligne => ligne.trim());
    console.log('Lignes de recommandations parsées:', lignes);

    if (lignes.length === 0) {
      return (
        <div className="text-gray-500 text-center p-4">
          <FaInfoCircle className="mx-auto text-2xl mb-2" />
          <p>Diagnostic complété sans recommandations spécifiques.</p>
        </div>
      );
    }

    const sections = [];
    let sectionCourante = null;
    let applications = [];
    let dansApplications = false;

    lignes.forEach((ligne, index) => {
      ligne = ligne.trim();
      console.log(`Ligne ${index}:`, ligne);

      // Détecter le début d'une section d'applications
      if (ligne.includes('📊 Applications consommant le plus de ressources') ||
          ligne.includes('📊 Applications gourmandes détectées') ||
          ligne.includes('Applications consommant le plus de ressources') ||
          ligne.includes('Applications gourmandes détectées')) {
        console.log('Début section applications détectée');
        dansApplications = true;
        sectionCourante = {
          type: 'applications',
          titre: ligne,
          items: []
        };
        return;
      }

      // Détecter la fin d'une section d'applications
      if (dansApplications && ligne.startsWith('⚠️')) {
        console.log('Fin section applications détectée');
        dansApplications = false;
        if (sectionCourante) {
          sections.push(sectionCourante);
          sectionCourante = null;
        }
        sections.push({
          type: 'alerte',
          contenu: ligne
        });
        return;
      }

      // Parser les applications dans la section
      if (dansApplications) {
        if (ligne.match(/^\s*[🔴🟡]\s*\d+\./u) || ligne.match(/^\s*\d+\./)) {
          console.log('Nouvelle application détectée:', ligne);
          // Nouvelle application - pattern plus flexible
          const matches = ligne.match(/^\s*([🔴🟡]?)\s*(\d+)\.\s*(.+)/u) ||
                         ligne.match(/^\s*(\d+)\.\s*(.+)/);
          if (matches) {
            const app = {
              icone: matches[1] || '🔴',
              numero: matches[2] || matches[1],
              nom: matches[3] || matches[2],
              details: {},
              conseils: []
            };
            applications.push(app);
          }
        } else if (ligne.includes('CPU:') && ligne.includes('RAM:')) {
          console.log('Détails application détectés:', ligne);
          // Détails de l'application
          const matches = ligne.match(/CPU:\s*(\d+(?:\.\d+)?)%.*RAM:\s*(\d+(?:\.\d+)?)%.*\(([^)]+)\)/);
          if (matches && applications.length > 0) {
            const dernierApp = applications[applications.length - 1];
            dernierApp.details = {
              cpu: matches[1],
              ram: matches[2],
              memoire: matches[3]
            };
          }
        } else if (ligne.includes('→') || ligne.includes('➜')) {
          console.log('Conseil application détecté:', ligne);
          // Conseil pour l'application
          if (applications.length > 0) {
            const dernierApp = applications[applications.length - 1];
            dernierApp.conseils.push(ligne.replace(/^\s*[→➜]\s*/, ''));
          }
        }
      } else {
        // Autres recommandations normales - pattern plus large
        if (ligne.startsWith('•') || ligne.startsWith('→') || ligne.startsWith('✅') ||
            ligne.startsWith('🚨') || ligne.startsWith('⚠️') || ligne.startsWith('-') ||
            ligne.length > 5) { // Accepter les lignes plus longues même sans symbole
          console.log('Recommandation normale détectée:', ligne);
          sections.push({
            type: 'recommandation',
            contenu: ligne,
            niveau: ligne.startsWith('🚨') ? 'critique' :
                   ligne.startsWith('⚠️') ? 'avertissement' :
                   ligne.startsWith('✅') ? 'succes' : 'normal'
          });
        }
      }
    });

    // Ajouter la section d'applications si elle existe
    if (sectionCourante && applications.length > 0) {
      console.log('Ajout section applications avec', applications.length, 'applications');
      sectionCourante.applications = applications;
      sections.push(sectionCourante);
    }

    console.log('Sections finales:', sections);

    if (sections.length === 0) {
      // Si aucune section n'a été parsée, afficher le texte brut
      return (
        <div className="space-y-2">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-blue-900 whitespace-pre-wrap">{recommandationsStr}</div>
          </div>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {sections.map((section, index) => {
          if (section.type === 'applications') {
            return (
              <div key={index} className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
                <h6 className="font-medium text-blue-900 mb-3 flex items-center">
                  <FaChartBar className="mr-2" />
                  {section.titre}
                </h6>
                <div className="space-y-3">
                  {section.applications?.map((app, appIndex) => (
                    <div key={appIndex} className="bg-white rounded-lg p-3 border border-blue-100">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-lg">{app.icone}</span>
                          <span className="font-medium text-gray-800">
                            {app.numero}. {app.nom}
                          </span>
                        </div>
                        {app.details.cpu && (
                          <div className="flex items-center space-x-3 text-sm">
                            <span className={`px-2 py-1 rounded ${
                              parseFloat(app.details.cpu) > 50 ? 'bg-red-100 text-red-700' :
                              parseFloat(app.details.cpu) > 25 ? 'bg-yellow-100 text-yellow-700' :
                              'bg-green-100 text-green-700'
                            }`}>
                              CPU: {app.details.cpu}%
                            </span>
                            <span className={`px-2 py-1 rounded ${
                              parseFloat(app.details.ram) > 10 ? 'bg-red-100 text-red-700' :
                              parseFloat(app.details.ram) > 5 ? 'bg-yellow-100 text-yellow-700' :
                              'bg-green-100 text-green-700'
                            }`}>
                              RAM: {app.details.ram}%
                            </span>
                            <span className="text-gray-600 text-xs">
                              {app.details.memoire}
                            </span>
                          </div>
                        )}
                      </div>
                      {app.conseils.length > 0 && (
                        <div className="space-y-1">
                          {app.conseils.map((conseil, conseilIndex) => (
                            <div key={conseilIndex} className="flex items-start space-x-2 text-sm">
                              <span className="text-blue-500 mt-0.5">→</span>
                              <span className="text-blue-800">{conseil}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          } else if (section.type === 'alerte') {
            return (
              <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-center text-red-700">
                  <FaExclamationTriangle className="mr-2 flex-shrink-0" />
                  <span className="font-medium">{section.contenu}</span>
                </div>
              </div>
            );
          } else {
            return (
              <div key={index} className={`flex items-start space-x-2 p-2 rounded ${
                section.niveau === 'critique' ? 'bg-red-50 text-red-800' :
                section.niveau === 'avertissement' ? 'bg-yellow-50 text-yellow-800' :
                section.niveau === 'succes' ? 'bg-green-50 text-green-800' :
                'text-blue-800'
              }`}>
                <span className="mt-0.5 flex-shrink-0">
                  {section.niveau === 'critique' ? '🚨' :
                   section.niveau === 'avertissement' ? '⚠️' :
                   section.niveau === 'succes' ? '✅' : '•'}
                </span>
                <span>{section.contenu.replace(/^[•→✅🚨⚠️-]\s*/u, '')}</span>
              </div>
            );
          }
        })}
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 bg-white border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <FaRobot className="text-blue-600 text-xl" />
            <h2 className="text-xl font-bold text-gray-900">Diagnostic manuel</h2>
          </div>
          <div className="flex items-center space-x-2">
            {currentSession && !sessionComplete && (
              <>
                <button
                  onClick={pauseSession}
                  className="text-yellow-600 hover:text-yellow-800 p-2"
                  title="Mettre en pause"
                >
                  <FaPause />
                </button>
                <button
                  onClick={onClose}
                  className="text-red-600 hover:text-red-800 p-2"
                  title="Arrêter le diagnostic"
                >
                  <FaStop />
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <FaTimes className="text-xl" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Informations système détaillées - affiché en premier pour les diagnostics de performance */}
          {renderSystemInfo()}

          {/* Chargement initial */}
          {sessionLoading && (
            <div className="flex items-center justify-center py-12">
              <FaSpinner className="animate-spin text-4xl text-blue-500" />
              <span className="ml-3 text-lg">Démarrage du diagnostic...</span>
            </div>
          )}

          {/* Erreur */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center text-red-700">
                <FaExclamationTriangle className="mr-2" />
                <span className="font-medium">Erreur</span>
              </div>
              <p className="text-red-600 mt-2">{error}</p>
              <button
                onClick={startDiagnostic}
                className="mt-3 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
              >
                Réessayer
              </button>
            </div>
          )}

          {/* Question actuelle */}
          {currentQuestion && !sessionLoading && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-2">
                  {currentQuestion.titre}
                </h3>
                {currentQuestion.description && (
                  <p className="text-gray-600 mb-4">{currentQuestion.description}</p>
                )}
                {currentQuestion.est_critique && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                    <div className="flex items-center text-red-700">
                      <FaExclamationTriangle className="mr-2" />
                      <span className="text-sm font-medium">Question critique pour le diagnostic</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Choix de réponses */}
              {currentQuestion.choix_reponses && currentQuestion.choix_reponses.length > 0 && (
                <div className="space-y-3">
                  {currentQuestion.choix_reponses.map((choix) => (
                    <button
                      key={choix.id}
                      onClick={() => submitAnswer(currentQuestion.id, {
                        choix_selectionnes_ids: [choix.id]
                      })}
                      disabled={answering}
                      className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors disabled:opacity-50"
                    >
                      <div className="flex items-center justify-between">
                        <span>{choix.texte}</span>
                        {choix.score_criticite > 0 && (
                          <span className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded">
                            Score: {choix.score_criticite}
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {/* Zone de texte libre */}
              {currentQuestion.type_question === 'texte' && (
                <div className="space-y-3">
                  <textarea
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="4"
                    placeholder="Décrivez votre problème en détail..."
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.ctrlKey) {
                        submitAnswer(currentQuestion.id, {
                          reponse_texte: e.target.value
                        });
                      }
                    }}
                  />
                  <button
                    onClick={(e) => {
                      const textarea = e.target.parentNode.querySelector('textarea');
                      submitAnswer(currentQuestion.id, {
                        reponse_texte: textarea.value
                      });
                    }}
                    disabled={answering}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg disabled:opacity-50"
                  >
                    {answering ? <FaSpinner className="animate-spin" /> : 'Continuer'}
                  </button>
                  <p className="text-xs text-gray-500">Astuce: Ctrl+Entrée pour envoyer rapidement</p>
                </div>
              )}

              {answering && (
                <div className="flex items-center justify-center py-4">
                  <FaSpinner className="animate-spin text-blue-500 mr-2" />
                  <span className="text-gray-600">Traitement de votre réponse...</span>
                </div>
              )}
            </div>
          )}

          {/* Résultats finaux */}
          {sessionComplete && finalResults && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FaCheck className="text-green-600 text-2xl" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Diagnostic terminé !
                </h3>
                <p className="text-gray-600">
                  Votre diagnostic a été complété avec succès.
                </p>
              </div>

              {/* Résultats */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-medium text-gray-900 mb-4">Résultats du diagnostic :</h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="bg-white p-4 rounded-lg border">
                    <h5 className="font-medium text-gray-700">Priorité estimée</h5>
                    <span className={`text-lg font-bold ${
                      finalResults.priorite_estimee === 'critique' ? 'text-red-600' :
                      finalResults.priorite_estimee === 'urgent' ? 'text-orange-600' :
                      finalResults.priorite_estimee === 'normal' ? 'text-blue-600' : 'text-green-600'
                    }`}>
                      {finalResults.priorite_estimee}
                    </span>
                  </div>
                  <div className="bg-white p-4 rounded-lg border">
                    <h5 className="font-medium text-gray-700">Score de criticité</h5>
                    <span className="text-lg font-bold text-gray-700">
                      {finalResults.score_total}/100
                    </span>
                  </div>
                </div>

                {finalResults.recommandations && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h5 className="font-medium text-blue-900 mb-3 flex items-center">
                      <FaInfoCircle className="mr-2" />
                      Recommandations personnalisées :
                    </h5>
                    <div className="space-y-2">
                      {renderRecommandations(finalResults.recommandations)}
                    </div>
                  </div>
                )}
              </div>

              {/* Actions finales */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={createTicketFromDiagnostic}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Créer un ticket
                </button>
                <button
                  onClick={handleComplete}
                  className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors font-medium"
                >
                  Terminer
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer avec informations de session */}
        {currentSession && !sessionComplete && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>Session #{currentSession}</span>
              <div className="flex items-center space-x-4">
                <span className="flex items-center">
                  <FaClock className="mr-1" />
                  Diagnostic en cours...
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DiagnosticManuelModal;
