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
  legend: {
    display: false,
  },
  scales: {
    y: {
      beginAtZero: true,
    },
  },
  plugins: {
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
