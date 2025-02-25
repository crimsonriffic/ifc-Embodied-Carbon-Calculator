import React from "react";
const HistoryTable = ({ projectHistory }) => {
  return (
    <div className="flex flex-1 flex-col">
      <h1 className="font-bold w-full md:w-1/2">Project Upload History</h1>
      <table className="w-full md:w-1/2 text-left border-separate border-spacing-0 border border-gray-800 rounded-lg overflow-hidden">
        <thead>
          <tr>
            <th className="border-b border-r border-gray-800 px-6 py-4 font-bold first:rounded-tl-lg ">
              User
            </th>
            <th className="border-b border-r w-96 border-gray-800 px-6 py-4 font-bold">
              Comments
            </th>
            <th className="border-b border-r border-gray-800 px-6 py-4 font-bold">
              Upload Time
            </th>
            <th className="border-b border-gray-800 px-6 py-4 font-bold">
              Comparison
            </th>
          </tr>
        </thead>
        <tbody>
          {projectHistory.map((item, index) => (
            <tr key={index} className="hover:bg-gray-50 px-6 py-4">
              <td
                className={`px-6 py-2 ${
                  index === projectHistory.length - 1
                    ? "first:rounded-bl-lg border-r border-gray-800"
                    : "border-b border-r border-gray-800"
                }`}
              >
                {item.uploaded_by}
              </td>
              <td
                className={` px-6 py-4 ${
                  index === projectHistory.length - 1
                    ? "border-r border-gray-800"
                    : "border-b border-r border-gray-800"
                }`}
              >
                {item.comments}
              </td>
              <td
                className={` px-6 py-4 ${
                  index === projectHistory.length - 1
                    ? "border-r border-gray-800"
                    : "border-b border-r border-gray-800"
                }`}
              >
                {item.date_uploaded}
              </td>
              <td
                className={` px-6 py-4 ${
                  index === projectHistory.length - 1
                    ? ""
                    : "border-b border-gray-800"
                }`}
              >
                TODO
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default HistoryTable;
