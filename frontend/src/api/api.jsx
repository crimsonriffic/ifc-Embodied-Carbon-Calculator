export async function getProjectsByUsername() {
  return new Promise((resolve) => {
    console.log("Calling getProjects api");
    setTimeout(() => {
      resolve([
        {
          projectName: "The Pinnacle @Duxton",
          clientName: "HDB",
          latestUpdate: "16/01/2025, John (Archi)",
          filepath: "",
        },
        {
          projectName: "The Interlace",
          clientName: "Capitaland Residential Limited",
          latestUpdate: "11/01/2025, Dave (C&S)",
          filepath: "dfasf",
        },
        {
          projectName: "Jewel Changi Airport",
          clientName: "Changi Airport Group",
          latestUpdate: "10/01/2025, Alice (Archi)",
          filepath: "",
        },
        {
          projectName: "Habitat 67",
          clientName: "Expo 67",
          latestUpdate: "09/01/2025, Jane (ESD)",
          filepath: "",
        },
        {
          projectName: "The Eden Project",
          clientName: "Eden Trust",
          latestUpdate: "06/01/2025, KW (C&S)",
          filepath: "",
        },
        {
          projectName: "Surbana Jurong Campus",
          clientName: "Surbana Jurong",
          latestUpdate: "04/01/2025, Sarah (Archi)",
          filepath: "",
        },
        {
          projectName: "DUO Tower",
          clientName: "M+S Pte Ltd",
          latestUpdate: "03/01/2025, Phoebe (C&S)",
          filepath: "",
        },
        {
          projectName: "NEX",
          clientName: "Gold Ridge Pte Ltd",
          latestUpdate: "03/01/2025, Sean (M&E)",
          filepath: "",
        },
        {
          projectName: "Punggol Waterway Terraces",
          clientName: "HDB",
          latestUpdate: "02/01/2025, Ray (ESD)",
          filepath: "",
        },
        {
          projectName: "Neptune Court",
          clientName: "SAF NCO Club",
          latestUpdate: "30/12/2024, JK (M&E)",
          filepath: "",
        },
        {
          projectName: "Tengah Garden Vines",
          clientName: "HDB",
          latestUpdate: "29/12/2024, JJ (Archi)",
          filepath: "",
        },
      ]);
    }, 1000); // Simulate a 1-second delay
  });
}

export function uploadIfc({ updateType, inputComment, file }) {
  console.log(
    `Calling uploadIfc API where updateType: "${updateType}" and inputComment: "${inputComment} and file: ${file}"`
  );
}

export async function getProjectDetails({ projectId }) {
  console.log("Project id is ", projectId);
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        total_ec: "5000",
        gfa: "1",
        typology: "Cool",
        phase: "A",
        cost: "$2000",
      });
    }, 1000);
  });
}
