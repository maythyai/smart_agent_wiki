import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useOnboardingStatus, useSeedStarterKit } from '../hooks/useOnboarding';

const STARTER_KITS = [
  { id: 'personal_pkm', name: 'Personal Knowledge Base', icon: '🧠', description: 'Organize your thoughts, bookmarks, and learning', page_count: 3 },
  { id: 'team_wiki', name: 'Team Wiki', icon: '👥', description: 'Collaborate with your team on projects', page_count: 7 },
  { id: 'research_notebook', name: 'Research Notebook', icon: '🔬', description: 'Track research topics and findings', page_count: 5 },
  { id: 'project_tracker', name: 'Project Tracker', icon: '📊', description: 'Track projects, tasks, and progress', page_count: 4 },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const { data: status } = useOnboardingStatus();
  const seedMutation = useSeedStarterKit();
  const [step, setStep] = useState(0); // 0=welcome, 1=choose, 2=seeding, 3=complete
  const [selectedKit, setSelectedKit] = useState<string | null>(null);

  const handleSkip = () => {
    localStorage.setItem('saw-onboarding-complete', 'true');
    navigate('/');
  };

  const handleSelectKit = (kitId: string) => {
    setSelectedKit(kitId);
    setStep(2);
    seedMutation.mutate(kitId, {
      onSuccess: () => {
        localStorage.setItem('saw-onboarding-complete', 'true');
        setStep(3);
      },
    });
  };

  const handleImport = () => {
    localStorage.setItem('saw-onboarding-complete', 'true');
    navigate('/import');
  };

  const handleStartScratch = () => {
    localStorage.setItem('saw-onboarding-complete', 'true');
    navigate('/pages');
  };

  const handleFinish = () => {
    navigate(selectedKit ? '/graph' : '/pages');
  };

  // If not first run and already completed, redirect
  if (status && !status.is_first_run && localStorage.getItem('saw-onboarding-complete')) {
    navigate('/');
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
        {/* Progress bar */}
        <div className="h-1 bg-gray-200 dark:bg-gray-700">
          <div
            className="h-full bg-indigo-600 transition-all duration-500"
            style={{ width: `${((step + 1) / 4) * 100}%` }}
          />
        </div>

        <div className="p-8">
          {step === 0 && <StepWelcome onNext={() => setStep(1)} onSkip={handleSkip} />}
          {step === 1 && (
            <StepChoosePath
              onSelectKit={handleSelectKit}
              onImport={handleImport}
              onScratch={handleStartScratch}
              onSkip={handleSkip}
            />
          )}
          {step === 2 && <StepSeeding kitName={selectedKit || ''} isPending={seedMutation.isPending} />}
          {step === 3 && (
            <StepComplete
              kitName={STARTER_KITS.find((k) => k.id === selectedKit)?.name || ''}
              onFinish={handleFinish}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function StepWelcome({ onNext, onSkip }: { onNext: () => void; onSkip: () => void }) {
  return (
    <div className="text-center">
      <div className="text-6xl mb-4">🎉</div>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
        Welcome to Smart Agent Wiki
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
        Your local-first knowledge platform with AI agents. Let's get you started in under a minute.
      </p>
      <div className="flex gap-3 justify-center">
        <button
          onClick={onNext}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
        >
          Get Started →
        </button>
        <button
          onClick={onSkip}
          className="px-6 py-3 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 font-medium"
        >
          Skip
        </button>
      </div>
    </div>
  );
}

function StepChoosePath({
  onSelectKit,
  onImport,
  onScratch,
  onSkip,
}: {
  onSelectKit: (id: string) => void;
  onImport: () => void;
  onScratch: () => void;
  onSkip: () => void;
}) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Choose Your Path</h2>
      <p className="text-gray-600 dark:text-gray-400 mb-6">
        How would you like to start?
      </p>

      {/* Starter Kits */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {STARTER_KITS.map((kit) => (
          <button
            key={kit.id}
            onClick={() => onSelectKit(kit.id)}
            className="text-left p-4 rounded-lg border-2 border-gray-200 dark:border-gray-600
              hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors"
          >
            <div className="text-2xl mb-1">{kit.icon}</div>
            <div className="font-semibold text-gray-900 dark:text-white text-sm">{kit.name}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{kit.description}</div>
            <div className="text-xs text-indigo-600 mt-2">{kit.page_count} sample pages</div>
          </button>
        ))}
      </div>

      {/* Other options */}
      <div className="border-t dark:border-gray-700 pt-4 space-y-2">
        <button
          onClick={onImport}
          className="w-full text-left p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          <span className="text-lg mr-2">📥</span>
          <span className="font-medium text-gray-900 dark:text-white">Import from Obsidian / Markdown</span>
        </button>
        <button
          onClick={onScratch}
          className="w-full text-left p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          <span className="text-lg mr-2">✨</span>
          <span className="font-medium text-gray-900 dark:text-white">Start from scratch</span>
        </button>
      </div>

      <button onClick={onSkip} className="mt-4 text-sm text-gray-400 hover:text-gray-600">
        Skip onboarding
      </button>
    </div>
  );
}

function StepSeeding({ kitName, isPending }: { kitName: string; isPending: boolean }) {
  return (
    <div className="text-center py-8">
      <div className="text-4xl mb-4 animate-bounce">🌱</div>
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
        Setting up {kitName}...
      </h2>
      <p className="text-gray-600 dark:text-gray-400">
        {isPending ? 'Creating sample pages with wiki links...' : 'Almost ready!'}
      </p>
      {isPending && (
        <div className="mt-4 w-48 mx-auto h-1 bg-gray-200 rounded-full overflow-hidden">
          <div className="h-full bg-indigo-600 rounded-full animate-pulse" style={{ width: '60%' }} />
        </div>
      )}
    </div>
  );
}

function StepComplete({ kitName, onFinish }: { kitName: string; onFinish: () => void }) {
  return (
    <div className="text-center">
      <div className="text-6xl mb-4">🎊</div>
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
        You're All Set!
      </h2>
      {kitName && (
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Your <strong>{kitName}</strong> is ready with sample pages and connections.
        </p>
      )}

      <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 mb-6 text-left">
        <h3 className="font-semibold text-indigo-900 dark:text-indigo-300 mb-2">Quick Tips</h3>
        <ul className="space-y-1 text-sm text-indigo-800 dark:text-indigo-400">
          <li>⌨️ <kbd className="px-1 bg-white/50 rounded text-xs">Cmd+K</kbd> — Search & navigate</li>
          <li>⌨️ <kbd className="px-1 bg-white/50 rounded text-xs">Cmd+Shift+N</kbd> — Quick capture</li>
          <li>🔗 Type <code className="bg-white/50 px-1 rounded text-xs">[[page-name]]</code> to link pages</li>
          <li>📊 Check the Graph view to see connections</li>
        </ul>
      </div>

      <button
        onClick={onFinish}
        className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
      >
        Explore Your Wiki →
      </button>
    </div>
  );
}
