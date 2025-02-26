const HistoryTable = ({ projectHistory }) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border border-black bg-white shadow-md rounded-lg">
        <thead className="bg-gray-100">
          <tr>
            <th className="border border-black px-4 py-2">S/N</th>
            <th className="border border-black px-4 py-2">User</th>
            <th className="border border-black px-4 py-2">Comments</th>
            <th className="border border-black px-4 py-2">Upload Time</th>
          </tr>
        </thead>
        <tbody>
          {projectHistory.map((entry, index) => (
            <tr key={entry.version} className="border-b">
              <td className="border border-black px-4 py-2 text-center">
                {entry.version}
              </td>
              <td className="border border-black px-4 py-2">
                {entry.uploaded_by}
              </td>
              <td className="border border-black px-4 py-2">
                {entry.comments}
              </td>
              <td className="border border-black px-4 py-2">
                {new Date(entry.date_uploaded).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Example usage:
// <ProjectHistoryTable projectHistory={yourProjectHistoryArray} />

export default HistoryTable;
