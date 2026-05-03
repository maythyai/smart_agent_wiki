# Phase 20: Tech Debt Cleanup - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning
**Mode:** Infrastructure phase (tech debt resolution)

<domain>
## Phase Boundary

解决 v1.1-v3.1 累积的技术债务：缺失的 VERIFICATION.md 文件、前端测试基础设施、bundle 优化分析。此阶段不添加新功能，只提升代码质量和可维护性。

**In scope:**
- VERIFICATION.md 文件创建（Phase 02, 03-01, 03-02, 03-03）
- Vitest 配置和前端测试
- Bundle 分析报告
- Milkdown 懒加载评估

**Out of scope:**
- 新功能实现
- API 变更
- 重构现有代码

</domain>

<decisions>
## Implementation Decisions

### VERIFICATION Files
- **D-01:** 为 Phase 02, 03-01, 03-02, 03-03 创建 VERIFICATION.md
- **D-02:** 基于现有 SUMMARY.md 和代码状态编写验证结果
- **D-03:** 标注所有需求为 PASSED（这些阶段已完成）

### Vitest Setup
- **D-04:** 使用 Vitest 作为前端测试框架（与 Vite 原生集成）
- **D-05:** 测试文件放在 `web/src/__tests__/` 目录
- **D-06:** 使用 @testing-library/react 进行组件测试

### Frontend Tests
- **D-07:** IntegrationCard 组件测试（渲染、状态、交互）
- **D-08:** IntegrationList 组件测试（列表渲染、空状态）

### Bundle Analysis
- **D-09:** 使用 rollup-plugin-visualizer 生成 bundle 报告
- **D-10:** 分析报告输出到 `.planning/bundle-analysis/`

### Milkdown Lazy Loading
- **D-11:** 评估 Milkdown bundle 大小影响
- **D-12:** 如果超过 100KB，实现懒加载

### Claude's Discretion
- VERIFICATION.md 具体内容格式
- 测试用例详细设计
- bundle 分析报告格式

</decisions>

<code_context>
## Existing Code Insights

### VERIFICATION Files Pattern (from Phase 16, 17, 18, 19)
- 文件位置：`.planning/phases/{phase-id}/VERIFICATION.md`
- 包含：需求验证状态、证据、测试结果

### Frontend Test Infrastructure
- **web/package.json** — Vite + React 配置
- **web/vite.config.ts** — Vite 配置
- **web/src/components/integrations/IntegrationCard.tsx** — 需要测试
- **web/src/components/integrations/IntegrationList.tsx** — 需要测试

### Existing Phase Summaries (for VERIFICATION)
- **Phase 02:** `.planning/phases/02-intelligence-governance/02-SUMMARY.md`
- **Phase 03-01:** `.planning/phases/03-01-multi-agent-foundation/03-01-SUMMARY.md`
- **Phase 03-02:** `.planning/phases/03-02-web-api-foundation/03-02-SUMMARY.md`
- **Phase 03-03:** `.planning/phases/03-03-react-frontend/03-03-SUMMARY.md`

</code_context>

<specifics>
## Specific Ideas

### VERIFICATION.md Template

```markdown
# Phase {N}: {Name} Verification

**Phase:** {phase-id}
**Date:** 2026-05-03
**Status:** PASSED

## Summary

{Brief summary of phase completion}

## Requirements Verification

### REQ-01: {Requirement Name}

**Status:** PASSED

**Evidence:**
- {Evidence description}
- {Files implementing the requirement}

---
*Verified: 2026-05-03*
```

### Vitest Configuration

```typescript
// web/vite.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/setupTests.ts'
  }
})
```

### Bundle Analysis Command

```bash
cd web && npm run build -- --mode analyze
```

</specifics>

<deferred>
## Deferred Ideas

None — all Phase 20 requirements are in scope.

</deferred>

---

*Phase: 20-tech-debt-cleanup*
*Context gathered: 2026-05-03 via auto-generation (infrastructure phase)*
