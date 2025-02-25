import SankeyChart from "../components/SankeyChart";
function DraftPage() {
  const data = {
    total_ec: 10731.417534758186,
    ec_breakdown: [
      {
        category: "substructure",
        total_ec: 5342.129999999996,
        elements: [
          {
            element: "slab",
            ec: 1938.21875,
            materials: [{ material: "concrete", ec: 1938.21875 }],
          },
          {
            element: "wall",
            ec: 8311.679999999998,
            materials: [{ material: "concrete", ec: 8311.679999999998 }],
          },
        ],
      },
      {
        category: "superstructure",
        total_ec: 5389.287534758189,
        elements: [
          {
            element: "roof",
            ec: 481.5187485187485,
            materials: [{ material: "concrete", ec: 481.5187485187485 }],
          },
        ],
      },
    ],
  };

  return (
    <div className="p-4 mt-20">
      <h1 className="text-2xl font-bold mb-4">Sankey Chart</h1>
      <SankeyChart data={data} />
    </div>
  );
}

export default DraftPage;
