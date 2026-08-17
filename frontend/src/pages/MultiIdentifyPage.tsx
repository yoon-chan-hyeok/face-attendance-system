import React, { useMemo, useRef, useState } from 'react';
import { identifyUsersFromPhoto, type MultiIdentifyResponse } from '../api/face';

const MultiIdentifyPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MultiIdentifyResponse | null>(null);
  const [naturalSize, setNaturalSize] = useState<{ w: number; h: number } | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const previewUrl = useMemo(() => {
    if (!selectedFile) return null;
    return URL.createObjectURL(selectedFile);
  }, [selectedFile]);

  return (
    <div className="h-full w-full flex flex-col gap-6">
      <h1 className="text-3xl font-bold text-white">Multi-Face Photo Mode</h1>

      <div className="bg-gray-800/60 border border-gray-700 rounded-lg p-4">
        <p className="text-gray-300 text-sm mb-3">
          Upload a group photo to identify multiple people in one image.
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={(e) => {
            const file = e.target.files?.[0] ?? null;
            setSelectedFile(file);
            setResult(null);
            setError(null);
          }}
          className="hidden"
        />
        <div className="flex items-center gap-2">
          <button
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded"
            onClick={() => fileInputRef.current?.click()}
          >
            Upload Image
          </button>
          <span className="text-sm text-gray-300">
            {selectedFile ? selectedFile.name : 'No file selected'}
          </span>
        </div>
        <div className="mt-4 flex gap-2">
          <button
            onClick={async () => {
              if (!selectedFile) {
                setError('Please select an image first.');
                return;
              }
              setLoading(true);
              setError(null);
              setResult(null);
              try {
                const data = await identifyUsersFromPhoto(selectedFile);
                setResult(data);
              } catch (err: any) {
                setError(err.message || 'Failed to identify faces.');
              } finally {
                setLoading(false);
              }
            }}
            disabled={loading}
            className={`px-4 py-2 rounded text-white ${
              loading ? 'bg-gray-600' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {loading ? 'Processing...' : 'Identify Faces'}
          </button>
        </div>
      </div>

      {previewUrl && (
        <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
          <div className="relative inline-block">
            <img
              src={previewUrl}
              alt="preview"
              className="max-h-[420px] rounded border border-gray-700"
              onLoad={(e) => {
                const img = e.currentTarget;
                setNaturalSize({ w: img.naturalWidth, h: img.naturalHeight });
              }}
            />

            {result && naturalSize && (
              <div className="absolute inset-0 pointer-events-none">
                {result.results.map((item) => {
                  const fa = item.facial_area || {};
                  const x = Number(fa.x);
                  const y = Number(fa.y);
                  const w = Number(fa.w);
                  const h = Number(fa.h);
                  if ([x, y, w, h].some((v) => Number.isNaN(v))) return null;

                  const left = `${(x / naturalSize.w) * 100}%`;
                  const top = `${(y / naturalSize.h) * 100}%`;
                  const width = `${(w / naturalSize.w) * 100}%`;
                  const height = `${(h / naturalSize.h) * 100}%`;
                  const label = item.identified
                    ? `${item.user?.name ?? 'Matched'} (${(item.distance ?? 0).toFixed(3)})`
                    : `Unknown (${item.failure_reason ?? 'N/A'})`;

                  return (
                    <div
                      key={`box-${item.face_index}`}
                      className={`absolute border-2 ${item.identified ? 'border-green-400' : 'border-yellow-300'}`}
                      style={{ left, top, width, height }}
                    >
                      <div
                        className={`absolute -top-6 left-0 text-[11px] px-2 py-0.5 rounded text-white ${
                          item.identified ? 'bg-green-600/90' : 'bg-yellow-600/90'
                        }`}
                      >
                        {label}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-900/50 border border-red-700 text-red-200 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
          <h2 className="text-xl font-semibold text-white mb-3">
            Results ({result.face_count} faces)
          </h2>
          <div className="space-y-3">
            {result.results.map((item) => (
              <div key={item.face_index} className="p-3 rounded border border-gray-700 bg-gray-800/40">
                <div className="text-sm text-gray-300">Face #{item.face_index + 1}</div>
                <div className={`text-sm font-medium ${item.identified ? 'text-green-400' : 'text-yellow-300'}`}>
                  {item.message}
                </div>
                {item.user && (
                  <div className="text-xs text-gray-300 mt-1">
                    {item.user.name} ({item.user.employee_id})
                  </div>
                )}
                <div className="text-xs text-gray-400 mt-1">
                  distance={item.distance ?? 'N/A'}, second={item.second_distance ?? 'N/A'}, margin={item.margin ?? 'N/A'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiIdentifyPage;
