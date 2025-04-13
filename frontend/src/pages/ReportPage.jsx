import { useRef } from "react";
import html2pdf from "html2pdf.js";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import { useLocation, useSearchParams } from "react-router-dom";
import { useEffect, useState, version } from "react";
import {
  getProjectBreakdown,
  getMissingMaterials,
  getProjectInfo,
} from "../api/api";
import BarChart from "../components/BarChart";

import Sankey2 from "../components/Sankey2";
import { ArrowDownIcon } from "@heroicons/react/24/solid";
function ReportPage() {
  const [isInIframe, setIsInIframe] = useState(false);
  const [isReadyToDownload, setIsReadyToDownload] = useState(false);

  const [loading, setLoading] = useState(true); // Loading state
  const [error, setError] = useState(null);
  const [sankeyData, setSankeyData] = useState([]);
  const [currentVersionData, setCurrentVersionData] = useState({});
  const [totalEc, setTotalEc] = useState("");
  const [summaryData, setSummaryData] = useState(null);
  const [versionArray, setVersionArray] = useState([]);
  const [isEnabled, setIsEnabled] = useState(false);
  const [buildingList, setBuildingList] = useState([]);
  const [materialList, setMaterialList] = useState([]);
  const [isErrorDetected, setIsErrorDetected] = useState(false);
  const [barData, setBarData] = useState({
    labels: [],
    datasets: [],
  });
  const [projectInfo, setProjectInfo] = useState({});
  const [benchmarkStandard, setBenchmarkstandard] = useState("");
  const [benchmarkTarget, setBenchmarkTarget] = useState(0);
  const [materialBar, setMaterialBar] = useState({
    labels: [],
    datasets: [],
  });
  const [elementBar, setElementBar] = useState({
    labels: [],
    datasets: [],
  });
  const [buildingSystemBar, setBuildingSystemBar] = useState({
    labels: [],
    datasets: [],
  });
  const [isChartReady, setIsChartReady] = useState(false);

  const [projectId, setProjectId] = useState(null);
  const [projectName, setProjectName] = useState("");
  const [versionNumber, setVersionNumber] = useState("");
  const [projectHistory, setProjectHistory] = useState(null);
  const reportRef = useRef();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  const [generatedAt, setGeneratedAt] = useState("");
  const handleDownload = async () => {
    console.log("Downloading report...");
    const element = reportRef.current;
    const opt = {
      margin: 0,
      filename: "page.pdf",
      image: { type: "jpeg", quality: 1 },
      html2canvas: { scale: 3 }, // increase for better quality (e.g., 2–4)
      jsPDF: { unit: "in", format: "letter", orientation: "portrait" },
    };

    html2pdf().set(opt).from(element).save();
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
      const projectResponse = await getProjectInfo(projectId);
      console.log("Project Info response data is: ", projectResponse.data);
      console.log("Benchmarks are", projectResponse.data.benchmark);
      setProjectInfo(projectResponse.data);
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

      setError(null);
      setLoading(false);
      console.log("Loading state set to false");
    } catch (err) {
      console.error("Failed to data: ", err);
      setError("Failed to fetch data."); // Set error message
    }
  };
  useEffect(() => {
    const data = localStorage.getItem("reportData");
    if (data) {
      const parsed = JSON.parse(data);
      setProjectId(parsed.projectId);
      setProjectName(parsed.projectName);
      setVersionNumber(parsed.versionNumber);
      setProjectHistory(parsed.projectHistory);
    }
  }, []);
  useEffect(() => {
    setIsInIframe(window.self !== window.top);
  }, []);
  useEffect(() => {
    if (!loading && isInIframe) {
      setIsReadyToDownload(true);
    }
  }, [loading, isInIframe]);

  useEffect(() => {
    if (isReadyToDownload && isChartReady) {
      setTimeout(() => {
        handleDownload(); // Trigger the download with a slight delay
      }, 500); // 500ms delay (adjust as needed)
    }
  }, [isReadyToDownload, isChartReady]);
  useEffect(() => {
    const now = new Date();
    const formatted = now.toLocaleString("en-GB", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    setGeneratedAt(formatted);
  }, []);
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
          "Number of errors",
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
    const generateBarData = (projectHistory, label) => {
      if (!projectHistory) return null;
      const labels = projectHistory.map((entry) => `Upload ${entry.version}`);
      const data = projectHistory.map(
        (entry) => Number(entry.total_ec) / Number(entry.gfa)
      );

      return {
        labels: labels,
        datasets: [
          {
            label: `A1-A3 Carbon (${label})`,
            data: data,
            backgroundColor: ["#673091", "#305791", "#308791", "#5B9130"],
            borderColor: "#000000",
            borderWidth: 0,
            barThickness: 40,
          },
        ],
      };
    };

    if (projectId) {
      fetchData();
      fetchErrorData();
      setBarData(generateBarData(projectHistory, "Comparison"));
    }
  }, [projectId]);
  useEffect(() => {
    // Helper function to generate bar chart data
    const generateBarData = (values, label) => {
      if (!values) return null; // Handle undefined values safely
      const labels = Object.keys(values).map(
        (key) => key.charAt(0).toUpperCase() + key.slice(1)
      );
      const data = Object.values(values);

      console.log(`${label} labels and data: `, labels, data);
      return {
        labels: labels,
        datasets: [
          {
            label: `A1-A3 Carbon Comparison (${label})`,
            data: data,
            backgroundColor: "#B7D788",
            borderColor: "#000000",
            borderWidth: 0,
            barThickness: 40,
          },
        ],
      };
    };

    console.log("Full SummaryData: ", summaryData);
    if (
      !summaryData ||
      !summaryData["by_material"] ||
      !summaryData["by_element"] ||
      !summaryData["by_building_system"]
    ) {
      console.log("SummaryData is not ready yet");
      return;
    }
    console.log("SummaryData is: ", summaryData);
    const materialValues = summaryData["by_material"];
    const elementValues = summaryData["by_element"];
    const systemValues = summaryData["by_building_system"];
    console.log(
      "Const values are",
      materialValues,
      elementValues,
      systemValues
    );

    // Set state for all three bar charts
    setMaterialBar(generateBarData(materialValues, "Material"));
    setElementBar(generateBarData(elementValues, "Element"));
    setBuildingSystemBar(generateBarData(systemValues, "Building System"));
    setIsChartReady(true);
  }, [summaryData]);
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
  useEffect(() => {
    if (
      projectInfo.benchmark &&
      Object.keys(projectInfo.benchmark).length > 0
    ) {
      const firstBenchmark = Object.keys(projectInfo.benchmark)[0]; // Get first key
      console.log(
        "Benchmark standard: ",
        firstBenchmark,
        "Benchmark Target: ",
        projectInfo.benchmark[firstBenchmark]
      );
      setBenchmarkstandard(firstBenchmark);
      setBenchmarkTarget(projectInfo.benchmark[firstBenchmark]); // Set initial target value
    }
  }, [projectInfo.benchmark]);
  return (
    <div
      ref={reportRef}
      className="bg-white text-black mx-auto p-8"
      style={{
        width: "794px",
        height: "auto", // Or 'auto' if your content varies
        boxSizing: "border-box",
      }}
    >
      <div className="flex flex-col">
        <img src="/reportLogo.png" alt="CarbonSmart Logo" className="w-1/2" />

        {/* Banner Section */}
        <div className="bg-[#5B9130] text-white mx-8 mt-2 w-full mr-4 py-2 px-4 rounded-lg shadow-md text-left ml-0">
          <div className="flex flex-row gap-x-2">
            <h1 className="text-2xl font-bold">Embodied Carbon Report</h1>
          </div>
          {/**add a button here with the arrowdownicon */}
          <p className="text-sm">Generated on {generatedAt}</p>
        </div>
        <div className="flex flex-row mt-2 gap-x-12">
          {/**Project Info left side */}
          <div className="flex flex-col gap-y-4">
            <div>
              <h1 className="text-base font-bold"> {projectName} </h1>
            </div>
            <div>
              <h1 className="text-xs">Client Name</h1>
              <p className=" text-base font-bold ">{projectInfo.client_name}</p>
            </div>
            <div>
              <h1 className="text-xs">Typology</h1>
              <p className=" text-base font-bold ">{projectInfo.typology}</p>
            </div>
          </div>

          {/**Right side upload info */}
          <div className="flex flex-col ">
            <div>
              <h1 className="text-base font-bold"> Upload {versionNumber} </h1>
            </div>
            <div className="flex flex-row space-x-12">
              <div className="flex flex-col gap-y-4">
                <div>
                  <h1 className="text-xs">Total A1-A3 Embodied Carbon</h1>
                  <p className=" text-base font-bold ">
                    {Number(totalEc).toLocaleString()} kgCO2eq
                  </p>
                </div>

                <div>
                  <h1 className="text-xs">
                    A1-A3 Embodied Carbon per floor area
                  </h1>
                  <p className=" text-base font-bold">
                    {" "}
                    {(Number(totalEc) / Number(currentVersionData.gfa)).toFixed(
                      0
                    )}{" "}
                    kgCO2eq/m2
                  </p>
                </div>
                <div>
                  <h1 className="text-xs">Computed Floor Area</h1>
                  <p className=" text-base font-bold ">
                    {Number(currentVersionData.gfa).toFixed(0)} m2
                  </p>
                </div>
              </div>
              <div className="flex flex-col gap-y-4">
                <div>
                  <h1 className="text-xs">Status</h1>
                  <p className=" text-base font-bold">
                    {currentVersionData.status}
                  </p>
                </div>
                <div>
                  <h1 className="text-xs">Uploaded by</h1>
                  <p className=" text-base font-bold">
                    {" "}
                    {currentVersionData.uploaded_by}
                  </p>
                </div>
                <div>
                  <h1 className="text-xs">Comments</h1>
                  <p className=" text-base font-bold">
                    {currentVersionData.comments}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        {/** Card 2 - Sankey chart  */}
        <div className="flex flex-col mt-12">
          <h1 className="text-base font-bold text-[#5B9130]">
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
            </div>
          )}
          {loading ? (
            <p className="text-gray-500 mt-4">Loading Sankey chart...</p>
          ) : (
            <Sankey2
              data={sankeyData}
              width={700}
              height={600}
              totalEc={Number(totalEc)}
              buildingElements={buildingList}
              materials={materialList}
            />
          )}
        </div>
        {/** Card 3 - Project Progress  */}
        <div className="flex flex-col justify-center mt-12">
          <div>
            <h1 className="text-base font-bold text-[#5B9130]">
              Project Progress
            </h1>
          </div>
          <div className="flex flex-row gap-x-4">
            <div className="w-[500px] h-[300px] mt-4">
              <BarChart data={barData} benchmark={benchmarkTarget} />
            </div>
            <div className="flex flex-col mt-20">
              <h1 className="text-xs">Benchmark Standard</h1>
              <p className="text-base font-bold">{benchmarkStandard}</p>
              <h1 className="text-xs mt-4">Benchmark Target</h1>
              <p className="text-base font-bold">{benchmarkTarget} kgCO2/m2</p>
            </div>
          </div>
        </div>
        {/** Card 4 - Hotspot analysis  */}
        <div className="flex flex-col justify-center mt-12 gap-y-4">
          <div>
            <h1 className="text-base font-bold text-[#5B9130]">
              Hotspot Analysis
            </h1>
          </div>
          {/* Building System */}
          <div className="flex-1 px-4">
            <p className="mb-4 ">
              Hotspot by: <span className="font-bold">Building System</span>
            </p>
            <div className="h-[300px]">
              <BarChart data={buildingSystemBar} />
            </div>
          </div>
          <div style={{ pageBreakAfter: "always" }}></div>

          {/*Building Material */}
          <div className="flex-1 px-4">
            <p className="mb-4">
              Hotspot by: <span className="font-bold">Building Material</span>
            </p>
            <div className="h-[300px]">
              <BarChart data={materialBar} />
            </div>
          </div>
          {/*  Building Element */}
          <div className="flex-1 px-4">
            <p className="mb-4">
              Hotspot by: <span className="font-bold">Building Element</span>
            </p>
            <div className="h-[300px]">
              <BarChart data={elementBar} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReportPage;
