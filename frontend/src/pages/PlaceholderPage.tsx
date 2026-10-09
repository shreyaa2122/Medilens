// Honest placeholder: the route exists, but the feature is not available yet.
interface PlaceholderPageProps {
  title: string;
  description: string;
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div>
      <h1 className="text-3xl font-semibold">{title}</h1>
      <div className="mt-6 rounded-lg border border-dashed border-line bg-surface p-8">
        <p className="font-medium">This page is not available yet.</p>
        <p className="mt-1 max-w-prose text-sm text-slate">{description}</p>
      </div>
    </div>
  );
}
