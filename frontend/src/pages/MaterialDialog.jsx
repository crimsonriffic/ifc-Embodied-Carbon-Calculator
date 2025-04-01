import { useState } from "react";
import { uploadMaterial } from "../api/api.jsx";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext.jsx";
import { ArrowRightIcon, XMarkIcon } from "@heroicons/react/24/solid";
function MaterialDialog({ onClose }) {
  const [category, setCategory] = useState("Material");
  const [family, setFamily] = useState("Concrete");

  const [materialType, setMaterialType] = useState("");
  const [density, setDensity] = useState("");
  const [ec, setEc] = useState("");
  const [unit, setUnit] = useState("kg");
  const [uploadError, setUploadError] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [loading, setLoading] = useState(false); // Loading state

  const { username } = useUser();

  const navigate = useNavigate();
  const handleUpdateFamily = (e) => {
    setFamily(e.target.value);
  };

  const handleUpdateCategory = (e) => {
    setCategory(e.target.value);
    if (e.target.value === "Product") {
      setUnit("m2");
    } else {
      setUnit("kg");
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    console.log("Handle Upload Called");
    setLoading(true);

    try {
      const userId = "user123";
      const response = await uploadMaterial(
        userId,
        family,
        materialType,
        density,
        ec,
        unit
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

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-white p-4 rounded shadow-lg  w-[700px] h-[450px]  max-w-full">
        <div className="flex flex-row justify-between">
          <h2 className="text-xl font-semibold mb-4">New Product Material</h2>
          <button onClick={onClose}>
            <XMarkIcon
              className="rounded-full w-5 h-5 text-gray-500 border-2 border-gray-500 font-bold"
              stroke="currentColor"
              strokeWidth={2}
            />
          </button>
        </div>

        {showSuccess && (
          <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg">
            Upload successful!
          </div>
        )}
        {uploadError && (
          <div className="mb-4 text-red-600 font-semibold">{uploadError}</div>
        )}
        {/*Upload form */}
        <div className="w-full ">
          {/*Upload form */}
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="flex flex-row space-x-4">
              <div className="flex flex-col">
                <div className="max-w-md ">
                  {/*Input Category */}
                  <label
                    htmlFor="category"
                    className="block text-gray-700 mb-1"
                  >
                    Category
                  </label>
                  <select
                    id="category"
                    value={category}
                    onChange={handleUpdateCategory}
                    className="p-2 border w-80 border-gray-200 shadow-md mb-4"
                  >
                    <option value="Material">Material</option>
                    <option value="Product">Product</option>
                  </select>
                </div>
                <div className="max-w-md">
                  {/*Input Family */}
                  <label htmlFor="family" className="block text-gray-700 mb-1">
                    Family
                  </label>
                  <select
                    id="family"
                    value={family}
                    onChange={handleUpdateFamily}
                    className="p-2 border w-80 border-gray-200 shadow-md mb-4"
                  >
                    <option value="Concrete">Concrete</option>
                    <option value="Steel">Steel</option>
                    <option value="Wood">Wood</option>
                    <option value="Door">Door</option>
                    <option value="Window">Window</option>
                  </select>
                </div>

                {/** Material Type */}
                <div className="mb-4">
                  <label htmlFor="client" className="block text-gray-700 mb-1">
                    Type
                  </label>
                  <input
                    type="text"
                    id="materialType"
                    value={materialType}
                    onChange={(e) => setMaterialType(e.target.value)}
                    className="p-2 w-80 border border-gray-200 shadow-md focus:outline-none resize-none"
                    required
                  />
                </div>
              </div>

              <div className="max-w-md flex flex-col">
                {/** Unit*/}
                <div className="max-w-md">
                  <label htmlFor="status" className="block text-gray-700 mb-1">
                    Unit
                  </label>
                  <p className="p-2 border w-80 border-gray-200 shadow-md mb-4">
                    {unit}
                  </p>
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
                    className={`p-2 w-80 border shadow-md focus:outline-none resize-none ${
                      category === "Product"
                        ? "bg-gray-100 cursor-not-allowed"
                        : "border-gray-200"
                    }`}
                    disabled={category === "Product"}
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

                {/**Upload Button */}
                <div className="mt-16 flex justify-end space-x-2">
                  <button
                    className={`px-4 py-2 rounded ${
                      loading
                        ? "bg-gray-400 cursor-not-allowed text-black"
                        : "bg-[#5B9130] text-white "
                    } `}
                    disabled={loading}
                  >
                    {loading ? (
                      "Uploading..."
                    ) : (
                      <span className="flex items-center space-x-1">
                        <ArrowRightIcon className="w-6 h-6 text-white mr-2" />
                        Confirm{" "}
                      </span>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default MaterialDialog;
