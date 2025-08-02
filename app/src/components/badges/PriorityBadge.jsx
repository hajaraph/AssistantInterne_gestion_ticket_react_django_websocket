import React from 'react';
import {
  FaExclamationTriangle,
  FaExclamation,
  FaInfoCircle,
  FaArrowDown,
  FaBolt,
  FaFire,
  FaShieldAlt
} from 'react-icons/fa';

const PriorityBadge = ({ priority }) => {
  const getPriorityConfig = (priority) => {
    const priorityMap = {
      // Valeurs du backend Django
      'critique': {
        icon: FaBolt,
        color: 'var(--danger-color)',
        bgColor: 'var(--danger-light)',
        textColor: 'white',
        displayName: 'Critique'
      },
      'urgent': {
        icon: FaExclamationTriangle,
        color: 'var(--warning-color)',
        bgColor: 'var(--warning-light)',
        textColor: 'white',
        displayName: 'Urgent'
      },
      'normal': {
        icon: FaInfoCircle,
        color: 'var(--info-color)',
        bgColor: 'var(--info-light)',
        textColor: 'white',
        displayName: 'Normal'
      },
      'faible': {
        icon: FaArrowDown,
        color: 'var(--success-color)',
        bgColor: 'var(--success-light)',
        textColor: 'white',
        displayName: 'Faible'
      },
      // Valeurs mappées de TechnicianTickets (pour compatibilité)
      'Critique': {
        icon: FaBolt,
        color: 'var(--danger-color)',
        bgColor: 'var(--danger-light)',
        textColor: 'white',
        displayName: 'Critique'
      },
      'Haute': {
        icon: FaExclamationTriangle,
        color: 'var(--warning-color)',
        bgColor: 'var(--warning-light)',
        textColor: 'white',
        displayName: 'Haute'
      },
      'Normale': {
        icon: FaInfoCircle,
        color: 'var(--info-color)',
        bgColor: 'var(--info-light)',
        textColor: 'white',
        displayName: 'Normale'
      },
      'Basse': {
        icon: FaArrowDown,
        color: 'var(--success-color)',
        bgColor: 'var(--success-light)',
        textColor: 'white',
        displayName: 'Basse'
      }
    };

    return priorityMap[priority] || priorityMap['normal'];
  };

  const config = getPriorityConfig(priority);
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

export default PriorityBadge;
