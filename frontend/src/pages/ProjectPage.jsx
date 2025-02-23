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
import BarChart from "../components/BarChart";
function ProjectPage() {
  const location = useLocation();
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [projectHistory, setProjectHistory] = useState([]);
  const [barData, setBarData] = useState({
    labels: [],
    datasets: [],
  });
  const { projectName } = useParams();
  console.log("Location state is ", location.state);

  const { projectId } = location.state;
  useEffect(() => {
    const fetchProjectHistory = async () => {
      try {
        const response = await getProjectHistory(projectId);
        console.log("API response data", response.data);

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

  useEffect(() => {
    if (!projectHistory) {
      console.log("Project history is empty");
      return;
    }

    console.log("Project history is: ", projectHistory);
    const sortedHistory = projectHistory
      ? [...projectHistory].sort((a, b) => a.version - b.version)
      : [];

    const versionLabels = sortedHistory
      ? sortedHistory.map((item) => item.version)
      : [];
    const versionValues = projectHistory
      ? sortedHistory.map((item) => item.total_ec)
      : [];
    console.log("Project history labels is: ", versionLabels);
    console.log("Project history values is: ", versionValues);
    const data = {
      labels: versionLabels,
      datasets: [
        {
          label: "A1-A3 carbon Comparison",
          data: versionValues,
          backgroundColor: ["#E4937B", "#CAA05C", "#E2D35E", "#E5E548"],
          borderColor: "#000000",
          borderWidth: 0,
        },
      ],
    };
    setBarData(data);
  }, [projectHistory]);

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
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="overflow-x-auto bg-white rounded-lg p-4 mt-16">
        {/**Check if project name exists */}
        {projectName ? (
          <div>
            <div className="bg-[#A9C0A0]  text-white rounded-lg px-4 py-2 flex items-center shadow-md mb-2 sm:max-w-md">
              <h1 className="text-lg font-semibold tracking-wide">
                {decodeURIComponent(projectName)}
              </h1>
            </div>
            <div className="flex flex-col">
              <div className="flex flex-row">
                <div className="flex flex-1 flex-col">
                  <h1 className="font-bold w-full md:w-1/2">
                    Project Upload History
                  </h1>
                  <table className="w-full md:w-1/2 text-left border-separate border-spacing-0 border border-gray-800 rounded-lg overflow-hidden">
                    <thead>
                      <tr>
                        <th className="border-b border-r border-gray-800 px-6 py-4 font-bold first:rounded-tl-lg ">
                          User
                        </th>
                        <th className="border-b border-r w-96 border-gray-800 px-6 py-4 font-bold">
                          Comments
                        </th>
                        <th className="border-b border-r border-gray-800 px-6 py-4 font-bold">
                          Upload Time
                        </th>
                        <th className="border-b border-gray-800 px-6 py-4 font-bold">
                          Comparison
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {projectHistory.map((item, index) => (
                        <tr key={index} className="hover:bg-gray-50 px-6 py-4">
                          <td
                            className={`px-6 py-2 ${
                              index === projectHistory.length - 1
                                ? "first:rounded-bl-lg border-r border-gray-800"
                                : "border-b border-r border-gray-800"
                            }`}
                          >
                            {item.uploaded_by}
                          </td>
                          <td
                            className={` px-6 py-4 ${
                              index === projectHistory.length - 1
                                ? "border-r border-gray-800"
                                : "border-b border-r border-gray-800"
                            }`}
                          >
                            {item.comments}
                          </td>
                          <td
                            className={` px-6 py-4 ${
                              index === projectHistory.length - 1
                                ? "border-r border-gray-800"
                                : "border-b border-r border-gray-800"
                            }`}
                          >
                            {item.date_uploaded}
                          </td>
                          <td
                            className={` px-6 py-4 ${
                              index === projectHistory.length - 1
                                ? ""
                                : "border-b border-gray-800"
                            }`}
                          >
                            TODO
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex flex-1 flex-col">
                  <h1 className="font-bold">
                    A1-A3 Embodied Carbon Comparison
                  </h1>
                  <div className="h-[400px]">
                    <BarChart data={barData} />
                  </div>
                </div>
              </div>
              <div className="flex flex-col mt-6">
                <h1 className="font-bold">Project Information</h1>
                <BuildingInfoCard projectId={projectId} />
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
