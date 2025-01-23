import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import ProjectPage from "./pages/ProjectPage";
import ECBreakdownPage from "./pages/ECBreakdownPage";
import IfcDialog from "./pages/IfcDialog";
const routes = [
  { path: "/", element: <LoginPage /> },
  { path: "/home", element: <HomePage /> },
  { path: "/project", element: <ProjectPage /> },
  { path: "/ecbreakdown", element: <ECBreakdownPage /> },
  { path: "/ifc", element: <IfcDialog /> },
];

export default routes;
