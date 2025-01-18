// app/region-status/page.tsx
async function getRegionStatus() {
  const res = await fetch('https://api.cloudping.co/regions', {
    next: { revalidate: 300 } // Cache for 5 minutes
  });
  
  if (!res.ok) {
    throw new Error('Failed to fetch region status');
  }
  
  const data = await res.json();
  return data.sort((a: any, b: any) => a.region_name.localeCompare(b.region_name));
}

export default async function RegionStatusPage() {
  const regions = await getRegionStatus();

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">AWS Region Status</h1>
      
      <div className="overflow-x-auto border border-zinc-700 rounded">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="p-3 border border-zinc-700 bg-zinc-800 text-white text-left">Region</th>
              <th className="p-3 border border-zinc-700 bg-zinc-800 text-white text-left">Status</th>
              <th className="p-3 border border-zinc-700 bg-zinc-800 text-white text-left">First Data Point</th>
              <th className="p-3 border border-zinc-700 bg-zinc-800 text-white text-left">Latest Data Point</th>
              <th className="p-3 border border-zinc-700 bg-zinc-800 text-white text-left">Opt-in Required</th>
            </tr>
          </thead>
          <tbody>
            {regions.map((region: any) => (
              <tr key={region.region_name}>
                <td className="p-3 border border-zinc-700">
                  <span className="text-white font-medium">{region.region_name}</span>
                </td>
                <td className="p-3 border border-zinc-700">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium
                    ${region.status === 'ENABLED_BY_DEFAULT' ? 'bg-green-500/20 text-green-400' : 
                      region.status === 'ENABLED' ? 'bg-blue-500/20 text-blue-400' : 
                      'bg-yellow-500/20 text-yellow-400'}`}>
                    {region.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="p-3 border border-zinc-700 text-zinc-300">
                  {new Date(region.earliest_data_timestamp).toLocaleDateString()}
                </td>
                <td className="p-3 border border-zinc-700 text-zinc-300">
                  {new Date(region.most_recent_data_timestamp).toLocaleDateString()}
                </td>
                <td className="p-3 border border-zinc-700">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium
                    ${region.is_opt_in ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'}`}>
                    {region.is_opt_in ? 'Yes' : 'No'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 text-zinc-400 text-sm">
        <h2 className="text-white text-lg font-medium mb-2">About Region Status</h2>
        <ul className="space-y-2">
          <li><strong className="text-white">ENABLED_BY_DEFAULT:</strong> Region is enabled by default in AWS accounts</li>
          <li><strong className="text-white">ENABLED:</strong> Region requires explicit enabling in AWS accounts</li>
          <li><strong className="text-white">Data Points:</strong> Shows the date range for which we have collected latency data</li>
          <li><strong className="text-white">Opt-in Required:</strong> Indicates whether the region needs to be explicitly enabled in your AWS account</li>
        </ul>
      </div>
    </div>
  );
}