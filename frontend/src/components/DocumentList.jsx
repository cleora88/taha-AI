import React, { useEffect, useState } from 'react';

export default function DocumentList() {
  const [docs, setDocs] = useState([]);

  const load = async () => {
    const res = await fetch('/api/documents/');
    const data = await res.json();
    setDocs(data.documents || []);
  };

  useEffect(()=>{ load(); }, []);

  return (
    <div className="card">
      <h3>📚 Documents</h3>
      {docs.length === 0 ? (<div>No documents yet.</div>) : (
        docs.map(d => (
          <div key={d.document_id}>
            <strong>{d.title}</strong> — {new Date(d.upload_date).toLocaleString()} — chunks: {d.total_chunks}
          </div>
        ))
      )}
      <button onClick={load} style={{marginTop:8}}>Refresh</button>
    </div>
  );
}
