'use client'

import { TemplateEditorToolbar } from '@/app/templates/components/editor/editor-toolbar'
import {
  GovukDetails,
  GovukErrorSummary,
  GovukFormGroup,
  GovukHint,
  GovukInput,
  GovukLabel,
} from '@/components/govuk'
import { cn } from '@/lib/utils'
import { TemplateData } from '@/types/templates'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { ReactNode, useEffect } from 'react'
import { Controller, useFormContext } from 'react-hook-form'

export const DocumentTemplateEditor = ({
  onSubmit,
  actions,
}: {
  onSubmit: (data: TemplateData) => void
  actions: ReactNode
}) => {
  const form = useFormContext<TemplateData>()
  const { errors, isSubmitted } = form.formState

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
          data-testid="error-summary"
        />
      )}

      <div>
        <h2 className="govuk-heading-m govuk-!-margin-bottom-1">
          Template details
        </h2>
        <GovukHint className="govuk-!-margin-bottom-4">
          Add a title and description to help you find your template later
        </GovukHint>

        <GovukFormGroup hasError={!!errors.name}>
          <GovukLabel htmlFor="template-name">Title</GovukLabel>
          {errors.name?.message && (
            <p id="template-name-error" className="govuk-error-message">
              <span className="govuk-visually-hidden">Error:</span>{' '}
              {errors.name.message}
            </p>
          )}
          <GovukInput
            id="template-name"
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'template-name-error' : undefined}
            {...form.register('name', {
              required: { value: true, message: 'Enter a title' },
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

      <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-bottom-0" />

      <div>
        <h2 className="govuk-heading-m govuk-!-margin-bottom-1">
          Content and style
        </h2>

        <GovukDetails summary="Useful tips" className="govuk-!-margin-bottom-4">
          <p className="govuk-body">
            Customise your template based on how you want your document to be
            presented.
          </p>
          <p className="govuk-body govuk-!-font-weight-bold govuk-!-margin-bottom-1">
            Headings:
          </p>
          <ul className="govuk-list govuk-list--bullet">
            <li>
              write each heading how you want it to appear in the document
            </li>
            <li>headings are case sensitive</li>
          </ul>
          <p className="govuk-body govuk-!-font-weight-bold govuk-!-margin-bottom-1">
            Placeholder text:
          </p>
          <ul className="govuk-list govuk-list--bullet">
            <li>
              state the information you&rsquo;d like to include, or questions
              you&rsquo;d like answered, in each section
            </li>
            <li>
              the information will be pulled from the transcript into the
              document
            </li>
          </ul>
          <p className="govuk-body govuk-!-font-weight-bold govuk-!-margin-bottom-1">
            Format instructions:
          </p>
          <ul className="govuk-list govuk-list--bullet govuk-!-margin-bottom-0">
            <li>
              state how you&rsquo;d like the information to be presented, for
              example:
              <ul className="govuk-list govuk-list--bullet">
                <li>tone (more or less formal)</li>
                <li>specific language to include</li>
                <li>length</li>
                <li>bulleted list</li>
                <li>any text to make bold</li>
              </ul>
            </li>
          </ul>
        </GovukDetails>

        <GovukFormGroup className="govuk-!-margin-bottom-4">
          <GovukLabel htmlFor="template-heading">
            Template heading (optional)
          </GovukLabel>
          <GovukHint
            id="template-heading-hint"
            className="govuk-!-margin-bottom-1"
          >
            This will appear at the top of your document above Section 1 (it can
            be different from the template title, which will not appear in the
            document)
          </GovukHint>
          <GovukInput
            id="template-heading"
            aria-describedby="template-heading-hint"
            {...form.register('heading')}
          />
        </GovukFormGroup>

        <GovukFormGroup
          hasError={!!errors.content}
          className="govuk-!-margin-bottom-0"
        >
          <h3 className="govuk-heading-s govuk-!-margin-bottom-2">
            Template content
          </h3>
          <GovukHint
            id="template-content-hint"
            className="govuk-!-margin-bottom-2"
          >
            The template content should look how you would like the output to
            look. Use placeholder text combined with format instructions to
            describe what you would like in each section and how you want the
            information presented.
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

      {actions}
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
    extensions: [StarterKit],
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
    immediatelyRender: false,
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
      aria-describedby="template-content-hint"
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
