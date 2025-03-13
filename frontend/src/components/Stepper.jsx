const steps = [
  { id: 1, name: "Project Information" },
  { id: 2, name: "Upload Information" },
  { id: 3, name: "Material Information" },
  { id: 4, name: "Upload Confirmation" },
  { id: 5, name: "View Results" },
];

const Stepper = ({ currentStep }) => {
  return (
    <div className="flex items-center justify-between w-full max-w-3xl mx-auto">
      {steps.map((step, index) => (
        <div key={step.id} className="relative flex flex-col items-center">
          {/*Step Circle*/}

          <div
            className={`z-10 w-8 h-8 flex items-center justify-center rounded-full text-white font-bold 
                        ${
                          currentStep >= step.id
                            ? "bg-green-500"
                            : "bg-gray-300"
                        }
                      `}
          >
            {step.id}
          </div>
          {/* Step Name */}
          <span className="text-sm text-gray-800 whitespace-nowrap">
            {step.name}
          </span>

          {/** Step Line */}
          {index < steps.length - 1 && (
            <div
              className={`absolute h-0.5 top-4 -translate-y-1/2 z-0
                ${currentStep > step.id ? "bg-green-500" : "bg-gray-300"}
              `}
              style={{
                left: "50%",
                width: "calc(100% + 32px)",
              }}
            />
          )}
        </div>
      ))}
    </div>
  );
};

export default Stepper;
