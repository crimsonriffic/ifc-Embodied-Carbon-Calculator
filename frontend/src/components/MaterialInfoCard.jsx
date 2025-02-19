import { getBuildingInfo } from "../api/api.jsx";
import { useEffect, useState } from "react";
export default function MaterialInfoCard({ projectId }) {
  const [materialInfo, setMaterialInfo] = useState([]);
  const [ecValue, setEcValue] = useState(0);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true); // Loading state

  useEffect(() => {
    const fetchBuildingInfo = async () => {
      try {
        const response = await getBuildingInfo(projectId);
        console.log("Building Info (EC breakdown)", response.data);
        setMaterialInfo(response.data.ec_breakdown.by_material);
        setEcValue(response.data.total_embodied_carbon);
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
    return <p>Loading material information...</p>; // Show loading state
  }

  if (error) {
    return <p className="text-red-500">{error}</p>; // Display error message
  }

  if (!materialInfo) {
    return <p>No material information available.</p>;
  }
  return (
    <div className="bg-white shadow-lg rounded-lg p-6 border border-gray-300  sm:max-w-xs">
      <h2 className="text-lg font-bold mb-4 text-gray-800">MATERIAL INFO</h2>
      <div className="space-y-3">
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">
            TOTAL EC VALUE:
          </span>
          <span className="text-sm font-semibold text-gray-800">
            {ecValue ? ecValue.toFixed(2) : "N/A"}
          </span>
        </div>
        <ul>
          {Object.entries(materialInfo).map(([key, value]) => (
            <li key={key}>
              <strong>{key}:</strong> {value.toFixed(2)}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
