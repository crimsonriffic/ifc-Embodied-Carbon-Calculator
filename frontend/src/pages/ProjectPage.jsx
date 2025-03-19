import Navbar from "../components/NavBar";
import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, version } from "react";
import { getProjectHistory, getProjectBreakdown } from "../api/api";
import ProjectErrorDialog from "./ProjectErrorDialog";
import BuildingInfoCard from "../components/BuildingInfoCard";
import MaterialInfoCard from "../components/MaterialInfoCard";
import ElementInfoCard from "../components/ElementInfoCard";
import BarChart from "../components/BarChart";
import HistoryTable from "../components/HistoryTable";
import UploadInfoCard from "../components/UploadInfoCard";
import { ChevronDownIcon } from "@heroicons/react/24/solid";
import SankeyChart from "../components/SankeyChart";
import Stepper from "../components/Stepper";
function ProjectPage() {
  const location = useLocation();
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [sankeyData, setSankeyData] = useState([]);
  const [projectHistory, setProjectHistory] = useState([]);
  const [summaryData, setSummaryData] = useState([]);
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
  const fromHomePage = location.state?.fromHomePage === true;
  const navigate = useNavigate();
  console.log("Project Name and project Id is ", projectName, projectId);
  const handleVersionClick = (e) => {
    setVersionNumber(e.target.value);
  };
  const handleMoreDetails = (projectId, projectName) => {
    console.log("HandleMoreDetails called");
    navigate(`/breakdown/${encodeURIComponent(projectName)}`, {
      state: { projectId },
    });
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
        console.log("Breakdown response data: ", breakdownResponse.data);
        console.log(
          "Sankey data that i want: ",
          breakdownResponse.data.ec_breakdown
        );
        setProjectHistory(historyResponse.data.history);
        setSummaryData(breakdownResponse.data.summary);
        setSankeyData(breakdownResponse.data.ec_breakdown);
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
      summaryData[selectedBreakdownType]
    );
    console.log("Sankey data is", sankeyData);

    const breakdownValues = summaryData[selectedBreakdownType];

    // Extract labels (keys) and data (values)
    const labels = Object.keys(breakdownValues).map(
      (key) => key.charAt(0).toUpperCase() + key.slice(1)
    );
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
    const chartValues = [16000, 14000, 12000, 10731];
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
      <div className="mt-6">{!fromHomePage && <Stepper currentStep={5} />}</div>
      {/**Check if project name exists */}

      <div className="bg-[#A9C0A0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mt-4 mb-6 sm:max-w-md">
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

        <div className="flex flex-row mt-2 justify-between gap-x-96">
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
            <div className="flex items-center gap-2">
              <h1 className="font-bold">A1-A3 Embodied Carbon Data</h1>
              <button
                className="inline-flex items-center gap-1 px-3 py-1 text-sm bg-green-100 text-green-800 rounded-md hover:bg-green-200"
                onClick={() => {
                  handleMoreDetails(projectId, projectName);
                }}
              >
                More details
                <span>→</span>
              </button>
            </div>
            <div className="flex flex-row">
              <p>Total Embodied Carbon: </p>
              <p className="font-bold">
                {Number(
                  projectHistory
                    .find((item) => item.version === versionNumber)
                    ?.total_ec.toFixed(0)
                ).toLocaleString()}{" "}
                kgCO2eq
              </p>
            </div>
            {/** Card 2 - Sankey chart  */}
            <SankeyChart data={sankeyData} width={600} height={300} />
          </div>
        </div>
      </div>
      {/**Bottom half of screen */}
      <div className="flex flex-row justify-between mt-12 gap-x-16 h-[300px] ">
        <div className="flex flex-1 flex-col">
          <h1 className="font-bold mb-4">Project Upload History</h1>
          <HistoryTable projectHistory={projectHistory} />
        </div>

        <div className="flex flex-1 flex-col">
          <h1 className="font-bold mb-4">A1-A3 Embodied Carbon Comparison</h1>

          <div className="h-full">
            <BarChart data={versionBar} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProjectPage;
