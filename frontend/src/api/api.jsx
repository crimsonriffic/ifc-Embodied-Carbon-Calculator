import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000", // Replace with your backend's base URL
});
export const getProjectsByUsername = (user_id) => {
  console.log("api.jsx being called");
  return api.get("/projects", { params: { user_id } });
};
export const uploadIfc = async (
  projectId,
  file,
  userId,
  comments,
  updateType
) => {
  try {
    // Create FormData to send the file
    const formData = new FormData();
    formData.append("file", file);
    formData.append("comments", comments);
    formData.append("update_type", updateType);
    console.log(
      "The uploadIFC inputs are",
      projectId,
      file,
      userId,
      comments,
      updateType
    );
    // Upload file using Axios
    const response = await axios.post(
      `http://localhost:8000/projects/${projectId}/upload_ifc`, // Dynamically add project ID
      formData, // Form data with the file
      {
        params: {
          user_id: userId, // Add user ID as a query parameter
        },
        headers: {
          "Content-Type": "multipart/form-data", // Set the correct content type for file uploads
        },
      }
    );

    return response.data; // Return response from the backend
  } catch (err) {
    console.error("Failed to upload IFC file: ", err);
    throw err; // Re-throw the error for handling in the calling function
  }
};

export const getBuildingInfo = async (projectId) => {
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
  status
) => {
  console.log("Calling create projects API");

  //Construct the project data object
  const projectData = {
    project_name: projectName,
    client_name: client,
    typology: typology,
    status: status,
    last_edited_date: new Date().toISOString(), // Current timestamp
    last_edited_user: userId,
    user_job_role: "Senior Architect", // Replace with actual role
    current_version: 1,
    access_control: {
      user123: {
        role: "owner",
        permissions: ["read", "write", "upload", "delete", "admin"],
      },
      user789: {
        role: "viewer",
        permissions: ["read"],
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
    const response = await axios.post(
      `http://localhost:8000/create_project`,
      projectData,
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    console.log("Project created successfully: ", response.data);

    // Extract the project Id from the response
    const projectId = response.data._id;
    // Call the upload IFC file api

    const formData = new FormData();
    formData.append("file", file);
    console.log("The uploadIFC inputs are", projectId, file, userId);
    // Upload file using Axios
    const fileResponse = await axios.post(
      `http://localhost:8000/projects/${projectId}/upload_ifc`, // Dynamically add project ID
      formData, // Form data with the file
      {
        params: {
          user_id: userId, // Add user ID as a query parameter
        },
        headers: {
          "Content-Type": "multipart/form-data", // Set the correct content type for file uploads
        },
      }
    );
    console.log("File uploaded successfully:", fileResponse.data);

    // Return the project and file upload response
    return {
      project: response.data,
      fileUpload: fileResponse.data,
    };
  } catch (err) {
    console.error("Failed to create project: ", err);
    throw err; // Re-throw the error for handling in the calling function
  }
};

export const getProjectBreakdown = async (projectId) => {
  console.log("getProjectBreakdown API is called with  ", projectId);
  return api.get(`/projects/${projectId}/get_breakdown`);
};
