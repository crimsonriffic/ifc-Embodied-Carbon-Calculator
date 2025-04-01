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
import UploadOverview from "./pages/UploadOverview";
import UploadComparison from "./pages/UploadComparison";
import ProjectProgress from "./pages/ProjectProgress";
import UploadReview from "./pages/UploadReview";
import ErrorHandlingPage from "./pages/ErrorHandlingPage";
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
      { path: "/uploadOverview/:projectName?", element: <UploadOverview /> },
      { path: "/uploadReview/:projectName?", element: <UploadReview /> },
      {
        path: "/uploadComparison/:projectName?",
        element: <UploadComparison />,
      },
      { path: "/errorHandling/:projectName?", element: <ErrorHandlingPage /> },

      { path: "/projectProgress/:projectName?", element: <ProjectProgress /> },
      { path: "/ifc", element: <IfcDialog /> },
    ],
  },
];

export default routes;
