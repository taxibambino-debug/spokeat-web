# Writing brief: SEO + E-E-A-T articles for a speaking-opportunity platform

## The site
A platform called Spoke At (spokeat.com) that helps mid-level and senior professionals find speaking opportunities: guest lectures in specific university courses (campus and online), business schools, student societies, alumni programmes, professional associations and chambers of commerce, meetups, and conferences/podcasts/webinars. It researches opportunities, identifies the right contact (for example the course coordinator), drafts the outreach email in the organiser's language, and can send it for the user (max 2 pitches per organiser per month; one polite follow-up; never goes around someone who did not reply). Search is free; users buy outreach packs; "no replies, no charge" guarantee. It is NOT for paid speaking gigs and does NOT write talks, slides or presentation material for users. Audience: professionals who want visibility, credibility and practice. The site is in English and Swedish.

Mention the product only in the intro hook (optional, one line) and the final call to action. Articles must be genuinely useful on their own.

## Your task
For each article number assigned to you, write TWO files:
- English: `/home/claude/spk/articles/en/<en-slug>.md`
- Swedish: `/home/claude/spk/articles/sv/<sv-slug>.md`

Slugs, titles, keywords, angle, internal links and CTA for every article are in the content plan, which is in your task message. The slug map for ALL 47 articles is `/home/claude/spk/articles/slugs.json` (use it for internal links).

The Swedish article is a local version, not a translation: Swedish examples, Swedish sources where they exist (for example 1177.se, UHR, antagning.se, studera.nu, university .se pages), natural Swedish terms (kursansvarig, läsperiod, studentkår, termin). Same structure and quality.

## Hard rules (non-negotiable)
1. **No invented facts.** Every statistic, research finding, date, price, programme name or claim about an organisation must come from a page you opened with WebFetch (or a WebSearch result you then verified). If you cannot verify it, leave it out.
2. **Every external link must be one you successfully opened.** No guessed URLs. Prefer: peer-reviewed research (journal pages, PubMed, DOI links), universities, government and public bodies (1177.se, Folkhälsomyndigheten, UHR, Universitetskanslersämbetet, NHS, APA), recognised professional bodies, established publications. Avoid Wikipedia as a cited source, content farms, and competitors' sales pages.
3. **No invented people.** No fake quotes, testimonials, case studies or named experts. Author and reviewer are placeholders (see template). You may write illustrative examples only if clearly marked as hypothetical ("For example, a head of payments might…").
4. **No invented organisations or listings.** City pages and directory pages list only real institutions/providers you verified, each with its source link and the date checked. Prices only if published on the provider's own page, with the date. No "best" rankings; order alphabetically or by type.
5. **YMYL care (articles 39, 40, 41, 47 and any health mention):** no diagnosis or treatment advice; describe research findings with their limits; state that persistent or severe anxiety should be discussed with a doctor or psychologist; include where to get help (Swedish version: 1177.se and, for acute situations, 112; English version: a GP/healthcare provider and local emergency number, optionally NHS/APA pages). The reviewer placeholder must say a licensed psychologist must review before publishing.
6. **Do not misrepresent research.** Note when findings are contested (for example power posing, the 7-38-55 rule).
7. **Plain, direct language.** Active voice, short sentences, no fluff, no "in today's fast-paced world", no em-dash asides. British English spelling for English.
8. Length: 1,200–1,800 words of body text per article (directory and city pages may be longer if the listings need it).

## File template (Markdown with YAML front matter)

```markdown
---
title: "<H1 title>"
meta_title: "<max 60 characters, includes main keyword>"
meta_description: "<max 155 characters>"
slug: "<slug>"
lang: "en"            # or "sv"
alternate: "/sv/<sv-slug>"   # the other language version (for hreflang); use /en/<en-slug> in Swedish files
article_number: <n>
cluster: "<cluster>"
main_keyword: "<keyword>"
secondary_keywords: ["...", "..."]
author: "[AUTHOR NAME]"
author_role: "[AUTHOR ROLE, e.g. guest lecturer and founder]"
author_bio_url: "/authors/[author-slug]"
reviewer: "[REVIEWER NAME]"          # required for YMYL; otherwise "[OPTIONAL REVIEWER NAME]"
reviewer_credentials: "[e.g. Licensed psychologist (leg. psykolog)]"
reviewer_url: "/authors/[reviewer-slug]"
published: "[PUBLISH DATE]"
last_reviewed: "2026-11-16"
sources_checked: "2026-11-16"
---

# <H1 title>

> **Written by** [[AUTHOR NAME]](/authors/[author-slug]), [AUTHOR ROLE]. **Reviewed by** [[REVIEWER NAME]](/authors/[reviewer-slug]), [CREDENTIALS]. Last reviewed 16 November 2026. [How we research and fact-check](/about/editorial-policy)

<intro: 2–4 short paragraphs, the reader's problem and what they get>

## Key takeaways
- 3–5 bullets

## <H2 sections …>
(Use H2/H3. Cite sources inline as numbered links, e.g. "…increases heart rate [[1]](#ref-1)." Use descriptive internal links to other articles: [how to email a course coordinator](/en/guest-lecture-email-templates).)

## Frequently asked questions
### <question>
<answer, 2–4 sentences>
(3–5 questions people actually search)

## <CTA heading>
<2–3 sentences + link to the product: [CTA text](/start)>

## Sources
1. <a id="ref-1"></a>Author(s)/Organisation. "Title". Publisher/Journal, year. <https://…> (accessed 16 November 2026)
2. …

<!-- schema -->
```json
{ "@context": "https://schema.org", "@graph": [
  { "@type": "Article", "headline": "...", "inLanguage": "en", "author": {"@type":"Person","name":"[AUTHOR NAME]","url":"[SITE]/authors/[author-slug]"}, "reviewedBy": {"@type":"Person","name":"[REVIEWER NAME]"}, "datePublished": "[PUBLISH DATE]", "dateModified": "2026-11-16", "citation": ["https://…","https://…"] },
  { "@type": "FAQPage", "mainEntity": [ {"@type":"Question","name":"...","acceptedAnswer":{"@type":"Answer","text":"..."}} ] }
]}
```
```

Swedish files use Swedish labels: "Skriven av", "Granskad av", "Senast granskad 16 november 2026", "Så researchar och faktagranskar vi", "Viktigt att veta" (key takeaways), "Vanliga frågor", "Källor" (and "(hämtad 16 november 2026)"), internal links to `/sv/<sv-slug>`, CTA link `/sv/start`.

Minimum sources: 4 reputable external sources per article (YMYL and science articles: 6+, mostly peer-reviewed or public-health bodies). City and directory pages: every listed organisation links to its own official page.

## Before you finish
- Re-read each file: no unverified claims, no broken Markdown, every [n] citation has a matching source, internal links use slugs from slugs.json.
- Reply with: the files written, word counts, number of sources per file, and anything you could not verify and therefore left out.
