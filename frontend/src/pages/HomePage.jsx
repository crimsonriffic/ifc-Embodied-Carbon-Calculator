import { getProjectsByUsername } from "../api/api";
import Navbar from "../components/NavBar";
import IfcDialog from "./IfcDialog";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import {
  ArrowUpTrayIcon,
  DocumentIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/solid";

function HomePage() {
  const [projects, setProjects] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const navigate = useNavigate();
  const handleUploadClick = () => {
    setIsDialogOpen(true);
  };
  const handleCloseDialog = () => {
    setIsDialogOpen(false);
  };

  const handleGoToProject = (projectName) => {
    console.log("HandleGoToProject called");
    navigate(`/project/${encodeURIComponent(projectName)}`);
  };
  // Re-fetch files whenever the dialog is closed
  useEffect(() => {
    const fetchProjects = async () => {
      if (!isDialogOpen) {
        try {
          const data = await getProjectsByUsername();
          setProjects(data);
        } catch (error) {
          console.error("Failed to fetch projects: ", error);
        }
      }
    };
    fetchProjects();
  }, [isDialogOpen]);

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="overflow-x-auto bg-white shadow-md rounded-lg p-4 mt-16">
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
                IFC file
              </th>
              <th className="border border-gray-300 px-4 py-2 text-left">
                Go To Project
              </th>
            </tr>
          </thead>
          <tbody>
            {projects.map((project, index) => (
              <tr key={index} className="hover:bg-gray-100">
                <td className="border border-gray-300 px-4 py-2">
                  {project.projectName}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  {project.clientName}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  {project.latestUpdate}
                </td>
                <td className="border border-gray-300 px-4 py-2 text-center">
                  {/*Conditional upload icon rendering */}
                  <button
                    className="text-gray-600 hover:text-blue-500"
                    onClick={handleUploadClick}
                  >
                    {project.filepath === "" ? (
                      <ArrowUpTrayIcon className="w-6 h-6 text-gray-500" />
                    ) : (
                      <DocumentIcon className="w-6 h-6 text-blue-500" />
                    )}
                  </button>
                </td>
                <td className="border border-gray-300 px-4 py-2 text-center">
                  <button
                    onClick={() => handleGoToProject(project.projectName)}
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
        {isDialogOpen && <IfcDialog onClose={handleCloseDialog} />}
      </div>
    </div>
  );
}

export default HomePage;
