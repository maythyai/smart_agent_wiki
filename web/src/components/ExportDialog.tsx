import React, { useState } from 'react';
import { useExport } from '../hooks/useExport';
import { useFileDialog } from '../hooks/useFileDialog';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  pageIds: string[];
  onComplete?: (result: { format: string; path: string; count: number }) => void;
}

type ExportFormat = 'markdown' | 'pdf';

/**
 * ExportDialog component for wiki page export.
 *
 * Provides format selection and location picker for exports.
 */
export const ExportDialog: React.FC<ExportDialogProps> = ({
  isOpen,
  onClose,
  pageIds,
  onComplete,
}) => {
  const [format, setFormat] = useState<ExportFormat>('markdown');
  const [selectedPath, setSelectedPath] = useState<string>('');
  const [status, setStatus] = useState<'idle' | 'exporting' | 'success' | 'error'>('idle');

  const exportHook = useExport();
  const fileDialog = useFileDialog();

  if (!isOpen) return null;

  const handleSelectLocation = async () => {
    if (format === 'markdown') {
      const path = await fileDialog.saveFile('wiki-export.md');
      if (path) setSelectedPath(path);
    } else {
      const path = await fileDialog.saveFile('wiki-export.pdf');
      if (path) setSelectedPath(path);
    }
  };

  const handleExport = async () => {
    setStatus('exporting');

    try {
      if (format === 'markdown') {
        const result = await exportHook.exportMarkdown(pageIds, selectedPath);
        if (result) {
          setStatus('success');
          onComplete?.({
            format: 'markdown',
            path: result.path,
            count: result.pages_exported,
          });
        } else {
          setStatus('error');
        }
      } else {
        // PDF exports single page
        const pageId = pageIds[0] || 'wiki-page';
        const path = await exportHook.exportPdf(pageId, selectedPath);
        if (path) {
          setStatus('success');
          onComplete?.({
            format: 'pdf',
            path,
            count: 1,
          });
        } else {
          setStatus('error');
        }
      }
    } catch (err) {
      setStatus('error');
    }
  };

  const handleClose = () => {
    setStatus('idle');
    setSelectedPath('');
    onClose();
  };

  return (
    <div className="export-dialog-overlay">
      <div className="export-dialog">
        <h2 className="export-dialog-title">Export Wiki Pages</h2>

        {/* Format Selection */}
        <div className="export-format-selection">
          <label className="export-format-label">Format:</label>
          <div className="export-format-options">
            <button
              className={`export-format-btn ${format === 'markdown' ? 'active' : ''}`}
              onClick={() => setFormat('markdown')}
            >
              Markdown (.md)
            </button>
            <button
              className={`export-format-btn ${format === 'pdf' ? 'active' : ''}`}
              onClick={() => setFormat('pdf')}
              disabled={pageIds.length > 1}
            >
              PDF (.pdf)
            </button>
          </div>
          {pageIds.length > 1 && format === 'pdf' && (
            <p className="export-format-note">PDF export supports single page only</p>
          )}
        </div>

        {/* Page Count */}
        <div className="export-page-count">
          <span>{pageIds.length} pages selected</span>
        </div>

        {/* Location Selection */}
        <div className="export-location">
          <label className="export-location-label">Save to:</label>
          <div className="export-location-input">
            <input
              type="text"
              value={selectedPath}
              onChange={(e) => setSelectedPath(e.target.value)}
              placeholder="Select export location..."
              className="export-location-text"
            />
            <button
              onClick={handleSelectLocation}
              className="export-location-btn"
              disabled={exportHook.isLoading}
            >
              Browse...
            </button>
          </div>
        </div>

        {/* Progress/Status */}
        {status === 'exporting' && (
          <div className="export-progress">
            <span className="export-spinner">⏳</span>
            <span>Exporting...</span>
          </div>
        )}

        {status === 'success' && (
          <div className="export-success">
            <span className="export-icon">✓</span>
            <span>Export completed successfully!</span>
          </div>
        )}

        {status === 'error' && (
          <div className="export-error">
            <span className="export-icon">✗</span>
            <span>Export failed. Please try again.</span>
            {exportHook.error && <p className="export-error-msg">{exportHook.error}</p>}
          </div>
        )}

        {/* Actions */}
        <div className="export-actions">
          <button
            onClick={handleClose}
            className="export-btn-cancel"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            className="export-btn-confirm"
            disabled={status === 'exporting' || !selectedPath}
          >
            Export
          </button>
        </div>
      </div>
    </div>
  );
};