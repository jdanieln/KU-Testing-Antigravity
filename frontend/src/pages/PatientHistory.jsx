import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function PatientHistory() {
    const [diagnoses, setDiagnoses] = useState([]);
    const [loading, setLoading] = useState(true);

    const { currentUser } = useAuth();

    const fetchMyHistory = useCallback(async () => {
        if (!currentUser) return;
        const token = await currentUser.getIdToken();
        try {
            setLoading(true);
            const res = await fetch(`${import.meta.env.VITE_API_URL}/api/diagnoses/patient/${currentUser.uid}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setDiagnoses(data);
            } else {
                console.error("Failed to load history");
            }
        } catch (err) {
            console.error("Failed to fetch history", err);
        } finally {
            setLoading(false);
        }
    }, [currentUser]);

    useEffect(() => {
        fetchMyHistory();
    }, [fetchMyHistory]);

    return (
        <div className="p-8 bg-gray-50 min-h-screen">
            <div className="max-w-4xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">My Medical History</h1>
                        <p className="text-gray-500 mt-1">View all your past consultations and prescriptions.</p>
                    </div>
                    <Link to="/" className="text-blue-600 hover:underline bg-white px-4 py-2 rounded shadow-sm border">Back to Home</Link>
                </div>

                {loading ? (
                    <div className="flex justify-center py-20">
                        <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    </div>
                ) : diagnoses.length === 0 ? (
                    <div className="bg-white rounded-xl shadow-sm p-12 text-center border">
                        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <h3 className="text-lg font-medium text-gray-900">No medical history found</h3>
                        <p className="mt-1 text-gray-500">When a doctor creates a diagnosis for you, it will appear here.</p>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {diagnoses.map(diag => {
                            const dateObj = diag.createdAt ? new Date(diag.createdAt._seconds * 1000) : new Date();
                            const formattedDate = dateObj.toLocaleDateString();
                            const formattedTime = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                            return (
                                <div key={diag.id} className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100 hover:shadow-md transition">
                                    <div className="bg-indigo-50 px-6 py-4 border-b border-indigo-100 flex flex-col sm:flex-row sm:justify-between sm:items-center">
                                        <div className="flex items-center gap-3">
                                            <div className="bg-indigo-100 text-indigo-700 p-2 rounded-full">
                                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                                            </div>
                                            <div>
                                                <p className="text-sm text-gray-500 font-medium">Attending Doctor</p>
                                                <p className="font-semibold text-indigo-900">{diag.doctorName}</p>
                                            </div>
                                        </div>
                                        <div className="text-left sm:text-right mt-2 sm:mt-0">
                                            <p className="text-gray-800 font-medium">{formattedDate}</p>
                                            <p className="text-gray-500 text-sm">{formattedTime}</p>
                                        </div>
                                    </div>
                                    <div className="p-6 space-y-4">
                                        <div>
                                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Symptoms Reported</h4>
                                            <p className="text-gray-800 bg-gray-50 p-3 rounded-md">{diag.symptoms}</p>
                                        </div>
                                        <div>
                                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Medical Diagnosis</h4>
                                            <p className="text-gray-800 bg-gray-50 p-3 rounded-md">{diag.diagnosis}</p>
                                        </div>
                                        {diag.prescription && (
                                            <div>
                                                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">Prescription / Treatment</h4>
                                                <p className="text-indigo-900 bg-indigo-50/50 p-3 rounded-md border border-indigo-50">{diag.prescription}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
