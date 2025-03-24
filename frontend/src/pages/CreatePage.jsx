import Navbar from "../components/NavBar";
import Stepper from "../components/Stepper";

import { getBuildingInfo } from "../api/api";

import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { useUser } from "../context/UserContext";

import { createProject } from "../api/api";

function CreatePage() {
  const [projectName, setProjectName] = useState("");
  const [client, setClient] = useState("");
  const [typology, setTypology] = useState("");
  const [status, setStatus] = useState("");
  const [benchmark, setBenchmark] = useState({});
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false); // Loading state

  const { username } = useUser();
  const navigate = useNavigate();

  const handleProceed = (projectId, projectName) => {
    console.log("HandleProceed called");
    navigate(`/uploadHistory/${encodeURIComponent(projectName)}`, {
      state: { projectId },
    });
  };

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
      console.log("Successfully created project: ", response.project);
      navigate(`/uploadHistory/${encodeURIComponent(projectName)}`, {
        state: { projectId: response.project._id },
      });
    } catch (err) {
      console.error("Faild to create project", err);
      alert("Failed to create projec!");
    } finally {
      setLoading(false);
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
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Project Information</h1>
        <p>Please enter the relevant information for your project</p>
      </div>
      <div className="mt-6">
        <Stepper currentStep={1} />
      </div>
      <div className="bg-[#A9C0A0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mt-4 mb-6 sm:max-w-md">
        <h1 className="text-2xl font-semibold tracking-wide">
          {projectName ? decodeURIComponent(projectName) : "New Project"}
        </h1>
      </div>
      <div className="flex flex-row gap-x-32">
        {/* Create project form */}
        {/*Upload form */}
        <div className="flex flex-col max-w-md">
          {/** New Upload section*/}
          <h1 className="text-2xl font-semibold tracking-wide mb-2">
            Create New Project
          </h1>
          <form onSubmit={handleUpload} className="space-y-8">
            <div className="max-w-md">
              <label htmlFor="projectName" className="block text-gray-700 mb-1">
                Project Name
              </label>
              <input
                type="text"
                id="projectName"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="Enter Project Name"
                className="p-2 border w-80 border-gray-200 shadow-md"
                required
              />
            </div>

            <div className="max-w-md">
              <label htmlFor="clientName" className="block text-gray-700 mb-1">
                Client Name
              </label>
              <input
                type="text"
                id="client"
                value={client}
                onChange={(e) => setClient(e.target.value)}
                placeholder="Enter Client"
                className="p-2 border w-80 border-gray-200 shadow-md"
                required
              />
            </div>

            <div className="max-w-md">
              <label htmlFor="typology" className="block text-gray-700 mb-1">
                Typology
              </label>
              <select
                id="typology"
                value={typology}
                onChange={handleUpdateTypology}
                className="w-full max-w-xs p-2 border border-gray-200 shadow-md"
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

            <div className="max-w-md">
              <label htmlFor="status" className="block text-gray-700 mb-1">
                Status
              </label>
              <select
                id="status"
                value={status}
                onChange={handleUpdateStatus}
                className="w-full max-w-xs p-2 border border-gray-200 shadow-md"
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

            <button className="px-4 py-2 bg-[#5B9130] text-white rounded">
              {loading ? "Creating project..." : "Create Project"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default CreatePage;
