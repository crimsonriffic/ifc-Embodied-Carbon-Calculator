import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";

function LoginTab() {
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
      navigate("/activeProjects");
    } else {
      alert("Please enter a username");
    }
  };

  return (
    <div>
      {/* Centered content container */}
      <div className="flex flex-col mt-4">
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
                className="w-full px-4 py-2 bg-[#A9C0A0]  border border-white border-opacity-30 rounded text-white text-xl placeholder-white focus:outline-none"
                placeholder="Username"
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
                className="w-full px-4 py-2 bg-[#A9C0A0] border border-white border-opacity-30 rounded text-white text-xl placeholder-white focus:outline-none"
                placeholder="Password"
                required
              />
            </div>

            {/* Login Button */}
            <div className="pt-2">
              <button
                type="submit"
                className=" px-4 py-2 bg-white text-[#5B9130] text-xl rounded font-medium hover:bg-opacity-90 transition-colors duration-200"
              >
                Login
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default LoginTab;
