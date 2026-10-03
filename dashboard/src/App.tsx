import { EnterpriseControlCenterPage } from './pages/EnterpriseControlCenterPage';
import { TenantManagementPage } from './pages/TenantManagementPage';
import { PolicyManagementPage } from './pages/PolicyManagementPage';
import { UserManagementPage } from './pages/UserManagementPage';
import { TeamManagementPage } from './pages/TeamManagementPage';
import { AnalyticsExplorerPage } from './pages/AnalyticsExplorerPage';
import { ReportingCenterPage } from './pages/ReportingCenterPage';
import { DecisioningSandboxPage } from './pages/DecisioningSandboxPage';
import React, { useState } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { AlertsPage } from './pages/AlertsPage';
import { AlertDetailPage } from './pages/AlertDetailPage';
import { AccountsPage } from './pages/AccountsPage';
import { AccountDetailPage } from './pages/AccountDetailPage';
import { CasesPage } from './pages/CasesPage';
import { InvestigationPage } from './pages/InvestigationPage';
import { FraudNetworksPage } from './pages/FraudNetworksPage';
import { FraudNetworkDetailPage } from './pages/FraudNetworkDetailPage';
import { AlertQueuePage } from './pages/AlertQueuePage';
import { InvestigationOperationsPage } from './pages/InvestigationOperationsPage';
import { FraudOperationsDashboard } from './pages/FraudOperationsDashboard';
import { FraudCommandCenterPage } from './pages/FraudCommandCenterPage';
import { CaseIntelligencePage } from './pages/CaseIntelligencePage';
import { FraudCampaignDetailPage } from './pages/FraudCampaignDetailPage';
import { NetworkEvolutionPage } from './pages/NetworkEvolutionPage';
import { EarlyWarningPage } from './pages/EarlyWarningPage';
import { PatternIntelligencePage } from './pages/PatternIntelligencePage';
import { AdaptiveIntelligencePage } from './pages/AdaptiveIntelligencePage';
import { ThreatPropagationPage } from './pages/ThreatPropagationPage';
import { InvestigationIntelligencePage } from './pages/InvestigationIntelligencePage';
import { AlertCorrelationPage } from './pages/AlertCorrelationPage';
import { TaskManagementPage } from './pages/TaskManagementPage';
import { TransactionInvestigationDetailPage } from './pages/TransactionInvestigationDetailPage';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { RealtimeProvider } from './realtime/RealtimeContext';
import { AlertToast } from './components/realtime/AlertToast';

export const AppContent: React.FC = () => {  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [selectedNetworkId, setSelectedNetworkId] = useState<string | null>(null);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>('CMP-2026-001');
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [selectedTransactionId, setSelectedTransactionId] = useState<string | null>('TX-892410-FRD');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const handleSelectAccount = (accountId: string) => {
    setSelectedAccountId(accountId);
    setActiveTab('account-detail');
  };

  const handleSelectAlert = (alertId: string) => {
    setSelectedAlertId(alertId);
    setActiveTab('alert-detail');
  };

  const handleSelectNetwork = (networkId: string) => {
    setSelectedNetworkId(networkId);
    setActiveTab('network-detail');
  };

  const handleSelectCampaign = (campaignId: string) => {
    setSelectedCampaignId(campaignId);
    setActiveTab('campaign-detail');
  };

  const handleSelectCase = (caseId: string) => {
    setSelectedCaseId(caseId);
    setActiveTab('cases');
  };

  const handleSelectTransaction = (transactionId: string) => {
    setSelectedTransactionId(transactionId);
    setActiveTab('transaction-detail');
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setActiveTab('investigation');
  };

  return (
    <RealtimeProvider>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
        <AlertToast onSelectAlert={handleSelectAlert} />

        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onSearch={handleSearch}
          onRefresh={() => window.location.reload()}
          onSelectAlert={handleSelectAlert}
          onSelectAccount={handleSelectAccount}
        />

        <div className="flex-1 flex overflow-hidden">
          <Sidebar
            activeTab={
              activeTab.startsWith('account')
                ? 'accounts'
                : activeTab.startsWith('alert')
                ? 'alerts'
                : activeTab.startsWith('network')
                ? 'networks'
                : activeTab.startsWith('campaign')
                ? 'command-center'
                : activeTab
            }
            setActiveTab={setActiveTab}
          />

          <main className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full">
            {/* 6 PRIMARY CORE MODULES */}
            {activeTab === 'dashboard' && (
              <DashboardPage
                onSelectAccount={handleSelectAccount}
                onSelectAlert={handleSelectAlert}
                onNavigate={setActiveTab}
              />
            )}

            {activeTab === 'investigation' && (
              <InvestigationPage
                onSelectAccount={handleSelectAccount}
                onSelectAlert={handleSelectAlert}
                initialQuery={searchQuery}
              />
            )}

            {activeTab === 'networks' && (
              <FraudNetworksPage
                onSelectNetwork={handleSelectNetwork}
                onSelectAccount={handleSelectAccount}
              />
            )}

            {activeTab === 'alerts' && (
              <AlertsPage onSelectAlert={handleSelectAlert} />
            )}

            {activeTab === 'analytics-explorer' && <AnalyticsExplorerPage />}

            {activeTab === 'transaction-detail' && (
              <TransactionInvestigationDetailPage
                transactionId={selectedTransactionId || 'TX-892410-FRD'}
                onBack={() => setActiveTab('dashboard')}
                onSelectAccount={handleSelectAccount}
                onSelectAlert={handleSelectAlert}
                onSelectCase={handleSelectCase}
                onSelectNetwork={handleSelectNetwork}
              />
            )}

            {/* SECONDARY / ADVANCED ENTERPRISE SUITE */}
            {activeTab === 'control-center' && <EnterpriseControlCenterPage />}
            {activeTab === 'tenants' && <TenantManagementPage />}
            {activeTab === 'policies' && <PolicyManagementPage />}
            {activeTab === 'user-management' && <UserManagementPage />}
            {activeTab === 'team-management' && <TeamManagementPage />}
            {activeTab === 'reporting-center' && <ReportingCenterPage />}
            {activeTab === 'decisioning-sandbox' && <DecisioningSandboxPage />}

            {activeTab === 'command-center' && (
              <FraudCommandCenterPage
                onNavigate={setActiveTab}
                onSelectCampaign={handleSelectCampaign}
              />
            )}

            {activeTab === 'early-warnings' && <EarlyWarningPage />}
            {activeTab === 'network-evolution' && <NetworkEvolutionPage />}
            {activeTab === 'pattern-intelligence' && <PatternIntelligencePage />}
            {activeTab === 'adaptive-intelligence' && <AdaptiveIntelligencePage />}
            {activeTab === 'threat-propagation' && <ThreatPropagationPage />}
            {activeTab === 'investigation-intelligence' && <InvestigationIntelligencePage />}
            {activeTab === 'alert-correlation' && <AlertCorrelationPage />}
            {activeTab === 'task-management' && <TaskManagementPage />}

            {activeTab === 'campaign-detail' && selectedCampaignId && (
              <FraudCampaignDetailPage
                campaignId={selectedCampaignId}
                onBack={() => setActiveTab('command-center')}
                onSelectCase={handleSelectCase}
              />
            )}

            {activeTab === 'case-intelligence' && (
              <CaseIntelligencePage onSelectCase={handleSelectCase} />
            )}

            {activeTab === 'operations' && (
              <FraudOperationsDashboard onNavigate={setActiveTab} />
            )}

            {activeTab === 'queue' && (
              <AlertQueuePage
                onSelectAlert={handleSelectAlert}
                onSelectAccount={handleSelectAccount}
              />
            )}

            {activeTab === 'investigator-hub' && (
              <InvestigationOperationsPage
                onSelectAccount={handleSelectAccount}
                onSelectAlert={handleSelectAlert}
                onNavigate={setActiveTab}
              />
            )}

            {activeTab === 'alert-detail' && selectedAlertId && (
              <AlertDetailPage
                alertId={selectedAlertId}
                onBack={() => setActiveTab('alerts')}
                onSelectAccount={handleSelectAccount}
              />
            )}

            {activeTab === 'network-detail' && selectedNetworkId && (
              <FraudNetworkDetailPage
                networkId={selectedNetworkId}
                onBack={() => setActiveTab('networks')}
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

            {activeTab === 'cases' && (
              <CasesPage
                onSelectAccount={handleSelectAccount}
                onSelectAlert={handleSelectAlert}
              />
            )}
          </main>
        </div>
      </div>
    </RealtimeProvider>
  );
};

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
