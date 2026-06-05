# qzq.at (SamuelQZQ) 交互效果逆向分析

> 分析日期：2026-05-21
> 站点：https://www.qzq.at/
> 技术栈：Next.js (Pages Router) + Tailwind CSS v3.2.7 + Motion (motion.dev) + Font Awesome 6

## 发现的所有交互效果

### 1. 3D Tilt Card — 鼠标追踪立体倾斜

**这是"按压效果"的实际原理。** 卡片不是简单地缩放，而是跟着鼠标位置做 3D 倾斜。

**架构：**
```
MouseEnterProvider (React Context, 顶层包裹)
  └── TiltContainer (div, transform-style: preserve-3d)
       └── Tilt (组件, 根据鼠标位置计算变换值)
            └── children (实际内容)
```

**Tilt 组件核心逻辑（反编译还原）：**
```js
// 接收 translateX/Y/Z, rotateX/Y/Z 的默认偏移参数
// 读取鼠标位置上下文
function Tilt({ as="div", children, className, 
                translateX=0, translateY=0, translateZ=0,
                rotateX=0, rotateY=0, rotateZ=0, ...props }) {
  const ref = useRef(null);
  const [mousePos] = useMouseEnter();

  useEffect(() => {
    if (ref.current) {
      if (mousePos) {
        // 鼠标在元素上 → 应用 3D 变换
        ref.current.style.transform = 
          `translateX(${r}px) translateY(${l}px) translateZ(${n}px) 
           rotateX(${o}deg) rotateY(${c}deg) rotateZ(${d}deg)`;
      } else {
        // 鼠标离开 → 归零
        ref.current.style.transform = 'translateX(0) translateY(0) translateZ(0) rotateX(0) rotateY(0) rotateZ(0)';
      }
    }
  }, [mousePos]);

  return <t ref={ref} className="w-fit transition duration-200 ease-linear" ...>{children}</t>;
}
```

**关键点：** CSS `transition: all 200ms ease-linear` 做平滑过渡，不需要额外动画库。

### 2. 动画数字计数器 — Motion 弹簧动画

**粉丝总数（591,819.832）是动态计算的：**
```
total = bilibili.followers + game_bilibili.followers + twitter.followers 
        + tiktok.followers + xiaohongshu.followers
```

**实现（反编译还原）：**
```js
import { useSpringValue, useSpring, useInView } from 'motion';  // motion.dev 包

function AnimatedNumber({ value, direction="up", delay=0, className }) {
  const ref = useRef(null);
  const springValue = useSpringValue(direction === "down" ? value : 0);  // 起始值
  const spring = useSpring(springValue, {
    damping: 60,      // 弹簧阻尼
    stiffness: 100     // 弹簧刚度
  });
  const isInView = useInView(ref, { once: true, margin: "0px" });  // 滚动触发

  // 进入视口后：延迟→弹簧值弹到目标
  useEffect(() => {
    if (isInView) {
      setTimeout(() => {
        springValue.set(direction === "down" ? 0 : value);
      }, 1000 * delay);
    }
  }, [springValue, isInView, delay, value, direction]);

  // 每帧更新 DOM
  useEffect(() => {
    spring.on("change", (val) => {
      if (ref.current) {
        ref.current.textContent = Intl.NumberFormat("en-US").format(val);
      }
    });
  }, [spring]);

  return <span ref={ref} className="inline-block tabular-nums text-black dark:text-white" />;
}
```

**注意：** 带小数的数字（`.832`）是因为弹簧动画在到达目标值前会微幅振荡，`Intl.NumberFormat("en-US")` 将其格式化为带小数点的数字。这实际上是一个无意但很酷的效果。

### 3. 无限滚动 Marquee

```js
function InfiniteScroll({ items, direction="left", speed="fast", pauseOnHover=true, className }) {
  const containerRef = useRef(null);
  const innerRef = useRef(null);
  
  useEffect(() => {
    if (containerRef.current && innerRef.current) {
      // 克隆子元素实现无缝循环
      Array.from(innerRef.current.children).forEach(child => {
        const clone = child.cloneNode(true);
        innerRef.current.appendChild(clone);
      });
      setDirection();
      setSpeed();
      setPaused(true);  // 初始化完成
    }
  }, []);

  // speed: "fast"=20s, "normal"=40s, "slow"=80s
  const setSpeed = () => {
    const durations = { fast: "20s", normal: "40s", slow: "80s" };
    containerRef.current.style.setProperty("--animation-duration", durations[speed]);
  };
  
  // direction: "left"=forwards, "right"=reverse
  const setDirection = () => {
    containerRef.current.style.setProperty(
      "--animation-direction",
      direction === "left" ? "forwards" : "reverse"
    );
  };

  return (
    <div ref={containerRef} className="scroller relative z-20 overflow-hidden
         [mask-image:linear-gradient(to_right,transparent,white_20%,white_80%,transparent)]">
      <ul ref={innerRef} className="flex min-w-full shrink-0 gap-4 py-4 w-max flex-nowrap
           animate-scroll hover:[animation-play-state:paused]">
        {items}
      </ul>
    </div>
  );
}
```

**CSS：**
```css
@keyframes scroll {
  to { transform: translate(calc(-50% - 0.5rem)); }
}
.animate-scroll {
  animation: scroll var(--animation-duration, 40s) var(--animation-direction, forwards) linear infinite;
}
.scroller {
  mask-image: linear-gradient(to right, transparent, white 20%, white 80%, transparent);
}
```

### 4. 滚动视差（Scroll Parallax）

```js
// 使用 Motion 库
function ScrollParallax({ children, offset=150 }) {
  const [elementTop, setElementTop] = useState(0);
  const [clientHeight, setClientHeight] = useState(0);
  const ref = useRef(null);
  const { scrollY } = useScroll();
  const progress = useMotionValue(scrollY, 
    [elementTop - clientHeight, elementTop + offset], 
    [-offset, offset]
  );
  const y = useSpring(progress, { stiffness: 400, damping: 90 });

  return (
    <motion.div ref={ref} style={{ y }}>
      {children}
    </motion.div>
  );
}
```

### 5. 噪点纹理

每个卡片上覆盖的噪点层：
```html
<div 
  class="absolute inset-0 w-full h-full scale-[1.2] transform opacity-10 
         [mask-image:radial-gradient(#fff,transparent,75%)]"
  style="background-image: url(/noise.webp); background-size: 30%"
/>
```

### 6. 位置脉冲动画

```css
@keyframes pulse {
  0%   { transform: scale(.98); box-shadow: 0 0 0 0 rgba(255, 193, 129, .7); }
  70%  { transform: scale(1);   box-shadow: 0 0 0 90px rgba(255, 193, 129, 0); }
  100% { transform: scale(.98); box-shadow: 0 0 0 0 rgba(255, 193, 129, 0); }
}
```

### 7. 装饰轨道动画

```css
@keyframes orbit {
  0%   { transform: rotate(0deg) translateY(calc(var(--radius) * 1px)) rotate(0deg); }
  100% { transform: rotate(1turn) translateY(calc(var(--radius) * 1px)) rotate(-1turn); }
}
.animate-orbit {
  animation: orbit calc(var(--duration) * 1s) linear infinite;
}
```

### 8. 卡片背景色轮换

```js
const CARD_COLORS = [
  "bg-pink-800", "bg-indigo-800", "bg-green-800", 
  "bg-purple-700", "bg-blue-800", "bg-teal-800"
];
// 根据索引循环取色
```

### 9. 外部链接图标

```css
a[rel=external]:after {
  content: "";
  display: inline-block;
  width: 0.4em; height: 0.4em;
  background-image: url(/arrowUpRight.svg);
  background-size: contain;
  vertical-align: top;
  margin-left: 0.15em;
  position: relative; top: 6px;
}
```

### 10. 自定义滚动条

```css
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background-color: rgb(209 213 219); }
::-webkit-scrollbar-thumb { background-color: rgb(51 65 85); }
::-webkit-scrollbar-thumb:hover { background-color: rgb(251 146 60); }  /* orange */
```

## 所用库

- **motion** (`motion.dev`) — 弹簧动画 + 滚动追踪（独立包，非 framer-motion）
- **React Context** — 鼠标位置全局追踪
- **Intl.NumberFormat** — 数字格式化
- **Tailwind CSS v3.2.7** — 全部样式
- **Font Awesome 6** — 图标

## 技术栈判断方法

```js
// 1. 框架
document.querySelectorAll('script[src*="chunks"]').length > 0 → Next.js
// 2. CSS 框架
document.querySelectorAll('link[rel=stylesheet]').map(l => l.href) → Tailwind bundle
// 3. 动画库
typeof window.gsap !== 'undefined' → GreenSock
typeof window.framer !== 'undefined' || document.querySelector('[data-framer]') → framer-motion
// 4. React
document.querySelector('#__next') → React/Next.js
```
