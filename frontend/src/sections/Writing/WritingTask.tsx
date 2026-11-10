import { useState } from 'react'
import type { TaskProps } from '../types'
import BuildSentence from './BuildSentence'
import TextTask from './TextTask'

export default function WritingTask({ run, examMode, answers, setAnswer }: TaskProps) {
  const [index, setIndex] = useState(0)
  const first = run.items[0]
  if (!first) return null

  if (run.task_type === 'build_a_sentence') {
    const orders = Object.fromEntries(
      run.items.map((it) => {
        const a = answers[it.response_id]
        return [it.response_id, a && 'order' in a ? a.order : []]
      }),
    )
    return (
      <BuildSentence
        items={run.items}
        answers={orders}
        index={index}
        onIndex={setIndex}
        onChange={(id, order) => setAnswer(id, { order })}
      />
    )
  }
  const a = answers[first.response_id]
  return (
    <TextTask
      item={first}
      text={a && 'text' in a ? a.text : ''}
      examMode={examMode}
      onChange={(text) => setAnswer(first.response_id, { text })}
    />
  )
}
