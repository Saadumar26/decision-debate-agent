# Decision Muse

Build a clean, modern web app called "Decision Debate Agent" — a tool where a user types a hard personal decision they're weighing, and gets back a structured multi-perspective analysis.

Layout:

A hero section with the title "Decision Debate Agent" and a subtitle: "Three perspectives argue your decision. You make the call."

A large textarea for the user to type their decision, with a placeholder example, and a "Run the Debate" button

While loading, show a tasteful loading state (e.g. three pulsing cards labeled "Optimist", "Skeptic", "Analyst")

After results load, show three side-by-side cards (stack vertically on mobile) titled "Optimist", "Skeptic", "Analyst" — each with a distinct accent color (e.g. green for Optimist, amber for Skeptic, blue for Analyst) — displaying their argument as bullet points

Below that, a prominent "Recommendation" card that stands out visually (different background), showing the final moderator recommendation

If verification_retries > 0, show a small subtle badge like "Revised once after review" near the recommendation

Footer note: "This is a recommendation, not a decision. The choice stays with you."

Functionality:

On submitting the form, POST to http://localhost:5000/debate with JSON body {"query": "<user's text>"}

The response JSON has fields: optimist_view (string), skeptic_view (string), analyst_view (string), moderator_output (string), verification_retries (number), retrieved_context (string, may be empty)

Render the string fields as markdown (they contain bullet points formatted with * or -)

Handle loading and error states gracefully (show a clear error message if the fetch fails)

Use React with TypeScript, Tailwind CSS, and shadcn/ui components

Design should feel premium and calm — soft shadows, generous whitespace, a serif or clean sans-serif heading font — not like a generic AI-tool template

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://decision-debate-agent.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/4b78f881-52ad-45e7-b142-4a0cbf1c41bb).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
