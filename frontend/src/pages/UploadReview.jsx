import Navbar from "../components/NavBar";
import Stepper from "../components/Stepper";
import {
  getProjectHistory,
  uploadIfc,
  getProjectInfo,
  getMaterialsDetected,
  getElementsDetected,
} from "../api/api";

import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import LoadingPage from "./LoadingPage";

function UploadReview() {
  const [versionNumber, setVersionNumber] = useState("");
  const [materialsDetected, setMaterialsDetected] = useState([]);
  const [elementsDetected, setElementsDetected] = useState({});
  const [loading, setLoading] = useState(true); // Single loading state

  const [error, setError] = useState(null);
  const [projectInfo, setProjectInfo] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { projectId } = location.state;
  const { projectName } = useParams();
  useEffect(() => {
    // 7-second loading screen
    const timer = setTimeout(() => {
      setLoading(false);
    }, 10000);
    return () => clearTimeout(timer);
  }, []);
  /* Initial API calls to fetch project history and breakdown data */
  useEffect(() => {
    const fetchData = async () => {
      try {
        const projectResponse = await getProjectInfo(projectId);

        console.log("Project Info response data is: ", projectResponse.data);
        console.log("IFC Path:", projectResponse.data.file_path); // Debug log

        setProjectInfo(projectResponse.data);
        setError(null);
      } catch (err) {
        console.error("Failed to data: ", err);
        setError("Failed to fetch data."); // Set error message
      }
    };
    if (projectId) {
      fetchData();
    }
  }, [projectId]);
  useEffect(() => {
    if (!projectInfo) return;

    console.log("Project Info state is ", projectInfo.file_path);
    // setLoading(true);
    const fetchDetected = async () => {
      try {
        const versionedMaterialResponse = await getMaterialsDetected(
          projectId,
          projectInfo.latest_version
        );

        const elementsDetectedResponse = await getElementsDetected(
          projectInfo.file_path
        );
        console.log(
          "Materials Detected response data is: ",
          versionedMaterialResponse.data
        );
        console.log(
          "Elements Detected response data is: ",
          elementsDetectedResponse.data
        );
        setMaterialsDetected(versionedMaterialResponse.data);
        setElementsDetected(elementsDetectedResponse.data.elements);
        setError(null);
      } catch (err) {
        console.error("Failed to data: ", err);
        setError("Failed to fetch data."); // Set error message
      } finally {
        setLoading(false); // Set loading to false after data is fetched
      }
    };
    if (projectInfo) fetchDetected();
  }, [projectInfo]);
  if (loading) {
    // Show loading page while loading
    return <LoadingPage />;
  }
  return (
    <div className="px-6">
      <Navbar />

      {/* Banner Section */}
      <div className="bg-[#5B9130] text-white mx-8 mt-20 w-full mr-4 py-6 px-6 rounded-lg shadow-md text-left ml-0">
        <h1 className="text-3xl font-bold">Upload Review</h1>
        <p className="mt-2 text-lg">
          Please review the information and error handling of your uploaded
          model.
        </p>
      </div>
      <div className="mt-6">
        <Stepper currentStep={3} />
      </div>
      <div className="bg-[#A9C0A0] text-white rounded-lg px-4 py-2 flex items-center shadow-md mt-4 mb-6 sm:max-w-md">
        <h1 className="text-2xl font-semibold tracking-wide">
          {decodeURIComponent(projectName)}
        </h1>
      </div>
      <div className="flex flex-row space-x-8">
        <div className=" flex flex-col w-1/3 min-w-[200px] gap-y-4">
          <h1 className="text-2xl font-bold">
            Upload {projectInfo.latest_version}
          </h1>
          <div>
            <h1 className="text-sm">Detected Elements </h1>
            <p className=" text-xl font-bold ">
              {loading
                ? "Loading..."
                : `${Object.keys(elementsDetected).length} elements`}
            </p>
          </div>

          <div>
            <h1 className="text-sm">Detected Materials</h1>
            <p className=" text-xl font-bold">
              {loading
                ? "Loading..."
                : `${materialsDetected.length} material types`}
            </p>
          </div>
        </div>
        {/**Elements Detected Table */}
        <div className="flex flex-col">
          <h1 className="text-2xl font-bold mt-10 mb-4"> Detected Elements</h1>

          <div className="overflow-x-auto h-96">
            <table className="min-w-full border relative border-gray-300 bg-white shadow-md rounded-lg">
              <thead className="bg-gray-100 sticky top-0">
                <tr>
                  <th className="border border-gray-300 px-4 py-2">
                    IfcElement
                  </th>
                  <th className="border border-gray-300 px-4 py-2">Quantity</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td
                      className="border border-gray-300 px-4 py-2 text-center"
                      colSpan="3"
                    >
                      Loading...
                    </td>
                  </tr>
                ) : (
                  Object.entries(elementsDetected).map(
                    ([element, count], index) => (
                      <tr className="border-b" key={index}>
                        <td className="border border-gray-300 px-4 py-2 text-center">
                          {element}
                        </td>
                        <td className="border border-gray-300 px-4 py-2">
                          {count}
                        </td>
                      </tr>
                    )
                  )
                )}
              </tbody>
            </table>
          </div>
        </div>
        {/**Materials Detected Table */}
        <div className="flex flex-col">
          <h1 className="text-2xl font-bold mt-10 mb-4">
            {" "}
            Detected Product Materials
          </h1>
          <div className="overflow-x-auto h-96">
            <table className="min-w-full border relative border-gray-300 bg-white shadow-md rounded-lg">
              <thead className="bg-gray-100 sticky top-0">
                <tr>
                  <th className="border border-gray-300 px-4 py-2">Family</th>
                  <th className="border border-gray-300 px-4 py-2">Type</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td
                      className="border border-gray-300 px-4 py-2 text-center"
                      colSpan="3"
                    >
                      Loading...
                    </td>
                  </tr>
                ) : (
                  Object.entries(materialsDetected).map(
                    ([key, value], index) => (
                      <tr className="border-b" key={index}>
                        <td className="border border-gray-300 px-4 py-2 text-center">
                          {value.material_type}
                        </td>
                        <td className="border border-gray-300 px-4 py-2">
                          {value.specified_material}
                        </td>
                      </tr>
                    )
                  )
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UploadReview;
