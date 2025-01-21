import ProjectPage from "./pages/ProjectPage";
import LoginPage from "./pages/LoginPage";

const routes = [
  { path: "/", element: <LoginPage /> },
  { path: "/projects", element: <ProjectPage /> },
];

export default routes;
