"use client";
import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { API, generate, update, health, transcribe, speak } from "@/lib/api";
const Walk = dynamic(() => import("./Walkthrough3D"), { ssr: false });
const LANGS: [string, string][] = [["en-IN", "English"], ["hi-IN", "हिन्दी Hindi"], ["te-IN", "తెలుగు Telugu"], ["ta-IN", "தமிழ் Tamil"], ["kn-IN", "ಕನ್ನಡ Kannada"], ["ml-IN", "മലയാളം Malayalam"], ["mr-IN", "मराठी Marathi"], ["bn-IN", "বাংলা Bengali"], ["gu-IN", "ગુજરાતી Gujarati"], ["pa-IN", "ਪੰਜਾਬੀ Punjabi"]];

const lakh = (n: number) => `₹${(n / 1e5).toFixed(1)} lakh`;

export default function Home() {
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const [busy, setBusy] = useState(false);
  const [question, setQuestion] = useState<string | null>(null);
  const [pid, setPid] = useState<string | undefined>();
  const [proj, setProj] = useState<any>(null);
  const [floor, setFloor] = useState(0);
  const [err, setErr] = useState("");
  const [gnani, setGnani] = useState(false);
  const [lang, setLang] = useState("en-IN");
  const [view, setView] = useState("plan");
  const rec = useRef<MediaRecorder | null>(null);
  const sr = useRef<any>(null);
  const chunks = useRef<Blob[]>([]);

  useEffect(() => { health().then(h => setGnani(h.gnani_configured)).catch(() => setErr("Backend not reachable. Start it on port 8000.")); }, []);

  async function startMic() {
    setErr("");
    try {
    if (gnani) { // Gnani Prisma path: record audio, send to backend
      const s = await navigator.mediaDevices.getUserMedia({ audio: true });
      const m = new MediaRecorder(s); chunks.current = [];
      m.ondataavailable = e => chunks.current.push(e.data);
      m.onstop = async () => {
        s.getTracks().forEach(t => t.stop()); setBusy(true);
        try { setText(t => (t + " " + "").trim()); const tr = await transcribe(new Blob(chunks.current, { type: "audio/webm" }), lang); setText(t => (t + " " + tr).trim()); }
        catch (e: any) { setErr(e.message); if (String(e.message).includes("limit")) setGnani(false); } finally { setBusy(false); }
      };
      m.start(); rec.current = m;
    } else { // Browser fallback when no Gnani key is set
      const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SR) { setErr("Voice not supported in this browser. Type instead, or add a Gnani key."); return; }
      const r = new SR(); r.lang = lang; r.interimResults = true; r.continuous = true;
      r.onresult = (e: any) => setText(Array.from(e.results).map((x: any) => x[0].transcript).join(" "));
      r.onerror = (e: any) => { setListening(false); setErr(e.error === "not-allowed" ? "Microphone blocked. Click the lock icon in the address bar, allow the microphone, and reload." : "Voice error: " + e.error + ". You can type instead."); };
      r.onend = () => setListening(false); r.start(); sr.current = r;
    }
    setListening(true);
    } catch (e: any) {
      setListening(false);
      setErr(e?.name === "NotAllowedError" ? "Microphone blocked. Click the lock icon in the address bar, allow the microphone, and reload." : e?.name === "NotFoundError" ? "No microphone found on this device." : "Could not start the microphone: " + (e?.message || e));
    }
  }
  function stopMic() { rec.current?.stop(); sr.current?.stop(); setListening(false); }

  async function submit() {
    if (!text.trim()) return;
    setBusy(true); setErr("");
    try {
      const res = proj ? await update(proj.id, text, lang) : await generate(text, pid, lang);
      if (res.needs_more_info) { setPid(res.project_id); setQuestion(res.question); speak(res.question, false, lang); setText(""); }
      else { const p = res.project; setProj(p); setPid(p.id); setQuestion(null); setFloor(0); setText(""); speak(p.explanation, gnani, lang); }
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }

  const r = proj?.requirements;
  return (
    <main className="mx-auto grid max-w-7xl gap-6 p-4 md:grid-cols-[380px_1fr] md:p-8">
      <section className="space-y-4">
        <h1 className="text-4xl font-extrabold leading-none tracking-tight">BuildWise AI</h1>
        <p className="text-lg">Describe your plot, budget and rooms out loud. You get a floor plan, cost and schedule.</p>
        <div className="sheet space-y-3 p-4">
          <select value={lang} onChange={e => setLang(e.target.value)} aria-label="Language" className="w-full border-2 border-ink bg-white p-2">
            {LANGS.map(([c, n]) => <option key={c} value={c}>{n}</option>)}</select>
          {question && <p className="rounded bg-plumb/40 p-3 font-medium" role="status">{question}</p>}
          <button onClick={listening ? stopMic : startMic} aria-pressed={listening}
            className={`mic ${listening ? "live" : ""} mx-auto flex h-24 w-24 items-center justify-center rounded-full border-2 border-ink bg-plumb text-4xl`}
            aria-label={listening ? "Stop recording" : "Start speaking"}>🎤</button>
          <p className="text-center text-sm">{listening ? "Listening. Tap to stop." : "Tap and speak"}</p>
          <textarea value={text} onChange={e => setText(e.target.value)} rows={5} placeholder="Or type: 30x40 plot in Hyderabad, 60 lakh, modern 3 BHK with study, garden and parking"
            className="w-full border-2 border-ink bg-white p-2" aria-label="Requirements" />
          <button onClick={submit} disabled={busy || !text.trim()} className="w-full border-2 border-ink bg-ink px-4 py-3 font-bold text-paper disabled:opacity-40">
            {busy ? "Working…" : proj ? "Update design" : question ? "Send answer" : "Generate design"}</button>
          {err && <p className="text-sm font-medium text-red-700" role="alert">{err}</p>}
          <p className="text-xs">Voice engine: {gnani ? "Gnani Prisma and Timbre" : "browser fallback (add GNANI_API_KEY for Gnani)"}</p>
        </div>
      </section>

      <section>
        {!proj ? (
          <div className="sheet flex min-h-[420px] items-center justify-center p-8 text-center text-lg">Your drawing sheet will appear here after you describe the home.</div>
        ) : (
          <div className="space-y-6">
            <div className="sheet p-4">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <h2 className="text-2xl font-bold">{r.bedrooms} BHK, {r.plot_w}×{r.plot_d} ft, {r.city}</h2>
                <div className="ml-auto flex gap-2">
                  {proj.floor_plans.map((_: any, i: number) => (
                    <button key={i} onClick={() => setFloor(i)} className={`border-2 border-ink px-3 py-1 ${floor === i ? "bg-plumb" : "bg-white"}`}>Floor {i + 1}</button>))}
                </div>
              </div>
              <div className="mb-2 flex gap-2">{[["plan", "2D plan"], ["3d", "3D walkthrough"]].map(([k, n]) => <button key={k} onClick={() => setView(k)} className={`border-2 border-ink px-3 py-1 ${view === k ? "bg-plumb" : "bg-white"}`}>{n}</button>)}</div>
              {view === "plan" ? <div className="mx-auto max-w-2xl" dangerouslySetInnerHTML={{ __html: proj.floor_plans[floor] }} /> : <Walk floors={proj.geo} />}
              {proj.geo?.[floor]?.notes?.length > 0 && <p className="mt-2 text-sm"><b>Layout score {proj.geo[floor].score}/100.</b> {proj.geo[floor].notes.join(". ")}.</p>}
            </div>

            <div className="sheet p-4">
              <h3 className="text-xl font-bold">Explanation</h3>
              <p className="mt-1 max-w-prose">{proj.explanation}</p>
              <button onClick={() => speak(proj.explanation, gnani, lang)} className="mt-3 border-2 border-ink bg-plumb px-3 py-1 font-bold">🔊 Play explanation</button>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <div className="sheet p-4">
                <h3 className="text-xl font-bold">Cost estimate</h3>
                <table className="mt-2 w-full text-sm"><tbody>
                  {Object.entries(proj.cost.items).map(([k, v]: any) => <tr key={k} className="border-b border-rule"><td className="py-1">{k}</td><td className="text-right">{lakh(v)}</td></tr>)}
                  <tr className="font-bold"><td className="py-2">Total</td><td className="text-right">{lakh(proj.cost.total)}</td></tr>
                </tbody></table>
                <p className="mt-1 text-sm">Likely range: <b>{lakh(proj.cost.low)} to {lakh(proj.cost.high)}</b> ({proj.cost.tier} finish, about ₹{proj.cost.rate_per_sqft.toLocaleString("en-IN")}/sq ft)</p>
                {proj.cost.suggestions?.length > 0 && <ul className="mt-1 list-disc pl-5 text-sm">{proj.cost.suggestions.map((s: string) => <li key={s}>{s}</li>)}</ul>}
                {proj.cost.budget && <p className="mt-1 text-sm font-medium">{proj.cost.within_budget ? "Within" : "Over"} your {lakh(proj.cost.budget)} budget.</p>}
                <p className="mt-1 text-xs">{proj.cost.note}</p>
              </div>
              <div className="sheet p-4">
                <h3 className="text-xl font-bold">Construction timeline</h3>
                <ol className="mt-2 space-y-1">
                  {proj.timeline.map((t: any) => <li key={t.phase} className="flex items-center gap-2 text-sm">
                    <span className="w-24">{t.phase}</span><span className="h-3 bg-plumb" style={{ width: t.weeks * 8 }} /><span>{t.weeks} wk</span></li>)}
                </ol>
              </div>
              <div className="sheet p-4"><h3 className="text-xl font-bold">Sustainability</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{proj.sustainability.map((s: string) => <li key={s}>{s}</li>)}</ul></div>
              <div className="sheet p-4"><h3 className="text-xl font-bold">Interior and utilities</h3>
                <p className="mt-2 text-sm"><b>{proj.interior.theme}.</b> {proj.interior.colors.join(", ")}.</p>
                <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">{[...proj.utilities.electrical, ...proj.utilities.plumbing].map((s: string) => <li key={s}>{s}</li>)}</ul></div>
            </div>
            <a href={`${API}/api/report/${proj.id}`} className="inline-block border-2 border-ink bg-ink px-5 py-3 font-bold text-paper">Download PDF report</a>
            <p className="text-xs">Conceptual design only. Have a licensed architect and structural engineer verify before building.</p>
          </div>
        )}
      </section>
    </main>
  );
}