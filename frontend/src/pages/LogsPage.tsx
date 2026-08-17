import React, { useEffect, useMemo, useState } from 'react';
import { clearLogs, getRecentLogs, type LogItem } from '../api/face';

const LogsPage: React.FC = () => {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');

  const loadLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRecentLogs(800);
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    const timer = setInterval(() => {
      loadLogs();
    }, 1500);
    return () => clearInterval(timer);
  }, [autoRefresh]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return logs;
    return logs.filter((x) =>
      `${x.timestamp} ${x.level} ${x.source} ${x.message}`.toLowerCase().includes(q)
    );
  }, [logs, query]);

  return (
    <div className="h-full w-full flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-white">Server Logs</h1>
        <button
          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
          onClick={loadLogs}
          disabled={loading}
        >
          Refresh
        </button>
        <button
          className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded"
          onClick={async () => {
            await clearLogs();
            await loadLogs();
          }}
        >
          Clear
        </button>
        <label className="text-gray-300 text-sm flex items-center gap-2">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
          />
          Auto refresh
        </label>
      </div>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Filter logs..."
        className="w-full px-3 py-2 bg-gray-800 text-white border border-gray-700 rounded"
      />

      {error && <div className="p-3 bg-red-900/50 border border-red-700 text-red-200 rounded">{error}</div>}

      <div className="flex-1 overflow-auto rounded border border-gray-700 bg-black/50 p-3 font-mono text-xs">
        {filtered.length === 0 ? (
          <div className="text-gray-400">No logs</div>
        ) : (
          filtered.map((log, idx) => (
            <div key={`${log.timestamp}-${idx}`} className="whitespace-pre-wrap break-words text-gray-200 py-0.5">
              [{log.timestamp}] [{log.level}] [{log.source}] {log.message}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LogsPage;
