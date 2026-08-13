/**
 * Structured data for the Notion-powered blog (/blog/*).
 *
 * The 45 blog posts are rendered outside this repo, so this cannot be applied
 * by editing HTML files. Drop `blogPostJsonLd(post)` into whatever renders the
 * blog `<head>` and emit the returned string there.
 *
 * What it adds, matching the static pages in this repo:
 *   - Organization + WebSite, sharing the same @id as the rest of the site so
 *     the whole domain resolves to one entity rather than 70 anonymous ones.
 *   - BreadcrumbList  (Home > Blog > Post)   -- currently missing on all 45.
 *   - BlogPosting, wired to those @ids via author/publisher/isPartOf.
 *   - Review + SoftwareApplication for posts whose Notion `Category` is
 *     "Review" or "Comparison".
 *
 * `post` is the Notion row you already have in the renderer:
 *   { Title, Slug, "Meta Description", Category, Author,
 *     "Published Date", "Featured Image" }
 *
 * NOTE ON RATINGS -- read before adding any.
 * `Review.reviewRating` and `aggregateRating` are deliberately absent. Google
 * and Bing both require a rating in structured data to be visible to the user
 * on the same page, and the blog posts do not currently display one. The
 * ratings that already exist elsewhere on the site also disagree with the
 * Notion directory (see docs/rating-discrepancies.md). To earn review rich
 * results properly: add a numeric `Rating` field to the Xchatbots Blog Posts
 * database, render it visibly in the post, and only then uncomment the
 * reviewRating block below.
 */

const ORIGIN = "https://x-chatbots.com";
const ORG_ID = `${ORIGIN}/#organization`;
const SITE_ID = `${ORIGIN}/#website`;
const LOGO_ID = `${ORIGIN}/#logo`;

const esc = (s) =>
  String(s == null ? "" : s).replace(/</g, "\\u003c").replace(/>/g, "\\u003e");

function organizationAndWebsite() {
  return [
    {
      "@type": "Organization",
      "@id": ORG_ID,
      name: "Xchatbots",
      url: `${ORIGIN}/`,
      logo: {
        "@type": "ImageObject",
        "@id": LOGO_ID,
        url: `${ORIGIN}/media/XC-2.png`,
        contentUrl: `${ORIGIN}/media/XC-2.png`,
        width: 406,
        height: 258,
        caption: "Xchatbots",
      },
      image: { "@id": LOGO_ID },
      description:
        "Xchatbots is an independent directory of NSFW and uncensored AI chatbots, " +
        "AI companions, and AI image and video generators, with hands-on testing " +
        "and transparent review criteria.",
      sameAs: ["https://www.reddit.com/r/XChatbots/"],
    },
    {
      "@type": "WebSite",
      "@id": SITE_ID,
      url: `${ORIGIN}/`,
      name: "Xchatbots",
      description:
        "Independent directory and reviews of NSFW AI chatbots, AI companions and " +
        "uncensored AI image and video generators.",
      publisher: { "@id": ORG_ID },
      inLanguage: "en",
    },
  ];
}

/** "OurDream AI Review 2026: ..." -> "OurDream AI" */
function reviewedToolName(title) {
  const m = String(title).match(
    /^(.+?)\s+(?:Review\b|vs\.?\s|Alternatives\b)/i
  );
  return m ? m[1].trim() : null;
}

function blogPostJsonLd(post) {
  const slug = String(post.Slug || "").replace(/^\/+|\/+$/g, "");
  const url = `${ORIGIN}/blog/${slug}`;
  const title = post.Title || "";
  const description = post["Meta Description"] || "";
  const published = String(post["Published Date"] || "").split("T")[0];
  const category = post.Category || "";
  const image = post["Featured Image"] || `${ORIGIN}/media/XC-2.png`;

  const graph = organizationAndWebsite();

  graph.push({
    "@type": "BreadcrumbList",
    "@id": `${url}#breadcrumb`,
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: `${ORIGIN}/` },
      { "@type": "ListItem", position: 2, name: "Blog", item: `${ORIGIN}/blog` },
      { "@type": "ListItem", position: 3, name: title, item: url },
    ],
  });

  const posting = {
    "@type": "BlogPosting",
    "@id": `${url}#article`,
    headline: title,
    description,
    url,
    mainEntityOfPage: { "@type": "WebPage", "@id": url },
    isPartOf: { "@id": SITE_ID },
    author: post.Author
      ? { "@type": "Organization", "@id": ORG_ID, name: post.Author }
      : { "@id": ORG_ID },
    publisher: { "@id": ORG_ID },
    breadcrumb: { "@id": `${url}#breadcrumb` },
    inLanguage: "en",
  };
  if (published) {
    posting.datePublished = published;
    // Swap in a real "last edited" field here if the blog service exposes one.
    posting.dateModified = published;
  }
  if (image) posting.image = image;
  graph.push(posting);

  // Tool reviews and head-to-head comparisons get a Review entity.
  if (category === "Review" || category === "Comparison") {
    const tool = reviewedToolName(title);
    if (tool) {
      graph.push({
        "@type": "Review",
        "@id": `${url}#review`,
        url,
        name: title,
        author: { "@id": ORG_ID },
        publisher: { "@id": ORG_ID },
        ...(published ? { datePublished: published } : {}),
        itemReviewed: {
          "@type": "SoftwareApplication",
          name: tool,
          applicationCategory: "LifestyleApplication",
          operatingSystem: "Web",
        },
        // Add ONLY once a rating is stored in Notion and shown on the page:
        // reviewRating: {
        //   "@type": "Rating",
        //   ratingValue: String(post.Rating),
        //   bestRating: "5",
        //   worstRating: "1",
        // },
      });
    }
  }

  return (
    '<script type="application/ld+json">' +
    esc(JSON.stringify({ "@context": "https://schema.org", "@graph": graph })) +
    "</script>"
  );
}

/*
 * While you are in this file: the `<title>` for blog posts currently appends
 * " | Xchatbots Blog". That 17-character suffix is the sole reason 8 posts
 * exceed Bing's 70-character title limit -- every one of them is <= 68
 * characters without it. Dropping the suffix clears all 8 with no editorial
 * change.
 */

export { blogPostJsonLd, organizationAndWebsite };
