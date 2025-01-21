import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import Login from "./pages/LoginPage.jsx";
//import Test from "./Test.jsx";

import { createBrowserRouter, RouterProvider } from "react-router-dom";
import routes from "./routes.jsx";
const router = createBrowserRouter(routes);
createRoot(document.getElementById("root")).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);