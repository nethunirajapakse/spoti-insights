import SignUpForm from "@/components/auth/SignUpForm"; 

const SignUp = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b0b0b] p-6 relative overflow-hidden">
      
      {/* High-fidelity moving shapes passing perfectly behind the glass canvas */}
      <div className="absolute top-[15%] left-[20%] w-[450px] h-[450px] bg-[#53e076]/10 rounded-full blur-[130px] pointer-events-none animate-float-1" />
      <div className="absolute bottom-[10%] right-[15%] w-[400px] h-[400px] bg-emerald-600/5 rounded-full blur-[110px] pointer-events-none animate-float-2" />
      
      {/* Extra tracking subtle color layer */}
      <div className="absolute top-[50%] left-[45%] w-[250px] h-[250px] bg-teal-500/5 rounded-full blur-[90px] pointer-events-none animate-float-1" />

      <SignUpForm />
    </div>
  );
};

export default SignUp;
