import { Navigate, Outlet } from "react-router-dom";
import { useCurrentUser } from "@/hooks/useCurrentUser";

const ProtectedRoute = () => {
  const { data, isLoading, isError } = useCurrentUser();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  if (isError || !data) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;