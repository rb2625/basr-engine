export default function EmptyState({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && (
        <div className="mb-4 text-4xl opacity-40">{icon}</div>
      )}
      <div className="text-[15px] font-medium text-ink">{title}</div>
      <div className="mt-1 max-w-sm text-[13px] text-mute">{description}</div>
    </div>
  );
}
