import { Sankey, Tooltip, Layer, Rectangle } from "recharts";
import { useState } from "react";

const transformDataForSankey = (data) => {
  // Define all building elements (singular form to match data)
  const buildingElements = [
    "Column",
    "Beam",
    "Slab",
    "Wall",
    "Window",
    "Door",
    "Roof",
    "Stair",
    "Railing",
    "Pile",
    "Footing",
  ];

  const materials = ["Concrete", "Steel"];

  // Create nodes array
  const nodes = [
    { name: "Total EC" },
    { name: "Substructure" },
    { name: "Superstructure" },
    ...buildingElements.map((element) => ({ name: element })),
    ...materials.map((material) => ({ name: material })),
  ].map((node, index) => ({
    ...node,
    nodeId: index,
  }));

  // Create a map for easy node lookup
  const nodeMap = nodes.reduce((acc, node, index) => {
    acc[node.name] = index;
    return acc;
  }, {});

  // Calculate sums for different element types in each category
  const substructureElements = data.ec_breakdown[0].elements.reduce(
    (acc, element) => {
      if (!acc[element.element]) acc[element.element] = 0;
      acc[element.element] += parseFloat(element.ec);
      return acc;
    },
    {}
  );

  const superstructureElements = data.ec_breakdown[1].elements.reduce(
    (acc, element) => {
      if (!acc[element.element]) acc[element.element] = 0;
      acc[element.element] += parseFloat(element.ec);
      return acc;
    },
    {}
  );

  // Create links array
  const links = [
    // Total EC to categories
    {
      source: nodeMap["Total EC"],
      target: nodeMap["Substructure"],
      value: data.ec_breakdown[0].total_ec,
    },
    {
      source: nodeMap["Total EC"],
      target: nodeMap["Superstructure"],
      value: data.ec_breakdown[1].total_ec,
    },
  ];

  // Add links from Substructure to elements
  for (const element of buildingElements) {
    if (substructureElements[element]) {
      links.push({
        source: nodeMap["Substructure"],
        target: nodeMap[element],
        value: substructureElements[element],
      });
    }
  }

  // Add links from Superstructure to elements
  for (const element of buildingElements) {
    if (superstructureElements[element]) {
      links.push({
        source: nodeMap["Superstructure"],
        target: nodeMap[element],
        value: superstructureElements[element],
      });
    }
  }

  // Add links from elements to materials
  for (const element of buildingElements) {
    const elementTotal =
      (substructureElements[element] || 0) +
      (superstructureElements[element] || 0);

    if (elementTotal > 0) {
      // Assuming a 60-40 split between Concrete and Steel for demonstration
      // You should replace these with actual proportions from your data
      links.push({
        source: nodeMap[element],
        target: nodeMap["Concrete"],
        value: elementTotal * 0.6, // 60% to Concrete
      });
      links.push({
        source: nodeMap[element],
        target: nodeMap["Steel"],
        value: elementTotal * 0.4, // 40% to Steel
      });
    }
  }

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

export default function Sankey2({ data, width, height, totalEc }) {
  const { nodes, links } = transformDataForSankey(data);
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
