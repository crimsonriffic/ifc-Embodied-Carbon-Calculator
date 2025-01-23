import { getProjectDetails } from "../api/apiPlaceholder";
import { useEffect, useState } from "react";
export default function BuildingInfoCard() {
  const [buildingInfo, setBuildingInfo] = useState([]);
  useEffect(() => {
    const fetchBuildingInfo = async () => {
      try {
        const data = await getProjectDetails(1);
        console.log(data);
        setBuildingInfo(data);
      } catch (error) {
        console.error("Failed to fetch projects: ", error);
      }
    };
    fetchBuildingInfo();
  }, []);
  return (
    <div className="bg-white shadow-lg rounded-lg p-6 border border-gray-300  sm:max-w-xs">
      <h2 className="text-lg font-bold mb-4 text-gray-800">BUILDING INFO</h2>
      <div className="space-y-3">
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">
            TOTAL EC VALUE:
          </span>
          <span className="text-sm font-semibold text-gray-800">
            {buildingInfo.total_ec}
          </span>
        </div>
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">GFA:</span>
          <span className="text-sm font-semibold text-gray-800">
            {buildingInfo.gfa}
          </span>
        </div>
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">TYPOLOGY:</span>
          <span className="text-sm font-semibold text-gray-800">
            {buildingInfo.typology}
          </span>
        </div>
        <div className="flex justify-between border-b pb-2">
          <span className="text-sm font-medium text-gray-600">PHASE:</span>
          <span className="text-sm font-semibold text-gray-800">
            {buildingInfo.phase}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm font-medium text-gray-600">COST:</span>
          <span className="text-sm font-semibold text-gray-800">
            {buildingInfo.cost}
          </span>
        </div>
      </div>
    </div>
  );
}
