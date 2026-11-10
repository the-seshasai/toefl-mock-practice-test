import { useEffect, useRef, useState } from 'react'

type State = 'idle' | 'loading' | 'playing' | 'ended' | 'blocked' | 'error'

interface Props {
  src: string
  /** Exam mode: the clip plays once, with no replay or seeking. Practice mode: replay allowed. */
  once: boolean
  /** The server says the one allowed play was already used (e.g. after a refresh). */
  alreadyPlayed?: boolean
  onEnded?: () => void
}

/** Fetches the clip once into memory and plays it from there, so a single server fetch equals a single play. */
export default function AudioPlayer({ src, once, alreadyPlayed = false, onEnded }: Props) {
  const [state, setState] = useState<State>(alreadyPlayed ? 'blocked' : 'idle')
  const [progress, setProgress] = useState(0)
  const audio = useRef<HTMLAudioElement | null>(null)
  const blobUrl = useRef<string | null>(null)
  const onEndedRef = useRef(onEnded)
  useEffect(() => {
    onEndedRef.current = onEnded
  })

  useEffect(
    () => () => {
      audio.current?.pause()
      if (blobUrl.current) URL.revokeObjectURL(blobUrl.current)
    },
    [],
  )

  const play = async () => {
    try {
      if (!blobUrl.current) {
        setState('loading')
        const res = await fetch(src, { cache: 'no-store' })
        if (res.status === 403 || res.status === 409) {
          setState('blocked')
          onEndedRef.current?.()
          return
        }
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        blobUrl.current = URL.createObjectURL(await res.blob())
      }
      const el = new Audio(blobUrl.current)
      audio.current = el
      el.ontimeupdate = () => setProgress(el.duration ? el.currentTime / el.duration : 0)
      el.onended = () => {
        el.ontimeupdate = null // a late timeupdate must not move the bar back from 100%
        setProgress(1)
        setState('ended')
        if (once && blobUrl.current) {
          URL.revokeObjectURL(blobUrl.current) // exam mode: the clip is gone once it has played
          blobUrl.current = null
        }
        onEndedRef.current?.()
      }
      el.onerror = () => setState('error')
      setProgress(0)
      setState('playing')
      await el.play()
    } catch {
      setState('error')
    }
  }

  return (
    <div className="rounded border bg-slate-50 p-4" role="group" aria-label="Audio player">
      <div className="flex items-center gap-4">
        {(state === 'idle' || state === 'error' || (state === 'ended' && !once)) && (
          <button className="rounded bg-blue-600 px-5 py-3 text-white" onClick={() => void play()}>
            {state === 'ended' ? '↻ Replay audio' : state === 'error' ? 'Retry audio' : '▶ Play audio'}
          </button>
        )}
        {state === 'loading' && <span className="text-slate-600">Loading audio…</span>}
        {state === 'playing' && <span className="font-medium text-blue-700">Playing…</span>}
        {state === 'ended' && once && <span className="text-slate-600">Audio finished. It cannot be replayed.</span>}
        {state === 'blocked' && <span className="text-slate-600">The audio for this item has already been played.</span>}
        {state === 'error' && <span className="text-red-600">Audio could not be played.</span>}
        {(state === 'idle' || state === 'error') && once && <span className="text-sm text-slate-500">Audio plays once.</span>}
      </div>
      {(state === 'playing' || state === 'ended') && (
        <div className="mt-3 h-2 overflow-hidden rounded bg-slate-200" aria-hidden>
          <div className="h-full bg-blue-600 transition-[width]" style={{ width: `${Math.round(progress * 100)}%` }} />
        </div>
      )}
    </div>
  )
}
