import Navbar from "../components/NavBar";
import Stepper from "../components/Stepper";
import HistoryTable from "../components/HistoryTable";
import { getProjectHistory, uploadIfc } from "../api/api";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

function EditPage1() {
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

  const handleProceed = (projectId, projectName) => {
    console.log("HandleProceed called");
    navigate(`/materialInfo/${encodeURIComponent(projectName)}`, {
      state: { projectId },
    });
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    console.log("Uploading for project ID:", projectId);
    console.log("Project id type ", typeof projectId);
    if (!selectedFile) {
      alert("Please select a file to upload!");
      return;
    }
    try {
      const userId = "user123";
      const response = await uploadIfc(
        projectId,
        selectedFile,
        userId,
        inputComment,
        status
      );
      setSuccessMessage(response.message);
      setUploadError(null);
      setShowSuccess(true);
    } catch (err) {
      setUploadError(
        err.response?.data?.detail || "An error occurred during upload."
      );
    }
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
      <div className="flex flex-row gap-x-32">
        {/**Left section */}
        <div className="flex flex-col max-w-md">
          {/** New Upload section*/}
          <h1 className="text-2xl font-semibold tracking-wide mb-2">
            New Upload
          </h1>
          <p className="block text-gray-700 mb-4">Upload Number: </p>

          {/*Upload form */}
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="max-w-md">
              {/*Input Status type */}
              <label htmlFor="status" className="block text-gray-700 mb-1">
                Status
              </label>
              <select
                id="status"
                value={status}
                onChange={handleUpdateStatus}
                className="p-2 border w-80 border-gray-200 shadow-md mb-4"
              >
                <option value="Conceptual Design">Conceptual Design</option>
                <option value="Schematic Design">Schematic Design</option>
                <option value="Detailed Design">Detailed Design</option>
                <option value="Construction Evaluation">
                  Construction Evaluaton
                </option>
                <option value="Final Assessment">Final Assessment</option>
                <option value="Verification">Verification</option>
              </select>
            </div>

            {/** Upload IFC Section */}
            <div className="mb-4">
              <label htmlFor="client" className="block text-gray-700 mb-1">
                Upload IFC
              </label>
              <input
                type="file"
                onChange={handleFileChange}
                className="p-2 w-80 border border-gray-200 shadow-md focus:outline-none resize-none mb-4"
                required
              />
            </div>

            {/** Comments Section */}
            <div className="mb-4">
              <label htmlFor="client" className="block text-gray-700 mb-1">
                Comments
              </label>
              <input
                type="text"
                id="inputComment"
                value={inputComment}
                onChange={(e) => setInputComment(e.target.value)}
                className="p-2 w-80 border border-gray-200 shadow-md focus:outline-none resize-none"
                placeholder="Add comments"
                required
              />
            </div>

            {/**Upload Button */}
            <div className="flex flex-row">
              <button className="px-4 py-2 bg-[#E3EBE0] text-black rounded">
                Upload now
              </button>
              {showSuccess && (
                <div className=" p-2 text-green-700 rounded-lg">
                  Upload successful!
                </div>
              )}
              {uploadError && (
                <div className=" text-red-600 font-semibold">{uploadError}</div>
              )}
            </div>
          </form>

          <button
            className="px-4 py-2 mt-6 w-28 bg-[#9FD788] text-black rounded"
            onClick={() => {
              handleProceed(projectId, projectName);
            }}
          >
            Proceed
          </button>
        </div>

        {/**Right section */}
        <div className="flex flex-1 flex-col">
          <h1 className="text-2xl font-semibold tracking-wide mb-2">
            Upload History
          </h1>
          <HistoryTable projectHistory={projectHistory} />
        </div>
      </div>
    </div>
  );
}

export default EditPage1;
