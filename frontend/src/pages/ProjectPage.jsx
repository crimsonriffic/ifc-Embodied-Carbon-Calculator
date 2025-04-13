import Navbar from "../components/NavBar";
import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, version } from "react";
import { getProjectHistory, getProjectBreakdown } from "../api/api";
import BarChart from "../components/BarChart";
import HistoryTable from "../components/HistoryTable";
import UploadInfoCard from "../components/UploadInfoCard";
import SankeyChart from "../components/SankeyChart";
import Stepper from "../components/Stepper";
import UploadOverview from "./UploadOverview";
import UploadComparison from "./UploadComparison";
import ProjectProgress from "./ProjectProgress";
import ExportResults from "./ExportResults";
function ProjectPage() {
  const location = useLocation();

  const [activeTab, setActiveTab] = useState("Upload Overview");
  const { projectName } = useParams();
  const { projectId } = location.state;
  const fromHomePage = location.state?.fromHomePage === true;
  const [projectHistory, setProjectHistory] = useState([]);
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  console.log("Project Name and project Id is ", projectName, projectId);
  useEffect(() => {
    const fetchData = async () => {
      try {
        const historyResponse = await getProjectHistory(projectId);
        console.log(
          "PROJECTPAGE: History response data: ",
          historyResponse.data.history
        );

        setProjectHistory(historyResponse.data.history);

        setError(null);
        setLoading(false);
      } catch (err) {
        console.error("Failed to data: ", err);
        setError("Failed to fetch data."); // Set error message
      }
    };
    if (projectId) {
      fetchData();
    }
  }, [projectId]);
  if (!projectId) {
    return <p className="text-red-500 mt-16">No project ID provided.</p>;
  }

  if (loading) {
    return <p className="mt-16">Loading project data...</p>; // Show loading state
  }

  if (error) {
    return <p className="text-red-500 mt-16">{error}</p>; // Display error message
  }

  if (!projectHistory) {
    return <p className="mt-16">No project history available.</p>;
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">View Results</h1>
        <p>Your embodied carbon calculations are ready for viewing</p>
      </div>
      <div className="mt-6">{!fromHomePage && <Stepper currentStep={5} />}</div>
      {/**Check if project name exists */}

      <div className="bg-[#A9C0A0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mt-4 mb-6 sm:max-w-md">
        <h1 className="text-2xl font-semibold tracking-wide">
          {decodeURIComponent(projectName)}
        </h1>
      </div>
      {/**TODO: Insert tabs here */}
      <div className="flex flex-row space-x-4 mb-4">
        <button
          onClick={() => setActiveTab("Upload Overview")}
          className={` py-2 font-bold ${
            activeTab === "Upload Overview"
              ? "border-b-2 border-gray-600 text-gray-600"
              : "text-gray-500"
          }`}
        >
          Upload Overview
        </button>
        <button
          onClick={() => setActiveTab("Upload Comparison")}
          className={`py-2 font-bold ${
            activeTab === "Upload Comparison"
              ? "border-b-2 border-gray-600 text-gray-600"
              : "text-gray-500"
          }`}
        >
          Upload Comparison
        </button>
        <button
          onClick={() => setActiveTab("Project Progress")}
          className={`py-2 font-bold ${
            activeTab === "Project Progress"
              ? "border-b-2 border-gray-600 text-gray-600"
              : "text-gray-500"
          }`}
        >
          Project Progress
        </button>
        <button
          onClick={() => setActiveTab("Export Results")}
          className={`py-2 font-bold ${
            activeTab === "Project Progress"
              ? "border-b-2 border-gray-600 text-gray-600"
              : "text-gray-500"
          }`}
        >
          Export Results
        </button>
      </div>
      {activeTab === "Upload Overview" && (
        <UploadOverview
          projectId={projectId}
          projectName={projectName}
          projectHistory={projectHistory}
        />
      )}
      {activeTab === "Upload Comparison" && (
        <UploadComparison projectId={projectId} projectName={projectName} />
      )}
      {activeTab === "Project Progress" && (
        <ProjectProgress
          projectId={projectId}
          projectName={projectName}
          projectHistory={projectHistory}
        />
      )}
      {activeTab === "Export Results" && (
        <ExportResults
          projectId={projectId}
          projectName={projectName}
          projectHistory={projectHistory}
        />
      )}
    </div>
  );
}

export default ProjectPage;
