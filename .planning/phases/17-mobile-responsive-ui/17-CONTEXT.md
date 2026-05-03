# Phase 17: Mobile Responsive UI - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning
**Mode:** Smart discuss (autonomous)

<domain>
## Phase Boundary

实现移动端响应式布局，让 Integration Dashboard 和其他核心页面在 320px-768px 屏幕宽度正确渲染。优化卡片布局、导航菜单、字体大小，确保触摸交互正常工作。

此阶段依赖 Phase 16 的 Real-Time Dashboard 作为 UI 基础，扩展其组件以支持移动端布局和触摸交互。

**In scope:**
- Dashboard 320px-768px 响应式布局
- Integration 卡片移动端折叠视图
- 导航菜单汉堡化（<768px）
- 触摸手势支持（swipe、tap）
- WCAG 2.1 移动端字体/间距规范

**Out of scope:**
- PWA 支持（Phase 20+）
- 移动端专属功能
- 原生 App 开发

</domain>

<decisions>
## Implementation Decisions

### Responsive Breakpoints
- **D-01:** 使用 TailwindCSS 响应式断点：sm(640px)、md(768px)、lg(1024px)
- **D-02:** 最小支持宽度 320px（iPhone SE 等小屏设备）
- **D-03:** 卡片在 <768px 切换到紧凑视图

### Navigation Strategy
- **D-04:** <768px 导航菜单折叠为 hamburger menu
- **D-05:** hamburger menu 从左侧滑出（drawer pattern）
- **D-06:** 导栏高度固定 56px（符合 Material Design 移动规范）

### Card Layout
- **D-07:** IntegrationCard 移动端单列布局
- **D-08:** 卡片内容折叠：只显示平台名、状态图标、核心数据
- **D-09:** 点击卡片展开完整详情（modal 或 inline expand）

### Touch Interactions
- **D-10:** 添加 touch-friendly 的按钮尺寸（min 44x44px）
- **D-11:** 支持 swipe to dismiss（错误消息卡片等）
- **D-12:** 防止 double-tap zoom（touch-action: manipulation）

### Typography
- **D-13:** 正文最小字体 16px（防止 iOS 自动缩放）
- **D-14:** 标题按屏幕缩放：H1 24px(sm) → 32px(lg)
- **D-15:** 行高移动端增加 1.5（桌面 1.25）

### Claude's Discretion
- 具体响应式 CSS 实现（media queries vs container queries）
- 卡片展开动画细节
- hamburger menu 过渡效果
- 测试设备选择（Chrome DevTools 模拟 vs 真机）

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 16)
- **IntegrationCard.tsx** — 连接器状态卡片，需扩展移动端折叠
- **IntegrationList.tsx** — 卡片列表容器，需响应式网格
- **ConnectionIndicator.tsx** — 连接状态徽章，移动端位置调整

### Reusable Assets (from Phase 03-03)
- **Dashboard.tsx** — Agent Dashboard 页面布局
- **AgentList.tsx** — Agent 卡片列表
- **ConnectionStatus.tsx** — WebSocket 连接状态组件

### Established Patterns
- TailwindCSS 响应式类（sm:, md:, lg:）
- Zustand 状态管理
- React hooks 模式

### Integration Points
- **web/src/pages/Integrations.tsx** — Integration Dashboard 主页面
- **web/src/App.tsx** — 应用导航布局
- **web/src/components/ui/** — 通用 UI 组件库

</code_context>

<specifics>
## Specific Ideas

### Hamburger Menu Pattern

```tsx
// MobileNav.tsx
<button className="md:hidden p-2" onClick={toggleMenu}>
  <MenuIcon className="w-6 h-6" />
</button>

// Drawer overlay
<div className={`fixed inset-y-0 left-0 w-64 bg-white transform 
  ${isOpen ? 'translate-x-0' : '-translate-x-full'} 
  transition-transform duration-300 md:hidden`}>
  <nav className="p-4">...</nav>
</div>
```

### Responsive Card Grid

```tsx
// IntegrationList.tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {connectors.map(c => <IntegrationCard key={c.platform} connector={c} />)}
</div>
```

### Touch-Friendly Button Sizing

```css
/* Ensure minimum touch target size */
.btn-mobile {
  min-width: 44px;
  min-height: 44px;
  touch-action: manipulation; /* Prevent double-tap zoom */
}
```

</specifics>

<deferred>
## Deferred Ideas

None — all Phase 17 requirements are in scope.

</deferred>

---

*Phase: 17-mobile-responsive-ui*
*Context gathered: 2026-05-03 via smart discuss*