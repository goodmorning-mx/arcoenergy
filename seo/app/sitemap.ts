import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  if (process.env.SITE_INDEXABLE !== 'true') return [];
  const base = process.env.SITE_URL || 'https://arcoenergy.goodmorning.mx';
  return [{ url: base, changeFrequency: 'monthly', priority: 1 }];
}
