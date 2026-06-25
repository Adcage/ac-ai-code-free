const PLANNING_RESUME_MARKER = '<<RESUME_ANSWERS>>'

export interface PlanningResumePayload {
  questionSetId?: string
  answers: Record<string, string>
}

export interface PlanningDisplayAnswer {
  question: string
  answer: string
}

export function buildPlanningResumePrompt(payload: PlanningResumePayload): string {
  const body: PlanningResumePayload = payload.questionSetId
    ? { questionSetId: payload.questionSetId, answers: payload.answers }
    : { answers: payload.answers }
  return `${PLANNING_RESUME_MARKER}${JSON.stringify(body)}${PLANNING_RESUME_MARKER}`
}

export function buildPlanningResumeDisplay(items: PlanningDisplayAnswer[]): string {
  if (items.length === 0) {
    return '跳过补充需求，请继续生成。'
  }
  const readableAnswers = items.map((item) => `${item.question}：答：${item.answer}`)
  return `需求补充：${readableAnswers.join('；')}\n\n请继续生成。`
}
