import { createBrowserRouter } from 'react-router';
import App from '../App';
import Home from '../pages/Home';
import Search from '../pages/Search';
import Graph from '../pages/Graph';
import Page from '../pages/Page';
import Pages from '../pages/Pages';
import Dashboard from '../pages/Dashboard';
import Integrations from '../pages/Integrations';
import ConnectorSettings from '../pages/ConnectorSettings';
import Login from '../pages/Login';
import NotFound from '../pages/NotFound';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: <App />,
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
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);