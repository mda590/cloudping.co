// components/Header.tsx
import Link from 'next/link';

export default function Header() {
  return (
    <header className="bg-zinc-800 text-white">
      <nav className="max-w-6xl mx-auto px-4 py-4 flex items-center">
        <Link href="/" className="text-xl font-semibold hover:text-zinc-300">
          AWS Latency Monitoring
        </Link>
        <div className="flex gap-6 ml-8">
          <Link href="/" className="hover:text-zinc-300">
            Home
          </Link>
          <Link href="/about" className="hover:text-zinc-300">
            About
          </Link>
        </div>
        <div className="ml-auto flex items-center">
          <iframe 
            src="https://ghbtns.com/github-btn.html?user=mda590&repo=cloudping.co&type=star&count=true" 
            frameBorder="0" 
            scrolling="0" 
            width="170" 
            height="20"
            title="GitHub Stars"
            style={{ marginTop: '2px' }}
          />
        </div>
      </nav>
    </header>
  );
}