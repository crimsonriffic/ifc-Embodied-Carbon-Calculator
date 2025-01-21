import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import ProjectPage from "./pages/ProjectPage";
import ECBreakdownPage from "./pages/ECBreakdownPage";
const routes = [
  { path: "/", element: <LoginPage /> },
  { path: "/home", element: <HomePage /> },
  { path: "/project", element: <ProjectPage /> },
  { path: "/ecbreakdown", element: <ECBreakdownPage /> },
];

export default routes;
