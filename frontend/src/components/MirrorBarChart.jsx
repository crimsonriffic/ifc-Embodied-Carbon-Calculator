import React from "react";
import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";

function MirrorBarChart({ data, barKeys, colors, width = 500, height = 300 }) {
  return (
    <div className="justify-center">
      {/* Titles for Upload 5 and Upload 4 */}

      <ResponsiveContainer width={width} height={height}>
        <div className="flex justify-evenly mb-4 px-4 ">
          <span className="font-bold text-base ">{barKeys[1]}</span>
          <span className="font-bold text-base ">{barKeys[0]}</span>
        </div>
        <BarChart
          layout="vertical" // This makes the bars horizontal
          width={width}
          height={height}
          data={data}
          stackOffset="sign"
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" /> {/* X-axis now shows numerical values */}
          <YAxis type="category" dataKey="name" />{" "}
          {/* Y-axis shows categories */}
          <Tooltip />
          <ReferenceLine x={0} stroke="#000" />
          {barKeys.map((key, index) => (
            <Bar key={key} dataKey={key} stackId="stack">
              {data.map((entry, i) => {
                // Get both values and compare using absolute value
                const value1 = Math.abs(entry[barKeys[0]]);
                const value2 = Math.abs(entry[barKeys[1]]);
                // Determine the color dynamically
                const fillColor =
                  (key === barKeys[0] && value1 < value2) ||
                  (key === barKeys[1] && value2 < value1)
                    ? "#FCECEC"
                    : "#5B9130";
                return <Cell key={`cell-${i}`} fill={fillColor} />;
              })}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default MirrorBarChart;
