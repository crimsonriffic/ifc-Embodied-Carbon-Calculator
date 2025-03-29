import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";

function LoginPage() {
  const [inputUsername, setInputUsername] = useState("");
  const { setUsername } = useUser();
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    if (inputUsername.trim()) {
      setUsername(inputUsername);
      console.log("inputUsername:", inputUsername);
      console.log("Password:", password);
      navigate("/home");
    } else {
      alert("Please enter a username");
    }
  };

  return (
    // Full-screen background container
    <div
      className="fixed inset-0 w-full h-full bg-cover bg-center"
      style={{
        backgroundImage: `url('/loginbg.png')`,
      }}
    >
      {/* Centered content container */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex flex-col items-center">
          {/* Logo */}
          <div className="mb-16">
            <div className="bg-green-600 rounded-full px-8 py-3">
              <h1 className="text-white text-xl">CarbonSmart</h1>
            </div>
          </div>

          {/* Login Form */}
          <div className="w-full max-w-xs">
            <form onSubmit={handleLogin} className="space-y-4">
              {/* inputUsername Input */}
              <div>
                <input
                  type="text"
                  id="inputUsername"
                  value={inputUsername}
                  onChange={(e) => setInputUsername(e.target.value)}
                  className="w-full px-4 py-2 bg-white bg-opacity-20 border border-white border-opacity-30 rounded text-white placeholder-white focus:outline-none"
                  placeholder="USERNAME"
                  required
                />
              </div>

              {/* Password Input */}
              <div>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-2 bg-white bg-opacity-20 border border-white border-opacity-30 rounded text-white placeholder-white focus:outline-none"
                  placeholder="PASSWORD"
                  required
                />
              </div>

              {/* Login Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  className="w-full py-2 bg-white text-gray-700 rounded font-medium hover:bg-opacity-90 transition-colors duration-200"
                >
                  LOGIN
                </button>
              </div>

              {/* Forgot Password Link */}
              <div className="text-center pt-2">
                <a href="#" className="text-white text-sm hover:underline">
                  Forgot password?
                </a>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
