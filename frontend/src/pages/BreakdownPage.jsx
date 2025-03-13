import Navbar from "../components/NavBar";
import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, version, useMemo } from "react";
import Stepper from "../components/Stepper";

import ProjectErrorDialog from "./ProjectErrorDialog";
import { getProjectHistory, getProjectBreakdown } from "../api/api";
import SankeyChart from "../components/SankeyChart";
import BarChart from "../components/BarChart";

function BreakdownPage() {
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [sankeyData, setSankeyData] = useState([]);
  const [projectHistory, setProjectHistory] = useState([]);
  const [summaryData, setSummaryData] = useState([]);
  const [versionNumber, setVersionNumber] = useState("");
  const [versionArray, setVersionArray] = useState([]);
  const [materialBar, setMaterialBar] = useState({
    labels: [],
    datasets: [],
  });
  const [elementBar, setElementBar] = useState({
    labels: [],
    datasets: [],
  });
  const [buildingSystemBar, setBuildingSystemBar] = useState({
    labels: [],
    datasets: [],
  });
  const location = useLocation();
  const navigate = useNavigate();
  const { projectId } = location.state;
  const { projectName } = useParams();
  console.log("Project Name and project Id is ", projectName, projectId);
  // First useEffect for fetching data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch history first
        const historyResponse = await getProjectHistory(projectId);
        const history = historyResponse.data.history;
        setProjectHistory(history);

        // Determine version to fetch
        const latestVersion = history[0]?.version || "";
        const versionToFetch = versionNumber || latestVersion;

        // Update version number if not set
        if (!versionNumber) {
          setVersionNumber(latestVersion);
        }

        // Fetch breakdown data
        const breakdownResponse = await getProjectBreakdown(
          projectId,
          versionToFetch
        );
        const { summary, ec_breakdown } = breakdownResponse.data;

        setSummaryData(summary);
        setSankeyData(ec_breakdown);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch data: ", err);
        setError("Failed to fetch data.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [projectId, versionNumber]);
  useEffect(() => {
    if (!projectHistory) {
      console.log("Project history is empty");
      return;
    }

    console.log("Project history is: ", projectHistory);
    const sortedHistory = projectHistory
      ? [...projectHistory].sort((a, b) => a.version - b.version)
      : [];

    // Version array for the drop down to refer to
    const versionArr = sortedHistory
      ? sortedHistory.map((item) => item.version)
      : [];
    setVersionArray(versionArr);
  }, [projectHistory]);
  useEffect(() => {
    console.log("Full SummaryData: ", summaryData);
    if (
      !summaryData ||
      !summaryData["by_material"] ||
      !summaryData["by_element"] ||
      !summaryData["by_building_system"]
    ) {
      console.log("SummaryData is not ready yet");
      return;
    }
    console.log("SummaryData is: ", summaryData);
    const materialValues = summaryData["by_material"];
    const elementValues = summaryData["by_element"];
    const systemValues = summaryData["by_building_system"];
    console.log(
      "Const values are",
      materialValues,
      elementValues,
      systemValues
    );

    // Helper function to generate bar chart data
    const generateBarData = (values, label) => {
      if (!values) return null; // Handle undefined values safely
      const labels = Object.keys(values).map(
        (key) => key.charAt(0).toUpperCase() + key.slice(1)
      );
      const data = Object.values(values);

      console.log(`${label} labels and data: `, labels, data);
      return {
        labels: labels,
        datasets: [
          {
            label: `A1-A3 Carbon Comparison (${label})`,
            data: data,
            backgroundColor: "#B7D788",
            borderColor: "#000000",
            borderWidth: 0,
            barThickness: 40,
          },
        ],
      };
    };

    // Set state for all three bar charts
    setMaterialBar(generateBarData(materialValues, "Material"));
    setElementBar(generateBarData(elementValues, "Element"));
    setBuildingSystemBar(generateBarData(systemValues, "Building System"));
  }, [summaryData]);
  if (!projectId) {
    return <p className="text-red-500 mt-16">No project ID provided.</p>;
  }

  if (loading) {
    return <p className="mt-16">Loading project data...</p>; // Show loading state
  }

  if (error) {
    return <p className="text-red-500 mt-16">{error}</p>; // Display error message
  }

  if (!projectHistory) {
    return <p className="mt-16">No project history available.</p>;
  }
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Detailed Results</h1>
      </div>
      <div className="mt-6">
        <Stepper currentStep={5} />
      </div>
      <div className="bg-[#A9C0A0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mt-4 mb-6 sm:max-w-md">
        <h1 className="text-2xl font-semibold tracking-wide">
          {decodeURIComponent(projectName)}
        </h1>
      </div>
      {/*Dropdown of version number*/}
      <div className="mb-4">
        <select
          id="versionNumber"
          value={versionNumber}
          onChange={(e) => setVersionNumber(e.target.value)}
          className="text-2xl font-bold"
        >
          {[...versionArray].reverse().map((version) => (
            <option key={version} value={version} className="text-lg ">
              Upload {version}
            </option>
          ))}
        </select>
      </div>
      <h1 className="text-2xl font-semibold tracking-wide">
        A1-A3 Embodied Carbon Data
      </h1>

      <div className="flex gap-4 px-1 w-full overflow-x-hidden overflow-y-hidden">
        <div className="flex-[1.5] min-w-0 bg-white p-4 rounded-lg shadow-md">
          <div className="flex flex-row">
            <p>Total Embodied Carbon: </p>
            <span className="font-bold">
              {Number(
                projectHistory
                  .find((item) => item.version === versionNumber)
                  ?.total_ec.toFixed(0)
              ).toLocaleString()}{" "}
              kgCO2eq
            </span>
          </div>

          <SankeyChart data={sankeyData} width={380} height={250} />
        </div>
        {/* Card 2 - Building Material */}
        <div className="flex-1 min-w-0 bg-white p-4 rounded-lg shadow-md ">
          <p className="mb-4">
            Hotspot by: <span className="font-bold">Building Material</span>
          </p>
          <div className="h-[300px]">
            <BarChart data={materialBar} />
          </div>
        </div>
        {/* Card 3 - Building Element */}
        <div className="flex-1 min-w-0 bg-white p-4 rounded-lg shadow-md ">
          <p className="mb-4">
            Hotspot by: <span className="font-bold">Building Element</span>
          </p>
          <div className="h-[300px]">
            <BarChart data={elementBar} />
          </div>
        </div>

        {/* Card 4 - Building System */}
        <div className="flex-1 min-w-0 bg-white p-4 rounded-lg shadow-md ">
          <p className="mb-4">
            Hotspot by: <span className="font-bold">Building System</span>
          </p>
          <div className="h-[300px]">
            <BarChart data={buildingSystemBar} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default BreakdownPage;
