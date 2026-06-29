'use client'

import {
  GovukButton,
  GovukErrorSummary,
  GovukFormGroup,
  GovukHint,
  GovukLabel,
} from '@/components/govuk'
import { TemplateData } from '@/types/templates'
import { Loader2 } from 'lucide-react'
import { useFieldArray, useFormContext } from 'react-hook-form'

export const FormTemplateEditor = ({
  onSubmit,
}: {
  onSubmit: (data: TemplateData) => void
}) => {
  const form = useFormContext<TemplateData>()
  const { errors, isSubmitting, isSubmitted } = form.formState

  const fieldArray = useFieldArray({
    control: form.control,
    name: 'questions',
    rules: {
      minLength: { value: 1, message: 'Must have at least one question.' },
      required: { value: true, message: 'Must have at least one question.' },
    },
  })

  const errorList = [
    errors.name?.message && {
      href: '#template-name',
      text: errors.name.message,
    },
    errors.description?.message && {
      href: '#template-description',
      text: errors.description.message,
    },
    errors.questions?.root?.message && {
      href: '#template-questions',
      text: errors.questions.root.message,
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

      <div className="flex items-center gap-4">
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
      </div>

      {/* Template details */}
      <div>
        <h2 className="govuk-heading-m">Template details</h2>
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
          <input
            id="template-name"
            className={`govuk-input govuk-!-margin-top-1${errors.name ? ' govuk-input--error' : ''}`}
            placeholder="Name your template"
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
          <input
            id="template-description"
            className={`govuk-input govuk-!-margin-top-1${errors.description ? ' govuk-input--error' : ''}`}
            placeholder="A description to help identify the template."
            aria-describedby={
              errors.description ? 'template-description-error' : undefined
            }
            {...form.register('description', {
              required: { value: true, message: 'Enter a description' },
            })}
          />
        </GovukFormGroup>
      </div>

      {/* Template content */}
      <div>
        <h2 className="govuk-heading-m">Template content</h2>
        <GovukHint className="govuk-!-margin-bottom-4">
          Add questions that you would like to be answered based on the
          transcript. For each question you can provide a description of how to
          answer it, including any style guidance. Use the &ldquo;Style
          guide&rdquo; to provide guidance that applies to every question.
        </GovukHint>

        <GovukFormGroup className="govuk-!-margin-bottom-4">
          <GovukLabel htmlFor="template-style-guide">Style guide</GovukLabel>
          <GovukHint
            id="style-guide-hint"
            className="govuk-!-margin-top-1 govuk-!-margin-bottom-2"
          >
            Optional. Enter guidance that should be followed throughout the
            whole form.
          </GovukHint>
          <textarea
            id="template-style-guide"
            className="govuk-textarea"
            rows={3}
            placeholder="Enter any guidance that should be followed throughout the whole form."
            aria-describedby="style-guide-hint"
            {...form.register('content')}
          />
        </GovukFormGroup>

        <GovukFormGroup
          hasError={!!errors.questions?.root}
          id="template-questions"
          className="govuk-!-margin-bottom-0"
        >
          <GovukLabel size="s" className="govuk-!-margin-bottom-2">
            Questions
          </GovukLabel>
          {errors.questions?.root?.message && (
            <p
              id="template-questions-error"
              className="govuk-error-message govuk-!-margin-bottom-2"
            >
              <span className="govuk-visually-hidden">Error:</span>{' '}
              {errors.questions.root.message}
            </p>
          )}

          <div className="flex flex-col gap-3">
            {fieldArray.fields.map((field, index, array) => (
              <div
                key={field.id}
                className="rounded-md border border-[#b1b4b6] bg-[#f3f2f1] p-4"
              >
                {/* Question header row */}
                <div className="govuk-!-margin-bottom-3 flex items-center justify-between">
                  <span className="govuk-body govuk-!-font-weight-bold govuk-!-margin-bottom-0">
                    Question {index + 1}
                  </span>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      className="govuk-link govuk-body-s"
                      disabled={index === 0}
                      onClick={() => fieldArray.swap(index, index - 1)}
                      aria-label={`Move question ${index + 1} up`}
                    >
                      Move up
                    </button>
                    <button
                      type="button"
                      className="govuk-link govuk-body-s"
                      disabled={index === array.length - 1}
                      onClick={() => fieldArray.swap(index, index + 1)}
                      aria-label={`Move question ${index + 1} down`}
                    >
                      Move down
                    </button>
                    <button
                      type="button"
                      className="govuk-link govuk-body-s"
                      style={{ color: '#d4351c' }}
                      onClick={() => fieldArray.remove(index)}
                      aria-label={`Delete question ${index + 1}`}
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {/* Question fields */}
                <div className="flex flex-col gap-3">
                  <GovukFormGroup className="govuk-!-margin-bottom-0">
                    <GovukLabel htmlFor={`question-title-${index}`} size="s">
                      Question text
                    </GovukLabel>
                    <input
                      id={`question-title-${index}`}
                      className="govuk-input govuk-!-margin-top-1"
                      placeholder="Question text"
                      {...form.register(`questions.${index}.title`)}
                    />
                  </GovukFormGroup>
                  <GovukFormGroup className="govuk-!-margin-bottom-0">
                    <GovukLabel
                      htmlFor={`question-description-${index}`}
                      size="s"
                    >
                      Optional description of how to answer the question, what
                      information to include and style guidance:
                    </GovukLabel>
                    <textarea
                      id={`question-description-${index}`}
                      className="govuk-textarea govuk-!-margin-top-1"
                      rows={3}
                      placeholder="Description of how to answer the question, what information to include, and style guidance."
                      {...form.register(`questions.${index}.description`)}
                    />
                  </GovukFormGroup>
                </div>
              </div>
            ))}
          </div>

          <div className="govuk-!-margin-top-3">
            <GovukButton
              type="button"
              variant="secondary"
              className="govuk-!-margin-bottom-0"
              onClick={() =>
                fieldArray.append({
                  title: '',
                  description: '',
                  position: form.watch('questions')?.length || 0,
                })
              }
            >
              Add question
            </GovukButton>
          </div>
        </GovukFormGroup>
      </div>
    </form>
  )
}
