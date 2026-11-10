import type { RunItem } from '../../api'
import WordCountEditor from '../../components/WordCountEditor'

interface Props {
  item: RunItem
  text: string
  examMode: boolean
  onChange: (text: string) => void
}

interface Student {
  name: string
  text: string
}

export default function TextTask({ item, text, examMode, onChange }: Props) {
  const p = item.prompt
  if (item.task_type === 'write_email') {
    const points = p.points as string[]
    return (
      <div>
        <div className="rounded bg-slate-50 p-4">
          <p className="text-lg">{p.scenario as string}</p>
          <p className="mt-3 text-sm text-slate-600">
            To: <strong>{p.recipient as string}</strong>
          </p>
          <ul className="mt-2 list-disc pl-6">
            {points.map((pt) => (
              <li key={pt}>{pt}</li>
            ))}
          </ul>
        </div>
        <div className="mt-4">
          <WordCountEditor value={text} onChange={onChange} examMode={examMode} />
        </div>
      </div>
    )
  }
  const students = p.students as Student[]
  return (
    <div>
      <div className="space-y-3 rounded bg-slate-50 p-4">
        <div>
          <p className="text-sm font-semibold text-slate-600">{p.professor_name as string} (Professor)</p>
          <p className="text-lg">{p.professor_post as string}</p>
        </div>
        {students.map((s) => (
          <div key={s.name} className="border-l-4 border-slate-300 pl-3">
            <p className="text-sm font-semibold text-slate-600">{s.name}</p>
            <p>{s.text}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm text-slate-600">Add your contribution to the discussion.</p>
      <div className="mt-2">
        <WordCountEditor value={text} onChange={onChange} examMode={examMode} targetWords="100+ words" />
      </div>
    </div>
  )
}
