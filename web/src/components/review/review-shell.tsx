import Link from "next/link";

export function ReviewShell({ children, actions }: { children: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex h-14 w-full max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          <div className="flex items-baseline gap-3">
            <Link href="/review/" className="w-wide text-lg font-bold tracking-tight text-indigo">
              IntelliSettle
            </Link>
            <span className="hidden text-slate sm:inline">Review desk</span>
          </div>
          <div className="flex items-center gap-2">
            {actions}
            <Link href="/" className="rounded-lg px-3 py-2 text-sm text-slate hover:bg-muted">
              Switch user
            </Link>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">{children}</main>
    </div>
  );
}
