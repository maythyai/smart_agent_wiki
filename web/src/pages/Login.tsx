import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router';
import { api } from '../lib/api';
import { useAuthStore } from '../stores/authStore';

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * Login page — the first断裂点 fix.
 * Users can authenticate with email/password via JWT.
 */
export default function Login() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Redirect if already logged in
  if (isAuthenticated) {
    navigate('/dashboard', { replace: true });
    return null;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await api.post<TokenResponse>('/api/auth/login', {
        email,
        password,
      });

      setTokens(response.access_token, response.refresh_token);

      // Fetch the real user profile so the UI has id/role/display_name
      // instead of a stubbed empty id.
      try {
        const me = await api.get<{
          id: string;
          email: string;
          role: string;
          display_name?: string;
        }>('/api/auth/me');
        setUser({
          id: me.id,
          email: me.email,
          role: me.role,
          display_name: me.display_name,
        });
      } catch {
        // Profile fetch failed — keep the session authenticated with a
        // minimal user object so the user is not blocked.
        setUser({ id: '', email, role: 'viewer' });
      }

      navigate('/dashboard');
    } catch (err) {
      setError(
        err instanceof Error ? err.message : '登录失败，请检查邮箱和密码',
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Smart Agent Wiki
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2">
            登录以访问你的知识库
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border dark:border-gray-700 p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >
                邮箱
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="you@example.com"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                  dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
              />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >
                密码
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="••••••••"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                  dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50
                text-white font-medium rounded-lg transition-colors"
            >
              {isLoading ? '登录中...' : '登录'}
            </button>
          </form>

          {/* Help text */}
          <div className="mt-4 pt-4 border-t dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
              还没有账号？使用 CLI 注册: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">saw auth register</code>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
