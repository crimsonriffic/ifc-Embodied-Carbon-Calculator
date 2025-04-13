import { useState, useEffect } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import { useUser } from "../context/UserContext";

function LoadingPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [progress, setProgress] = useState(0);
  const { projectId } = location.state;
  const { projectName } = useParams();
  useEffect(() => {
    // Update progress every 50ms for smooth animation
    const interval = setInterval(() => {
      setProgress((prevProgress) => {
        if (prevProgress >= 100) {
          navigate(`/uploadReview/${encodeURIComponent(projectName)}`, {
            state: { projectId },
          });
          clearInterval(interval);
          return 100;
        }
        return prevProgress + 1;
      });
    }, 100); // 50ms * 100 steps = 5000ms (5 seconds)

    // Cleanup interval on component unmount
    return () => clearInterval(interval);
  }, []);
  return (
    // Full-screen background container
    <div
      className="fixed inset-0 w-full h-full bg-cover bg-center flex flex-col items-center justify-center"
      style={{
        backgroundImage: `url('/loadingbg.png')`,
      }}
    >
      {/* Content Container - 30% width and centered */}
      <div className="w-full max-w-lg px-4 mx-auto">
        {" "}
        {/* max-w-lg is about 32rem (~512px) */}
        {/* Icon and Text Container */}
        <div className="flex flex-col items-center gap-2 justify-center">
          {progress <= 33 && (
            <div className="flex flex-col items-center gap-2 justify-center">
              <img
                src="/loadingIcon1.svg"
                alt="CO2 Cloud"
                className="w-80 h-80"
              />
              <p className="text-white text-lg mt-2 text-center">
                <span className="font-bold">Did you know? </span> Embodied
                carbon can make up over 50% of a building's total emissions
                across its lifecycle. That's the carbon footprint before you
                even switch on the lights!
              </p>
            </div>
          )}
          {progress > 33 && progress <= 66 && (
            <div className="flex flex-col items-center gap-2 justify-center">
              <img
                src="/loadingIcon2.svg"
                alt="CO2 Cloud"
                className="w-80 h-80 "
              />

              <p className="text-white text-lg mt-2 text-center">
                <span className="font-bold">Did you know? </span> Conventional
                materials like concrete, steel, and glass are major embodied
                carbon culprits. Swapping one out for another sustainable
                material during design can greatly reduce emissions.
              </p>
            </div>
          )}
          {progress > 66 && (
            <div className="flex flex-col items-center gap-2 justify-center">
              <img
                src="/loadingIcon3.svg"
                alt="CO2 Cloud"
                className="w-80 h-80"
              />

              <p className="text-white text-lg mt-2 text-center">
                <span className="font-bold">Did you know? </span> Unlike
                operational carbon, embodied carbon is locked in from Day 1.
                Once built, there's no going back. That's why early design
                decisions matter so much!
              </p>
            </div>
          )}

          {/* Progress Bar */}
          <div className="w-full h-2 bg-white/30 rounded-full mt-4">
            <div
              className="h-full bg-white rounded-full transition-all  ease-linear"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-white text-base transition-all">
            Calculating... {progress}%
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoadingPage;
