// app/about/page.tsx
export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-6">About CloudPing</h1>
      
      <ul className="space-y-6 text-zinc-200">
        <li>
          Who am I? My name is{' '}
          <a href="https://twitter.com/mattadorjan" className="text-blue-400 hover:text-blue-300">
            Matt
          </a>
          . I&apos;m an AWS architect, and overall fan of all things cloud.
        </li>
        
        <li>
          Why did I create this? Over time, as I&apos;ve worked on global AWS deployments, 
          I have often been faced with the question of which inter-region transactions 
          will be faced with the most latency. I haven&apos;t been able to find any kind of dynamic, 
          consistently updated, latency monitoring. The goal here is to provide a single source 
          of truth for inter-region AWS region latency.
        </li>
        
        <li>
          Please get in touch if you have any comments or suggestions. You can also use{' '}
          <a 
            href="https://github.com/mda590/cloudping.co/issues" 
            className="text-blue-400 hover:text-blue-300"
          >
            GitHub Issues
          </a>
          {' '}to submit comments, questions, or new feature requests.
        </li>
        
        <li>
          More details on the project can be found in the{' '}
          <a 
            href="https://github.com/mda590/cloudping.co" 
            className="text-blue-400 hover:text-blue-300"
          >
            GitHub README
          </a>
          . This project is in no way associated with Amazon or AWS.
        </li>
      </ul>
    </div>
  );
}