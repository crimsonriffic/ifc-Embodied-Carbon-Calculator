import Navbar from "../components/NavBar";
import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, version } from "react";
import { getProjectHistory, getProjectBreakdown } from "../api/api";
import BuildingInfoCard from "../components/BuildingInfoCard";
import BarChart from "../components/BarChart";
import HistoryTable from "../components/HistoryTable";
import UploadInfoCard from "../components/UploadInfoCard";
import SankeyChart from "../components/SankeyChart";
import Stepper from "../components/Stepper";
import UploadOverview from "./UploadOverview";
import UploadComparison from "./UploadComparison";
import ProjectProgress from "./ProjectProgress";
function ProjectPage() {
  const location = useLocation();

  const [activeTab, setActiveTab] = useState("Upload Overview");
  const { projectName } = useParams();
  const { projectId } = location.state;
  const fromHomePage = location.state?.fromHomePage === true;

  console.log("Project Name and project Id is ", projectName, projectId);

  if (!projectId) {
    return <p className="text-red-500 mt-16">No project ID provided.</p>;
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
      </div>
      {activeTab === "Upload Overview" && (
        <UploadOverview projectId={projectId} projectName={projectName} />
      )}
      {activeTab === "Upload Comparison" && <UploadComparison />}
      {activeTab === "Project Progress" && <ProjectProgress />}
    </div>
  );
}

export default ProjectPage;
