import React, { useState, useEffect } from 'react';
import { FaRobot, FaTicketAlt, FaQuestionCircle, FaTimes, FaChartLine, FaCog } from 'react-icons/fa';
import apiService from '../../services/api';

const DiagnosticOrTicketModal = ({ isOpen, onClose, onCreateTicket, onStartDiagnostic }) => {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('choice'); // 'choice', 'category_selection', 'diagnostic_preview'
  const [diagnosticInfo, setDiagnosticInfo] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadCategories();
      setStep('choice');
      setSelectedCategory('');
      setDiagnosticInfo(null);
    }
  }, [isOpen]);

  const loadCategories = async () => {
    setLoading(true);
    try {
      const categoriesData = await apiService.getCategories();
      setCategories(categoriesData);
    } catch (error) {
      console.error('Erreur lors du chargement des catégories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategorySelect = async (categoryId) => {
    setSelectedCategory(categoryId);
    setLoading(true);

    try {
      // Obtenir des informations sur le diagnostic pour cette catégorie
      const category = categories.find(c => c.id === categoryId);

      // Simuler une estimation du temps et du contenu du diagnostic
      const estimatedInfo = {
        category: category,
        estimatedTime: Math.floor(Math.random() * 5) + 3, // 3-8 minutes
        steps: [
          'Analyse automatique du système',
          'Questions spécialisées',
          'Génération de recommandations',
          'Actions correctives suggérées'
        ],
        benefits: [
          'Résolution automatique possible',
          'Informations détaillées pour le technicien',
          'Priorité du ticket optimisée',
          'Gain de temps pour tous'
        ]
      };

      setDiagnosticInfo(estimatedInfo);
      setStep('diagnostic_preview');
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartDiagnostic = () => {
    if (onStartDiagnostic && selectedCategory) {
      onStartDiagnostic(selectedCategory);
      onClose();
    }
  };

  const handleDirectTicket = () => {
    if (onCreateTicket) {
      onCreateTicket();
    }
    onClose();
  };

  const renderChoiceStep = () => (
    <div className="p-6">
      <div className="text-center mb-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Comment souhaitez-vous procéder ?
        </h3>
        <p className="text-gray-600">
          Nous recommandons de commencer par un diagnostic automatique pour une résolution plus rapide.
        </p>
      </div>

      <div className="space-y-4">
        {/* Option Diagnostic Intelligent */}
        <div
          onClick={() => setStep('category_selection')}
          className="border-2 border-blue-200 rounded-lg p-4 cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 group"
        >
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                <FaRobot className="text-blue-600 text-xl" />
              </div>
            </div>
            <div className="flex-1">
              <h4 className="text-lg font-medium text-gray-900 mb-1">
                Diagnostic intelligent <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded-full ml-2">Recommandé</span>
              </h4>
              <p className="text-gray-600 text-sm mb-2">
                Analyse automatique de votre système + questionnaire adaptatif
              </p>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span className="flex items-center">
                  <FaCog className="mr-1" /> 3-8 minutes
                </span>
                <span className="flex items-center">
                  <FaChartLine className="mr-1" /> Résolution possible sans ticket
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Option Ticket Direct */}
        <div
          onClick={handleDirectTicket}
          className="border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-gray-400 hover:bg-gray-50 transition-all duration-200 group"
        >
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                <FaTicketAlt className="text-gray-600 text-xl" />
              </div>
            </div>
            <div className="flex-1">
              <h4 className="text-lg font-medium text-gray-900 mb-1">
                Créer un ticket directement
              </h4>
              <p className="text-gray-600 text-sm mb-2">
                Passer directement à la création d'un ticket de support
              </p>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>Traitement par un technicien</span>
                <span>•</span>
                <span>Délai de réponse selon priorité</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <div className="flex items-start space-x-2">
          <FaQuestionCircle className="text-amber-600 mt-1 flex-shrink-0" />
          <div className="text-sm">
            <p className="text-amber-800 font-medium mb-1">Pourquoi choisir le diagnostic ?</p>
            <p className="text-amber-700">
              Le diagnostic intelligent peut résoudre immédiatement certains problèmes et fournit des informations précieuses qui accélèrent le traitement si un ticket est nécessaire.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderCategorySelection = () => (
    <div className="p-6">
      <div className="mb-6">
        <button
          onClick={() => setStep('choice')}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium mb-4"
        >
          ← Retour aux options
        </button>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Sélectionnez la catégorie de votre problème
        </h3>
        <p className="text-gray-600">
          Choisissez la catégorie qui correspond le mieux à votre problème pour un diagnostic optimal.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {categories.map((category) => (
            <div
              key={category.id}
              onClick={() => handleCategorySelect(category.id)}
              className="border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-all duration-200"
            >
              <div className="flex items-center space-x-3">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: category.couleur_affichage || '#4F46E5' }}
                ></div>
                <div>
                  <h4 className="font-medium text-gray-900">{category.nom_categorie}</h4>
                  {category.description_categorie && (
                    <p className="text-sm text-gray-600 mt-1">{category.description_categorie}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderDiagnosticPreview = () => (
    <div className="p-6">
      <div className="mb-6">
        <button
          onClick={() => setStep('category_selection')}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium mb-4"
        >
          ← Changer de catégorie
        </button>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Diagnostic - {diagnosticInfo?.category?.nom_categorie}
        </h3>
        <p className="text-gray-600">
          Aperçu du processus de diagnostic pour votre problème.
        </p>
      </div>

      {diagnosticInfo && (
        <div className="space-y-6">
          {/* Estimation de temps */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <FaCog className="text-blue-600" />
              <div>
                <h4 className="font-medium text-blue-900">Temps estimé</h4>
                <p className="text-blue-700 text-sm">Environ {diagnosticInfo.estimatedTime} minutes</p>
              </div>
            </div>
          </div>

          {/* Étapes du diagnostic */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Étapes du diagnostic :</h4>
            <div className="space-y-2">
              {diagnosticInfo.steps.map((step, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  <span className="text-gray-700">{step}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Avantages */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Avantages :</h4>
            <div className="space-y-2">
              {diagnosticInfo.benefits.map((benefit, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-gray-700 text-sm">{benefit}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex space-x-3 pt-4">
            <button
              onClick={handleStartDiagnostic}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Commencer le diagnostic
            </button>
            <button
              onClick={handleDirectTicket}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Créer un ticket
            </button>
          </div>
        </div>
      )}
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">
            {step === 'choice' && 'Nouveau problème'}
            {step === 'category_selection' && 'Diagnostic intelligent'}
            {step === 'diagnostic_preview' && 'Aperçu du diagnostic'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <FaTimes className="text-xl" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-140px)]">
          {step === 'choice' && renderChoiceStep()}
          {step === 'category_selection' && renderCategorySelection()}
          {step === 'diagnostic_preview' && renderDiagnosticPreview()}
        </div>

        {/* Footer */}
        {step === 'choice' && (
          <div className="p-6 border-t border-gray-200 bg-gray-50">
            <div className="text-center text-sm text-gray-600">
              Vous pouvez toujours créer un ticket manuellement après le diagnostic si nécessaire.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DiagnosticOrTicketModal;
