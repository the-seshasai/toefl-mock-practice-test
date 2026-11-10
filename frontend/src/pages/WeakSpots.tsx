import { useEffect, useState } from 'react'
import { api, type Analytics, type Difficulty, type TaskStat } from '../api'
import { SECTION_LABEL, TASK_LABEL } from '../labels'
import { navigate } from '../route'

const LEVELS: Difficulty[] = ['beginner', 'intermediate', 'advanced']
const CATEGORY_LABEL: Record<string, string> = {
  grammar: 'Grammar',
  vocabulary: 'Vocabulary',
  organization: 'Organization',
  task_fulfillment: 'Task fulfillment',
  delivery: 'Delivery',
}

function TrendMark({ trend }: { trend: number | null }) {
  if (trend === null) return <span className="text-slate-400" title="Only one attempt so far">–</span>
  if (trend >= 0.25) return <span className="text-green-700" title={`+${trend} vs earlier attempts`}>▲ {trend.toFixed(1)}</span>
  if (trend <= -0.25) return <span className="text-red-700" title={`${trend} vs earlier attempts`}>▼ {Math.abs(trend).toFixed(1)}</span>
  return <span className="text-slate-500" title="About the same as earlier attempts">≈</span>
}

function BandBar({ stat, weak }: { stat: TaskStat; weak: boolean }) {
  return (
    <div className="flex items-center gap-2" role="meter" aria-valuemin={1} aria-valuemax={6} aria-valuenow={stat.band} aria-label={`${stat.band} of 6`}>
      <div className="h-2 w-32 overflow-hidden rounded bg-slate-200">
        <div className={`h-full ${weak ? 'bg-red-500' : 'bg-blue-600'}`} style={{ width: `${((stat.band - 1) / 5) * 100}%` }} />
      </div>
      <span className="w-8 text-right font-mono text-sm">{stat.band.toFixed(1)}</span>
    </div>
  )
}

export default function WeakSpots() {
  const [data, setData] = useState<Analytics | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [count, setCount] = useState(3)
  const [level, setLevel] = useState<Difficulty | null>(null)
  const [examMode, setExamMode] = useState<'exam' | 'practice'>('practice')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.analytics().then(setData).catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
  }, [])

  if (error) return <p className="text-red-600">{error}</p>
  if (!data) return null
  if (data.tasks.length === 0) return <p className="rounded bg-slate-50 p-4 text-slate-600">Finish a scored practice to see your weakest task types here.</p>

  const chosen = level ?? data.suggested_difficulty ?? 'intermediate'
  const focus = new Set(data.tasks.slice(0, count).map((t) => t.task_type))
  const categories = Object.entries(data.error_categories)

  const start = async () => {
    setBusy(true)
    setError(null)
    try {
      const attempt = await api.startWeakSpots({ difficulty: chosen, exam_mode: examMode, timed: examMode === 'exam', count })
      navigate(`/attempt/${attempt.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setBusy(false)
    }
  }

  return (
    <section className="space-y-4 rounded border p-4" aria-labelledby="weak-heading">
      <div>
        <h2 id="weak-heading" className="text-xl font-semibold">Your weak spots</h2>
        <p className="text-sm text-slate-600">
          Task types ranked by an estimated band that is adjusted for difficulty level and weights recent attempts more. Based on {data.attempts_scored}{' '}
          scored {data.attempts_scored === 1 ? 'attempt' : 'attempts'}. Estimates, not official ETS scores.
        </p>
      </div>

      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b">
            <th className="py-1">Task type</th><th>Estimated band</th><th>Accuracy</th><th>Trend</th><th>Attempts</th>
          </tr>
        </thead>
        <tbody>
          {data.tasks.map((t) => (
            <tr key={t.task_type} className={`border-b ${focus.has(t.task_type) ? 'bg-red-50' : ''}`}>
              <td className="py-1.5">
                {TASK_LABEL[t.task_type]} <span className="text-xs text-slate-500">· {SECTION_LABEL[t.section]}</span>
              </td>
              <td><BandBar stat={t} weak={focus.has(t.task_type)} /></td>
              <td>{Math.round(t.accuracy * 100)}%</td>
              <td><TrendMark trend={t.trend} /></td>
              <td>{t.attempts}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {categories.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold">Most frequent writing and speaking errors (recent attempts)</h3>
          <ul className="mt-1 flex flex-wrap gap-2 text-sm">
            {categories.map(([name, n]) => (
              <li key={name} className="rounded bg-slate-100 px-2 py-1">
                {CATEGORY_LABEL[name] ?? name} <span className="font-semibold">{n}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap items-end gap-4 border-t pt-4">
        <label className="text-sm">
          Task types to drill
          <select className="ml-2 rounded border p-1" value={count} onChange={(e) => setCount(Number(e.target.value))}>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n} disabled={n > data.tasks.length}>{n}</option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Level
          <select className="ml-2 rounded border p-1 capitalize" value={chosen} onChange={(e) => setLevel(e.target.value as Difficulty)}>
            {LEVELS.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Mode
          <select className="ml-2 rounded border p-1" value={examMode} onChange={(e) => setExamMode(e.target.value as 'exam' | 'practice')}>
            <option value="practice">Practice (timers off, replay allowed)</option>
            <option value="exam">Exam (strict timers)</option>
          </select>
        </label>
        <button className="rounded bg-blue-600 px-5 py-2 text-white disabled:opacity-50" disabled={busy} onClick={() => void start()}>
          {busy ? 'Preparing…' : 'Practice my weak spots'}
        </button>
      </div>
    </section>
  )
}
