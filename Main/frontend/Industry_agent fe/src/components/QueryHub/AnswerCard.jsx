import React from "react";
import {
  CheckCircle,
  AlertTriangle,
  Sparkles,
  FileText,
  ArrowRight,
  ShieldCheck,
  HelpCircle,
  Clock,
  ListChecks,
  BookOpen,
  Wrench,
  TriangleAlert
} from "lucide-react";

/**
 * Parses a raw answer string and splits it into structured sections.
 * Detects: Step-by-step lists, bold headers like "Root Cause Analysis:", bullet points, etc.
 */
function parseAnswer(answer) {
  if (!answer) return [];
  const lines = answer.split(/\n+/).map(l => l.trim()).filter(Boolean);
  const sections = [];
  let currentSection = null;

  const SECTION_HEADERS = [
    "Operational Status", "Root Cause Analysis", "RCA",
    "Step-by-Step", "Step-by-step", "Remediation", "Procedure",
    "Safety", "Isolation", "Post-Repair", "Post-repair",
    "Findings", "Summary", "Conclusion", "Recommendations"
  ];

  for (const line of lines) {
    // Detect numbered step: "Step 1:", "1.", "Step 1 -"
    const stepMatch = line.match(/^(Step\s*\d+[:\-]?\s*|^\d+\.\s+)/i);
    // Detect section header ending with ":"
    const headerMatch = SECTION_HEADERS.some(h => line.toLowerCase().startsWith(h.toLowerCase()) && (line.endsWith(":") || line.includes(":")));
    // Detect bullet
    const bulletMatch = line.startsWith("•") || line.startsWith("-") || line.startsWith("*");

    if (headerMatch) {
      if (currentSection) sections.push(currentSection);
      currentSection = { type: "header", title: line.replace(/:$/, ""), items: [] };
    } else if (stepMatch && !line.includes("IEEE") && !line.includes("NFPA")) {
      if (!currentSection || currentSection.type !== "steps") {
        if (currentSection) sections.push(currentSection);
        currentSection = { type: "steps", title: "Procedure", items: [] };
      }
      currentSection.items.push(line.replace(stepMatch[0], "").trim() || line);
    } else if (bulletMatch) {
      if (!currentSection || currentSection.type !== "bullets") {
        if (currentSection) sections.push(currentSection);
        currentSection = { type: "bullets", title: null, items: [] };
      }
      currentSection.items.push(line.replace(/^[•\-\*]\s*/, "").trim());
    } else {
      if (!currentSection || currentSection.type === "steps" || currentSection.type === "bullets") {
        if (currentSection) sections.push(currentSection);
        currentSection = { type: "prose", text: line };
      } else if (currentSection.type === "prose") {
        currentSection.text += " " + line;
      } else if (currentSection.type === "header") {
        currentSection.items.push(line);
      } else {
        if (currentSection) sections.push(currentSection);
        currentSection = { type: "prose", text: line };
      }
    }
  }
  if (currentSection) sections.push(currentSection);
  return sections;
}

const SECTION_ICONS = {
  "Operational Status": BookOpen,
  "Findings": BookOpen,
  "Root Cause": TriangleAlert,
  "RCA": TriangleAlert,
  "Remediation": Wrench,
  "Procedure": ListChecks,
  "Step-by-Step": ListChecks,
  "Safety": AlertTriangle,
  "Isolation": AlertTriangle,
  "Post-Repair": CheckCircle,
  "Post-repair": CheckCircle,
  "Summary": BookOpen,
};

function getSectionIcon(title) {
  for (const [key, Icon] of Object.entries(SECTION_ICONS)) {
    if (title && title.toLowerCase().includes(key.toLowerCase())) return Icon;
  }
  return BookOpen;
}

export const AnswerCard = ({ responseData, fallbackContent, onSelectFollowUp, onHighlightSource }) => {
  const data = responseData || (fallbackContent ? { answer: fallbackContent } : null);
  if (!data) return null;

  const {
    answer = fallbackContent || "No response content available.",
    confidence = 0.85,
    sources = [],
    evidence_classification = [],
    contradictions = [],
    follow_up_suggestions = []
  } = data;

  const confidencePct = Math.round(confidence * 100);
  const isConfidenceHigh = confidencePct >= 75;
  const sections = parseAnswer(answer);

  return (
    <div className="answer-container-card animate-fade-in">

      {/* ── Top meta bar ─────────────────────────────────── */}
      <div className="answer-header-meta">
        <div className="answer-meta-left">
          <span style={{ color: "var(--amber-primary)", fontWeight: 600 }}>COPILOT ANALYSIS</span>
          <span>&middot;</span>
          <span>{sources.length} SOURCES</span>
          {contradictions.length > 0 && (
            <><span>&middot;</span><span style={{ color: "var(--rose-primary)" }}>⚠ {contradictions.length} DISCREPANCY</span></>
          )}
        </div>
        <div className={`confidence-gauge ${isConfidenceHigh ? "" : "medium"}`}>
          <ShieldCheck size={13} />
          <span>{confidencePct}% CONFIDENCE</span>
        </div>
      </div>

      {/* ── Structured answer body ───────────────────────── */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px", padding: "4px 0" }}>
        {sections.length === 0 && (
          <p style={{ fontSize: "14px", lineHeight: "1.75", color: "var(--text-primary)", margin: 0 }}>{answer}</p>
        )}

        {sections.map((sec, i) => {
          if (sec.type === "prose") {
            return (
              <p key={i} style={{ fontSize: "14px", lineHeight: "1.75", color: "var(--text-primary)", margin: 0 }}>
                {sec.text}
              </p>
            );
          }

          if (sec.type === "header") {
            const Icon = getSectionIcon(sec.title);
            return (
              <div key={i} style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-base)",
                borderRadius: "8px",
                overflow: "hidden"
              }}>
                <div style={{
                  display: "flex", alignItems: "center", gap: "8px",
                  padding: "8px 14px",
                  background: "var(--bg-surface-elevated)",
                  borderBottom: "1px solid var(--border-subtle)"
                }}>
                  <Icon size={14} style={{ color: "var(--amber-primary)", flexShrink: 0 }} />
                  <span style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--text-secondary)" }}>
                    {sec.title}
                  </span>
                </div>
                {sec.items.length > 0 && (
                  <div style={{ padding: "10px 14px", display: "flex", flexDirection: "column", gap: "6px" }}>
                    {sec.items.map((item, j) => (
                      <p key={j} style={{ margin: 0, fontSize: "13.5px", lineHeight: "1.7", color: "var(--text-primary)" }}>{item}</p>
                    ))}
                  </div>
                )}
              </div>
            );
          }

          if (sec.type === "steps") {
            return (
              <div key={i} style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-base)",
                borderRadius: "8px",
                overflow: "hidden"
              }}>
                <div style={{
                  display: "flex", alignItems: "center", gap: "8px",
                  padding: "8px 14px",
                  background: "rgba(6,182,212,0.06)",
                  borderBottom: "1px solid rgba(6,182,212,0.15)"
                }}>
                  <ListChecks size={14} style={{ color: "var(--cyan-primary)", flexShrink: 0 }} />
                  <span style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--cyan-primary)" }}>
                    Step-by-Step Procedure
                  </span>
                </div>
                <div style={{ padding: "10px 14px", display: "flex", flexDirection: "column", gap: "8px" }}>
                  {sec.items.map((item, j) => (
                    <div key={j} style={{ display: "flex", gap: "10px", alignItems: "flex-start" }}>
                      <span style={{
                        minWidth: "22px", height: "22px", borderRadius: "50%",
                        background: "rgba(6,182,212,0.15)", border: "1px solid rgba(6,182,212,0.4)",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: "11px", fontWeight: 700, color: "var(--cyan-primary)",
                        fontFamily: "var(--font-mono)", flexShrink: 0, marginTop: "2px"
                      }}>{j + 1}</span>
                      <p style={{ margin: 0, fontSize: "13.5px", lineHeight: "1.7", color: "var(--text-primary)" }}>{item}</p>
                    </div>
                  ))}
                </div>
              </div>
            );
          }

          if (sec.type === "bullets") {
            return (
              <div key={i} style={{ display: "flex", flexDirection: "column", gap: "5px", paddingLeft: "4px" }}>
                {sec.items.map((item, j) => (
                  <div key={j} style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}>
                    <span style={{ color: "var(--amber-primary)", marginTop: "6px", flexShrink: 0 }}>▸</span>
                    <p style={{ margin: 0, fontSize: "13.5px", lineHeight: "1.7", color: "var(--text-primary)" }}>{item}</p>
                  </div>
                ))}
              </div>
            );
          }

          return null;
        })}
      </div>

      {/* ── Contradiction warning ─────────────────────────── */}
      {contradictions && contradictions.length > 0 && (
        <div className="contradiction-alert-box" style={{ marginTop: "12px" }}>
          <AlertTriangle size={16} style={{ color: "var(--rose-primary)", flexShrink: 0, marginTop: "2px" }} />
          <div>
            <div style={{ fontWeight: 600, color: "var(--rose-primary)", marginBottom: "4px" }}>
              Discrepancy Detected:
            </div>
            {contradictions.map((c, i) => (
              <div key={i} style={{ fontSize: "13px", marginBottom: "2px" }}>• {c}</div>
            ))}
          </div>
        </div>
      )}

      {/* ── Evidence classification badges ───────────────── */}
      {evidence_classification && evidence_classification.length > 0 && (
        <div className="findings-badge-grid" style={{ marginTop: "10px" }}>
          {evidence_classification.map((item, idx) => {
            const type = item.evidence_type || "FACT";
            let icon = <CheckCircle size={12} />;
            let cssClass = "direct-fact";
            if (type === "HYPOTHESIS") { icon = <HelpCircle size={12} />; cssClass = "hypothesis"; }
            else if (type === "RECOMMENDATION") { icon = <Sparkles size={12} />; cssClass = "recommendation"; }
            else if (type === "HISTORICAL_FACT") { icon = <Clock size={12} />; cssClass = "historical-fact"; }
            return (
              <div key={idx} className={`finding-tag ${cssClass}`}>
                {icon}
                <span style={{ fontWeight: 600 }}>{type}:</span>
                <span>{item.claim}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Follow-up suggestions ─────────────────────────── */}
      {follow_up_suggestions && follow_up_suggestions.length > 0 && (
        <div className="followup-suggestions-row" style={{ marginTop: "12px" }}>
          <div className="followup-title">SUGGESTED NEXT STEPS:</div>
          <div className="followup-chips">
            {follow_up_suggestions.map((sugg, idx) => (
              <button
                key={idx}
                type="button"
                className="followup-chip-btn"
                onClick={() => onSelectFollowUp && onSelectFollowUp(sugg)}
              >
                <span>{sugg}</span>
                <ArrowRight size={11} style={{ marginLeft: "4px", opacity: 0.7 }} />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
