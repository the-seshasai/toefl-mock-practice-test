import { useState } from 'react'
import Pager from '../../components/Pager'
import type { TaskProps } from '../types'
import CompleteWords, { type Segment } from './CompleteWords'
import MultipleChoiceSet from './MultipleChoiceSet'

export default function ReadingTask({ run, answers, setAnswer }: TaskProps) {
  const [index, setIndex] = useState(0)
  const item = run.items[index]
  if (!item) return null

  const started = run.items.filter((it) => {
    const a = answers[it.response_id]
    if (!a) return false
    if ('letters' in a) return a.letters.some((s) => s !== '')
    if ('choices' in a) return a.choices.some((c) => c !== null)
    return false
  }).length
  const answer = answers[item.response_id]

  const label = run.task_type === 'complete_the_words' ? 'Paragraph' : run.task_type === 'read_in_daily_life' ? 'Text' : 'Passage'

  return (
    <div className="space-y-4">
      {run.items.length > 1 && <Pager index={index} count={run.items.length} label={label} started={started} onIndex={setIndex} />}
      {run.task_type === 'complete_the_words' ? (
        <>
          <p className="text-sm text-slate-600">Type the missing letters to complete each word. The first sentence is complete.</p>
          <CompleteWords
            key={item.response_id}
            segments={item.prompt.segments as Segment[]}
            letters={answer && 'letters' in answer ? answer.letters : []}
            onChange={(letters) => setAnswer(item.response_id, { letters })}
          />
        </>
      ) : (
        <MultipleChoiceSet
          key={item.response_id}
          kind={run.task_type === 'read_in_daily_life' ? 'daily_life' : 'academic'}
          prompt={item.prompt}
          choices={answer && 'choices' in answer ? answer.choices : []}
          onChange={(choices) => setAnswer(item.response_id, { choices })}
        />
      )}
    </div>
  )
}
