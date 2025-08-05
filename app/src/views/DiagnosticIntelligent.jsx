import React, { useState, useEffect, useCallback } from 'react';
import ContentCard from '../components/ContentCard';
import DiagnosticManuelModal from '../components/modals/DiagnosticManuelModal';
import {
  FaRobot, FaPlay, FaPause,
  FaClock, FaExclamationTriangle, FaInfoCircle,
  FaChartLine, FaUser, FaBuilding, FaSpinner, FaSync
} from 'react-icons/fa';
import { FaComputer, FaNetworkWired, FaShield, FaPrint } from 'react-icons/fa6';
import apiService from '../services/api';

const DiagnosticIntelligent = () => {
  // États pour les données d'accueil
  const [accueilData, setAccueilData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // États pour le diagnostic manuel
  const [isDiagnosticManuelOpen, setIsDiagnosticManuelOpen] = useState(false);
  const [selectedCategoryForManuel, setSelectedCategoryForManuel] = useState(null);

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

  // Démarrer un nouveau diagnostic manuel
  const startDiagnosticManuel = (categoryId) => {
    setSelectedCategoryForManuel(categoryId);
    setIsDiagnosticManuelOpen(true);
  };

  // Gérer la fin du diagnostic manuel
  const handleDiagnosticManuelComplete = async (results) => {
    console.log('Diagnostic manuel terminé:', results);

    // Recharger les données d'accueil pour mettre à jour les stats
    await loadAccueilData();

    // Afficher un message de succès
    if (results) {
      alert(`Diagnostic terminé!\nPriorité: ${results.priorite_estimee}\nScore: ${results.score_total}`);
    }
  };

  // Reprendre une session
  const resumeSession = async (sessionId) => {
    try {
      setLoading(true);
      await apiService.resumeDiagnosticSession(sessionId);
      // Après reprise, ouvrir le modal de diagnostic manuel
      setSelectedCategoryForManuel(null); // On laisse le modal déterminer la catégorie
      setIsDiagnosticManuelOpen(true);
    } catch (err) {
      console.error('Erreur lors de la reprise:', err);
      setError(err.message);
    } finally {
      setLoading(false);
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
                  disabled={loading}
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
                className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow hover:border-blue-300 cursor-pointer"
                onClick={() => startDiagnosticManuel(category.id)}
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

                {/* Bouton de lancement */}
                <div className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-3 rounded-lg flex items-center justify-center transition-all">
                  <FaRobot className="mr-2" />
                  Commencer le diagnostic
                </div>
              </div>
            );
          })}
        </div>

        {/* Message d'aide */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start space-x-3">
            <FaInfoCircle className="text-blue-500 mt-1 flex-shrink-0" />
            <div>
              <h4 className="font-medium text-blue-800 mb-2">Comment fonctionne le diagnostic ?</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <p>• <strong>Analyse automatique :</strong> Le système analysera automatiquement votre ordinateur</p>
                <p>• <strong>Questions ciblées :</strong> Répondez aux questions pour affiner le diagnostic</p>
                <p>• <strong>Recommandations :</strong> Obtenez des solutions personnalisées à votre problème</p>
                <p>• <strong>Création de ticket :</strong> Un ticket peut être créé automatiquement si nécessaire</p>
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

      {/* Modal de diagnostic manuel */}
      <DiagnosticManuelModal
        isOpen={isDiagnosticManuelOpen}
        onClose={() => setIsDiagnosticManuelOpen(false)}
        categoryId={selectedCategoryForManuel}
        onComplete={handleDiagnosticManuelComplete}
      />
    </div>
  );
};

export default DiagnosticIntelligent;
