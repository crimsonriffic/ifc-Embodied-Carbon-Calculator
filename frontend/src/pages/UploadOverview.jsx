import { useUser } from "../context/UserContext";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, version } from "react";
import { getProjectHistory, getProjectBreakdown } from "../api/api";
import BuildingInfoCard from "../components/BuildingInfoCard";

import UploadInfoCard from "../components/UploadInfoCard";
import SankeyChart from "../components/SankeyChart";
import { Sankey } from "recharts";

function UploadOverview({ projectId, projectName }) {
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [sankeyData, setSankeyData] = useState([]);
  const [projectHistory, setProjectHistory] = useState([]);
  const [summaryData, setSummaryData] = useState([]);
  const [versionNumber, setVersionNumber] = useState("");
  const [versionArray, setVersionArray] = useState([]);

  const handleVersionClick = (e) => {
    setVersionNumber(e.target.value);
  };
  console.log(projectId);
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
      {/**Left side */}
      <div className="flex flex-row space-x-28">
        <div className=" flex flex-col ">
          <h1>Total A1-A3 Embodied Carbon</h1>
          <p className="font-bold mb-4">
            {Number(
              projectHistory
                .find((item) => item.version === versionNumber)
                ?.total_ec.toFixed(0)
            ).toLocaleString()}{" "}
            kgCO2eq
          </p>

          <h1>A1-A3 Embodied Carbon per floor area</h1>
          <p className="font-bold mb-4">-</p>

          <h1>Computed Floor Area</h1>
          <p className="font-bold mb-4">-</p>

          <h1>Status</h1>
          <p className="font-bold mb-4">Status</p>
        </div>
        {/** Card 2 - Sankey chart  */}
        <SankeyChart data={sankeyData} width={700} height={350} />
      </div>
    </div>
  );
}

export default UploadOverview;
