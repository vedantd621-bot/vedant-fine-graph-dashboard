export enum Role {
  PLATFORM_ADMIN = 'PLATFORM_ADMIN',
  ADMIN = 'ADMIN',
  TENANT_ADMIN = 'TENANT_ADMIN',
  INVESTIGATOR = 'INVESTIGATOR',
  ANALYST = 'ANALYST',
  REVIEWER = 'REVIEWER',
  AUDITOR = 'AUDITOR',
  EXECUTIVE = 'EXECUTIVE',
  READ_ONLY = 'READ_ONLY',
}

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
