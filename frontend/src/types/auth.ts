export type Role = 'ANALYST' | 'INVESTIGATOR' | 'ADMIN';

export interface User {
  user_id: string;
  username: string;
  email: string;
  full_name?: string;
  role: Role;
  is_active: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}
