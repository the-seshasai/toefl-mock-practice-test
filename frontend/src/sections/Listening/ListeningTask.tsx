import { useState } from 'react'
import { audioUrl } from '../../api'
import AudioPlayer from '../../components/AudioPlayer'
import Pager from '../../components/Pager'
import { QuestionList, type Question } from '../Reading/MultipleChoiceSet'
import type { TaskProps } from '../types'

export default function ListeningTask({ run, examMode, answers, setAnswer, attemptId }: TaskProps) {
  const [index, setIndex] = useState(0)
  const [heard, setHeard] = useState<Record<number, boolean>>({})
  const item = run.items[index]
  if (!item) return null

  const answer = answers[item.response_id]
  const choices = answer && 'choices' in answer ? answer.choices : []
  // Exam mode: questions appear once the clip has played (or was already used before a refresh).
  const showQuestions = !examMode || heard[item.response_id] || item.audio_played[0]
  const started = run.items.filter((it) => {
    const a = answers[it.response_id]
    return !!a && 'choices' in a && a.choices.some((c) => c !== null)
  }).length
  const single = run.task_type === 'listen_choose_response'

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      {examMode ? (
        <p className="rounded bg-slate-50 px-3 py-2 text-sm text-slate-600">
          Item {index + 1} of {run.items.length} · {started} answered · you cannot go back to earlier items
        </p>
      ) : (
        <Pager index={index} count={run.items.length} label="Item" started={started} onIndex={setIndex} />
      )}
      <p className="text-slate-700">{item.prompt.setting as string}</p>
      <AudioPlayer
        key={item.response_id}
        src={audioUrl(attemptId, item.response_id)}
        once={examMode}
        alreadyPlayed={examMode && item.audio_played[0]}
        onEnded={() => setHeard((h) => ({ ...h, [item.response_id]: true }))}
      />
      {showQuestions ? (
        <QuestionList
          questions={item.prompt.questions as Question[]}
          choices={choices}
          onChange={(c) => setAnswer(item.response_id, { choices: c })}
        />
      ) : (
        <p className="text-sm text-slate-500">{single ? 'The answer choices appear after the audio.' : 'The questions appear after the audio.'}</p>
      )}
      {examMode && (
        <div className="flex justify-end">
          <button
            className="rounded border px-4 py-2 disabled:opacity-40"
            disabled={!showQuestions || index === run.items.length - 1}
            onClick={() => setIndex(index + 1)}
          >
            Next item
          </button>
        </div>
      )}
    </div>
  )
}
