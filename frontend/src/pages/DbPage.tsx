import React, { useEffect, useState } from 'react';
import { deleteRegisteredUser, getRegisteredUsers, type RegisteredUserItem } from '../api/face';

const DbPage: React.FC = () => {
  const [users, setUsers] = useState<RegisteredUserItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRegisteredUsers();
      setUsers(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  return (
    <div className="h-full w-full flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-white">DB Manager</h1>
        <button
          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
          onClick={loadUsers}
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      {error && <div className="p-3 bg-red-900/50 border border-red-700 text-red-200 rounded">{error}</div>}

      <div className="overflow-auto rounded border border-gray-700 bg-gray-900/40">
        <table className="w-full text-sm">
          <thead className="bg-gray-800 text-gray-200">
            <tr>
              <th className="text-left px-3 py-2">ID</th>
              <th className="text-left px-3 py-2">Employee ID</th>
              <th className="text-left px-3 py-2">Name</th>
              <th className="text-left px-3 py-2">Embeddings</th>
              <th className="text-left px-3 py-2">Created</th>
              <th className="text-left px-3 py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-gray-400">
                  No registered users
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.id} className="border-t border-gray-800 text-gray-100">
                  <td className="px-3 py-2">{u.id}</td>
                  <td className="px-3 py-2">{u.employee_id}</td>
                  <td className="px-3 py-2">{u.name}</td>
                  <td className="px-3 py-2">{u.embedding_count}</td>
                  <td className="px-3 py-2">{u.created_at ?? '-'}</td>
                  <td className="px-3 py-2">
                    <button
                      className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-white"
                      onClick={async () => {
                        const ok = window.confirm(`Delete user ${u.name} (${u.employee_id})?`);
                        if (!ok) return;
                        await deleteRegisteredUser(u.id);
                        await loadUsers();
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DbPage;
