import React from 'react';
import ContentCard from '../components/ContentCard';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

// Données pour le graphique des tickets par catégorie
const categoryData = [
  { name: 'Jan', 'Matériel': 40, 'Logiciel': 24, 'Réseau': 18, 'Autre': 12 },
  { name: 'Fév', 'Matériel': 30, 'Logiciel': 13, 'Réseau': 22, 'Autre': 8 },
  { name: 'Mar', 'Matériel': 20, 'Logiciel': 18, 'Réseau': 25, 'Autre': 15 },
  { name: 'Avr', 'Matériel': 27, 'Logiciel': 22, 'Réseau': 20, 'Autre': 10 },
  { name: 'Mai', 'Matériel': 35, 'Logiciel': 15, 'Réseau': 18, 'Autre': 12 },
  { name: 'Juin', 'Matériel': 42, 'Logiciel': 28, 'Réseau': 15, 'Autre': 10 },
];

// Données pour le graphique des tickets par statut
const statusData = [
  { name: 'Nouveau', value: 45 },
  { name: 'En cours', value: 28 },
  { name: 'En attente', value: 15 },
  { name: 'Résolu', value: 32 },
  { name: 'Fermé', value: 25 },
];

// Couleurs personnalisées pour les graphiques
const colors = {
  primary: 'var(--primary-color)',
  secondary: 'var(--secondary-color)',
  success: 'var(--success-color)',
  warning: 'var(--warning-color)',
  danger: 'var(--danger-color)',
  info: 'var(--info-color)',
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
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Tableau de bord</h1>
      <ContentCard>
        {/* Cartes de statistiques */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Carte Annuelle */}
          <ContentCard className="border-t-4 border-[var(--primary-color)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total sur 1 an</p>
                <h3 className="text-2xl font-bold text-[var(--primary-dark)]">1,248</h3>
                <p className="text-sm text-gray-500 mt-2">
                  <span className="text-[var(--success-color)]">+12%</span> vs année dernière
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
                <h3 className="text-2xl font-bold text-[var(--secondary-dark)]">148</h3>
                <p className="text-sm text-gray-500 mt-2">
                  <span className="text-[var(--success-color)]">+5%</span> vs mois dernier
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
                <h3 className="text-2xl font-bold text-[var(--info-dark)]">24</h3>
                <p className="text-sm text-gray-500 mt-2">
                  <span className="text-[var(--danger-color)]">-3%</span> vs hier
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
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={categoryData}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorMatériel" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={colors.primary} stopOpacity={0.8}/>
                      <stop offset="95%" stopColor={colors.primary} stopOpacity={0.1}/>
                    </linearGradient>
                    <linearGradient id="colorLogiciel" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={colors.secondary} stopOpacity={0.8}/>
                      <stop offset="95%" stopColor={colors.secondary} stopOpacity={0.1}/>
                    </linearGradient>
                    <linearGradient id="colorRéseau" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={colors.success} stopOpacity={0.8}/>
                      <stop offset="95%" stopColor={colors.success} stopOpacity={0.1}/>
                    </linearGradient>
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
                  <Area
                    type="monotone"
                    dataKey="Matériel"
                    stroke={colors.primary}
                    fillOpacity={1}
                    fill="url(#colorMatériel)"
                  />
                  <Area
                    type="monotone"
                    dataKey="Logiciel"
                    stroke={colors.secondary}
                    fillOpacity={1}
                    fill="url(#colorLogiciel)"
                  />
                  <Area
                    type="monotone"
                    dataKey="Réseau"
                    stroke={colors.success}
                    fillOpacity={1}
                    fill="url(#colorRéseau)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </ContentCard>

          {/* Graphique des tickets par statut */}
          <ContentCard title="Répartition des tickets par statut" className="col-span-1">
            <div className="h-80 mt-4">
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
                  <Bar 
                  dataKey="value"
                  radius={[0, 4, 4, 0]}
                  label={{ position: 'right' }}
                >
                  {statusData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`}
                      fill={
                        entry.name === 'Nouveau' ? '#FF9800' : // Orange
                        entry.name === 'En cours' ? '#2196F3' : // Blue
                        entry.name === 'En attente' ? '#9E9E9E' : // Grey
                        entry.name === 'Résolu' ? '#4CAF50' : // Green
                        '#F44336' // Red for 'Fermé'
                      }
                    />
                  ))}
                </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ContentCard>
        </div>
      </ContentCard>
    </div>
  );
};

export default Dashboard;
