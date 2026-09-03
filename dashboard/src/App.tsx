import React, { useState } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { AlertsPage } from './pages/AlertsPage';
import { AlertDetailPage } from './pages/AlertDetailPage';
import { AccountsPage } from './pages/AccountsPage';
import { AccountDetailPage } from './pages/AccountDetailPage';
import { InvestigationPage } from './pages/InvestigationPage';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const handleSelectAccount = (accountId: string) => {
    setSelectedAccountId(accountId);
    setActiveTab('account-detail');
  };

  const handleSelectAlert = (alertId: string) => {
    setSelectedAlertId(alertId);
    setActiveTab('alert-detail');
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setActiveTab('investigation');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onSearch={handleSearch}
        onRefresh={() => window.location.reload()}
      />

      {/* Main Body Layout */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeTab={activeTab.startsWith('account') ? 'accounts' : activeTab.startsWith('alert') ? 'alerts' : activeTab}
          setActiveTab={setActiveTab}
        />

        <main className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full">
          {activeTab === 'dashboard' && (
            <DashboardPage
              onSelectAccount={handleSelectAccount}
              onSelectAlert={handleSelectAlert}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === 'alerts' && (
            <AlertsPage onSelectAlert={handleSelectAlert} />
          )}

          {activeTab === 'alert-detail' && selectedAlertId && (
            <AlertDetailPage
              alertId={selectedAlertId}
              onBack={() => setActiveTab('alerts')}
              onSelectAccount={handleSelectAccount}
            />
          )}

          {activeTab === 'accounts' && (
            <AccountsPage onSelectAccount={handleSelectAccount} />
          )}

          {activeTab === 'account-detail' && selectedAccountId && (
            <AccountDetailPage
              accountId={selectedAccountId}
              onBack={() => setActiveTab('accounts')}
              onSelectAccount={handleSelectAccount}
            />
          )}

          {activeTab === 'investigation' && (
            <InvestigationPage
              onSelectAccount={handleSelectAccount}
              onSelectAlert={handleSelectAlert}
              initialQuery={searchQuery}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
