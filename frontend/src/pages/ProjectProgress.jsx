import { useUser } from "../context/UserContext";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, version } from "react";
import { getProjectHistory, getProjectInfo } from "../api/api";

import SankeyChart from "../components/SankeyChart";

function ProjectProgress({ projectId, projectName }) {
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [projectHistory, setProjectHistory] = useState([]);
  const [totalEc, setTotalEc] = useState("");
  const [versionNumber, setVersionNumber] = useState("");
  const [versionArray, setVersionArray] = useState([]);
  const [projectInfo, setProjectInfo] = useState({});
  const [benchmarkStandard, setBenchmarkstandard] = useState("");
  const [benchmarkTarget, setBenchmarkTarget] = useState(0);
  console.log(projectId);

  const handleStandardsClick = (e) => {
    const selectedStandard = e.target.value;
    setBenchmarkstandard(selectedStandard);
    setBenchmarkTarget(projectInfo.benchmark[selectedStandard]); // Update target value};
  };
  useEffect(() => {
    const fetchData = async () => {
      try {
        const historyResponse = await getProjectHistory(projectId);
        console.log("History response data: ", historyResponse.data.history);
        // Get the latest version from history
        // If versionNumber is empty, use the latest version
        const latestVersion = historyResponse.data.history[0]?.version || "";
        const versionToFetch = versionNumber || latestVersion;
        console.log("Fetching breakdown for version: ", versionToFetch);

        const projectResponse = await getProjectInfo(projectId);
        console.log("Project Info response data is: ", projectResponse.data);
        console.log("Benchmarks are", projectResponse.data.benchmark);
        setProjectInfo(projectResponse.data);
        setProjectHistory(historyResponse.data.history);

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
  }, [projectHistory, versionNumber]);
  useEffect(() => {
    if (
      projectInfo.benchmark &&
      Object.keys(projectInfo.benchmark).length > 0
    ) {
      const firstBenchmark = Object.keys(projectInfo.benchmark)[0]; // Get first key
      setBenchmarkstandard(firstBenchmark);
      setBenchmarkTarget(projectInfo.benchmark[firstBenchmark]); // Set initial target value
    }
  }, [projectInfo.benchmark]);
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
      <h1 className="text-2xl font-bold mb-4">Project Progress</h1>
      {/**Left side */}
      <div className="flex flex-row space-x-24">
        <div className=" flex flex-col w-1/3 min-w-[300px] gap-y-4">
          <div>
            <h1 className="text-sm">Typology</h1>
            <p className=" text-xl font-bold ">{projectInfo.typology}</p>
          </div>

          <div>
            <h1 className="text-sm">Benchmark Standard</h1>
            <select
              id="benchmarkStandard"
              value={benchmarkStandard}
              onChange={(e) => handleStandardsClick(e)}
              className="text-xl font-bold w-full focus:outline-none focus:border-none focus:ring-0 "
            >
              {Object.entries(projectInfo.benchmark).map(([key, value]) => (
                <option key={key} value={key} className="text-sm">
                  {key}
                </option>
              ))}
            </select>
          </div>

          <div>
            <h1 className="text-sm">Benchmark Target</h1>
            <p className="text-xl font-bold ">{benchmarkTarget}</p>
          </div>

          <div>
            <h1 className="text-sm">Select Upload for Progress Check</h1>
            <p className="text-xl font-bold ">-</p>
          </div>
        </div>
        {/** Card 2 - Sankey chart  */}
      </div>
    </div>
  );
}

export default ProjectProgress;
