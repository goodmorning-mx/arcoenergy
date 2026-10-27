type SeoRouteProps = { params: Promise<{ slug?: string[] }> };

export default async function SeoRoutePage({ params }: SeoRouteProps) {
  const { slug = [] } = await params;
  const path = slug.length > 0 ? `/${slug.join('/')}` : '/';

  return (
    <main>
      <p className="eyebrow">SEO route</p>
      <h1>{path}</h1>
      <p>This Next.js route is reachable through the hybrid gateway.</p>
    </main>
  );
}
