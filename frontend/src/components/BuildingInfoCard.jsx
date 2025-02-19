import { getBuildingInfo } from "../api/api.jsx";
import { useEffect, useState } from "react";
export default function BuildingInfoCard({ projectId }) {
  const [buildingInfo, setBuildingInfo] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true); // Loading state

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
    <div className="bg-white shadow-lg rounded-lg p-6 border border-gray-300  sm:max-w-xs">
      <h2 className="text-lg font-bold mb-4 text-gray-800">BUILDING INFO</h2>
      <div className="space-y-3">
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">
            TOTAL EC VALUE:
          </span>
          <span className="text-sm font-semibold text-gray-800">
            {buildingInfo.total_embodied_carbon
              ? buildingInfo.total_embodied_carbon.toFixed(2)
              : "N/A"}
          </span>
        </div>
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">GFA:</span>
          <span className="text-sm font-semibold text-gray-800">
            {buildingInfo.gfa || "N/A"}
          </span>
        </div>
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">TYPOLOGY:</span>
          <span className="text-sm font-semibold text-gray-800">
            {buildingInfo.typology || "N/A"}
          </span>
        </div>
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">PHASE:</span>
          <span className="text-sm font-semibold text-gray-800">
            {buildingInfo.phase || "N/A"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm font-medium text-gray-600">COST:</span>
          <span className="text-sm font-semibold text-gray-800">
            {buildingInfo.cost || "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
}
