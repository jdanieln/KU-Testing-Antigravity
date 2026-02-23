import { useState, useEffect } from "react";
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
function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const { currentUser } = useAuth();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    if (!currentUser) return;
    const token = await currentUser.getIdToken();
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
      }
    } catch (err) {
      console.error("Failed to fetch users", err);
    }
  };

  const handleRoleChange = async (uid, newRole) => {
    if (!currentUser) return;
    const token = await currentUser.getIdToken();
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/admin/users/${uid}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ role: newRole })
      });
      if (res.ok) {
        alert("Role updated!");
        fetchUsers(); // Refresh list
      } else {
        alert("Failed to update role");
      }
    } catch (err) {
      console.error("Error updating role", err);
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Admin Dashboard</h1>
          <Link to="/" className="text-blue-600 hover:underline">Back to Home</Link>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map(user => (
                <tr key={user.uid}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{user.displayName || 'No Name'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{user.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                            ${user.role === 'SUPER_ADMIN' ? 'bg-purple-100 text-purple-800' :
                        user.role === 'DOCTOR' ? 'bg-green-100 text-green-800' :
                          user.role === 'ASSISTANT' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'}`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <select
                      value={user.role}
                      onChange={(e) => handleRoleChange(user.uid, e.target.value)}
                      className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    >
                      <option value="Same" disabled>Change Role...</option>
                      <option value="PATIENT">PATIENT</option>
                      <option value="DOCTOR">DOCTOR</option>
                      <option value="ASSISTANT">ASSISTANT</option>
                      <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

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
