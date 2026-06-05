# 3D Tilt Card — 鼠标追踪倾斜效果

自包含组件，无外部依赖（仅 framer-motion 用于 hover 放大时的弹簧动画，但 tilt 本身用原生 JS）。

## 实现

```tsx
function TiltCard({ children, href }: { children: React.ReactNode; href?: string }) {
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * -8;
    const rotateY = ((x - centerX) / centerX) * 8;
    cardRef.current.style.transform = `perspective(400px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    cardRef.current.style.transition = "transform 0.08s ease-out";
  };

  const handleMouseLeave = () => {
    if (!cardRef.current) return;
    cardRef.current.style.transform = "perspective(400px) rotateX(0deg) rotateY(0deg)";
    cardRef.current.style.transition = "transform 0.4s ease-out";
  };

  return (
    <div ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="rounded-2xl border border-border/50 bg-card p-5 cursor-pointer
                 transition-shadow duration-300 hover:shadow-[0_0_30px_-8px] hover:shadow-primary/20"
      style={{ transformStyle: "preserve-3d" }}>
      {children}
    </div>
  );
}
```

## 关键参数

| 参数 | 值 | 作用 |
|------|-----|------|
| `perspective` | 400px | 透视深度，越小倾斜越强烈 |
| `rotateX/Y 范围` | ±8deg | 最大倾斜角度 |
| move transition | 0.08s ease-out | 跟手响应时间 |
| leave transition | 0.4s ease-out | 归位缓出时间 |
| `transformStyle` | preserve-3d | 启动 3D 空间，子元素可独立 Z 轴 |

## 与 MagicCard 组合

```tsx
<MagicCard className="rounded-2xl" gradientColor="#262626">
  <TiltCard href={project.href}>
    {/* card content */}
  </TiltCard>
</MagicCard>
```

注意：TiltCard 的 `perspective` transform 会和 MagicCard 的 hover glow 效果竞争。如果两者叠加效果不佳，二选一。
