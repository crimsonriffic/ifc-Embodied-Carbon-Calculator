import { useUser } from "../context/UserContext";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, version } from "react";
import { getBuildingElements } from "../api/api";

import SankeyChart from "../components/SankeyChart";
import Sankey2 from "../components/Sankey2";
import { ArrowDownIcon } from "@heroicons/react/24/solid";
function ExportResults() {
  const [loading, setLoading] = useState(false);
  const location = useLocation();
  const { projectId } = location.state;

  //Test this API later
  const handleExportCsv = async () => {
    setLoading(true);
    const response = await getBuildingElements(projectId);
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
  if (!projectId) {
    return <p className="text-red-500 mt-16">No project ID provided.</p>;
  }

  return (
    <div className="flex flex-col">
      <h1 className="text-2xl font-bold">Upload xx</h1>
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
      </div>
    </div>
  );
}

export default ExportResults;
