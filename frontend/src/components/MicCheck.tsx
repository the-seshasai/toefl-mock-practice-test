import { useEffect, useState } from 'react'
import { useAudioLevel } from '../lib/recorder'

type State = 'idle' | 'asking' | 'ok' | 'denied'

/** Asks for microphone permission and shows a live level so the test taker can confirm it works. */
export default function MicCheck({ onResult }: { onResult: (ok: boolean) => void }) {
  const [state, setState] = useState<State>('idle')
  const [stream, setStream] = useState<MediaStream | null>(null)
  const level = useAudioLevel(stream)

  useEffect(() => () => stream?.getTracks().forEach((t) => t.stop()), [stream])

  const enable = async () => {
    setState('asking')
    try {
      setStream(await navigator.mediaDevices.getUserMedia({ audio: true }))
      setState('ok')
      onResult(true)
    } catch {
      setState('denied')
      onResult(false)
    }
  }

  return (
    <div className="rounded border bg-slate-50 p-4">
      <p className="font-medium">Microphone check</p>
      {state === 'ok' ? (
        <>
          <p className="mt-1 text-sm text-slate-600">Say a few words. The bar should move.</p>
          <div className="mt-2 h-3 w-64 overflow-hidden rounded bg-slate-200" role="meter" aria-valuenow={Math.round(level * 100)}>
            <div className="h-full bg-green-600 transition-[width] duration-75" style={{ width: `${Math.round(level * 100)}%` }} />
          </div>
        </>
      ) : (
        <>
          <p className="mt-1 text-sm text-slate-600">Speaking needs your microphone. Your recordings stay on this computer.</p>
          <button className="mt-2 rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50" disabled={state === 'asking'} onClick={() => void enable()}>
            {state === 'asking' ? 'Waiting for permission…' : state === 'denied' ? 'Try again' : 'Enable microphone'}
          </button>
          {state === 'denied' && (
            <p className="mt-2 text-sm text-red-600">
              The microphone is blocked or missing. Allow it in the browser's address bar (site settings), then try again.
            </p>
          )}
        </>
      )}
    </div>
  )
}
