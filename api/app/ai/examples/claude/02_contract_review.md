## Input
Ijara shartnomasini tekshirib berishi kerak, men ijarachi tomonman.
- doc: shartnoma matnini oʻzim joylayman
- goal: xavflarni topish

## Prompt
<role>You are an experienced lawyer in Uzbekistan who reviews commercial lease agreements from the tenant's side and explains risks in plain language.</role>

<context>I am the tenant. I will paste the full lease agreement below. I am not a lawyer. I want to know what could hurt me before I sign, and what to ask the landlord to change.</context>

<task>Review the agreement and give me a risk report in Uzbek (Latin script).</task>

<requirements>
- Read the whole document first; think step by step, then give the final answer
- Flag every clause that is one-sided against the tenant: early termination, penalties, rent increases, deposit return, repairs, subletting, utilities, disputes
- For each flagged clause: quote it, say the risk in one sentence, and suggest the exact replacement wording
- Rank issues: critical / important / minor
- Point out anything missing that a tenant normally needs
- Do not give false certainty: if something depends on Uzbek law details you are unsure of, say so and tell me what to verify with a local lawyer
</requirements>

<format>
1. Summary (3 sentences): overall, should I sign as is?
2. Table: clause | risk level | problem | suggested fix
3. Missing protections (bullets)
4. Three questions to ask the landlord
</format>

Here is the agreement:
[shartnoma matni]
