import { Link, useParams, useLocation, useNavigate } from "react-router-dom";

function Stepper({ currentStep }) {
  const navigate = useNavigate();
  const { projectName } = useParams();
  const location = useLocation();
  const { projectId } = location.state || {}; // Ensure projectId is available
  const steps = [
    { id: 1, name: "Project Information" },
    { id: 2, name: "Upload Information" },
    { id: 3, name: "Upload Review" },
    { id: 4, name: "Error Handling" },
    { id: 5, name: "View Results" },
  ];
  const handleClick = (stepId) => {
    console.log("HandleClick called with ", stepId);
    switch (stepId) {
      case 1:
        navigate(`/projectInfo/${encodeURIComponent(projectName)}`, {
          state: { projectId },
        });
        break;
      case 2:
        navigate(`/uploadHistory/${encodeURIComponent(projectName)}`, {
          state: { projectId },
        });
        break;
      case 3:
        navigate(`/uploadReview/${encodeURIComponent(projectName)}`, {
          state: { projectId },
        });
        break;
      case 4:
        navigate(`/errorHandling/${encodeURIComponent(projectName)}`, {
          state: { projectId },
        });
        break;
      case 5:
        navigate(`/project/${encodeURIComponent(projectName)}`, {
          state: { projectId },
        });
        break;
    }
  };
  return (
    <div className="flex items-center justify-between w-full max-w-3xl mx-auto">
      {steps.map((step, index) => (
        <div key={step.id} className="relative flex flex-col items-center">
          {/*Step Circle*/}

          <button
            className={`z-10 w-8 h-8 flex items-center justify-center rounded-full text-white font-bold 
                        ${
                          currentStep >= step.id
                            ? "bg-[#5B9130]"
                            : "bg-gray-300"
                        }
                      `}
            onClick={() => {
              handleClick(step.id);
            }}
          >
            {step.id}
          </button>
          {/* Step Name */}
          <span className="text-sm text-gray-800 whitespace-nowrap">
            {step.name}
          </span>

          {/** Step Line */}
          {index < steps.length - 1 && (
            <div
              className={`absolute h-0.5 top-4 -translate-y-1/2 z-0
                ${currentStep > step.id ? "bg-[#5B9130]" : "bg-gray-300"}
              `}
              style={{
                left: "50%",
                width: "calc(100% + 50px)",
              }}
            />
          )}
        </div>
      ))}
    </div>
  );
}

export default Stepper;
