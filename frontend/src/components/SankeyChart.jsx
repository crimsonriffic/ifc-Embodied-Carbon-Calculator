import { Sankey, Tooltip, Layer, Rectangle } from "recharts";
import { useState } from "react";
//Helper function
const transformDataForSankey = (data) => {
  console.log("Input data: ", data);

  // First create all unique nodes
  const uniqueNodes = new Set();
  uniqueNodes.add("Total EC");

  // Add category nodes and links from total
  data.ec_breakdown.forEach((category) => {
    uniqueNodes.add(category.category);
    category.elements.forEach((element) => {
      uniqueNodes.add(element.element);
      element.materials.forEach((material) => {
        uniqueNodes.add(material.material);
      });
    });
  });
  console.log("Unique Nodes are: ", uniqueNodes);
  // Convert Set to arrray of node objects with index
  const nodes = Array.from(uniqueNodes).map((name, index) => ({
    name,
    nodeId: index,
  }));

  console.log("Nodes in array notation are: ", nodes);
  // Create a map of name to index for creating links
  const nodeMap = {};
  nodes.forEach((node, index) => {
    nodeMap[node.name] = index;
  });

  // Create links using node indices
  const links = [];
  data.ec_breakdown.forEach((category) => {
    links.push({
      source: nodeMap["Total EC"],
      target: nodeMap[category.category],
      value: category.total_ec,
    });

    // Links from categories to elements
    category.elements.forEach((element) => {
      links.push({
        source: nodeMap[category.category],
        target: nodeMap[element.element],
        value: element.ec,
      });

      // Links from elements to materials
      element.materials.forEach((material) => {
        links.push({
          source: nodeMap[element.element],
          target: nodeMap[material.material],
          value: material.ec,
        });
      });
    });
  });
  console.log("Links are: ", links);

  return { nodes, links };
};
function CustomNode({ x, y, width, height, index, payload, containerWidth }) {
  const isOut = x + width + 6 > containerWidth;
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
        {Math.round(payload.value)} kgCO2e
      </text>
    </Layer>
  );
}
export default function SankeyChart({ data }) {
  const { nodes, links } = transformDataForSankey(data);
  const [activeNode, setActiveNode] = useState(null);

  return (
    <Sankey
      width={600}
      height={300}
      data={{ nodes, links }}
      nodePadding={50}
      margin={{ top: 20, right: 100, bottom: 20, left: 0 }}
      link={{ stroke: "url(#gradient)", fill: "url(gradient)" }}
      node={<CustomNode />}
      onMouseEnter={(node) => setActiveNode(node)}
      onMouseLeave={() => setActiveNode(null)}
    >
      <defs>
        <linearGradient
          id="gradient"
          gradientUnits="Useron"
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
  );
}
