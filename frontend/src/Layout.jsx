import { Outlet } from "react-router-dom";
import Navbar from "./components/NavBar";

const Layout = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="flex-1 p-6 md:px-36">
        <Outlet />
      </div>
    </div>
  );
};

export default Layout;
