import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';
import { User, Role, LoginCredentials, LoginResponse } from '../types/auth';

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

const TOKEN_KEY = 'fingraph_token';
const USER_KEY = 'fingraph_user';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem(USER_KEY);
    return saved ? JSON.parse(saved) : null;
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const apiBase =
    (typeof process !== 'undefined' && process.env?.REACT_APP_API_BASE_URL) ||
    (typeof window !== 'undefined' && (window as any).__ENV__?.REACT_APP_API_BASE_URL) ||
    'http://localhost:8000';

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      if (storedToken) {
        try {
          const res = await axios.get(`${apiBase}/api/v1/auth/me`, {
            headers: { Authorization: `Bearer ${storedToken}` }
          });
          setUser(res.data);
          localStorage.setItem(USER_KEY, JSON.stringify(res.data));
        } catch (err) {
          logout();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, [apiBase]);

  const login = async (credentials: LoginCredentials) => {
    const res = await axios.post<LoginResponse>(`${apiBase}/api/v1/auth/login`, credentials);
    const { access_token, user: loggedInUser } = res.data;
    setToken(access_token);
    setUser(loggedInUser);
    localStorage.setItem(TOKEN_KEY, access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(loggedInUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  const hasRole = (required: Role | Role[]): boolean => {
    if (!user) return false;
    if (user.role === 'ADMIN') return true;
    const requiredList = Array.isArray(required) ? required : [required];
    return requiredList.includes(user.role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
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
