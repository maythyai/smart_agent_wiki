import { useState } from 'react';
import { MobileDrawer } from './MobileDrawer';

/**
 * MobileNav shows hamburger button only on screens <768px.
 * Per D-04: Navigation collapses to hamburger on screens <768px.
 * Per D-10: Touch targets minimum 44x44px.
 */
export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Hamburger button - only visible <768px */}
      <button
        className="md:hidden p-2 rounded-lg hover:bg-gray-100 touch-manipulation"
        onClick={() => setIsOpen(true)}
        aria-label="Open navigation menu"
        style={{ minWidth: '44px', minHeight: '44px' }}
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <MobileDrawer isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}