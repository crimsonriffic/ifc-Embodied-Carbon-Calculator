import Navbar from "../components/NavBar";
import Stepper from "../components/Stepper";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import {
  getMissingElements,
  getMissingMaterials,
  uploadMaterial,
} from "../api/api";
import {
  PlusIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/solid";
function ErrorHandlingPage() {
  const [missingMaterials, setMissingMaterials] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(false); // Loading state
  const [uploadError, setUploadError] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();
  const { projectId } = location.state;

  const { projectName } = useParams();
  //TODO: handleReUpload()

  const handleInputChange = (index, field, value) => {
    setMaterials((prev) => {
      const newMaterials = [...prev];
      newMaterials[index][field] = value;
      console.log(newMaterials);
      return newMaterials;
    });
  };

  const handleAddMaterial = async (material) => {
    console.log("HandleAddMaterial is called with, ", material);
    try {
      const userId = "user123";
      const response = await uploadMaterial(
        userId,
        material.family,
        material.materialType,
        material.density,
        material.ec,
        material.unit
      );
      console.log("Response from upload material is, ", response);

      // Store the new material's ID to highlight it
      setUploadError(null);
      setShowSuccess(true);
      setLoading(false);
    } catch (err) {
      setUploadError(
        err.response?.data?.detail || "An error occurred during upload."
      );
    }
  };

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

        const initializedMaterials =
          missingMaterialsResponse.data.missing_materials.map((item) => ({
            materialType: item.SpecifiedMaterial,
            category: "",
            unit: "",
            ec: "",
            density: "",
            family: "",
          }));
        console.log("Initial Materials set as ", initializedMaterials);
        setMaterials(initializedMaterials);
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
      <div className="flex flex-row">
        {/**Left Section */}
        <div className=" flex flex-col w-1/3 min-w-[200px] gap-y-4">
          <h1 className="text-2xl font-bold">Upload XX</h1>
          <div>
            <h1 className="text-sm">Detected Errors </h1>
            <p className=" text-xl font-bold ">xx</p>
          </div>
        </div>

        {/**Right section */}
        <div className=" flex flex-col w-2/3 min-w-[200px] gap-y-4">
          <h1 className="text-2xl font-bold">
            Errors Requiring File Correction
          </h1>
          <p className="text-sm">
            These elements contain errors that cannot be resolved within the
            system. Please review the details below, correct them in the source
            IFC file, and re-upload the updated file to proceed.{" "}
          </p>
          {/**Elements error table */}
          <table className="table-auto w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-200">
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Element ID
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  IfcElement
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Material Family
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Material Type
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Error
                </th>
              </tr>
            </thead>
            <tbody>
              {missingMaterials
                .slice() // Create a copy to avoid mutating the original array
                .map((missingMaterial, index) => (
                  <tr key={index} className="hover:bg-gray-100">
                    <td className="border border-gray-300 px-4 py-2">
                      Do with brayden and davis on weds
                    </td>
                    <td className="border border-gray-300 px-4 py-2">-</td>
                    <td className="border border-gray-300 px-4 py-2">-</td>
                    <td className="border border-gray-300 px-4 py-2">-</td>
                    <td className="border border-gray-300 px-4 py-2 text-center">
                      -
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
          <div className="flex justify-end mt-auto">
            <button
              className="flex items-center gap-x-2 px-4 py-2 w-fit mt-6 mb-4 bg-gray-400 text-white rounded font-semibold"
              onClick={() => {
                handleReUpload(projectId, projectName);
              }}
            >
              <ArrowLeftIcon className="w-6 h-6 text-white" /> Re-upload
            </button>
          </div>
          <h1 className="text-2xl font-bold">
            Errors Resolvable by Database Update
          </h1>
          <p className="text-sm">
            Unrecognised materials has been identified in the model. Resolve
            these errors by adding the identified materials to the system
            material database. Once added, the system will automatically update
            the calculations for these elements{" "}
          </p>
          {/**Materials error table */}
          <table className="table-auto w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-200">
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Category
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Unit
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Family
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Type
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Density
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  A1-A3 Emission / Unit
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  Add
                </th>
              </tr>
            </thead>
            <tbody>
              {materials.map((material, index) => (
                <tr key={index} className="hover:bg-gray-100">
                  <td className="border border-gray-300 px-4 py-2">
                    <select
                      id="category"
                      className="border border-gray-300 rounded px-2 py-1 w-full"
                      value={material.category || ""}
                      onChange={(e) => {
                        // Update the category and corresponding unit + density
                        handleInputChange(index, "category", e.target.value);
                        const unit =
                          e.target.value === "Material" ? "kg" : "m2";
                        handleInputChange(index, "unit", unit);
                        handleInputChange(index, "density", "");
                      }}
                    >
                      <option value="" disabled>
                        Select a category
                      </option>
                      <option value="Material">Material</option>
                      <option value="Product">Product</option>
                    </select>
                  </td>
                  <td className="border border-gray-300 px-4 py-2">
                    {material.unit}
                  </td>
                  <td className="border border-gray-300 px-4 py-2">
                    <select
                      id="family"
                      className="border border-gray-300 rounded px-2 py-1 w-full"
                      value={material.family || ""}
                      onChange={(e) => {
                        // Update the category and corresponding unit
                        handleInputChange(index, "family", e.target.value);
                      }}
                    >
                      {" "}
                      <option value="" disabled>
                        Select a family
                      </option>
                      <option value="Concrete">Concrete</option>
                      <option value="Steel">Steel</option>
                      <option value="Wood">Wood</option>
                      <option value="Door">Door</option>
                      <option value="Window">Window</option>
                    </select>
                  </td>
                  <td className="border border-gray-300 px-4 py-2">
                    {material.materialType}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-center">
                    <input
                      type="text"
                      id="density"
                      value={material.density}
                      onChange={(e) =>
                        handleInputChange(index, "density", e.target.value)
                      }
                      className={`p-2 w-80 border shadow-md focus:outline-none resize-none ${
                        material.category === "Product"
                          ? "bg-gray-100 cursor-not-allowed"
                          : "border-gray-200"
                      }`}
                      disabled={material.category === "Product"}
                      required
                    />
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-center">
                    <input
                      type="text"
                      id="ec"
                      value={material.ec}
                      onChange={(e) =>
                        handleInputChange(index, "ec", e.target.value)
                      }
                      className="p-2 w-80 border border-gray-200 shadow-md focus:outline-none resize-none"
                      required
                    ></input>
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-center">
                    <button
                      onClick={() => handleAddMaterial(material)}
                      className="text-gray-600 hover:text-blue-500"
                    >
                      <PlusIcon className="w-6 h-6 text-[#5B9130]" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex justify-end mt-auto">
            <button
              className="flex items-center gap-x-2 px-4 py-2 w-fit mt-6 mb-4 bg-[#5B9130] text-white rounded font-semibold"
              onClick={() => {
                handleConfirm(projectId, projectName);
              }}
            >
              <ArrowRightIcon className="w-6 h-6 text-white" /> Confirm
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ErrorHandlingPage;
