---
name: eli5
description: "Explains any topic, code, concept or error at a chosen audience's level of understanding, by age, education level, job role or relationship. Use when the user asks for an explanation aimed at someone, for example 'ELI5', 'explain like I am', 'explain this to my manager', 'break this down for', 'how would I explain this to my mom', 'make this understandable for a 5th grader', or asks for a non-technical explanation."
---

# Explain Like I Am... (ELI5)

Explain the topic so it matches the audience's background, vocabulary and interests.

## Step 1: Identify the audience

Parse the user's request to determine who the explanation is for, and find the closest row below. If the
audience isn't listed (a lawyer, a CEO, a nurse), infer what they know and care about, or map them to the
closest row. If the audience isn't stated at all, default to "Age 5" (classic ELI5).

### Age or education level

| Audience | Style |
|----------|-------|
| Age 5 | Super simple words. Use fun analogies with toys, animals, candy, playground. Short sentences. "Imagine you have a box of crayons..." |
| Age 10 / 5th grade | Elementary school level. Simple vocabulary, concrete examples, basic cause-and-effect, no jargon. Use school, sports, video game analogies. "Think of it like..." |
| Middle school | Can introduce basic terminology with definitions. Step-by-step logic. |
| Age 15 / High school | Teenager. Can handle moderate complexity and some abstraction. Introduce proper terms but explain them; SAT-level vocabulary OK. Be slightly casual but not cringey. Use social media, phone, gaming references. |
| Age 20-30 | Young adult. Clear and direct. Real-world analogies from daily life, work, money. |
| College student | Academic framing. Can use technical terms with brief context. Theory + practical application. |
| Graduate school | Assume strong foundational knowledge. Focus on nuance, trade-offs, edge cases, and deeper implications. Be precise. |
| Age 40+ | Mature adult. Respectful tone. Analogies from home ownership, career, family management. |

### Job roles

| Audience | They care about... | Frame explanations around... |
|----------|-------------------|------------------------------|
| Manager | Impact, timeline, risk, cost | Business outcomes, team implications, what decisions need to be made |
| Engineer | How it works, architecture, trade-offs | Technical details, implementation, performance, maintainability |
| Designer | User experience, visual impact, flow | How it affects the user, interaction patterns, accessibility |
| Director | Strategy, ROI, competitive advantage | Big picture, market position, resource allocation |
| Colleague | Practical context, shared work | How it affects their work, what they need to know to collaborate |
| Product Manager | User value, priorities, scope | Feature impact, user stories, what to build vs. skip |

### Relationships

| Audience | Tone | Analogy style |
|----------|------|---------------|
| Wife / Husband / Partner | Warm, conversational, patient | Household tasks, shared experiences, daily routines |
| Father / Mother / Parents | Respectful, clear, no condescension | Familiar technology they use, home analogies, generational bridges |
| Kids / Children (age unknown) | Playful, encouraging, short | Games, cartoons, school, animals |
| Friend | Casual, maybe humorous | Pop culture, shared interests, "you know how..." |

## Step 2: Craft the explanation

Follow these principles, scaled to the audience.

### Structure

1. **Start with the "what"**: one sentence that captures the essence.
2. **Use an analogy**: connect to something the audience already knows.
3. **Fill in details**: add layers only as appropriate for the audience level.
4. **End with the "so what"**: why does this matter to them specifically?

### Language calibration

For **simple audiences** (young ages, non-technical roles, family):
- No jargon. Zero. If a technical term is essential, define it immediately.
- One idea per sentence.
- Concrete over abstract. "The server is like a waiter at a restaurant" beats "the server handles client-server communication."
- Use "you" and "your" to make it personal.

For **technical audiences** (engineers, grad students):
- Use proper terminology, or they'll feel patronized.
- Focus on the *interesting* parts: trade-offs, edge cases, design decisions.
- Compare to things they already know: "It's like a hash map but with X difference."
- Be concise. Respect their existing knowledge.

For **business audiences** (managers, directors):
- Lead with impact and outcomes.
- Quantify where possible.
- Skip implementation details unless asked.
- Frame in terms of decisions: "This means we should..."

## Examples

**User says**: "ELI5 what a database index is"
**Audience**: Age 5 (default)
**Response style**: "Imagine you have a huuuge book with thousands of pages. Now, if I asked you to find the page about dinosaurs, you could flip through every single page... or you could look at the index at the back of the book! A database index is like that index. It helps the computer find things really fast without looking through everything."

**User says**: "Explain this API rate limiting to my manager"
**Audience**: Manager
**Response style**: "The API has a speed limit — we can only make 100 requests per minute. Right now we're hitting that limit during peak hours, which means some user requests are failing. We have two options: optimize our code to make fewer calls (1-2 days of work), or pay for a higher tier ($X/month). I'd recommend..."

**User says**: "Break down this React useEffect hook for a college student"
**Audience**: College student
**Response style**: "useEffect is React's way of handling side effects — things that happen outside the normal render cycle, like API calls, subscriptions, or DOM manipulation. Think of it as a lifecycle hook (if you've seen class components) that combines componentDidMount, componentDidUpdate, and componentWillUnmount. The dependency array controls when it re-runs..."

## Important reminders

- Never talk down to anyone. A 5-year-old explanation should feel delightful, not dumbing-down. A manager explanation should feel empowering, not dismissive of their intelligence.
- When explaining code, read the relevant code first, and explain the *purpose* before the mechanism. Nobody cares about syntax until they know why it exists.
- If the topic is genuinely complex and the audience is very non-technical, it's OK to simplify ruthlessly. Getting the core idea across at 80% accuracy is better than a 100% accurate explanation that loses the audience.
- Match the length to the audience: short and sweet for young kids, more detailed for technical audiences who want depth.

## Attribution

Adapted from [DreambigOu/ELI5](https://github.com/DreambigOu/ELI5), MIT License.
