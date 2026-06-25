import test from 'node:test'
import assert from 'node:assert/strict'
import { createJiti } from 'jiti'

const jiti = createJiti(import.meta.url, {
  interopDefault: true,
  moduleCache: false,
})

const {
  buildPlanningResumeDisplay,
  buildPlanningResumePrompt,
} = jiti('../src/utils/planningResume.ts')

test('buildPlanningResumePrompt: 使用 Python runtime 期望的结构化 resume 标记', () => {
  const prompt = buildPlanningResumePrompt({
    questionSetId: 'qs_confirm_design_1',
    answers: {
      design_confirmation: 'no_changes',
    },
  })

  assert.equal(
    prompt,
    '<<RESUME_ANSWERS>>{"questionSetId":"qs_confirm_design_1","answers":{"design_confirmation":"no_changes"}}<<RESUME_ANSWERS>>',
  )
})

test('buildPlanningResumeDisplay: 保持用户可读的答案文本', () => {
  const display = buildPlanningResumeDisplay([
    { question: '以上是为您设计的登录页面方案，请确认是否需要调整？', answer: '没有需要调整' },
  ])

  assert.equal(
    display,
    '需求补充：以上是为您设计的登录页面方案，请确认是否需要调整？：答：没有需要调整\n\n请继续生成。',
  )
})
