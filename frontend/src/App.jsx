import { useState, useCallback, useRef, useEffect } from "react";

// ── API ─────────────────────────────────────────────────────────────────────

const api = async (path, options = {}) => {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Server error ${res.status}`);
  }
  return res.json();
};

// ── Sample ──────────────────────────────────────────────────────────────────

const SAMPLE_ORDINANCE = `ORDINANCE NO. 2024-0187

AN ORDINANCE OF THE CITY COUNCIL OF THE CITY OF GREENFIELD AMENDING CHAPTER 8.60 
OF THE GREENFIELD MUNICIPAL CODE RELATING TO POLYSTYRENE AND PFAS-FREE FOOD SERVICE WARE

THE CITY COUNCIL OF THE CITY OF GREENFIELD DOES HEREBY ORDAIN AS FOLLOWS:

SECTION 1. PURPOSE AND FINDINGS.
The City Council finds that expanded polystyrene (EPS) foam food service ware and food 
packaging containing per- and polyfluoroalkyl substances (PFAS) pose significant threats 
to public health and the environment.

SECTION 2. DEFINITIONS.
(a) "Food Provider" means any restaurant, cafeteria, food truck, mobile food vendor, 
grocery store, delicatessen, coffee shop, or other business that provides prepared food 
for consumption on or off premises.
(b) "Polystyrene" means expanded polystyrene (EPS), extruded polystyrene (XPS), and 
polystyrene #6.
(c) "PFAS" means per- and polyfluoroalkyl substances, including PFOA, PFOS, and related compounds.
(d) "Food Service Ware" means containers, cups, plates, bowls, trays, cartons, utensils, 
straws, lids, and similar items used for serving or packaging food.

SECTION 3. PROHIBITIONS.
(a) Effective January 1, 2025, no Food Provider shall sell, offer for sale, or distribute 
any polystyrene food service ware.
(b) Effective July 1, 2025, no Food Provider shall sell, offer for sale, or distribute 
any food service ware containing intentionally added PFAS.
(c) Single-use plastic straws, stirrers, and utensils shall be provided only upon request 
by the customer.

SECTION 4. REQUIRED ALTERNATIVES.
All food service ware shall be either:
(a) Compostable and certified by BPI or equivalent certification body, or
(b) Recyclable and accepted by the City's curbside recycling program, or
(c) Reusable.

SECTION 5. EXEMPTIONS.
(a) Packaging for raw meat, fish, and poultry.
(b) Food service ware provided by healthcare facilities for medical purposes.
(c) Food distributed by government agencies during emergency disaster relief.
(d) Pre-packaged food sealed prior to receipt by the Food Provider.

SECTION 6. LABELING.
All compostable food service ware must be clearly labeled "Compostable" with green color 
coding. All recyclable food service ware must display the universal recycling symbol.

SECTION 7. ENFORCEMENT AND PENALTIES.
(a) The Department of Environmental Services shall enforce this ordinance.
(b) First violation: Written warning and compliance deadline of 30 days.
(c) Second violation: Administrative fine of $250.
(d) Third and subsequent violations: Administrative fine of $500 per violation.
(e) The City may also seek injunctive relief in addition to administrative penalties.
City facilities and city contractors and lessees must comply by October 1, 2024.

SECTION 8. EFFECTIVE DATE.
This ordinance shall take effect on January 1, 2025.

PASSED AND ADOPTED by the City Council of the City of Greenfield on September 15, 2024.`;

// ── Tokens ──────────────────────────────────────────────────────────────────

const FONT = `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`;
const MONO = `'SF Mono', 'Fira Code', 'Consolas', monospace`;

const c = {
  bg: "#f8f9fa",
  white: "#ffffff",
  border: "#e2e8f0",
  borderLight: "#edf2f7",
  text: "#1a202c",
  textSecondary: "#4a5568",
  muted: "#718096",
  dim: "#a0aec0",
  accent: "#2b6cb0",
  accentLight: "#ebf4ff",
  green: "#276749",
  greenBg: "#c6f6d5",
  greenLight: "#f0fff4",
  amber: "#975a16",
  amberBg: "#fefcbf",
  amberLight: "#fffff0",
  red: "#c53030",
  redBg: "#fed7d7",
  redLight: "#fff5f5",
  purple: "#553c9a",
  purpleBg: "#e9d8fd",
};

// ── Shared Components ───────────────────────────────────────────────────────

function StatusBadge({ children, variant = "green" }) {
  const styles = {
    green: { color: c.green, background: c.greenBg },
    amber: { color: c.amber, background: c.amberBg },
    red: { color: c.red, background: c.redBg },
    blue: { color: c.accent, background: c.accentLight },
    purple: { color: c.purple, background: c.purpleBg },
  };
  const s = styles[variant] || styles.green;
  return (
    <span
      style={{
        display: "inline-block",
        padding: "3px 12px",
        borderRadius: 4,
        fontSize: 12,
        fontWeight: 600,
        ...s,
      }}
    >
      {children}
    </span>
  );
}

function SidebarItem({ icon, label, value }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "10px 0" }}>
      <span style={{ color: c.muted, fontSize: 16, marginTop: 1, width: 20, textAlign: "center" }}>{icon}</span>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, color: c.text }}>{label}</div>
        {value !== null && <div style={{ fontSize: 13, color: c.textSecondary, marginTop: 1 }}>{value}</div>}
      </div>
    </div>
  );
}

function Tab({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "10px 20px",
        border: "none",
        borderBottom: active ? `2px solid ${c.accent}` : "2px solid transparent",
        background: "none",
        color: active ? c.text : c.muted,
        fontSize: 14,
        fontWeight: active ? 600 : 400,
        cursor: "pointer",
        fontFamily: FONT,
        transition: "all 0.15s",
      }}
    >
      {children}
    </button>
  );
}

function SectionHeading({ children }) {
  return (
    <h3 style={{ fontSize: 16, fontWeight: 700, color: c.text, margin: "0 0 12px 0" }}>
      {children}
    </h3>
  );
}

function EditableText({ value, onChange, multiline = false, placeholder = "" }) {
  const style = {
    width: "100%",
    padding: "8px 12px",
    borderRadius: 6,
    border: `1px solid ${c.borderLight}`,
    background: c.bg,
    color: c.text,
    fontSize: 14,
    lineHeight: 1.7,
    fontFamily: FONT,
    outline: "none",
    boxSizing: "border-box",
    transition: "border-color 0.15s",
    resize: multiline ? "vertical" : "none",
  };
  if (multiline) {
    return (
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={3}
        style={{ ...style, minHeight: 60 }}
        onFocus={(e) => (e.target.style.borderColor = c.accent)}
        onBlur={(e) => (e.target.style.borderColor = c.borderLight)}
      />
    );
  }
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={style}
      onFocus={(e) => (e.target.style.borderColor = c.accent)}
      onBlur={(e) => (e.target.style.borderColor = c.borderLight)}
    />
  );
}

function EditableList({ items, onChange }) {
  if (!items || items.length === 0) return null;
  const isDefault = items.length === 1 && items[0].toLowerCase().startsWith("no ");

  const updateItem = (idx, val) => {
    const next = [...items];
    next[idx] = val;
    onChange(next);
  };
  const removeItem = (idx) => {
    const next = items.filter((_, i) => i !== idx);
    onChange(next.length > 0 ? next : ["Not specified."]);
  };
  const addItem = () => onChange([...items, ""]);

  return (
    <div>
      {items.map((item, i) => (
        <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "flex-start" }}>
          <textarea
            value={item}
            onChange={(e) => updateItem(i, e.target.value)}
            rows={1}
            style={{
              flex: 1, padding: "8px 12px", borderRadius: 6,
              border: `1px solid ${c.borderLight}`, background: c.bg,
              color: isDefault ? c.muted : c.text, fontSize: 14, lineHeight: 1.6,
              fontFamily: FONT, outline: "none", boxSizing: "border-box",
              resize: "vertical", minHeight: 38,
              fontStyle: isDefault ? "italic" : "normal",
              transition: "border-color 0.15s",
            }}
            onFocus={(e) => {
              e.target.style.borderColor = c.accent;
              if (isDefault) { onChange([""]); }
            }}
            onBlur={(e) => (e.target.style.borderColor = c.borderLight)}
          />
          {!isDefault && (
            <button
              onClick={() => removeItem(i)}
              style={{
                padding: "8px 10px", borderRadius: 6, border: `1px solid ${c.border}`,
                background: c.white, color: c.dim, fontSize: 13, cursor: "pointer",
                fontFamily: FONT, flexShrink: 0,
              }}
              title="Remove"
            >
              ✕
            </button>
          )}
        </div>
      ))}
      {!isDefault && (
        <button
          onClick={addItem}
          style={{
            padding: "6px 14px", borderRadius: 6, border: `1px dashed ${c.border}`,
            background: "none", color: c.muted, fontSize: 13, cursor: "pointer",
            fontFamily: FONT, marginTop: 4,
          }}
        >
          + Add item
        </button>
      )}
    </div>
  );
}

function BulletList({ items }) {
  if (!items || items.length === 0) return null;
  const isDefault = items.length === 1 && items[0].toLowerCase().startsWith("no ");
  if (isDefault) {
    return <div style={{ fontSize: 14, color: c.muted, fontStyle: "italic" }}>{items[0]}</div>;
  }
  return (
    <ul style={{ margin: 0, paddingLeft: 20, listStyle: "disc" }}>
      {items.map((item, i) => (
        <li key={i} style={{ fontSize: 14, color: c.textSecondary, lineHeight: 1.7, marginBottom: 4 }}>
          {item}
        </li>
      ))}
    </ul>
  );
}

function SignalGrid({ signals, title }) {
  if (!signals) return null;
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: c.muted, textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 10 }}>
        {title}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 6 }}>
        {Object.entries(signals).map(([key, val]) => (
          <div
            key={key}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "8px 12px",
              borderRadius: 6,
              background: val ? c.greenLight : c.bg,
              border: `1px solid ${val ? "#c6f6d5" : c.border}`,
            }}
          >
            <div style={{ width: 8, height: 8, borderRadius: 4, background: val ? c.green : c.dim, flexShrink: 0 }} />
            <span style={{ fontSize: 12, fontFamily: MONO, color: val ? c.green : c.dim }}>
              {key.replace(/^(contains_|mentions_)/, "")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RuleCard({ rule }) {
  return (
    <div style={{ padding: 16, borderRadius: 8, border: `1px solid ${c.border}`, background: c.white, marginBottom: 10 }}>
      <div style={{ marginBottom: 8 }}>
        <StatusBadge variant="purple">{rule.rule_type}</StatusBadge>
      </div>
      <div style={{ fontSize: 14, color: c.text, marginBottom: 6, lineHeight: 1.5 }}>
        <strong>Outcome:</strong> {rule.assertion_outcome}
      </div>
      <div style={{ fontSize: 13, color: c.muted, lineHeight: 1.5, fontStyle: "italic", marginBottom: 8 }}>
        {rule.reason_template}
      </div>
      {rule.applicability_conditions && (
        <div style={{ padding: "10px 12px", borderRadius: 6, background: c.bg }}>
          {rule.applicability_conditions.all?.length > 0 && (
            <div style={{ marginBottom: 4, fontSize: 13 }}>
              <span style={{ fontWeight: 600, color: c.green }}>ALL: </span>
              <span style={{ color: c.textSecondary }}>{rule.applicability_conditions.all.join(" AND ")}</span>
            </div>
          )}
          {rule.applicability_conditions.any?.length > 0 && (
            <div style={{ fontSize: 13 }}>
              <span style={{ fontWeight: 600, color: c.amber }}>ANY: </span>
              <span style={{ color: c.textSecondary }}>{rule.applicability_conditions.any.join(" OR ")}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ValidationPanel({ issues }) {
  if (!issues || issues.length === 0) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "14px 18px", background: c.greenLight, borderRadius: 8, border: "1px solid #c6f6d5" }}>
        <span style={{ color: c.green, fontSize: 16 }}>✓</span>
        <span style={{ color: c.green, fontSize: 14, fontWeight: 500 }}>All fields validated successfully</span>
      </div>
    );
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {issues.map((issue, i) => {
        const isErr = issue.severity === "error";
        return (
          <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "12px 16px", borderRadius: 8, background: isErr ? c.redLight : c.amberLight, border: `1px solid ${isErr ? "#fed7d7" : "#fefcbf"}` }}>
            <span style={{ fontSize: 14, marginTop: 1, color: isErr ? c.red : c.amber }}>{isErr ? "✕" : "⚠"}</span>
            <div>
              <div style={{ fontSize: 13, fontFamily: MONO, color: isErr ? c.red : c.amber, fontWeight: 600, marginBottom: 2 }}>{issue.field}</div>
              <div style={{ fontSize: 13, color: c.textSecondary }}>{issue.message}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════════════════════════

export default function App() {
  const [view, setView] = useState("input");
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [editDoc, setEditDoc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("overview");
  const ref = useRef(null);

  const canSubmit = !loading && text.trim().length >= 50;

  // Helper to update a single field on the editable doc
  const updateField = (field, value) => {
    setEditDoc((prev) => ({ ...prev, [field]: value }));
  };

  const handleExtract = useCallback(async () => {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api("/api/extract", {
        method: "POST",
        body: JSON.stringify({ legislative_text: text }),
      });
      setResult(data);
      setEditDoc(JSON.parse(JSON.stringify(data.document)));
      setTab("overview");
      setView("results");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [text, canSubmit]);

  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        handleExtract();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleExtract]);

  const handleDownload = () => {
    if (!editDoc) return;
    const blob = new Blob([JSON.stringify(editDoc, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const name = editDoc?.jurisdiction || "extraction";
    a.download = `${name.replace(/\s+/g, "_").toLowerCase()}_ordinance.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const doc = editDoc;

  const getRegTypes = () => {
    if (!doc?.rule_signals) return [];
    const types = [];
    if (doc.rule_signals.contains_polystyrene_ban) types.push("Polystyrene Ban");
    if (doc.rule_signals.contains_pfas_ban) types.push("PFAS Ban");
    if (doc.rule_signals.contains_packaging_ban) types.push("Packaging Ban");
    if (doc.rule_signals.contains_upon_request_rule) types.push("Upon Request");
    if (doc.rule_signals.contains_alternative_requirement) types.push("Alternative Req.");
    if (types.length === 0) types.push("Material Ban");
    return types;
  };

  // ═════════════════════════════════════════════════════════════════════════
  // INPUT VIEW
  // ═════════════════════════════════════════════════════════════════════════

  if (view === "input" && !loading) {
    return (
      <div style={{ minHeight: "100vh", background: c.bg, fontFamily: FONT, color: c.text }}>
        <header style={{ background: c.white, borderBottom: `1px solid ${c.border}`, padding: "12px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 20, fontWeight: 700, color: c.accent }}>§</span>
            <span style={{ fontSize: 15, fontWeight: 600 }}>LegParser</span>
            <span style={{ fontSize: 12, color: c.dim, marginLeft: 4 }}>v2.0</span>
          </div>
          {result && (
            <button
              onClick={() => setView("results")}
              style={{ padding: "7px 16px", borderRadius: 6, border: `1px solid ${c.border}`, background: c.white, color: c.textSecondary, fontSize: 13, fontWeight: 500, cursor: "pointer", fontFamily: FONT }}
            >
              View Last Result →
            </button>
          )}
        </header>

        <div style={{ maxWidth: 1000, margin: "40px auto", padding: "0 24px" }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Extract Ordinance Data</h1>
          <p style={{ fontSize: 14, color: c.muted, marginBottom: 24 }}>
            Paste legislative text below to extract structured data using AI.
          </p>

          <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <label style={{ fontSize: 14, fontWeight: 600 }}>Legislative Text</label>
              <div style={{ display: "flex", gap: 8 }}>
                <span style={{ fontSize: 12, color: c.dim, fontFamily: MONO, lineHeight: "28px" }}>{text.length.toLocaleString()} chars</span>
                <button onClick={() => { setText(SAMPLE_ORDINANCE); ref.current?.focus(); }} style={{ padding: "5px 14px", borderRadius: 6, border: `1px solid ${c.border}`, background: c.bg, color: c.textSecondary, fontSize: 12, cursor: "pointer", fontFamily: FONT }}>
                  Load Sample
                </button>
                {text.length > 0 && (
                  <button onClick={() => setText("")} style={{ padding: "5px 14px", borderRadius: 6, border: `1px solid ${c.border}`, background: c.bg, color: c.textSecondary, fontSize: 12, cursor: "pointer", fontFamily: FONT }}>
                    Clear
                  </button>
                )}
              </div>
            </div>

            <textarea
              ref={ref}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste ordinance text here…"
              spellCheck={false}
              style={{
                width: "100%", minHeight: 480, resize: "vertical", padding: 16, borderRadius: 8,
                border: `1px solid ${c.border}`, background: c.bg, color: c.text, fontSize: 13,
                lineHeight: 1.7, fontFamily: MONO, outline: "none", boxSizing: "border-box",
                transition: "border-color 0.15s",
              }}
              onFocus={(e) => (e.target.style.borderColor = c.accent)}
              onBlur={(e) => (e.target.style.borderColor = c.border)}
            />

            {error && (
              <div style={{ marginTop: 12, padding: "10px 14px", borderRadius: 6, background: c.redLight, border: "1px solid #fed7d7", color: c.red, fontSize: 13 }}>
                {error}
              </div>
            )}

            <div style={{ marginTop: 16, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: 12, color: c.dim }}>
                {text.trim().length > 0 && text.trim().length < 50 ? `${50 - text.trim().length} more characters needed` : "⌘+Enter to extract"}
              </span>
              <button
                onClick={handleExtract}
                disabled={!canSubmit}
                style={{
                  padding: "10px 28px", borderRadius: 6, border: "none",
                  background: canSubmit ? c.accent : c.dim, color: "#fff",
                  fontSize: 14, fontWeight: 600, cursor: canSubmit ? "pointer" : "not-allowed",
                  fontFamily: FONT, transition: "background 0.15s",
                }}
              >
                Extract Information
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════════════════════
  // LOADING VIEW
  // ═════════════════════════════════════════════════════════════════════════

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", background: c.bg, fontFamily: FONT, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 16 }}>
        <div style={{ width: 36, height: 36, border: `3px solid ${c.border}`, borderTopColor: c.accent, borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <div style={{ fontSize: 14, color: c.textSecondary }}>Extracting with Claude Sonnet…</div>
        <div style={{ fontSize: 12, color: c.dim }}>Parsing text & validating against schema</div>
      </div>
    );
  }

  // ═════════════════════════════════════════════════════════════════════════
  // RESULTS VIEW
  // ═════════════════════════════════════════════════════════════════════════

  if (!doc) return null;

  const regTypes = getRegTypes();

  return (
    <div style={{ minHeight: "100vh", background: c.bg, fontFamily: FONT, color: c.text }}>
      <header style={{ background: c.white, borderBottom: `1px solid ${c.border}`, padding: "12px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 20, fontWeight: 700, color: c.accent }}>§</span>
          <span style={{ fontSize: 15, fontWeight: 600 }}>LegParser</span>
          <span style={{ fontSize: 12, color: c.dim, marginLeft: 4 }}>v2.0</span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setView("input")} style={{ padding: "7px 16px", borderRadius: 6, border: `1px solid ${c.border}`, background: c.white, color: c.textSecondary, fontSize: 13, fontWeight: 500, cursor: "pointer", fontFamily: FONT }}>
            ← New Extraction
          </button>
          <button onClick={handleDownload} style={{ padding: "7px 16px", borderRadius: 6, border: `1px solid ${c.border}`, background: c.white, color: c.textSecondary, fontSize: 13, fontWeight: 500, cursor: "pointer", fontFamily: FONT }}>
            ↓ Export JSON
          </button>
        </div>
      </header>

      <div style={{ display: "flex", maxWidth: 1440, margin: "0 auto", padding: "32px 24px", gap: 32 }}>
        {/* SIDEBAR */}
        <div style={{ width: 240, flexShrink: 0 }}>
          <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: "20px 20px 12px" }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>Key Details</h3>
            <div style={{ borderTop: `1px solid ${c.borderLight}` }}>
              <SidebarItem icon="⊙" label="Location" value={doc.jurisdiction} />
              <SidebarItem icon="⊙" label="Effective Date" value={doc.effective_date} />
              <SidebarItem
                icon="⊙"
                label="Phase-in Dates"
                value={doc.phase_in_dates?.[0]?.toLowerCase().startsWith("no ") ? "None" : doc.phase_in_dates?.join(", ")}
              />
              <SidebarItem icon="⊙" label="Regulation Type" value={null} />
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: -4, marginBottom: 12, paddingLeft: 30 }}>
              {regTypes.map((t) => (
                <StatusBadge key={t} variant="blue">{t}</StatusBadge>
              ))}
            </div>
          </div>

          <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: "16px 20px", marginTop: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 10 }}>Extraction Info</h3>
            <div style={{ fontSize: 12, color: c.muted, lineHeight: 1.8 }}>
              <div>Model: <span style={{ color: c.textSecondary }}>{result.model_used?.split("-").slice(0, 2).join(" ")}</span></div>
              <div>Tokens: <span style={{ color: c.textSecondary }}>{result.tokens_used?.toLocaleString()}</span></div>
              <div style={{ marginTop: 4 }}>
                Status: {result.is_valid
                  ? <StatusBadge variant="green">Valid</StatusBadge>
                  : <StatusBadge variant="amber">{result.issues?.length} issues</StatusBadge>}
              </div>
            </div>
          </div>
        </div>

        {/* MAIN */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, lineHeight: 1.3, marginBottom: 4 }}>
            {doc.ordinance_number !== "Not specified" ? `${doc.ordinance_number}: ` : ""}
            {doc.jurisdiction !== "Not specified" ? doc.jurisdiction : "Extraction Result"}
          </h1>
          <div style={{ marginBottom: 20 }}>
            <StatusBadge variant="green">Active</StatusBadge>
          </div>

          <div style={{ display: "flex", borderBottom: `1px solid ${c.border}`, marginBottom: 24, background: c.white, borderRadius: "8px 8px 0 0" }}>
            {[
              ["overview", "Overview"],
              ["requirements", "Requirements"],
              ["signals", "Signals"],
              ["logic", "Regulatory Logic"],
              ["validation", `Validation (${result.issues?.length || 0})`],
              ["json", "Raw JSON"],
            ].map(([key, label]) => (
              <Tab key={key} active={tab === key} onClick={() => setTab(key)}>{label}</Tab>
            ))}
          </div>

          {/* OVERVIEW */}
          {tab === "overview" && (
            <div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>Regulation Overview</SectionHeading>
                <EditableText value={doc.overview} onChange={(v) => updateField("overview", v)} multiline placeholder="Overview…" />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>Key Provisions</SectionHeading>
                <EditableList items={doc.provisions} onChange={(v) => updateField("provisions", v)} />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>Prohibited Items</SectionHeading>
                <EditableList items={doc.prohibited_items} onChange={(v) => updateField("prohibited_items", v)} />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>Required Alternatives</SectionHeading>
                <EditableList items={doc.required_alternatives} onChange={(v) => updateField("required_alternatives", v)} />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>Exemptions</SectionHeading>
                <EditableList items={doc.exemptions} onChange={(v) => updateField("exemptions", v)} />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>Penalties</SectionHeading>
                <EditableText value={doc.penalties} onChange={(v) => updateField("penalties", v)} multiline placeholder="Penalties…" />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24 }}>
                <SectionHeading>Enforcement Agency</SectionHeading>
                <EditableText value={doc.enforcement_agency} onChange={(v) => updateField("enforcement_agency", v)} placeholder="Agency name…" />
              </div>
            </div>
          )}

          {/* REQUIREMENTS */}
          {tab === "requirements" && (
            <div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>Covered Establishments</SectionHeading>
                <EditableList items={doc.covered_establishments} onChange={(v) => updateField("covered_establishments", v)} />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>SKU Types</SectionHeading>
                <EditableList items={doc.SKU_types} onChange={(v) => updateField("SKU_types", v)} />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>Labeling Requirements</SectionHeading>
                <EditableList items={doc.labeling_requirements} onChange={(v) => updateField("labeling_requirements", v)} />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>Utensils and Accessories Requirements</SectionHeading>
                <EditableList items={doc.utensils_and_accessories_requirements} onChange={(v) => updateField("utensils_and_accessories_requirements", v)} />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24, marginBottom: 24 }}>
                <SectionHeading>Operational Requirements</SectionHeading>
                <EditableList items={doc.operational_requirements} onChange={(v) => updateField("operational_requirements", v)} />
              </div>
              <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24 }}>
                <SectionHeading>Phase-in Dates</SectionHeading>
                <EditableList items={doc.phase_in_dates} onChange={(v) => updateField("phase_in_dates", v)} />
              </div>
            </div>
          )}

          {/* SIGNALS */}
          {tab === "signals" && (
            <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24 }}>
              <SignalGrid signals={doc.rule_signals} title="Rule Signals" />
              <SignalGrid signals={doc.legislative_text_signals} title="Legislative Text Signals" />
            </div>
          )}

          {/* LOGIC */}
          {tab === "logic" && (
            <div>
              <div style={{ fontSize: 13, color: c.muted, marginBottom: 12 }}>{doc.regulatory_logic?.length || 0} rule(s) extracted</div>
              {doc.regulatory_logic?.length > 0
                ? doc.regulatory_logic.map((rule, i) => <RuleCard key={i} rule={rule} />)
                : <div style={{ padding: 24, background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, color: c.muted, fontSize: 14 }}>No regulatory logic rules extracted.</div>}
            </div>
          )}

          {/* VALIDATION */}
          {tab === "validation" && (
            <div style={{ background: c.white, borderRadius: 10, border: `1px solid ${c.border}`, padding: 24 }}>
              <SectionHeading>Validation Results</SectionHeading>
              <ValidationPanel issues={result.issues} />
            </div>
          )}

          {/* JSON */}
          {tab === "json" && (
            <pre style={{ padding: 24, borderRadius: 10, background: c.white, border: `1px solid ${c.border}`, fontSize: 12, lineHeight: 1.6, fontFamily: MONO, color: c.textSecondary, overflow: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {JSON.stringify(doc, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}