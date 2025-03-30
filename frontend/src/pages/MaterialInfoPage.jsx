import Navbar from "../components/NavBar";
import MaterialTable from "../components/MaterialTable";
import MaterialDialog from "./MaterialDialog";
import { getMaterialDatabase } from "../api/api";

import { useState, useEffect } from "react";

function MaterialInfoPage() {
  const [materialDatabase, setMaterialDatabase] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const materialData = await getMaterialDatabase();

        setMaterialDatabase(materialData.data);
        console.log("Material Database set as : ", materialData.data);
      } catch (err) {
        console.error("Failed to get data: ", err);
      }
    };
    fetchData();
  }, []);
  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Material Database</h1>
      </div>

      {/**Left section */}
      <div className="flex flex-col max-w-md"></div>

      <button
        className="px-4 py-2 w-fit mt-6 mb-4 bg-[#5B9130] text-white rounded font-semibold"
        onClick={() => {
          setIsDialogOpen(true);
        }}
      >
        + New Custom Product Material
      </button>
      {/*Conditional Rendering for IfcDialog*/}
      {isDialogOpen && <MaterialDialog onClose={handleCloseDialog} />}
      <h1 className="text-2xl font-semibold tracking-wide mb-2">
        Product Material Database
      </h1>
      <MaterialTable materialDatabase={materialDatabase} />
    </div>
  );
}

export default MaterialInfoPage;
