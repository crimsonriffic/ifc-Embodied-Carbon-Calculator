import { NavLink, Routes, Route } from "react-router-dom";

function UploadTabs() {
  return (
    <nav className="flex space-x-6 border-b border-gray-200">
      <NavLink
        to="/uploadOverview"
        className={({ isActive }) =>
          isActive
            ? "pb-2 border-b-2 border-black font-bold text-black"
            : "pb-2 hover:text-gray-800 text-gray-500"
        }
      >
        Upload Overview
      </NavLink>
      <NavLink
        to="/uploadComparison"
        className={({ isActive }) =>
          isActive
            ? "pb-2 border-b-2 border-black text-black"
            : "pb-2 hover:text-gray-800 text-gray-500"
        }
      >
        Upload Comparison
      </NavLink>
      <NavLink
        to="/projectProgress"
        className={({ isActive }) =>
          isActive
            ? "pb-2 border-b-2 border-black text-black"
            : "pb-2 hover:text-gray-800 text-gray-500"
        }
      >
        Project Progress
      </NavLink>
    </nav>
  );
}

export default UploadTabs;
