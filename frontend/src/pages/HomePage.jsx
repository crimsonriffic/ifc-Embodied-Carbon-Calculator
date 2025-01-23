import getProjectsByUsername from "../api/api";
import Navbar from "../components/NavBar";
function HomePage() {
  const projects = getProjectsByUsername();

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar username="carina" />
      <div className="overflow-x-auto bg-white shadow-md rounded-lg p-4 mt-16">
        <table className="table-auto w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-200">
              <th className="border border-gray-300 px-4 py-2 text-left">
                Project Name
              </th>
              <th className="border border-gray-300 px-4 py-2 text-left">
                Client Name
              </th>
              <th className="border border-gray-300 px-4 py-2 text-left">
                Latest Update
              </th>
              <th className="border border-gray-300 px-4 py-2 text-left">
                IFC file
              </th>
              <th className="border border-gray-300 px-4 py-2 text-left">
                Go To Project
              </th>
            </tr>
          </thead>
          <tbody>
            {projects.map((project, index) => (
              <tr key={index} className="hover:bg-gray-100">
                <td className="border border-gray-300 px-4 py-2">
                  {project.projectName}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  {project.clientName}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  {project.latestUpdate}
                </td>
                <td className="border border-gray-300 px-4 py-2 text-center">
                  <button className="text-gray-600 hover:text-blue-500">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-6 w-6 inline"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 4v16m8-8H4"
                      />
                    </svg>
                  </button>
                </td>
                <td className="border border-gray-300 px-4 py-2 text-center">
                  <button className="text-gray-600 hover:text-blue-500">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-6 w-6 inline"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M14 5l7 7m0 0l-7 7m7-7H3"
                      />
                    </svg>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default HomePage;
