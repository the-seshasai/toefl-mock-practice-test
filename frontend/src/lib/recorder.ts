import { useEffect, useState } from 'react'

export interface RecordingResult {
  blob: Blob
  durationMs: number
}

export function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === 'undefined') return undefined
  return ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'].find((m) => MediaRecorder.isTypeSupported(m))
}

/** Thin MediaRecorder wrapper: start(), then stop() resolves with the recorded blob and its duration. */
export class Recorder {
  private rec: MediaRecorder
  private chunks: Blob[] = []
  private startedAt = 0

  constructor(stream: MediaStream) {
    const mimeType = pickMimeType()
    this.rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
    this.rec.ondataavailable = (e) => {
      if (e.data.size > 0) this.chunks.push(e.data)
    }
  }

  start(): void {
    this.startedAt = Date.now()
    this.rec.start(250)
  }

  stop(): Promise<RecordingResult> {
    return new Promise((resolve) => {
      const finish = () => resolve({ blob: new Blob(this.chunks, { type: this.rec.mimeType || 'audio/webm' }), durationMs: Date.now() - this.startedAt })
      if (this.rec.state === 'inactive') return finish()
      this.rec.onstop = finish
      this.rec.stop()
    })
  }

  abort(): void {
    this.rec.ondataavailable = null
    if (this.rec.state !== 'inactive') this.rec.stop()
  }
}

/** Live input level (0..1) of a stream, for the microphone check and the recording indicator. */
export function useAudioLevel(stream: MediaStream | null): number {
  const [level, setLevel] = useState(0)
  useEffect(() => {
    if (!stream) return
    const ctx = new AudioContext()
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 512
    ctx.createMediaStreamSource(stream).connect(analyser)
    const data = new Uint8Array(analyser.fftSize)
    let raf = 0
    const tick = () => {
      analyser.getByteTimeDomainData(data)
      let sum = 0
      for (const v of data) sum += ((v - 128) / 128) ** 2
      setLevel(Math.min(1, Math.sqrt(sum / data.length) * 4))
      raf = requestAnimationFrame(tick)
    }
    tick()
    return () => {
      cancelAnimationFrame(raf)
      void ctx.close()
    }
  }, [stream])
  return stream ? level : 0
}
