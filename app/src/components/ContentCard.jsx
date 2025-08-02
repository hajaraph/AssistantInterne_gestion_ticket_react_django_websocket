import React from 'react';

const ContentCard = ({ title, children, className = '' }) => {
  return (
    <div className={`bg-white rounded-lg shadow-md p-6 mb-6 ${className}`}>
      {title && (
        <h2 className="text-xl font-semibold text-gray-800 mb-4">
          {title}
        </h2>
      )}
      <div className="text-gray-600">
        {children}
      </div>
    </div>
  );
};

export default ContentCard;
