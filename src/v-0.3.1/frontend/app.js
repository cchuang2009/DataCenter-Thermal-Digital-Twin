
//import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';

//import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/controls/OrbitControls.js';
//import * as THREE from 'https://unpkg.com/three@0.170.0/build/three.module.js';
//import { OrbitControls } from 'https://unpkg.com/three@0.170.0/examples/jsm/controls/OrbitControls.js';

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const host = document.getElementById("scene");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b1422);

const camera = new THREE.PerspectiveCamera(
    48,
    host.clientWidth / host.clientHeight,
    0.1,
    100
);

camera.position.set(14, 11, 15);

const renderer = new THREE.WebGLRenderer({
    antialias: true
});

renderer.setPixelRatio(
    Math.min(window.devicePixelRatio, 2)
);

renderer.setSize(
    host.clientWidth,
    host.clientHeight
);

host.appendChild(renderer.domElement);

// Camera controls
const controls = new OrbitControls(
    camera,
    renderer.domElement
);

controls.target.set(6, 1, 4);
controls.enableDamping = true;

// Lighting
scene.add(
    new THREE.HemisphereLight(
        0xc9e4ff,
        0x263044,
        2
    )
);

const light = new THREE.DirectionalLight(
    0xffffff,
    2
);

light.position.set(8, 13, 5);
scene.add(light);

// Room floor
const floor = new THREE.Mesh(
    new THREE.BoxGeometry(12, 0.12, 8),
                             new THREE.MeshStandardMaterial({
                                 color: 0x26374b
                             })
);

floor.position.set(6, -0.08, 4);
scene.add(floor);

// Grid
const grid = new THREE.GridHelper(
    12, 24, 0x60758d, 0x34475d
);

grid.position.set(6, 0, 4);
scene.add(grid);

// Room boundary
const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(
        new THREE.BoxGeometry(12, 3.5, 8)
    ),
    new THREE.LineBasicMaterial({
        color: 0x66829f,
        transparent: true,
        opacity: 0.5
    })
);

edges.position.set(6, 1.75, 4);
scene.add(edges);

// Object groups
const racksGroup = new THREE.Group();
const sensorsGroup = new THREE.Group();
const airflowGroup = new THREE.Group();

scene.add(racksGroup);
scene.add(sensorsGroup);
scene.add(airflowGroup);

let sensorMeshes = [];
let particles = [];

let currentFrame = 0;
let playing = false;
let playTimer = null;

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();


// --------------------------
// Rack generation
// --------------------------

function addRack(r) {

    const body = new THREE.Mesh(
        new THREE.BoxGeometry(
            r.width,
            r.height,
            r.depth
        ),
        new THREE.MeshStandardMaterial({
            color: 0x34475c,
            metalness: 0.3,
            roughness: 0.6
        })
    );

    body.position.set(
        r.x,
        r.height / 2,
        r.y
    );

    racksGroup.add(body);

    // Front door
    const front = new THREE.Mesh(
        new THREE.BoxGeometry(
            r.width * 0.82,
            r.height * 0.9,
            0.025
        ),
        new THREE.MeshStandardMaterial({
            color: 0x172638
        })
    );

    front.position.set(
        r.x,
        r.height / 2,
        r.y - r.depth / 2 - 0.015
    );

    racksGroup.add(front);

    // Server ventilation lines
    for (let k = 0; k < 8; k++) {

        const vent = new THREE.Mesh(
            new THREE.BoxGeometry(
                r.width * 0.68,
                0.018,
                0.03
            ),
            new THREE.MeshBasicMaterial({
                color: 0x6f91ad
            })
        );

        vent.position.set(
            r.x,
            0.18 + k * 0.22,
            r.y - r.depth / 2 - 0.035
        );

        racksGroup.add(vent);
    }
}


// --------------------------
// Temperature color mapping
// --------------------------

function temperatureColor(value) {

    const x = THREE.MathUtils.clamp(
        (value - 22) / 12,
                                    0,
                                    1
    );

    const color = new THREE.Color();

    color.setHSL(
        (1 - x) * 0.58,
                 0.88,
                 0.52
    );

    return color;
}


// --------------------------
// Sensor generation
// --------------------------

function drawSensors(data) {

    sensorsGroup.clear();
    sensorMeshes = [];

    for (const s of data) {

        const color = temperatureColor(
            s.temperature
        );

        const mesh = new THREE.Mesh(
            new THREE.SphereGeometry(
                0.105,
                16,
                12
            ),
            new THREE.MeshStandardMaterial({
                color: color,
                emissive: color,
                emissiveIntensity: 0.18
            })
        );

        // Model coordinates: X, Y, Z
        // Three.js coordinates: X, Z, Y
        mesh.position.set(
            s.x,
            s.z,
            s.y
        );

        mesh.userData.sensor = s;

        sensorsGroup.add(mesh);
        sensorMeshes.push(mesh);
    }
}


// --------------------------
// Airflow animation
// --------------------------

function createAirflow() {

    airflowGroup.clear();
    particles = [];

    for (let i = 0; i < 70; i++) {

        const particle = new THREE.Mesh(
            new THREE.SphereGeometry(
                0.035,
                8,
                6
            ),
            new THREE.MeshBasicMaterial({
                color: 0x68c9ff,
                transparent: true,
                opacity: 0.8
            })
        );

        particle.position.set(
            1 + Math.random() * 10,
                              0.25 + Math.random() * 1.7,
                              2.8 + Math.random() * 2.4
        );

        particle.userData.speed =
        0.018 + Math.random() * 0.025;

        airflowGroup.add(particle);
        particles.push(particle);
    }
}


// --------------------------
// API data
// --------------------------

async function loadFrame(t) {

    const response = await fetch(
        `/api/frame/${t}`
    );

    if (!response.ok) {
        throw new Error("Frame API failed");
    }

    const data = await response.json();

    currentFrame = t;

    document.getElementById(
        "time-label"
    ).textContent = data.timestamp;

    document.getElementById(
        "time"
    ).value = t;

    drawSensors(data.sensors);

    const temperatures = data.sensors.map(
        s => s.temperature
    );

    const airflows = data.sensors.map(
        s => s.airflow
    );

    const meanTemp =
    temperatures.reduce((a, b) => a + b, 0)
    / temperatures.length;

    const maxTemp = Math.max(
        ...temperatures
    );

    const meanAir =
    airflows.reduce((a, b) => a + b, 0)
    / airflows.length;

    document.getElementById(
        "mean-temp"
    ).textContent = meanTemp.toFixed(1) + " °C";

    document.getElementById(
        "max-temp"
    ).textContent = maxTemp.toFixed(1) + " °C";

    document.getElementById(
        "mean-air"
    ).textContent = meanAir.toFixed(2) + " m/s";

    document.getElementById(
        "selection"
    ).textContent = "Click a sensor sphere.";
}


// --------------------------
// Initialize
// --------------------------

async function initialize() {

    const response = await fetch("/api/config");

    if (!response.ok) {
        throw new Error("Config API failed");
    }

    const config = await response.json();

    document.getElementById(
        "rack-count"
    ).textContent = config.racks.length;

    document.getElementById(
        "sensor-count"
    ).textContent = config.sensor_count;

    config.racks.forEach(addRack);

    createAirflow();

    await loadFrame(0);

    document.getElementById(
        "status"
    ).textContent = "API connected";
}


// --------------------------
// UI events
// --------------------------

document.getElementById(
    "time"
).addEventListener("input", e => {

    loadFrame(Number(e.target.value))
    .catch(console.error);
});

document.getElementById(
    "show-temp"
).addEventListener("change", e => {

    sensorsGroup.visible = e.target.checked;
});

document.getElementById(
    "show-air"
).addEventListener("change", e => {

    airflowGroup.visible = e.target.checked;
});

document.getElementById(
    "play"
).addEventListener("click", () => {

    playing = !playing;

    document.getElementById(
        "play"
    ).textContent = playing ? "Pause" : "Play";

    if (playing) {

        playTimer = setInterval(() => {

            loadFrame(
                (currentFrame + 1) % 48
            ).catch(console.error);

        }, 650);

    } else {

        clearInterval(playTimer);
    }
});

document.getElementById(
    "reset"
).addEventListener("click", () => {

    playing = false;

    clearInterval(playTimer);

    document.getElementById(
        "play"
    ).textContent = "Play";

    loadFrame(0).catch(console.error);

    controls.reset();
});


// --------------------------
// Sensor selection
// --------------------------

renderer.domElement.addEventListener(
    "pointerdown",
    event => {

        const rect =
        renderer.domElement.getBoundingClientRect();

        pointer.x =
        ((event.clientX - rect.left) / rect.width)
        * 2 - 1;

        pointer.y =
        -((event.clientY - rect.top) / rect.height)
        * 2 + 1;

        raycaster.setFromCamera(
            pointer,
            camera
        );

        const hits = raycaster.intersectObjects(
            sensorMeshes
        );

        if (hits.length > 0) {

            const s = hits[0].object.userData.sensor;

            document.getElementById(
                "selection"
            ).innerHTML = `
            <b>${s.id}</b><br>
            Rack: ${s.rack_id}<br>
            Temperature: ${s.temperature} °C<br>
            Airflow: ${s.airflow} m/s<br>
            XYZ: (
                ${s.x.toFixed(2)},
                  ${s.y.toFixed(2)},
                  ${s.z.toFixed(2)}
            ) m
            `;
        }
    }
);


// --------------------------
// Rendering loop
// --------------------------

function animate() {

    controls.update();

    for (const p of particles) {

        p.position.x += p.userData.speed;

        if (p.position.x > 11.8) {
            p.position.x = 0.2;
        }
    }

    renderer.render(scene, camera);

    requestAnimationFrame(animate);
}


// --------------------------
// Responsive rendering
// --------------------------

const resizeObserver = new ResizeObserver(() => {

    const width = host.clientWidth;
    const height = host.clientHeight;

    if (!width || !height) return;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    renderer.setSize(width, height);

});

resizeObserver.observe(host);


// Start application
initialize().catch(error => {

    console.error(error);

    document.getElementById(
        "status"
    ).textContent = "API error";
});

animate();
