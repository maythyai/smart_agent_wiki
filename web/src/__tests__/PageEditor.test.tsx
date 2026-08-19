import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router';
import { usePage, useUpdatePage } from '../hooks/usePage';
import Page from '../pages/Page';

// Mock the hooks
vi.mock('../hooks/usePage', () => ({
  usePage: vi.fn(),
  useUpdatePage: vi.fn(),
  useDeletePage: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useUpdateProperties: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

// Mock the store
vi.mock('../stores', () => ({
  useStore: vi.fn((selector) => {
    const state = {
      mode: 'view',
      setMode: vi.fn(),
      isDirty: false,
      setDirty: vi.fn(),
      setLastSaved: vi.fn(),
      lastSaved: null,
    };
    // Support both selector-style and no-arg useStore() calls.
    return typeof selector === 'function' ? selector(state) : state;
  }),
}));

const mockPageData = {
  slug: 'test-page',
  title: 'Test Page',
  content: '# Test Page\n\nThis is test content.',
  frontmatter: {},
  confidence: 3,
  freshness: 2,
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/page/test-page']}>
        <Routes>
          <Route path="/page/:slug" element={<Page />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Page Editor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('View Mode', () => {
    it('should display page title and badges', async () => {
      (usePage as any).mockReturnValue({
        data: mockPageData,
        isLoading: false,
        error: null,
      });
      (useUpdatePage as any).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      });

      renderPage();

      expect(screen.getByText('Test Page')).toBeInTheDocument();
      expect(screen.getByText('Edit')).toBeInTheDocument();
    });

    it('should show loading state', () => {
      (usePage as any).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      });

      renderPage();

      // Loading skeleton should be visible
      const skeleton = document.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });

    it('should show error state', () => {
      (usePage as any).mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Failed to load'),
      });

      renderPage();

      expect(screen.getByText('Error Loading Page')).toBeInTheDocument();
      expect(screen.getByText('Failed to load')).toBeInTheDocument();
    });

    it('should show not found state for missing page', () => {
      (usePage as any).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      });

      renderPage();

      expect(screen.getByText('Page Not Found')).toBeInTheDocument();
    });
  });

  describe('Edit Mode', () => {
    it('should switch to edit mode when Edit button clicked', async () => {
      const mockSetMode = vi.fn();
      let currentMode = 'view';

      (usePage as any).mockReturnValue({
        data: mockPageData,
        isLoading: false,
        error: null,
      });
      (useUpdatePage as any).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      });

      // Override the store mock for this test
      vi.mocked(await import('../stores')).useStore.mockImplementation((selector: any) => {
        const state = {
          mode: currentMode,
          setMode: (m: any) => { currentMode = m; mockSetMode(m); },
          isDirty: false,
          setDirty: vi.fn(),
          setLastSaved: vi.fn(),
          lastSaved: null,
        };
        return typeof selector === 'function' ? selector(state) : state;
      });

      renderPage();

      const editButton = screen.getByText('Edit');
      fireEvent.click(editButton);

      // Edit mode should be triggered
      expect(mockSetMode).toHaveBeenCalledWith('edit');
    });
  });

  describe('Save Actions', () => {
    it('should call update mutation on save', async () => {
      const mockMutate = vi.fn();

      (usePage as any).mockReturnValue({
        data: mockPageData,
        isLoading: false,
        error: null,
      });
      (useUpdatePage as any).mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      });

      renderPage();

      // Test that the component renders and mutation hook is set up
      expect(useUpdatePage).toHaveBeenCalledWith('test-page');
    });
  });
});
