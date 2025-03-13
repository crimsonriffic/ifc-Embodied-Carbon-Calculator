import { Sankey, Tooltip, Layer, Rectangle } from "recharts";
import { useState } from "react";

const transformDataForSankey = (data) => {
  // Create nodes first

  const nodes = [
    { name: "Total EC" },
    { name: "Substructure" },
    { name: "Superstructure" },
    { name: "Wall" },
    { name: "Slab" },
    { name: "Roof" },
    { name: "Concrete" },
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
      acc[element.element] += element.ec;
      return acc;
    },
    {}
  );

  const superstructureElements = data.ec_breakdown[1].elements.reduce(
    (acc, element) => {
      if (!acc[element.element]) acc[element.element] = 0;
      acc[element.element] += element.ec;
      return acc;
    },
    {}
  );

  // Create links
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

    // Substructure to elements
    {
      source: nodeMap["Substructure"],
      target: nodeMap["Wall"],
      // value: 4050.28, //TODO: i dont want it to be hardcoded
      value: substructureElements["Wall"] || 0,
    },
    {
      source: nodeMap["Substructure"],
      target: nodeMap["Slab"],
      // value: 1291.952, //TODO: i dont want it to be hardcoded
      value: superstructureElements["Wall"] || 0,
    },

    // Superstructure to elements
    {
      source: nodeMap["Superstructure"],
      target: nodeMap["Wall"],
      // value: 4262.4, //TODO: i dont want it to be hardcoded
      value: superstructureElements["Wall"] || 0,
    },
    {
      source: nodeMap["Superstructure"],
      target: nodeMap["Slab"],
      // value: 645.5215, //TODO: i dont want it to be hardcoded
      value: superstructureElements["Slab"] || 0,
    },
    {
      source: nodeMap["Superstructure"],
      target: nodeMap["Roof"],
      // value: 481.5187485187485, //TODO: i dont want it to be hardcoded
      value: superstructureElements["Roof"] || 0,
    },

    // Elements to Concrete
    {
      source: nodeMap["Wall"],
      target: nodeMap["Concrete"],
      // value: 8312.68, //TODO: i dont want it to be hardcoded
      value:
        (substructureElements["Wall"] || 0) +
        (superstructureElements["Wall"] || 0),
    },
    {
      source: nodeMap["Slab"],
      target: nodeMap["Concrete"],
      // value: 1937.4735, //TODO: i dont want it to be hardcoded
      value:
        (substructureElements["Slab"] || 0) +
        (superstructureElements["Slab"] || 0),
    },
    {
      source: nodeMap["Roof"],
      target: nodeMap["Concrete"],
      // value: 481.5187485187485, //TODO: i dont want it to be hardcoded
      value: superstructureElements["Roof"] || 0,
    },
  ];

  return { nodes, links };
};

function CustomNode({ x, y, width, height, index, payload, containerWidth }) {
  const isOut = x + width + 6 > containerWidth;
  const showEC = width > 400;
  console.log("width is ", width, showEC);
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
      {showEC && (
        <text
          textAnchor={isOut ? "end" : "start"}
          x={isOut ? x - 6 : x + width + 6}
          y={y + height / 2 + 13}
          fontSize="12"
          stroke="#333"
          strokeOpacity="0.5"
        >
          {Math.round(payload.value)} kgCO2eq
        </text>
      )}
    </Layer>
  );
}

export default function SankeyChart({ data, width, height }) {
  console.log("SankeyChart received data:", data); // Debugging line
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
        margin={{ top: 20, right: 100, bottom: 20, left: 0 }}
        link={{
          stroke: "url(#gradient)",
          fill: "none",
          opacity: 1,
        }}
        node={<CustomNode width={width} />}
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
