export function Privacy() {
  return (
    <div className="container-page max-w-prose py-14 prose-editorial">
      <p className="eyebrow">Privacy</p>
      <h1 className="mt-2 font-serif text-4xl">Privacy in plain language</h1>
      <p />
      <h2 className="mt-8 font-serif text-2xl">What we store</h2>
      <p>
        Your account details, profile information, uploaded resumes and derived analyses, generated documents,
        roadmaps and application records — all tied to your account and protected by ownership checks.
      </p>
      <h2 className="mt-8 font-serif text-2xl">Your files</h2>
      <p>
        Uploaded files are stored privately and served only through authorisation-checked access. We keep the
        original and any derived content separately so you can compare them. Deleting a resume removes its stored
        files and derived records.
      </p>
      <h2 className="mt-8 font-serif text-2xl">When AI is used</h2>
      <p>
        AI features are optional. If you use them, the text you submit for that action (for example a resume and a
        job description) is sent to the configured AI provider. By default Resumo is configured to use a provider
        you control (such as a local Ollama model). Deterministic parsing, scoring and export work without any AI.
      </p>
      <h2 className="mt-8 font-serif text-2xl">What we don't do</h2>
      <p>
        We don't sell your data, use uploaded documents to train models without informed consent, collect sensitive
        personal data you don't need to provide, or profile you for unrelated purposes.
      </p>
      <h2 className="mt-8 font-serif text-2xl">Deleting your data</h2>
      <p>
        You can delete resumes and applications from the workspace, and request full account deletion. Deletion
        covers related records, stored files and derived artifacts.
      </p>
      <p className="mt-8 text-sm text-ink-muted">
        This is a demonstration deployment. Before production use, replace this text with a reviewed policy.
      </p>
    </div>
  );
}
