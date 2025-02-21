import Navbar from "../components/NavBar";
import { Link, useParams, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { getProjectHistory } from "../api/api";
import ProjectErrorDialog from "./ProjectErrorDialog";
import BuildingInfoCard from "../components/BuildingInfoCard";
import SystemInfoCard from "../components/SystemInfoCard";
import MaterialInfoCard from "../components/MaterialInfoCard";
import ElementInfoCard from "../components/ElementInfoCard";
import AwardCard from "../components/AwardCard";
function ProjectPage() {
  const location = useLocation();
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [projectHistory, setProjectHistory] = useState([]);
  const { projectName } = useParams();
  console.log("Location state is ", location.state);

  const { projectId } = location.state;
  useEffect(() => {
    const fetchProjectHistory = async () => {
      try {
        const response = await getProjectHistory(projectId);
        console.log("API response data", response.data.history);
        //TODO fix to 2dp
        setProjectHistory(response.data.history);

        setError(null);
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch project history: ", err);
        setError("Failed to fetch project history."); // Set error message
      }
    };
    if (projectId) {
      fetchProjectHistory();
    }
  }, [projectId]);

  if (!projectId) {
    return <p className="text-red-500">No project ID provided.</p>;
  }

  if (loading) {
    return <p>Loading building system information...</p>; // Show loading state
  }

  if (error) {
    return <p className="text-red-500">{error}</p>; // Display error message
  }

  if (!projectHistory) {
    return <p>No project history available.</p>;
  }
  console.log("Project history is: ", projectHistory);
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="overflow-x-auto bg-white rounded-lg p-4 mt-16">
        {/**Check if project name exists */}
        {projectName ? (
          <div>
            <div className="bg-[#A0ABC0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mb-2 sm:max-w-xs">
              <h1 className="text-lg font-semibold tracking-wide">
                {decodeURIComponent(projectName)}
              </h1>
            </div>
            <div className="space-y-2">
              <BuildingInfoCard projectId={projectId} />
              <SystemInfoCard projectId={projectId} />
              <div className="flex flex-row justify-left">
                <div className="w-1/3">
                  {" "}
                  {/* Adjust width as needed */}
                  <AwardCard projectId={projectId} />
                </div>
                <div>
                  <table className="w-full text-left border-collapse border border-gray-300">
                    <thead>
                      <tr>
                        <th className="border border-gray-300 p-2 font-bold">
                          USER
                        </th>
                        <th className="border border-gray-300 p-2 font-bold">
                          COMMENTS
                        </th>
                        <th className="border border-gray-300 p-2 font-bold">
                          TIME
                        </th>
                        <th className="border border-gray-300 p-2 font-bold">
                          UPDATE TYPE
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {projectHistory.map((item, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="border border-gray-300 px-4 py-2">
                            {item.uploaded_by}
                          </td>
                          <td className="border border-gray-300 px-4 py-2">
                            {item.comments}
                          </td>
                          <td className="border border-gray-300 px-4 py-2">
                            {item.date_uploaded}
                          </td>
                          <td className="border border-gray-300 px-4 py-2">
                            {item.update_type}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <ProjectErrorDialog />
        )}
      </div>
    </div>
  );
}

export default ProjectPage;
