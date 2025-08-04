import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Dashboard from './views/Dashboard';
import MyTickets from './views/MyTickets';
import TechnicianTickets from './views/TechnicianTickets';
import Materiel from './views/Materiel';
import Rapport from './views/Rapport';
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';
import DiagnosticIntelligent from "./views/DiagnosticIntelligent.jsx";

// Composant pour gérer la redirection de la page d'accueil
const HomeRedirect = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2" style={{ borderColor: 'var(--primary-color)' }}></div>
      </div>
    );
  }

  // Si l'utilisateur est connecté, le rediriger vers le dashboard
  if (isAuthenticated) {
    return <Navigate to="/tableau-de-bord" replace />;
  }

  // Sinon, afficher la page de connexion
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
      <Login />
    </div>
  );
};

function AppContent() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Router
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true
        }}
      >
        <Routes>
          {/* Page d'accueil avec logique de redirection */}
          <Route path="/" element={<HomeRedirect />} />

          {/* Routes protégées */}
          <Route path="/tableau-de-bord" element={
            <ProtectedRoute>
              <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
                <Navbar />
                <main className="flex-1 ml-64 p-8 overflow-auto">
                  <Dashboard />
                </main>
              </div>
            </ProtectedRoute>
          } />

          <Route path="/mes-tickets" element={
            <ProtectedRoute>
              <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
                <Navbar />
                <main className="flex-1 ml-64 p-8 overflow-auto">
                  <MyTickets />
                </main>
              </div>
            </ProtectedRoute>
          } />

          <Route path="/diagnostic" element={
            <ProtectedRoute>
              <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
                <Navbar />
                <main className="flex-1 ml-64 p-8 overflow-auto">
                  <DiagnosticIntelligent />
                </main>
              </div>
            </ProtectedRoute>
          } />

          <Route path="/materiel" element={
            <ProtectedRoute>
              <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
                <Navbar />
                <main className="flex-1 ml-64 p-8 overflow-auto">
                  <Materiel />
                </main>
              </div>
            </ProtectedRoute>
          } />

          <Route path="/support-technique" element={
            <ProtectedRoute>
              <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
                <Navbar />
                <main className="flex-1 ml-64 p-8 overflow-auto">
                  <TechnicianTickets />
                </main>
              </div>
            </ProtectedRoute>
          } />

          <Route path="/rapport" element={
            <ProtectedRoute>
              <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
                <Navbar />
                <main className="flex-1 ml-64 p-8 overflow-auto">
                  <Rapport />
                </main>
              </div>
            </ProtectedRoute>
          } />

          {/* Redirection pour toutes les autres routes */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;