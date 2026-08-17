import React, { useEffect, useMemo, useRef, useState } from 'react';
import { clearLogs, getRecentLogs, type LogItem } from '../../api/face';

const BottomLogPanel: React.FC = () => {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [collapsed, setCollapsed] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState('');
  const viewportRef = useRef<HTMLDivElement | null>(null);

  const load = async () => {
    try {
      const data = await getRecentLogs(500);
      setLogs(data);
    } catch {
      // Keep panel silent on network errors to avoid UI noise.
    }
  };

  useEffect(() => {
    load();
    if (!autoRefresh) return;
    const timer = setInterval(load, 1500);
    return () => clearInterval(timer);
  }, [autoRefresh]);

  useEffect(() => {
    if (!autoScroll || collapsed) return;
    if (viewportRef.current) {
      viewportRef.current.scrollTop = viewportRef.current.scrollHeight;
    }
  }, [logs, autoScroll, collapsed]);

  const filteredLogs = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return logs;
    return logs.filter((x) =>
      `${x.timestamp} ${x.level} ${x.source} ${x.message}`.toLowerCase().includes(q)
    );
  }, [logs, filter]);

  return (
    <div className="border-t border-gray-800 bg-black/70 backdrop-blur-sm">
      <div className="flex items-center gap-3 px-4 py-2">
        <div className="text-xs font-semibold text-gray-300">Live Logs</div>
        <button
          className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 text-gray-100"
          onClick={() => setCollapsed((v) => !v)}
        >
          {collapsed ? 'Expand' : 'Collapse'}
        </button>
        <button
          className="text-xs px-2 py-1 rounded bg-blue-700 hover:bg-blue-600 text-gray-100"
          onClick={load}
        >
          Refresh
        </button>
        <button
          className="text-xs px-2 py-1 rounded bg-red-700 hover:bg-red-600 text-gray-100"
          onClick={async () => {
            await clearLogs();
            setLogs([]);
          }}
        >
          Reset
        </button>
        <label className="text-xs text-gray-300 flex items-center gap-1">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
          />
          Auto refresh
        </label>
        <label className="text-xs text-gray-300 flex items-center gap-1">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
          />
          Auto scroll
        </label>
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter..."
          className="ml-auto w-56 bg-gray-800 text-gray-100 border border-gray-700 rounded px-2 py-1 text-xs"
        />
      </div>

      {!collapsed && (
        <div
          ref={viewportRef}
          className="h-44 overflow-y-auto px-4 pb-3 font-mono text-[11px] leading-5 text-gray-200"
        >
          {filteredLogs.length === 0 ? (
            <div className="text-gray-500">No logs</div>
          ) : (
            filteredLogs.map((log, idx) => (
              <div key={`${log.timestamp}-${idx}`} className="whitespace-pre-wrap break-words">
                [{log.timestamp}] [{log.level}] [{log.source}] {log.message}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default BottomLogPanel;
