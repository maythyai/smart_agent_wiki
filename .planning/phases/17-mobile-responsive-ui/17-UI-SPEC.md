---
phase: 17-mobile-responsive-ui
created: 2026-05-03
design_contract: mobile-responsive
target_breakpoints:
  - xs: 320px-479px (small phones)
  - sm: 480px-639px (large phones)
  - md: 640px-767px (tablets portrait)
breakpoint_strategy: TailwindCSS default breakpoints
---

# UI Design Contract: Mobile Responsive UI

**Scope:** Phase 17 — Mobile Responsive UI
**Pages:** Integrations Dashboard, Agent Dashboard, App Navigation

## 1. Visual Language

### 1.1 Brand Colors
继承 Phase 03-03 建立的 TailwindCSS 默认配色体系：
- Primary: Blue-600 (#2563eb)
- Success: Green-500 (#22c55e)
- Warning: Yellow-500 (#eab308)
- Error: Red-500 (#ef4444)
- Neutral: Gray-900/600/400

### 1.2 Typography Scale (Mobile)

| Element | xs/sm (320-639) | md (640-767) | Desktop |
|---------|-----------------|--------------|---------|
| H1 | 20px | 24px | 32px |
| H2 | 18px | 20px | 24px |
| H3 | 16px | 18px | 20px |
| Body | 16px | 16px | 14px |
| Small | 14px | 14px | 12px |
| Caption | 12px | 12px | 11px |

**WCAG 2.1 Compliance:**
- 正文最小 16px（防止 iOS Safari 自动缩放）
- 行高移动端 1.5（桌面 1.25）
- 所有文本保持 4.5:1 对比度

### 1.3 Spacing Scale

| Token | xs/sm | md | Desktop |
|-------|-------|----|---------|
| xs | 4px | 4px | 4px |
| sm | 8px | 8px | 8px |
| md | 12px | 16px | 16px |
| lg | 16px | 20px | 24px |
| xl | 20px | 24px | 32px |
| 2xl | 24px | 32px | 48px |

### 1.4 Component Dimensions (Touch-Friendly)

| Component | Min Width | Min Height | Desktop |
|-----------|-----------|------------|---------|
| Button | 44px | 44px | Auto |
| Card | Full width | Auto | 320px |
| Input | 100% | 44px | Auto |
| Nav Item | 100% | 48px | Auto |

## 2. Layout Architecture

### 2.1 Navigation

**Desktop (>768px):**
- 固定顶部导航栏，高度 56px
- 水平导航项布局
- Logo 左侧，导航项居中，操作右侧

**Mobile (<768px):**
- hamburger menu 触发左侧 drawer
- drawer 全屏高度，宽度 280px
- Logo + hamburger button 顶部
- drawer 内容：垂直导航项列表

**Drawer Pattern:**
```tsx
// Slide-in drawer with backdrop
<div className="fixed inset-0 z-50 md:hidden">
  {/* Backdrop */}
  <div className="absolute inset-0 bg-black/50" onClick={close} />
  {/* Drawer */}
  <nav className={`absolute left-0 top-0 h-full w-72 bg-white
    transform transition-transform duration-300
    ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
    {/* Nav items */}
  </nav>
</div>
```

### 2.2 Integration Dashboard Grid

**xs/sm (320-639px):**
- 单列布局
- 卡片全宽，间距 12px
- 卡片紧凑模式（只显示核心数据）

**md (640-767px):**
- 双列布局
- 卡片宽度 50%，间距 16px

**Desktop (>768px):**
- 三列布局
- 卡片宽度 ~320px，间距 24px

### 2.3 Integration Card States

**Compact Mode (Mobile):**
```
┌─────────────────────────────────────┐
│ 🟢 Slack        Connected    ⚙️    │
│ 45/100 items synced                 │
└─────────────────────────────────────┘
```

**Expanded Mode (Desktop/Tap-Expand):**
```
┌────────────────────────────────────────────────┐
│ 🟢 Slack                    Connected     ⚙️   │
│                                                │
│ Last sync: 2 min ago                           │
│ Health: Healthy                                │
│ Progress: ████████████░░░░░░░░ 45/100         │
│                                                │
│ [Sync Now] [Disconnect] [Settings]             │
└────────────────────────────────────────────────┘
```

**Tap-to-Expand Behavior:**
- Mobile: 点击卡片展开详情（inline 或 modal）
- 展开/折叠有平滑过渡动画（300ms）

## 3. Component States

### 3.1 Connection Indicator (Mobile)

**位置调整:**
- Desktop: Integration 页面 header 右侧
- Mobile: 卡片内部或底部状态栏

**尺寸:**
- 状态点: 8px (mobile) vs 12px (desktop)
- 文字: 12px (mobile) vs 14px (desktop)

### 3.2 Touch Interactions

**Tap Targets:**
- 所有可点击元素最小 44x44px
- Icon buttons 增加 padding 达到最小尺寸

**Swipe Gestures:**
- IntegrationCard: swipe to dismiss（用于 disconnect confirmation）
- Drawer: swipe right to close
- Modal/Overlay: swipe down to dismiss

**Touch Action:**
```css
touch-action: manipulation; /* Prevent double-tap zoom */
```

### 3.3 Loading States (Mobile)

- Skeleton cards: 灰色矩形占位，animate-pulse
- Progress bars: 移动端使用 thinner bars (height 4px vs 8px)
- Spinner: 24px (mobile) vs 32px (desktop)

## 4. Accessibility Requirements

### 4.1 WCAG 2.1 Level AA

- [ ] 所有文本对比度 ≥ 4.5:1
- [ ] 大文本对比度 ≥ 3:1
- [ ] 可点击元素焦点可见（focus ring）
- [ ] 语义化 HTML（nav, main, section）
- [ ] aria-label 用于 icon buttons
- [ ] 跳过导航链接（Skip to main content）

### 4.2 Mobile-Specific

- [ ] 表单输入最小 16px（防止 zoom）
- [ ] Touch 目标最小 44x44px
- [ ] 横向滚动区域有 scroll indicator
- [ ] Modal 有关闭按钮且可 swipe dismiss

## 5. Performance Budget

### 5.1 CSS Constraints

- [ ] 不引入新 CSS 框架（使用现有 TailwindCSS）
- [ ] 响应式样式不超过 500 行新增
- [ ] 使用 CSS containment 优化渲染

### 5.2 Animation Performance

- [ ] 使用 transform/opacity（GPU accelerated）
- [ ] 避免 width/height 动画（causes layout）
- [ ] drawer 过渡 300ms (流畅感知)
- [ ] 卡片展开过渡 200ms

## 6. Testing Checklist

### 6.1 Device Coverage

必须验证的设备/分辨率：
- iPhone SE (320px) — 最小宽度测试
- iPhone 14 (390px) — 标准手机
- iPad Mini (768px) — 边界 case
- iPad Pro (1024px) — tablet landscape

### 6.2 Orientation Testing

- [ ] Portrait mode 所有页面
- [ ] Landscape mode tablet+ (>768px)
- [ ] 小屏 landscape 滚动测试

### 6.3 Touch Testing

- [ ] 所有 buttons/links 可点击
- [ ] Swipe gestures 正常触发
- [ ] 无 unwanted double-tap zoom
- [ ] Long press 不触发意外行为

---

*UI Design Contract for Phase 17*
*Created: 2026-05-03*
*Designer: Claude (autonomous mode)*