import ExamRunner from './pages/ExamRunner'
import History from './pages/History'
import Results from './pages/Results'
import Setup from './pages/Setup'
import { navigate, useRoute } from './route'

export default function App() {
  const route = useRoute()
  const attempt = /^\/attempt\/(\d+)$/.exec(route)
  const results = /^\/results\/(\d+)$/.exec(route)

  return (
    <div className="min-h-screen bg-white text-slate-900">
      <nav className="border-b px-8 py-3">
        <button className="font-semibold" onClick={() => navigate('/')}>
          TOEFL Practice
        </button>
        <button className="ml-6 text-slate-600" onClick={() => navigate('/history')}>
          History
        </button>
      </nav>
      <main className="mx-auto max-w-5xl p-8">
        {route === '/history' ? <History /> : attempt ? <ExamRunner key={attempt[1]} attemptId={Number(attempt[1])} /> : results ? <Results key={results[1]} attemptId={Number(results[1])} /> : <Setup />}
      </main>
    </div>
  )
}
