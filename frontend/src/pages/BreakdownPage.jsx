import Navbar from "../components/NavBar";
import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, version } from "react";
import Stepper from "../components/Stepper";

import ProjectErrorDialog from "./ProjectErrorDialog";
import { getProjectHistory, getProjectBreakdown } from "../api/api";
import SankeyChart from "../components/SankeyChart";

function BreakdownPage() {
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [sankeyData, setSankeyData] = useState([]);
  const [projectHistory, setProjectHistory] = useState([]);
  const [summaryData, setSummaryData] = useState([]);
  const [versionNumber, setVersionNumber] = useState("");
  const [versionArray, setVersionArray] = useState([]);
  const location = useLocation();
  const navigate = useNavigate();
  const { projectId } = location.state;
  const { projectName } = useParams();
  console.log("Project Name and project Id is ", projectName, projectId);
  useEffect(() => {
    const fetchData = async () => {
      try {
        const historyResponse = await getProjectHistory(projectId);

        console.log("History response data: ", historyResponse.data.history);
        setProjectHistory(historyResponse.data.history);
        // Get the latest version from history
        const latestVersion = historyResponse.data.history[0]?.version || "";
        const versionToFetch = versionNumber || latestVersion;
        console.log("Fetching breakdown for version: ", versionToFetch);
        if (!versionNumber) {
          setVersionNumber(latestVersion);
        }
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
        // Set latest version only if history exists
        // Set the versionNumber state if it's empty

        const sortedHistory = projectHistory
          ? [...projectHistory].sort((a, b) => a.version - b.version)
          : [];

        // Version array for the drop down to refer to
        const versionArr = sortedHistory
          ? sortedHistory.map((item) => item.version)
          : [];
        setVersionArray(versionArr);

        setError(null);
        setLoading(false);
      } catch (err) {
        console.error("Failed to data: ", err);
        setError("Failed to fetch data."); // Set error message
      }
    };

    fetchData();
  }, [projectId, versionNumber]);

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

      <div className="flex flex-row space-x-10">
        <div className="flex flex-col">
          <div className="flex flex-row mt-4">
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
          <SankeyChart data={sankeyData} />
        </div>
        <div className="flex flex-col">
          <p>Hotspot by: </p>
          <p className="font-bold">Building Material</p>
        </div>
        <div className="flex flex-col">
          <p>Hotspot by: </p>
          <p className="font-bold">Building Element</p>
        </div>
        <div className="flex flex-col">
          <p>Hotspot by: </p>
          <p className="font-bold">Building System</p>
        </div>
      </div>
    </div>
  );
}

export default BreakdownPage;
