import { getBuildingInfo } from "../api/api.jsx";
import { useEffect, useState } from "react";
import BarChart from "./BarChart.jsx";
export default function SystemInfoCard({ projectId }) {
  const [systemInfo, setSystemInfo] = useState([]);
  const [ecValue, setEcValue] = useState(0);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true); // Loading state

  useEffect(() => {
    const fetchBuildingInfo = async () => {
      try {
        const response = await getBuildingInfo(projectId);
        console.log("Building Info (EC breakdown)", response.data);
        setSystemInfo(response.data.ec_breakdown.by_building_system);
        setEcValue(response.data.total_ec);
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
    return <p>Loading building system information...</p>; // Show loading state
  }

  if (error) {
    return <p className="text-red-500">{error}</p>; // Display error message
  }

  if (!systemInfo) {
    return <p>No building information available.</p>;
  }

  const data = {
    labels: ["TOTAL", "SUPER-STRUCTURE", "SUB-STRUCTURE"],
    datasets: [
      {
        label: [""],
        data: [
          ecValue,
          systemInfo["superstructure_ec"].toFixed(2),
          systemInfo["substructure_ec"].toFixed(2),
        ],
        backgroundColor: "rgba(75,192,192,0.6)",
        borderColor: "rgba(75,192,192,1)",
        borderWidth: 1,
      },
    ],
  };
  return (
    <div className="bg-white shadow-lg rounded-lg p-6 border border-gray-300  sm:max-w-xs">
      <h2 className="text-lg font-bold mb-4 text-gray-800">
        BUILDING SYSTEM INFO
      </h2>
      <div className="space-y-3">
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">
            TOTAL EC VALUE:
          </span>
          <span className="text-sm font-semibold text-gray-800">
            {ecValue ? ecValue.toFixed(2) : "N/A"}
          </span>
        </div>
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">
            Substructure EC
          </span>
          <span className="text-sm font-semibold text-gray-800">
            {systemInfo["substructure_ec"].toFixed(2) || "N/A"}
          </span>
        </div>
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">
            Superstructure EC
          </span>
          <span className="text-sm font-semibold text-gray-800">
            {systemInfo["superstructure_ec"].toFixed(2) || "N/A"}
          </span>
        </div>
        <BarChart data={data} />
      </div>
    </div>
  );
}
