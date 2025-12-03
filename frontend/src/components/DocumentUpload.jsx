import React, { useState } from 'react';

export default function DocumentUpload() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');

  const onUpload = async () => {
    if (!file) return;
    setStatus('Uploading...');
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch('/api/documents/upload', { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) {
        const msg = data?.detail || 'Upload failed';
        setStatus(msg);
        return;
      }
      setStatus(`Uploaded: ${data.title} (chunks: ${data.chunks_processed})`);
    } catch (e) {
      setStatus('Upload failed');
    }
  };

  return (
    <div className="card">
      <h3>📤 Upload PDF</h3>
      <input type="file" accept="application/pdf" onChange={(e)=>setFile(e.target.files[0])} />
      <button onClick={onUpload} style={{marginLeft:8}}>Upload</button>
      <div>{status}</div>
    </div>
  );
}
