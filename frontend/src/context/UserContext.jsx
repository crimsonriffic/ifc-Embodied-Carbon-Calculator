import { createContext, useContext, useState } from "react";
const UserContext = createContext(); // creates a context that acts as a global state

// Create a custom hook to acess the usercontext
export const useUser = () => useContext(UserContext);

// Create the Provider component
export const UserProvider = ({ children }) => {
  const [username, setUsername] = useState(null);
  return (
    <UserContext.Provider value={{ username, setUsername }}>
      {children}
    </UserContext.Provider>
  );
};
