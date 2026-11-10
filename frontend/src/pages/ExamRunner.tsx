import { useCallback, useEffect, useState, type ComponentType } from 'react'
import { api, type Attempt, type Run, type SectionName, type SectionStatus } from '../api'
import MicCheck from '../components/MicCheck'
import { formatBudget, SECTION_LABEL, TASK_LABEL } from '../labels'
import { navigate } from '../route'
import ListeningTask from '../sections/Listening/ListeningTask'
import ReadingTask from '../sections/Reading/ReadingTask'
import SpeakingTask from '../sections/Speaking/SpeakingTask'
import TaskRunner from '../sections/TaskRunner'
import type { TaskProps } from '../sections/types'
import WritingTask from '../sections/Writing/WritingTask'

const POLL_MS = 1500
const FINISHED = ['scoring', 'scored', 'scoring_failed']

const TASK_RENDERERS: Record<SectionName, ComponentType<TaskProps>> = {
  listening: ListeningTask,
  reading: ReadingTask,
  speaking: SpeakingTask,
  writing: WritingTask,
}

interface RunState {
  section: SectionName
  run: Run
  offsetMs: number
}

export default function ExamRunner({ attemptId }: { attemptId: number }) {
  const [attempt, setAttempt] = useState<Attempt | null>(null)
  const [runState, setRunState] = useState<RunState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [micOk, setMicOk] = useState(false)
  const [submitted, setSubmitted] = useState<SectionName | null>(null)

  const sections = attempt?.sections ?? []
  // The active section is the first one that has not been submitted yet. When none is left, the exam is over.
  const activeIndex = sections.findIndex((s) => !FINISHED.includes(s.status))
  const section: SectionStatus | undefined = sections[activeIndex]
  const status = section?.status
  const name = section?.section

  const refresh = useCallback(async () => {
    try {
      setAttempt(await api.getAttempt(attemptId))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }, [attemptId])

  const loadRun = useCallback(
    (sectionName: SectionName) =>
      api.getRun(attemptId, sectionName).then((run) => setRunState({ section: sectionName, run, offsetMs: Date.parse(run.server_now) - Date.now() })),
    [attemptId],
  )

  // Poll: later sections and Module 2 are prepared in the background while earlier work is under way.
  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const a = await api.getAttempt(attemptId)
        if (!cancelled) setAttempt(a)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      }
    }
    void load()
    const id = window.setInterval(() => void load(), POLL_MS)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [attemptId])

  useEffect(() => {
    if (attempt && activeIndex === -1) navigate(`/results/${attemptId}`)
  }, [attempt, activeIndex, attemptId])

  // Resume after a refresh, and pick up Module 2 once it opens.
  useEffect(() => {
    if (status === 'in_progress' && name && submitted !== name && (!runState || runState.section !== name)) {
      loadRun(name).catch((e: unknown) => setError(String(e)))
    }
  }, [status, name, submitted, runState, loadRun])

  if (error) return <p className="text-red-600">Error: {error}</p>
  if (!attempt || !section || !name) return <p>Loading…</p>

  const full = attempt.mode === 'full'
  const progress = full && (
    <ol className="mb-6 flex gap-2 text-sm" aria-label="Test progress">
      {sections.map((s, i) => (
        <li
          key={s.section}
          className={`rounded px-3 py-1 ${i < activeIndex ? 'bg-green-100 text-green-800' : i === activeIndex ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500'}`}
        >
          {i < activeIndex ? '✓ ' : ''}
          {SECTION_LABEL[s.section]}
        </li>
      ))}
    </ol>
  )

  if (status === 'generating')
    return (
      <div className="py-16 text-center">
        {progress}
        <p className="text-xl font-semibold">{activeIndex > 0 ? `Preparing the ${SECTION_LABEL[name]} section…` : `Preparing your ${SECTION_LABEL[name]} exam…`}</p>
        <p className="mt-2 text-slate-600">Generating fresh, unique questions. This usually takes a minute or two.</p>
      </div>
    )

  if (status === 'failed')
    return (
      <div className="space-y-3">
        <p className="text-red-600">Could not prepare the {SECTION_LABEL[name]} section: {section.error ?? 'unknown error'}</p>
        <button className="rounded border px-4 py-2" onClick={() => navigate('/')}>
          Back to setup
        </button>
      </div>
    )

  if (status === 'preparing_next' && !runState)
    return (
      <div className="py-16 text-center">
        {progress}
        <p className="text-xl font-semibold">Preparing Module 2…</p>
        <p className="mt-2 text-slate-600">Your time has not started.</p>
      </div>
    )

  if (status === 'ready')
    return (
      <div className="space-y-6">
        {progress}
        <h1 className="text-2xl font-bold">
          {SECTION_LABEL[name]} section{full && ` (${activeIndex + 1} of ${sections.length})`}
        </h1>
        {section.stage_count > 1 && (
          <p className="rounded bg-blue-50 p-3 text-sm text-blue-900">
            This section is adaptive. Module 1 comes first; based on your answers, Module 2 will be easier or harder.
          </p>
        )}
        <ul className="space-y-1">
          {section.tasks.map((t) => (
            <li key={t.task_type}>
              <strong>{TASK_LABEL[t.task_type]}</strong> — {t.count} {t.count === 1 ? 'item' : 'items'}
              {attempt.timed && `, ${formatBudget(t.budget_seconds)}`}
            </li>
          ))}
        </ul>
        <ul className="list-disc space-y-1 pl-6 text-slate-700">
          <li>{attempt.timed ? 'Each task has its own timer. When it ends, you move on automatically.' : 'Timers are off for this practice run.'}</li>
          <li>You cannot go back to a task, a module or a section once it ends.</li>
          <li>Your answers are saved automatically.</li>
          {full && <li>There is no break between sections in the full test.</li>}
          {name === 'speaking' && (
            <li>{attempt.exam_mode === 'exam' ? 'Each question plays once and you get one attempt per response. Recording starts automatically.' : 'Practice mode: you can re-record and play back your answers.'}</li>
          )}
          {name === 'listening' && (
            <li>{attempt.exam_mode === 'exam' ? 'Each audio clip plays only once, so be ready before you press Play.' : 'Practice mode: you may replay audio.'}</li>
          )}
        </ul>
        {section.warnings.length > 0 && <p className="rounded bg-amber-50 p-3 text-sm text-amber-800">Note: {section.warnings.join('; ')}</p>}
        {name === 'speaking' && <MicCheck onResult={setMicOk} />}
        <button
          className="rounded bg-blue-600 px-6 py-3 text-lg text-white disabled:opacity-50"
          disabled={name === 'speaking' && !micOk}
          onClick={() => {
            void api
              .start(attemptId, name)
              .then(() => Promise.all([refresh(), loadRun(name)]))
              .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
          }}
        >
          Start {SECTION_LABEL[name]}
        </button>
      </div>
    )

  const live = runState && ['in_progress', 'preparing_next'].includes(runState.run.status)
  if ((status === 'in_progress' || status === 'preparing_next') && runState && live && runState.section === name) {
    return (
      <>
        {progress}
        <TaskRunner
          key={name}
          attemptId={attemptId}
          section={name}
          examMode={attempt.exam_mode === 'exam'}
          initialRun={runState.run}
          initialOffsetMs={runState.offsetMs}
          onDone={() => {
            setSubmitted(name)
            setRunState(null)
            void refresh()
          }}
          Task={TASK_RENDERERS[name]}
        />
      </>
    )
  }

  return <p>Loading…</p>
}
