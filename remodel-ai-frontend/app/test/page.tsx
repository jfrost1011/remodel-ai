'use client';
import { useEffect, useState } from 'react'
export default function TestPage() {
  const [status, setStatus] = useState('Checking...')
  const [apiUrl, setApiUrl] = useState('')
  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    setApiUrl(url)
    fetch(`${url}/health`)
      .then(res => res.json())
      .then(data => setStatus(`Connected! Status: ${data.status}`))
      .catch(err => setStatus(`Error: ${err.message}`))
  }, [])
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Connection Test</h1>
      <p>API URL: {apiUrl}</p>
      <p>Status: {status}</p>
    </div>
  )
}
