import React from 'react';
import { type CheckInOutResponse } from '../../api/face';

interface Props {
  result: CheckInOutResponse;
}

export const IdentificationResult: React.FC<Props> = ({ result }) => {
  const isSuccess = result.success;
  const isCheckIn = result.action_type === 'IN';
  
  const borderColor = isSuccess ? 'border-green-500' : 'border-yellow-500';
  const titleColor = isSuccess ? 'text-green-400' : 'text-yellow-400';
  const actionColor = isCheckIn ? 'text-blue-400' : 'text-orange-400';
  const actionIcon = isCheckIn ? '🟢' : '🔴';

  // Format time
  const formatTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="fixed top-10 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-md px-4 pointer-events-none">
      <div className={`pointer-events-auto w-full p-6 rounded-lg border-2 bg-gray-900/95 shadow-2xl backdrop-blur-sm ${borderColor} animate-fadeIn`}>
        
        <div className="flex items-center justify-between mb-3">
          <h2 className={`text-xl font-bold ${titleColor}`}>
            {actionIcon} {result.message}
          </h2>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between pt-2 border-t border-gray-700">
            <div className="flex-1">
              <p className="text-lg font-semibold text-white">{result.employee_name}</p>
              <p className="text-sm text-gray-400">Employee ID: {result.employee_id}</p>
            </div>
            <div className={`text-2xl font-bold ${actionColor}`}>
              {result.action_type}
            </div>
          </div>
          
          <div className="pt-2 border-t border-gray-700">
            <p className="text-xs text-gray-400">
              Processed at: {formatTime(result.action_at)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};