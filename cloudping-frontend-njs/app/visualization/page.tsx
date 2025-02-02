// app/visualization/page.tsx
import HubSpokeVisualization from '@/components/HubSpokeVisualization';

async function getLatencyData() {
  const res = await fetch('https://api.cloudping.co/latencies', {
    headers: {
      'x-api-key': process.env.API_KEY || '',
    },
    next: { revalidate: 300 } // Cache for 5 minutes
  });

  if (!res.ok) {
    throw new Error('Failed to fetch latency data');
  }

  return res.json();
}

export default async function VisualizationPage() {
  const data = await getLatencyData();

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">Latency Visualization</h1>
      <HubSpokeVisualization latencyData={data.data} />
    </div>
  );
}