import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Unauthorized from "./pages/Unauthorized";

function Home() {
  const { currentUser, userRole, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-md">
        <h1 className="text-3xl font-bold text-blue-600 mb-2">Clinical Connect</h1>

        {currentUser ? (
          <div className="mt-4">
            <p className="text-gray-800">Welcome, <span className="font-semibold">{currentUser.displayName}</span></p>
            <p className="text-sm text-gray-500 mb-4">Role: <span className="font-mono bg-gray-200 px-1 rounded">{userRole || 'Loading...'}</span></p>

            <button onClick={logout} className="w-full bg-red-500 text-white py-2 rounded mb-4 hover:bg-red-600">Logout</button>

            <div className="border-t pt-4 text-left">
              <p className="font-semibold mb-2">Quick Links:</p>
              <ul className="list-disc pl-5 text-blue-600 space-y-1">
                <li><Link to="/patient/history">My History (Patient)</Link></li>
                <li><Link to="/doctor/diagnoses">Diagnoses (Doctor)</Link></li>
                <li><Link to="/admin/dashboard">Admin Dashboard (Super Admin)</Link></li>
              </ul>
            </div>
          </div>
        ) : (
          <div className="mt-6">
            <p className="mb-4 text-gray-600">Please log in to continue.</p>
            <Link to="/login" className="block w-full bg-blue-600 text-white text-center py-2 rounded hover:bg-blue-700">Go to Login</Link>
          </div>
        )}
      </div>
    </div>
  );
}

function PatientHistory() { return <h1 className="p-8 text-2xl">Patient Medical History</h1> }
function DoctorDiagnoses() { return <h1 className="p-8 text-2xl">Doctor Diagnoses Panel</h1> }
function AdminDashboard() { return <h1 className="p-8 text-2xl">Super Admin Dashboard</h1> }

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          <Route path="/" element={<Home />} />

          {/* Protected Routes */}
          <Route
            path="/patient/history"
            element={
              <ProtectedRoute allowedRoles={['PATIENT', 'SUPER_ADMIN']}>
                <PatientHistory />
              </ProtectedRoute>
            }
          />
          <Route
            path="/doctor/diagnoses"
            element={
              <ProtectedRoute allowedRoles={['DOCTOR', 'SUPER_ADMIN']}>
                <DoctorDiagnoses />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
