interface Props {
  index: number
  count: number
  label: string
  onIndex: (i: number) => void
  /** How many items already have an answer */
  started: number
}

export default function Pager({ index, count, label, onIndex, started }: Props) {
  return (
    <div className="flex items-center justify-between rounded bg-slate-50 px-3 py-2 text-sm">
      <button className="rounded border bg-white px-3 py-1 disabled:opacity-40" disabled={index === 0} onClick={() => onIndex(index - 1)}>
        Previous
      </button>
      <span className="text-slate-600">
        {label} {index + 1} of {count} · {started} started
      </span>
      <button
        className="rounded border bg-white px-3 py-1 disabled:opacity-40"
        disabled={index === count - 1}
        onClick={() => onIndex(index + 1)}
      >
        Next
      </button>
    </div>
  )
}
