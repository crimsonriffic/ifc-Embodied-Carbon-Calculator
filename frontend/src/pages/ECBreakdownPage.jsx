import Navbar from "../components/NavBar";
import MaterialInfoCard from "../components/MaterialInfoCard";
import ElementInfoCard from "../components/ElementInfoCard";
import ProjectErrorDialog from "./ProjectErrorDialog";
import { useParams, useLocation, Link } from "react-router-dom";
import { getBuildingInfo } from "../api/api.jsx";
import { useEffect, useState } from "react";
import BarChart from "../components/BarChart.jsx";

function ECBreakdownPage() {
  const location = useLocation();
  const { projectName } = useParams();
  const [error, setError] = useState(null);
  const [barData, setBarData] = useState({
    labels: [],
    datasets: [],
  });

  const [elementData, setElementData] = useState({
    labels: [],
    datasets: [],
  });
  const [elementInfo, setElementInfo] = useState({});
  const [loading, setLoading] = useState(true); // Loading state
  const [systemInfo, setSystemInfo] = useState({});
  const [ecValue, setEcValue] = useState(0);
  console.log("Location state is ", location.state);

  const { projectId } = location.state;

  useEffect(() => {
    const fetchBuildingInfo = async () => {
      try {
        const response = await getBuildingInfo(projectId);
        console.log("Building Info (EC breakdown)", response.data);
        //TODO fix to 2dp
        setSystemInfo(response.data.ec_breakdown.by_building_system);
        setElementInfo(response.data.ec_breakdown.by_element);
        setEcValue(response.data.total_ec.toFixed(2));

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

  useEffect(() => {
    if (
      !ecValue ||
      Object.keys(systemInfo).length === 0 ||
      Object.keys(elementInfo).length === 0
    ) {
      return; // Don't execute if state is empty
    }
    console.log("EC value, ", ecValue);
    console.log("System info, ", systemInfo);
    console.log("Element Info:", elementInfo);
    const data = {
      labels: ["Total", "Superstructure", "Substructure"],
      datasets: [
        {
          label: "EC Breakdown",
          data: [
            ecValue,
            systemInfo["superstructure_ec"],
            systemInfo["substructure_ec"],
          ],
          backgroundColor: ["#E17352", "#E17352", "#D0C4C4"],
          borderColor: "#000000",
          borderWidth: 0,
        },
      ],
    };

    const elementLabels = elementInfo ? Object.keys(elementInfo) : {};

    const elementValues = elementInfo ? Object.values(elementInfo) : {};

    console.log("Element labels are ", elementLabels);
    console.log("Element values are ", elementValues);
    const element_data = {
      labels: elementLabels,
      datasets: [
        {
          label: "EC Breakdown by Element",
          data: elementValues,
          backgroundColor: ["#D0C4C4"],
          borderColor: "#000000",
          borderWidth: 0,
        },
      ],
    };
    setBarData(data);
    setElementData(element_data);
  }, [elementInfo, systemInfo, ecValue]);

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

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="overflow-x-auto bg-white rounded-lg p-4 mt-16">
        {/**Check if project name exists */}
        {projectName ? (
          <div>
            <div className="bg-[#A0ABC0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mb-2 sm:max-w-xs">
              <h1 className="text-lg font-semibold tracking-wide">
                {decodeURIComponent(projectName)}
              </h1>
            </div>
            <div className="space-y-1">
              <h1 className="font-bold">
                Overall EC Breakdown - <br /> by Substructure/Superstructure
              </h1>
              <div className="flex flex-col w-[400px] h-[200px]">
                <BarChart data={barData} />
              </div>
              <h1 className="font-bold">
                Overall EC Breakdown - <br /> by Element
              </h1>
              <div className="flex flex-col w-[400px] h-[200px]">
                <BarChart data={elementData} />
              </div>
            </div>
          </div>
        ) : (
          <ProjectErrorDialog />
        )}
      </div>
    </div>
  );
}

export default ECBreakdownPage;
