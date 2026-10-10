"use client";

import { SWRConfig } from "swr";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { fetcher } from "@/lib/api";
import { LangProvider } from "@/lib/i18n";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <LangProvider>
      <SWRConfig value={{ fetcher, revalidateOnFocus: false, shouldRetryOnError: false }}>
        <TooltipProvider>
          {children}
          <Toaster position="top-center" theme="light" richColors />
        </TooltipProvider>
      </SWRConfig>
    </LangProvider>
  );
}
