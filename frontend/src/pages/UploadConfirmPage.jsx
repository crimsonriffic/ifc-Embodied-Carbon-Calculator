import Navbar from "../components/NavBar";
import Stepper from "../components/Stepper";
import MaterialTable from "../components/MaterialTable";
import HistoryTable from "../components/HistoryTable";
import UploadInfoCard from "../components/UploadInfoCard";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { getProjectHistory } from "../api/api";
function UploadConfirmPage() {
  const [versionNumber, setVersionNumber] = useState("");
  const [projectHistory, setProjectHistory] = useState([]);
  const location = useLocation();
  const navigate = useNavigate();
  const { projectId } = location.state;

  const { projectName } = useParams();

  const handleProceed = (projectId, projectName) => {
    console.log("HandleProceed called");
    navigate(`/project/${encodeURIComponent(projectName)}`, {
      state: { projectId },
    });
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const historyResponse = await getProjectHistory(projectId);
        setProjectHistory(historyResponse.data.history);
        console.log("History response data: ", historyResponse.data.history);
        // Get the latest version from history
        const latestVersion = historyResponse.data.history[0]?.version || "";
        setVersionNumber(latestVersion);
      } catch (err) {
        console.error("Failed to data: ", err);
      }
    };
    if (projectId) {
      fetchData();
    }
  }, []);
  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Upload Information</h1>
      </div>
      <div className="mt-6">
        <Stepper currentStep={4} />
      </div>
      <div className="bg-[#A9C0A0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mt-4 mb-6 sm:max-w-md">
        <h1 className="text-2xl font-semibold tracking-wide">
          {decodeURIComponent(projectName)}
        </h1>
      </div>

      {/**Left section */}
      <div className="flex flex-col">
        {/** New Upload section*/}
        <h1 className="text-2xl font-semibold tracking-wide mb-2">
          Upload {versionNumber}
        </h1>
        <div className="flex-1 flex-col sm:max-w-md ">
          <UploadInfoCard
            uploadInfoData={projectHistory.find(
              (item) => item.version === versionNumber
            )}
          />
          <h1 className="text-2xl font-semibold tracking-wide mt-6 mb-2">
            Upload Confirmation
          </h1>
          <p className="text-semibold text-[#5B9130]">
            {" "}
            Your uploaded model is ready for embodied carbon calculation{" "}
          </p>
        </div>

        <button
          className="px-4 py-2 mt-6 w-28 bg-[#5B9130] text-black rounded"
          onClick={() => {
            handleProceed(projectId, projectName);
          }}
        >
          Proceed
        </button>
      </div>
    </div>
  );
}

export default UploadConfirmPage;
