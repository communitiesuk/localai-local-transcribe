interface PauseButtonProps {
  width?: number
  height?: number
}

export function PauseButton({ width = 24, height = 24 }: PauseButtonProps) {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect
        x="5"
        y="4"
        width="4"
        height="16"
        fill="white"
        stroke="black"
        strokeWidth="1.5"
      />
      <rect
        x="15"
        y="4"
        width="4"
        height="16"
        fill="white"
        stroke="black"
        strokeWidth="1.5"
      />
    </svg>
  )
}
