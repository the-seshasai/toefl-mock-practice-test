import type { RunItem } from '../../api'
import { capitalize } from '../../lib/text'

interface Props {
  items: RunItem[]
  answers: Record<number, string[]>
  index: number
  onIndex: (i: number) => void
  onChange: (responseId: number, order: string[]) => void
}

export default function BuildSentence({ items, answers, index, onIndex, onChange }: Props) {
  const item = items[index]
  if (!item) return null
  const chunks = item.prompt.chunks as string[]
  const context = item.prompt.context as string
  const placed = answers[item.response_id] ?? []
  const remaining = chunks.filter((c) => !placed.includes(c))
  const answeredCount = items.filter((it) => (answers[it.response_id] ?? []).length > 0).length

  return (
    <div>
      <p className="text-sm text-slate-500">
        Sentence {index + 1} of {items.length} · {answeredCount} started
      </p>
      <p className="mt-3 rounded bg-slate-50 p-3 text-lg">{context}</p>

      <p className="mt-6 text-sm font-medium text-slate-600">Your sentence (click a word group to remove it)</p>
      <div className="mt-2 flex min-h-14 flex-wrap items-center gap-2 rounded border-2 border-dashed border-slate-300 p-3">
        {placed.length === 0 && <span className="text-slate-400">Click word groups below to build the sentence</span>}
        {placed.map((c, i) => (
          <button
            key={c}
            className="rounded bg-blue-600 px-3 py-2 text-white hover:bg-blue-700"
            onClick={() => onChange(item.response_id, placed.filter((_, j) => j !== i))}
          >
            {i === 0 ? capitalize(c) : c}
          </button>
        ))}
      </div>

      <p className="mt-6 text-sm font-medium text-slate-600">Word groups</p>
      <div className="mt-2 flex min-h-14 flex-wrap gap-2">
        {remaining.map((c) => (
          <button
            key={c}
            className="rounded border border-slate-400 bg-white px-3 py-2 hover:bg-slate-100"
            onClick={() => onChange(item.response_id, [...placed, c])}
          >
            {c}
          </button>
        ))}
      </div>

      <div className="mt-6 flex items-center justify-between">
        <button
          className="rounded border px-4 py-2 disabled:opacity-40"
          disabled={index === 0}
          onClick={() => onIndex(index - 1)}
        >
          Previous
        </button>
        <button className="text-sm text-slate-600 underline" onClick={() => onChange(item.response_id, [])}>
          Reset this sentence
        </button>
        <button
          className="rounded border px-4 py-2 disabled:opacity-40"
          disabled={index === items.length - 1}
          onClick={() => onIndex(index + 1)}
        >
          Next
        </button>
      </div>
    </div>
  )
}
