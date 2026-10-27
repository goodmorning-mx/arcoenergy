import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import './styles.css';

const siteName = process.env.NEXT_PUBLIC_SITE_NAME || 'GoodMorning Product';

export const metadata: Metadata = {
  title: siteName,
  description: process.env.NEXT_PUBLIC_SITE_DESCRIPTION || 'A GoodMorning product.',
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
