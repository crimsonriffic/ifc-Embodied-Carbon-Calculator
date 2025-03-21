import Navbar from "../components/NavBar";
import Stepper from "../components/Stepper";

import { getBuildingInfo } from "../api/api";

import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

function ProjectInfoPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [buildingInfo, setBuildingInfo] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true); // Loading state

  const { projectId } = location.state;
  const { projectName } = useParams();

  const handleProceed = (projectId, projectName) => {
    console.log("HandleProceed called");
    navigate(`/uploadHistory/${encodeURIComponent(projectName)}`, {
      state: { projectId },
    });
  };

  useEffect(() => {
    const fetchBuildingInfo = async () => {
      try {
        const response = await getBuildingInfo(projectId);
        console.log("Building Info (EC breakdown)", response.data);
        setBuildingInfo(response.data);
        setError(null);
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch building info: ", err);
        setError("Failed to fetch building information."); // Set error message
      }
    };
    if (projectId) {
      fetchBuildingInfo();
    }
  }, [projectId]);
  if (!projectId) {
    return <p className="text-red-500">No project ID provided.</p>;
  }

  if (loading) {
    return <p>Loading building information...</p>; // Show loading state
  }

  if (error) {
    return <p className="text-red-500">{error}</p>; // Display error message
  }

  if (!buildingInfo) {
    return <p>No building information available.</p>;
  }
  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Upload Information</h1>
      </div>
      <div className="mt-6">
        <Stepper currentStep={1} />
      </div>
      <div className="bg-[#A9C0A0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mt-4 mb-6 sm:max-w-md">
        <h1 className="text-2xl font-semibold tracking-wide">
          {decodeURIComponent(projectName)}
        </h1>
      </div>
      <div className="flex flex-row gap-x-32">
        {/**Left section */}
        <div className="flex flex-col max-w-md">
          {/** New Upload section*/}
          <h1 className="text-2xl font-semibold tracking-wide mb-2">
            View Project Information
          </h1>

          <div className="max-w-md">
            <label htmlFor="projectName" className="block text-gray-700 mb-1">
              Project Name
            </label>
            <p className="p-2 border w-80 border-gray-200 shadow-md mb-4">
              {buildingInfo.project_name}
            </p>
          </div>

          <div className="max-w-md">
            <label htmlFor="clientName" className="block text-gray-700 mb-1">
              Client Name
            </label>
            <p className="p-2 border w-80 border-gray-200 shadow-md mb-4">
              {buildingInfo.client_name}
            </p>
          </div>

          <div className="max-w-md">
            <label htmlFor="typology" className="block text-gray-700 mb-1">
              Typology
            </label>
            <p className="p-2 border w-80 border-gray-200 shadow-md mb-4">
              {buildingInfo.typology}
            </p>
          </div>

          <button
            className="px-4 py-2 mt-6 w-28 bg-[#5B9130] text-white rounded"
            onClick={() => {
              handleProceed(projectId, projectName);
            }}
          >
            Proceed
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProjectInfoPage;
