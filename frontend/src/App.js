import React from 'react';
import DocumentUpload from './components/DocumentUpload';
import DocumentList from './components/DocumentList';
import ChatInterface from './components/ChatInterface';

export default function App() {
  return (
    <div className="container">
      <h1>🔬 Intelligent Research Assistant</h1>
      <div className="grid" style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'16px'}}>
        <div>
          <DocumentUpload />
          <DocumentList />
        </div>
        <div>
          <ChatInterface />
        </div>
      </div>
    </div>
  );
}
