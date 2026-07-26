import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";
import { LineSegments2 } from "three/addons/lines/LineSegments2.js";
import { LineSegmentsGeometry } from "three/addons/lines/LineSegmentsGeometry.js";

const FLOOR_COLOR = 0x7d9cc0;
const HIGHLIGHT_COLOR = 0xe8a44c;
const EDGE_COLOR = 0x2c4568;
const SITE_COLOR = 0x9cb98c;
const FLOOR_OPACITY = 0.42;
const HIGHLIGHT_OPACITY = 0.6;
const EDGE_WIDTH = 2.5;

function siteCenter(outline) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const [x, y] of outline) {
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
  }
  return { cx: (minX + maxX) / 2, cy: (minY + maxY) / 2, span: Math.max(maxX - minX, maxY - minY) };
}

function makeShape(outline) {
  const shape = new THREE.Shape();
  outline.forEach(([x, y], index) => {
    if (index === 0) shape.moveTo(x, y);
    else shape.lineTo(x, y);
  });
  shape.closePath();
  return shape;
}

function disposeGroup(group) {
  for (const child of group.children) {
    if (child.geometry) child.geometry.dispose();
    if (child.material) child.material.dispose();
  }
  group.clear();
}

export default function ThreeView({ result, width, height, highlight }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.add(new THREE.HemisphereLight(0xffffff, 0x8899aa, 0.9));
    const sun = new THREE.DirectionalLight(0xffffff, 1.2);
    sun.position.set(60, 100, 40);
    scene.add(sun);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.1;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.33;
    controls.maxPolarAngle = Math.PI / 2.05;

    const group = new THREE.Group();
    scene.add(group);
    sceneRef.current = { camera, controls, group };

    let frame;
    const animate = () => {
      frame = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frame);
      controls.dispose();
      disposeGroup(group);
      renderer.dispose();
      mount.removeChild(renderer.domElement);
      sceneRef.current = null;
    };
  }, [width, height]);

  useEffect(() => {
    const ctx = sceneRef.current;
    if (!ctx || !result) return;
    const { camera, controls, group } = ctx;
    disposeGroup(group);

    const { cx, cy, span } = siteCenter(result.site_outline);

    const siteGeometry = new THREE.ShapeGeometry(makeShape(result.site_outline));
    const siteMesh = new THREE.Mesh(
      siteGeometry,
      new THREE.MeshLambertMaterial({ color: SITE_COLOR, side: THREE.DoubleSide }),
    );
    siteMesh.rotation.x = -Math.PI / 2;
    group.add(siteMesh);

    const gridSize = Math.ceil(span) + 10;
    const grid = new THREE.GridHelper(gridSize, gridSize, 0xc5cdc0, 0xdde4d8);
    grid.position.set(cx, -0.02, -cy);
    group.add(grid);

    result.buildings.forEach((building, b) => {
      building.floors.forEach((floor, f) => {
        const highlighted =
          highlight && highlight.building === b && (highlight.floor === undefined || highlight.floor === f);
        const geometry = new THREE.ExtrudeGeometry(makeShape(floor.outline), {
          depth: floor.height_m,
          bevelEnabled: false,
        });
        const mesh = new THREE.Mesh(
          geometry,
          new THREE.MeshLambertMaterial({
            color: highlighted ? HIGHLIGHT_COLOR : FLOOR_COLOR,
            transparent: true,
            opacity: highlighted ? HIGHLIGHT_OPACITY : FLOOR_OPACITY,
            depthWrite: false,
            side: THREE.DoubleSide,
          }),
        );
        mesh.rotation.x = -Math.PI / 2;
        mesh.position.y = floor.level_m;
        group.add(mesh);

        const edgeMaterial = new LineMaterial({ color: EDGE_COLOR, linewidth: EDGE_WIDTH });
        edgeMaterial.resolution.set(width, height);
        const edgeGeometry = new LineSegmentsGeometry().fromEdgesGeometry(new THREE.EdgesGeometry(geometry));
        const edges = new LineSegments2(edgeGeometry, edgeMaterial);
        edges.rotation.x = -Math.PI / 2;
        edges.position.y = floor.level_m + 0.01;
        group.add(edges);
      });
    });

    group.position.set(-cx, 0, cy);
    const maxHeight = Math.max(result.metrics.max_height_m, 6);
    controls.target.set(0, maxHeight / 3, 0);
    if (!ctx.placed) {
      camera.position.set(span * 1.1, span * 0.75, span * 1.1);
      ctx.placed = true;
    }
    camera.lookAt(controls.target);
  }, [result, highlight, width, height]);

  return <div ref={mountRef} className="three-view" style={{ width, height }} />;
}
