import { Sankey, Tooltip, Layer, Rectangle } from "recharts";
import { useState } from "react";
const simplifyElementName = (ifcName) => {
  // Remove the "Ifc" prefix and return the simplified name
  return ifcName.replace(/^Ifc/, "");
};

const transformDataForSankey = (data, elements = [], materials = []) => {
  // Create nodes
  const nodes = [
    { name: "Total EC" },
    { name: "Substructure" },
    { name: "Superstructure" },
  ];

  // Add element nodes
  elements.forEach((ifcElement) => {
    nodes.push({ name: simplifyElementName(ifcElement) });
  });

  // Add material nodes
  materials.forEach((material) => {
    nodes.push({ name: material });
  });

  // Assign node IDs
  nodes.forEach((node, index) => {
    node.nodeId = index;
  });

  // Create a map for easy node lookup
  const nodeMap = nodes.reduce((acc, node) => {
    acc[node.name] = node.nodeId;
    return acc;
  }, {});

  // Calculate sums for different element types in each category
  const substructureElements =
    data.ec_breakdown?.[0]?.elements.reduce((acc, element) => {
      if (!acc[element.element]) acc[element.element] = 0;
      acc[element.element] += element.ec;
      return acc;
    }, {}) || {};

  const superstructureElements =
    data.ec_breakdown?.[1]?.elements.reduce((acc, element) => {
      if (!acc[element.element]) acc[element.element] = 0;
      acc[element.element] += element.ec;
      return acc;
    }, {}) || {};

  // Create links for total EC to categories
  const categoryLinks = ["Substructure", "Superstructure"].map(
    (category, index) => ({
      source: nodeMap["Total EC"],
      target: nodeMap[category],
      value: data.ec_breakdown?.[index]?.total_ec || 0,
    })
  );

  // Create links for substructure and superstructure to elements and materials
  const elementLinks = [];
  const materialLinks = [];

  ["Substructure", "Superstructure"].forEach((category, index) => {
    const elements = data.ec_breakdown?.[index]?.elements || [];
    elements.forEach((element) => {
      // Links to element nodes
      elementLinks.push({
        source: nodeMap[category],
        target: nodeMap[simplifyElementName(element.element)],
        value: element.ec,
      });

      // Links to material nodes
      element.materials.forEach((material) => {
        materialLinks.push({
          source: nodeMap[simplifyElementName(element.element)],
          target: nodeMap[material.name],
          value: material.ec,
        });
      });
    });
  });

  // Combine all links
  const links = [...categoryLinks, ...elementLinks, ...materialLinks];

  return { nodes, links };
};

function CustomNode({
  x,
  y,
  width,
  height,
  index,
  payload,
  containerWidth,
  totalEc,
}) {
  const isOut = x + width + 6 > containerWidth;
  const percentage = ((payload.value / totalEc) * 100).toFixed(0); // Round percentage

  return (
    <Layer key={`CustomNode${index}`}>
      <Rectangle
        x={x}
        y={y}
        width={width}
        height={height}
        fill="#79E779"
        fillOpacity="1"
        stroke="#79E779"
        strokeWidth={2}
      />
      <text
        textAnchor={isOut ? "end" : "start"}
        x={isOut ? x - 6 : x + width + 6}
        y={y + height / 2}
        fontSize="14"
        stroke="#333"
      >
        {payload.name}
      </text>

      <text
        textAnchor={isOut ? "end" : "start"}
        x={isOut ? x - 6 : x + width + 6}
        y={y + height / 2 + 13}
        fontSize="12"
        stroke="#333"
        strokeOpacity="0.5"
      >
        <tspan x={isOut ? x - 6 : x + width + 6} dy="0">
          {percentage}%
        </tspan>
        <tspan x={isOut ? x - 6 : x + width + 6} dy="16">
          {Math.round(payload.value)} kgCO2eq
        </tspan>
      </text>
    </Layer>
  );
}

export default function SankeyChart({
  data,
  width,
  height,
  totalEc,
  elements,
  materials,
}) {
  const { nodes, links } = transformDataForSankey(data, elements, materials);
  const [activeNode, setActiveNode] = useState(null);
  // Determine dimensions based on size prop

  return (
    <div className="w-full h-full">
      <Sankey
        width={width}
        height={height}
        data={{ nodes, links }}
        nodePadding={50}
        margin={{ top: 20, right: 100, bottom: 50, left: 0 }}
        link={{
          stroke: "url(#gradient)",
          fill: "none",
          opacity: 1,
        }}
        node={<CustomNode width={width} totalEc={totalEc} />}
        onMouseEnter={(node) => setActiveNode(node)}
        onMouseLeave={() => setActiveNode(null)}
      >
        <defs>
          <linearGradient
            id="gradient"
            gradientUnits="userSpaceOnUse"
            x1="0"
            y1="0"
            x2="1"
            y2="0"
          >
            <stop offset="0%" stopColor="#B7D788" stopOpacity={1.0} />
            <stop offset="50%" stopColor="#79E779" stopOpacity={1.0} />
            <stop offset="100%" stopColor="#69F798" stopOpacity={1.0} />
          </linearGradient>
        </defs>
        <Tooltip />
      </Sankey>
    </div>
  );
}
