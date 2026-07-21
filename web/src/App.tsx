import { Outlet, NavLink, useNavigate } from 'react-router';
import { MobileNav } from './components/layout/MobileNav';
import { CommandPalette } from './components/search/CommandPalette';
import { QuickCapture } from './components/capture/QuickCapture';
import { useStore } from './stores';
import { useAuthStore } from './stores/authStore';

/**
 * Main App layout with responsive navigation.
 * Per D-06: Header has fixed height 56px (h-14).
 * Per D-04: Hamburger menu visible on mobile, horizontal nav on desktop.
 */
export default function App() {
  const theme = useStore((s) => s.theme);
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const logout = useAuthStore((s) => s.logout);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={`min-h-screen flex flex-col ${theme === 'dark' ? 'dark' : ''}`}>
      {/* Skip to main content link for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2
          focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded"
      >
        Skip to main content
      </a>

      {/* Command Palette (Cmd+K) */}
      <CommandPalette />

      {/* Quick Capture (Cmd+Shift+N) */}
      <QuickCapture />

      {/* Fixed height header per D-06 */}
      <header className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 h-14 fixed top-0 left-0 right-0 z-30">
        <div className="flex items-center justify-between h-full px-4 max-w-7xl mx-auto">
          {/* Logo */}
          <h1 className="text-lg md:text-xl font-bold text-gray-900 dark:text-white">
            Smart Agent Wiki
          </h1>

          {/* Desktop navigation - hidden on mobile */}
          <nav className="hidden md:flex gap-4 items-center">
            <NavLink
              to="/pages"
              className={({ isActive }) =>
                isActive
                  ? 'text-blue-600 font-medium'
                  : 'text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
              }
            >
              Pages
            </NavLink>
            <NavLink
              to="/search"
              className={({ isActive }) =>
                isActive
                  ? 'text-blue-600 font-medium'
                  : 'text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
              }
            >
              Search
            </NavLink>
            <NavLink
              to="/graph"
              className={({ isActive }) =>
                isActive
                  ? 'text-blue-600 font-medium'
                  : 'text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
              }
            >
              Graph
            </NavLink>
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                isActive
                  ? 'text-blue-600 font-medium'
                  : 'text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
              }
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/import"
              className={({ isActive }) =>
                isActive
                  ? 'text-blue-600 font-medium'
                  : 'text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
              }
            >
              Import
            </NavLink>
            <NavLink
              to="/templates"
              className={({ isActive }) =>
                isActive
                  ? 'text-blue-600 font-medium'
                  : 'text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
              }
            >
              Templates
            </NavLink>
            <NavLink
              to="/timeline"
              className={({ isActive }) =>
                isActive
                  ? 'text-blue-600 font-medium'
                  : 'text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
              }
            >
              Timeline
            </NavLink>

            {/* Cmd+K search button */}
            <button
              onClick={() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400
                bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg
                transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span className="hidden lg:inline">Search</span>
              <kbd className="hidden lg:inline-block px-1.5 py-0.5 text-xs font-mono
                bg-white dark:bg-gray-800 rounded">⌘K</kbd>
            </button>
          </nav>

          {/* Logout button */}
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="hidden md:block text-sm text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
            >
              Logout
            </button>
          )}

          {/* Mobile hamburger menu */}
          <MobileNav />
        </div>
      </header>

      {/* Main content with top padding for fixed header */}
      <main id="main-content" className="flex-1 pt-14 px-4 md:px-6 dark:bg-gray-900 dark:text-white">
        <Outlet />
      </main>
    </div>
  );
}
