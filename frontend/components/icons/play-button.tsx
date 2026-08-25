interface PlayButtonProps {
  width?: number
  height?: number
}

export function PlayButton({ width = 24, height = 24 }: PlayButtonProps) {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M8 19V5L19 12L8 19Z" fill="#1C1B1F" />
    </svg>
  )
}
