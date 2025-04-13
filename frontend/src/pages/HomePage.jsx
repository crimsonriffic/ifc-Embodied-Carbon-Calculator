import { useState, useEffect } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import { useUser } from "../context/UserContext";
import Navbar from "../components/NavBar.jsx";
import LoginTab from "../components/LoginTab.jsx";
import HowItWorks from "../components/HowItWorks.jsx";

function HomePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState("About");

  return (
    // Full-screen background container
    <div
      className="min-h-screen w-full bg-cover bg-center overflow-y-auto"
      style={{
        backgroundImage: `url('/loadingbg.png')`,
      }}
    >
      <Navbar />
      <div className="mx-10 mt-20 py-10 ml-40 flex flex-col">
        <img src="/logo.png" alt="CarbonSmart Logo" className="w-2/3" />
        <div className="flex flex-row mt-10">
          {/**Left side */}
          <div className="w-2/5 pr-24 flex flex-col">
            {/* Navigation Buttons */}
            <div className="flex flex-row space-x-6 ">
              <button
                onClick={() => setActiveTab("About")}
                className={`py-2 font-bold text-2xl ${
                  activeTab === "About"
                    ? "border-b text-white "
                    : "text-[#A9C0A0]"
                } `}
              >
                About
              </button>
              <button
                onClick={() => setActiveTab("How It Works")}
                className={`py-2 font-bold text-2xl ${
                  activeTab === "How It Works"
                    ? "border-b text-white "
                    : "text-[#A9C0A0]"
                } `}
              >
                How it Works
              </button>
              <button
                onClick={() => setActiveTab("Login")}
                className={`py-2 font-bold text-2xl ${
                  activeTab === "Login"
                    ? "border-b text-white "
                    : "text-[#A9C0A0]"
                } `}
              >
                Login
              </button>
            </div>
            {activeTab === "About" && (
              <p className="text-white text-2xl mt-4">
                CarbonSmart is an automated embodied carbon calculator that
                enables users to perform sustainability assessments using
                standardised, vendor-neutral file formats during the building
                design development stage.{" "}
              </p>
            )}
            {activeTab === "Login" && <LoginTab />}
            {activeTab === "How It Works" && <HowItWorks />}
          </div>
          {/**Right side */}
          <div className="w-3/5">
            <img
              src="/homePageImage.png"
              alt="Homepage"
              className="w-2/3 h-auto "
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
