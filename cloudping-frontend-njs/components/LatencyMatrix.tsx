'use client';
import { useState, useEffect } from 'react';
import Image from 'next/image';
import StripeButton from './StripeButton';
import RegionFilterPanel from './RegionFilterPanel';

interface LatencyData {
  metadata: {
    timestamp: string;
    percentile: string;
    timeframe: string;
    unit: string;
  };
  data: {
    [key: string]: {
      [key: string]: number;
    };
  };
}

interface LatencyMatrixProps {
  initialData: LatencyData;
}

export default function LatencyMatrix({ initialData }: LatencyMatrixProps) {
  const [selectedPercentile, setSelectedPercentile] = useState('p_50');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1D');
  const [data, setData] = useState<LatencyData | null>(initialData);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);
  
  // Get all available regions
  const allRegions = data?.data ? Object.keys(data.data).sort() : [];
  
  // State for selected regions (initially all regions)
  const [selectedRegions, setSelectedRegions] = useState<string[]>(allRegions);
  
  // Update selected regions when data changes
  useEffect(() => {
    if (data?.data) {
      const newRegions = Object.keys(data.data).sort();
      setSelectedRegions(prevSelected => {
        // Add any new regions to the selection
        const updatedSelection = [...prevSelected];
        let changed = false;
        
        newRegions.forEach(region => {
          if (!prevSelected.includes(region)) {
            updatedSelection.push(region);
            changed = true;
          }
        });
        
        // Only update state if there were changes
        return changed ? updatedSelection : prevSelected;
      });
    }
  }, [data]); // Remove selectedRegions from dependency array

  const getLatencyColor = (latency: number): string => {
    if (latency < 100) return 'bg-green-500';
    if (latency < 180) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const updateData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await fetch(`/api/latencies?percentile=${selectedPercentile}&timeframe=${selectedTimeframe}`);
      if (!res.ok) {
        throw new Error(`Error fetching data: ${res.statusText}`);
      }
      const newData = await res.json();
      if (!newData || !newData.data) {
        throw new Error('Invalid data received from server');
      }
      setData(newData);
    } catch (error) {
      console.error('Failed to update data:', error);
      setError(error instanceof Error ? error.message : 'Failed to update data');
      // Keep the old data displayed
    } finally {
      setIsLoading(false);
    }
  };

  if (!data) {
    return <div className="text-white">Loading...</div>;
  }

  // Use only the selected regions for display
  const displayRegions = allRegions.filter(region => selectedRegions.includes(region));

  return (
    <div className="w-full max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-white">AWS Region Latency Matrix</h1>
        {isLoading && (
          <div className="text-sm text-zinc-400 flex items-center gap-2">
            <div className="animate-spin h-4 w-4 border-2 border-zinc-500 border-t-zinc-200 rounded-full"></div>
            Updating...
          </div>
        )}
      </div>
      
      {error && (
        <div className="mb-4 p-2 bg-red-900/50 border border-red-500 text-red-200 rounded text-sm">
          {error}
        </div>
      )}

      <div className="flex flex-wrap gap-4 mb-6 items-center">
        <div>
          <select 
            value={selectedPercentile}
            onChange={(e) => {
              setSelectedPercentile(e.target.value);
              updateData();
            }}
            disabled={isLoading}
            className="bg-zinc-700 border border-zinc-600 rounded px-2 py-1 text-white w-36 text-sm disabled:opacity-50"
          >
            {['p_10', 'p_25', 'p_50', 'p_75', 'p_90', 'p_98', 'p_99'].map((p) => (
              <option key={p} value={p}>
                {p.toUpperCase().replace('_', '')}
              </option>
            ))}
          </select>
        </div>

        <div>
          <select
            value={selectedTimeframe}
            onChange={(e) => {
              setSelectedTimeframe(e.target.value);
              updateData();
            }}
            disabled={isLoading}
            className="bg-zinc-700 border border-zinc-600 rounded px-2 py-1 text-white w-36 text-sm disabled:opacity-50"
          >
            <option value="1D">1 Day</option>
            <option value="1W">1 Week</option>
            <option value="1M">1 Month</option>
            <option value="1Y">1 Year</option>
          </select>
        </div>

        <button
          onClick={() => setIsFilterPanelOpen(true)}
          className="bg-zinc-700 hover:bg-zinc-600 border border-zinc-600 rounded px-3 py-1 text-white text-sm flex items-center gap-1.5"
          disabled={isLoading}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
          </svg>
          Filter Regions
          <span className="bg-zinc-800 text-xs px-1.5 py-0.5 rounded-full">
            {selectedRegions.length}/{allRegions.length}
          </span>
        </button>

        <div className="ml-auto">
          <StripeButton />
        </div>
      </div>

      <div className="overflow-x-auto border border-zinc-700 rounded">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr>
              <th className="p-2 border border-zinc-700 bg-zinc-800 text-white text-left sticky left-0 z-10">To \ From</th>
              {displayRegions.map(region => (
                <th key={region} className="p-2 border border-zinc-700 bg-zinc-800 text-white font-medium text-left whitespace-nowrap">
                  {region}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className={isLoading ? 'opacity-50' : ''}>
            {displayRegions.map(fromRegion => (
              <tr key={fromRegion}>
                <td className="p-2 border border-zinc-700 bg-zinc-800 text-white font-medium sticky left-0 z-10 whitespace-nowrap">
                  {fromRegion}
                </td>
                {displayRegions.map(toRegion => {
                  const latency = data.data[fromRegion][toRegion];
                  return (
                    <td 
                      key={`${fromRegion}-${toRegion}`} 
                      className="p-2 border border-zinc-700 bg-zinc-900 hover:bg-zinc-800 transition-colors duration-150"
                    >
                      <div className="flex items-center gap-1.5">
                        {(latency !== undefined && latency !== null) ? (
                          <>
                            <div className={`w-2 h-2 rounded-full ${getLatencyColor(latency)}`} />
                            <span className="text-white whitespace-nowrap">{latency.toFixed(2)}ms</span>
                          </>
                        ) : (
                          <>
                            <div className="w-2 h-2 rounded-full bg-zinc-600" />
                            <span className="text-zinc-400 whitespace-nowrap">N/A</span>
                          </>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 text-white text-sm">
        <div className="flex items-center gap-6">
          <span className="font-medium">Latency:</span>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span>&lt; 100ms</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-yellow-500" />
            <span>100-180ms</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span>&gt; 180ms</span>
          </div>
        </div>
        <div className="mt-1 text-zinc-400 italic text-xs">
          All times are in milliseconds.
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 py-4 border-t border-zinc-700 flex items-center gap-3 text-zinc-400">
        <div className="w-8 h-8">
          <Image 
            src="/static/logo.png" 
            alt="CloudPing Logo" 
            width={32}
            height={32}
            className="object-contain"
          />
        </div>
        <div className="text-sm">
          Questions? Comments? Concerns? Reach out to{' '}
          <a href="mailto:matt@ma.dev" className="text-blue-400 hover:text-blue-300">matt@ma.dev</a>.
        </div>
      </div>

      {/* Region filter panel */}
      <RegionFilterPanel
        allRegions={allRegions}
        selectedRegions={selectedRegions}
        setSelectedRegions={setSelectedRegions}
        isOpen={isFilterPanelOpen}
        onClose={() => setIsFilterPanelOpen(false)}
      />
    </div>
  );
}