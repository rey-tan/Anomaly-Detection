import React from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import MainLayout from '../layouts/MainLayout'
import DashboardPage from '../pages/Dashboard'
import AnalysisPage from '../pages/AnalysisPage'
import ResultsPage from '../pages/ResultsPage'
import UsersPage from '../pages/UsersPage'
import DataPage from '../pages/DataPage'
import ActivityPage from '../pages/ActivityPage'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'

export default function AppRoutes(props) {
  const navigate = useNavigate();
  const {
    user,
    token,
    results,
    selectedAnalysis,
    setResults,
    setSelectedAnalysis,  
    activityUser,
    handleOpenLastRun,
    handleSelectAnalysis,
    onLogout,
    setActivityUser,
    handleLogin,
  } = props;

  return (
    <Routes>
      <Route
        path="/login"
        element={token ? <Navigate to="/dashboard" replace /> : <LoginPage onSuccess={handleLogin} />}
      />
      <Route
        path="/register"
        element={token ? <Navigate to="/dashboard" replace /> : <RegisterPage />}
      />
      <Route
        path="/"
        element={token ? (
          <MainLayout
            user={user}
            token={token}
            results={results}
            selectedAnalysis={selectedAnalysis}
            onLogout={onLogout}
            handleOpenLastRun={handleOpenLastRun}
          />
        ) : (
          <Navigate to="/login" replace />
        )}
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage user={user} selectedAnalysis={selectedAnalysis} results={results} onOpenLastRun={handleOpenLastRun} />} />
        <Route path="analysis" element={<AnalysisPage  token = {token} setResults={setResults} setSelectedAnalysis = {setSelectedAnalysis}/>} />
        <Route path="results" element={<ResultsPage token={token} results={results} selectedAnalysis={selectedAnalysis} setResults={setResults} setSelectedAnalysis={setSelectedAnalysis}  navigate={navigate} handleSelectAnalysis={handleSelectAnalysis} />} />
        <Route path="activity" element={
          user?.role === 'admin' ? (
            <ActivityPage token={token} initialUserId={activityUser} />
          ) : (
            <section className="empty-state-card">
              <h2>Admin access required</h2>
              <p>Only admin users can open the activity page.</p>
            </section>
          )
        } />
        <Route
          path="users"
          element={
            user?.role === 'admin' ? (
              <UsersPage token={token} user={user} onOpenActivity={(id) => {
                setActivityUser(id)
                navigate('/activity')
              }} />
            ) : (
              <section className="empty-state-card">
                <h2>Admin access required</h2>
                <p>Only admin users can open the user management page.</p>
              </section>
            )
          }
        />
       
        <Route
          path="data"
          element={
            user?.role === 'admin' ? (
              <DataPage token={token} />
            ) : (
              <section className="empty-state-card">
                <h2>Admin access required</h2>
                <p>Only admin users can open the data management page.</p>
              </section>
            )
          }
        />
      </Route>
      <Route path="*" element={<Navigate to={token ? "/dashboard" : "/login"} replace />} />
    </Routes>
  )
}
