import type { SectionName, TaskType } from './api'

export const TASK_LABEL: Record<TaskType, string> = {
  complete_the_words: 'Complete the Words',
  read_in_daily_life: 'Read in Daily Life',
  read_academic_passage: 'Read an Academic Passage',
  listen_choose_response: 'Listen and Choose a Response',
  listen_conversation: 'Listen to a Conversation',
  listen_announcement: 'Listen to an Announcement',
  listen_academic_talk: 'Listen to an Academic Talk',
  build_a_sentence: 'Build a Sentence',
  write_email: 'Write an Email',
  write_academic_discussion: 'Write for an Academic Discussion',
  listen_and_repeat: 'Listen and Repeat',
  take_interview: 'Take an Interview',
}

export const SECTION_LABEL: Record<SectionName, string> = {
  reading: 'Reading',
  listening: 'Listening',
  writing: 'Writing',
  speaking: 'Speaking',
}

export const SPEAKING_TASKS: TaskType[] = ['listen_and_repeat', 'take_interview']
export const LISTENING_TASKS: TaskType[] = [
  'listen_choose_response',
  'listen_conversation',
  'listen_announcement',
  'listen_academic_talk',
]
export const READING_TASKS: TaskType[] = ['complete_the_words', 'read_in_daily_life', 'read_academic_passage']
export const WRITING_TASKS: TaskType[] = ['build_a_sentence', 'write_email', 'write_academic_discussion']

export function formatBudget(seconds: number): string {
  return `${Math.round(seconds / 60)} min`
}
