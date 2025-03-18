'use client';
import { useState } from 'react';
import StripeButton from './StripeButton';

// Function to dynamically group AWS regions by geography
const getRegionGroups = (regions: string[]) => {
  const groups: { [key: string]: string[] } = {
    "All Regions": [],
    "Americas": [],
    "Europe": [],
    "Asia Pacific": [],
    "Middle East & Africa": []
  };
  
  regions.forEach(region => {
    const prefix = region.split('-')[0];
    
    switch (prefix) {
      case 'us':
      case 'ca':
      case 'sa':
      case 'mx':
        groups["Americas"].push(region);
        break;
      case 'eu':
        groups["Europe"].push(region);
        break;
      case 'ap':
        groups["Asia Pacific"].push(region);
        break;
      case 'me':
      case 'af':
      case 'il':
        groups["Middle East & Africa"].push(region);
        break;
      default:
        // If we encounter a new region type, add it to All Regions only
        console.log(`Unrecognized region prefix: ${prefix} for region ${region}`);
    }
  });
  
  return groups;
};

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
  const [selectedRegionGroup, setSelectedRegionGroup] = useState('All Regions');
  const [data, setData] = useState<LatencyData | null>(initialData);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Get all available regions
  const allRegions = data?.data ? Object.keys(data.data).sort() : [];
  
  // Dynamically create region groups
  const regionGroups = getRegionGroups(allRegions);
  
  // Filter regions based on selected group
  const getFilteredRegions = () => {
    if (selectedRegionGroup === 'All Regions') {
      return allRegions;
    }
    return allRegions.filter(region => regionGroups[selectedRegionGroup].includes(region));
  };

  const regions = getFilteredRegions();

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

        <div>
          <select
            value={selectedRegionGroup}
            onChange={(e) => setSelectedRegionGroup(e.target.value)}
            disabled={isLoading}
            className="bg-zinc-700 border border-zinc-600 rounded px-2 py-1 text-white w-48 text-sm disabled:opacity-50"
          >
            {Object.keys(regionGroups).map((group) => (
              <option key={group} value={group}>
                {group} ({group === 'All Regions' ? allRegions.length : regionGroups[group].length})
              </option>
            ))}
          </select>
        </div>

        <div className="ml-auto">
          <StripeButton />
        </div>
      </div>

      <div className="overflow-x-auto border border-zinc-700 rounded">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr>
              <th className="p-2 border border-zinc-700 bg-zinc-800 text-white text-left sticky left-0 z-10">To \ From</th>
              {regions.map(region => (
                <th key={region} className="p-2 border border-zinc-700 bg-zinc-800 text-white font-medium text-left whitespace-nowrap">
                  {region}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className={isLoading ? 'opacity-50' : ''}>
            {regions.map(fromRegion => (
              <tr key={fromRegion}>
                <td className="p-2 border border-zinc-700 bg-zinc-800 text-white font-medium sticky left-0 z-10 whitespace-nowrap">
                  {fromRegion}
                </td>
                {regions.map(toRegion => {
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
          <img 
            src="/static/logo.png" 
            alt="CloudPing Logo" 
            className="w-full h-full object-contain"
          />
        </div>
        <div className="text-sm">
          Questions? Comments? Concerns? Reach out to{' '}
          <a href="mailto:matt@ma.dev" className="text-blue-400 hover:text-blue-300">matt@ma.dev</a>.
        </div>
      </div>
    </div>
  );
}