import { useNavigate } from 'react-router';
import { useCreateDailyNote } from '../../hooks/useTimeline';

export function DailyNoteButton() {
  const navigate = useNavigate();
  const createMutation = useCreateDailyNote();

  const handleClick = () => {
    createMutation.mutate(undefined, {
      onSuccess: (data) => {
        navigate(`/page/${data.slug}`);
      },
    });
  };

  return (
    <button
      onClick={handleClick}
      disabled={createMutation.isPending}
      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50
        text-white rounded-lg font-medium transition-colors flex items-center gap-2"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
      {createMutation.isPending ? 'Creating...' : "Today's Note"}
    </button>
  );
}
