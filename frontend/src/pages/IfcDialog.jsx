import { useState } from "react";
import { uploadIfc } from "../api/api.jsx";
import { useNavigate } from "react-router-dom";
function IfcDialog({ onClose, projectName, projectId }) {
  const [status, setStatus] = useState("Conceptual Design");

  const [inputComment, setInputComment] = useState("");
  const [updateType, setUpdateType] = useState("Nil");
  const [selectedFile, setSelectedFile] = useState("null");
  const [uploadError, setUploadError] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");
  const [showSuccess, setShowSuccess] = useState(false);

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
    try {
      const userId = "user123";
      const response = await uploadIfc(
        projectId,
        selectedFile,
        userId,
        inputComment,
        updateType
      );
      setSuccessMessage(response.message);
      setUploadError(null);
      setShowSuccess(true);
      // Navigate after 1 seconds
      setTimeout(() => {
        onClose();
        navigate(`/project/${encodeURIComponent(projectName)}`, {
          state: { projectId },
        });
      }, 1000);
    } catch (err) {
      setUploadError(
        err.response?.data?.detail || "An error occurred during upload."
      );
    }
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white p-6 rounded shadow-lg">
        <h2 className="text-xl font-semibold mb-4">Upload IFC file</h2>

        {showSuccess && (
          <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg">
            Upload successful! Directing to project page
          </div>
        )}
        {uploadError && (
          <div className="mb-4 text-red-600 font-semibold">{uploadError}</div>
        )}
        {/*Upload form */}
        <div className="w-full max-w-xs">
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
                className="w-full p-2 border border-gray-300 rounded-lg"
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
                placeholder="Input Comments"
                className="w-full p-2 border border-gray-300 rounded-lg resize-none"
                required
              />
            </div>

            <div className="flex justify-end space-x-2">
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-300 rounded"
              >
                Cancel
              </button>
              <button className="px-4 py-2 bg-blue-500 text-white rounded">
                Upload
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default IfcDialog;
