import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import ProjectPage from "./pages/ProjectPage";
import IfcDialog from "./pages/IfcDialog";
import CreatePage from "./pages/CreatePage";
import Layout from "./Layout";
import DraftPage from "./pages/DraftPage";
const routes = [
  { path: "/", element: <LoginPage /> },
  {
    path: "/",
    element: <Layout />,
    children: [
      { path: "/home", element: <HomePage /> },
      { path: "/createProject", element: <CreatePage /> },
      { path: "/project/:projectName?", element: <ProjectPage /> },
      { path: "/ifc", element: <IfcDialog /> },
      { path: "/draft", element: <DraftPage /> },
    ],
  },
];

export default routes;
