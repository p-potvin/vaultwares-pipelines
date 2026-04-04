import './tailwind.css';
import '../vault-themes/README.md'; // Placeholder: import theme info for reference
import { WorkflowList } from './WorkflowList';

function App() {
  // Example workflows for demo
  const workflows = [
    { name: 'Data Ingestion Pipeline' },
    { name: 'ML Model Training' },
    { name: 'Report Generation' },
  ];

  return (
    <div className="min-h-screen bg-vault-bg text-vault-text">
      <header className="p-4 border-b border-vault-border bg-vault-header">
        <h1 className="text-3xl font-bold text-vault-heading">Workflow Manager</h1>
      </header>
      <main className="max-w-2xl mx-auto py-8">
        <WorkflowList workflows={workflows} />
      </main>
    </div>
  );
}

export default App;
