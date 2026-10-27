export const dynamic = 'force-static';

export function GET() {
  return Response.json({ service: 'arcoenergy-seo', status: 'ok' });
}
