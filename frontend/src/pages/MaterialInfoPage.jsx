import Navbar from "../components/NavBar";
import Stepper from "../components/Stepper";
import MaterialTable from "../components/MaterialTable";
import HistoryTable from "../components/HistoryTable";
import {
  getMaterialDatabase,
  getProjectHistory,
  uploadIfc,
  uploadMaterial,
} from "../api/api";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

function MaterialInfoPage() {
  const [materialType, setMaterialType] = useState("Concrete");
  const [specifiedMaterial, setSpecifiedMaterial] = useState("");
  const [density, setDensity] = useState("");
  const [ec, setEc] = useState("");
  const [unit, setUnit] = useState("kg");
  const [newMaterialId, setNewMaterialId] = useState("");
  const [uploadError, setUploadError] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");
  const [showSuccess, setShowSuccess] = useState(false);
  const [materialDatabase, setMaterialDatabase] = useState([]);

  const location = useLocation();
  const navigate = useNavigate();
  const { projectId } = location.state;
  const { projectName } = useParams();

  const handleProceed = (projectId, projectName) => {
    console.log("HandleProceed called");
    navigate(`/uploadConfirm/${encodeURIComponent(projectName)}`, {
      state: { projectId },
    });
  };
  const handleUpdateMaterialType = (e) => {
    setMaterialType(e.target.value);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    console.log("Handle Upload Called");

    try {
      const userId = "user123";
      const response = await uploadMaterial(
        userId,
        materialType,
        specifiedMaterial,
        density,
        ec,
        unit
      );
      console.log("Response from upload material is, ", response);
      // After successful upload, fetch updated materials
      const materialData = await getMaterialDatabase();
      setMaterialDatabase(materialData.data);

      // Store the new material's ID to highlight it
      setNewMaterialId(response._id); // Add this state variable
      setSuccessMessage(response.message);
      setUploadError(null);
      setShowSuccess(true);

      // Remove highlight after 3 seconds
      setTimeout(() => {
        setNewMaterialId(null);
      }, 3000);
    } catch (err) {
      setUploadError(
        err.response?.data?.detail || "An error occurred during upload."
      );
    }
  };
  useEffect(() => {
    const fetchData = async () => {
      try {
        const materialData = await getMaterialDatabase();

        setMaterialDatabase(materialData.data);
        console.log("Material Database set as : ", materialData.data);
      } catch (err) {
        console.error("Failed to data: ", err);
      }
    };
    if (projectId) {
      fetchData();
    }
  }, []);
  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Upload Information</h1>
      </div>
      <div className="mt-6">
        <Stepper currentStep={3} />
      </div>
      <div className="bg-[#A9C0A0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mt-4 mb-6 sm:max-w-md">
        <h1 className="text-2xl font-semibold tracking-wide">
          {decodeURIComponent(projectName)}
        </h1>
      </div>
      <div className="flex flex-row gap-x-32">
        {/**Left section */}
        <div className="flex flex-col max-w-md">
          {/** New Upload section*/}
          <h1 className="text-2xl font-semibold tracking-wide mb-2">
            New Custom Material
          </h1>

          {/*Upload form */}
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="max-w-md">
              {/*Input Material type */}
              <label
                htmlFor="materialType"
                className="block text-gray-700 mb-1"
              >
                Material Type
              </label>
              <select
                id="material-type"
                value={materialType}
                onChange={handleUpdateMaterialType}
                className="p-2 border w-80 border-gray-200 shadow-md mb-4"
              >
                <option value="Concrete">Concrete</option>
                <option value="Steel">Steel</option>
                <option value="Wood">Wood</option>
              </select>
            </div>

            {/** Specified Material */}
            <div className="mb-4">
              <label htmlFor="client" className="block text-gray-700 mb-1">
                Specified Material
              </label>
              <input
                type="text"
                id="specifiedMaterial"
                value={specifiedMaterial}
                onChange={(e) => setSpecifiedMaterial(e.target.value)}
                className="p-2 w-80 border border-gray-200 shadow-md focus:outline-none resize-none"
                required
              />
            </div>
            {/** Density */}
            <div className="mb-4">
              <label htmlFor="client" className="block text-gray-700 mb-1">
                Density
              </label>
              <input
                type="text"
                id="density"
                value={density}
                onChange={(e) => setDensity(e.target.value)}
                className="p-2 w-80 border border-gray-200 shadow-md focus:outline-none resize-none"
                required
              />
            </div>

            {/** EC */}
            <div className="mb-4">
              <label htmlFor="client" className="block text-gray-700 mb-1">
                A1-A3 Embodied Carbon (kgCO2eq/unit)
              </label>
              <input
                type="text"
                id="ec"
                value={ec}
                onChange={(e) => setEc(e.target.value)}
                className="p-2 w-80 border border-gray-200 shadow-md focus:outline-none resize-none"
                required
              />
            </div>

            {/** Unit*/}
            <div className="max-w-md">
              <label htmlFor="status" className="block text-gray-700 mb-1">
                Unit
              </label>
              <select
                id="unit"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="p-2 border w-80 border-gray-200 shadow-md mb-4"
              >
                <option value="kg">kg</option>
                <option value="m2">m2</option>
              </select>
            </div>

            {/**Upload Button */}
            <div className="flex flex-row">
              <button className="px-4 py-2 bg-[#E3EBE0] text-black rounded">
                Add new custom material
              </button>
              {showSuccess && (
                <div className=" p-2 text-green-700 rounded-lg">
                  Upload successful!
                </div>
              )}
              {uploadError && (
                <div className=" text-red-600 font-semibold">{uploadError}</div>
              )}
            </div>
          </form>
          <button
            className="px-4 py-2 mt-6 w-28 bg-[#5B9130] text-black rounded"
            onClick={() => {
              handleProceed(projectId, projectName);
            }}
          >
            Proceed
          </button>
        </div>

        {/**Right section */}
        <div className="flex flex-1 flex-col">
          <h1 className="text-2xl font-semibold tracking-wide mb-2">
            Material Database
          </h1>
          <MaterialTable
            materialDatabase={materialDatabase}
            newMaterialId={newMaterialId}
          />
        </div>
      </div>
    </div>
  );
}

export default MaterialInfoPage;
