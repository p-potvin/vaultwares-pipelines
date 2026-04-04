import React, { useState } from 'react';

export function ExecutionToggle({ value, onChange }) {
  return (
    <div className="flex items-center gap-2 p-2">
      <span className="text-vault-muted">Run on:</span>
      <button
        className={`px-3 py-1 rounded ${value === 'local' ? 'bg-vault-accent text-white' : 'bg-vault-card text-vault-text'}`}
        onClick={() => onChange('local')}
      >
        Local
      </button>
      <button
        className={`px-3 py-1 rounded ${value === 'nim' ? 'bg-vault-accent text-white' : 'bg-vault-card text-vault-text'}`}
        onClick={() => onChange('nim')}
      >
        NIM VM
      </button>
    </div>
  );
}
