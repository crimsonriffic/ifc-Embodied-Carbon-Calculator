import { useState } from "react";
import { uploadIfc } from "../api/api.jsx";
function IfcDialog({ onClose, projectId }) {
  const [inputComment, setInputComment] = useState("");
  const [updateType, setUpdateType] = useState("Master File");
  const [selectedFile, setSelectedFile] = useState("null");
  const [uploadError, setUploadError] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpdateTypeChange = (e) => {
    setUpdateType(e.target.value);
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
      onClose();
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

        {/*Upload form */}
        <div className="w-full max-w-xs">
          <form onSubmit={handleUpload} className="space-y-4">
            <input
              type="file"
              onChange={handleFileChange}
              className="w-full mb-4 p-2 border border-gray-300 rounded-lg"
              required
            />
            {/*Input update type */}
            <div className="mb-4">
              <label
                htmlFor="updateType"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Update Type
              </label>
              <select
                id="updateType"
                value={updateType}
                onChange={handleUpdateTypeChange}
                className="w-full p-2 border border-gray-300 rounded-lg"
              >
                <option value="Master File">Master File</option>
                <option value="Linked File">Linked File</option>
              </select>
            </div>
            {/*Input comment */}
            <div className="mb-4">
              <label
                htmlFor="comments"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
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
