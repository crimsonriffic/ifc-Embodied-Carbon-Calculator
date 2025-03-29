import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import MirrorBarChart from "../components/MirrorBarChart";
function UploadComparison() {
  const sampleData = [
    { name: "Concrete", Upload4: -3400, Upload1: 2400 },
    { name: "Steel", Upload4: -3000, Upload1: 1398 },
    { name: "Page C", Upload4: -2000, Upload1: 2800 },
    { name: "Page D", Upload4: -2780, Upload1: 3908 },
  ];

  const barKeys = ["Upload1", "Upload4"];
  const colors = ["#8884d8", "#82ca9d"];

  return (
    <div style={{ width: "100%", height: "400px" }}>
      <MirrorBarChart data={sampleData} barKeys={barKeys} colors={colors} />
    </div>
  );
}

export default UploadComparison;
