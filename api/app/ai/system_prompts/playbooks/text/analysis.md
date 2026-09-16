# Analysis: decision, comparison, idea critique
## Required facts
- question: the exact decision or thing to evaluate (open a second branch or not; idea A vs idea B; is this business idea viable) | ask: What exactly should be decided or evaluated? | default: narrow the user's text to one yes/no or A-vs-B question and state it
- data: the numbers and facts that matter (revenue, costs, customers, prices, time, competitors) | ask: What numbers or facts do you have (revenue, costs, customers, prices)? | default: [raqamlar] placeholders with an instruction to ask for the 3 most important ones before analysing
- criteria: what "good" means for the user (profit, risk, time, effort, growth) and their priority | ask: What matters most in this decision — profit, risk, time or something else? | default: profit, risk and required effort, in that order
- context: who the user is and their situation (a small shop owner in Samarkand, a student choosing a course) | ask: Tell me about your situation in one or two lines | default: a small business owner or student in Uzbekistan with limited budget
- horizon: over what period the result matters (3 months, 1 year, 5 years) | ask: Over what period should the outcome be judged? | default: 12 months
- language: language of the answer | ask: Which language should the analysis be in? | default: Uzbek (Latin)
## Must include
- The decision stated as one precise question with the criteria and the horizon
- Summary first: a 3-sentence verdict with a confidence percentage, then the detailed analysis
- Options laid out in a table with the same criteria for each (Criterion | Option A | Option B | Which wins and why)
- Critical block: the strongest 3 counter-arguments to the recommended option, hidden assumptions the analysis relies on, and what evidence would change the verdict
- Scenarios: best / likely / worst with a rough probability each and the concrete trigger for each
- A named framework fitting the case (SWOT, Pros/Cons with weights, 5W1H, cost–benefit / simple ROI, Eisenhower for priorities, pre-mortem for risky plans) and an instruction to use it visibly
- Answer language and plain-language rule (no MBA jargon; explain any term once)
## Quality rules
- The model must separate facts given by the user from its own assumptions and list the assumptions explicitly
- "Not enough information" rule: where data is missing, the model writes what is missing and how to get it instead of guessing a number
- Every argument must be backed by a number, a concrete mechanism or a local example — no "it is generally better"
- Second perspective: require one paragraph from an opposing role (a cautious accountant, a competitor, the customer) to stress-test the recommendation
- Recommendation ends with the next 3 concrete steps and one cheap test to validate the decision within 2 weeks
- Length cap: under 600 words, tables preferred over paragraphs
- Confidence must be stated as a percentage and justified in one sentence
- If the question is a comparison of products or services with changing prices, instruct the model to say prices may be outdated and to mark them [tekshirish kerak]
## Avoid
- A one-sided "yes, great idea" answer with no counter-arguments or worst case
- Inventing market sizes, competitor numbers or prices to fill the table
- Analysing several unrelated decisions in one prompt
- Generic theory about decision making instead of the user's actual numbers
- Ten-page consultant structure for a decision a small business needs to make this week
