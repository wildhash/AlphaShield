import React from "react";

type Props = { children: React.ReactNode; title?: string; area?: string; tall?: boolean; wide?: boolean };

export default function Card({ children, title, area, tall, wide }: Props) {
  const styles: React.CSSProperties = area ? { gridArea: area } : {};
  return (
    <section className={`card ${tall ? "tall" : ""} ${wide ? "wide" : ""}`} style={styles}>
      {title && <div className="card-header"><span>{title}</span></div>}
      <div className="card-body">{children}</div>
    </section>
  );
}