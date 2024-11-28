console.log(window.IFC ? "IFC.js loaded" : "IFC.js not loaded");

document.addEventListener("DOMContentLoaded", function () {
    const dropzone = document.getElementById("dropzone");
    const viewer = document.getElementById("viewer");
    const renderer = new THREE.WebGLRenderer({ canvas: viewer });
    renderer.setSize(viewer.clientWidth, viewer.clientHeight);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xaaaaaa); // Light grey background
    const camera = new THREE.PerspectiveCamera(75, viewer.clientWidth / viewer.clientHeight, 0.1, 1000);

    const light = new THREE.DirectionalLight(0xffffff, 1); // White light
    light.position.set(10, 10, 10); // Position the light
    scene.add(light);

    camera.position.z = 5;

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.style.backgroundColor = "#f0f0f0";
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.style.backgroundColor = "#fff";
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.style.backgroundColor = "#fff";
        const file = e.dataTransfer.files[0];
        processIFCFile(file);
    });

    dropzone.addEventListener("click", () => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".ifc";
        input.onchange = (e) => {
            const file = e.target.files[0];
            processIFCFile(file);
        };
        input.click();
    });

    function processIFCFile(file) {
        const reader = new FileReader();
        reader.onload = async function (event) {
            const arrayBuffer = event.target.result;

            // Load the IFC model using IFC.js
            const loader = new window.IFC.IFCViewerAPI({ container: viewer });
            const model = await loader.IFC.loadIfc(new Uint8Array(arrayBuffer));

            // Add the model to the scene
            scene.add(model);

            // Adjust the camera to fit the model
            loader.cameraControls.fitToFrame();
        };
        reader.readAsArrayBuffer(file);
    }

    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }

    animate();
});
