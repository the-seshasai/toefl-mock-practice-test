export interface Question {
  prompt: string
  options: string[]
}

interface Props {
  kind: 'daily_life' | 'academic'
  prompt: Record<string, unknown>
  choices: (number | null)[]
  onChange: (choices: (number | null)[]) => void
}

const LETTERS = ['A', 'B', 'C', 'D']

export function TextPanel({ kind, prompt }: { kind: 'daily_life' | 'academic'; prompt: Record<string, unknown> }) {
  const title = (prompt.title as string | undefined) ?? ''
  if (kind === 'daily_life') {
    return (
      <div className="rounded border bg-slate-50 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">{prompt.format as string}</p>
        {title && <h2 className="mt-1 text-lg font-semibold">{title}</h2>}
        <p className="mt-2 whitespace-pre-line text-lg leading-relaxed">{prompt.text as string}</p>
      </div>
    )
  }
  const paragraphs = (prompt.passage as string).split(/\n\n+/)
  return (
    <div className="rounded border bg-slate-50 p-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      {paragraphs.map((p, i) => (
        <p key={i} className="mt-3 font-serif text-lg leading-relaxed">
          {p}
        </p>
      ))}
    </div>
  )
}

export function QuestionList({ questions, choices, onChange }: { questions: Question[]; choices: (number | null)[]; onChange: (choices: (number | null)[]) => void }) {
  const pick = (qi: number, oi: number) => {
    const next = Array.from({ length: questions.length }, (_, k) => choices[k] ?? null)
    next[qi] = oi
    onChange(next)
  }
  return (
    <div className="space-y-6">
      {questions.map((q, qi) => (
        <fieldset key={qi}>
          <legend className="font-medium">
            {qi + 1}. {q.prompt}
          </legend>
          <div className="mt-2 space-y-2">
            {q.options.map((opt, oi) => (
              <label
                key={oi}
                className="flex cursor-pointer items-start gap-2 rounded border p-2 has-[:checked]:border-blue-600 has-[:checked]:bg-blue-50"
              >
                <input type="radio" name={`q${qi}`} checked={choices[qi] === oi} onChange={() => pick(qi, oi)} />
                <span>
                  <strong>{LETTERS[oi]}.</strong> {opt}
                </span>
              </label>
            ))}
          </div>
        </fieldset>
      ))}
    </div>
  )
}

export default function MultipleChoiceSet({ kind, prompt, choices, onChange }: Props) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="md:sticky md:top-4 md:max-h-[75vh] md:self-start md:overflow-y-auto">
        <TextPanel kind={kind} prompt={prompt} />
      </div>
      <QuestionList questions={prompt.questions as Question[]} choices={choices} onChange={onChange} />
    </div>
  )
}
