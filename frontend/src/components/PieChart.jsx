import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

// Register required chart elements
ChartJS.register(ArcElement, Tooltip, Legend);

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "right", // You can change to "bottom", "left", "right"
      labels: {
        padding: 10,
        boxWidth: 12,
        boxHeight: 12,
        usePointStyle: false,
        borderWidth: 0,
      },
    },
  },
  layout: {
    padding: 0, // Removes extra padding around the pie chart
  },
};

export default function PieChart({ data }) {
  return <Pie data={data} options={options} />;
}
