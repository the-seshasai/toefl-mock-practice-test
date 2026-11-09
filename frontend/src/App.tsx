import { useEffect, useState } from 'react'

interface Health {
  status: string
  llm_provider: string
  sections: string[]
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json() as Promise<Health>)
      .then(setHealth)
      .catch((e: unknown) => setError(String(e)))
  }, [])

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-3xl font-bold">TOEFL iBT Practice (2026 format)</h1>
      <p className="mt-2 text-slate-600">Scores in this app are estimates, not official ETS scores.</p>
      <section className="mt-6 rounded border border-slate-300 p-4">
        <h2 className="font-semibold">Backend status</h2>
        {error && <p className="text-red-600">Backend unreachable: {error}</p>}
        {health && (
          <p>
            {health.status} · LLM: {health.llm_provider} · {health.sections.join(' → ')}
          </p>
        )}
        {!health && !error && <p>Checking…</p>}
      </section>
    </main>
  )
}
