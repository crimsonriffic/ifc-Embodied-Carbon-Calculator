import { getBuildingInfo } from "../api/api.jsx";
import { useEffect, useState } from "react";
import PieChart from "./PieChart.jsx";
import { Pie } from "react-chartjs-2";
import { ArrowRightIcon } from "@heroicons/react/24/solid";
import { useNavigate, useParams, useLocation } from "react-router-dom";

export default function SystemInfoCard({ projectId }) {
  const [systemInfo, setSystemInfo] = useState([]);
  const [ecValue, setEcValue] = useState(0);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true); // Loading state
  const navigate = useNavigate();
  const location = useLocation();
  const { projectName } = useParams();
  console.log("Location state is ", location.state);

  const handleGoToBreakdown = (projectId, projectName) => {
    console.log("HandleGoToBreakdown called");
    navigate(`/ecbreakdown/${encodeURIComponent(projectName)}`, {
      state: { projectId },
    });
  };

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

  const piedata = {
    labels: ["Superstructure", "Substructure"],
    datasets: [
      {
        label: "EC Breakdown",
        data: [
          systemInfo["superstructure_ec"].toFixed(2),
          systemInfo["substructure_ec"].toFixed(2),
        ],
        backgroundColor: ["#E17352", "#D0C4C4"],
        borderColor: "#000000",
        borderWidth: 2,
      },
    ],
  };
  return (
    <div className="bg-white shadow-lg rounded-lg border-2 border-gray-800  sm:max-w-md">
      <h2 className="text-lg font-bold  text-gray-800 px-4 py-2 border-b-2 border-gray-800">
        EC DISTRIBUTION
      </h2>
      <div className="flex flex-col p-4">
        <PieChart data={piedata} />
      </div>
      <div className="flex justify-end px-2 py-1">
        <button
          className="text-gray-500 hover:bg-blue-500"
          onClick={() => handleGoToBreakdown(projectId, projectName)}
        >
          <ArrowRightIcon className="w-6 h-6 text-gray-500" />
        </button>
      </div>
    </div>
  );
}
