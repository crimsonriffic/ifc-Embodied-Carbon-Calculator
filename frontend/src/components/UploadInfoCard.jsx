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
    <div className="bg-white rounded-lg  ">
      <div className="space-y-2 ">
        <div className="flex justify-between  py-2">
          <span>User:</span>
          <span>{uploadInfo.uploaded_by || "N/A"}</span>
        </div>
        <div className="flex justify-between py-2">
          <span>Comments:</span>
          <span>{uploadInfo.comments || "Create project"}</span>
        </div>
        <div className="flex justify-between py-2">
          <span>Upload Time:</span>
          <span>{formatDate(uploadInfo.date_uploaded) || "N/A"}</span>
        </div>
      </div>
    </div>
  );
}
