import ActiveProjectsPage from "./pages/ActiveProjectsPage";
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
import ExportResults from "./pages/ExportResults";
import LoadingPage from "./pages/LoadingPage";
import HomePage from "./pages/HomePage";
import ReportPage from "./pages/ReportPage";
const routes = [
  { path: "/", element: <HomePage /> },
  { path: "/report", element: <ReportPage /> },

  {
    path: "/",
    element: <Layout />,
    children: [
      { path: "/activeProjects", element: <ActiveProjectsPage /> },
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
      { path: "/exportResults/:projectName?", element: <ExportResults /> },
      { path: "/ifc", element: <IfcDialog /> },
      { path: "/loading/:projectName?", element: <LoadingPage /> },
    ],
  },
];

export default routes;
