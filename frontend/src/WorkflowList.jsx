import React from 'react';

export function WorkflowList({ workflows }) {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Workflows</h2>
      <ul className="space-y-2">
        {workflows && workflows.length > 0 ? (
          workflows.map((wf, i) => (
            <li key={i} className="bg-white dark:bg-gray-800 rounded shadow p-3 border border-gray-200 dark:border-gray-700">
              <span className="font-medium text-gray-900 dark:text-gray-100">{wf.name}</span>
            </li>
          ))
        ) : (
          <li className="text-gray-500">No workflows found.</li>
        )}
      </ul>
    </div>
  );
}
