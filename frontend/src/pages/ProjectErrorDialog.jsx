import { useState } from "react";
import { Link } from "react-router-dom";
function ProjectErrorDialog() {
  return (
    <div className="bg-white shadow-lg rounded-lg p-8 text-center max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-red-600 mt-4 mb-4">
        No project selected
      </h1>
      <p className="text-gray-700 mb-6">
        Please choose a project from the home page.
      </p>
      <Link
        to="/home"
        className="inline-block bg-blue-500 text-white text-sm font-medium px-6 py-3 rounded-lg shadow-md hover:bg-blue-600 transition"
      >
        Go to Home Page
      </Link>
    </div>
  );
}

export default ProjectErrorDialog;
