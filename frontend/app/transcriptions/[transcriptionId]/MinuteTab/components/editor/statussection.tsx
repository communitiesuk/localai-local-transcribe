import { LucideIcon } from 'lucide-react'

type Variant = 'error' | 'warning' | 'success'

interface StatusSectionProps {
  title: string
  icon: LucideIcon
  variant: Variant
  children: React.ReactNode
}

const styles: Record<Variant, string> = {
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  success: 'bg-pink-50 border-green-200 text-green-800',
}

export function StatusSection({
  title,
  icon: Icon,
  variant,
  children,
}: StatusSectionProps) {
  return (
    <div
      className={`mb-4 flex flex-col gap-2 rounded-md border p-4 ${styles[variant]}`}
    >
      <div className="flex items-center gap-2 font-semibold">
        <Icon className="h-5 w-5" />
        <span className="text-lg">{title}</span>
      </div>
      <div className="flex flex-col gap-2">{children}</div>
    </div>
  )
}
