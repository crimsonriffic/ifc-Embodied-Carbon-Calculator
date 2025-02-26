import React from "react";
const HistoryTable = ({ projectHistory }) => {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-GB"); // 'en-GB' ensures DD/MM/YYYY format
  };
  return (
    <div className="flex flex-1 flex-col h-[300px]">
      <h1 className="font-bold w-full mb-4">Project Upload History</h1>
      <table className="w-full  text-left border-separate border-spacing-0 border border-gray-800 rounded-lg overflow-hidden">
        <thead>
          <tr>
            <th className="border-b border-r border-gray-800 px-2 py-2 font-bold first:rounded-tl-lg text-left align-top ">
              User
            </th>
            <th className="border-b border-r w-96 border-gray-800 px-2 py-2 font-bold text-left align-top">
              Comments
            </th>
            <th className="border-b border-r border-gray-800 px-2 py-2 font-bold text-left align-top">
              Upload Time
            </th>
            <th className="border-b border-gray-800 px-2 py-2 font-bold text-left align-top">
              Comparison
            </th>
          </tr>
        </thead>
        <tbody className="overflow-auto">
          {projectHistory.map((item, index) => (
            <tr key={index} className="hover:bg-gray-50 px-4 py-2">
              <td
                className={`px-4 py-2 text-left align-top ${
                  index === projectHistory.length - 1
                    ? "first:rounded-bl-lg border-r border-gray-800"
                    : "border-b border-r border-gray-800"
                }`}
              >
                {item.uploaded_by}
              </td>
              <td
                className={` px-4 py-2 text-left align-top ${
                  index === projectHistory.length - 1
                    ? "border-r border-gray-800"
                    : "border-b border-r border-gray-800"
                }`}
              >
                {item.comments}
              </td>
              <td
                className={` px-4 py-2 text-left align-top ${
                  index === projectHistory.length - 1
                    ? "border-r border-gray-800"
                    : "border-b border-r border-gray-800"
                }`}
              >
                {formatDate(item.date_uploaded)}
              </td>
              <td
                className={` px-4 py-2 text-left align-top ${
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
