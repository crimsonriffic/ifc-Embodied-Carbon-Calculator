import Navbar from "../components/NavBar";
import Stepper from "../components/Stepper";
import { Link, useParams, useLocation } from "react-router-dom";

function EditPage1() {
  const { projectName } = useParams();
  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Upload Information</h1>
      </div>
      <div className="mt-6">
        <Stepper currentStep={1} />
      </div>
      <div className="bg-[#A9C0A0] mt-4 text-white rounded-lg px-4 py-2 flex items-center shadow-md mb-2 sm:max-w-md">
        <h1 className="text-2xl font-semibold tracking-wide">
          {decodeURIComponent(projectName)}
        </h1>
      </div>
    </div>
  );
}

export default EditPage1;
