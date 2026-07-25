import { useEffect, useState } from "react";
import { createSite, getHealth } from "./api.js";
import SiteDrawer from "./components/SiteDrawer.jsx";

export default function App() {
  const [health, setHealth] = useState("проверяем…");
  const [site, setSite] = useState(null);
  const [rootOption, setRootOption] = useState(null);
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
      setRootOption(created.root_option);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function handleReset() {
    setSite(null);
    setRootOption(null);
    setError(null);
  }

  const metrics = rootOption?.result?.metrics;

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

      {site && metrics && (
        <section className="site-summary">
          <p>Участок сохранён, посчитан корневой вариант застройки.</p>
          <ul>
            <li>Площадь участка: {metrics.site_area_m2} м²</li>
            <li>Застраиваемая площадь: {metrics.buildable_area_m2} м²</li>
            <li>Зданий: {metrics.building_count}</li>
            <li>Общая площадь этажей (GFA): {metrics.gfa_m2} м²</li>
          </ul>
        </section>
      )}
    </main>
  );
}
