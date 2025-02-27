import { Sankey, Tooltip } from "recharts";
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

export default function SankeyChart({ data }) {
  const { nodes, links } = transformDataForSankey(data);
  const [activeNode, setActiveNode] = useState(null);

  return (
    <div className="w-full h-[600px]">
      <Sankey
        width={800}
        height={600}
        data={{ nodes, links }}
        nodePadding={50}
        margin={{ top: 20, right: 200, bottom: 20, left: 20 }}
        link={{ stroke: "url(#gradient)", fill: "url(gradient)" }}
        node={{
          stroke: "#79E779",
          strokeWidth: 2,
          fill: "#79E779",
          label: true,
        }}
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
    </div>
  );
}
