import React from 'react';
import { Link } from 'react-router-dom';

export default function Sidebar() {
  return (
    <aside className="w-64 p-4 border-r border-gray-200 hidden md:block">
      <nav className="space-y-2">
        <Link to="/dashboard" className="block">Dashboard</Link>
        <Link to="/chart-of-accounts" className="block">Chart of Accounts</Link>
        <Link to="/journal-entries" className="block">Journal Entries</Link>
        <Link to="/financial-statements" className="block">Financial Statements</Link>
        <Link to="/reports" className="block">Reports</Link>
        <Link to="/users" className="block">Users</Link>
        <Link to="/settings" className="block">Settings</Link>
      </nav>
    </aside>
  );
}


