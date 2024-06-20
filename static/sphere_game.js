import * as THREE from 'https://cdn.skypack.dev/three@0.128.0';
import { OrbitControls } from 'https://cdn.skypack.dev/three@0.128.0/examples/jsm/controls/OrbitControls.js';

let scene, camera, renderer, controls, soccerBall, geometry, edges, material, lineMaterial;
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();
let startFaceIndex, finishFaceIndex;
let coloredFaces = new Set();
let vertexA = new THREE.Vector3();
let vertexB = new THREE.Vector3();
let vertexC = new THREE.Vector3();

function init() {
    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xffffff);

    // Camera setup
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 5;

    // Renderer setup
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    // Controls setup
    controls = new OrbitControls(camera, renderer.domElement);

    // Soccer ball geometry
    const radius = 1;
    const detail = 1;
    geometry = new THREE.IcosahedronBufferGeometry(radius, detail).toNonIndexed();

    // Material
    material = new THREE.MeshStandardMaterial({
        vertexColors: true,
        flatShading: true
    });

    // Initialize all vertices to white
    const white = new THREE.Color(0xffffff);
    const colors = [];
    for (let i = 0; i < geometry.attributes.position.count; i++) {
        colors.push(white.r, white.g, white.b);
    }
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

    // Mesh
    soccerBall = new THREE.Mesh(geometry, material);

    // Create wireframe for the edges
    const wireframe = new THREE.WireframeGeometry(geometry);
    lineMaterial = new THREE.LineBasicMaterial({ color: 0x000000 });
    edges = new THREE.LineSegments(wireframe, lineMaterial);

    scene.add(soccerBall);
    scene.add(edges);

    // Lighting
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(5, 5, 5).normalize();
    scene.add(light);

    const ambientLight = new THREE.AmbientLight(0x404040,2);
    scene.add(ambientLight);

    // Select start and finish hexagons
    selectStartAndFinish();

    // Resize handler
    window.addEventListener('resize', onWindowResize);

    // Mouse click event
    window.addEventListener('click', onMouseClick);

    //Touch end event
    window.addEventListener('touchend', onTouchEnd);

    animate();
}

function selectStartAndFinish() {
    const faceCount = geometry.attributes.position.count / 3;
    startFaceIndex = Math.floor(Math.random() * faceCount);
    do {
        finishFaceIndex = Math.floor(Math.random() * faceCount);
    } while (finishFaceIndex === startFaceIndex);

    // Color the start face green
    colorFace(startFaceIndex, new THREE.Color(0x00ff00));
    coloredFaces.add(startFaceIndex);

    // Color the finish face red
    colorFace(finishFaceIndex, new THREE.Color(0xff0000));
}

function colorFace(faceIndex, color) {
    const colorArray = geometry.attributes.color.array;
    for (let i = 0; i < 3; i++) {
        const vertexIndex = faceIndex * 3 + i;
        color.toArray(colorArray, vertexIndex * 3);
    }
    geometry.attributes.color.needsUpdate = true;
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function onMouseClick(event) {
    // Convert mouse position to normalized device coordinates
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    // Raycast to find intersected objects
    raycaster.setFromCamera(mouse, camera);
    TriangleActivation(raycaster)


}

function onTouchEnd(event) {
    // Convert mouse position to normalized device coordinates
    mouse.x = (event.changedTouches[0].clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.changedTouches[0].clientY / window.innerHeight) * 2 + 1;

    // Raycast to find intersected objects
    raycaster.setFromCamera(mouse, camera);
    TriangleActivation(raycaster)


}

function TriangleActivation(raycaster)
{
    const intersects = raycaster.intersectObject(soccerBall);
    if (intersects.length > 0) {
        const intersect = intersects[0];
        const faceIndex = intersect.faceIndex;

        // Check if the face is not the start or finish face and is adjacent to a colored face
        if (faceIndex !== startFaceIndex && faceIndex !== finishFaceIndex && isAdjacentToColoredFace(faceIndex)) {
            // Color the clicked face yellow
            colorFace(faceIndex, new THREE.Color(0xffff00));
            coloredFaces.add(faceIndex);

            // Check if the newly colored face is adjacent to the finish face
            if (isAdjacentToFace(faceIndex, finishFaceIndex)) {
                // End the game and show the popup
                setTimeout(() => {
                    if (confirm("You reached the finish! Do you want to play again?")) {
                        resetGame();
                    }
                }, 100);
            }
        }
    }
}

function isAdjacentToColoredFace(faceIndex) {
    const positionsAttr = geometry.attributes.position;
    const currentFaceVertices = [];

    // Get the vertices of the current face
    for (let i = 0; i < 3; i++) {
        const vertexIndex = faceIndex * 3 + i;
        currentFaceVertices.push(new THREE.Vector3(
            positionsAttr.getX(vertexIndex),
            positionsAttr.getY(vertexIndex),
            positionsAttr.getZ(vertexIndex)
        ));
    }

    for (let coloredFaceIndex of coloredFaces) {
        let sharedVerticesCount = 0;

        // Get vertices of the colored face
        const coloredFaceVertices = [];
        for (let i = 0; i < 3; i++) {
            const vertexIndex = coloredFaceIndex * 3 + i;
            coloredFaceVertices.push(new THREE.Vector3(
                positionsAttr.getX(vertexIndex),
                positionsAttr.getY(vertexIndex),
                positionsAttr.getZ(vertexIndex)
            ));
        }

        // Check if the current face shares an edge with the colored face
        for (const currentVertex of currentFaceVertices) {
            for (const coloredVertex of coloredFaceVertices) {
                if (currentVertex.distanceTo(coloredVertex) < 0.01) {
                    sharedVerticesCount++;
                }
            }
        }

        // If at least two vertices are shared, the faces share an edge
        if (sharedVerticesCount >= 2) {
            return true;
        }
    }

    return false;
}

function isAdjacentToFace(faceIndex, targetFaceIndex) {
    const positionsAttr = geometry.attributes.position;
    const currentFaceVertices = [];
    const targetFaceVertices = [];

    // Get the vertices of the current face
    for (let i = 0; i < 3; i++) {
        const vertexIndex = faceIndex * 3 + i;
        currentFaceVertices.push(new THREE.Vector3(
            positionsAttr.getX(vertexIndex),
            positionsAttr.getY(vertexIndex),
            positionsAttr.getZ(vertexIndex)
        ));
    }

    // Get the vertices of the target face
    for (let i = 0; i < 3; i++) {
        const vertexIndex = targetFaceIndex * 3 + i;
        targetFaceVertices.push(new THREE.Vector3(
            positionsAttr.getX(vertexIndex),
            positionsAttr.getY(vertexIndex),
            positionsAttr.getZ(vertexIndex)
        ));
    }

    let sharedVerticesCount = 0;

    // Check if the current face shares an edge with the target face
    for (const currentVertex of currentFaceVertices) {
        for (const targetVertex of targetFaceVertices) {
            if (currentVertex.distanceTo(targetVertex) < 0.001) {
                sharedVerticesCount++;
            }
        }
    }

    // If at least two vertices are shared, the faces share an edge
    return sharedVerticesCount >= 2;
}

function resetGame() {
    coloredFaces.clear();

    // Reset the colors of all faces to white
    const white = new THREE.Color(0xffffff);
    const colorArray = geometry.attributes.color.array;
    for (let i = 0; i < colorArray.length; i += 3) {
        white.toArray(colorArray, i);
    }
    geometry.attributes.color.needsUpdate = true;

    // Select new start and finish faces
    selectStartAndFinish();
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}











init();
