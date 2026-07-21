import { useRef, useEffect, useCallback } from 'react';
import { Editor, rootCtx, defaultValueCtx } from '@milkdown/kit/core';
import { commonmark } from '@milkdown/kit/preset/commonmark';
import { gfm } from '@milkdown/kit/preset/gfm';
import { history } from '@milkdown/kit/plugin/history';
import { listener, listenerCtx } from '@milkdown/kit/plugin/listener';
import { Milkdown, MilkdownProvider, useEditor } from '@milkdown/react';
import { useStore } from '../../stores';

interface WikiEditorProps {
  /** Page slug for identification */
  slug: string;
  /** Initial markdown content */
  initialContent: string;
  /** Callback when content is saved (Ctrl+S or toolbar save) */
  onSave?: (content: string) => void;
  /** Callback when content changes (for dirty tracking) */
  onContentChange?: (content: string) => void;
  /** Whether editor is in read-only mode */
  readOnly?: boolean;
}

/**
 * Milkdown WYSIWYG Markdown editor component.
 * Per D-13: Uses Milkdown for WYSIWYG editing.
 * Per D-14: Supports view/edit/preview modes.
 */
export function WikiEditor({
  slug: _slug,
  initialContent,
  onSave,
  onContentChange,
  readOnly = false,
}: WikiEditorProps) {
  const contentRef = useRef(initialContent);
  const { mode, setDirty, setLastSaved } = useStore();
  const isInitializedRef = useRef(false);

  // Update content reference when props change
  useEffect(() => {
    contentRef.current = initialContent;
  }, [initialContent]);

  // Handle save action
  const handleSave = useCallback(() => {
    if (onSave && contentRef.current) {
      onSave(contentRef.current);
      setLastSaved(new Date().toISOString());
      setDirty(false);
    }
  }, [onSave, setDirty, setLastSaved]);

  // Keyboard shortcut for save (Ctrl/Cmd+S)
  useEffect(() => {
    if (readOnly) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleSave, readOnly]);

  useEditor((root) =>
    Editor.make()
      .config((ctx) => {
        ctx.set(rootCtx, root);
        ctx.set(defaultValueCtx, contentRef.current);

        // Listen for markdown updates to track dirty state
        ctx.get(listenerCtx).markdownUpdated((_ctx, markdown, prevMarkdown) => {
          if (markdown !== prevMarkdown && isInitializedRef.current) {
            setDirty(true);
            contentRef.current = markdown;
            onContentChange?.(markdown);
          }
        });
      })
      .use(commonmark)
      .use(gfm)
      .use(history)
      .use(listener)
  );

  // Mark initialization complete after first render
  useEffect(() => {
    const timer = setTimeout(() => {
      isInitializedRef.current = true;
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  // Read-only mode: disable editing
  const isEditable = !readOnly && mode === 'edit';

  return (
    <div
      className={`wiki-editor ${isEditable ? 'editable' : 'read-only'}`}
      style={{
        minHeight: '400px',
        pointerEvents: isEditable ? 'auto' : 'none',
        opacity: readOnly ? 0.8 : 1,
      }}
    >
      <Milkdown />
    </div>
  );
}

/**
 * Wrapper component with MilkdownProvider.
 * Required for proper React context setup.
 */
export function WikiEditorWrapper(props: WikiEditorProps) {
  return (
    <MilkdownProvider>
      <WikiEditor {...props} />
    </MilkdownProvider>
  );
}

export default WikiEditorWrapper;