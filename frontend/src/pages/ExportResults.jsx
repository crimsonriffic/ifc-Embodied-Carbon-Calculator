import { useUser } from "../context/UserContext";

import {
  Link,
  useParams,
  useLocation,
  useNavigate,
  NavLink,
} from "react-router-dom";
import { useEffect, useState, version } from "react";
import { getBuildingElements } from "../api/api";

import SankeyChart from "../components/SankeyChart";
import Sankey2 from "../components/Sankey2";
import { ArrowRightIcon, ArrowDownIcon } from "@heroicons/react/24/solid";
function ExportResults({ projectId, projectName, projectHistory }) {
  const [versionNumber, setVersionNumber] = useState(null);
  const [versionArray, setVersionArray] = useState([]);
  const [loading, setLoading] = useState(false);
  const location = useLocation();
  const handleVersionClick = (e) => {
    console.log("Handle version is clicked");
    setVersionNumber(e.target.value);
  };
  const handleExportCsv = async () => {
    setLoading(true);
    const response = await getBuildingElements(projectId, versionNumber);
    console.log("Except response is: ", response);
    // Create a Blob from the response data
    const blob = new Blob([response.data], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    // Create a download link for the Blob
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;

    // Set the desired filename
    a.download = `building_elements.xlsx`;
    document.body.appendChild(a);
    a.click();

    // Cleanup the DOM and revoke the Object URL
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    setLoading(false);
  };
  // const handleExportReport = () => {
  //   const iframe = document.getElementById("reportFrame");
  //   if (iframe && iframe.contentWindow) {
  //     iframe.onload = () => {
  //       iframe.contentWindow.focus();
  //       iframe.contentWindow.print(); // or trigger html2pdf inside the iframe
  //     };
  //   }
  // };
  const handleExportReport = () => {
    // Save data to localStorage
    localStorage.setItem(
      "reportData",
      JSON.stringify({ projectId, projectName, versionNumber, projectHistory })
    );

    // Open /report in iframe
    const iframe = document.getElementById("reportFrame");
    if (iframe) {
      iframe.src = "/report"; // Reload to trigger useEffect
      iframe.style.display = "block";
    }
  };
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
    // Set initial versionNumber to the latest (i.e., highest)
    if (versionNumber === null && versionArr.length > 0) {
      setVersionNumber(versionArr[versionArr.length - 1]);
    }
  }, [projectHistory, versionNumber]);
  if (!projectId) {
    return <p className="text-red-500 mt-16">No project ID provided.</p>;
  }

  return (
    <div className="flex flex-col">
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
      <div className="border border-gray-300 rounded-md shadow max-w-lg p-4 mt-4">
        <button
          onClick={() => handleExportCsv()}
          className="flex items-center gap-x-2 px-2 py-2 w-fit bg-[#5B9130] text-white rounded-md font-semibold"
        >
          <ArrowDownIcon className="w-6 h-6 text-white" /> Export Breakdown
          (CSV)
        </button>
        <h1 className="text-2xl font-bold text-[#5B9130] mt-2 mb-2">
          Embodied Carbon Breakdown
        </h1>
        <p className="text-sm">
          A detailed breakdown with quantities and calculation per element is
          provided.
        </p>
      </div>
      <div className="border border-gray-300 rounded-md shadow max-w-lg p-4 mt-4">
        <button
          onClick={() => handleExportReport()}
          className="flex items-center gap-x-2 px-2 py-2 w-fit bg-[#5B9130] text-white rounded-md font-semibold"
        >
          <ArrowDownIcon className="w-6 h-6 text-white" /> Export Breakdown
          (PDF)
        </button>
        <h1 className="text-2xl font-bold text-[#5B9130] mt-2 mb-2">
          Embodied Carbon Report
        </h1>
        <p className="text-sm">
          A summarised report with key charts, insights, and analysis is
          provided.
        </p>
        <NavLink
          to="/report"
          state={{
            projectId,
            projectName,
            projectHistory,
            versionNumber,
          }}
          className="flex flex-row "
        >
          Preview Report <ArrowRightIcon className="w-6 h-6" />
        </NavLink>
      </div>
      {/* <iframe
        id="reportFrame"
        src={`/report?projectId=${projectId}&projectName=${encodeURIComponent(
          projectName
        )}&versionNumber=${versionNumber}`}
        style={{ display: "none" }}
        title="Report"
      /> */}
      <iframe
        id="reportFrame"
        src=""
        style={{ display: "none", width: "0px", height: "0px" }}
        title="Report"
      />
    </div>
  );
}

export default ExportResults;
