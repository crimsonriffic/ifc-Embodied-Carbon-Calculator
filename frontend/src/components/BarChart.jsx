import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const options = {
  responsive: true,

  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        drawBorder: true,
        borderColor: "black",
        borderWidth: 2,
      },
    },
    x: {
      grid: {
        drawBorder: true, // Adds a border to X-axis
        borderColor: "black", // Set border color
        borderWidth: 2, // Set border thickness
      },
    },
  },
  plugins: {
    legend: {
      display: false,
      labels: {
        boxWidth: 0,
      },
    },
    tooltip: {
      callbacks: {
        title: () => "", // Remove the title
        label: (tooltipItem) => tooltipItem.raw, // Show only the value
      },
    },
  },
};
export default function BarChart({ data }) {
  return <Bar data={data} options={options} />;
}
