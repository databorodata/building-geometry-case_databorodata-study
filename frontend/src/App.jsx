import { useEffect, useState } from "react";
import { compareOptions, createOption, createSite, getHealth } from "./api.js";
import Board from "./components/Board.jsx";
import CompareModal from "./components/CompareModal.jsx";
import Editor from "./components/Editor.jsx";
import SiteDrawer from "./components/SiteDrawer.jsx";

export default function App() {
  const [health, setHealth] = useState("проверяем…");
  const [site, setSite] = useState(null);
  const [options, setOptions] = useState([]);
  const [editing, setEditing] = useState(null);
  const [compareIds, setCompareIds] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getHealth()
      .then((data) => setHealth(data.status === "healthy" ? "работает" : data.status))
      .catch((err) => setHealth(`недоступен (${err.message})`));
  }, []);

  async function handleCreateSite(name, polygon) {
    setBusy(true);
    setError(null);
    try {
      const created = await createSite(name, polygon);
      setSite(created.site);
      setOptions([created.root_option]);
      setEditing(null);
      setCompareIds([]);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveOption(base, name, params, kind) {
    const saved = await createOption(site.id, base.id, name, params, kind);
    setOptions((current) => [...current, saved]);
    if (kind === "save") setEditing(saved);
    return saved;
  }

  function handleToggleCompare(optionId) {
    setCompareIds((current) => {
      if (current.includes(optionId)) return current.filter((id) => id !== optionId);
      if (current.length >= 2) return [current[1], optionId];
      return [...current, optionId];
    });
  }

  async function handleCompare() {
    setError(null);
    try {
      setComparison(await compareOptions(compareIds[0], compareIds[1]));
    } catch (err) {
      setError(err.message);
    }
  }

  function handleReset() {
    if (!window.confirm("Сбросить доску и вернуться к заданию участка?")) return;
    setSite(null);
    setOptions([]);
    setEditing(null);
    setCompareIds([]);
    setComparison(null);
    setError(null);
  }

  return (
    <main className="app">
      <header className="app-header">
        <h1>{site ? site.name : "Задание участка"}</h1>
        <div className="header-right">
          {site && (
            <>
              <button type="button" disabled={compareIds.length !== 2} onClick={handleCompare}>
                Сравнить выбранные
              </button>
              <button type="button" onClick={handleReset}>
                Задать участок заново
              </button>
            </>
          )}
          <span className={`health ${health === "работает" ? "ok" : "bad"}`}>API: {health}</span>
        </div>
      </header>

      {error && (
        <p className="error banner" onClick={() => setError(null)}>
          {error}
        </p>
      )}

      {!site && <SiteDrawer onCreate={handleCreateSite} busy={busy} error={error} />}

      {site && (
        <Board
          options={options}
          onOpen={(option) => setEditing(option)}
          compareIds={compareIds}
          onToggleCompare={handleToggleCompare}
        />
      )}

      {editing && <Editor site={site} option={editing} onSave={handleSaveOption} onClose={() => setEditing(null)} />}

      {comparison && <CompareModal comparison={comparison} onClose={() => setComparison(null)} />}
    </main>
  );
}
