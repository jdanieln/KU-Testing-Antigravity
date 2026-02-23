import { createContext, useContext, useState, useEffect } from "react";
import {
    signInWithPopup,
    signOut,
    onAuthStateChanged
} from "firebase/auth";
import { auth, googleProvider } from "../firebase";

const AuthContext = createContext();

export function useAuth() {
    return useContext(AuthContext);
}

export function AuthProvider({ children }) {
    const [currentUser, setCurrentUser] = useState(null);
    const [userRole, setUserRole] = useState(null); // 'SUPER_ADMIN', 'DOCTOR', 'ASSISTANT', 'PATIENT'
    const [loading, setLoading] = useState(true);

    function loginWithGoogle() {
        return signInWithPopup(auth, googleProvider);
    }

    function logout() {
        return signOut(auth);
    }

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (user) => {
            setCurrentUser(user);

            if (user) {
                // Sync user with backend and get role
                try {
                    const token = await user.getIdToken();
                    console.log(import.meta.env.VITE_API_URL, "API URL");
                    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/sync`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        console.log("DEBUG: Role fetched:", data.role);
                        setUserRole(data.role);
                    } else {
                        console.error("Failed to sync user role");
                        // Fallback or handle error
                        setUserRole('PATIENT');
                    }
                } catch (error) {
                    console.error("Error fetching user role:", error);
                    alert(`Error syncing role: ${error.message}`);
                    setUserRole('PATIENT');
                }
            } else {
                setUserRole(null);
            }

            setLoading(false);
        });

        return unsubscribe;
    }, []);

    const value = {
        currentUser,
        userRole,
        loginWithGoogle,
        logout
    };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    );
}
