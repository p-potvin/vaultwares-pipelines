import React from 'react';

export function WorkflowList({ workflows }) {
  return (
    <div className="p-4 bg-vault-bg text-vault-text">
      <h2 className="text-2xl font-bold mb-4 text-vault-heading">Workflows</h2>
      <ul className="space-y-2">
        {workflows && workflows.length > 0 ? (
          workflows.map((wf, i) => (
            <li key={i} className="bg-vault-card rounded shadow p-3 border border-vault-border">
              <span className="font-medium text-vault-text-h">{wf.name}</span>
            </li>
          ))
        ) : (
          <li className="text-vault-muted">No workflows found.</li>
        )}
      </ul>
    </div>
  );
}
