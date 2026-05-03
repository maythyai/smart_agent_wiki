/**
 * OAuth Status Section
 * Per UI-SPEC.md 2.1, 3.1, 3.3 and D-15-D-17: OAuth status badge and re-authorize button.
 */

import { useState } from 'react';

interface OAuthStatusSectionProps {
  status: 'connected' | 'expiring' | 'expired';
  expiresInDays: number | null;
  onReauthorize: () => void;
  loading?: boolean;
}

// Status badge styling
const STATUS_STYLES = {
  connected: {
    badge: 'bg-green-500',
    text: 'Connected',
  },
  expiring: {
    badge: 'bg-yellow-500',
    text: 'Expires soon',
  },
  expired: {
    badge: 'bg-red-500',
    text: 'Token expired',
  },
};

// Button text based on status
const BUTTON_TEXT = {
  connected: 'Refresh Token',
  expiring: 'Re-authorize',
  expired: 'Re-authorize Now',
};

export function OAuthStatusSection({
  status,
  expiresInDays,
  onReauthorize,
  loading = false,
}: OAuthStatusSectionProps) {
  const [isReauthorizing, setIsReauthorizing] = useState(false);

  // Determine if this platform uses OAuth
  // Note: Platform detection would typically come from props or context
  // For now, we'll show this section only when called with valid status

  const handleReauthorize = async () => {
    setIsReauthorizing(true);
    try {
      await onReauthorize();
    } finally {
      setIsReauthorizing(false);
    }
  };

  const styles = STATUS_STYLES[status];
  const buttonText = BUTTON_TEXT[status];
  const isLoading = loading || isReauthorizing;

  // Status description
  const getStatusDescription = () => {
    if (status === 'connected' && expiresInDays !== null) {
      return `Expires in ${expiresInDays} day${expiresInDays !== 1 ? 's' : ''}`;
    }
    if (status === 'expiring' && expiresInDays !== null) {
      return `Expires in ${expiresInDays} day${expiresInDays !== 1 ? 's' : ''}`;
    }
    if (status === 'expired') {
      return 'Token expired — re-authorize now';
    }
    return '';
  };

  return (
    <section className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        OAuth Status
      </h2>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {/* Status badge */}
        <div className="flex items-center gap-3">
          <span
            className={`w-3 h-3 rounded-full ${styles.badge}`}
            aria-hidden="true"
          />
          <div>
            <span className="text-sm font-medium text-gray-900">
              {styles.text}
            </span>
            {getStatusDescription() && (
              <span className="text-sm text-gray-500 ml-2">
                ({getStatusDescription()})
              </span>
            )}
          </div>
        </div>

        {/* Re-authorize button */}
        <button
          onClick={handleReauthorize}
          disabled={isLoading}
          className={`
            px-4 py-2 text-sm font-medium rounded-lg
            transition-colors
            ${status === 'expired'
              ? 'bg-red-600 text-white hover:bg-red-700'
              : 'bg-blue-600 text-white hover:bg-blue-700'
            }
            focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
            disabled:opacity-50 disabled:cursor-not-allowed
            min-w-[140px]
          `}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <svg
                className="animate-spin w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Re-authorizing...
            </span>
          ) : (
            buttonText
          )}
        </button>
      </div>
    </section>
  );
}

/**
 * Helper to determine OAuth status from token expiry.
 */
export function getOAuthStatus(expiresAt: string | null): {
  status: 'connected' | 'expiring' | 'expired';
  expiresInDays: number | null;
} {
  if (!expiresAt) {
    return { status: 'expired', expiresInDays: null };
  }

  const expiry = new Date(expiresAt);
  const now = new Date();
  const diffMs = expiry.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays <= 0) {
    return { status: 'expired', expiresInDays: 0 };
  }
  if (diffDays <= 7) {
    return { status: 'expiring', expiresInDays: diffDays };
  }
  return { status: 'connected', expiresInDays: diffDays };
}