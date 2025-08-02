import React, {useEffect, useRef, useState} from 'react';
import {FaExclamationCircle, FaTimes} from 'react-icons/fa';
import PriorityBadge from '../badges/PriorityBadge';
import apiService from '../../services/api';

const NewTicketModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    titre: '',
    categorie: '',
    priorite: 'normal',
    description: '',
    equipement: ''
  });
  
  const [categories, setCategories] = useState([]);
  const [equipements, setEquipements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [isTouched, setIsTouched] = useState({
    titre: false,
    description: false
  });
  
  const titleInputRef = useRef(null);
  
  // Charger les données de référence au montage du composant
  useEffect(() => {
    if (isOpen) {
      loadReferenceData();
      if (titleInputRef.current) {
        titleInputRef.current.focus();
      }
    }
  }, [isOpen]);

  const loadReferenceData = async () => {
    setLoading(true);
    try {
      const [categoriesData, equipementsData] = await Promise.all([
        apiService.getCategories(),
        apiService.getEquipments()
      ]);

      setCategories(categoriesData);
      setEquipements(equipementsData);

      // Sélectionner la première catégorie par défaut
      if (categoriesData.length > 0) {
        setFormData(prev => ({
          ...prev,
          categorie: categoriesData[0].id
        }));
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error);
      setErrors({ form: 'Erreur lors du chargement des données de référence' });
    } finally {
      setLoading(false);
    }
  };

  // Validation des champs
  const validateField = (name, value) => {
    switch (name) {
      case 'titre':
        if (!value.trim()) return 'Le titre est obligatoire';
        if (value.trim().length < 5) return 'Le titre doit contenir au moins 5 caractères';
        if (value.length > 255) return 'Le titre ne doit pas dépasser 255 caractères';
        return '';
      case 'description':
        if (!value.trim()) return 'La description est obligatoire';
        if (value.trim().length < 10) return 'La description doit contenir au moins 10 caractères';
        return '';
      case 'categorie':
        if (!value) return 'Veuillez sélectionner une catégorie';
        return '';
      default:
        return '';
    }
  };
  
  const validateForm = () => {
    const newErrors = {};
    let isValid = true;
    
    // Valider les champs obligatoires
    ['titre', 'description', 'categorie'].forEach(field => {
      const error = validateField(field, formData[field]);
      if (error) {
        newErrors[field] = error;
        isValid = false;
      }
    });
    
    setErrors(newErrors);
    return isValid;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Validation en temps réel après la première interaction
    if (isTouched[name]) {
      const error = validateField(name, value);
      setErrors(prev => ({
        ...prev,
        [name]: error || null
      }));
    }
  };
  
  const handleBlur = (e) => {
    const { name, value } = e.target;
    setIsTouched(prev => ({
      ...prev,
      [name]: true
    }));
    
    // Validation au blur
    const error = validateField(name, value);
    setErrors(prev => ({
      ...prev,
      [name]: error || null
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Marquer tous les champs comme touchés pour afficher les erreurs
    const newTouched = {};
    Object.keys(formData).forEach(key => {
      newTouched[key] = true;
    });
    setIsTouched(newTouched);
    
    // Valider le formulaire
    if (!validateForm()) {
      // Faire défiler jusqu'au premier champ en erreur
      const firstErrorField = Object.keys(errors).find(field => errors[field]);
      if (firstErrorField) {
        const element = document.getElementById(firstErrorField);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          element.focus({ preventScroll: true });
        }
      }
      return;
    }
    
    setSubmitLoading(true);
    try {
      // Préparer les données pour l'API
      const ticketData = {
        titre: formData.titre.trim(),
        description: formData.description.trim(),
        priorite: formData.priorite,
        categorie: parseInt(formData.categorie),
        ...(formData.equipement && { equipement: parseInt(formData.equipement) })
      };

      const newTicket = await apiService.createTicket(ticketData);

      // Informer le parent du succès
      if (onSubmit) {
        onSubmit(newTicket);
      }

      // Réinitialiser le formulaire
      resetForm();
      onClose();

    } catch (error) {
      console.error('Erreur lors de la création du ticket:', error);
      setErrors({
        form: error.message || 'Erreur lors de la création du ticket'
      });
    } finally {
      setSubmitLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      titre: '',
      categorie: categories.length > 0 ? categories[0].id : '',
      priorite: 'normal',
      description: '',
      equipement: ''
    });
    setErrors({});
    setIsTouched({
      titre: false,
      description: false
    });
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  // Fonction pour obtenir les classes CSS d'un champ en fonction de son état
  const getFieldClasses = (fieldName, hasIcon = false) => {
    const baseClasses = "block w-full pl-3 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[var(--primary-color)] focus:border-[var(--primary-light)] sm:text-sm transition-colors";
    const errorClasses = "border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500";
    
    if (errors[fieldName] && isTouched[fieldName]) {
      return `${baseClasses} ${errorClasses} ${hasIcon ? 'pl-10' : ''}`;
    }
    return `${baseClasses} ${hasIcon ? 'pl-10' : ''}`;
  };

  // Mapping des priorités pour l'affichage
  const priorityDisplayMap = {
    'faible': 'Basse',
    'normal': 'Normale',
    'urgent': 'Haute',
    'critique': 'Critique'
  };

  return (
    <div 
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      onClick={handleClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-gray-200"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-between items-center p-4 border-b border-gray-100">
          <h3 className="text-xl font-semibold text-gray-800">Nouveau ticket d'assistance</h3>
          <button 
            onClick={handleClose}
            className="text-gray-500 hover:text-gray-700 cursor-pointer"
            aria-label="Fermer la fenêtre"
          >
            <FaTimes className="h-5 w-5" />
          </button>
        </div>
        
        {/* Message d'erreur global */}
        {errors.form && (
          <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{errors.form}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Champ Titre */}
          <div>
            <label htmlFor="titre" className="block text-sm font-medium text-gray-700 mb-1">
              Titre du ticket
              <span className="text-red-500 ml-1">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                id="titre"
                name="titre"
                ref={titleInputRef}
                value={formData.titre}
                onChange={handleChange}
                onBlur={handleBlur}
                className={getFieldClasses('titre')}
                placeholder="Décrivez brièvement votre problème"
                aria-invalid={!!(errors.titre && isTouched.titre)}
                aria-describedby={errors.titre && isTouched.titre ? 'titre-error' : undefined}
                disabled={loading || submitLoading}
              />
              {errors.titre && isTouched.titre && (
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                  <FaExclamationCircle className="h-5 w-5 text-red-500" />
                </div>
              )}
            </div>
            {errors.titre && isTouched.titre ? (
              <p className="mt-1 text-sm text-red-600" id="titre-error">
                {errors.titre}
              </p>
            ) : (
              <p className="mt-1 text-xs text-gray-500">
                {formData.titre.length}/255 caractères
              </p>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Champ Catégorie */}
            <div>
              <label htmlFor="categorie" className="block text-sm font-medium text-gray-700 mb-1">
                Catégorie
                <span className="text-red-500 ml-1">*</span>
              </label>
              <div className="relative">
                <select
                  id="categorie"
                  name="categorie"
                  value={formData.categorie}
                  onChange={handleChange}
                  className={getFieldClasses('categorie')}
                  disabled={loading || submitLoading}
                >
                  <option value="">Sélectionnez une catégorie</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.nom_categorie}
                    </option>
                  ))}
                </select>
              </div>
              {errors.categorie && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.categorie}
                </p>
              )}
            </div>
            
            {/* Champ Priorité */}
            <div>
              <label htmlFor="priorite" className="block text-sm font-medium text-gray-700 mb-1">
                Priorité
              </label>
              <div className="relative">
                <select
                  id="priorite"
                  name="priorite"
                  value={formData.priorite}
                  onChange={handleChange}
                  className={getFieldClasses('priorite')}
                  disabled={loading || submitLoading}
                >
                  <option value="faible">Basse</option>
                  <option value="normal">Normale</option>
                  <option value="urgent">Haute</option>
                  <option value="critique">Critique</option>
                </select>
                <div className="absolute inset-y-0 right-8 flex items-center pointer-events-none">
                  <PriorityBadge priority={priorityDisplayMap[formData.priorite]} />
                </div>
              </div>
            </div>
          </div>

          {/* Champ Équipement (optionnel) */}
          <div>
            <label htmlFor="equipement" className="block text-sm font-medium text-gray-700 mb-1">
              Équipement concerné (optionnel)
            </label>
            <div className="relative">
              <select
                id="equipement"
                name="equipement"
                value={formData.equipement}
                onChange={handleChange}
                className={getFieldClasses('equipement')}
                disabled={loading || submitLoading}
              >
                <option value="">Aucun équipement spécifique</option>
                {equipements.map(equipment => (
                  <option key={equipment.id} value={equipment.id}>
                    {equipment.nom_modele} ({equipment.numero_serie})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Champ Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description détaillée
              <span className="text-red-500 ml-1">*</span>
            </label>
            <div className="relative">
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                onBlur={handleBlur}
                rows={5}
                className={getFieldClasses('description')}
                placeholder="Décrivez votre problème en détail..."
                aria-invalid={!!(errors.description && isTouched.description)}
                aria-describedby={errors.description && isTouched.description ? 'description-error' : undefined}
                disabled={loading || submitLoading}
              />
              {errors.description && isTouched.description && (
                <div className="absolute top-3 right-3">
                  <FaExclamationCircle className="h-5 w-5 text-red-500" />
                </div>
              )}
            </div>
            {errors.description && isTouched.description ? (
              <p className="mt-1 text-sm text-red-600" id="description-error">
                {errors.description}
              </p>
            ) : (
              <p className="mt-1 text-xs text-gray-500">
                Soyez aussi précis que possible pour une résolution plus rapide.
              </p>
            )}
          </div>
          
          <div className="flex justify-end space-x-3 border-t border-gray-100 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer"
              disabled={submitLoading}
            >
              Annuler
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-[var(--primary-color)] rounded-md hover:bg-[var(--primary-dark)] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading || submitLoading}
            >
              {submitLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Création...
                </>
              ) : 'Créer le ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewTicketModal;
