import { audioUrl, type ReviewItem } from '../api'
import AudioPlayer from '../components/AudioPlayer'
import type { Segment } from '../sections/Reading/CompleteWords'
import { TextPanel } from '../sections/Reading/MultipleChoiceSet'

interface BlankResult {
  prefix: string
  answer: string
  typed: string
  correct: boolean
}

interface QuestionResult {
  chosen: number | null
  correct_index: number
  correct: boolean
  explanation: string
  kind: string
}

const LETTERS = ['A', 'B', 'C', 'D']

export function CompleteWordsReview({ it }: { it: ReviewItem }) {
  const segments = it.prompt.segments as Segment[]
  const blanks = ((it.feedback?.blanks as BlankResult[] | undefined) ?? [])
  return (
    <div>
      <p className="mb-2 text-sm text-slate-600">
        {(it.feedback?.correct_count as number | undefined) ?? 0} of {blanks.length} words correct
      </p>
      <p className="rounded bg-slate-50 p-4 font-serif text-lg leading-9">
        {segments.map((seg, k) => {
          if ('text' in seg) return <span key={k} className="whitespace-pre-wrap">{seg.text}</span>
          const b = blanks[seg.blank]
          if (!b) return <span key={k}>{seg.prefix}</span>
          return b.correct ? (
            <span key={k} className="rounded bg-green-100 px-1 text-green-900">{b.answer}</span>
          ) : (
            <span key={k} className="rounded bg-red-100 px-1">
              <s className="text-red-700">{b.prefix}{b.typed || '___'}</s>{' '}
              <span className="font-semibold text-green-800">{b.answer}</span>
            </span>
          )
        })}
      </p>
    </div>
  )
}

interface ScriptLine {
  speaker: string
  text: string
}

export function ListeningReview({ it, attemptId }: { it: ReviewItem; attemptId: number }) {
  const script = it.prompt.script as ScriptLine[]
  const multi = new Set(script.map((l) => l.speaker)).size > 1
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600">{it.prompt.setting as string}</p>
      <AudioPlayer src={audioUrl(attemptId, it.response_id)} once={false} />
      <details>
        <summary className="cursor-pointer text-sm text-slate-600">Show the transcript</summary>
        <div className="mt-2 space-y-1 rounded border bg-slate-50 p-3">
          {script.map((l, i) => (
            <p key={i}>
              {multi && <strong>{l.speaker}: </strong>}
              {l.text}
            </p>
          ))}
        </div>
      </details>
      <MultipleChoiceReview it={it} hideText />
    </div>
  )
}

export function MultipleChoiceReview({ it, hideText = false }: { it: ReviewItem; hideText?: boolean }) {
  const kind = it.task_type === 'read_in_daily_life' ? 'daily_life' : 'academic'
  const questions = it.prompt.questions as { prompt: string; options: string[] }[]
  const results = (it.feedback?.questions as QuestionResult[] | undefined) ?? []
  return (
    <div className="space-y-4">
      {!hideText && (
        <details>
          <summary className="cursor-pointer text-sm text-slate-600">Show the text</summary>
          <div className="mt-2">
            <TextPanel kind={kind} prompt={it.prompt} />
          </div>
        </details>
      )}
      {questions.map((q, qi) => {
        const r = results[qi]
        return (
          <div key={qi} className="rounded border p-3">
            <p className="font-medium">
              {qi + 1}. {q.prompt}{' '}
              {r && <span className={r.correct ? 'text-green-700' : 'text-red-700'}>{r.correct ? '✓ correct' : r.chosen === null ? '✗ not answered' : '✗ incorrect'}</span>}
            </p>
            <ul className="mt-2 space-y-1">
              {q.options.map((opt, oi) => {
                const isCorrect = r?.correct_index === oi
                const isChosenWrong = r?.chosen === oi && !isCorrect
                return (
                  <li
                    key={oi}
                    className={`rounded px-2 py-1 ${isCorrect ? 'bg-green-100 font-medium' : isChosenWrong ? 'bg-red-100 line-through' : ''}`}
                  >
                    {LETTERS[oi]}. {opt} {isCorrect && '✓'} {r?.chosen === oi && <em className="text-xs">(your answer)</em>}
                  </li>
                )
              })}
            </ul>
            {r && <p className="mt-2 text-sm text-slate-700">{r.explanation}</p>}
          </div>
        )
      })}
    </div>
  )
}
