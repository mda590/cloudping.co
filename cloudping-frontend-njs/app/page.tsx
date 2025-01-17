// app/page.tsx
import LatencyMatrix from '@/components/LatencyMatrix';

async function getLatencyData() {
  const API_KEY = process.env.API_KEY;
  const response = await fetch('https://api.cloudping.co/latencies', {
    headers: {
      'x-api-key': API_KEY || '',
    },
    next: { revalidate: 300 }, // Cache for 5 minutes
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch latency data');
  }
  
  return response.json();
}

export default async function Home() {
  const initialData = await getLatencyData();
  
  return (
    <main className="min-h-screen bg-zinc-900 p-8">
      <LatencyMatrix initialData={initialData} />
    </main>
  );
}