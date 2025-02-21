import Navbar from "../components/NavBar";
import ProjectErrorDialog from "./ProjectErrorDialog";
import { useParams, useLocation, Link } from "react-router-dom";
import { getBuildingInfo } from "../api/api.jsx";
import { useEffect, useState } from "react";
import BarChart from "../components/BarChart.jsx";

function ECBreakdownPage() {
  const location = useLocation();
  const { projectName } = useParams();
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  // Charts Data
  const [barData, setBarData] = useState({
    labels: [],
    datasets: [],
  });

  const [elementData, setElementData] = useState({
    labels: [],
    datasets: [],
  });

  const [materialData, setMaterialData] = useState({
    labels: [],
    datasets: [],
  });

  // API data

  const [buildingInfo, setBuildingInfo] = useState({});
  const [ecValue, setEcValue] = useState(0);

  // console.log("Location state is ", location.state);

  const { projectId } = location.state;

  useEffect(() => {
    const fetchBuildingInfo = async () => {
      try {
        const response = await getBuildingInfo(projectId);
        console.log("API response data", response.data);
        //TODO fix to 2dp
        setBuildingInfo(response.data.ec_breakdown);
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
      !buildingInfo.by_building_system ||
      !buildingInfo.by_element ||
      Object.keys(buildingInfo.by_building_system).length === 0 ||
      Object.keys(buildingInfo.by_element).length === 0
    ) {
      console.log("State is empty");
      return; // Don't execute if state is empty
    }
    console.log("EC value: ", ecValue);
    console.log("Building info: ", buildingInfo);
    console.log("System info: ", buildingInfo.by_building_system);
    console.log("Element Info:", buildingInfo.by_element);
    const data = {
      labels: ["Total", "Superstructure", "Substructure"],
      datasets: [
        {
          label: "EC Breakdown",
          data: [
            ecValue,
            buildingInfo.by_building_system["superstructure_ec"],
            buildingInfo.by_building_system["substructure_ec"],
          ],
          backgroundColor: ["#E17352", "#E17352", "#D0C4C4"],
          borderColor: "#000000",
          borderWidth: 0,
        },
      ],
    };

    const elementLabels = buildingInfo.by_element
      ? Object.keys(buildingInfo.by_element)
      : {};

    const elementValues = buildingInfo.by_element
      ? Object.values(buildingInfo.by_element)
      : {};

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

    const materialLabels = buildingInfo.by_material
      ? Object.keys(buildingInfo.by_material)
      : {};

    const materialValues = buildingInfo.by_material
      ? Object.values(buildingInfo.by_material)
      : {};
    const material_data = {
      labels: materialLabels,
      datasets: [
        {
          label: "EC Breakdown by Material",
          data: materialValues,
          backgroundColor: ["#D0C4C4"],
          borderColor: "#000000",
          borderWidth: 0,
        },
      ],
    };
    setBarData(data);
    setElementData(element_data);
    setMaterialData(material_data);
  }, [buildingInfo, ecValue]);

  if (!projectId) {
    return <p className="text-red-500">No project ID provided.</p>;
  }

  if (loading) {
    return <p>Loading building system information...</p>; // Show loading state
  }

  if (error) {
    return <p className="text-red-500">{error}</p>; // Display error message
  }

  if (!buildingInfo) {
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
              <h1 className="font-bold">
                Overall EC Breakdown - <br /> by Material
              </h1>
              <div className="flex flex-col w-[400px] h-[200px]">
                <BarChart data={materialData} />
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
