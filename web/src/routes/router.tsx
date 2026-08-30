import { createBrowserRouter, Navigate } from 'react-router';
import { useEffect, useState, type ReactNode } from 'react';
import { api } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import App from '../App';
import Home from '../pages/Home';
import Search from '../pages/Search';
import Graph from '../pages/Graph';
import Page from '../pages/Page';
import Pages from '../pages/Pages';
import Dashboard from '../pages/Dashboard';
import Integrations from '../pages/Integrations';
import ConnectorSettings from '../pages/ConnectorSettings';
import Import from '../pages/Import';
import Templates from '../pages/Templates';
import Timeline from '../pages/Timeline';
import Onboarding from '../pages/Onboarding';
import Login from '../pages/Login';
import NotFound from '../pages/NotFound';

// F-WEB-04: conditional route guard. In team mode, redirect unauthenticated
// users to /login. In local mode the backend trusts tokenless requests
// (single-user, local-first), so a hard guard would break that usage.
function RequireAuth({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [mode, setMode] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .get<{ auth_mode: string }>('/api/auth/mode')
      .then((d) => !cancelled && setMode(d.auth_mode))
      .catch(() => !cancelled && setMode('local'));
    return () => {
      cancelled = true;
    };
  }, []);

  if (mode === null) return null; // loading — avoid a flash of the wrong page
  if (mode === 'team' && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/onboarding',
    element: <Onboarding />,
  },
  {
    path: '/',
    element: (
      <RequireAuth>
        <App />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <Home /> },
      { path: 'search', element: <Search /> },
      { path: 'graph', element: <Graph /> },
      { path: 'pages', element: <Pages /> },
      { path: 'page/:slug', element: <Page /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'integrations', element: <Integrations /> },
      { path: 'integrations/:platform', element: <Integrations /> },
      { path: 'integrations/:platform/settings', element: <ConnectorSettings /> },
      { path: 'import', element: <Import /> },
      { path: 'templates', element: <Templates /> },
      { path: 'timeline', element: <Timeline /> },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);