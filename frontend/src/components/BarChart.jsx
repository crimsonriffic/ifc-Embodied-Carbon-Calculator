import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";
import annotationPlugin from "chartjs-plugin-annotation";
ChartJS.register(
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  annotationPlugin
);

const options = (benchmark) => ({
  responsive: true,
  devicePixelRatio: 3, // Increase this value for better resolution

  maintainAspectRatio: false,

  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        drawBorder: true,
        borderColor: "black",
        borderWidth: 2,
        font: {
          size: 12, // Increase font size for better legibility
        },
      },
    },
    x: {
      grid: {
        drawBorder: true, // Adds a border to X-axis
        borderColor: "black", // Set border color
        borderWidth: 2, // Set border thickness
        display: false,
        font: {
          size: 12, // Increase font size for better legibility
        },
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
    annotation: benchmark
      ? {
          annotations: {
            benchmarkLine: {
              type: "line",
              yMin: benchmark, // Draw the line at the benchmark value
              yMax: benchmark, // Keep the line horizontal
              borderColor: "#A9C0A0", // Line color
              borderWidth: 2, // Line thickness
              label: {
                enabled: true,
                content: "Benchmark", // Display the benchmark value
                position: "center",
                backgroundColor: "rgba(255, 255, 255, 0.8)", // Light background with transparency
                color: "black", // Label text color
              },
            },
          },
        }
      : undefined, // Don't include the annotation plugin if no benchmark is provided
  },
});
export default function BarChart({ data, benchmark = null }) {
  return <Bar data={data} options={options(benchmark)} />;
}
