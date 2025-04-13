import { useUser } from "../context/UserContext";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, version } from "react";
import {
  getProjectHistory,
  getProjectBreakdown,
  getAiBreakdown,
  getMissingMaterials,
} from "../api/api";

import SankeyChart from "../components/SankeyChart";
import Sankey2 from "../components/Sankey2";

function UploadOverview({ projectId, projectName, projectHistory }) {
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [sankeyData, setSankeyData] = useState([]);
  const [currentVersionData, setCurrentVersionData] = useState({});
  const [totalEc, setTotalEc] = useState("");
  const [summaryData, setSummaryData] = useState(null);
  const [versionNumber, setVersionNumber] = useState("");
  const [versionArray, setVersionArray] = useState([]);
  const [isEnabled, setIsEnabled] = useState(false);
  const [buildingList, setBuildingList] = useState([]);
  const [materialList, setMaterialList] = useState([]);
  const [isErrorDetected, setIsErrorDetected] = useState(false);
  const handleVersionClick = (e) => {
    setVersionNumber(e.target.value);
  };
  const toggleHandler = () => {
    setIsEnabled((prevState) => {
      const newState = !prevState;
      if (projectId) {
        if (newState) {
          fetchAiData(); // Fetch AI-enhanced breakdown
        } else {
          fetchData(); // Fetch standard breakdown
        }
      }
      return newState;
    });
  };

  const convertToSingular = (str) => {
    // Check if the word ends with "s" and remove it if present
    if (str.endsWith("s")) {
      return str.slice(0, -1); // Remove the last character ("s")
    }
    return str; // Return the original string if it doesn't end with "s"
  };

  const extractKeysFromSummaryData = (summaryData) => {
    // Extract keys from the summaryData for building elements and materials
    console.log("Checking..", summaryData.by_element, summaryData.by_material);
    const buildingElements = Object.entries(summaryData.by_element)
      .filter(([_, value]) => value !== 0) // Only include non-zero values
      .map(([key]) => convertToSingular(key));
    const materials = Object.keys(summaryData.by_material).filter(
      (key) => key !== "Others"
    );
    return { buildingElements, materials };
  };
  const fetchData = async () => {
    try {
      const latestVersion = projectHistory[0]?.version || "";
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
      console.log("Total ec is", breakdownResponse.data.ec_breakdown.total_ec);
      console.log("Sumary data is", breakdownResponse.data.summary);
      setTotalEc(breakdownResponse.data.ec_breakdown.total_ec.toFixed(0));
      setSummaryData(breakdownResponse.data.summary);
      setSankeyData(breakdownResponse.data.ec_breakdown);
      const { buildingElements, materials } = extractKeysFromSummaryData(
        breakdownResponse.data.summary
      );
      setBuildingList(buildingElements);
      setMaterialList(materials);

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

  const fetchAiData = async () => {
    try {
      const latestVersion = projectHistory[0]?.version || "";
      const versionToFetch = versionNumber || latestVersion;
      console.log("Fetching AI breakdown for version: ", versionToFetch);

      const breakdownResponse = await getAiBreakdown(projectId, versionToFetch);
      console.log("AI Breakdown response data: ", breakdownResponse.data);
      console.log(
        "Sankey AI data that i want: ",
        breakdownResponse.data.ec_breakdown
      );
      console.log("Total ec is", breakdownResponse.data.ec_breakdown.total_ec);

      setTotalEc(breakdownResponse.data.ec_breakdown.total_ec.toFixed(0));
      setSummaryData(breakdownResponse.data.summary);
      setSankeyData(breakdownResponse.data.ec_breakdown);
      const { buildingElements, materials } = extractKeysFromSummaryData(
        breakdownResponse.data.summary
      );
      setBuildingList(buildingElements);
      setMaterialList(materials);

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
  useEffect(() => {
    const fetchErrorData = async () => {
      try {
        setLoading(true);
        const missingMaterialsResponse = await getMissingMaterials(projectId);

        console.log(
          "Missing materials response: ",
          missingMaterialsResponse.data
        );
        console.log(
          Number(missingMaterialsResponse.data.total_missing_materials)
        );
        if (Number(missingMaterialsResponse.data.total_missing_materials) > 0) {
          console.log("Errors detected");
          setIsErrorDetected(true);
          return;
        } else {
          setIsErrorDetected(false);
          console.log("Errors not detected -No materials data found!");
        }
      } catch (err) {
        console.error("Failed to fetch data: ", err);
      }
    };
    if (projectId) {
      fetchErrorData();
    }
  }, [projectId]);
  useEffect(() => {
    if (projectId) {
      isEnabled ? fetchAiData() : fetchData();
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

    const currentData = projectHistory.find(
      (item) => item.version === versionNumber
    );
    console.log("Setting currentVersionData:", currentData);

    setCurrentVersionData(currentData || {});
  }, [projectHistory, versionNumber]);

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

      {/**Left side */}
      <div className="flex flex-row space-x-24">
        <div className=" flex flex-col w-1/3 min-w-[300px] gap-y-4">
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
          <div>
            <h1 className="text-sm">Total A1-A3 Embodied Carbon</h1>
            <p className=" text-xl font-bold ">
              {Number(totalEc).toLocaleString()} kgCO2eq
            </p>
          </div>

          <div>
            <h1 className="text-sm">A1-A3 Embodied Carbon per floor area</h1>
            <p className=" text-xl font-bold">
              {" "}
              {(Number(totalEc) / Number(currentVersionData.gfa)).toFixed(
                0
              )}{" "}
              kgCO2eq/m2
            </p>
          </div>

          <div>
            <h1 className="text-sm">Computed Floor Area</h1>
            <p className="text-xl font-bold ">
              {Number(currentVersionData.gfa).toFixed(0)} m2
            </p>
          </div>

          <div>
            <h1 className="text-sm">Status</h1>
            <p className="text-xl font-bold">{currentVersionData.status}</p>
          </div>

          <div>
            <h1 className="text-sm">Uploaded by</h1>
            <p className="text-sm font-bold">
              {currentVersionData.uploaded_by}
            </p>
          </div>

          <div>
            <h1 className="text-sm">Comments</h1>
            <p className="text-sm font-bold">{currentVersionData.comments}</p>
          </div>
        </div>
        {/** Card 2 - Sankey chart  */}
        <div className="flex flex-col">
          <h1 className="text-2xl font-bold text-[#5B9130]">
            Total A1-A3 Embodied Carbon
          </h1>
          {!isErrorDetected ? (
            <p className="text-base text-[#6C71D1]">
              Calculation completed with no errors
            </p>
          ) : (
            <div className="flex flex-row space-x-10">
              {/* Status message */}
              {isEnabled ? (
                <p className="text-base text-[#6C71D1]">
                  Calculation completed with AI Material Filler
                </p>
              ) : (
                <p className="text-base text-red-600">
                  Calculation completed with errors ignored
                </p>
              )}

              {/* Toggle section */}
              <div className="flex items-center space-x-4">
                {isEnabled ? (
                  <span className="text-[#6C71D1] text-base font-bold">
                    AI Material Filler: On
                  </span>
                ) : (
                  <span className="text-gray-500 text-base font-bold">
                    AI Material Filler: Off
                  </span>
                )}

                <button
                  onClick={toggleHandler}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    isEnabled ? "bg-[#6C71D1]" : "bg-gray-300"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      isEnabled ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>
            </div>
          )}
          <Sankey2
            data={sankeyData}
            width={900}
            height={700}
            totalEc={Number(totalEc)}
            buildingElements={buildingList}
            materials={materialList}
          />
        </div>
      </div>
    </div>
  );
}

export default UploadOverview;
