import Link from 'next/link';

export default function HomePage() {
  return (
    <main>
      <p className="eyebrow">GoodMorning</p>
      <h1>Build a clear next step.</h1>
      <p>This is the SEO-ready Next.js surface for products that opt into the next or hybrid profile.</p>
      <Link href="/examples/hello">View a dynamic example</Link>
    </main>
  );
}
