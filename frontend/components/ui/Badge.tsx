import { cn, CATEGORY_COLORS } from "@/lib/utils";

interface BadgeProps {
  category: string;
  className?: string;
}

export function CategoryBadge({ category, className }: BadgeProps) {
  return (
    <span className={cn("badge", CATEGORY_COLORS[category] || CATEGORY_COLORS.other, className)}>
      {category}
    </span>
  );
}
