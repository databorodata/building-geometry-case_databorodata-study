import { useEffect, useState } from "react";
import { createOption, createSite, getHealth } from "./api.js";
import Board from "./components/Board.jsx";
import Editor from "./components/Editor.jsx";
import SiteDrawer from "./components/SiteDrawer.jsx";

export default function App() {
  const [health, setHealth] = useState("проверяем…");
  const [site, setSite] = useState(null);
  const [options, setOptions] = useState([]);
  const [editing, setEditing] = useState(null);
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
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveOption(base, name, params) {
    const saved = await createOption(site.id, base.id, name, params);
    setOptions((current) => [...current, saved]);
    setEditing(saved);
    return saved;
  }

  function handleReset() {
    if (!window.confirm("Сбросить доску и вернуться к заданию участка?")) return;
    setSite(null);
    setOptions([]);
    setEditing(null);
    setError(null);
  }

  return (
    <main className="app">
      <header className="app-header">
        <h1>{site ? site.name : "Задание участка"}</h1>
        <div className="header-right">
          {site && (
            <button type="button" onClick={handleReset}>
              Задать участок заново
            </button>
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

      {site && <Board options={options} onOpen={(option) => setEditing(option)} />}

      {editing && <Editor site={site} option={editing} onSave={handleSaveOption} onClose={() => setEditing(null)} />}
    </main>
  );
}
