import React, { useState } from 'react';

export function WorkflowList({ workflows, onPin, onFavorite, filter, sortKey, onSort, onFilter }) {
  const [selected, setSelected] = useState([]);

  const handleSelect = (wf) => {
    setSelected((prev) => prev.includes(wf) ? prev.filter(x => x !== wf) : [...prev, wf]);
  };

  const filtered = workflows.filter(wf => !filter || wf.category === filter);
  const sorted = [...filtered].sort((a, b) => {
    if (!sortKey) return 0;
    if (a[sortKey] < b[sortKey]) return -1;
    if (a[sortKey] > b[sortKey]) return 1;
    return 0;
  });

  return (
    <div className="p-4 bg-vault-bg text-vault-text">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-vault-heading">Workflows</h2>
        <div>
          <select className="mr-2 border rounded px-2 py-1" value={filter} onChange={e => onFilter(e.target.value)}>
            <option value="">All</option>
            {/* Add category options dynamically */}
          </select>
          <select className="border rounded px-2 py-1" value={sortKey} onChange={e => onSort(e.target.value)}>
            <option value="">Sort</option>
            <option value="name">Name</option>
            <option value="created">Created</option>
          </select>
        </div>
      </div>
      <ul className="space-y-2">
        {sorted.length > 0 ? (
          sorted.map((wf, i) => (
            <li key={i} className={`bg-vault-card rounded shadow p-3 border border-vault-border flex items-center justify-between ${selected.includes(wf) ? 'ring-2 ring-vault-accent' : ''}`}>
              <div className="flex items-center gap-2">
                <input type="checkbox" checked={selected.includes(wf)} onChange={() => handleSelect(wf)} />
                <span className="font-medium text-vault-text-h">{wf.name}</span>
                <button className={`ml-2 ${wf.pinned ? 'text-vault-accent' : 'text-vault-muted'}`} onClick={() => onPin(wf)} title="Pin">
                  📌
                </button>
                <button className={`ml-1 ${wf.favorite ? 'text-yellow-400' : 'text-vault-muted'}`} onClick={() => onFavorite(wf)} title="Favorite">
                  ★
                </button>
              </div>
            </li>
          ))
        ) : (
          <li className="text-vault-muted">No workflows found.</li>
        )}
      </ul>
      <div className="mt-4 flex gap-2">
        <button className="px-3 py-1 rounded bg-vault-accent text-white" disabled={selected.length === 0}>Export</button>
        <button className="px-3 py-1 rounded bg-vault-accent text-white" disabled={selected.length === 0}>Backup</button>
      </div>
    </div>
  );
}
