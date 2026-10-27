import type { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  const indexable = process.env.SITE_INDEXABLE === 'true';
  const host = process.env.SITE_URL || 'https://dev.arcoenergy.goodmorning.mx';
  return { rules: { userAgent: '*', allow: indexable ? '/' : [], disallow: indexable ? [] : '/' }, ...(indexable ? { sitemap: `${host}/sitemap.xml` } : {}) };
}
