import Navbar from "../components/NavBar";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";

import { createProject } from "../api/api";
export default function OldCreatePage() {
  const [projectName, setProjectName] = useState("");
  const [client, setClient] = useState("");
  const [typology, setTypology] = useState("");
  const [status, setStatus] = useState("");
  const [benchmark, setBenchmark] = useState({});
  const [isDialogOpen, setIsDialogOpen] = useState(false); // State for IfcDialog
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const { username } = useUser();
  const navigate = useNavigate();

  const benchmarks = {
    Residential: { "Green Mark": 1500, "LETI 2030 Design Target": 300 },
    "Non-Residential (Generic)": { "Green Mark": 1000 },
    "Non-Residential (Office)": { "LETI 2030 Design Target": 350 },
    "Non-Residential (Education)": { "LETI 2030 Design Target": 300 },
    "Non-Residential (Retail)": { "LETI 2030 Design Target": 300 },
    Industrial: { "Green Mark": 2500 },
  };
  const handleUpload = async (e) => {
    e.preventDefault();
    console.log("Handle Upload with user:", username);
    setLoading(true);
    try {
      const response = await createProject(
        projectName,
        client,
        selectedFile,
        username,
        typology,
        status,
        benchmark
      );
      console.log("Successfully created project: ", response.data);
      navigate("/home");
    } catch (err) {
      console.error("Faild to create project", err);
      alert("Failed to create projec!");
    } finally {
      setLoading(false);
    }
  };
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };
  const handleUpdateTypology = (e) => {
    setTypology(e.target.value);
  };

  const handleUpdateStatus = (e) => {
    setStatus(e.target.value);
  };

  useEffect(() => {
    if (!typology) {
      return;
    } else {
      if (typology.startsWith("Non-Residential")) {
        setBenchmark({
          "Non-Residential (Generic)": benchmarks["Non-Residential (Generic)"],
          [typology]: benchmarks[typology],
        });
      } else {
        setBenchmark({ [typology]: benchmarks[typology] || {} });
      }
    }
  }, [typology]);
  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-10 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Create a new project</h1>
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
          {/*Input typology type */}
          <div className="mb-4">
            <label
              htmlFor="typology"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Typology
            </label>
            <select
              id="typology"
              value={typology}
              onChange={handleUpdateTypology}
              className="w-full max-w-xs p-2 border border-gray-300 rounded-lg"
            >
              <option value="Residential">Residential</option>
              <option value="Non-residential Generic">
                Non-residential (Generic)
              </option>
              <option value="Non-residential Office">
                Non-residential (Office)
              </option>
              <option value="Non-residential Education">
                Non-residential (Education)
              </option>
              <option value="Non-residential Retail">
                Non-residential (Retail)
              </option>
              <option value="Industrial">Industrial</option>
            </select>
          </div>

          {/*Input Status type */}
          <div className="mb-4">
            <label
              htmlFor="status"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Status
            </label>
            <select
              id="status"
              value={status}
              onChange={handleUpdateStatus}
              className="w-full max-w-xs p-2 border border-gray-300 rounded-lg"
            >
              <option value="Conceptual Design">Conceptual Design</option>
              <option value="Schematic Design">Schematic Design</option>
              <option value="Detailed Design">Detailed Design</option>
              <option value="Construction Evaluation">
                Construction Evaluaton
              </option>
              <option value="Final Assessment">Final Assessment</option>
              <option value="Verification">Verification</option>
            </select>
          </div>

          {/** Upload IFC Section */}
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
              {loading ? "Creating project..." : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
