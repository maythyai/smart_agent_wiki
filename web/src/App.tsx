import { Outlet, NavLink } from 'react-router';
import { MobileNav } from './components/layout/MobileNav';
import { useStore } from './stores';

/**
 * Main App layout with responsive navigation.
 * Per D-06: Header has fixed height 56px (h-14).
 * Per D-04: Hamburger menu visible on mobile, horizontal nav on desktop.
 */
export default function App() {
  const theme = useStore((s) => s.theme);

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

      {/* Fixed height header per D-06 */}
      <header className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 h-14 fixed top-0 left-0 right-0 z-30">
        <div className="flex items-center justify-between h-full px-4 max-w-7xl mx-auto">
          {/* Logo */}
          <h1 className="text-lg md:text-xl font-bold text-gray-900 dark:text-white">
            Smart Agent Wiki
          </h1>

          {/* Desktop navigation - hidden on mobile */}
          <nav className="hidden md:flex gap-4">
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
          </nav>

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
