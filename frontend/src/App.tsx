import { useState } from 'react'
import spotiInsightsLogo from './assets/logo.svg'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-blue-100 p-6">
      <div className="flex gap-6 mb-8">
        <a href="https://vite.dev" target="_blank" className="transition-transform hover:scale-110">
          <img src={spotiInsightsLogo} className="w-20 h-20" alt="Vite logo" />
        </a>
      </div>

      <h1 className="text-8xl font-bold text-gray-800 mb-6">Vite + React</h1>

      <div className="card bg-white shadow-md rounded-xl p-6 flex flex-col items-center gap-4">
        <button
          onClick={() => setCount((count) => count + 1)}
          className="px-6 py-3 bg-blue-500 text-white font-semibold rounded-lg shadow hover:bg-blue-600 transition"
        >
          count is {count}
        </button>
        <p className="text-gray-600 text-center">
          Edit <code className="bg-gray-100 px-1 rounded">src/App.tsx</code> and save to test HMR
        </p>
      </div>

      <p className="mt-8 text-gray-700 text-center max-w-md">
        Click on the Vite and React logos to learn more
      </p>
    </div>
  )
}

export default App
