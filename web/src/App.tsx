export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <h1 className="text-xl font-bold">Smart Agent Wiki</h1>
          <nav className="flex gap-4">
            <a href="/search" className="text-gray-600 hover:text-blue-600">
              Search
            </a>
            <a href="/graph" className="text-gray-600 hover:text-blue-600">
              Graph
            </a>
            <a href="/dashboard" className="text-gray-600 hover:text-blue-600">
              Dashboard
            </a>
          </nav>
        </div>
      </header>
      <main className="flex-1 p-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-4">Welcome to Smart Agent Wiki</h2>
          <p className="text-gray-600 mb-6">
            A next-generation intelligent multi-agent knowledge platform.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="/search"
              className="p-4 bg-white rounded-lg border hover:border-blue-500 hover:shadow transition"
            >
              <h3 className="font-semibold mb-2">Search</h3>
              <p className="text-sm text-gray-500">Search your knowledge base</p>
            </a>
            <a
              href="/graph"
              className="p-4 bg-white rounded-lg border hover:border-blue-500 hover:shadow transition"
            >
              <h3 className="font-semibold mb-2">Knowledge Graph</h3>
              <p className="text-sm text-gray-500">Visualize knowledge connections</p>
            </a>
            <a
              href="/dashboard"
              className="p-4 bg-white rounded-lg border hover:border-blue-500 hover:shadow transition"
            >
              <h3 className="font-semibold mb-2">Dashboard</h3>
              <p className="text-sm text-gray-500">Agent status and workflows</p>
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
