import { useState } from "react";
import { uploadIfc } from "../api/api.jsx";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import { ArrowRightIcon, XMarkIcon } from "@heroicons/react/24/solid";
function IfcDialog({ onClose, projectName, projectId, uploadNumber }) {
  const [status, setStatus] = useState("Conceptual Design");

  const [inputComment, setInputComment] = useState("");
  const [selectedFile, setSelectedFile] = useState("null");
  const [uploadError, setUploadError] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [loading, setLoading] = useState(false); // Loading state

  const { username } = useUser();

  const navigate = useNavigate();
  console.log(
    "Project name and project id from ifc dialog is",
    projectName,
    projectId
  );
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };
  const handleUpdateStatus = (e) => {
    setStatus(e.target.value);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    console.log("Uploading for project ID:", projectId);
    console.log("Project id type ", typeof projectId);
    if (!selectedFile) {
      alert("Please select a file to upload!");
      return;
    }
    setLoading(true);
    try {
      // const userId = username;
      const response = await uploadIfc(
        projectId,
        selectedFile,
        username,
        inputComment,
        status
      );
      setUploadError(null);
      setShowSuccess(true);
      // Navigate after 1 seconds
      setTimeout(() => {
        onClose();
        navigate(`/loading/${encodeURIComponent(projectName)}`, {
          state: { projectId },
        });
      }, 2000);
    } catch (err) {
      setUploadError(
        err.response?.data?.detail || "An error occurred during upload."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-white p-4 rounded shadow-lg  w-[600px]  max-w-full">
        <div className="flex flex-row justify-between">
          <h2 className="text-xl font-semibold mb-4">
            New Upload: Upload {uploadNumber}
          </h2>
          <button onClick={onClose}>
            <XMarkIcon
              className="rounded-full w-5 h-5 text-gray-500 border-2 border-gray-500 font-bold"
              stroke="currentColor"
              strokeWidth={2}
            />
          </button>
        </div>

        {showSuccess && (
          <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg">
            Upload successful!
          </div>
        )}
        {uploadError && (
          <div className="mb-4 text-red-600 font-semibold">{uploadError}</div>
        )}
        {/*Upload form */}
        <div className="w-full ">
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="mb-4">
              {/*Input Status type */}
              <label htmlFor="status" className="block text-gray-700 mb-1">
                Status
              </label>
              <select
                id="status"
                value={status}
                onChange={handleUpdateStatus}
                className="p-2 border w-80 border-gray-200 shadow-md"
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
            <div className="mb-4">
              <label htmlFor="status" className="block text-gray-700 mb-1">
                Upload IFC
              </label>
              <input
                type="file"
                onChange={handleFileChange}
                className="w-80 p-2 border border-gray-300 rounded-lg"
                required
              />
            </div>

            {/*Input comment */}
            <div className="mb-4">
              <label htmlFor="status" className="block text-gray-700 mb-1">
                Comments
              </label>
              <input
                type="text"
                id="inputComment"
                value={inputComment}
                onChange={(e) => setInputComment(e.target.value)}
                placeholder="Edited roof..."
                className="w-80 p-2 border border-gray-300 rounded-lg resize-none"
                required
              />
              <p className="px-1 text-gray-500 text-sm mb-16">
                Comments will be used to help identify the uploads
              </p>
            </div>
            <div className="flex justify-end space-x-2">
              <button
                className={`px-4 py-2 rounded ${
                  loading
                    ? "bg-gray-400 cursor-not-allowed text-black"
                    : "bg-[#5B9130] text-white "
                } `}
                disabled={loading}
              >
                {loading ? (
                  "Uploading..."
                ) : (
                  <span className="flex items-center space-x-1">
                    <ArrowRightIcon className="w-6 h-6 text-white mr-2" />
                    Confirm New Upload{" "}
                  </span>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default IfcDialog;
