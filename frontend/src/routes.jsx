import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import ProjectPage from "./pages/ProjectPage";
import IfcDialog from "./pages/IfcDialog";
import CreatePage from "./pages/CreatePage";
import Layout from "./Layout";
import DraftPage from "./pages/DraftPage";
import EditPage1 from "./pages/EditPage1";
import MaterialInfoPage from "./pages/MaterialInfoPage";
import ProjectInfoPage from "./pages/ProjectInfoPage";
import UploadConfirmPage from "./pages/UploadConfirmPage";
const routes = [
  { path: "/", element: <LoginPage /> },
  {
    path: "/",
    element: <Layout />,
    children: [
      { path: "/home", element: <HomePage /> },
      { path: "/createProject", element: <CreatePage /> },
      { path: "/projectInfo/:projectName?", element: <ProjectInfoPage /> },
      { path: "/editProject/:projectName?", element: <EditPage1 /> },
      { path: "/materialInfo/:projectName?", element: <MaterialInfoPage /> },
      { path: "/uploadConfirm/:projectName?", element: <UploadConfirmPage /> },
      { path: "/project/:projectName?", element: <ProjectPage /> },
      { path: "/ifc", element: <IfcDialog /> },
      { path: "/draft", element: <DraftPage /> },
    ],
  },
];

export default routes;
