import React from 'react';

export function CategorySidebar({ categories, selected, onSelect }) {
  return (
    <aside className="w-64 bg-vault-card border-r border-vault-border p-4 min-h-screen">
      <h2 className="text-xl font-bold mb-4 text-vault-heading">Categories</h2>
      <ul className="space-y-2">
        {categories.map((cat) => (
          <li key={cat}
              className={`cursor-pointer px-3 py-2 rounded hover:bg-vault-accent-bg ${selected === cat ? 'bg-vault-accent-bg text-vault-accent font-semibold' : 'text-vault-text'}`}
              onClick={() => onSelect(cat)}>
            {cat}
          </li>
        ))}
      </ul>
    </aside>
  );
}
