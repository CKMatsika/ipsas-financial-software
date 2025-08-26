import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export default function Login() {
  const { login } = useAuth();
  return (
    <div className="p-8">
      <h2 className="text-xl mb-4">Login</h2>
      <button className="px-4 py-2 bg-black text-white" onClick={login}>Login</button>
    </div>
  );
}


