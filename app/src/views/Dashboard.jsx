import React, { useState, useEffect } from 'react';
import ContentCard from '../components/ContentCard';
import StatusBadge from '../components/badges/StatusBadge';
import PriorityBadge from '../components/badges/PriorityBadge';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

// Données par défaut pour les graphiques
const defaultCategoryData = [];
const defaultStatusData = [];

// Couleurs personnalisées pour les graphiques
const colors = {
  primary: 'var(--primary-color)',
  secondary: 'var(--secondary-color)',
  success: 'var(--success-color)',
  warning: 'var(--warning-color)',
  danger: 'var(--danger-color)',
  info: 'var(--info-color)',
  
  // Couleurs pour les statuts
  'Nouveau': 'var(--info-color)',
  'Ouvert': 'var(--primary-color)',
  'En cours': 'var(--warning-color)',
  'En attente': 'var(--secondary-color)',
  'Résolu': 'var(--success-color)',
  'Fermé': 'var(--gray-500)',
  'Annulé': 'var(--danger-color)',
  
  // Couleurs pour les priorités
  'Critique': 'var(--danger-color)',
  'Urgent': 'var(--warning-color)',
  'Normal': 'var(--info-color)',
  'Faible': 'var(--success-color)',

  // Couleurs pour les catégories
  'Matériel': 'var(--primary-color)',
  'Logiciel': 'var(--info-color)',
  'Réseau': 'var(--success-color)',
  'Autre': 'var(--secondary-color)'
};

// Fonction pour formater les noms de statuts
const formatStatusName = (statusKey) => {
  const statusMap = {
    'nouveau': 'Nouveau',
    'ouvert': 'Ouvert',
    'en_cours': 'En cours',
    'en_attente': 'En attente',
    'resolu': 'Résolu',
    'ferme': 'Fermé',
    'annule': 'Annulé'
  };
  return statusMap[statusKey] || statusKey;
};

// Fonction pour formater les noms de priorités
const formatPriorityName = (priorityKey) => {
  const priorityMap = {
    'critique': 'Critique',
    'urgent': 'Urgent',
    'normal': 'Normal',
    'faible': 'Faible'
  };
  return priorityMap[priorityKey] || priorityKey;
};

// Composant personnalisé pour la légende du graphique
const CustomLegend = ({ payload }) => {
  return (
    <div className="flex justify-center space-x-4 mt-2">
      {payload.map((entry, index) => (
        <div key={`item-${index}`} className="flex items-center">
          <div 
            className="w-3 h-3 rounded-full mr-2" 
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-sm text-gray-600">{entry.value}</span>
        </div>
      ))}
    </div>
  );
};

// Composant personnalisé pour l'infobulle
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
        <p className="font-medium text-gray-900">{label}</p>
        {payload.map((entry, index) => (
          <p key={`tooltip-${index}`} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const Dashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState({
    stats: {},
    recentTickets: [],
    recentComments: []
  });
  const [categoryData, setCategoryData] = useState(defaultCategoryData);
  const [statusData, setStatusData] = useState(defaultStatusData);
  const [priorityData, setPriorityData] = useState([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const data = await apiService.getDashboardData();
        setDashboardData(data);
        
        // Mettre à jour les données des graphiques
        if (data.stats.tickets_by_category) {
          setCategoryData(data.stats.tickets_by_category);
        }
        
        if (data.stats.tickets_by_status) {
          // Formater les noms de statuts pour l'affichage
          const formattedStatusData = data.stats.tickets_by_status.map(item => ({
            ...item,
            name: formatStatusName(item.name)
          }));
          setStatusData(formattedStatusData);
        }

        if (data.stats.tickets_by_priority) {
          // Formater les noms de priorités pour l'affichage
          const formattedPriorityData = data.stats.tickets_by_priority.map(item => ({
            ...item,
            name: formatPriorityName(item.name)
          }));
          setPriorityData(formattedPriorityData);
        }
      } catch (err) {
        console.error('Erreur lors du chargement des données du tableau de bord:', err);
        setError('Impossible de charger les données du tableau de bord');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        Tableau de bord
        {dashboardData.user_info && (
          <span className="text-lg font-normal text-gray-600 ml-2">
            - {dashboardData.user_info.name} ({dashboardData.user_info.role})
          </span>
        )}
      </h1>
      <ContentCard>
        {/* Cartes de statistiques */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Carte Annuelle */}
          <ContentCard className="border-t-4 border-[var(--primary-color)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total sur 1 an</p>
                <h3 className="text-2xl font-bold text-[var(--primary-dark)]">
                  {dashboardData.stats?.tickets_this_year || 0}
                </h3>
                <p className="text-sm text-gray-500 mt-2">
                  {dashboardData.stats?.avg_resolution_time_hours ? (
                    <span className="text-[var(--info-color)]">
                      {dashboardData.stats.avg_resolution_time_hours}h résolution moyenne
                    </span>
                  ) : (
                    <span className="text-gray-400">Données en cours de calcul</span>
                  )}
                </p>
              </div>
              <div className="bg-[var(--primary-light)]/20 p-3 rounded-full">
                <svg className="w-6 h-6 text-[var(--primary-color)]" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
            </div>
          </ContentCard>

          {/* Carte Mensuelle */}
          <ContentCard className="border-t-4 border-[var(--secondary-color)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Ce mois-ci</p>
                <h3 className="text-2xl font-bold text-[var(--secondary-dark)]">
                  {dashboardData.stats?.tickets_this_month || 0}
                </h3>
                <p className="text-sm text-gray-500 mt-2">
                  {dashboardData.stats?.tickets_resolved_this_month !== undefined ? (
                    <span className="text-[var(--success-color)]">
                      {dashboardData.stats.tickets_resolved_this_month} résolus
                    </span>
                  ) : dashboardData.stats?.resolution_rate !== undefined ? (
                    <span className="text-[var(--success-color)]">
                      {dashboardData.stats.resolution_rate}% résolus
                    </span>
                  ) : (
                    <span className="text-gray-400">Calcul en cours</span>
                  )}
                </p>
              </div>
              <div className="bg-[var(--secondary-light)]/20 p-3 rounded-full">
                <svg className="w-6 h-6 text-[var(--secondary-color)]" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </ContentCard>

          {/* Carte Quotidienne */}
          <ContentCard className="border-t-4 border-[var(--info-color)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Aujourd'hui</p>
                <h3 className="text-2xl font-bold text-[var(--info-dark)]">
                  {dashboardData.stats?.tickets_today || 0}
                </h3>
                <p className="text-sm text-gray-500 mt-2">
                  {dashboardData.stats?.urgent_tickets !== undefined ? (
                    <span className={dashboardData.stats.urgent_tickets > 0 ? "text-[var(--danger-color)]" : "text-[var(--success-color)]"}>
                      {dashboardData.stats.urgent_tickets} urgent{dashboardData.stats.urgent_tickets > 1 ? 's' : ''}
                    </span>
                  ) : dashboardData.stats?.unassigned_tickets !== undefined ? (
                    <span className={dashboardData.stats.unassigned_tickets > 0 ? "text-[var(--warning-color)]" : "text-[var(--success-color)]"}>
                      {dashboardData.stats.unassigned_tickets} non assigné{dashboardData.stats.unassigned_tickets > 1 ? 's' : ''}
                    </span>
                  ) : (
                    <span className="text-gray-400">En temps réel</span>
                  )}
                </p>
              </div>
              <div className="bg-[var(--info-light)]/20 p-3 rounded-full">
                <svg className="w-6 h-6 text-[var(--info-color)]" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </ContentCard>

          {/* Graphique des tickets par catégorie */}
          <ContentCard title="Tickets par catégorie (6 derniers mois)" className="col-span-1 md:col-span-2">
            <div className="h-80 mt-4">
              {categoryData && categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={categoryData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <defs>
                      {/* Génération dynamique des gradients selon les catégories disponibles */}
                      {Object.keys(categoryData[0] || {}).filter(key => key !== 'name').map((category) => (
                        <linearGradient key={category} id={`color${category}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={colors[category] || colors.primary} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={colors[category] || colors.primary} stopOpacity={0.1}/>
                        </linearGradient>
                      ))}
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                    <XAxis
                      dataKey="name"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#6b7280' }}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#6b7280' }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend content={<CustomLegend />} />
                    {/* Génération dynamique des Areas selon les catégories */}
                    {Object.keys(categoryData[0] || {}).filter(key => key !== 'name').map((category) => (
                      <Area
                        key={category}
                        type="monotone"
                        dataKey={category}
                        stroke={colors[category] || colors.primary}
                        fillOpacity={1}
                        fill={`url(#color${category})`}
                      />
                    ))}
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p className="text-gray-500">Aucune donnée disponible pour les 6 derniers mois</p>
                </div>
              )}
            </div>
          </ContentCard>

          {/* Graphique des tickets par statut */}
          <ContentCard title="Répartition des tickets par statut" className="col-span-1">
            <div className="h-80 mt-4">
              {statusData && statusData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={statusData}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid horizontal={true} vertical={false} stroke="#f0f0f0" />
                    <XAxis
                      type="number"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#6b7280' }}
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#6b7280' }}
                      width={80}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend content={<CustomLegend />} />
                    <Bar
                      dataKey="value"
                      radius={[0, 4, 4, 0]}
                      label={{ position: 'right' }}
                    >
                      {statusData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={colors[entry.name] || colors.primary}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p className="text-gray-500">Aucune donnée de statut disponible</p>
                </div>
              )}
            </div>
          </ContentCard>

          {/* Graphique des tickets par priorité */}
          <ContentCard title="Répartition des tickets par priorité" className="col-span-1">
            <div className="h-80 mt-4">
              {priorityData && priorityData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={priorityData}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid horizontal={true} vertical={false} stroke="#f0f0f0" />
                    <XAxis
                      type="number"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#6b7280' }}
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#6b7280' }}
                      width={80}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar
                      dataKey="value"
                      radius={[0, 4, 4, 0]}
                      label={{ position: 'right' }}
                    >
                      {priorityData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={colors[entry.name] || colors.primary}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p className="text-gray-500">Aucune donnée de priorité disponible</p>
                </div>
              )}
            </div>
          </ContentCard>
        </div>

        {/* Section des tickets récents - Affichage conditionnel selon le rôle */}
        {dashboardData.recent_tickets && dashboardData.recent_tickets.length > 0 && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              {user?.role === 'technicien' ? 'Mes tickets assignés récents' :
               user?.role === 'admin' ? 'Tickets récents du système' :
               'Mes tickets récents'}
            </h2>
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ticket
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Statut
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Priorité
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dashboardData.recent_tickets.slice(0, 5).map((ticket) => (
                      <tr key={ticket.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            #{ticket.id} - {ticket.titre}
                          </div>
                          <div className="text-sm text-gray-500">
                            {ticket.categorie_nom}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge status={ticket.statut_ticket} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <PriorityBadge priority={ticket.priorite} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(ticket.date_creation).toLocaleDateString('fr-FR')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Section résumé pour employés */}
        {user?.role === 'employe' && dashboardData.summary && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            <ContentCard>
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Résumé de mes tickets</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Tickets en cours :</span>
                  <span className="font-medium text-blue-600">{dashboardData.summary.pending_tickets || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Tickets urgents :</span>
                  <span className="font-medium text-red-600">{dashboardData.summary.urgent_tickets || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Total tickets :</span>
                  <span className="font-medium text-gray-900">{dashboardData.stats?.total_tickets || 0}</span>
                </div>
              </div>
            </ContentCard>

            <ContentCard>
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Informations</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Département :</span>
                  <span className="font-medium">{dashboardData.user_info?.department || 'Non spécifié'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Dernier ticket :</span>
                  <span className="font-medium text-gray-600">
                    {dashboardData.summary.last_ticket_date ?
                      new Date(dashboardData.summary.last_ticket_date).toLocaleDateString('fr-FR') :
                      'Aucun'
                    }
                  </span>
                </div>
              </div>
            </ContentCard>
          </div>
        )}

        {/* Section performance pour techniciens */}
        {user?.role === 'technicien' && dashboardData.performance && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Ma Performance</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <ContentCard>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{dashboardData.performance.total_resolved || 0}</div>
                  <div className="text-sm text-gray-600">Tickets résolus</div>
                </div>
              </ContentCard>
              <ContentCard>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{dashboardData.performance.resolution_rate || 0}%</div>
                  <div className="text-sm text-gray-600">Taux de résolution</div>
                </div>
              </ContentCard>
              <ContentCard>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{dashboardData.performance.avg_resolution_time || 0}h</div>
                  <div className="text-sm text-gray-600">Temps moyen</div>
                </div>
              </ContentCard>
              <ContentCard>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{dashboardData.performance.tickets_this_month || 0}</div>
                  <div className="text-sm text-gray-600">Ce mois-ci</div>
                </div>
              </ContentCard>
            </div>
          </div>
        )}

        {/* Section admin - statistiques système */}
        {user?.role === 'admin' && dashboardData.system_health && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Santé du Système</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <ContentCard>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{dashboardData.system_health.resolution_rate || 0}%</div>
                  <div className="text-sm text-gray-600">Taux de résolution global</div>
                </div>
              </ContentCard>
              <ContentCard>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{dashboardData.system_health.active_technicians || 0}</div>
                  <div className="text-sm text-gray-600">Techniciens actifs</div>
                </div>
              </ContentCard>
              <ContentCard>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{dashboardData.system_health.avg_resolution_time || 0}h</div>
                  <div className="text-sm text-gray-600">Temps moyen global</div>
                </div>
              </ContentCard>
              <ContentCard>
                <div className="text-center">
                  <div className="text-2xl font-bold text-indigo-600">{dashboardData.system_health.total_users || 0}</div>
                  <div className="text-sm text-gray-600">Utilisateurs total</div>
                </div>
              </ContentCard>
            </div>
          </div>
        )}
      </ContentCard>
    </div>
  );
};

export default Dashboard;
