import { afterEach, describe, expect, it } from 'vitest'
import { useTemplateDraftStore } from '@/stores/use-template-draft-store'
import { TemplateData } from '@/types/templates'

const initialStoreState = useTemplateDraftStore.getState()

const templateId = 'template-123'

const data: TemplateData = {
  name: 'Edited name',
  content: 'Edited content',
  description: 'Edited description',
  type: 'document',
  questions: null,
}

const setDraft = () =>
  useTemplateDraftStore.getState().setDraft({ templateId, data })

describe('useTemplateDraftStore', () => {
  afterEach(() => {
    useTemplateDraftStore.setState(initialStoreState, true)
  })

  it('keeps the draft while on the template editor', () => {
    setDraft()

    useTemplateDraftStore
      .getState()
      .handleRouteChange(`/templates/${templateId}`)

    expect(useTemplateDraftStore.getState().draft).not.toBeNull()
  })

  it('keeps the draft while on one of the template interstitials', () => {
    setDraft()

    useTemplateDraftStore
      .getState()
      .handleRouteChange(`/templates/${templateId}/cancel`)

    expect(useTemplateDraftStore.getState().draft).not.toBeNull()
  })

  it('clears the draft when navigating to the templates list', () => {
    setDraft()

    useTemplateDraftStore.getState().handleRouteChange('/templates')

    expect(useTemplateDraftStore.getState().draft).toBeNull()
  })

  it('clears the draft when navigating away from templates entirely', () => {
    setDraft()

    useTemplateDraftStore.getState().handleRouteChange('/transcriptions')

    expect(useTemplateDraftStore.getState().draft).toBeNull()
  })

  it('clears the draft when navigating to a different template', () => {
    setDraft()

    useTemplateDraftStore
      .getState()
      .handleRouteChange('/templates/template-456')

    expect(useTemplateDraftStore.getState().draft).toBeNull()
  })

  it('clears the draft when a path merely starts with the editor path', () => {
    setDraft()

    useTemplateDraftStore
      .getState()
      .handleRouteChange(`/templates/${templateId}-other`)

    expect(useTemplateDraftStore.getState().draft).toBeNull()
  })
})
