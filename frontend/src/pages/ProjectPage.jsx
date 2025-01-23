import Navbar from "../components/NavBar";
import { Link, useParams, useLocation } from "react-router-dom";
import ProjectErrorDialog from "./ProjectErrorDialog";
import BuildingInfoCard from "../components/BuildingInfoCard";
function ProjectPage() {
  const location = useLocation();
  console.log("Location state is ", location.state);
  const { projectId } = location.state;
  const { projectName } = useParams();
  if (!projectId) {
    return <p className="text-red-500">No project ID provided.</p>;
  }
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
