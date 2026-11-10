export type Difficulty = 'beginner' | 'intermediate' | 'advanced'
export type TaskType =
  | 'build_a_sentence'
  | 'write_email'
  | 'write_academic_discussion'
  | 'complete_the_words'
  | 'read_in_daily_life'
  | 'read_academic_passage'
  | 'listen_choose_response'
  | 'listen_conversation'
  | 'listen_announcement'
  | 'listen_academic_talk'
  | 'listen_and_repeat'
  | 'take_interview'
export type SectionName = 'reading' | 'listening' | 'writing' | 'speaking'

export interface TaskInfo {
  task_type: TaskType
  budget_seconds: number
  count: number
}
export interface Route {
  to: 'upper' | 'lower'
  router_fraction: number
  router_level: Difficulty
  module_level: Difficulty
  fallback?: boolean
}
export interface SectionStatus {
  section: SectionName
  status: string
  band: number | null
  stage: string
  stage_label: string
  stage_count: number
  route: Route | null
  tasks: TaskInfo[]
  current_task: number
  task_deadline: string | null
  warnings: string[]
  error: string | null
}
export interface Attempt {
  id: number
  mode: string
  difficulty: Difficulty
  exam_mode: 'exam' | 'practice'
  timed: boolean
  status: string
  server_now: string
  sections: SectionStatus[]
}
export interface RecordedPart {
  file: string
  duration_ms: number
  content_type: string
}
export type Answer =
  | { order: string[] }
  | { text: string }
  | { letters: string[] }
  | { choices: (number | null)[] }
  | { parts: Record<string, RecordedPart> }
export interface RunItem {
  response_id: number
  position: number
  task_type: TaskType
  prompt: Record<string, unknown>
  answer: Record<string, unknown> | null
  has_audio: boolean
  audio_parts: number
  audio_played: boolean[]
}
export interface Run {
  status: string
  stage: string
  stage_label: string
  stage_count: number
  server_now: string
  current_task: number
  task_type: TaskType | null
  task_deadline: string | null
  tasks: TaskInfo[]
  items: RunItem[]
}
export interface ErrorNote {
  category: string
  quote: string
  issue: string
  fix: string
}
export interface ReviewItem {
  response_id: number
  task_type: TaskType
  position: number
  prompt: Record<string, unknown>
  answer: Record<string, unknown> | null
  score: number | null
  max_score: number | null
  feedback: Record<string, unknown> | null
}
export interface TaskResult {
  stage: string
  stage_label: string
  level: Difficulty | null
  task_type: TaskType
  points: number
  max_points: number
  items: ReviewItem[]
}
export interface SectionResult {
  route: Route | null
  section: SectionName
  status: string
  band: number | null
  points: number | null
  max_points: number | null
  tasks: TaskResult[]
  error: string | null
}
export interface Results {
  attempt_id: number
  difficulty: Difficulty
  mode: string
  status: string
  overall_band: number | null
  disclaimer: string
  sections: SectionResult[]
}
export interface CreateAttempt {
  mode: 'full' | 'section' | 'task' | 'weak'
  difficulty: Difficulty
  exam_mode: 'exam' | 'practice'
  timed: boolean
  section?: SectionName
  task_type?: TaskType
}

async function request<T>(method: string, path: string, body?: unknown, keepalive = false, rawType?: string): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': rawType ?? 'application/json' },
    body: body === undefined ? undefined : rawType ? (body as Blob) : JSON.stringify(body),
    keepalive,
  })
  if (!res.ok) {
    const detail = (await res.json().catch(() => null)) as { detail?: string } | null
    throw new ApiError(res.status, detail?.detail ?? res.statusText)
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T)
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

const base = (id: number, section: SectionName) => `/attempts/${id}/sections/${section}`

export const audioUrl = (attemptId: number, responseId: number, part = 0) =>
  `/api/attempts/${attemptId}/responses/${responseId}/audio?part=${part}`
export const recordingUrl = (attemptId: number, responseId: number, part = 0) =>
  `/api/attempts/${attemptId}/responses/${responseId}/recording?part=${part}`

export const api = {
  createAttempt: (body: CreateAttempt) => request<Attempt>('POST', '/attempts', body),
  getAttempt: (id: number) => request<Attempt>('GET', `/attempts/${id}`),
  start: (id: number, s: SectionName) => request<Attempt>('POST', `${base(id, s)}/start`),
  getRun: (id: number, s: SectionName) => request<Run>('GET', `${base(id, s)}/run`),
  save: (id: number, responseId: number, answer: Answer, keepalive = false) =>
    request<void>('PUT', `/attempts/${id}/responses/${responseId}`, { answer }, keepalive),
  uploadRecording: (id: number, responseId: number, part: number, blob: Blob, durationMs: number) =>
    request<void>('POST', `/attempts/${id}/responses/${responseId}/recording?part=${part}&duration_ms=${Math.round(durationMs)}`, blob, false, blob.type || 'audio/webm'),
  advance: (id: number, s: SectionName) => request<Run>('POST', `${base(id, s)}/advance`),
  submit: (id: number, s: SectionName) => request<Run>('POST', `${base(id, s)}/submit`),
  rescore: (id: number, s: SectionName) => request<Attempt>('POST', `${base(id, s)}/rescore`),
  results: (id: number) => request<Results>('GET', `/attempts/${id}/results`),
  history: () => request<{ attempts: HistoryAttempt[] }>('GET', '/history'),
  analytics: () => request<Analytics>('GET', '/analytics'),
  startWeakSpots: (body: WeakSpotRequest) => request<Attempt>('POST', '/practice/weak-spots', body),
}

export interface HistoryAttempt {
  id: number
  mode: string
  difficulty: Difficulty
  exam_mode: string
  status: string
  started_at: string
  overall_band: number | null
  bands: Partial<Record<SectionName, number | null>>
  tasks: string[]
}

export interface TaskStat {
  task_type: TaskType
  section: SectionName
  band: number
  last_band: number
  accuracy: number
  attempts: number
  trend: number | null
}
export interface SectionSummary {
  section: SectionName
  latest: number
  best: number
  average: number
  count: number
}
export interface Analytics {
  attempts_scored: number
  tasks: TaskStat[]
  weakest: TaskType[]
  sections: SectionSummary[]
  error_categories: Record<string, number>
  suggested_difficulty: Difficulty | null
}
export interface WeakSpotRequest {
  difficulty?: Difficulty
  exam_mode: 'exam' | 'practice'
  timed: boolean
  count: number
}
