// app/api/latencies/route.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const API_KEY = process.env.API_KEY;
  const { searchParams } = new URL(request.url);
  
  const percentile = searchParams.get('percentile') || 'p_50';
  const timeframe = searchParams.get('timeframe') || '1D';

  try {
    const response = await fetch(
      `https://api.cloudping.co/latencies?percentile=${percentile}&timeframe=${timeframe}`,
      {
        headers: {
          'x-api-key': API_KEY || '',
        },
      }
    );

    if (!response.ok) {
      console.error('Backend API error:', response.status, response.statusText);
      throw new Error('Failed to fetch data');
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch latency data' },
      { status: 500 }
    );
  }
}