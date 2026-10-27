import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../../lib/api";
import type { PortfolioPage } from "../../lib/types";
import { Card, EmptyState, Spinner } from "../../components/ui";

export function PortfolioPublic() {
  const { slug = "" } = useParams();
  const query = useQuery({
    queryKey: ["public-portfolio", slug],
    queryFn: () => api.get<PortfolioPage>(`/portfolio/public/${slug}`),
  });

  if (query.isLoading) return <Spinner label="Loading portfolio" />;
  if (query.isError || !query.data) {
    return (
      <div className="container-page py-20">
        <EmptyState title="Portfolio not found" description="This portfolio may be unpublished or the link may be incorrect." action={<Link to="/" className="link-quiet">Go home</Link>} />
      </div>
    );
  }

  const page = query.data;
  const bio = page.content?.bio;

  return (
    <div className="min-h-screen bg-ivory-100">
      <div className="container-page max-w-3xl py-16">
        <p className="eyebrow">Portfolio</p>
        <h1 className="mt-2 font-serif text-4xl">{page.title}</h1>
        {bio && <p className="mt-4 max-w-prose text-ink-soft">{bio}</p>}
        <Card className="mt-8">
          <h2 className="font-serif text-xl">Projects & evidence</h2>
          <p className="mt-2 text-sm text-ink-muted">
            Project case studies and links you publish from the Resumo workspace appear here.
          </p>
        </Card>
        <p className="mt-8 text-xs text-ink-muted">
          Built with Resumo — an advisory career-preparation tool. All content is provided by the candidate.
        </p>
      </div>
    </div>
  );
}
