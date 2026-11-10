import { useEffect, useRef, useState } from 'react'

interface Props {
  deadline: string | null
  /** serverNow - clientNow in ms, so the countdown follows the server clock */
  offsetMs: number
  onExpire: () => void
}

function format(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000))
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
}

export default function Timer({ deadline, offsetMs, onExpire }: Props) {
  const [remaining, setRemaining] = useState<number | null>(null)
  const fired = useRef<string | null>(null)
  const onExpireRef = useRef(onExpire)
  useEffect(() => {
    onExpireRef.current = onExpire
  })

  useEffect(() => {
    if (!deadline) return
    const target = Date.parse(deadline)
    const tick = () => {
      const left = target - (Date.now() + offsetMs)
      setRemaining(left)
      if (left <= 0 && fired.current !== deadline) {
        fired.current = deadline
        onExpireRef.current()
      }
    }
    tick()
    const id = window.setInterval(tick, 250)
    return () => window.clearInterval(id)
  }, [deadline, offsetMs])

  if (!deadline) return <span className="rounded bg-slate-100 px-3 py-1 text-sm text-slate-600">Untimed practice</span>
  const low = remaining !== null && remaining < 60_000
  return (
    <span
      className={`rounded px-3 py-1 font-mono text-lg ${low ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-800'}`}
      aria-label="Time remaining"
    >
      {remaining === null ? '--:--' : format(remaining)}
    </span>
  )
}
