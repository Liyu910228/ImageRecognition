import type { LucideIcon } from "lucide-react";

export type UserRole = "admin" | "business";

export type WorkspaceModule = {
  key: string;
  label: string;
  description: string;
  icon: LucideIcon;
};
