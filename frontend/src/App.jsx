import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  Coins,
  FileText,
  Gauge,
  KeyRound,
  ListFilter,
  Plus,
  RefreshCcw,
  Server,
  ShieldCheck
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import api, { setAdminToken } from "./api";

const tabs = [
  { id: "overview", label: "Overview", icon: Gauge },
  { id: "keys", label: "API Keys", icon: KeyRound },
  { id: "logs", label: "Usage Logs", icon: ListFilter },
  { id: "costs", label: "Cost Analytics", icon: Coins },
  { id: "prompts", label: "Prompt Versions", icon: FileText },
  { id: "health", label: "Provider Health", icon: Server }
];

const palette = ["#2563eb", "#059669", "#f59e0b", "#dc2626", "#7c3aed", "#0f766e"];

function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [adminToken, setAdminTokenState] = useState(localStorage.getItem("llmops_admin_token") || "change-me-admin-token");
  const [state, setState] = useState({
    summary: null,
    keys: [],
    logs: [],
    prompts: [],
    health: null,
    loading: true,
    error: ""
  });
  const [newKeyName, setNewKeyName] = useState("recruiter-demo");
  const [newKey, setNewKey] = useState(null);
  const [promptForm, setPromptForm] = useState({
    prompt_id: "sales-assistant",
    name: "Sales Assistant",
    version: "v1",
    template: "You are a helpful sales assistant for $company."
  });

  async function loadData() {
    setAdminToken(adminToken);
    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const [summary, keys, logs, prompts, health] = await Promise.all([
        api.get("/api/admin/costs/summary"),
        api.get("/api/admin/api-keys"),
        api.get("/api/admin/usage?limit=100"),
        api.get("/api/admin/prompts"),
        api.get("/api/admin/providers/health")
      ]);
      setState({
        summary: summary.data,
        keys: keys.data,
        logs: logs.data,
        prompts: prompts.data,
        health: health.data,
        loading: false,
        error: ""
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        loading: false,
        error: error.response?.data?.detail || error.message
      }));
    }
  }

  useEffect(() => {
    localStorage.setItem("llmops_admin_token", adminToken);
    loadData();
  }, [adminToken]);

  const providerCostRows = useMemo(() => {
    const entries = Object.entries(state.summary?.cost_by_provider || {});
    return entries.length ? entries.map(([name, value]) => ({ name, value })) : [{ name: "No data", value: 0 }];
  }, [state.summary]);

  async function createKey(event) {
    event.preventDefault();
    const response = await api.post("/api/admin/api-keys", {
      name: newKeyName,
      rpm_limit: 60,
      tpd_limit: 10000
    });
    setNewKey(response.data.api_key);
    setNewKeyName("");
    loadData();
  }

  async function createPrompt(event) {
    event.preventDefault();
    await api.post("/api/admin/prompts", promptForm);
    setPromptForm((current) => ({ ...current, version: nextVersion(current.version) }));
    loadData();
  }

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-950">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">LLMOps Gateway</h1>
            <p className="mt-1 text-sm text-zinc-600">AI gateway operations, usage, cost, prompts, and provider routing.</p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <label className="text-xs font-medium uppercase text-zinc-500" htmlFor="admin-token">
              Admin Token
            </label>
            <input
              id="admin-token"
              className="h-10 min-w-72 border border-zinc-300 bg-white px-3 text-sm outline-none focus:border-blue-600"
              value={adminToken}
              onChange={(event) => setAdminTokenState(event.target.value)}
            />
            <button className="icon-button" onClick={loadData} title="Refresh dashboard">
              <RefreshCcw size={18} />
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[220px_1fr]">
        <nav className="flex gap-2 overflow-auto lg:flex-col">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                className={`nav-tab ${activeTab === tab.id ? "nav-tab-active" : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={18} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        <section className="min-w-0">
          {state.error && <div className="mb-4 border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{state.error}</div>}
          {state.loading ? <Loading /> : null}
          {!state.loading && activeTab === "overview" && <Overview summary={state.summary} logs={state.logs} />}
          {!state.loading && activeTab === "keys" && (
            <ApiKeys keys={state.keys} newKey={newKey} newKeyName={newKeyName} setNewKeyName={setNewKeyName} createKey={createKey} />
          )}
          {!state.loading && activeTab === "logs" && <UsageLogs logs={state.logs} />}
          {!state.loading && activeTab === "costs" && <CostAnalytics summary={state.summary} providerRows={providerCostRows} />}
          {!state.loading && activeTab === "prompts" && (
            <Prompts prompts={state.prompts} promptForm={promptForm} setPromptForm={setPromptForm} createPrompt={createPrompt} />
          )}
          {!state.loading && activeTab === "health" && <ProviderHealth health={state.health} />}
        </section>
      </div>
    </main>
  );
}

function Loading() {
  return <div className="border border-zinc-200 bg-white px-4 py-6 text-sm text-zinc-500">Loading dashboard data...</div>;
}

function Overview({ summary, logs }) {
  const successRate = logs.length ? Math.round((logs.filter((log) => log.status !== "failed").length / logs.length) * 100) : 100;
  const avgLatency = logs.length ? Math.round(logs.reduce((sum, log) => sum + log.latency_ms, 0) / logs.length) : 0;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Activity} label="Requests" value={summary.total_requests} />
        <StatCard icon={BarChart3} label="Tokens" value={summary.total_tokens.toLocaleString()} />
        <StatCard icon={Coins} label="Cost" value={`$${summary.total_cost.toFixed(6)}`} />
        <StatCard icon={ShieldCheck} label="Success" value={`${successRate}%`} sub={`${avgLatency} ms avg latency`} />
      </div>
      <Panel title="Daily Usage Trend">
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={summary.daily_usage_trend}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
            <XAxis dataKey="date" stroke="#71717a" />
            <YAxis stroke="#71717a" />
            <Tooltip />
            <Area type="monotone" dataKey="tokens" stroke="#2563eb" fill="#bfdbfe" />
          </AreaChart>
        </ResponsiveContainer>
      </Panel>
    </div>
  );
}

function ApiKeys({ keys, newKey, newKeyName, setNewKeyName, createKey }) {
  return (
    <div className="space-y-6">
      <Panel title="Create API Key">
        <form className="flex flex-col gap-3 sm:flex-row" onSubmit={createKey}>
          <input className="input flex-1" value={newKeyName} onChange={(event) => setNewKeyName(event.target.value)} placeholder="Key name" />
          <button className="primary-button" type="submit">
            <Plus size={18} />
            <span>Create</span>
          </button>
        </form>
        {newKey && <code className="mt-4 block overflow-auto bg-zinc-950 px-3 py-2 text-sm text-white">{newKey}</code>}
      </Panel>
      <Table
        columns={["Name", "Prefix", "RPM", "Tokens/Day", "Status", "Created"]}
        rows={keys.map((key) => [key.name, key.key_prefix, key.rpm_limit, key.tpd_limit, key.active ? "active" : "disabled", formatDate(key.created_at)])}
      />
    </div>
  );
}

function UsageLogs({ logs }) {
  return (
    <Table
      columns={["Time", "Provider", "Model", "Tokens", "Cost", "Latency", "Status"]}
      rows={logs.map((log) => [
        formatDate(log.created_at),
        log.provider,
        log.model,
        log.total_tokens,
        `$${log.estimated_cost.toFixed(6)}`,
        `${Math.round(log.latency_ms)} ms`,
        log.status
      ])}
    />
  );
}

function CostAnalytics({ summary, providerRows }) {
  return (
    <div className="space-y-6">
      <Panel title="Cost By Provider">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={providerRows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
            <XAxis dataKey="name" stroke="#71717a" />
            <YAxis stroke="#71717a" />
            <Tooltip />
            <Legend />
            <Bar dataKey="value" name="Cost">
              {providerRows.map((_, index) => (
                <Cell key={index} fill={palette[index % palette.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Panel>
      <Table
        columns={["API Key", "Cost"]}
        rows={Object.entries(summary.cost_by_api_key || {}).map(([key, cost]) => [key, `$${cost.toFixed(6)}`])}
      />
    </div>
  );
}

function Prompts({ prompts, promptForm, setPromptForm, createPrompt }) {
  return (
    <div className="space-y-6">
      <Panel title="New Prompt Version">
        <form className="grid grid-cols-1 gap-3 md:grid-cols-2" onSubmit={createPrompt}>
          <input className="input" value={promptForm.prompt_id} onChange={(e) => setPromptForm({ ...promptForm, prompt_id: e.target.value })} />
          <input className="input" value={promptForm.name} onChange={(e) => setPromptForm({ ...promptForm, name: e.target.value })} />
          <input className="input" value={promptForm.version} onChange={(e) => setPromptForm({ ...promptForm, version: e.target.value })} />
          <button className="primary-button" type="submit">
            <Plus size={18} />
            <span>Save Version</span>
          </button>
          <textarea
            className="input min-h-28 md:col-span-2"
            value={promptForm.template}
            onChange={(e) => setPromptForm({ ...promptForm, template: e.target.value })}
          />
        </form>
      </Panel>
      <Table
        columns={["Prompt ID", "Name", "Version", "Template", "Created"]}
        rows={prompts.map((prompt) => [prompt.prompt_id, prompt.name, prompt.version, prompt.template, formatDate(prompt.created_at)])}
      />
    </div>
  );
}

function ProviderHealth({ health }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {(health?.providers || []).map((provider) => (
        <div key={provider.model} className="border border-zinc-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-zinc-500">{provider.provider}</p>
              <h3 className="mt-1 text-lg font-semibold">{provider.model}</h3>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">{provider.status}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="border border-zinc-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-zinc-500">{label}</p>
        <Icon size={18} className="text-zinc-500" />
      </div>
      <p className="mt-4 text-2xl font-semibold">{value}</p>
      {sub && <p className="mt-1 text-xs text-zinc-500">{sub}</p>}
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div className="border border-zinc-200 bg-white p-4">
      <h2 className="mb-4 text-base font-semibold">{title}</h2>
      {children}
    </div>
  );
}

function Table({ columns, rows }) {
  return (
    <div className="overflow-hidden border border-zinc-200 bg-white">
      <div className="overflow-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-zinc-200 bg-zinc-100 text-xs uppercase text-zinc-500">
            <tr>
              {columns.map((column) => (
                <th key={column} className="whitespace-nowrap px-4 py-3 font-semibold">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length ? (
              rows.map((row, rowIndex) => (
                <tr key={rowIndex} className="border-b border-zinc-100 last:border-b-0">
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="max-w-md whitespace-nowrap px-4 py-3 text-zinc-700">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-4 py-8 text-center text-zinc-500" colSpan={columns.length}>
                  No records found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "-";
}

function nextVersion(version) {
  const match = version.match(/^v(\d+)$/);
  return match ? `v${Number(match[1]) + 1}` : version;
}

export default App;
