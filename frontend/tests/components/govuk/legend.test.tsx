import { GovukLegend } from '@/components/govuk/legend'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukLegend />', () => {
  it('renders a legend with the canonical govuk-fieldset__legend class', () => {
    render(<GovukLegend>Question</GovukLegend>)
    const legend = screen.getByText('Question')
    expect(legend.tagName).toBe('LEGEND')
    expect(legend).toHaveClass('govuk-fieldset__legend')
  })

  it.each(['s', 'm', 'l', 'xl'] as const)(
    'adds govuk-fieldset__legend--%s when size=%s',
    (size) => {
      render(<GovukLegend size={size}>Question</GovukLegend>)
      const legend = screen.getByText('Question')
      expect(legend).toHaveClass(
        'govuk-fieldset__legend',
        `govuk-fieldset__legend--${size}`
      )
    }
  )

  it('does not add a size modifier when size is omitted', () => {
    render(<GovukLegend>Question</GovukLegend>)
    const legend = screen.getByText('Question')
    expect(legend.className).toBe('govuk-fieldset__legend')
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    render(<GovukLegend className="mb-2">Question</GovukLegend>)
    const legend = screen.getByText('Question')
    expect(legend).toHaveClass('govuk-fieldset__legend', 'mb-2')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    render(
      <GovukLegend data-testid="lg" id="legend-1">
        Question
      </GovukLegend>
    )
    expect(screen.getByTestId('lg')).toHaveAttribute('id', 'legend-1')
  })
})
