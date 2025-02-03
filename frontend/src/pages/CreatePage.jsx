import Navbar from "../components/NavBar";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { ArrowUpTrayIcon } from "@heroicons/react/24/solid";
import { Navigate } from "react-router-dom";
export default function CreatePage() {
  const [projectName, setProjectName] = useState("");
  const [client, setClient] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false); // State for IfcDialog
  const [selectedFile, setSelectedFile] = useState("null");
  const navigate = useNavigate();
  const handleUpload = async (e) => {
    e.preventDefault();
    console.log("Handle Upload");
    alert("Successfully created project!");
    navigate("/home");
  };
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };
  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-10 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Create a new project</h1>
        <p className="mt-2 text-lg">Placeholder text</p>
      </div>
      {/* Create project form */}
      {/*Upload form */}
      <div className=" bg-white shadow-md rounded-lg p-4 w-full mt-10">
        <form onSubmit={handleUpload} className="space-y-4">
          {/*Input Project Name */}
          <div className="mb-4">
            <label
              htmlFor="projectName"
              className="block text-sm font-medium text-gray-700 "
            >
              Project Name
            </label>
            <input
              type="text"
              id="projectName"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Enter Project Name"
              className=" p-2 text-sm border-b-2 border-gray-200 focus:outline-none resize-none"
              required
            />
          </div>

          {/*Input Client Name */}
          <div className="mb-4">
            <label
              htmlFor="client"
              className="block text-sm font-medium text-gray-700 "
            >
              Client Name
            </label>
            <input
              type="text"
              id="client"
              value={client}
              onChange={(e) => setClient(e.target.value)}
              placeholder="Enter Client"
              className=" p-2 text-sm border-b-2 border-gray-200 focus:outline-none resize-none"
              required
            />
          </div>

          {/** Upload IFC Seciton */}
          <div className="mb-4">
            <label
              htmlFor="client"
              className="block text-sm font-medium text-gray-700 "
            >
              Upload IFC
            </label>
            <input
              type="file"
              onChange={handleFileChange}
              className="p-2 text-sm border-b-2 border-gray-200 focus:outline-none resize-none"
              required
            />
          </div>

          <div className="flex justify-end space-x-2">
            <button className="px-4 py-2 bg-[#5B9130] text-white rounded">
              Create Project
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
