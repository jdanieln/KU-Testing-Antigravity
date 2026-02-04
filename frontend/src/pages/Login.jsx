import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function Login() {
    const { loginWithGoogle, currentUser } = useAuth();
    const navigate = useNavigate();

    const handleLogin = async () => {
        try {
            await loginWithGoogle();
            navigate("/");
        } catch (error) {
            console.error("Failed to login", error);
        }
    };

    if (currentUser) {
        navigate("/");
        return null;
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="bg-white p-8 rounded-xl shadow-lg max-w-sm w-full text-center">
                <h2 className="text-2xl font-bold mb-6 text-gray-800">Welcome Back</h2>
                <p className="text-gray-600 mb-6">Sign in to access your dashboard</p>
                <button
                    onClick={handleLogin}
                    className="w-full bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 transition duration-300 flex items-center justify-center gap-2"
                >
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" className="w-5 h-5" alt="Google" />
                    Sign in with Google
                </button>
            </div>
        </div>
    );
}
