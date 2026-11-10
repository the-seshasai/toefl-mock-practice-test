import { useEffect, useState } from 'react'
import { api, type ErrorNote, type ReviewItem, type Results as ResultsData, type Route, type SectionResult } from '../api'
import { SECTION_LABEL, TASK_LABEL } from '../labels'
import { navigate } from '../route'
import { capitalize } from '../lib/text'
import { InterviewReview, RepeatReview } from './SpeakingReview'
import { CompleteWordsReview, ListeningReview, MultipleChoiceReview } from './ReadingReview'

const PENDING = ['scoring', 'generating', 'in_progress', 'ready', 'preparing_next']

export default function Results({ attemptId }: { attemptId: number }) {
  const [data, setData] = useState<ResultsData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = () =>
      api
        .results(attemptId)
        .then((r) => {
          if (!cancelled) setData(r)
          return r
        })
        .catch((e: unknown) => {
          if (!cancelled) setError(e instanceof Error ? e.message : String(e))
          return null
        })
    void load()
    const id = window.setInterval(() => {
      void load()
    }, 2000)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [attemptId])

  if (error) return <p className="text-red-600">Error: {error}</p>
  if (!data) return <p>Loading results…</p>

  const waiting = data.sections.some((s) => PENDING.includes(s.status))
  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div className="flex items-start justify-between">
        <h1 className="text-3xl font-bold">Results</h1>
        <span className="space-x-2">
          <button className="rounded border px-4 py-2" onClick={() => navigate('/history')}>
            Progress history
          </button>
          <button className="rounded border px-4 py-2" onClick={() => navigate('/')}>
            New practice
          </button>
        </span>
      </div>
      <p className="rounded bg-amber-50 p-3 text-sm text-amber-900">{data.disclaimer}</p>
      {waiting && <p className="text-slate-600">Scoring your answers… this can take a minute.</p>}
      {data.overall_band !== null && (
        <div className="rounded border-2 border-blue-600 p-5">
          <p className="text-sm uppercase tracking-wide text-slate-500">Overall estimated band</p>
          <p className="text-5xl font-bold text-blue-700">{data.overall_band.toFixed(1)}</p>
          <p className="mt-1 text-sm text-slate-600">Average of the four section bands, rounded to the nearest half band.</p>
          <ul className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {data.sections.map((s) => (
              <li key={s.section} className="rounded bg-slate-50 p-2 text-center">
                <span className="block text-xs text-slate-500">{SECTION_LABEL[s.section]}</span>
                <span className="text-xl font-semibold">{s.band?.toFixed(1) ?? '—'}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {data.sections.map((s) => (
        <SectionView key={s.section} s={s} attemptId={attemptId} />
      ))}
    </div>
  )
}

function SectionView({ s, attemptId }: { s: SectionResult; attemptId: number }) {
  return (
    <section className="space-y-4">
      <div className="flex items-baseline gap-4 border-b pb-2">
        <h2 className="text-2xl font-semibold">{SECTION_LABEL[s.section]}</h2>
        {s.band !== null && (
          <span className="text-3xl font-bold text-blue-700" title="Estimated band">
            {s.band.toFixed(1)} <span className="text-base font-normal text-slate-500">estimated band (1–6)</span>
          </span>
        )}
        {s.points !== null && s.max_points !== null && (
          <span className="text-slate-600">
            {s.points} / {s.max_points} points
          </span>
        )}
      </div>
      {s.route && <RouteNote route={s.route} />}
      {s.status === 'scoring_failed' && (
        <div className="rounded bg-red-50 p-3 text-red-800">
          Some responses could not be scored.{' '}
          <button className="underline" onClick={() => void api.rescore(attemptId, s.section)}>
            Retry scoring
          </button>
        </div>
      )}
      {s.tasks.map((t) => (
        <details key={`${t.stage}-${t.task_type}`} className="rounded border p-4" open>
          <summary className="cursor-pointer font-semibold">
            {t.stage_label && <span className="mr-2 rounded bg-slate-200 px-2 py-0.5 text-xs font-normal">{t.stage_label}{t.level ? ` · ${t.level}` : ''}</span>}
            {TASK_LABEL[t.task_type]} — {t.points} / {t.max_points}
          </summary>
          <div className="mt-4 space-y-6">
            {t.items.map((it) => (
              <ItemReview key={it.response_id} it={it} attemptId={attemptId} />
            ))}
          </div>
        </details>
      ))}
    </section>
  )
}

function RouteNote({ route }: { route: Route }) {
  const harder = route.to === 'upper'
  const pct = Math.round(route.router_fraction * 100)
  return (
    <p className="rounded bg-blue-50 p-3 text-sm text-blue-900">
      Module 1 ({route.router_level}): you scored {pct}%, so Module 2 was the {harder ? 'harder' : 'easier'} one ({route.module_level}).
      {route.fallback && ' The module that matched your score could not be prepared, so the other one was used.'} Your band combines both modules.
    </p>
  )
}

function ItemReview({ it, attemptId }: { it: ReviewItem; attemptId: number }) {
  const fb = it.feedback ?? {}
  if (it.task_type === 'listen_and_repeat') return <RepeatReview it={it} attemptId={attemptId} />
  if (it.task_type === 'take_interview') return <InterviewReview it={it} attemptId={attemptId} />
  if (it.task_type === 'complete_the_words') return <CompleteWordsReview it={it} />
  if (it.task_type.startsWith('listen_')) return <ListeningReview it={it} attemptId={attemptId} />
  if (it.task_type === 'read_in_daily_life' || it.task_type === 'read_academic_passage') return <MultipleChoiceReview it={it} />
  if (it.task_type === 'build_a_sentence') {
    const ok = fb.correct === true
    return (
      <div className={`rounded border-l-4 p-3 ${ok ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}>
        <p className="text-sm text-slate-600">{it.prompt.context as string}</p>
        <p>
          <strong>Your sentence:</strong> {fb.your_sentence ? capitalize(fb.your_sentence as string) : <em>(no answer)</em>}
        </p>
        {!ok && (
          <p>
            <strong>Correct:</strong> {capitalize(fb.correct_sentence as string)}
          </p>
        )}
        <p className="mt-1 text-sm text-slate-700">{fb.explanation as string}</p>
      </div>
    )
  }
  const text = (it.answer?.text as string | undefined) ?? ''
  const errors = (fb.errors as ErrorNote[] | undefined) ?? []
  const strengths = (fb.strengths as string[] | undefined) ?? []
  return (
    <div className="space-y-3">
      {it.task_type === 'write_email' ? (
        <p className="text-sm text-slate-600">{it.prompt.scenario as string}</p>
      ) : (
        <p className="text-sm text-slate-600">{it.prompt.professor_post as string}</p>
      )}
      {fb.error ? (
        <p className="text-red-700">Scoring failed: {fb.error as string}</p>
      ) : (
        <p className="text-xl font-semibold">
          Score: {it.score} / {it.max_score} <span className="text-sm font-normal text-slate-500">(estimate)</span>
        </p>
      )}
      {typeof fb.summary === 'string' && <p>{fb.summary}</p>}
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <h4 className="font-semibold">Your response ({(fb.word_count as number | undefined) ?? 0} words)</h4>
          <p className="mt-1 whitespace-pre-wrap rounded bg-slate-50 p-3">{text || <em>(no answer)</em>}</p>
        </div>
        <div>
          <h4 className="font-semibold">Model answer</h4>
          <p className="mt-1 whitespace-pre-wrap rounded bg-green-50 p-3">{(fb.model_answer as string | undefined) || '—'}</p>
        </div>
      </div>
      {strengths.length > 0 && (
        <div>
          <h4 className="font-semibold">Strengths</h4>
          <ul className="list-disc pl-6">
            {strengths.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
      )}
      {errors.length > 0 && (
        <div>
          <h4 className="font-semibold">Errors to fix</h4>
          <ul className="space-y-2">
            {errors.map((e, i) => (
              <li key={i} className="rounded border p-2 text-sm">
                <span className="mr-2 rounded bg-slate-200 px-2 py-0.5 text-xs">{e.category.replace('_', ' ')}</span>
                {e.quote && <q className="italic">{e.quote}</q>} — {e.issue}
                {e.fix && <span className="block text-green-800">Better: {e.fix}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="text-xs text-slate-400">Rubric: {fb.rubric_version as string}</p>
    </div>
  )
}
