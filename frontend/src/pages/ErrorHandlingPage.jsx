import Navbar from "../components/NavBar";
import Stepper from "../components/Stepper";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { getMissingElements, getMissingMaterials } from "../api/api";
function ErrorHandlingPage() {
  const [missingMaterials, setMissingMaterials] = useState([]);
  const location = useLocation();
  const navigate = useNavigate();
  const { projectId } = location.state;

  const { projectName } = useParams();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const missingElementsResponse = await getMissingElements(projectId);
        const missingMaterialsResponse = await getMissingMaterials(projectId);
        console.log(
          "Missing elements response: ",
          missingElementsResponse.data
        );
        console.log(
          "Missing materials response: ",
          missingMaterialsResponse.data
        );

        const materials = missingMaterialsResponse.data.missing_materials.map(
          (item) => item.SpecifiedMaterial
        );
        setMissingMaterials(materials);
      } catch (err) {
        console.error("Failed to fetch data: ", err);
      }
    };
    if (projectId) {
      fetchData();
    }
  }, [projectId]);
  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Error Handling</h1>
        <p className="mt-2 text-lg">
          Please review the errors of your uploaded model and resolve them as
          required.
        </p>
      </div>
      <div className="mt-6">
        <Stepper currentStep={4} />
      </div>
      <div className="bg-[#A9C0A0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mt-4 mb-6 sm:max-w-md">
        <h1 className="text-2xl font-semibold tracking-wide">
          {decodeURIComponent(projectName)}
        </h1>
      </div>
      {missingMaterials}
    </div>
  );
}

export default ErrorHandlingPage;
