import React from 'react'
import { Link } from 'react-router-dom'

export default function NavButton({ item, active, badge }) {
  return (
    
    <Link to={item.path} className={active ? "nav-item active" : "nav-item"}>
      <span className="nav-item-label">
        <h3>{item.label}</h3>
        <small>{item.description}</small>
      </span>
      {badge ? <span className="nav-badge">{badge}</span> : null}
    </Link>

  )
}
