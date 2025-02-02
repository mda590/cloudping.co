'use client';
// components/HubSpokeVisualization.tsx
import { useState } from 'react';

interface LatencyData {
  [key: string]: {
    [key: string]: number;
  };
}

interface Props {
  latencyData: LatencyData;
}

export default function HubSpokeVisualization({ latencyData }: Props) {
  const [selectedRegion, setSelectedRegion] = useState('us-east-1');
  const [hoveredConnection, setHoveredConnection] = useState<string | null>(null);

  // Get all unique regions and sort them alphabetically
  const regions = Object.keys(latencyData).sort();
  const otherRegions = regions.filter(r => r !== selectedRegion);

  // Calculate positions for the regions
  const centerX = 400;
  const centerY = 400;
  const radius = 300;

  const getLatencyColor = (latency: number) => {
    if (latency < 100) return '#4ade80';
    if (latency < 180) return '#fbbf24';
    return '#ef4444';
  };

  const getLineWidth = (latency: number) => {
    // Scale line width inversely with latency (thicker = faster)
    return Math.max(1, 6 - (latency / 50));
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="mb-4 flex justify-between items-center">
        <h2 className="text-xl font-medium text-white">
          Latencies from {selectedRegion}
        </h2>
        <select
          value={selectedRegion}
          onChange={(e) => setSelectedRegion(e.target.value)}
          className="bg-zinc-700 border border-zinc-600 rounded px-3 py-1 text-white"
        >
          {regions.map(region => (
            <option key={region} value={region}>{region}</option>
          ))}
        </select>
      </div>

      <div className="border border-zinc-700 rounded bg-zinc-800/50 p-4">
        <svg width="800" height="800" viewBox="0 0 800 800">
          {/* Draw connections */}
          {otherRegions.map((region, index) => {
            const angle = (index * 2 * Math.PI) / otherRegions.length;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            const latency = latencyData[selectedRegion][region];

            return (
              <g key={region}>
                {/* Connection line */}
                <line
                  x1={centerX}
                  y1={centerY}
                  x2={x}
                  y2={y}
                  stroke={getLatencyColor(latency)}
                  strokeWidth={getLineWidth(latency)}
                  strokeOpacity={hoveredConnection === region ? 1 : 0.5}
                  onMouseEnter={() => setHoveredConnection(region)}
                  onMouseLeave={() => setHoveredConnection(null)}
                />

                {/* Region circle */}
                <circle
                  cx={x}
                  cy={y}
                  r={6}
                  fill={hoveredConnection === region ? '#fff' : '#666'}
                  cursor="pointer"
                  onClick={() => setSelectedRegion(region)}
                />

                {/* Region label */}
                <text
                  x={x}
                  y={y + 20}
                  textAnchor="middle"
                  fill="#fff"
                  fontSize="12"
                >
                  {region}
                </text>

                {/* Latency label - only show when hovered */}
                {hoveredConnection === region && (
                  <text
                    x={(centerX + x) / 2}
                    y={(centerY + y) / 2}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize="14"
                    fontWeight="bold"
                  >
                    {latency.toFixed(1)}ms
                  </text>
                )}
              </g>
            );
          })}

          {/* Center region */}
          <circle
            cx={centerX}
            cy={centerY}
            r={8}
            fill="#fff"
          />
          <text
            x={centerX}
            y={centerY + 24}
            textAnchor="middle"
            fill="#fff"
            fontSize="14"
            fontWeight="bold"
          >
            {selectedRegion}
          </text>
        </svg>
      </div>

      {/* Legend */}
      <div className="mt-4 flex gap-6 text-sm text-zinc-300">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          &lt; 100ms
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          100-180ms
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          &gt; 180ms
        </div>
      </div>
    </div>
  );
}