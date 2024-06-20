import * as THREE from 'https://cdn.skypack.dev/three@0.128.0';
import { OrbitControls } from 'https://cdn.skypack.dev/three@0.128.0/examples/jsm/controls/OrbitControls.js';

let scene, camera, renderer, controls, soccerBall, geometry, edges, material, lineMaterial;
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();
let startFaceIndex, finishFaceIndex;
let coloredFaces = [];
let vertexA = new THREE.Vector3();
let vertexB = new THREE.Vector3();
let vertexC = new THREE.Vector3();
//let openSet = []; //array containing unevaluated faces
//let closedSet = []; //array containing completely evaluated faces
let faceNeighbors = [];
let pathFaces = new Set();
let shortestPath = [];
let obstacles = [];
let radius, detail;
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
    initShape('icosahedron', 1, 1)

    // Resize handler
    window.addEventListener('resize', onWindowResize);

    // Mouse click event
    window.addEventListener('click', onMouseClick);

    //Touch end event
    window.addEventListener('touchend', onTouchEnd);


    animate();
}

function initShape(shape, radius, detail){

    switch (shape) {
      case 'icosahedron':
        geometry = new THREE.IcosahedronBufferGeometry(radius, detail);
        break;
      case 'dodecahedron':
        geometry = new THREE.DodecahedronGeometry(radius, detail).toNonIndexed();
        break;
      case 'octahedron':
        geometry = new THREE.OctahedronGeometry(radius, detail).toNonIndexed();
        break;
      case 'tetrahedron':
        geometry = new THREE.TetrahedronGeometry(radius, detail).toNonIndexed();
        break;
      default:
        console.log('Error, please select a valid shape');
    }

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

    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);

    // Select start and finish hexagons
    selectStartAndFinish();


}
function selectStartAndFinish() {
    const faceCount = geometry.attributes.position.count / 3;
    startFaceIndex = Math.floor(Math.random() * faceCount);
    do {
        finishFaceIndex = Math.floor(Math.random() * faceCount);
    } while (finishFaceIndex === startFaceIndex || isAdjacentToFace(finishFaceIndex, startFaceIndex));

    // Color the start face green
    colorFace(startFaceIndex, new THREE.Color(0x00ff00));
    coloredFaces.push(startFaceIndex);

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
//    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
//    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ( ( event.clientX - rect.left ) / ( rect.right - rect.left ) ) * 2 - 1;
    mouse.y = - ( ( event.clientY - rect.top ) / ( rect.bottom - rect.top) ) * 2 + 1;
    // Raycast to find intersected objects
    raycaster.setFromCamera(mouse, camera);
    TriangleActivation(raycaster)


}

function onTouchEnd(event) {
    // Convert mouse position to normalized device coordinates
    //mouse.x = (event.changedTouches[0].clientX / window.innerWidth) * 2 - 1;
    //mouse.y = -(event.changedTouches[0].clientY / window.innerHeight) * 2 + 1;
        const rect = renderer.domElement.getBoundingClientRect();

    mouse.x = ( ( event.changedTouches[0].clientX - rect.left ) / ( rect.right - rect.left ) ) * 2 - 1;
    mouse.y = - ( ( event.changedTouches[0].clientY- rect.top ) / ( rect.bottom - rect.top) ) * 2 + 1;


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

        //debug
        console.log(faceIndex)


        // Check if the face is not the start or finish face and is adjacent to a colored face
        if (faceIndex !== startFaceIndex && faceIndex !== finishFaceIndex) {
            // Color the clicked face yellow
            if(coloredFaces.includes(faceIndex)){
                coloredFaces.splice(coloredFaces.indexOf(faceIndex),1);
                colorFace(faceIndex, new THREE.Color(0xffffff))
            }else{
                colorFace(faceIndex, new THREE.Color(0x000000));
                coloredFaces.push(faceIndex);
            }


        }
    }
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

function clearGame() {
    coloredFaces = [];
    faceNeighbors = [];
    const faceCount = geometry.attributes.position.count / 3;

    // Reset the colors of all faces to white
    const white = new THREE.Color(0xffffff);

    for(let i = 0; i < faceCount; i++){
        if(i !== startFaceIndex && i !== finishFaceIndex){
            colorFace(i, white)
        }
    }

    // Select new start and finish faces

}

function resetGame() {
    coloredFaces = [];
    faceNeighbors = [];
    const faceCount = geometry.attributes.position.count / 3;

    // Reset the colors of all faces to white
    const white = new THREE.Color(0xffffff);

    for(let i = 0; i < faceCount; i++){
            colorFace(i, white)
    }

    selectStartAndFinish();
}

function search() {
    const openSet = new Set([startFaceIndex]);
    const cameFrom = [];
    pathFaces.clear();
    const gScore = [];
    const fScore = [];

    const faceCount = geometry.attributes.position.count / 3;

    for (let i = 0; i < faceCount; i++) {
        gScore[i] = Infinity;
        fScore[i] = Infinity;
    }

    gScore[startFaceIndex] = 0;
    fScore[startFaceIndex] = heuristic(startFaceIndex, finishFaceIndex);

    while (openSet.size > 0) {
        let current = null;
        let currentFScore = Infinity;

        // Find the node in openSet with the lowest fScore
        for (let face of openSet) {
            if (fScore[face] < currentFScore) {
                currentFScore = fScore[face];
                current = face;
            }
        }

        if (current === finishFaceIndex) {
            return reconstructPath(cameFrom, current);
        }

        openSet.delete(current);

        const neighbors = faceNeighbors[current];
        for (let neighbor of neighbors) {
//            if (cameFrom.includes(neighbor)) {
//                continue; // Skip if neighbor is part of the pathFaces
//            }

            // Calculate tentative gScore for neighbor
            const tentativeGScore = gScore[current] + 1;

            if (tentativeGScore < gScore[neighbor]) {
                // This path to neighbor is better than any previous one
                cameFrom[neighbor] = current;
                gScore[neighbor] = tentativeGScore;
                fScore[neighbor] = gScore[neighbor] + heuristic(neighbor, finishFaceIndex);

                if (!openSet.has(neighbor)) {
                    openSet.add(neighbor);
                }
            }
        }
    }

    // If we reach here, it means there is no path
    alert("No possible paths!")
    return [];
}


function reconstructPath(cameFrom, current) {
    const totalPath = [current];
    while (cameFrom[current] !== undefined) {
        current = cameFrom[current];
        totalPath.unshift(current);
    }
    shortestPath = totalPath;
    console.log(totalPath);
    return totalPath;
}

function buildGraph() {
    const faceCount = geometry.attributes.position.count / 3;

    for (let i = 0; i < faceCount; i++) {
        faceNeighbors[i] = [];
        for (let j = 0; j < faceCount; j++) {
            if (i !== j && isAdjacentToFace(i, j) && !coloredFaces.includes(j)) {
                faceNeighbors[i].push(j);
            }
        }
    }
}
function findShortestPath(){
    buildGraph();
    colorPath(search());
}

function heuristic(start, end) {
    const aCenter = getFaceCenter(start);
    const bCenter = getFaceCenter(end);
    return aCenter.distanceTo(bCenter);
}

function getFaceCenter(faceIndex) {
    const positionsAttr = geometry.attributes.position;
    const center = new THREE.Vector3();
    for (let i = 0; i < 3; i++) {
        const vertexIndex = faceIndex * 3 + i;
        center.add(new THREE.Vector3(
            positionsAttr.getX(vertexIndex),
            positionsAttr.getY(vertexIndex),
            positionsAttr.getZ(vertexIndex)
        ));
    }
    return center.divideScalar(3);
}

function getNeighbors()
{
    return faceNeighbors;
}

function colorPath(faces){
    for (let i = 0; i < faces.length; i++) {
        if(faces[i]!==startFaceIndex && faces[i]!==finishFaceIndex){
            colorFace(faces[i], new THREE.Color(0xffff00));
        }
    }

}
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}


document.getElementById('helpButton').addEventListener('click', () => {
    // Start animation or action
    console.log('Help button clicked');
});

document.getElementById('clearButton').addEventListener('click', () => {
    // Stop animation or action
    console.log('Clear button clicked');
    clearGame();
});

document.getElementById('resetButton').addEventListener('click', () => {
    // Reset the scene or action
    console.log('Reset button clicked');
    resetGame();

   // animate();
});

document.getElementById('pathButton').addEventListener('click', () => {
    // Trigger the pathfinding algorithm
    for(let i = 0; i < shortestPath.length; i++ ){
        if (shortestPath[i] !== startFaceIndex && shortestPath[i] !== finishFaceIndex && !coloredFaces.includes(shortestPath[i])) {
            colorFace(shortestPath[i], new THREE.Color(0xffffff));
            }
    }
    findShortestPath();
});

document.addEventListener('DOMContentLoaded', (event) => {
    const settingsButton = document.getElementById('settingsButton');
    const settingsModal = document.getElementById('settingsModal');

    const helpButton = document.getElementById('helpButton');
    const helpModal = document.getElementById('helpModal');

    const closeSettingsModal = document.getElementsByClassName('close')[0];
    const closeHelpModal = document.getElementsByClassName('close')[1];

    const saveSettingsButton = document.getElementById('saveSettingsButton');

    settingsButton.onclick = function() {
        settingsModal.style.display = 'block';
    }

    helpButton.onclick = function() {
        helpModal.style.display = 'block';
    }

    closeSettingsModal.onclick = function() {
        settingsModal.style.display = 'none';
    }

    closeHelpModal.onclick = function() {
        helpModal.style.display = 'none';
    }



    window.onclick = function(event) {
        if (event.target == settingsModal) {
            settingsModal.style.display = 'none';
        }
    }

    window.onclick = function(event) {
        if (event.target == helpModal) {
            helpModal.style.display = 'none';
        }
    }

    saveSettingsButton.onclick = function() {
        const shape = document.getElementById('shape').value;
        const radius = document.getElementById('radius').value;
        const details = document.getElementById('details').value;

        // Update your 3D object with the new settings
        update3DObject(shape, radius, details);

        settingsModal.style.display = 'none';
    }
});

function update3DObject(shape, radius, details) {

    scene.remove(soccerBall);
    scene.remove(edges);
    console.log('Shape:', shape, 'Radius:', radius, 'Details:', details);


    initShape(shape, parseInt(radius), parseInt(details));


}


init();
