import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import { HelmetProvider } from 'react-helmet-async';

// Layout Components
import Layout from './components/layout/Layout';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';

// Authentication Components
import Login from './components/auth/Login';
import ProtectedRoute from './components/auth/ProtectedRoute';

// Dashboard Components
import Dashboard from './components/dashboard/Dashboard';

// Chart of Accounts Components
import ChartOfAccounts from './components/chart-of-accounts/ChartOfAccounts';
import AccountDetail from './components/chart-of-accounts/AccountDetail';

// Journal Entries Components
import JournalEntries from './components/journal-entries/JournalEntries';
import JournalEntryForm from './components/journal-entries/JournalEntryForm';
import JournalEntryDetail from './components/journal-entries/JournalEntryDetail';

// Financial Statements Components
import FinancialStatements from './components/financial-statements/FinancialStatements';
import StatementOfFinancialPosition from './components/financial-statements/StatementOfFinancialPosition';
import StatementOfFinancialPerformance from './components/financial-statements/StatementOfFinancialPerformance';
import StatementOfCashFlows from './components/financial-statements/StatementOfCashFlows';

// Reports Components
import Reports from './components/reports/Reports';
import TrialBalance from './components/reports/TrialBalance';
import BudgetVsActual from './components/reports/BudgetVsActual';

// User Management Components
import Users from './components/users/Users';
import UserProfile from './components/users/UserProfile';

// Settings Components
import Settings from './components/settings/Settings';

// Context and Hooks
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Layout>
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            
            {/* Chart of Accounts */}
            <Route path="/chart-of-accounts" element={<ChartOfAccounts />} />
            <Route path="/chart-of-accounts/:id" element={<AccountDetail />} />
            
            {/* Journal Entries */}
            <Route path="/journal-entries" element={<JournalEntries />} />
            <Route path="/journal-entries/new" element={<JournalEntryForm />} />
            <Route path="/journal-entries/:id" element={<JournalEntryDetail />} />
            <Route path="/journal-entries/:id/edit" element={<JournalEntryForm />} />
            
            {/* Financial Statements */}
            <Route path="/financial-statements" element={<FinancialStatements />} />
            <Route path="/financial-statements/position" element={<StatementOfFinancialPosition />} />
            <Route path="/financial-statements/performance" element={<StatementOfFinancialPerformance />} />
            <Route path="/financial-statements/cash-flows" element={<StatementOfCashFlows />} />
            
            {/* Reports */}
            <Route path="/reports" element={<Reports />} />
            <Route path="/reports/trial-balance" element={<TrialBalance />} />
            <Route path="/reports/budget-vs-actual" element={<BudgetVsActual />} />
            
            {/* User Management */}
            <Route path="/users" element={<Users />} />
            <Route path="/users/profile" element={<UserProfile />} />
            
            {/* Settings */}
            <Route path="/settings" element={<Settings />} />
            
            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </Layout>
  );
}

function App() {
  return (
    <HelmetProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AuthProvider>
            <Router>
              <div className="App">
                <AppRoutes />
                <Toaster
                  position="top-right"
                  toastOptions={{
                    duration: 4000,
                    style: {
                      background: '#363636',
                      color: '#fff',
                    },
                    success: {
                      duration: 3000,
                      iconTheme: {
                        primary: '#10b981',
                        secondary: '#fff',
                      },
                    },
                    error: {
                      duration: 5000,
                      iconTheme: {
                        primary: '#ef4444',
                        secondary: '#fff',
                      },
                    },
                  }}
                />
              </div>
            </Router>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </HelmetProvider>
  );
}

export default App;
