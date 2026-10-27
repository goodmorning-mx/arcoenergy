import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import './styles.css';

const siteName = process.env.SITE_NAME || 'ArcoEnergy | Paneles solares en Tamaulipas';

export const metadata: Metadata = {
  title: { default: siteName, template: '%s · ArcoEnergy' },
  description: process.env.SITE_DESCRIPTION || 'Cotiza e instala paneles solares para tu hogar o empresa en Tampico, Ciudad Madero y Altamira. Acompañamiento local de principio a fin.',
  metadataBase: new URL(process.env.SITE_URL || 'https://dev.arcoenergy.goodmorning.mx'),
  alternates: { canonical: '/' },
  robots: { index: process.env.SITE_INDEXABLE === 'true', follow: process.env.SITE_INDEXABLE === 'true' },
  openGraph: { title: siteName, description: 'Energía solar para hogares y empresas en el sur de Tamaulipas.', locale: 'es_MX', type: 'website' },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="es-MX">
      <body>{children}</body>
    </html>
  );
}
