import { useState } from 'react';
import SessionSelector from './components/SessionSelector';
import BankStatementUpload from './components/BankStatementUpload';

function App() {
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);

  return (
    <div className='min-hscreen bg-gray-100 p-8'>
      <h1 className='text-3xl font-bold mb-6'>AI Accounting Assistant</h1>
      <SessionSelector onSelect={setCurrentSessionId} />
      {currentSessionId && (
        <>
          <div className="mt-4 p-4 bg-green-100 rounded">
            Active Session: {currentSessionId}
          </div>
          <BankStatementUpload sessionId={currentSessionId} />
        </>
      )}
    </div>
  );
}

export default App;