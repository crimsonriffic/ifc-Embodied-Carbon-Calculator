import Navbar from "../components/NavBar";
import { Link, useParams, useLocation } from "react-router-dom";
import ProjectErrorDialog from "./ProjectErrorDialog";
import BuildingInfoCard from "../components/BuildingInfoCard";
function ProjectPage() {
  const location = useLocation();
  const { projectName } = useParams();
  console.log("Location state is ", location.state);

  // Check if location.state is null or undefined
  if (!location.state) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <Navbar />
        <div className="bg-white rounded-lg p-6 shadow-md text-center">
          <h1 className="text-xl font-semibold text-red-500 mb-4">
            Error: Missing Project Information
          </h1>
          <p className="text-gray-700">
            No project data was provided. Make sure you navigated to this page
            from a valid project link.
          </p>
          <Link
            to="/home"
            className="mt-4 inline-block px-4 py-2 bg-[#5B9130] text-white rounded hover:bg-[#3d5c23]"
          >
            Select Project
          </Link>
        </div>
      </div>
    );
  }
  const { projectId } = location.state;

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="overflow-x-auto bg-white rounded-lg p-4 mt-16">
        {/**Check if project name exists */}
        {projectName ? (
          <div>
            <div className="bg-gray-200 text-gray-800 rounded-lg px-4 py-2 flex items-center shadow-md mb-2 sm:max-w-xs">
              <h1 className="text-lg font-semibold tracking-wide">
                {decodeURIComponent(projectName)}
              </h1>
            </div>
            <BuildingInfoCard projectId={projectId} />
          </div>
        ) : (
          <ProjectErrorDialog />
        )}
      </div>
    </div>
  );
}

export default ProjectPage;
