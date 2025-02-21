import { getBuildingInfo } from "../api/api.jsx";
import { useEffect, useState } from "react";

export default function AwardCard({ projectId }) {
  return (
    <div className="bg-white shadow-lg rounded-lg border-2 border-gray-800  sm:max-w-md">
      <h2 className="text-lg font-bold  text-gray-800 px-4 py-2 border-b-2 border-gray-800">
        AWARDS PROGRESS
      </h2>
      <div className="px-4 py-2">
        <p className="font-semibold">BCA GREENMARK:</p>
        <p>
          One point for achieving 10% reduction <br /> from referenced embodied
          carbon value
        </p>
        <p className="font-semibold">TO IMPROVE:</p>
        <p>XXX KG C02/M2 AWAY FROM ACHIEVING 30% REDUCTION (2 POINTS)</p>
      </div>
    </div>
  );
}
