import { useState, useEffect } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { useUser } from "../context/UserContext";
import MirrorBarChart from "../components/MirrorBarChart";
import { getProjectHistory, getProjectBreakdown } from "../api/api";

function UploadComparison() {
  const [projectHistory, setProjectHistory] = useState([]);
  const [firstVersionNumber, setFirstVersionNumber] = useState("");
  const [secondVersionNumber, setSecondVersionNumber] = useState(null);
  const [firstVersionData, setFirstVersionData] = useState({});
  const [secondVersionData, setSecondVersionData] = useState({});
  const [firstSummary, setFirstSummary] = useState(null);
  const [secondSummary, setSecondSummary] = useState(null);
  const [versionArray, setVersionArray] = useState([]);
  const [systemData, setSystemData] = useState(null);
  const [materialData, setMaterialData] = useState(null);
  const [elementData, setElementData] = useState(null);
  const [barKeys, setBarKeys] = useState(null);
  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { projectId } = location.state;
  const { projectName } = useParams();

  // const sampleData = [
  //   { name: "Concrete", Upload4: -3400, Upload5: 2400 },
  //   { name: "Steel", Upload4: -3000, Upload5: 1398 },
  //   { name: "Wood", Upload4: -2000, Upload5: 2800 },
  //   { name: "Window", Upload4: -2780, Upload5: 3908 },
  // ];
  // const sampleData = [
  //   { name: "Substructure", Upload9: -266610.32, Upload8: 403693.3424 },
  //   { name: "Superstructure", Upload9: -252272.2341, Upload8: 93314.412 },
  // ];
  // const barKeys = ["Upload5", "Upload4"];
  const colors = ["#8884d8", "#82ca9d"];
  const transformData = (
    firstSummary,
    secondSummary,
    firstVersionNumber,
    secondVersionNumber
  ) => {
    // Extract the `by_building_system` objects from both summaries
    const firstBuildingSystem = firstSummary.by_building_system;
    const secondBuildingSystem = secondSummary.by_building_system;

    // Map the building system keys to the desired format
    const sampleData = [
      {
        name: "Substructure",
        [`Upload${firstVersionNumber}`]: -Number(
          firstBuildingSystem.substructure_ec
        ),
        [`Upload${secondVersionNumber}`]: Number(
          secondBuildingSystem.substructure_ec
        ),
      },
      {
        name: "Superstructure",
        [`Upload${firstVersionNumber}`]: -Number(
          firstBuildingSystem.superstructure_ec
        ),
        [`Upload${secondVersionNumber}`]: Number(
          secondBuildingSystem.superstructure_ec
        ),
      },
    ];

    //TODO: make sample data for materials , and another one for elements. i want the name to be dynamic
    // Extract `by_material` objects
    const firstMaterial = firstSummary.by_material;
    const secondMaterial = secondSummary.by_material;

    // Map the material keys dynamically
    const transformedMaterial = Object.keys(firstMaterial).map((key) => ({
      name: key.replace(/_/g, " "), // Replace underscores with spaces
      [`Upload${firstVersionNumber}`]: -Number(firstMaterial[key]),
      [`Upload${secondVersionNumber}`]: Number(secondMaterial[key]),
    }));

    // Extract `by_element` objects
    const firstElement = firstSummary.by_element;
    const secondElement = secondSummary.by_element;

    // Map the element keys dynamically
    const transformedElement = Object.keys(firstElement).map((key) => ({
      name: key.replace(/_/g, " "), // Replace underscores with spaces
      [`Upload${firstVersionNumber}`]: -Number(firstElement[key]),
      [`Upload${secondVersionNumber}`]: Number(secondElement[key]),
    }));

    return { sampleData, transformedMaterial, transformedElement };
  };

  /* Initial API calls to fetch project history and breakdown data */
  useEffect(() => {
    const fetchData = async () => {
      try {
        const historyResponse = await getProjectHistory(projectId);

        // Get the latest version from history
        const latestVersion = historyResponse.data.history[0]?.version || "";

        setProjectHistory(historyResponse.data.history);
        console.log("Project History set as: ", historyResponse.data.history);

        if (!firstVersionNumber && latestVersion) {
          setFirstVersionNumber(latestVersion);
        }
        if (!secondVersionNumber && latestVersion) {
          setSecondVersionNumber(latestVersion - 1);
        }

        setError(null);
        setLoading(false);
      } catch (err) {
        console.error("Failed to data: ", err);
        setError("Failed to fetch history data."); // Set error message
      }
    };
    if (projectId) {
      fetchData();
    }
  }, [projectId]);
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
      ? sortedHistory.reverse().map((item) => item.version)
      : [];
    setVersionArray(versionArr);

    const firstData = projectHistory.find(
      (item) => item.version === firstVersionNumber
    );
    console.log("Setting firstVersionData:", firstData);

    setFirstVersionData(firstData || {});
    console.log("Second version number is:", secondVersionNumber);
    const secondData = projectHistory.find(
      (item) => item.version === secondVersionNumber
    );
    console.log("Setting secondVersionData:", secondData, secondVersionNumber);

    setSecondVersionData(secondData || {});
    setBarKeys([secondVersionNumber, firstVersionNumber]);
  }, [projectHistory, firstVersionNumber, secondVersionNumber]);

  // Fetch breakdown data when version numbers change
  useEffect(() => {
    const fetchBreakdownData = async () => {
      try {
        if (firstVersionNumber) {
          const response = await getProjectBreakdown(
            projectId,
            firstVersionNumber
          );
          console.log("First version breakdown:", response.data.summary);
          setFirstSummary(response.data.summary);
        }

        if (secondVersionNumber) {
          const response = await getProjectBreakdown(
            projectId,
            secondVersionNumber
          );
          console.log("Second version breakdown:", response.data.summary);
          setSecondSummary(response.data.summary);
        }

        setError(null);
      } catch (err) {
        console.error("Error fetching breakdown data:", err);
        setError("Failed to fetch breakdown data.");
      }
    };

    if (firstVersionNumber || secondVersionNumber) {
      fetchBreakdownData();
    }
  }, [projectId, firstVersionNumber, secondVersionNumber]);

  // Transform data once both breakdowns are available
  useEffect(() => {
    if (firstSummary && secondSummary) {
      const { sampleData, transformedMaterial, transformedElement } =
        transformData(
          firstSummary,
          secondSummary,
          firstVersionNumber,
          secondVersionNumber
        );
      console.log(
        "Transformed Data is: ",
        sampleData,
        transformedMaterial,
        transformedElement
      );
      setSystemData(sampleData);
      // TODO setMaterialData and setElementsData
      setMaterialData(transformedMaterial); // New: setMaterialData
      setElementData(transformedElement); // New: setElementsData

      if (firstVersionNumber && secondVersionNumber) {
        setBarKeys([
          `Upload${secondVersionNumber}`,
          `Upload${firstVersionNumber}`,
        ]);
      }
    }
    console.log("Bar keys are", barKeys);
  }, [firstSummary, secondSummary, firstVersionNumber, secondVersionNumber]);
  if (loading) {
    return <p>Loading...</p>;
  }

  if (error) {
    return <p className="text-red-500">{error}</p>;
  }
  return (
    <div>
      <div className="flex flex-row">
        {/*Dropdown of first version number*/}
        <div className="flex flex-col ">
          <div className="mb-4">
            <select
              id="firstVersionNumber"
              value={firstVersionNumber}
              onChange={(e) => {
                setFirstVersionNumber(e.target.value);
              }}
              className="text-2xl font-bold"
            >
              {[...versionArray].map((version) => (
                <option key={version} value={version} className="text-lg ">
                  Upload {version}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-gray-700">Total Embodied Carbon</span>
            <span className="font-bold text-black">
              {Number(firstVersionData.total_ec).toLocaleString()} kgCO2eq
            </span>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-gray-700">
              Embodied Carbon per Floor Area
            </span>
            <span className="font-bold text-black">
              {(
                Number(firstVersionData.total_ec) / Number(firstVersionData.gfa)
              ).toFixed(0)}{" "}
              kgCO2eq/m2
            </span>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-gray-700">Computed Floor Area</span>
            <span className="font-bold text-black">
              {Number(firstVersionData.gfa).toFixed(0)} m2
            </span>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-gray-700">Status</span>
            <span className="font-bold text-black">
              {firstVersionData.status}
            </span>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-gray-700">Comments</span>
            <span className="font-bold text-black">
              {firstVersionData.comments}
            </span>
          </div>
        </div>
        {/*Dropdown of second version number*/}
        <div className="flex flex-col p-4 max-w-md mx-auto">
          <div className="mb-4">
            <select
              id="secondVersionNumber"
              value={secondVersionNumber}
              onChange={(e) => {
                setSecondVersionNumber(e.target.value);
              }}
              className="text-2xl font-bold"
            >
              {[...versionArray].map((version) => (
                <option key={version} value={version} className="text-lg ">
                  Upload {version}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-gray-700">Total Embodied Carbon</span>
            <span className="font-bold text-black">
              {Number(secondVersionData.total_ec).toLocaleString()} kgCO2eq
            </span>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-gray-700">
              Embodied Carbon per Floor Area
            </span>
            <span className="font-bold text-black">
              {(
                Number(secondVersionData.total_ec) /
                Number(secondVersionData.gfa)
              ).toFixed(0)}{" "}
              kgCO2eq/m2
            </span>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-gray-700">Computed Floor Area</span>
            <span className="font-bold text-black">
              {Number(secondVersionData.gfa).toFixed(0)} m2
            </span>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-gray-700">Status</span>
            <span className="font-bold text-black">
              {secondVersionData.status}
            </span>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-gray-700">Comments</span>
            <span className="font-bold text-black">
              {secondVersionData.comments}
            </span>
          </div>
        </div>
      </div>

      <div className="w-full space-y-10">
        <div>
          <h1 className="text-2xl font-bold"> System Hotspot Comparison </h1>
          {systemData && (
            <MirrorBarChart
              data={systemData}
              barKeys={barKeys}
              colors={colors}
            />
          )}
        </div>
        <div>
          <h1 className="text-2xl font-bold"> Material Hotspot Comparison </h1>
          {materialData && (
            <MirrorBarChart
              data={materialData}
              barKeys={barKeys}
              colors={colors}
            />
          )}
        </div>
        <div>
          <h1 className="text-2xl font-bold"> Elements Hotspot Comparison </h1>
          {elementData && (
            <MirrorBarChart
              data={elementData}
              barKeys={barKeys}
              colors={colors}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default UploadComparison;
