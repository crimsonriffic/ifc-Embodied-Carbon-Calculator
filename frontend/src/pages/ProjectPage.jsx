import Navbar from "../components/NavBar";
import { Link, useParams } from "react-router-dom";
import ProjectErrorDialog from "./ProjectErrorDialog";
function ProjectPage() {
  const { projectName } = useParams();
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="overflow-x-auto bg-white rounded-lg p-4 mt-16">
        {/**Check if project name exists */}
        {projectName ? (
          <h1>Project: {decodeURIComponent(projectName)}</h1>
        ) : (
          <ProjectErrorDialog />
        )}
      </div>
    </div>
  );
}

export default ProjectPage;
