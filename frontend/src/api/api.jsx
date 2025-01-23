import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000", // Replace with your backend's base URL
});
export const getProjectsByUsername = (user_id) => {
  return api.get("/projects", { params: { user_id } });
};
export const uploadIfc = async (projectId, file, userId) => {
  try {
    // Create FormData to send the file
    const formData = new FormData();
    formData.append("file", file);
    console.log("The uploadIFC inputs are", projectId, file, userId);
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
