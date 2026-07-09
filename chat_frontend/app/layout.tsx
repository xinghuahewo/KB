import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "BGP RAG Chat",
  description: "BGP 知识库对话工作台",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
