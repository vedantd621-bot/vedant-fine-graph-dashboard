import React, { createContext, useContext, useState, ReactNode } from 'react';
import { User, Role, LoginCredentials } from '../types/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  hasRole: (required: Role | Role[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEFAULT_ANALYST_USER: User = {
  id: 'usr-analyst-01',
  username: 'analyst',
  email: 'analyst@fingraph.internal',
  full_name: 'Lead Fraud Analyst',
  role: 'ADMIN',
  is_active: true,
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(DEFAULT_ANALYST_USER);
  const [token, setToken] = useState<string | null>('fingraph-direct-session');

  const login = async (_credentials: LoginCredentials) => {
    setUser(DEFAULT_ANALYST_USER);
    setToken('fingraph-direct-session');
  };

  const logout = () => {
    // Keep direct access session active without breaking dashboard
    setUser(DEFAULT_ANALYST_USER);
    setToken('fingraph-direct-session');
  };

  const hasRole = (_required: Role | Role[]): boolean => {
    return true;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
        login,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
