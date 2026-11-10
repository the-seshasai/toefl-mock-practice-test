import { recordingUrl, type ErrorNote, type RecordedPart, type ReviewItem } from '../api'

interface Delivery {
  duration_s: number
  words: number
  wpm: number
  long_pauses: number
  avg_confidence: number
  unclear_words: string[]
}

interface Difference {
  type: 'missing' | 'extra' | 'changed'
  target: string
  heard: string
}

interface InterviewEntry {
  question: string
  transcript: string
  score: number
  summary: string
  strengths: string[]
  errors: ErrorNote[]
  model_answer: string
  delivery: Delivery | null
}

function partsOf(it: ReviewItem): Record<string, RecordedPart> {
  const parts = (it.answer as { parts?: Record<string, RecordedPart> } | null)?.parts
  return parts ?? {}
}

function DeliveryLine({ d }: { d: Delivery | null | undefined }) {
  if (!d || d.words === 0) return null
  return (
    <p className="text-xs text-slate-500">
      Delivery: {d.wpm} words/min · {d.long_pauses} long {d.long_pauses === 1 ? 'pause' : 'pauses'} · recognizer confidence{' '}
      {Math.round(d.avg_confidence * 100)}%
      {d.unclear_words.length > 0 && <> · possibly unclear: {d.unclear_words.join(', ')}</>}
    </p>
  )
}

export function RepeatReview({ it, attemptId }: { it: ReviewItem; attemptId: number }) {
  const fb = it.feedback ?? {}
  const diffs = (fb.differences as Difference[] | undefined) ?? []
  const accuracy = Math.round(((fb.accuracy as number | undefined) ?? 0) * 100)
  const ok = (it.score ?? 0) >= 4
  return (
    <div className={`space-y-2 rounded border-l-4 p-3 ${ok ? 'border-green-500 bg-green-50' : 'border-amber-500 bg-amber-50'}`}>
      <p className="font-medium">
        Score {it.score} / {it.max_score} <span className="text-sm font-normal text-slate-500">· {accuracy}% of words matched (estimate)</span>
      </p>
      <p>
        <strong>Target:</strong> {it.prompt.sentence as string}
      </p>
      <p>
        <strong>You said:</strong> {(fb.transcript as string) || <em>{(fb.note as string) ?? '(nothing recognized)'}</em>}
      </p>
      {diffs.length > 0 && (
        <ul className="text-sm">
          {diffs.map((d, i) => (
            <li key={i}>
              {d.type === 'missing' && (
                <>
                  <span className="rounded bg-red-100 px-1">missing</span> “{d.target}”
                </>
              )}
              {d.type === 'extra' && (
                <>
                  <span className="rounded bg-slate-200 px-1">extra</span> “{d.heard}”
                </>
              )}
              {d.type === 'changed' && (
                <>
                  <span className="rounded bg-amber-200 px-1">changed</span> “{d.target}” → “{d.heard}”
                </>
              )}
            </li>
          ))}
        </ul>
      )}
      <DeliveryLine d={fb.delivery as Delivery | undefined} />
      {partsOf(it)['0'] && <audio controls src={recordingUrl(attemptId, it.response_id, 0)} className="w-full" />}
    </div>
  )
}

export function InterviewReview({ it, attemptId }: { it: ReviewItem; attemptId: number }) {
  const entries = ((it.feedback?.items as InterviewEntry[] | undefined) ?? [])
  const questions = it.prompt.questions as string[]
  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-600">{it.prompt.setting as string}</p>
      {questions.map((q, i) => {
        const e = entries[i]
        return (
          <div key={i} className="space-y-2 rounded border p-3">
            <p className="font-medium">
              {i + 1}. {q}
            </p>
            {partsOf(it)[String(i)] && <audio controls src={recordingUrl(attemptId, it.response_id, i)} className="w-full" />}
            {e && (
              <>
                <p className="text-lg font-semibold">
                  Score {e.score} / 5 <span className="text-sm font-normal text-slate-500">(estimate)</span>
                </p>
                <p className="text-sm text-slate-700">{e.summary}</p>
                <DeliveryLine d={e.delivery} />
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <h4 className="font-semibold">Your answer (transcript)</h4>
                    <p className="mt-1 whitespace-pre-wrap rounded bg-slate-50 p-3">{e.transcript || <em>(nothing recognized)</em>}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold">Model answer</h4>
                    <p className="mt-1 whitespace-pre-wrap rounded bg-green-50 p-3">{e.model_answer || '—'}</p>
                  </div>
                </div>
                {e.strengths.length > 0 && (
                  <ul className="list-disc pl-6 text-sm">
                    {e.strengths.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                )}
                {e.errors.length > 0 && (
                  <ul className="space-y-1">
                    {e.errors.map((er, k) => (
                      <li key={k} className="rounded border p-2 text-sm">
                        <span className="mr-2 rounded bg-slate-200 px-2 py-0.5 text-xs">{er.category.replace('_', ' ')}</span>
                        {er.quote && <q className="italic">{er.quote}</q>} {er.issue}
                        {er.fix && <span className="block text-green-800">Better: {er.fix}</span>}
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>
        )
      })}
      <p className="text-xs text-slate-400">Rubric: {it.feedback?.rubric_version as string}</p>
    </div>
  )
}
