import { useState } from 'react'
import { api, type Difficulty, type SectionName, type TaskType } from '../api'
import { LISTENING_TASKS, READING_TASKS, SPEAKING_TASKS, SECTION_LABEL, TASK_LABEL, WRITING_TASKS } from '../labels'
import { navigate } from '../route'

type Mode = 'full' | 'section' | 'task'

const DIFFICULTIES: { value: Difficulty; label: string; hint: string }[] = [
  { value: 'beginner', label: 'Beginner', hint: 'about band 2–3' },
  { value: 'intermediate', label: 'Intermediate', hint: 'about band 3.5–4.5' },
  { value: 'advanced', label: 'Advanced', hint: 'about band 5–6' },
]
const AVAILABLE: SectionName[] = ['reading', 'listening', 'writing', 'speaking']
const TASK_OPTIONS: { section: SectionName; task: TaskType }[] = [
  ...READING_TASKS.map((task) => ({ section: 'reading' as const, task })),
  ...LISTENING_TASKS.map((task) => ({ section: 'listening' as const, task })),
  ...SPEAKING_TASKS.map((task) => ({ section: 'speaking' as const, task })),
  ...WRITING_TASKS.map((task) => ({ section: 'writing' as const, task })),
]

export default function Setup() {
  const [mode, setMode] = useState<Mode>('section')
  const [section, setSection] = useState<SectionName>('reading')
  const [task, setTask] = useState<TaskType>('complete_the_words')
  const [difficulty, setDifficulty] = useState<Difficulty>('intermediate')
  const [examMode, setExamMode] = useState<'exam' | 'practice'>('exam')
  const [timed, setTimed] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const start = async () => {
    setBusy(true)
    setError(null)
    try {
      const attempt = await api.createAttempt({
        mode,
        difficulty,
        exam_mode: examMode,
        timed: examMode === 'exam' ? true : timed,
        ...(mode === 'full' ? {} : mode === 'section' ? { section } : { task_type: task }),
      })
      navigate(`/attempt/${attempt.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setBusy(false)
    }
  }

  const radio = 'flex cursor-pointer items-start gap-2 rounded border p-3 has-[:checked]:border-blue-600 has-[:checked]:bg-blue-50'

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="text-3xl font-bold">TOEFL iBT Practice (2026 format)</h1>
        <p className="mt-1 text-slate-600">Every attempt uses newly generated questions. Scores are estimates, not official ETS scores.</p>
      </div>

      <fieldset>
        <legend className="mb-2 font-semibold">What do you want to practice?</legend>
        <div className="grid gap-2 sm:grid-cols-3">
          <label className={radio}>
            <input type="radio" checked={mode === 'full'} onChange={() => setMode('full')} /> <span>Full test <em className="block text-sm text-slate-500">all four sections, no break</em></span>
          </label>
          <label className={radio}>
            <input type="radio" checked={mode === 'section'} onChange={() => setMode('section')} /> <span>One section</span>
          </label>
          <label className={radio}>
            <input type="radio" checked={mode === 'task'} onChange={() => setMode('task')} /> <span>One task type</span>
          </label>
        </div>
        {mode === 'full' ? null : mode === 'section' ? (
          <select className="mt-3 rounded border p-2" value={section} onChange={(e) => setSection(e.target.value as SectionName)}>
            {(Object.keys(SECTION_LABEL) as SectionName[]).map((s) => (
              <option key={s} value={s} disabled={!AVAILABLE.includes(s)}>
                {SECTION_LABEL[s]}{AVAILABLE.includes(s) ? '' : ' (not built yet)'}
              </option>
            ))}
          </select>
        ) : (
          <select className="mt-3 rounded border p-2" value={task} onChange={(e) => setTask(e.target.value as TaskType)}>
            {TASK_OPTIONS.map(({ section: s, task: t }) => (
              <option key={t} value={t}>
                {SECTION_LABEL[s]} · {TASK_LABEL[t]}
              </option>
            ))}
          </select>
        )}
      </fieldset>

      <fieldset>
        <legend className="mb-1 font-semibold">Difficulty</legend>
        <p className="mb-2 text-sm text-slate-500">Sets the starting level. In Reading and Listening, Module 2 then adapts up or down from your Module 1 score.</p>
        <div className="grid gap-2 sm:grid-cols-3">
          {DIFFICULTIES.map((d) => (
            <label key={d.value} className={radio}>
              <input type="radio" checked={difficulty === d.value} onChange={() => setDifficulty(d.value)} />
              <span>{d.label} <em className="block text-sm text-slate-500">{d.hint}</em></span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="mb-2 font-semibold">Mode</legend>
        <div className="grid gap-2 sm:grid-cols-2">
          <label className={radio}>
            <input type="radio" checked={examMode === 'exam'} onChange={() => setExamMode('exam')} />
            <span>Exam <em className="block text-sm text-slate-500">strict timers, no spellcheck</em></span>
          </label>
          <label className={radio}>
            <input type="radio" checked={examMode === 'practice'} onChange={() => setExamMode('practice')} />
            <span>Practice <em className="block text-sm text-slate-500">spellcheck on, timers optional</em></span>
          </label>
        </div>
        {examMode === 'practice' && (
          <label className="mt-3 flex items-center gap-2">
            <input type="checkbox" checked={timed} onChange={(e) => setTimed(e.target.checked)} /> Use timers
          </label>
        )}
      </fieldset>

      {error && <p className="text-red-600">{error}</p>}
      <button className="rounded bg-blue-600 px-6 py-3 text-lg text-white disabled:opacity-50" disabled={busy} onClick={() => void start()}>
        {busy ? 'Starting…' : 'Prepare exam'}
      </button>
    </div>
  )
}
