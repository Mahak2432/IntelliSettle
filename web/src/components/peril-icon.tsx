import { CloudHail, CloudRain, Waves } from "lucide-react";
import type { Peril } from "@/lib/types";

const ICONS = { flood: Waves, excess_rain: CloudRain, hailstorm: CloudHail } as const;

export function PerilIcon({ peril, className = "size-6" }: { peril: Peril; className?: string }) {
  const Icon = ICONS[peril];
  return <Icon className={className} aria-hidden />;
}
