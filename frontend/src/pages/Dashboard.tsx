import { useQuery } from "@tanstack/react-query";
import { CircleAlert, CircleCheck, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import { getHealth } from "../api/client";
import { DocumentList } from "../components/DocumentList";

function ServerStatus() {
  const { data, error, isPending } = useQuery({ queryKey: ["health"], queryFn: getHealth });

  if (isPending) {
    return (
      <p className="flex items-center gap-2 text-sm text-slate">
        <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
        Checking the MediLens server…
      </p>
    );
  }
  if (error) {
    return (
      <p className="flex items-start gap-2 text-sm text-rust">
        <CircleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <span>
          {error.message} Make sure the backend is running on port 8000.
        </span>
      </p>
    );
  }
  return (
    <p className="flex items-center gap-2 text-sm">
      <CircleCheck className="h-4 w-4 text-teal" aria-hidden="true" />
      Server connected · {data.service} v{data.version} ({data.environment})
    </p>
  );
}

export function Dashboard() {
  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-semibold">Your health documents</h1>
        <p className="mt-2 max-w-prose text-slate">
          Upload lab reports and prescriptions to see what they say in plain language, with every
          value traced back to the original page.
        </p>
      </header>

      <section aria-labelledby="status-heading" className="rounded-lg border border-line bg-surface p-5">
        <h2 id="status-heading" className="mb-3 text-lg font-semibold">
          System status
        </h2>
        <ServerStatus />
      </section>

      <section aria-labelledby="documents-heading" className="rounded-lg border border-line bg-surface p-5">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 id="documents-heading" className="text-lg font-semibold">
            Documents
          </h2>
          <Link
            to="/upload"
            className="rounded-md bg-teal px-4 py-2 text-sm font-medium text-white hover:bg-teal/90"
          >
            Upload a document
          </Link>
        </div>
        <DocumentList />
      </section>
    </div>
  );
}
