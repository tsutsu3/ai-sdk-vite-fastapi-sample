/**
 * Minimal user identity used across the UI.
 */
export type UserInfo = {
  id?: string;
  user_id?: string;
  email?: string | null;
  provider?: string;
  first_name?: string | null;
  last_name?: string | null;
};
