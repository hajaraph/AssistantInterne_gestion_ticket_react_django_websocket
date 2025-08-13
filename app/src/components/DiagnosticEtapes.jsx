import React, { useState, useEffect } from 'react';
import {
  FaPlay, FaPause, FaCheck, FaTimes, FaChevronRight, FaChevronLeft,
  FaCog, FaQuestionCircle, FaChartLine, FaTools, FaListUl,
  FaExclamationTriangle, FaCheckCircle, FaInfoCircle
} from 'react-icons/fa';
import apiService from '../services/api';

const DiagnosticEtapes = ({ isOpen, onClose, categoryId, onComplete }) => {
  const [session, setSession] = useState(null);
  const [currentStep, setCurrentStep] = useState(null);
  const [steps, setSteps] = useState([]);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [progress, setProgress] = useState({ current: 0, total: 0, percentage: 0 });
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState('');

  // États spécifiques aux étapes
  const [diagnosticResults, setDiagnosticResults] = useState(null);
  const [questionnaire, setQuestionnaire] = useState({ questions: [], answers: {} });
  const [analysisResults, setAnalysisResults] = useState(null);
  const [finalDecision, setFinalDecision] = useState('');

  useEffect(() => {
    if (isOpen && categoryId) {
      startDiagnostic();
    }
  }, [isOpen, categoryId]);

  const startDiagnostic = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await apiService.post('/diagnostic/etapes/start', {
        categorie: categoryId
      });

      setSession({ id: response.session_id });
      setSteps(response.plan_etapes || []);
      setCurrentStep(response.etape_actuelle);
      setProgress(response.progression || { current: 1, total: 0, percentage: 0 });

    } catch (error) {
      console.error('Erreur lors du démarrage du diagnostic:', error);
      setError('Impossible de démarrer le diagnostic. Veuillez réessayer.');
    } finally {
      setLoading(false);
    }
  };

  const executeCurrentStep = async (stepData = {}) => {
    if (!session || !currentStep) return;

    setExecuting(true);
    setError('');

    try {
      const response = await apiService.post(`/diagnostic/etapes/${session.id}/execute`, stepData);

      if (response.success) {
        // Mettre à jour les étapes complétées
        setCompletedSteps(prev => [...prev, response.etape_completee]);

        // Mettre à jour la progression
        setProgress(response.progression);

        // Passer à l'étape suivante ou terminer
        if (response.prochaine_etape) {
          setCurrentStep(response.prochaine_etape);
        } else {
          // Diagnostic terminé
          if (onComplete) {
            // Ajouter le session_id au résultat
            const resultat = {
              ...response.resultat,
              session_id: session.id
            };
            onComplete(resultat);
          }
        }

        // Traiter les résultats spécifiques à l'étape
        handleStepResults(response.etape_completee, response.resultat);

      } else {
        setError(response.error || 'Erreur lors de l\'exécution de l\'étape');
      }

    } catch (error) {
      console.error('Erreur lors de l\'exécution de l\'étape:', error);
      setError('Erreur lors de l\'exécution. Veuillez réessayer.');
    } finally {
      setExecuting(false);
    }
  };

  const handleStepResults = (completedStep, results) => {
    switch (completedStep.type) {
      case 'diagnostic_automatique':
        setDiagnosticResults(results.resultat_etape);
        break;
      case 'questionnaire_interactif':
      case 'questionnaire_simple':
        // Les réponses sont déjà sauvegardées
        break;
      case 'analyse_resultats':
        setAnalysisResults(results.resultat_etape);
        break;
      default:
        break;
    }
  };

  const renderStepIcon = (step) => {
    // Vérification de sécurité
    if (!step || !step.type) {
      return <FaInfoCircle className="text-lg" />;
    }

    switch (step.type) {
      case 'diagnostic_automatique':
        return <FaCog className="text-lg" />;
      case 'questionnaire_interactif':
      case 'questionnaire_simple':
        return <FaQuestionCircle className="text-lg" />;
      case 'analyse_resultats':
        return <FaChartLine className="text-lg" />;
      case 'actions_utilisateur':
        return <FaTools className="text-lg" />;
      case 'decision':
        return <FaListUl className="text-lg" />;
      default:
        return <FaInfoCircle className="text-lg" />;
    }
  };

  const renderProgressBar = () => (
    <div className="mb-6">
      <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
        <span>Progression</span>
        <span>{progress.current} / {progress.total}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress.percentage}%` }}
        ></div>
      </div>
    </div>
  );

  const renderStepsList = () => (
    <div className="mb-6">
      <h4 className="font-medium text-gray-900 mb-3">Étapes du diagnostic</h4>
      <div className="space-y-2">
        {steps.map((step, index) => {
          const isCompleted = completedSteps.some(cs => cs.id === step.id);
          const isCurrent = currentStep && currentStep.id === step.id;

          return (
            <div
              key={step.id}
              className={`flex items-center space-x-3 p-2 rounded-lg ${
                isCurrent ? 'bg-blue-50 border border-blue-200' :
                isCompleted ? 'bg-green-50' : 'bg-gray-50'
              }`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                isCompleted ? 'bg-green-500 text-white' :
                isCurrent ? 'bg-blue-500 text-white' :
                'bg-gray-300 text-gray-600'
              }`}>
                {isCompleted ? <FaCheck /> : index + 1}
              </div>
              <div className="flex-1">
                <h5 className={`font-medium ${isCurrent ? 'text-blue-900' : 'text-gray-900'}`}>
                  {step.titre}
                </h5>
                <p className={`text-sm ${isCurrent ? 'text-blue-700' : 'text-gray-600'}`}>
                  {step.description}
                </p>
              </div>
              {step.temps_estime > 0 && (
                <span className="text-xs text-gray-500">
                  ~{Math.ceil(step.temps_estime / 60)}min
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderCurrentStepContent = () => {
    if (!currentStep) {
      return (
        <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
          <div className="text-gray-500">
            <FaInfoCircle className="text-4xl mx-auto mb-4" />
            <p>Chargement de l'étape suivante...</p>
          </div>
        </div>
      );
    }

    switch (currentStep.type) {
      case 'diagnostic_automatique':
        return renderDiagnosticStep();
      case 'questionnaire_interactif':
      case 'questionnaire_simple':
        return renderQuestionnaireStep();
      case 'analyse_resultats':
        return renderAnalysisStep();
      case 'actions_utilisateur':
        return renderActionsStep();
      case 'decision':
        return renderDecisionStep();
      default:
        return renderGenericStep();
    }
  };

  const renderDiagnosticStep = () => (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <FaCog className="text-blue-600 text-2xl animate-spin" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {currentStep.titre}
        </h3>
        <p className="text-gray-600 mb-6">
          {currentStep.description}
        </p>

        {!executing ? (
          <button
            onClick={() => executeCurrentStep()}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            <FaPlay className="inline mr-2" />
            Lancer l'analyse
          </button>
        ) : (
          <div className="flex items-center justify-center space-x-2 text-blue-600">
            <FaCog className="animate-spin" />
            <span>Analyse en cours...</span>
          </div>
        )}
      </div>

      {diagnosticResults && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="font-medium text-gray-900 mb-3">Résultats de l'analyse :</h4>
          {renderDiagnosticResults(diagnosticResults)}
        </div>
      )}
    </div>
  );

  const renderDiagnosticResults = (results) => {
    if (!results || !results.resume) return null;

    const { resume } = results;

    return (
      <div className="space-y-3">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="text-2xl font-bold text-red-600">{resume.problemes_critiques}</div>
            <div className="text-sm text-red-700">Problèmes</div>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="text-2xl font-bold text-yellow-600">{resume.avertissements}</div>
            <div className="text-sm text-yellow-700">Avertissements</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="text-2xl font-bold text-green-600">{resume.tests_ok}</div>
            <div className="text-sm text-green-700">Tests OK</div>
          </div>
        </div>

        {resume.details_problemes && resume.details_problemes.length > 0 && (
          <div className="space-y-2">
            <h5 className="font-medium text-red-800">Problèmes détectés :</h5>
            {resume.details_problemes.map((probleme, index) => (
              <div key={index} className="flex items-center space-x-2 text-sm">
                <FaExclamationTriangle className="text-red-500 flex-shrink-0" />
                <span className="text-red-700">{probleme.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderQuestionnaireStep = () => {
    const questions = currentStep.parametres?.questions || [];

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {currentStep.titre}
        </h3>
        <p className="text-gray-600 mb-6">
          {currentStep.description}
        </p>

        <div className="space-y-6">
          {questions.map((question) => (
            <div key={question.id} className="border border-gray-200 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">
                {question.titre}
                {question.est_critique && (
                  <span className="ml-2 text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
                    Critique
                  </span>
                )}
              </h4>
              {question.description && (
                <p className="text-gray-600 text-sm mb-3">{question.description}</p>
              )}

              <div className="space-y-2">
                {question.choix.map((choix) => (
                  <label key={choix.id} className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type={question.type === 'choix_multiple' ? 'checkbox' : 'radio'}
                      name={`question_${question.id}`}
                      value={choix.id}
                      onChange={(e) => handleQuestionAnswer(question.id, choix.id, e.target.checked)}
                      className="form-checkbox text-blue-600"
                    />
                    <span className="text-gray-700">{choix.texte}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={() => executeCurrentStep({ reponses: questionnaire.answers })}
            disabled={executing || Object.keys(questionnaire.answers).length === 0}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            {executing ? 'Enregistrement...' : 'Continuer'}
          </button>
        </div>
      </div>
    );
  };

  const handleQuestionAnswer = (questionId, choixId, isSelected) => {
    setQuestionnaire(prev => {
      const newAnswers = { ...prev.answers };

      if (!newAnswers[questionId]) {
        newAnswers[questionId] = { choix_ids: [], texte: '' };
      }

      if (isSelected) {
        if (!newAnswers[questionId].choix_ids.includes(choixId)) {
          newAnswers[questionId].choix_ids.push(choixId);
        }
      } else {
        newAnswers[questionId].choix_ids = newAnswers[questionId].choix_ids.filter(id => id !== choixId);
      }

      return { ...prev, answers: newAnswers };
    });
  };

  const renderActionsStep = () => (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <FaTools className="text-orange-600 text-2xl" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {currentStep?.titre || 'Actions recommandées'}
        </h3>
        <p className="text-gray-600 mb-6">
          {currentStep?.description || 'Suivez les actions recommandées ci-dessous'}
        </p>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h4 className="font-medium text-blue-900 mb-3">Actions suggérées :</h4>
          <div className="space-y-2 text-left">
            <div className="flex items-center space-x-2">
              <input type="checkbox" className="form-checkbox text-blue-600" />
              <span className="text-blue-800">Redémarrer l'ordinateur</span>
            </div>
            <div className="flex items-center space-x-2">
              <input type="checkbox" className="form-checkbox text-blue-600" />
              <span className="text-blue-800">Vider le cache du navigateur</span>
            </div>
            <div className="flex items-center space-x-2">
              <input type="checkbox" className="form-checkbox text-blue-600" />
              <span className="text-blue-800">Vérifier les connexions réseau</span>
            </div>
          </div>
        </div>

        <button
          onClick={() => executeCurrentStep({ actions_effectuees: ['reboot', 'clear_cache', 'check_network'] })}
          disabled={executing}
          className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700 disabled:bg-gray-400 transition-colors"
        >
          {executing ? 'Enregistrement...' : 'J\'ai effectué ces actions'}
        </button>
      </div>
    </div>
  );

  const renderAnalysisStep = () => (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <FaChartLine className="text-green-600 text-2xl" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {currentStep?.titre || 'Analyse des résultats'}
        </h3>
        <p className="text-gray-600 mb-6">
          {currentStep?.description || 'Analyse en cours des informations collectées'}
        </p>

        {!executing && !analysisResults ? (
          <button
            onClick={() => executeCurrentStep()}
            className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium"
          >
            <FaChartLine className="inline mr-2" />
            Générer l'analyse
          </button>
        ) : executing ? (
          <div className="flex items-center justify-center space-x-2 text-green-600">
            <FaChartLine className="animate-pulse" />
            <span>Analyse en cours...</span>
          </div>
        ) : null}
      </div>

      {analysisResults && renderAnalysisResults(analysisResults)}
    </div>
  );

  const renderAnalysisResults = (results) => (
    <div className="mt-6 pt-6 border-t border-gray-200 text-left">
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900">Priorité estimée</h4>
          <span className={`text-lg font-bold ${
            results.priorite_estimee === 'critique' ? 'text-red-600' :
            results.priorite_estimee === 'urgent' ? 'text-orange-600' :
            results.priorite_estimee === 'normal' ? 'text-blue-600' : 'text-green-600'
          }`}>
            {results.priorite_estimee}
          </span>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900">Score de criticité</h4>
          <span className="text-lg font-bold text-gray-700">{results.score_total}/100</span>
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h4 className="font-medium text-yellow-900 mb-2">Recommandations :</h4>
        <div className="text-sm text-yellow-800 whitespace-pre-line">
          {results.recommandations}
        </div>
      </div>
    </div>
  );

  const renderDecisionStep = () => (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {currentStep.titre}
      </h3>
      <p className="text-gray-600 mb-6">
        {currentStep.description}
      </p>

      <div className="space-y-4">
        {[
          { id: 'probleme_resolu', label: 'Mon problème est résolu', description: 'Le diagnostic a permis de résoudre mon problème', color: 'green' },
          { id: 'creer_ticket_auto', label: 'Créer un ticket avec les infos du diagnostic', description: 'Créer automatiquement un ticket pré-rempli', color: 'blue' },
          { id: 'creer_ticket_manuel', label: 'Créer un ticket manuellement', description: 'Rédiger moi-même la description du problème', color: 'gray' },
          { id: 'contacter_support', label: 'Contacter le support directement', description: 'Pour les urgences ou problèmes complexes', color: 'red' }
        ].map((option) => (
          <label key={option.id} className="flex items-start space-x-3 p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="decision"
              value={option.id}
              checked={finalDecision === option.id}
              onChange={(e) => setFinalDecision(e.target.value)}
              className="mt-1 form-radio text-blue-600"
            />
            <div>
              <h4 className={`font-medium text-${option.color}-900`}>{option.label}</h4>
              <p className="text-sm text-gray-600">{option.description}</p>
            </div>
          </label>
        ))}
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={() => executeCurrentStep({ decision: finalDecision })}
          disabled={executing || !finalDecision}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
        >
          {executing ? 'Finalisation...' : 'Finaliser'}
        </button>
      </div>
    </div>
  );

  const renderGenericStep = () => (
    <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {currentStep.titre}
      </h3>
      <p className="text-gray-600 mb-6">
        {currentStep.description}
      </p>
      <button
        onClick={() => executeCurrentStep()}
        disabled={executing}
        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
      >
        {executing ? 'En cours...' : 'Continuer'}
      </button>
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden transform transition-all duration-300 ease-in-out">
        {/* Header */}
        <div className="flex items-center justify-between p-6 bg-white border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Diagnostic intelligent</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <FaTimes className="text-xl" />
          </button>
        </div>

        {/* Content */}
        <div className="flex h-[calc(90vh-140px)]">
          {/* Sidebar */}
          <div className="w-1/3 bg-white p-6 border-r border-gray-200 overflow-y-auto transition-all duration-300 ease-in-out">
            {renderProgressBar()}
            {renderStepsList()}
          </div>

          {/* Main content */}
          <div className="flex-1 p-6 overflow-y-auto bg-white">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center transform transition-all duration-500 ease-in-out">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Initialisation du diagnostic...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center transform transition-all duration-500 ease-in-out">
                  <FaTimes className="text-red-500 text-4xl mx-auto mb-4" />
                  <p className="text-red-600 font-medium mb-2">Erreur</p>
                  <p className="text-gray-600 mb-4">{error}</p>
                  <button
                    onClick={startDiagnostic}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-all duration-200 transform hover:scale-105"
                  >
                    Réessayer
                  </button>
                </div>
              </div>
            ) : (
              <div className="transition-all duration-500 ease-in-out transform">
                {renderCurrentStepContent()}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiagnosticEtapes;
