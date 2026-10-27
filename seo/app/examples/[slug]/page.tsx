import { notFound } from 'next/navigation';

type ExamplePageProps = { params: Promise<{ slug: string }> };

export default async function ExamplePage({ params }: ExamplePageProps) {
  const { slug } = await params;
  if (!slug) notFound();

  return (
    <main>
      <p className="eyebrow">Dynamic route</p>
      <h1>{slug}</h1>
      <p>This route is a minimal placeholder for product-owned SEO content.</p>
    </main>
  );
}
