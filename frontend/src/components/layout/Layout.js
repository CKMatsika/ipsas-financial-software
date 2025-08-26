import React from 'react';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen w-full bg-white text-gray-900">
      {children}
    </div>
  );
}


