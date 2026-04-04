module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'vault-bg': 'var(--bg)',
        'vault-text': 'var(--text)',
        'vault-heading': 'var(--text-h)',
        'vault-border': 'var(--border)',
        'vault-card': 'var(--code-bg)',
        'vault-muted': 'var(--accent-bg)',
      },
    },
  },
  plugins: [],
};
