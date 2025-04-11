import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL || "http://localhost:8000", // Replace with your backend's base URL
});
export const getProjectsByUsername = (user_id) => {
  console.log("api.jsx being called");
  return api.get("/projects", { params: { user_id } });
};
export const uploadIfc = async (projectId, file, userId, comments, status) => {
  try {
    // Create FormData to send the file
    const formData = new FormData();
    formData.append("file", file);
    formData.append("comments", comments || "");
    formData.append("status", status || "");
    console.log(
      "The uploadIFC inputs are",
      projectId,
      file,
      userId,
      comments,
      status
    );
    // Upload file using Axios
    const response = await api.post(
      `/projects/${projectId}/upload_ifc`, // Dynamically add project ID
      formData, // Form data with the file
      {
        params: {
          user_id: userId, // Add user ID as a query parameter
        },
        headers: {
          "Content-Type": "multipart/form-data", // Set the correct content type for file uploads
        },
        timeout: 60000,
      }
    );

    return response.data; // Return response from the backend
  } catch (err) {
    console.error("Failed to upload IFC file: ", err);
    throw err; // Re-throw the error for handling in the calling function
  }
};

export const getProjectInfo = async (projectId) => {
  console.log("Projectid at api.jsx is ", projectId);
  return api.get(`/projects/${projectId}/get_project_info`);
};

export const getProjectHistory = async (projectId) => {
  console.log("Projectid at api.jsx is ", projectId);
  return api.get(`/projects/${projectId}/get_history`);
};

export const createProject = async (
  projectName,
  client,
  file,
  userId,
  typology,
  status,
  benchmark
) => {
  console.log("Calling create projects API ");

  //Construct the project data object
  const projectData = {
    project_name: projectName,
    client_name: client,
    typology: typology,
    benchmark: benchmark,
    status: status,
    last_edited_date: new Date().toISOString(), // Current timestamp
    last_edited_user: userId,
    user_job_role: "Senior Architect", // Replace with actual role
    current_version: 0,
    access_control: {
      user123: {
        role: "owner",
        permissions: ["read", "write", "upload", "delete", "admin"],
      },
      john: {
        role: "editer",
        permissions: ["read", "write", "upload"],
      },
      davis: {
        role: "editer",
        permissions: ["read", "write", "upload"],
      },
      vanessa: {
        role: "editer",
        permissions: ["read", "write", "upload"],
      },
    },
    edit_history: [
      {
        timestamp: new Date().toISOString(),
        user: userId,
        action: "created_project",
        description: "Project initialization",
      },
    ],
    ifc_versions: {},
  };
  console.log("Project Data:", projectData);
  try {
    // Send project data to create project
    const response = await api.post("create_project", projectData, {
      headers: {
        "Content-Type": "application/json",
      },
    });
    console.log("Project created successfully: ", response.data);

    // Return the project and file upload response
    return {
      project: response.data,
      // fileUpload: fileResponse.data,
    };
  } catch (err) {
    console.error("Failed to create project: ", err);
    throw err; // Re-throw the error for handling in the calling function
  }
};

export const getProjectBreakdown = async (projectId, versionNumber) => {
  console.log(
    "getProjectBreakdown API is called with  ",
    projectId,
    "and version number ",
    versionNumber
  );
  const versionQuery = versionNumber ? `?version=${versionNumber}` : "";
  return api.get(`/projects/${projectId}/get_breakdown${versionQuery}`);
};

export const getAiBreakdown = async (projectId, versionNumber) => {
  console.log("getAiBreakdown API is called");
  return api.get(
    `/projects/${projectId}/get_breakdown`, // Replace with your API base URL if needed
    {
      params: {
        version: versionNumber || null, // Optional, only if you have a version
        calculation_type: "ai_enhanced", // Specify AI-enhanced calculation
      },
    }
  );
};

export const getMaterialDatabase = async () => {
  console.log("getMaterialDatabase API is called");
  return api.get("/materials");
};

export const uploadMaterial = async (
  userId,
  material_type,
  specified_material,
  density,
  embodied_carbon,
  unit
) => {
  console.log("Calling upload material API");

  //Construct the project data object
  const materialData = {
    material_type: material_type,
    specified_material: specified_material,
    density: density || null,
    embodied_carbon: embodied_carbon || "0.00",
    unit: unit,
    database_source: "Custom",
  };
  console.log("Material Data:", materialData);
  try {
    // Send project data to create project
    const response = await api.post(
      `materials?user_id=${userId}`,
      materialData,
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    console.log("Material Uploaded successfully: ", response.data);

    // Return the project and file upload response
    return response.data;
  } catch (err) {
    console.error("Failed to upload material: ", err);
    throw err; // Re-throw the error for handling in the calling function
  }
};

export const uploadMaterialAndQueue = async (
  projectId,
  userId,
  material_type,
  specified_material,
  density,
  embodied_carbon,
  unit,
  version = null // Optional parameter
) => {
  console.log("Calling upload material and queue API");

  // Construct the material data object
  const materialData = {
    material_type: material_type,
    specified_material: specified_material,
    density: density || null,
    embodied_carbon: embodied_carbon || "0.00",
    unit: unit,
    database_source: "Custom",
  };

  console.log("Material Data:", materialData);

  try {
    // Build the query parameters
    const queryParams = new URLSearchParams({ user_id: userId });
    if (version) {
      queryParams.append("version", version); // Add version if provided
    }

    // Send the material data to the API
    const response = await api.post(
      `projects/${projectId}/materials?${queryParams.toString()}`,
      materialData,
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    console.log("Material uploaded and queued successfully:", response.data);

    // Return the response data
    return response.data;
  } catch (err) {
    console.error("Failed to upload material and queue recalculation:", err);
    throw err; // Re-throw the error for handling in the calling function
  }
};
export const getMaterialsDetected = async (
  projectId = null,
  version = null
) => {
  console.log("getMaterialsDetected API is called");
  // Build query paramters
  const params = new URLSearchParams();
  if (projectId) params.append("project_id", projectId);
  if (version) params.append("version", version);

  // Convert params string and add to URL
  const queryString = params.toString();
  const url = `/materials${queryString ? `?${queryString}` : ""}`;
  return api.get(url);
};

export const getElementsDetected = async (ifc_path = null) => {
  console.log("getElementsDetected API is called with, ", ifc_path);
  if (!ifc_path) return null;
  // Create URL with properly encoded parameter
  const params = new URLSearchParams();
  params.append("ifc_path", ifc_path);

  const url = `/ifc/elements?${params.toString()}`;
  console.log("Requesting URL:", url);
  return api.get(url);
};

export const getMissingElements = async (projectId) => {
  console.log("getMissingElements API is called with, ", projectId);
  return api.get(`/projects/${projectId}/missing_elements`);
};

export const getMissingMaterials = async (projectId) => {
  console.log("getMissingMaterials API is called with, ", projectId);
  return api.get(`/projects/${projectId}/missing_materials`);
};

export const getBuildingElements = async (projectId) => {
  console.log("getBuildingElements API is called");
  return api.get(`/projects/${projectId}/get_building_elements`, {
    responseType: "blob", // Important to handle binary data
  });
};
