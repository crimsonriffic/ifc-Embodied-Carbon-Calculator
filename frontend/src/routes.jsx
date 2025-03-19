import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import ProjectPage from "./pages/ProjectPage";
import IfcDialog from "./pages/IfcDialog";
import CreatePage from "./pages/CreatePage";
import Layout from "./Layout";
import UploadHistory from "./pages/UploadHistory";
import MaterialInfoPage from "./pages/MaterialInfoPage";
import ProjectInfoPage from "./pages/ProjectInfoPage";
import UploadConfirmPage from "./pages/UploadConfirmPage";
import BreakdownPage from "./pages/BreakdownPage";
const routes = [
  { path: "/", element: <LoginPage /> },
  {
    path: "/",
    element: <Layout />,
    children: [
      { path: "/home", element: <HomePage /> },
      { path: "/createProject", element: <CreatePage /> },
      { path: "/projectInfo/:projectName?", element: <ProjectInfoPage /> },
      { path: "/uploadHistory/:projectName?", element: <UploadHistory /> },
      { path: "/materialInfo/:projectName?", element: <MaterialInfoPage /> },
      { path: "/uploadConfirm/:projectName?", element: <UploadConfirmPage /> },
      { path: "/project/:projectName?", element: <ProjectPage /> },
      { path: "/breakdown/:projectName?", element: <BreakdownPage /> },
      { path: "/ifc", element: <IfcDialog /> },
    ],
  },
];

export default routes;
