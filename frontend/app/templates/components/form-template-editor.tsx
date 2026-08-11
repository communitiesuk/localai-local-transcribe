'use client'

import {
  GovukButton,
  GovukDetails,
  GovukErrorSummary,
  GovukFormGroup,
  GovukHint,
  GovukInput,
  GovukLabel,
  GovukTextarea,
} from '@/components/govuk'
import { TemplateData } from '@/types/templates'
import Link from 'next/link'
import { Loader2 } from 'lucide-react'
import { useFieldArray, useFormContext } from 'react-hook-form'

export const FormTemplateEditor = ({
  onSubmit,
  submitLabel,
}: {
  onSubmit: (data: TemplateData) => void
  submitLabel: string
}) => {
  const form = useFormContext<TemplateData>()
  const { errors, isSubmitting, isSubmitted } = form.formState

  const fieldArray = useFieldArray({
    control: form.control,
    name: 'questions',
    rules: {
      minLength: {
        value: 1,
        message: 'A template must have at least one section',
      },
      required: {
        value: true,
        message: 'A template must have at least one section',
      },
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
      href: '#template-sections',
      text: errors.questions.root.message,
    },
    ...(fieldArray.fields.flatMap((_, index) => [
      errors.questions?.[index]?.title?.message && {
        href: `#section-heading-${index}`,
        text: `Section ${index + 1}: ${errors.questions![index]!.title!.message}`,
      },
      errors.questions?.[index]?.description?.message && {
        href: `#section-information-${index}`,
        text: `Section ${index + 1}: ${errors.questions![index]!.description!.message}`,
      },
    ]) as { href: string; text: string }[]),
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
        <GovukHint className="govuk-!-margin-bottom-2">
          Add and order sections to make up this template
        </GovukHint>

        <GovukDetails summary="Useful tips" className="govuk-!-margin-bottom-4">
          <p className="govuk-body">
            Customise your template based on how you want your document to be
            presented. Each section has 3 editable fields:
          </p>
          <p className="govuk-body govuk-!-font-weight-bold govuk-!-margin-bottom-1">
            Section heading:
          </p>
          <ul className="govuk-list govuk-list--bullet">
            <li>
              how you want each section&rsquo;s heading to appear in the
              document
            </li>
            <li>headings are case sensitive</li>
          </ul>
          <p className="govuk-body govuk-!-font-weight-bold govuk-!-margin-bottom-1">
            Section information:
          </p>
          <ul className="govuk-list govuk-list--bullet">
            <li>
              state the information you&rsquo;d like to include, or questions
              you&rsquo;d like answered, in this section
            </li>
            <li>
              use a new line for each question or desired piece of information
            </li>
            <li>
              the information will be pulled from the transcript into the
              document
            </li>
          </ul>
          <p className="govuk-body govuk-!-font-weight-bold govuk-!-margin-bottom-1">
            Format instructions (optional):
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
          hasError={!!errors.questions?.root}
          id="template-sections"
          className="govuk-!-margin-bottom-0"
        >
          <h3 className="govuk-heading-s govuk-!-margin-bottom-2">
            Template sections
          </h3>
          {errors.questions?.root?.message && (
            <p
              id="template-sections-error"
              className="govuk-error-message govuk-!-margin-bottom-2"
            >
              <span className="govuk-visually-hidden">Error:</span>{' '}
              {errors.questions.root.message}
            </p>
          )}

          <div className="flex flex-col gap-3">
            {fieldArray.fields.map((field, index, array) => (
              <div key={field.id} className="govuk-summary-card">
                <div className="govuk-summary-card__title-wrapper">
                  <h4 className="govuk-summary-card__title">
                    Section {index + 1}
                  </h4>
                  <ul className="govuk-summary-card__actions">
                    <li className="govuk-summary-card__action">
                      <button
                        type="button"
                        className="govuk-link govuk-body-s govuk-!-font-weight-bold"
                        disabled={index === 0}
                        onClick={() => fieldArray.swap(index, index - 1)}
                        aria-label={`Move section ${index + 1} up`}
                      >
                        Move up
                      </button>
                    </li>
                    <li className="govuk-summary-card__action">
                      <button
                        type="button"
                        className="govuk-link govuk-body-s govuk-!-font-weight-bold"
                        disabled={index === array.length - 1}
                        onClick={() => fieldArray.swap(index, index + 1)}
                        aria-label={`Move section ${index + 1} down`}
                      >
                        Move down
                      </button>
                    </li>
                    <li className="govuk-summary-card__action">
                      <button
                        type="button"
                        className="govuk-link govuk-body-s govuk-!-font-weight-bold"
                        disabled={array.length === 1}
                        onClick={() => fieldArray.remove(index)}
                        aria-label={`Remove section ${index + 1}`}
                      >
                        Remove
                      </button>
                    </li>
                  </ul>
                </div>
                <div className="govuk-summary-card__content">
                  <div className="flex flex-col gap-3">
                    <GovukFormGroup
                      hasError={!!errors.questions?.[index]?.title}
                      className="govuk-!-margin-bottom-0"
                    >
                      <GovukLabel htmlFor={`section-heading-${index}`}>
                        Section heading
                      </GovukLabel>
                      {errors.questions?.[index]?.title?.message && (
                        <p
                          id={`section-heading-${index}-error`}
                          className="govuk-error-message"
                        >
                          <span className="govuk-visually-hidden">Error:</span>{' '}
                          {errors.questions[index].title.message}
                        </p>
                      )}
                      <GovukInput
                        id={`section-heading-${index}`}
                        aria-invalid={!!errors.questions?.[index]?.title}
                        aria-describedby={
                          errors.questions?.[index]?.title
                            ? `section-heading-${index}-error`
                            : undefined
                        }
                        {...form.register(`questions.${index}.title`, {
                          required: {
                            value: true,
                            message: 'Enter a section heading',
                          },
                        })}
                      />
                    </GovukFormGroup>
                    <GovukFormGroup
                      hasError={!!errors.questions?.[index]?.description}
                      className="govuk-!-margin-bottom-0"
                    >
                      <GovukLabel htmlFor={`section-information-${index}`}>
                        Section information
                      </GovukLabel>
                      {errors.questions?.[index]?.description?.message && (
                        <p
                          id={`section-information-${index}-error`}
                          className="govuk-error-message"
                        >
                          <span className="govuk-visually-hidden">Error:</span>{' '}
                          {errors.questions[index].description.message}
                        </p>
                      )}
                      <GovukTextarea
                        id={`section-information-${index}`}
                        rows={3}
                        aria-invalid={!!errors.questions?.[index]?.description}
                        aria-describedby={
                          errors.questions?.[index]?.description
                            ? `section-information-${index}-error`
                            : undefined
                        }
                        {...form.register(`questions.${index}.description`, {
                          required: {
                            value: true,
                            message: 'Enter section information',
                          },
                        })}
                      />
                    </GovukFormGroup>
                    <GovukFormGroup className="govuk-!-margin-bottom-0">
                      <GovukLabel htmlFor={`section-format-${index}`}>
                        Format instructions (optional)
                      </GovukLabel>
                      <GovukTextarea
                        id={`section-format-${index}`}
                        className="govuk-!-margin-top-1"
                        rows={3}
                        {...form.register(
                          `questions.${index}.format_instructions`
                        )}
                      />
                    </GovukFormGroup>
                  </div>
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
                  format_instructions: '',
                  position: fieldArray.fields.length,
                })
              }
            >
              Add section
            </GovukButton>
          </div>
        </GovukFormGroup>
      </div>

      <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-bottom-0" />

      <div className="flex items-center gap-4">
        <GovukButton
          type="submit"
          disabled={isSubmitting}
          className="govuk-!-margin-bottom-0"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="animate-spin" aria-hidden="true" /> Saving…
            </>
          ) : (
            submitLabel
          )}
        </GovukButton>
        <Link href="/templates" className="govuk-link">
          Cancel
        </Link>
      </div>
    </form>
  )
}
