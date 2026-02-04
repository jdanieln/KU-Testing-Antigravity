import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, allowedRoles }) {
    const { currentUser, userRole } = useAuth();

    if (!currentUser) {
        return <Navigate to="/login" />;
    }

    if (allowedRoles && userRole && !allowedRoles.includes(userRole)) {
        return <Navigate to="/unauthorized" />;
    }

    return children;
}
