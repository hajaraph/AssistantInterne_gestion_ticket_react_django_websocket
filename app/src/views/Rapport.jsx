import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ContentCard from '../components/ContentCard';

const Rapport = () => {
  const { user } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simuler le chargement des rapports
    setTimeout(() => {
      setReports([
        { id: 1, title: 'Rapport mensuel des tickets', date: '2025-08-01', type: 'Tickets' },
        { id: 2, title: 'Rapport d\'activité technique', date: '2025-07-31', type: 'Activité' },
        { id: 3, title: 'Rapport des équipements', date: '2025-07-30', type: 'Matériel' },
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
        <h1 className="text-2xl font-bold text-gray-900">Rapports</h1>
        <button
          className="px-4 py-2 text-white rounded-lg font-medium hover:opacity-90 transition-opacity"
          style={{ backgroundColor: 'var(--primary-color)' }}
        >
          Générer un rapport
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map((report) => (
          <ContentCard key={report.id}>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{report.title}</h3>
              <p className="text-sm text-gray-600 mb-2">Type: {report.type}</p>
              <p className="text-sm text-gray-500 mb-4">Date: {report.date}</p>
              <button
                className="w-full px-4 py-2 text-white rounded-lg font-medium hover:opacity-90 transition-opacity"
                style={{ backgroundColor: 'var(--info-color)' }}
              >
                Télécharger
              </button>
            </div>
          </ContentCard>
        ))}
      </div>
    </div>
  );
};

export default Rapport;
