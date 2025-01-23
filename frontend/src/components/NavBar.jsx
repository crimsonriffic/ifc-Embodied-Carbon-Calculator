import { NavLink } from "react-router-dom";
import { useUser } from "../context/UserContext";

function Navbar() {
  const { username } = useUser();
  return (
    <div className="bg-[#5B9130] text-white fixed top-0 left-0 w-full z-10 shadow-md">
      <div className=" mx-auto px-4 flex justify-between items-center h-16">
        {/* Left section: Logo and navigation */}
        <div className="flex items-center space-x-8">
          {/* Logo */}
          <div className="flex items-center">
            <div className="bg-white rounded-full p-2">
              <h1 className="text-[#5B9130] font-bold text-lg">
                eCO2llaborate
              </h1>
            </div>
          </div>

          {/* Navigation links */}
          <nav className="flex space-x-6">
            <NavLink
              to="/home"
              className={({ isActive }) =>
                isActive ? "underline font-semibold" : "hover:underline"
              }
            >
              Home
            </NavLink>
            <NavLink
              to="/project"
              className={({ isActive }) =>
                isActive ? "underline font-semibold" : "hover:underline"
              }
            >
              Project Details
            </NavLink>
          </nav>
        </div>

        {/* Right section: Username */}
        <div className="flex items-center">
          <div className="bg-white text-[#5B9130] px-4 py-2 rounded-md shadow-md">
            Hi {username || "Guest"}!
          </div>
        </div>
      </div>
    </div>
  );
}

export default Navbar;
