import './tailwind.css'
import { WorkflowList } from './WorkflowList'

function App() {
  // Example workflows for demo
  const workflows = [
    { name: 'Data Ingestion Pipeline' },
    { name: 'ML Model Training' },
    { name: 'Report Generation' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Workflow Manager</h1>
      </header>
      <main className="max-w-2xl mx-auto py-8">
        <WorkflowList workflows={workflows} />
      </main>
    </div>
  );
}

export default App
