type ButtonVariant = "primary" | "secondary" | "danger";

type IconProps = {
  className: string;
};

type ButtonProps = {
  label: string;
  onClick?: () => void;
  isLoading?: boolean;
  disabled?: boolean;
  variant?: ButtonVariant;
  className?: string;
  type?: "button" | "submit" | "reset";
  Icon?: (props: IconProps) => any; 
};

const baseStyles =
  "px-6 py-2 font-semibold rounded-full transition duration-200 shadow-md disabled:opacity-50 flex items-center justify-center gap-3";

const variantStyles: Record<ButtonVariant, string> = {
  primary: "bg-green-500 hover:bg-green-600 text-white",
  secondary: "bg-gray-200 hover:bg-gray-300 text-gray-800",
  danger: "bg-red-500 hover:bg-red-600 text-white",
};

const Button = ({
  label,
  onClick,
  isLoading = false,
  disabled = false,
  variant = "primary",
  className = "",
  type = "button",
  Icon,
}: ButtonProps) => {
  const isDisabled = disabled || isLoading;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
    >
      {isLoading ? (
        "Loading..."
      ) : (
        <>
          {Icon ? <Icon className="w-6 h-6 fill-current" /> : null}
          <span>{label}</span>
        </>
      )}
    </button>
  );
};

export default Button;
