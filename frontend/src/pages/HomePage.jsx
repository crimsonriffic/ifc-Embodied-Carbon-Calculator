import { getProjectsByUsername } from "../api/api.jsx";
import Navbar from "../components/NavBar";
import IfcDialog from "./IfcDialog";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext.jsx";
import { ArrowUpTrayIcon, ArrowRightIcon } from "@heroicons/react/24/solid";

function HomePage() {
  const [projects, setProjects] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [error, setError] = useState(null); // State to store any errors
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [selectedProjectName, setSelectedProjectName] = useState(null);

  const { username } = useUser();
  const navigate = useNavigate();
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-GB"); // 'en-GB' ensures DD/MM/YYYY format
  };

  const handleUploadClick = (projectId, projectName) => {
    setSelectedProjectId(projectId);
    setSelectedProjectName(projectName);
    setIsDialogOpen(true);
  };
  const handleCloseDialog = () => {
    setIsDialogOpen(false);
  };
  const handleCreateButton = () => {
    navigate("/createProject");
  };

  const handleGoToProject = (projectId, projectName) => {
    console.log("HandleGoToProject called");
    navigate(`/project/${encodeURIComponent(projectName)}`, {
      state: { projectId },
    });
  };
  // Re-fetch files whenever the dialog is closed
  useEffect(() => {
    const fetchProjects = async () => {
      if (!isDialogOpen) {
        try {
          const response = await getProjectsByUsername(username);
          console.log("Response data is ", response.data);
          setProjects(response.data);
          setError(null);
        } catch (err) {
          setError(err.response?.data?.detail || "Failed to fetch projects");
          console.error("Failed to fetch projects: ", err);
        }
      }
    };
    fetchProjects();
  }, [isDialogOpen]);

  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-10 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Welcome to IFC Carbon Calculator</h1>
        <p className="mt-2 text-lg">
          Collaborate with stakeholders to analyze the embodied carbon of your
          projects.
        </p>
        <button
          className="mt-4 bg-white text-[#5B9130] font-semibold py-2 px-4 rounded-lg shadow hover:bg-gray-200"
          onClick={handleCreateButton}
        >
          Create a Project
        </button>
      </div>
      {projects.length === 0 ? (
        <p className="text-gray-500">
          No Active projects available for this user, try{" "}
          <strong>user123</strong>
        </p>
      ) : (
        /** Active projects table  */
        <div className="overflow-x-auto bg-white shadow-md rounded-lg p-4 w-full mt-10">
          <h1 className="text-2xl font-bold mb-4">Active Projects</h1>
          <table className="table-auto w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-200">
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Project Name
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Client Name
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Latest Update
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Upload IFC file
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Go To Project
                </th>
              </tr>
            </thead>
            <tbody>
              {projects
                .slice() // Create a copy to avoid mutating the original array
                .sort(
                  (a, b) =>
                    new Date(b.last_edited_date) - new Date(a.last_edited_date)
                ) // Sort by latest date
                .map((project, index) => (
                  <tr key={index} className="hover:bg-gray-100">
                    <td className="border border-gray-300 px-4 py-2">
                      {project.project_name}
                    </td>
                    <td className="border border-gray-300 px-4 py-2">
                      {project.client_name}
                    </td>
                    <td className="border border-gray-300 px-4 py-2">
                      {formatDate(project.last_edited_date)},{" "}
                      {project.last_edited_user}
                    </td>
                    <td className="border border-gray-300 px-4 py-2 text-center">
                      <button
                        className="text-gray-600 hover:text-blue-500"
                        onClick={() =>
                          handleUploadClick(project._id, project.project_name)
                        }
                      >
                        <ArrowUpTrayIcon className="w-6 h-6 text-gray-500" />
                      </button>
                    </td>
                    <td className="border border-gray-300 px-4 py-2 text-center">
                      <button
                        onClick={() =>
                          handleGoToProject(project._id, project.project_name)
                        }
                        className="text-gray-600 hover:text-blue-500"
                      >
                        <ArrowRightIcon className="w-6 h-6 text-gray-500" />
                      </button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>

          {/*Conditional Rendering for IfcDialog*/}
          {isDialogOpen && (
            <IfcDialog
              onClose={handleCloseDialog}
              projectName={selectedProjectName}
              projectId={selectedProjectId}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default HomePage;
