"use client";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, PointerLockControls, Text } from "@react-three/drei";
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";

const H = 10, T = 0.6;
const COL: Record<string, string> = { Living: "#F7E7B4", Kitchen: "#F4C7A1", Dining: "#E8D5B5", Bedroom: "#C9DDEB", "Master Bedroom": "#B5CFE3", Bath: "#BFE3DC", Study: "#D9D2EE", Pooja: "#F9D6D6", Utility: "#E3E3E3", Stairs: "#DDDDDD" };
const col = (n: string) => COL[n] || (n.startsWith("Living") ? COL.Living : "#EEEEEE");

function Floor({ g, y, roof }: any) {
  const xs = g.rooms.flatMap((r: any) => [r.x, r.x + r.w]), zs = g.rooms.flatMap((r: any) => [r.y, r.y + r.h]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), z0 = Math.min(...zs), z1 = Math.max(...zs);
  return (
    <group position={[0, y, 0]}>
      {g.rooms.map((r: any, i: number) => (
        <group key={i}>
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[r.x + r.w / 2, 0.05, r.y + r.h / 2]}><planeGeometry args={[r.w, r.h]} /><meshStandardMaterial color={col(r.n)} /></mesh>
          <Text position={[r.x + r.w / 2, 0.12, r.y + r.h / 2]} rotation={[-Math.PI / 2, 0, 0]} fontSize={0.9} color="#111">{r.n}</Text>
        </group>
      ))}
      {g.walls.map((w: number[], i: number) => {
        const horiz = Math.abs(w[1] - w[3]) < 1e-3, dx = Math.abs(w[0] - w[2]), dz = Math.abs(w[1] - w[3]);
        return <mesh key={i} position={[(w[0] + w[2]) / 2, H / 2, (w[1] + w[3]) / 2]}><boxGeometry args={horiz ? [dx + T, H, T] : [T, H, dz + T]} /><meshStandardMaterial color="#f4f1ea" /></mesh>;
      })}
      {g.windows.map((w: number[], i: number) => {
        const horiz = Math.abs(w[1] - w[3]) < 1e-3, len = Math.hypot(w[0] - w[2], w[1] - w[3]);
        return <mesh key={"w" + i} position={[(w[0] + w[2]) / 2, 5.5, (w[1] + w[3]) / 2]}><boxGeometry args={horiz ? [len, 3.5, T + 0.12] : [T + 0.12, 3.5, len]} /><meshStandardMaterial color="#7fb8e6" transparent opacity={0.65} /></mesh>;
      })}
      {roof && <mesh position={[(x0 + x1) / 2, H + 0.2, (z0 + z1) / 2]}><boxGeometry args={[x1 - x0 + 1, 0.4, z1 - z0 + 1]} /><meshStandardMaterial color="#b9b2a5" /></mesh>}
    </group>
  );
}

function Walker({ walls, start }: any) {
  const { camera } = useThree();
  const keys = useRef<Record<string, boolean>>({});
  useEffect(() => {
    camera.position.set(start[0], 5.5, start[1]);
    const dn = (e: KeyboardEvent) => (keys.current[e.code] = true), up = (e: KeyboardEvent) => (keys.current[e.code] = false);
    window.addEventListener("keydown", dn); window.addEventListener("keyup", up);
    return () => { window.removeEventListener("keydown", dn); window.removeEventListener("keyup", up); };
  }, []);
  const blocked = (x: number, z: number) => walls.some((w: number[]) => x > Math.min(w[0], w[2]) - 0.55 && x < Math.max(w[0], w[2]) + 0.55 && z > Math.min(w[1], w[3]) - 0.55 && z < Math.max(w[1], w[3]) + 0.55);
  useFrame((_, dt) => {
    const k = keys.current, f = (k["KeyW"] || k["ArrowUp"] ? 1 : 0) - (k["KeyS"] || k["ArrowDown"] ? 1 : 0), s = (k["KeyD"] || k["ArrowRight"] ? 1 : 0) - (k["KeyA"] || k["ArrowLeft"] ? 1 : 0);
    if (!f && !s) return;
    const d = new THREE.Vector3(); camera.getWorldDirection(d); d.y = 0; d.normalize();
    const r = new THREE.Vector3(-d.z, 0, d.x), v = 12 * dt;
    const nx = camera.position.x + (d.x * f + r.x * s) * v, nz = camera.position.z + (d.z * f + r.z * s) * v;
    if (!blocked(nx, camera.position.z)) camera.position.x = nx;
    if (!blocked(camera.position.x, nz)) camera.position.z = nz;
  });
  return null;
}

export default function Walkthrough3D({ floors }: { floors: any[] }) {
  const [mode, setMode] = useState<"orbit" | "walk">("orbit");
  const [roof, setRoof] = useState(false);
  const g0 = floors[0], W = g0.W, D = g0.D;
  const xs = g0.rooms.flatMap((r: any) => [r.x, r.x + r.w]), zs = g0.rooms.flatMap((r: any) => [r.y, r.y + r.h]);
  const start = [(Math.min(...xs) + Math.max(...xs)) / 2, Math.max(...zs) + 2.5];
  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center gap-2 text-sm">
        {(["orbit", "walk"] as const).map(m => <button key={m} onClick={() => setMode(m)} className={`border-2 border-ink px-3 py-1 ${mode === m ? "bg-plumb" : "bg-white"}`}>{m === "orbit" ? "Orbit view" : "Walk inside"}</button>)}
        <label className="flex items-center gap-1"><input type="checkbox" checked={roof} onChange={e => setRoof(e.target.checked)} /> Roof</label>
        <span>{mode === "walk" ? "Click the scene, then W A S D to walk and the mouse to look. Esc to release. Desktop only." : "Drag to rotate, scroll to zoom."}</span>
      </div>
      <div style={{ height: 520 }} className="border-2 border-ink">
        <Canvas key={mode} camera={{ position: [W * 0.5, 55, D * 1.5], fov: 50 }} style={{ background: "#dfe7ee" }}>
          <ambientLight intensity={0.9} /><directionalLight position={[W, 60, -D]} intensity={0.8} />
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[W / 2, -0.05, D / 2]}><planeGeometry args={[W * 3, D * 3]} /><meshStandardMaterial color="#cfe3bd" /></mesh>
          {floors.map((g, i) => <Floor key={i} g={g} y={i * (H + 0.5)} roof={roof && i === floors.length - 1} />)}
          {mode === "orbit" ? <OrbitControls target={[W / 2, 0, D / 2]} /> : <><PointerLockControls /><Walker walls={g0.walls} start={start} /></>}
        </Canvas>
      </div>
    </div>
  );
}