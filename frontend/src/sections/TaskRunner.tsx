import { useCallback, useEffect, useRef, useState, type ComponentType } from 'react'
import { api, ApiError, type Answer, type Run, type SectionName } from '../api'
import Timer from '../components/Timer'
import { formatBudget, SECTION_LABEL, TASK_LABEL } from '../labels'
import type { TaskProps } from './types'

interface Props {
  attemptId: number
  section: SectionName
  examMode: boolean
  initialRun: Run
  initialOffsetMs: number
  onDone: () => void
  /** Section-specific renderer for the current task */
  Task: ComponentType<TaskProps>
}

const AUTOSAVE_MS = 2000

/** Shared exam chrome: per-task timer, autosave, confirmation before leaving a task, and submit. */
export default function TaskRunner({ attemptId, section, examMode, initialRun, initialOffsetMs, onDone, Task }: Props) {
  const [run, setRun] = useState(initialRun)
  const [answers, setAnswers] = useState<Record<number, Answer>>(() => answersFrom(initialRun))
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)
  const [offsetMs, setOffsetMs] = useState(initialOffsetMs)
  const dirty = useRef(new Map<number, Answer>())

  const flush = useCallback(
    async (keepalive = false) => {
      const pending = [...dirty.current.entries()]
      await Promise.all(
        pending.map(async ([id, answer]) => {
          try {
            await api.save(attemptId, id, answer, keepalive)
            if (dirty.current.get(id) === answer) dirty.current.delete(id)
          } catch (e) {
            if (e instanceof ApiError && e.status === 409) dirty.current.delete(id) // locked by the server
          }
        }),
      )
    },
    [attemptId],
  )

  useEffect(() => {
    const id = window.setInterval(() => void flush(), AUTOSAVE_MS)
    const onUnload = () => void flush(true)
    window.addEventListener('beforeunload', onUnload)
    return () => {
      window.clearInterval(id)
      window.removeEventListener('beforeunload', onUnload)
    }
  }, [flush])

  const adopt = useCallback(
    (next: Run) => {
      setOffsetMs(Date.parse(next.server_now) - Date.now())
      setRun(next)
      setAnswers((prev) => ({ ...answersFrom(next), ...prev }))
      setConfirming(false)
      if (next.status !== 'in_progress' && next.status !== 'preparing_next') onDone()
    },
    [onDone],
  )

  // Module 2 is still being prepared: wait here (the clock has not started) until it opens.
  const waiting = run.status === 'preparing_next'
  useEffect(() => {
    if (!waiting) return
    const id = window.setInterval(() => {
      api.getRun(attemptId, section).then(adopt).catch(() => undefined)
    }, 2000)
    return () => window.clearInterval(id)
  }, [waiting, attemptId, section, adopt])

  const move = useCallback(
    async (submit: boolean) => {
      if (busy) return
      setBusy(true)
      try {
        await flush()
        adopt(submit ? await api.submit(attemptId, section) : await api.advance(attemptId, section))
      } finally {
        setBusy(false)
      }
    },
    [adopt, attemptId, busy, flush, section],
  )

  const setAnswer = (responseId: number, answer: Answer) => {
    dirty.current.set(responseId, answer)
    setAnswers((prev) => ({ ...prev, [responseId]: answer }))
  }

  const setLocalAnswer = (responseId: number, answer: Answer) => setAnswers((prev) => ({ ...prev, [responseId]: answer }))

  if (waiting) {
    return (
      <div className="py-16 text-center">
        <p className="text-xl font-semibold">Preparing Module 2…</p>
        <p className="mt-2 text-slate-600">Your next questions are being finalized. Your time has not started.</p>
      </div>
    )
  }

  const task = run.tasks[run.current_task]
  if (!task) return null
  const isLast = run.current_task === run.tasks.length - 1
  const isRouterEnd = isLast && run.stage_count > 1 && run.stage === 'router'
  const isFinal = isLast && !isRouterEnd

  return (
    <div className="mx-auto max-w-5xl">
      <header className="flex items-center justify-between border-b pb-3">
        <div>
          <h1 className="text-xl font-bold">
            {SECTION_LABEL[section]} · {run.stage_label && `${run.stage_label} · `}
            {TASK_LABEL[task.task_type]}
          </h1>
          <p className="text-sm text-slate-500">
            Task {run.current_task + 1} of {run.tasks.length} · {formatBudget(task.budget_seconds)} · answers save automatically
          </p>
        </div>
        <Timer deadline={run.task_deadline} offsetMs={offsetMs} onExpire={() => void move(isFinal)} />
      </header>

      <div className="mt-6">
        <Task key={`${run.stage}-${run.current_task}`} attemptId={attemptId} run={run} examMode={examMode} answers={answers} setAnswer={setAnswer} setLocalAnswer={setLocalAnswer} />
      </div>

      <footer className="mt-8 flex justify-end gap-3 border-t pt-4">
        {confirming ? (
          <>
            <span className="self-center text-sm text-slate-600">
              {isRouterEnd
                ? 'You cannot return to Module 1. Your answers decide how Module 2 is chosen.'
                : `You cannot return to this task. ${isFinal ? 'Submit the section?' : 'Continue?'}`}
            </span>
            <button className="rounded border px-4 py-2" onClick={() => setConfirming(false)}>
              Keep working
            </button>
            <button
              className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
              disabled={busy}
              onClick={() => void move(isFinal)}
            >
              {isFinal ? 'Yes, submit' : isRouterEnd ? 'Yes, go to Module 2' : 'Yes, next task'}
            </button>
          </>
        ) : (
          <button className="rounded bg-blue-600 px-4 py-2 text-white" onClick={() => setConfirming(true)}>
            {isFinal ? 'Submit section' : isRouterEnd ? 'Finish Module 1' : 'Next task'}
          </button>
        )}
      </footer>
    </div>
  )
}

function answersFrom(run: Run): Record<number, Answer> {
  const out: Record<number, Answer> = {}
  for (const it of run.items) if (it.answer) out[it.response_id] = it.answer as unknown as Answer
  return out
}
