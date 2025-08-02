import React from 'react';
import {
  FaCircle,
  FaPlay,
  FaCheck,
  FaTimes,
  FaBan,
  FaClock,
  FaSpinner,
  FaCheckCircle,
  FaTimesCircle,
  FaStopCircle
} from 'react-icons/fa';

const StatusBadge = ({ status }) => {
  const getStatusConfig = (status) => {
    const statusMap = {
      // Valeurs du backend Django
      'ouvert': {
        icon: FaCircle,
        color: 'var(--info-color)',
        bgColor: 'var(--info-light)',
        textColor: 'white',
        displayName: 'Ouvert'
      },
      'en_cours': {
        icon: FaSpinner,
        color: 'var(--warning-color)',
        bgColor: 'var(--warning-light)',
        textColor: 'white',
        displayName: 'En cours'
      },
      'resolu': {
        icon: FaCheckCircle,
        color: 'var(--success-color)',
        bgColor: 'var(--success-light)',
        textColor: 'white',
        displayName: 'Résolu'
      },
      'ferme': {
        icon: FaStopCircle,
        color: 'var(--dark-color)',
        bgColor: 'var(--secondary-color)',
        textColor: 'white',
        displayName: 'Fermé'
      },
      'annule': {
        icon: FaTimesCircle,
        color: 'var(--danger-color)',
        bgColor: 'var(--danger-light)',
        textColor: 'white',
        displayName: 'Annulé'
      },
      // Valeurs mappées de TechnicianTickets (pour compatibilité)
      'Nouveau': {
        icon: FaCircle,
        color: 'var(--info-color)',
        bgColor: 'var(--info-light)',
        textColor: 'white',
        displayName: 'Nouveau'
      },
      'Ouvert': {
        icon: FaCircle,
        color: 'var(--info-color)',
        bgColor: 'var(--info-light)',
        textColor: 'white',
        displayName: 'Ouvert'
      },
      'En cours': {
        icon: FaSpinner,
        color: 'var(--warning-color)',
        bgColor: 'var(--warning-light)',
        textColor: 'white',
        displayName: 'En cours'
      },
      'Résolu': {
        icon: FaCheckCircle,
        color: 'var(--success-color)',
        bgColor: 'var(--success-light)',
        textColor: 'white',
        displayName: 'Résolu'
      },
      'Fermé': {
        icon: FaStopCircle,
        color: 'var(--dark-color)',
        bgColor: 'var(--secondary-color)',
        textColor: 'white',
        displayName: 'Fermé'
      },
      'Annulé': {
        icon: FaTimesCircle,
        color: 'var(--danger-color)',
        bgColor: 'var(--danger-light)',
        textColor: 'white',
        displayName: 'Annulé'
      }
    };

    return statusMap[status] || statusMap['ouvert'];
  };

  const config = getStatusConfig(status);
  const IconComponent = config.icon;

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
      style={{
        backgroundColor: config.bgColor,
        color: config.textColor
      }}
    >
      <IconComponent
        className="w-3 h-3"
        style={{ color: config.textColor }}
      />
      <span className="font-medium">{config.displayName}</span>
    </span>
  );
};

export default StatusBadge;
