import React, { useState } from 'react'

export default function TruncatedCell({ value }) {
  const [expanded, setExpanded] = useState(false)
  
  if (value === null || value === undefined) {
    return <span>—</span>
  }
  
  const strVal = String(value).trim()
  if (strVal === '' || strVal === '—' || strVal === 'None' || strVal === 'NaN') {
    return <span>—</span>
  }
  
  if (strVal.length <= 20) {
    return <span>{strVal}</span>
  }
  
  if (expanded) {
    return (
      <span className="whitespace-normal break-words">
        {strVal}
        {' '}
        <span 
          onClick={(e) => {
            e.stopPropagation()
            setExpanded(false)
          }} 
          className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 cursor-pointer font-semibold underline select-none ml-1 inline-block"
        >
          see less
        </span>
      </span>
    )
  }
  
  const truncated = strVal.slice(0, 20)
  return (
    <span className="whitespace-normal break-words">
      {truncated}
      <span>..... </span>
      <span 
        onClick={(e) => {
          e.stopPropagation()
          setExpanded(true)
        }} 
        className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 cursor-pointer font-semibold underline select-none inline-block"
      >
        see more
      </span>
    </span>
  )
}
