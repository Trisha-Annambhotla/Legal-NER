import React from 'react'

const LABELS = {
  PERSON:   'Person',
  ORG:      'Organisation',
  DATE:     'Date',
  MONEY:    'Amount',
  LOCATION: 'Location',
  LAW:      'Legal Ref',
  UNKNOWN:  'Unknown',
}

export default function EntityTag({ type }) {
  return (
    <span className={`tag tag--${type}`}>
      {LABELS[type] || type}
    </span>
  )
}
