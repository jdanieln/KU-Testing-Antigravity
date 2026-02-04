import { Link } from "react-router-dom";

export default function Unauthorized() {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-4">
            <h1 className="text-4xl font-bold text-red-600 mb-2">403 - Unauthorized</h1>
            <p className="text-gray-700 mb-6">You do not have permission to access this page.</p>
            <Link to="/" className="text-blue-600 hover:underline">Go back home</Link>
        </div>
    );
}
