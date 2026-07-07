'use client'

import { TemplateEditorToolbar } from '@/app/templates/components/editor/editor-toolbar'
import {
  GovukButton,
  GovukErrorSummary,
  GovukFormGroup,
  GovukHint,
  GovukInput,
  GovukLabel,
} from '@/components/govuk'
import { cn } from '@/lib/utils'
import { TemplateData } from '@/types/templates'
import Document from '@tiptap/extension-document'
import HardBreak from '@tiptap/extension-hard-break'
import Paragraph from '@tiptap/extension-paragraph'
import Text from '@tiptap/extension-text'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { Loader2 } from 'lucide-react'
import { useEffect } from 'react'
import { Controller, useFormContext } from 'react-hook-form'

export const DocumentTemplateEditor = ({
  onSubmit,
}: {
  onSubmit: (data: TemplateData) => void
}) => {
  const form = useFormContext<TemplateData>()
  const { errors, isSubmitting, isSubmitted } = form.formState

  const errorList = [
    errors.name?.message && {
      href: '#template-name',
      text: errors.name.message,
    },
    errors.description?.message && {
      href: '#template-description',
      text: errors.description.message,
    },
    errors.content?.message && {
      href: '#template-content',
      text: errors.content.message,
    },
  ].filter(Boolean) as { href: string; text: string }[]

  return (
    <form
      className="flex flex-col gap-6"
      onSubmit={form.handleSubmit(onSubmit)}
      noValidate
    >
      {isSubmitted && errorList.length > 0 && (
        <GovukErrorSummary
          title="There is a problem"
          errorList={errorList}
          className="govuk-!-margin-bottom-6"
          data-testid="error-summary"
        />
      )}

      <div>
        <GovukButton
          type="submit"
          disabled={isSubmitting}
          className="govuk-!-margin-bottom-0"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="animate-spin" aria-hidden="true" />
              Saving…
            </>
          ) : (
            'Save'
          )}
        </GovukButton>
        <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-top-4 govuk-!-margin-bottom-0" />
      </div>

      <div>
        <h2 className="govuk-heading-m govuk-!-margin-bottom-1">
          Template details
        </h2>
        <GovukHint className="govuk-!-margin-bottom-4">
          Add a name and description so you can find your template later. Name
          and description are not used to generate your minute — add structure
          and style instructions to the template content field below.
        </GovukHint>

        <GovukFormGroup
          hasError={!!errors.name}
          className="govuk-!-margin-bottom-4"
        >
          <GovukLabel htmlFor="template-name">Template name</GovukLabel>
          {errors.name?.message && (
            <p id="template-name-error" className="govuk-error-message">
              <span className="govuk-visually-hidden">Error:</span>{' '}
              {errors.name.message}
            </p>
          )}
          <GovukInput
            id="template-name"
            className="govuk-!-margin-top-1"
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'template-name-error' : undefined}
            {...form.register('name', {
              required: { value: true, message: 'Enter a template name' },
            })}
          />
        </GovukFormGroup>

        <GovukFormGroup
          hasError={!!errors.description}
          className="govuk-!-margin-bottom-0"
        >
          <GovukLabel htmlFor="template-description">Description</GovukLabel>
          {errors.description?.message && (
            <p id="template-description-error" className="govuk-error-message">
              <span className="govuk-visually-hidden">Error:</span>{' '}
              {errors.description.message}
            </p>
          )}
          <GovukInput
            id="template-description"
            className="govuk-!-margin-top-1"
            aria-invalid={!!errors.description}
            aria-describedby={
              errors.description ? 'template-description-error' : undefined
            }
            {...form.register('description', {
              required: { value: true, message: 'Enter a description' },
            })}
          />
        </GovukFormGroup>
      </div>

      <div>
        <GovukFormGroup
          hasError={!!errors.content}
          className="govuk-!-margin-bottom-0"
        >
          <GovukLabel htmlFor="template-content" size="m">
            Template content
          </GovukLabel>
          <GovukHint
            id="template-content-hint"
            className="govuk-!-margin-top-1 govuk-!-margin-bottom-3"
          >
            The template content should look how you would like the minutes to
            look. Use placeholder text to describe what you would like in each
            section and provide style guidance, including examples if necessary.
            You may need to iterate on your template to get the best results.
          </GovukHint>
          {errors.content?.message && (
            <p
              id="template-content-error"
              className="govuk-error-message govuk-!-margin-bottom-2"
            >
              <span className="govuk-visually-hidden">Error:</span>{' '}
              {errors.content.message}
            </p>
          )}
          <Controller
            name="content"
            control={form.control}
            rules={{
              required: { value: true, message: 'Add some template content' },
            }}
            render={({ field: { onChange, value } }) => (
              <ControlledEditor
                onChange={onChange}
                value={value}
                hasError={!!errors.content}
              />
            )}
          />
        </GovukFormGroup>
      </div>
    </form>
  )
}

const ControlledEditor = ({
  onChange,
  value,
  hasError,
}: {
  onChange: (v: string) => void
  value: string
  hasError?: boolean
}) => {
  const editor = useEditor({
    extensions: [StarterKit, Document, Paragraph, Text, HardBreak],
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
    content: value,
  })

  useEffect(() => {
    if (editor && value !== editor.getHTML()) {
      editor.commands.setContent(value || '')
    }
  }, [editor, value])

  return (
    <div
      id="template-content"
      tabIndex={-1}
      onFocus={() => editor?.commands.focus()}
      className={cn('govuk-textarea p-0', hasError && 'govuk-textarea--error')}
    >
      <TemplateEditorToolbar editor={editor} />
      <div>
        <EditorContent
          editor={editor}
          className="editor-content"
          data-testid="template-content-editor"
        />
      </div>
    </div>
  )
}
