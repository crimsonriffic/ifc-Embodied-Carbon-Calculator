import Navbar from "../components/NavBar";
import { Link, useParams, useLocation } from "react-router-dom";
import { useEffect, useState, version } from "react";
import { getProjectHistory, getProjectBreakdown } from "../api/api";
import ProjectErrorDialog from "./ProjectErrorDialog";
import BuildingInfoCard from "../components/BuildingInfoCard";
import SystemInfoCard from "../components/SystemInfoCard";
import MaterialInfoCard from "../components/MaterialInfoCard";
import ElementInfoCard from "../components/ElementInfoCard";
import BarChart from "../components/BarChart";
import HistoryTable from "../components/HistoryTable";
import UploadInfoCard from "../components/UploadInfoCard";
import { ChevronDownIcon } from "@heroicons/react/24/solid";
import SankeyChart from "../components/SankeyChart";
function ProjectPage() {
  const location = useLocation();
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [projectHistory, setProjectHistory] = useState([]);
  const [breakdownData, setBreakdownData] = useState([]);
  const [selectedBreakdownType, setSelectedBreakdownType] = useState("");
  const [versionNumber, setVersionNumber] = useState("");
  const [versionArray, setVersionArray] = useState([]);
  const [versionBar, setVersionBar] = useState({
    labels: [],
    datasets: [],
  });
  const [breakdownBar, setBreakdownBar] = useState({
    labels: [],
    datasets: [],
  });
  const { projectName } = useParams();

  const { projectId } = location.state;
  console.log("Project Name and project Id is ", projectName, projectId);
  const handleVersionClick = (e) => {
    setVersionNumber(e.target.value);
  };
  // DUMMY DATA FOR SANKEY
  const data = {
    total_ec: 10731.417534758186,
    ec_breakdown: [
      {
        category: "substructure",
        total_ec: 5342.129999999996,
        elements: [
          {
            element: "slab",
            ec: 1938.21875,
            materials: [{ material: "concrete", ec: 1938.21875 }],
          },
          {
            element: "wall",
            ec: 8311.679999999998,
            materials: [{ material: "concrete", ec: 8311.679999999998 }],
          },
        ],
      },
      {
        category: "superstructure",
        total_ec: 5389.287534758189,
        elements: [
          {
            element: "roof",
            ec: 481.5187485187485,
            materials: [{ material: "concrete", ec: 481.5187485187485 }],
          },
        ],
      },
    ],
  };
  /* Initial API calls to fetch project history and breakdown data */
  useEffect(() => {
    const fetchData = async () => {
      try {
        const historyResponse = await getProjectHistory(projectId);

        console.log("History response data: ", historyResponse.data.history);
        // Get the latest version from history
        const latestVersion = historyResponse.data.history[0]?.version || "";

        // If versionNumber is empty, use the latest version
        const versionToFetch = versionNumber || latestVersion;
        console.log("Fetching breakdown for version: ", versionToFetch);

        const breakdownResponse = await getProjectBreakdown(
          projectId,
          versionToFetch
        );
        console.log(
          "Breakdown response data: ",
          breakdownResponse.data.ec_breakdown
        );

        setProjectHistory(historyResponse.data.history);
        setBreakdownData(breakdownResponse.data.ec_breakdown);
        setSelectedBreakdownType("by_material");
        // Set latest version only if history exists
        // Set the versionNumber state if it's empty
        if (!versionNumber && latestVersion) {
          setVersionNumber(latestVersion);
        }

        setError(null);
        setLoading(false);
      } catch (err) {
        console.error("Failed to data: ", err);
        setError("Failed to fetch data."); // Set error message
      }
    };
    if (projectId) {
      fetchData();
    }
  }, [projectId, versionNumber]);

  useEffect(() => {
    if (!selectedBreakdownType) {
      console.log("Selected Breakdown Type is empty");
      return;
    }

    console.log("Selected Breakdown Type is : ", selectedBreakdownType);
    console.log(
      "Data of the selected breakdown type is : ",
      breakdownData[selectedBreakdownType]
    );

    const breakdownValues = breakdownData[selectedBreakdownType];

    // Extract labels (keys) and data (values)
    const labels = Object.keys(breakdownValues);
    const data = Object.values(breakdownValues);

    console.log("Labels: ", labels);
    console.log("Data: ", data);
    const barData = {
      labels: labels,
      datasets: [
        {
          label: "A1-A3 carbon Comparison",
          data: data,
          backgroundColor: "#E4937B",
          borderColor: "#000000",
          borderWidth: 0,
          barThickness: 40,
        },
      ],
    };
    setBreakdownBar(barData);
  }, [selectedBreakdownType]);
  /* Set the data for history bar chart */
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

    // Chart labels and values
    const chartLabels = sortedHistory
      ? sortedHistory.map((item) => "Upload " + item.version)
      : [];
    const chartValues = projectHistory
      ? sortedHistory.map((item) => item.total_ec)
      : [];
    console.log("Project history labels is: ", chartLabels);
    console.log("Project history values is: ", chartValues);
    const data = {
      labels: chartLabels,
      datasets: [
        {
          label: "A1-A3 carbon Comparison",
          data: chartValues,
          backgroundColor: ["#E4937B", "#CAA05C", "#E2D35E", "#E5E548"],
          borderColor: "#000000",
          borderWidth: 0,
          barThickness: 40,
        },
      ],
    };
    setVersionBar(data);
  }, [projectHistory]);

  const handleUpdateTypeChange = (e) => {
    setSelectedBreakdownType(e.target.value);
  };
  if (!projectId) {
    return <p className="text-red-500">No project ID provided.</p>;
  }

  if (loading) {
    return <p>Loading building system information...</p>; // Show loading state
  }

  if (error) {
    return <p className="text-red-500">{error}</p>; // Display error message
  }

  if (!projectHistory) {
    return <p>No project history available.</p>;
  }
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="overflow-x-auto bg-white rounded-lg  mt-16">
        {/**Check if project name exists */}
        {projectName ? (
          <div>
            <div className="bg-[#A9C0A0]  text-white rounded-lg px-4 py-2 flex items-center shadow-md mb-2 sm:max-w-md">
              <h1 className="text-2xl font-semibold tracking-wide">
                {decodeURIComponent(projectName)}
              </h1>
            </div>
            <div className="flex flex-col">
              {/**Top half of screen */}

              {/*Dropdown of version number*/}
              <div className="mb-4">
                <select
                  id="versionNumber"
                  value={versionNumber}
                  onChange={handleVersionClick}
                  className="text-2xl font-bold"
                >
                  {[...versionArray].reverse().map((version) => (
                    <option key={version} value={version} className="text-lg ">
                      Upload {version}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-row mt-2 justify-between gap-x-12">
                {/** Card 1 - Building Info*/}
                <div className="flex-1 flex-col sm:max-w-md ">
                  <h1 className="font-bold">Upload Information</h1>
                  <UploadInfoCard
                    uploadInfoData={projectHistory.find(
                      (item) => item.version === versionNumber
                    )}
                  />
                  <h1 className="mt-4 font-bold">Project Information</h1>
                  <BuildingInfoCard projectId={projectId} />
                </div>

                <div className=" flex-1 flex flex-col ">
                  <h1 className="font-bold">A1-A3 Embodied Carbon Data</h1>
                  <div className="flex flex-row">
                    <p>Total Embodied Carbon: </p>
                    <p className="font-bold">
                      {projectHistory
                        .find((item) => item.version === versionNumber)
                        ?.total_ec.toFixed(0)}{" "}
                      kgCO2eq
                    </p>
                  </div>
                  {/** Card 2 - Sankey chart  */}
                  <SankeyChart data={data} />
                </div>
                <div className="flex flex-1 flex-col">
                  {/** Card 3- Breakdown graphs */}

                  <div className="flex flex-row items-center gap-2 mt-4">
                    <label
                      htmlFor="breakdownType"
                      className="inline-block text-sm font-medium text-gray-700"
                    >
                      Compare by:
                    </label>

                    <select
                      id="breakdownType"
                      value={selectedBreakdownType}
                      onChange={handleUpdateTypeChange}
                      className="font-semibold rounded-lg"
                    >
                      <option value="by_material">Building Material</option>
                      <option value="by_element">Building Element</option>
                      <option value="by_building_system">
                        Building System
                      </option>
                    </select>
                  </div>
                  <div className="h-[200px]">
                    <BarChart data={breakdownBar} />
                  </div>
                </div>
              </div>
            </div>
            {/**Bottom half of screen */}
            <div className="flex flex-row justify-between mt-4 gap-x-16 h-[300px] ">
              <div className="flex flex-1 flex-col">
                <h1 className="font-bold mb-4">Project Upload History</h1>
                <HistoryTable projectHistory={projectHistory} />
              </div>

              <div className="flex flex-1 flex-col">
                <h1 className="font-bold mb-4">
                  A1-A3 Embodied Carbon Comparison
                </h1>

                <div className="h-full">
                  <BarChart data={versionBar} />
                </div>
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

export default ProjectPage;
