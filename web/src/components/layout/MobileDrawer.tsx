import { NavLink } from 'react-router';
import { useEffect, useRef } from 'react';

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const navLinks = [
  { to: '/search', label: 'Search' },
  { to: '/graph', label: 'Graph' },
  { to: '/dashboard', label: 'Dashboard' },
];

/**
 * MobileDrawer slides in from left with navigation links.
 * Per D-05: Hamburger menu slides from left (drawer pattern).
 * Per D-10: Touch targets minimum 44x44px.
 * Per D-11: Swipe to dismiss support.
 * Per D-12: touch-action: manipulation prevents double-tap zoom.
 */
export function MobileDrawer({ isOpen, onClose }: MobileDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  // Swipe to close
  useEffect(() => {
    if (!isOpen || !drawerRef.current) return;

    let startX = 0;
    const handleTouchStart = (e: TouchEvent) => {
      startX = e.touches[0].clientX;
    };
    const handleTouchMove = (e: TouchEvent) => {
      const diff = e.touches[0].clientX - startX;
      if (diff > 50) onClose(); // Swipe right to close
    };

    drawerRef.current.addEventListener('touchstart', handleTouchStart);
    drawerRef.current.addEventListener('touchmove', handleTouchMove);
    return () => {
      drawerRef.current?.removeEventListener('touchstart', handleTouchStart);
      drawerRef.current?.removeEventListener('touchmove', handleTouchMove);
    };
  }, [isOpen, onClose]);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/50 z-40 transition-opacity duration-300 md:hidden
          ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <nav
        ref={drawerRef}
        className={`fixed left-0 top-0 h-full w-72 bg-white z-50 shadow-xl
          transform transition-transform duration-300 ease-out md:hidden
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
        aria-label="Mobile navigation"
      >
        {/* Header with close button */}
        <div className="flex items-center justify-between p-4 border-b">
          <span className="font-bold text-lg">Menu</span>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 touch-manipulation"
            aria-label="Close navigation menu"
            style={{ minWidth: '44px', minHeight: '44px' }}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation links */}
        <div className="p-4">
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={onClose}
              className={({ isActive }) =>
                `block py-3 px-4 rounded-lg mb-2 transition-colors touch-manipulation
                  ${isActive
                    ? 'bg-blue-50 text-blue-600 font-medium'
                    : 'text-gray-700 hover:bg-gray-50'
                  }`
              }
              style={{ minHeight: '48px' }}
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </>
  );
}