import { useEffect, useState } from "react";
export default function UploadInfoCard({ uploadInfoData }) {
  const [uploadInfo, setUploadInfo] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true); // Loading state
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-GB"); // 'en-GB' ensures DD/MM/YYYY format
  };
  useEffect(() => {
    setUploadInfo(uploadInfoData);
    console.log("Upload Info data is", uploadInfoData);
    setLoading(false);
  }, [uploadInfoData]);

  if (loading) {
    return <p>Loading upload information...</p>; // Show loading state
  }

  if (error) {
    return <p className="text-red-500">{error}</p>; // Display error message
  }

  if (!uploadInfo) {
    return <p>No upload information available.</p>;
  }
  return (
    <div className="bg-white rounded-lg sm:max-w-md ">
      <div className="space-y-2 ">
        <div className="flex justify-between border-b py-2">
          <span className="text-sm font-medium text-gray-600">User:</span>
          <span className="text-sm  text-gray-800">
            {uploadInfo.uploaded_by || "N/A"}
          </span>
        </div>
        <div className="flex justify-between border-b py-2">
          <span className="text-sm font-medium text-gray-600">Comments:</span>
          <span className="text-sm  text-gray-800">
            {uploadInfo.comments || "N/A"}
          </span>
        </div>
        <div className="flex justify-between border-b py-2">
          <span className="text-sm font-medium text-gray-600">
            Upload Time:
          </span>
          <span className="text-sm  text-gray-800">
            {formatDate(uploadInfo.date_uploaded) || "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
}
