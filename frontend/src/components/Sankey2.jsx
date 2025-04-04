import { Sankey, Tooltip, Layer, Rectangle } from "recharts";
import { useState } from "react";

const transformDataForSankey = (data, totalEc) => {
  //Unique elements
  const allElements = new Set();
  data.ec_breakdown.forEach((category) => {
    category.elements.forEach((element) => {
      allElements.add(element.element); // Add the element name to the Set
    });
  });
  const uniqueElements = Array.from(allElements); // Convert Set to Array

  //Uniqe materials
  const allMaterials = new Set();
  data.ec_breakdown.forEach((category) => {
    category.elements.forEach((element) => {
      element.materials.forEach((material) => {
        allMaterials.add(material.material); // Add material name to the Set
      });
    });
  });
  const uniqueMaterials = Array.from(allMaterials); // Convert Set to Array

  // Create nodes first
  const nodes = [
    { name: "Total EC" },
    ...data.ec_breakdown.map((category) => ({ name: category.category })),
    ...uniqueElements.map((element) => ({ name: element })), // Add elements
    ...uniqueMaterials.map((material) => ({ name: material })), // Add materials
    { name: "Others" },
  ].map((node, index) => ({
    ...node,
    nodeId: index, // Assign a unique node ID
  }));

  // const nodes = [
  //   { name: "Total EC" },
  //   { name: "Substructure" },
  //   { name: "Superstructure" },
  //   { name: "Wall" },
  //   { name: "Slab" },
  //   { name: "Roof" },
  //   { name: "Concrete" },
  // ].map((node, index) => ({
  //   ...node,
  //   nodeId: index,
  // }));

  // Create a map for easy node lookup
  const nodeMap = nodes.reduce((acc, node, index) => {
    acc[node.name] = index;
    return acc;
  }, {});

  // Create links
  const links = [];

  // Total EC to categories
  data.ec_breakdown.forEach((category) => {
    links.push({
      source: nodeMap["Total EC"],
      target: nodeMap[category.category],
      value: category.total_ec,
    });

    // Categories to elements
    category.elements.forEach((element) => {
      links.push({
        source: nodeMap[category.category],
        target: nodeMap[element.element],
        value: element.ec,
      });

      // Elements to materials
      element.materials.forEach((material) => {
        links.push({
          source: nodeMap[element.element],
          target: nodeMap[material.material],
          value: material.ec,
        });
      });
    });
  });

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
