import { useRef } from 'react'

export type Segment = { text: string } | { blank: number; prefix: string; missing: number }

interface Props {
  segments: Segment[]
  letters: string[]
  onChange: (letters: string[]) => void
}

export default function CompleteWords({ segments, letters, onChange }: Props) {
  const inputs = useRef<(HTMLInputElement | null)[]>([])
  const blankCount = segments.filter((s) => 'blank' in s).length

  const update = (i: number, raw: string, missing: number) => {
    const value = raw.replace(/[^A-Za-z]/g, '').slice(0, missing)
    const next = Array.from({ length: blankCount }, (_, k) => letters[k] ?? '')
    next[i] = value
    onChange(next)
    if (value.length === missing) inputs.current[i + 1]?.focus()
  }

  return (
    <p className="rounded bg-slate-50 p-5 font-serif text-xl leading-[2.4rem]">
      {segments.map((seg, k) =>
        'text' in seg ? (
          <span key={k} className="whitespace-pre-wrap">
            {seg.text}
          </span>
        ) : (
          <span key={k} className="whitespace-nowrap">
            {seg.prefix}
            <input
              ref={(el) => {
                inputs.current[seg.blank] = el
              }}
              className="mx-0.5 border-0 border-b-2 border-slate-500 bg-white px-1 text-center font-mono text-lg focus:border-blue-600 focus:outline-none"
              style={{ width: `${seg.missing * 0.95 + 1}em` }}
              value={letters[seg.blank] ?? ''}
              maxLength={seg.missing}
              spellCheck={false}
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              aria-label={`Missing letters ${seg.blank + 1} (${seg.missing} letters)`}
              onChange={(e) => update(seg.blank, e.target.value, seg.missing)}
              onKeyDown={(e) => {
                if (e.key === 'Backspace' && (letters[seg.blank] ?? '') === '') inputs.current[seg.blank - 1]?.focus()
              }}
            />
          </span>
        ),
      )}
    </p>
  )
}
