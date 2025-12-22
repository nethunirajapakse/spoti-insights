import SignIn from "@/components/SpotifyAuthForm"; 

const Login = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <SignIn />
    </div>
  );
};

export default Login;
