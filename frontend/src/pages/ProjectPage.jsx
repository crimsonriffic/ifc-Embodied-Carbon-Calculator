import Navbar from "../components/NavBar";
import { Link, useParams, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { getProjectHistory, getProjectBreakdown } from "../api/api";
import ProjectErrorDialog from "./ProjectErrorDialog";
import BuildingInfoCard from "../components/BuildingInfoCard";
import SystemInfoCard from "../components/SystemInfoCard";
import MaterialInfoCard from "../components/MaterialInfoCard";
import ElementInfoCard from "../components/ElementInfoCard";
import BarChart from "../components/BarChart";
import HistoryTable from "../components/HistoryTable";
function ProjectPage() {
  const location = useLocation();
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [projectHistory, setProjectHistory] = useState([]);
  const [breakdownData, setBreakdownData] = useState([]);
  const [selectedBreakdownType, setSelectedBreakdownType] = useState("");
  const [versionBar, setVersionBar] = useState({
    labels: [],
    datasets: [],
  });
  const [breakdownBar, setBreakdownBar] = useState({
    labels: [],
    datasets: [],
  });
  const { projectName } = useParams();
  console.log("Location state is ", location.state);

  const { projectId } = location.state;

  /* Initial API calls to fetch project history and breakdown data */
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [historyResponse, breakdownResponse] = await Promise.all([
          getProjectHistory(projectId),
          getProjectBreakdown(projectId),
        ]);
        console.log("History response data: ", historyResponse.data);
        console.log(
          "Breakdown response data: ",
          breakdownResponse.data.ec_breakdown
        );
        setProjectHistory(historyResponse.data.history);
        setBreakdownData(breakdownResponse.data.ec_breakdown);
        setSelectedBreakdownType("by_material");
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
  }, [projectId]);

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

    const versionLabels = sortedHistory
      ? sortedHistory.map((item) => item.version)
      : [];
    const versionValues = projectHistory
      ? sortedHistory.map((item) => item.total_ec)
      : [];
    console.log("Project history labels is: ", versionLabels);
    console.log("Project history values is: ", versionValues);
    const data = {
      labels: versionLabels,
      datasets: [
        {
          label: "A1-A3 carbon Comparison",
          data: versionValues,
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
      <div className="overflow-x-auto bg-white rounded-lg p-4 mt-16">
        {/**Check if project name exists */}
        {projectName ? (
          <div>
            <div className="bg-[#A9C0A0]  text-white rounded-lg px-4 py-2 flex items-center shadow-md mb-2 sm:max-w-md">
              <h1 className="text-lg font-semibold tracking-wide">
                {decodeURIComponent(projectName)}
              </h1>
            </div>
            <div className="flex flex-col">
              <div className="flex flex-row justify-between gap-x-16 h-[300px] ">
                <HistoryTable projectHistory={projectHistory} />

                <div className="flex flex-1 flex-col">
                  <h1 className="font-bold mb-4">
                    A1-A3 Embodied Carbon Comparison
                  </h1>
                  <div className="h-full">
                    <BarChart data={versionBar} />
                  </div>
                </div>
              </div>

              {/**Bottom half of screen */}
              <div className="flex flex-row mt-6 justify-between gap-x-16">
                {/** Card 1 - Building Info*/}
                <div className="flex-1 flex-col sm:max-w-md ">
                  <h1 className="font-bold">Project Information</h1>
                  <BuildingInfoCard projectId={projectId} />
                </div>

                {/** Card 2- Breakdown graphs */}
                <div className=" flex-1 flex flex-col ">
                  <div className="flex flex-row items-center gap-2">
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
          </div>
        ) : (
          <ProjectErrorDialog />
        )}
      </div>
    </div>
  );
}

export default ProjectPage;
