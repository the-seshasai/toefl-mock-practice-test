import { useCallback, useEffect, useRef, useState } from 'react'
import { api, audioUrl, recordingUrl, type RecordedPart, type RunItem } from '../../api'
import AudioPlayer from '../../components/AudioPlayer'
import { Recorder, useAudioLevel, type RecordingResult } from '../../lib/recorder'
import type { TaskProps } from '../types'

type Phase = 'listen' | 'prep' | 'record' | 'saving' | 'done'

interface Step {
  item: RunItem
  part: number
}

function partsOf(answer: TaskProps['answers'][number] | undefined): Record<string, RecordedPart> {
  return answer && 'parts' in answer ? answer.parts : {}
}

export default function SpeakingTask({ attemptId, run, examMode, answers, setLocalAnswer }: TaskProps) {
  const steps: Step[] = run.items.flatMap((item) => Array.from({ length: item.audio_parts }, (_, part) => ({ item, part })))
  const firstOpen = steps.findIndex((s) => !partsOf(answers[s.item.response_id])[String(s.part)])
  const [index, setIndex] = useState(firstOpen === -1 ? steps.length - 1 : firstOpen)
  const step = steps[index]
  if (!step) return null

  const recorded = steps.filter((s) => partsOf(answers[s.item.response_id])[String(s.part)]).length
  const info = partsOf(answers[step.item.response_id])[String(step.part)]

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex items-center justify-between rounded bg-slate-50 px-3 py-2 text-sm text-slate-600">
        <span>
          Response {index + 1} of {steps.length} · {recorded} recorded
        </span>
        {!examMode && (
          <span className="space-x-2">
            <button className="rounded border bg-white px-3 py-1 disabled:opacity-40" disabled={index === 0} onClick={() => setIndex(index - 1)}>
              Previous
            </button>
            <button className="rounded border bg-white px-3 py-1 disabled:opacity-40" disabled={index === steps.length - 1} onClick={() => setIndex(index + 1)}>
              Next
            </button>
          </span>
        )}
      </div>
      <SpeakingStep
        key={`${step.item.response_id}-${step.part}`}
        attemptId={attemptId}
        step={step}
        total={step.item.audio_parts}
        examMode={examMode}
        recorded={info ?? null}
        isLast={index === steps.length - 1}
        onRecorded={(part) => setLocalAnswer(step.item.response_id, { parts: { ...partsOf(answers[step.item.response_id]), [String(step.part)]: part } })}
        onNext={() => setIndex((i) => Math.min(i + 1, steps.length - 1))}
      />
    </div>
  )
}

interface StepProps {
  attemptId: number
  step: Step
  total: number
  examMode: boolean
  recorded: RecordedPart | null
  isLast: boolean
  onRecorded: (part: RecordedPart) => void
  onNext: () => void
}

function SpeakingStep({ attemptId, step, total, examMode, recorded, isLast, onRecorded, onNext }: StepProps) {
  const { item, part } = step
  const prompt = item.prompt as { setting: string; prep_seconds: number; response_seconds: number }
  const alreadyPlayed = examMode && item.audio_played[part]
  const [phase, setPhase] = useState<Phase>(recorded ? 'done' : alreadyPlayed ? (prompt.prep_seconds > 0 ? 'prep' : 'record') : 'listen')
  const [error, setError] = useState<string | null>(null)
  const pending = useRef<RecordingResult | null>(null)

  const afterListen = useCallback(() => setPhase(prompt.prep_seconds > 0 ? 'prep' : 'record'), [prompt.prep_seconds])

  const save = useCallback(
    async (result: RecordingResult) => {
      pending.current = result
      setPhase('saving')
      setError(null)
      try {
        await api.uploadRecording(attemptId, item.response_id, part, result.blob, result.durationMs)
        onRecorded({ file: '', duration_ms: Math.round(result.durationMs), content_type: result.blob.type })
        pending.current = null
        setPhase('done')
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
        setPhase('saving')
      }
    },
    [attemptId, item.response_id, part, onRecorded],
  )

  // Exam mode: move on by itself shortly after a response is saved.
  useEffect(() => {
    if (phase !== 'done' || !examMode || isLast) return
    const id = window.setTimeout(onNext, 1500)
    return () => window.clearTimeout(id)
  }, [phase, examMode, isLast, onNext])

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm text-slate-500">
          {item.task_type === 'take_interview' ? `Question ${part + 1} of ${total}` : 'Listen and repeat'}
        </p>
        <p className="text-slate-700">{prompt.setting}</p>
      </div>

      {phase === 'listen' && (
        <AudioPlayer src={audioUrl(attemptId, item.response_id, part)} once={examMode} alreadyPlayed={false} onEnded={afterListen} />
      )}
      {phase === 'prep' && <Countdown label="Prepare your answer" seconds={prompt.prep_seconds} onDone={() => setPhase('record')} onSkip={examMode ? undefined : () => setPhase('record')} />}
      {phase === 'record' && <RecordPhase seconds={prompt.response_seconds} onDone={(r) => void save(r)} />}
      {phase === 'saving' && (
        <div className="rounded border bg-slate-50 p-4">
          {error ? (
            <>
              <p className="text-red-600">Could not save the recording: {error}</p>
              <button className="mt-2 rounded bg-blue-600 px-4 py-2 text-white" onClick={() => pending.current && void save(pending.current)}>
                Retry saving
              </button>
            </>
          ) : (
            <p className="text-slate-600">Saving your response…</p>
          )}
        </div>
      )}
      {phase === 'done' && (
        <div className="space-y-3 rounded border border-green-300 bg-green-50 p-4">
          <p className="font-medium text-green-800">✓ Response recorded</p>
          {!examMode && (
            <>
              <audio controls src={recordingUrl(attemptId, item.response_id, part)} className="w-full" />
              <div className="space-x-2">
                <button className="rounded border bg-white px-3 py-1" onClick={() => setPhase('record')}>
                  Record again
                </button>
                {!isLast && (
                  <button className="rounded bg-blue-600 px-3 py-1 text-white" onClick={onNext}>
                    Next response
                  </button>
                )}
              </div>
            </>
          )}
          {examMode && !isLast && <p className="text-sm text-slate-600">Moving to the next response…</p>}
          {isLast && <p className="text-sm text-slate-600">That was the last response in this task.</p>}
        </div>
      )}
    </div>
  )
}

function Countdown({ label, seconds, onDone, onSkip }: { label: string; seconds: number; onDone: () => void; onSkip?: () => void }) {
  const [left, setLeft] = useState(seconds)
  const doneRef = useRef(onDone)
  useEffect(() => {
    doneRef.current = onDone
  })
  useEffect(() => {
    const startedAt = Date.now()
    const id = window.setInterval(() => {
      const l = seconds - (Date.now() - startedAt) / 1000
      setLeft(Math.max(0, l))
      if (l <= 0) {
        window.clearInterval(id)
        doneRef.current()
      }
    }, 200)
    return () => window.clearInterval(id)
  }, [seconds])
  return (
    <div className="rounded border bg-amber-50 p-4 text-center" role="timer">
      <p className="font-medium text-amber-900">{label}</p>
      <p className="mt-1 font-mono text-4xl">{Math.ceil(left)}</p>
      <p className="text-sm text-slate-600">Recording starts automatically.</p>
      {onSkip && (
        <button className="mt-2 rounded border bg-white px-3 py-1 text-sm" onClick={onSkip}>
          Start now
        </button>
      )}
    </div>
  )
}

function RecordPhase({ seconds, onDone }: { seconds: number; onDone: (r: RecordingResult) => void }) {
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [left, setLeft] = useState(seconds)
  const recorder = useRef<Recorder | null>(null)
  const finished = useRef(false)
  const stopRef = useRef<() => void>(() => undefined)
  const level = useAudioLevel(stream)

  useEffect(() => {
    stopRef.current = () => {
      const rec = recorder.current
      if (finished.current || !rec) return
      finished.current = true
      void rec.stop().then((result) => {
        stream?.getTracks().forEach((t) => t.stop())
        onDone(result)
      })
    }
  })

  useEffect(() => {
    let cancelled = false
    let timer = 0
    let opened: MediaStream | null = null
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((s) => {
        if (cancelled) {
          s.getTracks().forEach((t) => t.stop())
          return
        }
        opened = s
        setStream(s)
        const rec = new Recorder(s)
        recorder.current = rec
        rec.start()
        const startedAt = Date.now()
        timer = window.setInterval(() => {
          const l = seconds - (Date.now() - startedAt) / 1000
          setLeft(Math.max(0, l))
          if (l <= 0) stopRef.current()
        }, 200)
      })
      .catch(() => setError('The microphone could not be opened. Check the browser permission and try again.'))
    return () => {
      cancelled = true
      window.clearInterval(timer)
      if (!finished.current) recorder.current?.abort()
      opened?.getTracks().forEach((t) => t.stop())
    }
  }, [seconds])

  if (error) return <p className="rounded border border-red-300 bg-red-50 p-4 text-red-700">{error}</p>
  return (
    <div className="rounded border border-red-300 bg-red-50 p-4" role="timer">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 font-semibold text-red-700">
          <span className="inline-block h-3 w-3 animate-pulse rounded-full bg-red-600" aria-hidden /> Recording
        </span>
        <span className="font-mono text-3xl">{Math.ceil(left)}s</span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded bg-red-100" aria-hidden>
        <div className="h-full bg-red-600 transition-[width] duration-75" style={{ width: `${Math.round(level * 100)}%` }} />
      </div>
      <button className="mt-3 rounded bg-red-600 px-4 py-2 text-white" onClick={() => stopRef.current()}>
        Stop and save
      </button>
    </div>
  )
}
