import React from "react";

const HowItWorks = () => {
  const steps = [
    {
      title: "1. Export your BIM model to an IFC file",
      description:
        "Ensure your BIM model follows the CORENETX Code of Practice modeling standards before exporting.",
    },
    {
      title: "2. Create a new project on CarbonSmart",
      description:
        "Provide your project details to track your project information and enable project benchmarking.",
    },
    {
      title: "3. Create a new upload",
      description:
        "Upload the exported IFC file for processing. You may upload multiple file revisions for the project.",
    },
    {
      title: "4. Review your uploaded IFC file",
      description:
        "Review the model data to ensure key elements, quantities, and material assignments have been identified.",
    },
    {
      title: "5. Resolve detected errors",
      description:
        "Errors for missing materials or unsupported elements will be highlighted. Resolve the errors before calculation.",
    },
    {
      title: "6. View your embodied carbon results",
      description:
        "Receive your latest upload’s embodied carbon results. Identify hotspots, compare alternatives, and support low-carbon design decisions.",
    },
  ];

  return (
    <div className=" text-white rounded-lg w-full mt-4 space-y-6">
      {steps.map((step, index) => (
        <div key={index} className="mt-4">
          <h3 className="font-bold text-2xl">{step.title}</h3>
          <p className="text-xl text-gray-100 mt-1">{step.description}</p>
        </div>
      ))}
    </div>
  );
};

export default HowItWorks;
