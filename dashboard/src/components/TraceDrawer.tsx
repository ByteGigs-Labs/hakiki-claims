import { useState } from "react";
import { useAsync } from "../hooks/useAsync";
import { fetchStoredCheck } from "../lib/api";
import type { Language } from "../types";
import { CitationDrawer } from "./CitationDrawer";
import { Drawer } from "./Drawer";
import { NarrationPanel } from "./NarrationPanel";
import { TraceTimeline } from "./TraceTimeline";
import { VerdictBanner } from "./VerdictBanner";

function Body({ traceHash }: { traceHash: string }) {
  const { data, loading, error } = useAsync(() => fetchStoredCheck(traceHash), [traceHash]);
  const [language, setLanguage] = useState<Language>("en");
  const [cited, setCited] = useState<string | null>(null);
  if (loading) return <div className="skeleton" style={{ height: 320 }} />;
  if (error || !data) return <p>This check could not be loaded.</p>;
  return (
    <div className="trace-drawer">
      <VerdictBanner result={data} />
      <section className="trace-section">
        <header className="section-head">
          <div>
            <p className="eyebrow">The glass box</p>
            <h3>How the verdict was reached</h3>
          </div>
        </header>
        <TraceTimeline steps={data.trace} onCite={setCited} />
      </section>
      <NarrationPanel traceHash={data.trace_hash} language={language} onLanguage={setLanguage} />
      <CitationDrawer rule={cited} onClose={() => setCited(null)} />
    </div>
  );
}

export function TraceDrawer({ traceHash, onClose }: { traceHash: string | null; onClose: () => void }) {
  return (
    <Drawer open={traceHash !== null} onClose={onClose} label="Stored check">
      {traceHash && <Body traceHash={traceHash} />}
    </Drawer>
  );
}
