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
        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        link={{ stroke: "#ccc" }}
        onMouseEnter={(node) => setActiveNode(node)}
        onMouseLeave={() => setActiveNode(null)}
      >
        <Tooltip />
      </Sankey>
    </div>
  );
}
