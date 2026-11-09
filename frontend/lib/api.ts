const B = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const API = B;
async function j(path: string, body?: any) {
  const r = await fetch(B + path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : undefined);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
}
export const generate = (text: string, project_id?: string, lang = "en-IN") => j("/api/design/generate", { text, project_id, lang });
export const update = (project_id: string, text: string, lang = "en-IN") => j("/api/design/update", { project_id, text, lang });
export const health = () => j("/api/health");
// Gnani accepts WAV/MP3/OGG etc. but not webm, so convert the recording to 16 kHz mono WAV.
async function toWav(blob: Blob): Promise<Blob> {
  const ctx = new AudioContext();
  const buf = await ctx.decodeAudioData(await blob.arrayBuffer());
  const rate = 16000, len = Math.ceil(buf.duration * rate);
  const off = new OfflineAudioContext(1, len, rate);
  const src = off.createBufferSource(); src.buffer = buf; src.connect(off.destination); src.start();
  const pcm = (await off.startRendering()).getChannelData(0);
  const out = new DataView(new ArrayBuffer(44 + pcm.length * 2));
  const w = (o: number, s: string) => [...s].forEach((c, i) => out.setUint8(o + i, c.charCodeAt(0)));
  w(0, "RIFF"); out.setUint32(4, 36 + pcm.length * 2, true); w(8, "WAVEfmt "); out.setUint32(16, 16, true);
  out.setUint16(20, 1, true); out.setUint16(22, 1, true); out.setUint32(24, rate, true); out.setUint32(28, rate * 2, true);
  out.setUint16(32, 2, true); out.setUint16(34, 16, true); w(36, "data"); out.setUint32(40, pcm.length * 2, true);
  pcm.forEach((s, i) => out.setInt16(44 + i * 2, Math.max(-1, Math.min(1, s)) * 0x7fff, true));
  ctx.close();
  return new Blob([out], { type: "audio/wav" });
}
export async function transcribe(blob: Blob, lang = "en-IN"): Promise<string> {
  const fd = new FormData(); fd.append("file", await toWav(blob), "speech.wav"); fd.append("lang", lang);
  const r = await fetch(B + "/api/voice/transcribe", { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || "Transcription failed");
  return (await r.json()).transcript;
}
export async function speak(text: string, useGnani: boolean, lang = "en-IN") {
  if (useGnani) {
    try {
      const r = await fetch(B + "/api/voice/explain", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text, lang }) });
      if (r.ok) { const a = new Audio(URL.createObjectURL(await r.blob())); await a.play(); return; }
    } catch {}
  }
  const u = new SpeechSynthesisUtterance(text); u.lang = lang; window.speechSynthesis?.speak(u); // browser fallback
}