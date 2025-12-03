import React, { useState } from 'react';

export default function ChatInterface() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);

  const ask = async () => {
    if (!question) return;
    setAnswer('Thinking...');
    try {
      const res = await fetch('/api/chat/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, user_id: 'web' })
      });
      const data = await res.json();
      setAnswer(data.answer || 'No answer');
      setSources(data.sources || []);
    } catch (e) {
      setAnswer('Request failed');
      setSources([]);
    }
  };

  return (
    <div className="card">
      <h3>🤖 Chat</h3>
      <input value={question} onChange={(e)=>setQuestion(e.target.value)} placeholder="Ask something about your papers" style={{width:'100%',padding:8}} />
      <button onClick={ask} style={{marginTop:8}}>Ask</button>
      <div style={{marginTop:12}}><strong>Answer:</strong><div>{answer}</div></div>
      {sources.length>0 && (
        <div style={{marginTop:12}}>
          <strong>Sources:</strong>
          {sources.map((s,i)=> (
            <div key={i}>[{s.document_title}] — {s.chunk_text}</div>
          ))}
        </div>
      )}
    </div>
  );
}
