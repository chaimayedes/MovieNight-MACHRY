import { useState } from 'react'

export default function StarRating({ onRate, submitted }) {
  const [hovered,  setHovered]  = useState(0)
  const [selected, setSelected] = useState(0)

  const handle = (val) => {
    if (submitted) return
    setSelected(val)
    onRate(val)
  }

  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          disabled={submitted}
          onMouseEnter={() => !submitted && setHovered(star)}
          onMouseLeave={() => setHovered(0)}
          onClick={() => handle(star)}
          className={`text-3xl transition-all duration-100 disabled:cursor-default
            ${star <= (hovered || selected) ? 'text-amber-500' : 'text-gray-700'}
            ${!submitted ? 'hover:scale-110' : ''}`}
        >
          ★
        </button>
      ))}
    </div>
  )
}
