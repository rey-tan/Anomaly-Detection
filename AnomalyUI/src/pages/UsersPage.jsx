import React from 'react'
import UsersPanel from '../components/UsersPanel'

export default function UsersPage({ token, user, onOpenActivity }) {
  return (
    <section className="page-split">
      <div className="page-panel">
        <div className="page-intro">
          <p className="eyebrow">Admin dashboard</p>
          <h2>Manage users</h2>
          <p>Assign roles to users and manage their access to the application.</p>
        </div>
        <UsersPanel token={token} currentUser={user} onOpenActivity={onOpenActivity} />
      </div>
    </section>
  )
}
