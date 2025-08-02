import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ContentCard from '../components/ContentCard';

const Materiel = () => {
  const { user } = useAuth();
  const [equipments, setEquipments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simuler le chargement des équipements
    setTimeout(() => {
      setEquipments([
        { id: 1, name: 'Ordinateur portable HP', category: 'Informatique', status: 'Disponible' },
        { id: 2, name: 'Imprimante Canon', category: 'Périphérique', status: 'En maintenance' },
        { id: 3, name: 'Écran Dell 24"', category: 'Affichage', status: 'Disponible' },
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2" style={{ borderColor: 'var(--primary-color)' }}></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Gestion du Matériel</h1>
        <button
          className="px-4 py-2 text-white rounded-lg font-medium hover:opacity-90 transition-opacity"
          style={{ backgroundColor: 'var(--primary-color)' }}
        >
          Ajouter du matériel
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {equipments.map((equipment) => (
          <ContentCard key={equipment.id}>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{equipment.name}</h3>
              <p className="text-sm text-gray-600 mb-2">Catégorie: {equipment.category}</p>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  equipment.status === 'Disponible' 
                    ? 'text-green-800' 
                    : 'text-orange-800'
                }`}
                style={{
                  backgroundColor: equipment.status === 'Disponible'
                    ? 'var(--success-light)'
                    : 'var(--warning-light)',
                  color: 'white'
                }}
              >
                {equipment.status}
              </span>
            </div>
          </ContentCard>
        ))}
      </div>
    </div>
  );
};

export default Materiel;
