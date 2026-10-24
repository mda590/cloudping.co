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

/**
 * Friendly region names, keyed by region code, from the region inventory that
 * store_region_status fills in from AWS. Tooltips are cosmetic, so a failure
 * here degrades to bare region codes rather than taking the page down.
 */
async function getRegionNames(): Promise<Record<string, string>> {
  try {
    const response = await fetch('https://api.cloudping.co/regions', {
      next: { revalidate: 300 }, // Cache for 5 minutes
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch regions: ${response.statusText}`);
    }

    const regions: { region_name: string; region_long_name?: string }[] =
      await response.json();

    return Object.fromEntries(
      regions
        .filter(region => region.region_long_name)
        .map(region => [region.region_name, region.region_long_name as string])
    );
  } catch (error) {
    console.error('Failed to fetch region names:', error);
    return {};
  }
}

export default async function Home() {
  const [initialData, regionNames] = await Promise.all([
    getLatencyData(),
    getRegionNames(),
  ]);

  return (
    <main className="min-h-screen bg-zinc-900 p-8">
      <LatencyMatrix initialData={initialData} regionNames={regionNames} />
    </main>
  );
}
