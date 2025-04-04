import { useState, useEffect } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { useUser } from "../context/UserContext";
import MirrorBarChart from "../components/MirrorBarChart";
import { getProjectHistory } from "../api/api";

function UploadComparison() {
  const [projectHistory, setProjectHistory] = useState([]);
  const [firstVersionNumber, setFirstVersionNumber] = useState("");
  const [secondVersionNumber, setSecondVersionNumber] = useState(null);
  const [firstVersionData, setFirstVersionData] = useState({});
  const [secondVersionData, setSecondVersionData] = useState({});

  const [versionArray, setVersionArray] = useState([]);

  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { projectId } = location.state;
  const { projectName } = useParams();

  const sampleData = [
    { name: "Concrete", Upload4: -3400, Upload1: 2400 },
    { name: "Steel", Upload4: -3000, Upload1: 1398 },
    { name: "Page C", Upload4: -2000, Upload1: 2800 },
    { name: "Page D", Upload4: -2780, Upload1: 3908 },
  ];

  const barKeys = ["Upload1", "Upload4"];
  const colors = ["#8884d8", "#82ca9d"];

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
  }, [projectHistory, firstVersionNumber, secondVersionNumber]);

  return (
    <div>
      {/*Dropdown of first version number*/}
      <div className="flex flex-col p-4 max-w-md mx-auto">
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
          <span className="text-gray-700">Embodied Carbon per Floor Area</span>
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
          <span className="text-gray-700">Embodied Carbon per Floor Area</span>
          <span className="font-bold text-black">
            {(
              Number(secondVersionData.total_ec) / Number(secondVersionData.gfa)
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
      <div style={{ width: "100%", height: "400px" }}>
        <MirrorBarChart data={sampleData} barKeys={barKeys} colors={colors} />
      </div>
    </div>
  );
}

export default UploadComparison;
