import { NavLink, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useUser } from "../context/UserContext";
import { ChevronDownIcon } from "@heroicons/react/24/solid";
import React from "react";

function Navbar() {
  const { username, setUsername } = useUser();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = () => {
    setUsername(null);
    navigate("/");
  };

  const handleSettingsClick = () => {
    setIsOpen(true);
  };
  return (
    <div className="bg-white text-gray-500 fixed top-0 left-0 w-full z-10 border-b border-gray-300 ">
      <div className=" mx-auto px-4 flex justify-between items-center h-16 p-6 md:px-36">
        {/* Left section: Logo and navigation */}
        <div className="flex items-center space-x-8">
          {/* Logo */}
          <div className="flex items-center">
            <div className="bg-white rounded-full p-4">
              <h1 className="text-[#5B9130] font-bold text-lg">ECcalculator</h1>
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
              to="/createProject"
              className={({ isActive }) =>
                isActive ? "underline font-semibold" : "hover:underline"
              }
            >
              Create Project
            </NavLink>
            <NavLink
              to="/materialInfo"
              className={({ isActive }) =>
                isActive ? "underline font-semibold" : "hover:underline"
              }
            >
              Material Info
            </NavLink>
          </nav>
        </div>

        {/* Right section: Username */}
        <button
          onClick={handleSettingsClick}
          className="flex items-center border rounded-lg shadow-md"
        >
          <div className="bg-white text-[#5B9130] px-2 py-2 rounded-lg">
            {username || "Guest"}
          </div>
          <ChevronDownIcon className="w-5 h-5 text-[#5B9130] mr-1" />
        </button>
      </div>
      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white border rounded-lg shadow-lg z-10">
          <div className="p-4 text-gray-700">
            <p className="font-semibold">{username || "Guest"}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full text-left px-4 py-2 text-gray-500 border hover:bg-red-100"
          >
            Logout
          </button>
        </div>
      )}
    </div>
  );
}

export default Navbar;
