import { useParams, useNavigate } from 'react-router';
import { usePage, useUpdatePage, useDeletePage, useUpdateProperties } from '../hooks/usePage';
import { WikiEditorWrapper } from '../components/editor/WikiEditor';
import { useStore } from '../stores';
import { ConfidenceBadge } from '../components/common/ConfidenceBadge';
import { FreshnessBadge } from '../components/common/FreshnessBadge';
import { BacklinksPanel } from '../components/links/BacklinksPanel';
import { RelatedPagesPanel } from '../components/related/RelatedPagesPanel';
import EntityTypeBadge from '../components/entity/EntityTypeBadge';
import PropertiesEditor from '../components/entity/PropertiesEditor';
import { useState, useEffect } from 'react';

/**
 * Page component displays a Wiki page with view/edit modes.
 * Per D-14: Supports view -> edit -> submit workflow.
 * Per D-15: Changes persisted via Page API.
 */
export default function Page() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  // Local state for editor content (断裂点 #4 fix: track content for save)
  const [editorContent, setEditorContent] = useState<string | null>(null);

  // Store state for editor mode
  const mode = useStore((s) => s.mode);
  const setMode = useStore((s) => s.setMode);
  const isDirty = useStore((s) => s.isDirty);
  const setDirty = useStore((s) => s.setDirty);
  const lastSaved = useStore((s) => s.lastSaved);

  // Query and mutation hooks
  const { data: page, isLoading, error } = usePage(slug || '');
  const { mutate: updatePage, isPending: isSaving } = useUpdatePage(slug || '');
  const { mutate: deletePage, isPending: isDeleting } = useDeletePage(slug || '');
  const { mutate: updateProperties, isPending: isSavingProps } = useUpdateProperties(slug || '');

  // Local editable copy of the page's properties; re-syncs when the page
  // reloads (e.g. after a save invalidates and refetches the query).
  const [localProperties, setLocalProperties] = useState<Record<string, unknown>>(
    page?.properties ?? {},
  );
  const [propsSaved, setPropsSaved] = useState(true);

  useEffect(() => {
    setLocalProperties(page?.properties ?? {});
    setPropsSaved(true);
  }, [page?.properties]);

  // Handle save action — 断裂点 #4 fix: actually call updatePage
  const handleSave = (content: string) => {
    updatePage({ content });
  };

  // Track editor content changes for save button
  const handleContentChange = (content: string) => {
    setEditorContent(content);
    setDirty(content !== page?.content);
  };

  // Handle explicit save button click
  const handleSaveClick = () => {
    const content = editorContent ?? page?.content ?? '';
    if (content) {
      handleSave(content);
    }
    setMode('view');
  };

  // Handle edit mode toggle
  const handleEdit = () => {
    setMode('edit');
  };

  // Handle delete with confirmation — wires the previously-unused useDeletePage hook
  const handleDelete = () => {
    if (window.confirm(`Delete "${page?.title ?? slug}"? This cannot be undone.`)) {
      deletePage();
    }
  };

  // Handle Markdown export — browser-side download (works in `saw web`, no Tauri needed)
  const handleExport = () => {
    const content = page?.content ?? '';
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${slug}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Track property edits and persist them via the PATCH /properties endpoint.
  const handlePropertiesChange = (next: Record<string, unknown>) => {
    setLocalProperties(next);
    setPropsSaved(false);
  };

  const handleSaveProperties = () => {
    updateProperties(
      { properties: localProperties },
      { onSuccess: () => setPropsSaved(true) },
    );
  };

  // Handle cancel - revert to view mode
  const handleCancel = () => {
    setMode('view');
    setDirty(false);
  };

  // Handle back navigation
  const handleBack = () => {
    navigate(-1);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold text-red-700">Error Loading Page</h2>
          <p className="text-red-600 mt-1">{error.message}</p>
          <button
            onClick={handleBack}
            className="mt-4 px-4 py-2 bg-red-100 hover:bg-red-200 rounded text-red-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // No page found
  if (!page) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold text-yellow-700">Page Not Found</h2>
          <p className="text-yellow-600 mt-1">The page "{slug}" does not exist.</p>
          <button
            onClick={handleBack}
            className="mt-4 px-4 py-2 bg-yellow-100 hover:bg-yellow-200 rounded text-yellow-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header with title, badges, and actions */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <button
            onClick={handleBack}
            className="text-gray-500 hover:text-gray-700"
            aria-label="Go back"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{page.title}</h1>
        </div>

        {/* Badges row */}
        <div className="flex items-center gap-3 mb-3">
          <EntityTypeBadge typeId={page.entity_type} size="md" />
          <ConfidenceBadge value={page.confidence} />
          <FreshnessBadge value={page.freshness} />
          {isDirty && (
            <span className="text-sm text-orange-600 font-medium">Unsaved changes</span>
          )}
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between border-b pb-3">
          <div className="flex items-center gap-2">
            {mode === 'view' ? (
              <>
                <button
                  onClick={handleEdit}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium"
                >
                  Edit
                </button>
                <button
                  onClick={handleExport}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-200 rounded font-medium"
                  title="Download this page as Markdown"
                >
                  Export
                </button>
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="px-4 py-2 bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-900/30 dark:hover:bg-red-900/50 dark:text-red-300 rounded font-medium disabled:opacity-50"
                >
                  {isDeleting ? 'Deleting...' : 'Delete'}
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded font-medium"
                  disabled={isSaving}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveClick}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-medium disabled:opacity-50"
                  disabled={isSaving || !isDirty}
                >
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </>
            )}
          </div>

          {/* Status info */}
          <div className="text-sm text-gray-500">
            {lastSaved && (
              <span>Last saved: {new Date(lastSaved).toLocaleTimeString()}</span>
            )}
          </div>
        </div>
      </div>

      {/* Editor */}
      <div className="bg-white rounded-lg border shadow-sm">
        <WikiEditorWrapper
          slug={slug || ''}
          initialContent={page.content}
          onSave={handleSave}
          onContentChange={handleContentChange}
          readOnly={mode === 'view'}
        />
      </div>

      {/* Properties Editor */}
      {page.entity_type && page.entity_type !== 'note' && (
        <div className="mt-4 bg-white rounded-lg border shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-500 dark:text-gray-400">
              Properties
            </span>
            {mode === 'edit' && (
              <button
                onClick={handleSaveProperties}
                disabled={isSavingProps || propsSaved}
                className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50"
              >
                {isSavingProps ? 'Saving...' : propsSaved ? 'Saved' : 'Save Properties'}
              </button>
            )}
          </div>
          <PropertiesEditor
            typeId={page.entity_type}
            properties={localProperties}
            onChange={handlePropertiesChange}
            readOnly={mode === 'view'}
          />
        </div>
      )}

      {/* Backlinks Panel */}
      {slug && <BacklinksPanel slug={slug} />}

      {/* Related Pages Panel */}
      {slug && <RelatedPagesPanel slug={slug} />}
    </div>
  );
}