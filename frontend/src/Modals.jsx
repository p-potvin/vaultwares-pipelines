import React, { useState } from 'react';

export function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
      <div className="bg-vault-card rounded-lg shadow-lg p-6 min-w-[320px] max-w-lg relative">
        <button className="absolute top-2 right-2 text-vault-muted" onClick={onClose}>&times;</button>
        <h3 className="text-xl font-bold mb-4 text-vault-heading">{title}</h3>
        {children}
      </div>
    </div>
  );
}

// Example usage for Create, Import, Export, Restore modals
export function CreateWorkflowModal(props) {
  return <Modal {...props} title="Create Workflow">{/* form here */}</Modal>;
}
export function ImportWorkflowModal(props) {
  return <Modal {...props} title="Import Workflow">{/* form here */}</Modal>;
}
export function ExportWorkflowModal(props) {
  return <Modal {...props} title="Export Workflows">{/* export UI here */}</Modal>;
}
export function RestoreBackupModal(props) {
  return <Modal {...props} title="Restore Backup">{/* restore UI here */}</Modal>;
}
