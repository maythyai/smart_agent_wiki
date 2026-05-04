import React from 'react';
import { useDragDrop } from '../hooks/useDragDrop';

interface DropZoneProps {
  children: React.ReactNode;
  onIngestStart?: () => void;
  onIngestComplete?: (count: number) => void;
  onIngestError?: (error: Error) => void;
  className?: string;
}

/**
 * DropZone component for handling file drag-and-drop.
 *
 * Wraps content and provides visual feedback when files are dragged over.
 */
export const DropZone: React.FC<DropZoneProps> = ({
  children,
  onIngestStart,
  onIngestComplete,
  onIngestError,
  className = '',
}) => {
  const { isDragging, handleDragOver, handleDragLeave, handleDrop } = useDragDrop({
    onIngestStart,
    onIngestComplete,
    onIngestError,
    allowedTypes: ['md', 'txt', 'pdf', 'docx', 'html'],
  });

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`dropzone ${isDragging ? 'dropzone-active' : ''} ${className}`}
    >
      {children}
      {isDragging && (
        <div className="dropzone-overlay">
          <div className="dropzone-content">
            <div className="dropzone-icon">📁</div>
            <p>Drop files here to ingest</p>
          </div>
        </div>
      )}
    </div>
  );
};
