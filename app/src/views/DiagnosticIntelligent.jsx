import React, { useState, useEffect, useCallback } from 'react';
import ContentCard from '../components/ContentCard';
import {
  FaRobot, FaPlay, FaPause, FaStop,
  FaClock, FaExclamationTriangle, FaInfoCircle,
  FaChartLine, FaUser, FaBuilding, FaSpinner, FaSync
} from 'react-icons/fa';
import { FaComputer, FaNetworkWired, FaShield, FaPrint } from 'react-icons/fa6';
import apiService from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const DiagnosticIntelligent = () => {
  // États pour les données d'accueil
  const [accueilData, setAccueilData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // États pour le diagnostic en cours
  const [currentSession, setCurrentSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [currentEtape, setCurrentEtape] = useState(null);
  const [planEtapes, setPlanEtapes] = useState(null);
  const [progression, setProgression] = useState(null);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [answering, setAnswering] = useState(false);

  // États pour l'interface
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  const { user } = useAuth();

  // Chargement des données d'accueil
  const loadAccueilData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await apiService.getDiagnosticAccueil();
      setAccueilData(data);
    } catch (err) {
      console.error('Erreur lors du chargement des données d\'accueil:', err);
      setError(err.message || 'Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAccueilData();
  }, [loadAccueilData]);

  // Icônes pour les catégories
  const getCategoryIcon = (iconType) => {
    const iconMap = {
      hardware: FaComputer,
      network: FaNetworkWired,
      software: FaComputer,
      security: FaShield,
      email: FaInfoCircle,
      printer: FaPrint,
      performance: FaChartLine,
      system: FaComputer,
      general: FaInfoCircle
    };
    return iconMap[iconType] || FaInfoCircle;
  };

  // Démarrer un nouveau diagnostic
  const startDiagnostic = async (categoryId) => {
    try {
      setSessionLoading(true);
      setError(null);

      const sessionData = { categorie: categoryId };
      const response = await apiService.createDiagnosticSession(sessionData);

      setCurrentSession(response.session_id);
      setSelectedCategory(categoryId);

      // Charger la première question
      await loadNextQuestion(response.session_id);
    } catch (err) {
      console.error('Erreur lors du démarrage du diagnostic:', err);
      setError(err.message);
    } finally {
      setSessionLoading(false);
    }
  };

  // Démarrer un nouveau diagnostic avec le système d'étapes
  const startDiagnosticEtapes = async (categoryId, equipmentId = null, templateId = null) => {
    try {
      setSessionLoading(true);
      setError(null);

      const sessionData = {
        categorie: categoryId,
        equipement: equipmentId,
        template: templateId
      };

      const response = await apiService.startDiagnosticEtapes(sessionData);

      setCurrentSession(response.session_id);
      setSelectedCategory(categoryId);
      setCurrentEtape(response.etape_actuelle);
      setPlanEtapes(response.plan_etapes);
      setProgression(response.progression);

    } catch (err) {
      console.error('Erreur lors du démarrage du diagnostic par étapes:', err);
      setError(err.message);
    } finally {
      setSessionLoading(false);
    }
  };

  // Charger la prochaine question
  const loadNextQuestion = async (sessionId) => {
    try {
      const response = await apiService.getNextQuestion(sessionId);

      if (response.session_complete) {
        // Diagnostic terminé
        setCurrentQuestion(null);
        setCurrentSession(null);
        setSelectedCategory(null);

        // Recharger les données d'accueil pour mettre à jour les stats
        await loadAccueilData();

        // Afficher les résultats
        alert(`Diagnostic terminé!\nPriorité estimée: ${response.priorite_estimee}\nScore: ${response.score_total}`);
      } else {
        setCurrentQuestion(response);
      }
    } catch (err) {
      console.error('Erreur lors du chargement de la question:', err);
      setError(err.message);
    }
  };

  // Répondre à une question
  const submitAnswer = async (questionId, answerData) => {
    try {
      setAnswering(true);

      const response = await apiService.submitDiagnosticAnswer(currentSession, {
        question: questionId,
        ...answerData
      });

      // Charger la question suivante
      await loadNextQuestion(currentSession);
    } catch (err) {
      console.error('Erreur lors de l\'envoi de la réponse:', err);
      setError(err.message);
    } finally {
      setAnswering(false);
    }
  };

  // Exécuter l'étape actuelle
  const executerEtapeActuelle = async (donneesEtape) => {
    try {
      setAnswering(true);

      const response = await apiService.executerEtape(currentSession, donneesEtape);

      if (response.success) {
        setCurrentEtape(response.prochaine_etape);
        setProgression(response.progression);

        if (response.diagnostic_termine) {
          // Diagnostic terminé
          setCurrentSession(null);
          setCurrentEtape(null);
          setSelectedCategory(null);

          // Recharger les données d'accueil
          await loadAccueilData();

          alert(`Diagnostic terminé!\nRésultats disponibles dans l'historique.`);
        }
      } else {
        setError(response.error);
      }
    } catch (err) {
      console.error('Erreur lors de l\'exécution de l\'étape:', err);
      setError(err.message);
    } finally {
      setAnswering(false);
    }
  };

  // Naviguer entre les étapes
  const naviguerEtape = async (direction) => {
    try {
      const response = await apiService.naviguerEtape(currentSession, direction);
      setCurrentEtape(response.etape_actuelle);
      setProgression(response.progression);
    } catch (err) {
      console.error('Erreur lors de la navigation:', err);
      setError(err.message);
    }
  };

  // Mettre en pause la session
  const pauseSession = async () => {
    try {
      await apiService.pauseDiagnosticSession(currentSession, 'Pause utilisateur');
      setCurrentSession(null);
      setCurrentQuestion(null);
      setSelectedCategory(null);
      await loadAccueilData();
    } catch (err) {
      console.error('Erreur lors de la mise en pause:', err);
      setError(err.message);
    }
  };

  // Reprendre une session
  const resumeSession = async (sessionId) => {
    try {
      setSessionLoading(true);
      await apiService.resumeDiagnosticSession(sessionId);
      setCurrentSession(sessionId);
      await loadNextQuestion(sessionId);
    } catch (err) {
      console.error('Erreur lors de la reprise:', err);
      setError(err.message);
    } finally {
      setSessionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <FaSpinner className="animate-spin text-4xl text-blue-500" />
        <span className="ml-3 text-lg">Chargement du diagnostic intelligent...</span>
      </div>
    );
  }

  if (error) {
    return (
      <ContentCard title="Erreur" icon={FaExclamationTriangle}>
        <div className="text-center py-8">
          <FaExclamationTriangle className="mx-auto text-red-500 text-4xl mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadAccueilData}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center mx-auto"
          >
            <FaSync className="mr-2" />
            Réessayer
          </button>
        </div>
      </ContentCard>
    );
  }

  // Vue principale - sélection de catégorie
  if (!currentSession) {
    return (
      <div className="space-y-6">
        {/* En-tête de bienvenue */}
        <ContentCard title="Diagnostic Intelligent" icon={FaRobot}>
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <FaUser className="text-blue-600 text-2xl" />
                </div>
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-800 mb-2">
                  Bienvenue, {accueilData?.utilisateur?.nom_complet}
                </h2>
                <div className="text-gray-600 space-y-1">
                  <div className="flex items-center">
                    <FaBuilding className="mr-2 text-gray-400" />
                    <span>{accueilData?.utilisateur?.departement}</span>
                  </div>
                  <div className="flex items-center">
                    <FaInfoCircle className="mr-2 text-gray-400" />
                    <span>{accueilData?.utilisateur?.role}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </ContentCard>

        {/* Statistiques personnelles */}
        {accueilData?.statistiques_personnelles && (
          <ContentCard title="Vos statistiques" icon={FaChartLine}>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {accueilData.statistiques_personnelles.total_sessions}
                </div>
                <div className="text-sm text-gray-600">Sessions totales</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600">
                  {accueilData.statistiques_personnelles.sessions_completes}
                </div>
                <div className="text-sm text-gray-600">Complétées</div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {accueilData.statistiques_personnelles.sessions_cette_semaine}
                </div>
                <div className="text-sm text-gray-600">Cette semaine</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {Math.round((accueilData.statistiques_personnelles.temps_moyen_session || 0) / 60)}
                </div>
                <div className="text-sm text-gray-600">Minutes moy.</div>
              </div>
            </div>
          </ContentCard>
        )}

        {/* Sessions en cours */}
        {accueilData?.sessions_en_cours?.length > 0 && (
          <ContentCard title="Sessions en cours" icon={FaPause}>
            <div className="space-y-3">
              {accueilData.sessions_en_cours.map((session) => (
                <div key={session.id} className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="flex items-center space-x-3">
                    <FaPause className="text-yellow-500" />
                    <div>
                      <div className="font-medium">{session.categorie__nom_categorie}</div>
                      <div className="text-sm text-gray-500">
                        {session.statut === 'en_pause' ? 'En pause' : 'En cours'} -
                        Score: {session.score_criticite_total}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => resumeSession(session.id)}
                    className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg flex items-center"
                    disabled={sessionLoading}
                  >
                    <FaPlay className="mr-2" />
                    Reprendre
                  </button>
                </div>
              ))}
            </div>
          </ContentCard>
        )}

        {/* Catégories disponibles */}
        <ContentCard title="Choisir une catégorie de diagnostic" icon={FaRobot}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {accueilData?.categories_disponibles?.map((category) => {
              const IconComponent = getCategoryIcon(category.icone);
              return (
                <div
                  key={category.id}
                  className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow hover:border-blue-300"
                >
                  <div className="flex items-center space-x-3 mb-3">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: category.couleur_affichage + '20' }}
                    >
                      <IconComponent
                        className="text-xl"
                        style={{ color: category.couleur_affichage }}
                      />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-800">{category.nom_categorie}</h3>
                      <p className="text-sm text-gray-500">{category.nombre_questions} questions</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-4">{category.description_categorie}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                    <span className="flex items-center">
                      <FaClock className="mr-1" />
                      ~{category.temps_estime_minutes} min
                    </span>
                    <span className="text-gray-400">
                      {category.nombre_questions} questions
                    </span>
                  </div>

                  {/* Boutons de lancement */}
                  <div className="space-y-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startDiagnosticEtapes(category.id);
                      }}
                      disabled={sessionLoading}
                      className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-2 rounded-lg flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {sessionLoading ? (
                        <FaSpinner className="animate-spin mr-2" />
                      ) : (
                        <FaRobot className="mr-2" />
                      )}
                      {sessionLoading ? 'Démarrage...' : 'Diagnostic par étapes'}
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startDiagnostic(category.id);
                      }}
                      disabled={sessionLoading}
                      className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
                    >
                      <FaPlay className="mr-2 text-xs" />
                      Diagnostic classique
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Message d'aide pour les types de diagnostic */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-start space-x-3">
              <FaInfoCircle className="text-blue-500 mt-1 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Deux modes de diagnostic disponibles :</h4>
                <div className="text-sm text-blue-700 space-y-1">
                  <p><strong>Diagnostic par étapes :</strong> Système guidé avec analyse automatique du système, questions adaptatives et recommandations personnalisées.</p>
                  <p><strong>Diagnostic classique :</strong> Questions directes basées sur la catégorie sélectionnée.</p>
                </div>
              </div>
            </div>
          </div>
        </ContentCard>

        {/* Recommandations */}
        {accueilData?.recommandations?.length > 0 && (
          <ContentCard title="Recommandations personnalisées" icon={FaInfoCircle}>
            <div className="space-y-3">
              {accueilData.recommandations.map((rec, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                  <FaInfoCircle className="text-blue-500 mt-1 flex-shrink-0" />
                  <p className="text-sm text-gray-700">{rec}</p>
                </div>
              ))}
            </div>
          </ContentCard>
        )}

        {/* Guide d'utilisation */}
        <ContentCard title="Comment ça marche ?" icon={FaInfoCircle}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-800 mb-3">Étapes du diagnostic :</h4>
              <ol className="space-y-2 text-sm text-gray-600">
                {accueilData?.aide?.comment_ca_marche?.map((etape, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center flex-shrink-0 mt-0.5">
                      {index + 1}
                    </span>
                    <span>{etape}</span>
                  </li>
                ))}
              </ol>
            </div>
            <div className="space-y-3">
              <div className="flex items-center text-sm text-gray-600">
                <FaClock className="mr-2 text-blue-500" />
                <span>Temps estimé : {accueilData?.aide?.temps_estime_global}</span>
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <FaInfoCircle className="mr-2 text-blue-500" />
                <span>{accueilData?.aide?.support_contact}</span>
              </div>
            </div>
          </div>
        </ContentCard>
      </div>
    );
  }

  // Vue du diagnostic en cours
  return (
    <div className="space-y-6">
      {/* En-tête de la session en cours */}
      <ContentCard title="Diagnostic en cours" icon={FaRobot}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <FaRobot className="text-blue-600 text-xl" />
            </div>
            <div>
              <h3 className="font-medium text-gray-800">Session de diagnostic</h3>
              <p className="text-sm text-gray-600">Session #{currentSession}</p>
            </div>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={pauseSession}
              className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg flex items-center"
            >
              <FaPause className="mr-2" />
              Pause
            </button>
            <button
              onClick={() => {
                setCurrentSession(null);
                setCurrentQuestion(null);
                setSelectedCategory(null);
              }}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg flex items-center"
            >
              <FaStop className="mr-2" />
              Arrêter
            </button>
          </div>
        </div>
      </ContentCard>

      {/* Question actuelle */}
      {currentQuestion && (
        <ContentCard title={`Question ${currentQuestion.ordre || ''}`} icon={FaInfoCircle}>
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
              </div>
            )}

            {answering && (
              <div className="flex items-center justify-center py-4">
                <FaSpinner className="animate-spin text-blue-500 mr-2" />
                <span className="text-gray-600">Traitement de votre réponse...</span>
              </div>
            )}
          </div>
        </ContentCard>
      )}

      {/* Étapes du diagnostic */}
      {currentEtape && (
        <ContentCard title={`Étape ${currentEtape.ordre}`} icon={FaInfoCircle}>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-2">
                {currentEtape.titre}
              </h3>
              {currentEtape.description && (
                <p className="text-gray-600 mb-4">{currentEtape.description}</p>
              )}
            </div>

            {/* Zone de réponse selon le type d'étape */}
            <div>
              {currentEtape.type_etape === 'question' && currentEtape.question && (
                <div className="space-y-3">
                  <p className="text-gray-700">{currentEtape.question.texte}</p>
                  {currentEtape.question.choix_reponses && currentEtape.question.choix_reponses.length > 0 && (
                    <div className="space-y-3">
                      {currentEtape.question.choix_reponses.map((choix) => (
                        <button
                          key={choix.id}
                          onClick={() => executerEtapeActuelle({
                            reponse_question_id: choix.id
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
                </div>
              )}

              {currentEtape.type_etape === 'texte' && (
                <div className="space-y-3">
                  <textarea
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="4"
                    placeholder="Décrivez votre réponse..."
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.ctrlKey) {
                        executerEtapeActuelle({
                          reponse_texte: e.target.value
                        });
                      }
                    }}
                  />
                  <button
                    onClick={(e) => {
                      const textarea = e.target.parentNode.querySelector('textarea');
                      executerEtapeActuelle({
                        reponse_texte: textarea.value
                      });
                    }}
                    disabled={answering}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg disabled:opacity-50"
                  >
                    {answering ? <FaSpinner className="animate-spin" /> : 'Continuer'}
                  </button>
                </div>
              )}
            </div>

            {/* Navigation entre les étapes */}
            <div className="flex justify-between text-sm text-gray-600">
              <button
                onClick={() => naviguerEtape('precedente')}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg flex items-center"
                disabled={answering}
              >
                <FaClock className="mr-2" />
                Étape précédente
              </button>
              <button
                onClick={() => naviguerEtape('suivante')}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg flex items-center"
                disabled={answering}
              >
                Étape suivante
                <FaClock className="ml-2" />
              </button>
            </div>
          </div>
        </ContentCard>
      )}
    </div>
  );
};

export default DiagnosticIntelligent;
