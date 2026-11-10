import type { Answer, Run } from '../api'

/** What a section-specific task renderer receives from TaskRunner. */
export interface TaskProps {
  attemptId: number
  run: Run
  examMode: boolean
  answers: Record<number, Answer>
  setAnswer: (responseId: number, answer: Answer) => void
  /** Update the displayed answer without queuing an autosave (for recordings, which upload separately) */
  setLocalAnswer: (responseId: number, answer: Answer) => void
}
