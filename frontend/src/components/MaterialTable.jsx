const MaterialTable = ({ materialDatabase, newMaterialId }) => {
  return (
    <div className="overflow-x-auto h-96">
      <table className="min-w-full border relative border-gray-300 bg-white shadow-md rounded-lg">
        <thead className="bg-gray-100 sticky top-0">
          <tr>
            <th className="border border-gray-300 px-4 py-2">Material Type</th>
            <th className="border border-gray-300 px-4 py-2">
              Specified Material
            </th>
            <th className="border border-gray-300 px-4 py-2">Density</th>
            <th className="border border-gray-300 px-4 py-2">
              A1-A3 EC (kgCO2eq/unit)
            </th>
            <th className="border border-gray-300 px-4 py-2">Unit</th>
            <th className="border border-gray-300 px-4 py-2">
              Database Source
            </th>
          </tr>
        </thead>
        <tbody>
          {materialDatabase.map((entry, index) => (
            <tr
              className={`border-b ${
                entry.id === newMaterialId ? "bg-green-300" : ""
              }`}
              key={entry.id}
            >
              <td className="border border-gray-300 px-4 py-2 text-center">
                {entry.material_type}
              </td>
              <td className="border border-gray-300 px-4 py-2">
                {entry.specified_material}
              </td>
              <td className="border border-gray-300 px-4 py-2">
                {entry.density || "-"}
              </td>
              <td className="border border-gray-300 px-4 py-2">
                {entry.embodied_carbon}
              </td>
              <td className="border border-gray-300 px-4 py-2">{entry.unit}</td>
              <td className="border border-gray-300 px-4 py-2">
                {entry.database_source}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Example usage:
// <MaterialTable materialDatabase={yourmaterialDatabaseArray} />

export default MaterialTable;
