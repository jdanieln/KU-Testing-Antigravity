import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function DoctorDiagnoses() {
    const [patients, setPatients] = useState([]);
    const [selectedPatient, setSelectedPatient] = useState(null);
    const [diagnoses, setDiagnoses] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Form state
    const [formData, setFormData] = useState({ symptoms: "", diagnosis: "", prescription: "" });

    const { currentUser } = useAuth();

    const fetchPatients = useCallback(async () => {
        if (!currentUser) return;
        const token = await currentUser.getIdToken();
        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL}/api/doctors/patients`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setPatients(data);
            }
        } catch (err) {
            console.error("Failed to fetch patients", err);
        }
    }, [currentUser]);

    useEffect(() => {
        fetchPatients();
    }, [fetchPatients]);

    const fetchPatientDiagnoses = async (patientId) => {
        if (!currentUser) return;
        const token = await currentUser.getIdToken();
        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL}/api/diagnoses/patient/${patientId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setDiagnoses(data);
            }
        } catch (err) {
            console.error("Failed to fetch diagnoses", err);
        }
    };

    const handleSelectPatient = (patient) => {
        setSelectedPatient(patient);
        setDiagnoses([]); // Clear previous
        fetchPatientDiagnoses(patient.uid);
    };

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmitDiagnosis = async (e) => {
        e.preventDefault();
        if (!currentUser || !selectedPatient || isSubmitting) return;

        setIsSubmitting(true);
        const token = await currentUser.getIdToken();

        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL}/api/diagnoses`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    patientId: selectedPatient.uid,
                    symptoms: formData.symptoms,
                    diagnosis: formData.diagnosis,
                    prescription: formData.prescription
                })
            });

            if (res.ok) {
                // Clear form and refresh diagnoses
                setFormData({ symptoms: "", diagnosis: "", prescription: "" });
                fetchPatientDiagnoses(selectedPatient.uid);
            } else {
                const errData = await res.json();
                alert(`Error: ${errData.error}`);
            }
        } catch (err) {
            console.error("Error creating diagnosis", err);
            alert("Error creating diagnosis.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="p-8 bg-gray-50 min-h-screen">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-3xl font-bold text-gray-800">Doctor Panel - Diagnoses</h1>
                    <Link to="/" className="text-blue-600 hover:underline">Back to Home</Link>
                </div>

                <div className="flex flex-col md:flex-row gap-6">
                    {/* Patients List Sidebar */}
                    <div className="w-full md:w-1/3 bg-white rounded-lg shadow p-4 h-fit">
                        <h2 className="text-xl font-semibold mb-4 border-b pb-2">Patients</h2>
                        <ul className="space-y-2">
                            {patients.map(patient => (
                                <li key={patient.uid}>
                                    <button
                                        onClick={() => handleSelectPatient(patient)}
                                        className={`w-full text-left p-3 rounded-md transition ${selectedPatient?.uid === patient.uid ? 'bg-indigo-50 border-indigo-200 border' : 'hover:bg-gray-100 border border-transparent'}`}
                                    >
                                        <p className="font-medium text-gray-900">{patient.displayName || 'No Name'}</p>
                                        <p className="text-sm text-gray-500">{patient.email}</p>
                                    </button>
                                </li>
                            ))}
                            {patients.length === 0 && <p className="text-sm text-gray-500">No patients found.</p>}
                        </ul>
                    </div>

                    {/* Main Content Area */}
                    <div className="w-full md:w-2/3 flex flex-col gap-6">
                        {!selectedPatient ? (
                            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500 h-full flex flex-col justify-center border-2 border-dashed border-gray-200">
                                <p>Select a patient from the list to view history or add a diagnosis.</p>
                            </div>
                        ) : (
                            <>
                                {/* New Diagnosis Form */}
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h2 className="text-xl font-semibold mb-4 text-indigo-700">New Diagnosis - {selectedPatient.displayName || selectedPatient.email}</h2>
                                    <form onSubmit={handleSubmitDiagnosis} className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Symptoms</label>
                                            <textarea required name="symptoms" value={formData.symptoms} onChange={handleInputChange} rows="2" className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2" placeholder="Patient symptoms..."></textarea>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Diagnosis</label>
                                            <textarea required name="diagnosis" value={formData.diagnosis} onChange={handleInputChange} rows="2" className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2" placeholder="Medical diagnosis..."></textarea>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Prescription (Optional)</label>
                                            <textarea name="prescription" value={formData.prescription} onChange={handleInputChange} rows="2" className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2" placeholder="Medications or treatment plan..."></textarea>
                                        </div>
                                        <div className="flex justify-end">
                                            <button type="submit" disabled={isSubmitting} className="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 transition disabled:opacity-50 flex items-center justify-center min-w-[140px]">
                                                {isSubmitting ? 'Saving...' : 'Save Diagnosis'}
                                            </button>
                                        </div>
                                    </form>
                                </div>

                                {/* Patient History */}
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h2 className="text-xl font-semibold mb-4 border-b pb-2">Medical History</h2>
                                    {diagnoses.length === 0 ? (
                                        <p className="text-gray-500 italic">No previous diagnoses found for this patient.</p>
                                    ) : (
                                        <div className="space-y-6">
                                            {diagnoses.map(diag => {
                                                const dateStr = diag.createdAt ? new Date(diag.createdAt._seconds * 1000).toLocaleString() : 'Just now';
                                                return (
                                                    <div key={diag.id} className="bg-gray-50 p-4 rounded-md border border-gray-200">
                                                        <div className="flex justify-between items-start mb-2">
                                                            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{dateStr}</p>
                                                            <p className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded-full">By: {diag.doctorName}</p>
                                                        </div>
                                                        <div className="space-y-2 mt-3">
                                                            <p><span className="font-semibold text-gray-700 text-sm">Symptoms:</span><br /><span className="text-gray-800">{diag.symptoms}</span></p>
                                                            <p><span className="font-semibold text-gray-700 text-sm">Diagnosis:</span><br /><span className="text-gray-800">{diag.diagnosis}</span></p>
                                                            {diag.prescription && (
                                                                <p><span className="font-semibold text-gray-700 text-sm">Prescription:</span><br /><span className="text-gray-800">{diag.prescription}</span></p>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
