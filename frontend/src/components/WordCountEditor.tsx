import { countWords } from '../lib/text'

interface Props {
  value: string
  onChange: (text: string) => void
  /** Exam mode disables spellcheck and autocorrect, as on the real test */
  examMode: boolean
  targetWords?: string
}

export default function WordCountEditor({ value, onChange, examMode, targetWords }: Props) {
  return (
    <div>
      <textarea
        className="h-64 w-full rounded border border-slate-300 p-3 font-serif text-lg leading-relaxed focus:border-blue-500 focus:outline-none"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        spellCheck={!examMode}
        autoComplete="off"
        autoCorrect={examMode ? 'off' : 'on'}
        autoCapitalize="off"
        data-gramm="false"
        aria-label="Your response"
      />
      <p className="mt-1 text-sm text-slate-600">
        Words: <strong>{countWords(value)}</strong>
        {targetWords && <span> · suggested {targetWords}</span>}
      </p>
    </div>
  )
}
