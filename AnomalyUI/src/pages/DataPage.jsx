import React from 'react'
import AdminDataPanel from '../components/AdminDataPanel'

export default function DataPage({ token }) {
  return (
    <section className="page-split">
      <AdminDataPanel token={token} />
    </section>
  )
}
