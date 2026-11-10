import { useEffect, useState } from 'react'
import { api, type HistoryAttempt, type SectionName } from '../api'
import { SECTION_LABEL, TASK_LABEL } from '../labels'
import { navigate } from '../route'
import WeakSpots from './WeakSpots'

const COLORS: Record<SectionName | 'overall', string> = {
  reading: '#2563eb',
  listening: '#16a34a',
  writing: '#d97706',
  speaking: '#9333ea',
  overall: '#0f172a',
}
const SECTIONS = Object.keys(SECTION_LABEL) as SectionName[]

function Chart({ attempts }: { attempts: HistoryAttempt[] }) {
  const pts = [...attempts].reverse() // oldest first
  const W = 640
  const H = 260
  const pad = { l: 36, r: 12, t: 12, b: 24 }
  const x = (i: number) => pad.l + (pts.length < 2 ? (W - pad.l - pad.r) / 2 : (i * (W - pad.l - pad.r)) / (pts.length - 1))
  const y = (b: number) => pad.t + ((6 - b) * (H - pad.t - pad.b)) / 5
  const series: { key: SectionName | 'overall'; label: string; value: (a: HistoryAttempt) => number | null | undefined }[] = [
    { key: 'overall', label: 'Overall (full tests)', value: (a) => a.overall_band },
    ...SECTIONS.map((s) => ({ key: s, label: SECTION_LABEL[s], value: (a: HistoryAttempt) => a.bands[s] })),
  ]
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Estimated band scores over time">
        {[1, 2, 3, 4, 5, 6].map((b) => (
          <g key={b}>
            <line x1={pad.l} x2={W - pad.r} y1={y(b)} y2={y(b)} stroke="#e2e8f0" />
            <text x={pad.l - 6} y={y(b) + 4} textAnchor="end" fontSize="11" fill="#64748b">{b}</text>
          </g>
        ))}
        {series.map(({ key, value }) => {
          const dots = pts.map((a, i) => ({ v: value(a), i })).filter((p): p is { v: number; i: number } => typeof p.v === 'number')
          return (
            <g key={key}>
              <polyline fill="none" stroke={COLORS[key]} strokeWidth={key === 'overall' ? 3 : 1.5} points={dots.map((p) => `${x(p.i)},${y(p.v)}`).join(' ')} />
              {dots.map((p) => (
                <circle key={p.i} cx={x(p.i)} cy={y(p.v)} r={3.5} fill={COLORS[key]}>
                  <title>{`${key}: ${p.v} (attempt #${pts[p.i].id})`}</title>
                </circle>
              ))}
            </g>
          )
        })}
      </svg>
      <ul className="mt-2 flex flex-wrap gap-4 text-sm">
        {series.map((s) => (
          <li key={s.key} className="flex items-center gap-1">
            <span className="inline-block h-2 w-4 rounded" style={{ background: COLORS[s.key] }} /> {s.label}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function History() {
  const [attempts, setAttempts] = useState<HistoryAttempt[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    api.history().then((r) => setAttempts(r.attempts)).catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
  }, [])

  if (error) return <p className="text-red-600">{error}</p>
  if (!attempts) return <p>Loading…</p>
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">History</h1>
      <p className="text-sm text-slate-600">All bands are estimates, not official ETS scores.</p>
      <WeakSpots />
      {attempts.length === 0 ? (
        <p>No scored attempts yet.</p>
      ) : (
        <>
          <Chart attempts={attempts.filter((a) => a.mode === 'full' || a.mode === 'section')} />
          <p className="text-xs text-slate-500">The chart shows full tests and whole sections; single-task and weak-spot sessions appear in the table only.</p>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b">
                <th className="py-2">Date</th><th>Type</th><th>Level</th><th>Bands</th><th>Overall</th><th />
              </tr>
            </thead>
            <tbody>
              {attempts.map((a) => (
                <tr key={a.id} className="border-b">
                  <td className="py-2">{new Date(a.started_at).toLocaleString()}</td>
                  <td>{a.mode === 'full' ? 'Full test' : a.mode === 'section' ? 'Section' : a.mode === 'weak' ? 'Weak spots' : 'Task'} · {a.exam_mode}{a.tasks.length > 0 && <span className="block text-xs text-slate-500">{a.tasks.map((t) => TASK_LABEL[t as keyof typeof TASK_LABEL] ?? t).join(', ')}</span>}</td>
                  <td className="capitalize">{a.difficulty}</td>
                  <td>
                    {Object.entries(a.bands).map(([s, b]) => `${SECTION_LABEL[s as SectionName]} ${b ?? '–'}`).join(', ')}
                  </td>
                  <td>{a.overall_band ?? '–'}</td>
                  <td><button className="text-blue-600 underline" onClick={() => navigate(`/results/${a.id}`)}>View</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
