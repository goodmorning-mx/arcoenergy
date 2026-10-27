export const dynamic = 'force-dynamic';
export const revalidate = 0;

export function GET() {
  const commit = process.env.SOURCE_COMMIT ?? 'unknown';
  const commitSha = /^[0-9a-f]{7,64}$/.test(commit) ? commit : 'unknown';
  return Response.json(
    { commit_sha: commitSha },
    { headers: { 'Cache-Control': 'no-store, max-age=0' } },
  );
}
