import { getBuildingInfo } from "../api/api.jsx";
import { useEffect, useState } from "react";

export default function AwardCard({ projectId }) {
  return (
    <div className="bg-white shadow-lg rounded-lg border-2 border-gray-800  sm:max-w-xs">
      <h2 className="text-lg font-bold  text-gray-800 px-4 py-2 border-b-2 border-gray-800">
        AWARDS PROGRESS
      </h2>
    </div>
  );
}
