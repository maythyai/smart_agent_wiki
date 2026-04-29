import { Outlet, NavLink } from 'react-router';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <h1 className="text-xl font-bold">Smart Agent Wiki</h1>
          <nav className="flex gap-4">
            <NavLink
              to="/search"
              className={({ isActive }) => isActive ? 'text-blue-600' : 'text-gray-600 hover:text-blue-600'}
            >
              Search
            </NavLink>
            <NavLink
              to="/graph"
              className={({ isActive }) => isActive ? 'text-blue-600' : 'text-gray-600 hover:text-blue-600'}
            >
              Graph
            </NavLink>
            <NavLink
              to="/dashboard"
              className={({ isActive }) => isActive ? 'text-blue-600' : 'text-gray-600 hover:text-blue-600'}
            >
              Dashboard
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
