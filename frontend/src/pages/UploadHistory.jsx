import Navbar from "../components/NavBar";
import Stepper from "../components/Stepper";
import HistoryTable from "../components/HistoryTable";
import IfcDialog from "./IfcDialog";
import { getProjectHistory, uploadIfc } from "../api/api";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

function UploadHistory() {
  const [status, setStatus] = useState("Conceptual Design");
  const [selectedFile, setSelectedFile] = useState(null);
  const [inputComment, setInputComment] = useState("");
  const [projectHistory, setProjectHistory] = useState([]);
  const [versionNumber, setVersionNumber] = useState("");
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");
  const [showSuccess, setShowSuccess] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { projectId } = location.state;
  const { projectName } = useParams();

  const handleUpdateStatus = (e) => {
    setStatus(e.target.value);
  };
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
  };

  const handleProceed = (projectId, projectName) => {
    console.log("HandleProceed called");
    navigate(`/materialInfo/${encodeURIComponent(projectName)}`, {
      state: { projectId },
    });
  };

  const handleUpload = async (e) => {
    setIsDialogOpen(true);
  };
  /* Initial API calls to fetch project history and breakdown data */
  useEffect(() => {
    const fetchData = async () => {
      try {
        const historyResponse = await getProjectHistory(projectId);

        // Get the latest version from history
        const latestVersion = historyResponse.data.history[0]?.version || "";

        setProjectHistory(historyResponse.data.history);
        console.log("Project History set as: ", historyResponse.data.history);

        if (!versionNumber && latestVersion) {
          setVersionNumber(latestVersion);
        }

        setError(null);
        setLoading(false);
      } catch (err) {
        console.error("Failed to data: ", err);
        setError("Failed to fetch history data."); // Set error message
      }
    };
    if (projectId) {
      fetchData();
    }
  }, [projectId]);
  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Upload Information</h1>
      </div>
      <div className="mt-6">
        <Stepper currentStep={2} />
      </div>
      <div className="bg-[#A9C0A0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mt-4 mb-6 sm:max-w-md">
        <h1 className="text-2xl font-semibold tracking-wide">
          {decodeURIComponent(projectName)}
        </h1>
      </div>
      <div className="flex flex-col">
        <button
          className="px-2 py-2 mt-6 bg-[#5B9130] text-white rounded"
          onClick={() => {
            handleUpload(projectId, projectName);
          }}
        >
          +New Upload
        </button>
        {/*Conditional Rendering for IfcDialog*/}
        {isDialogOpen && (
          <IfcDialog
            onClose={handleCloseDialog}
            projectName={projectName}
            projectId={projectId}
          />
        )}
        <div className="flex flex-1 flex-col">
          <h1 className="text-2xl font-semibold tracking-wide mb-2">
            Active Uploads
          </h1>
          <HistoryTable projectHistory={projectHistory} />
        </div>
      </div>
    </div>
  );
}

export default UploadHistory;
