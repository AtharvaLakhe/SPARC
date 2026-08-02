# SPARC business viability hypotheses

**Status:** plausible product and business-model hypotheses; not market validation  
**Evidence boundary:** no customer interviews, paid pilots, procurement approvals, market sizing or revenue are recorded in this repository

## 1. Product hypothesis

SPARC could reduce the specialist effort required to turn open Earth-observation products into a transparent district-level screening view. The proposed value is not proprietary access to Sentinel or Landsat data and not a novel claim about index formulas. The value hypothesis is a usable workflow that packages:

- comparable before/after periods;
- reproducible water, vegetation and built-up proxy calculations;
- child-region context when geometry/data pass QA;
- quality, provenance and limitations beside each number;
- reliable offline or low-connectivity delivery; and
- a clear handoff from screening evidence to field verification.

This remains unvalidated. A working prototype can show technical feasibility; it cannot by itself prove willingness to pay, procurement fit or decision impact.

## 2. Candidate users, buyers and jobs

| User | Possible buyer | Job the prototype may help with | Evidence still needed |
|---|---|---|---|
| District/environment staff | District/state programme or implementation partner | Screen areas and changes that deserve inspection; prepare an evidence briefing | current workflow, legal mandate, procurement route, acceptable accuracy/latency and data-governance requirements |
| NGO/community programme team | NGO, foundation or donor | Prioritize field visits and communicate observations transparently | frequency, offline need, language/accessibility, harm/contestability concerns and budget |
| CSR sustainability team | Enterprise/CSR foundation | Screen project geographies and support monitoring conversations | reporting standard fit, auditability, liability, procurement/security and willingness to pay |
| Environmental consultant | Consulting firm | Produce reproducible screening evidence faster | time saved, integration/export needs, professional-review expectations and price sensitivity |
| Research/education team | Institution or grant | Teach/inspect methods and provenance | curriculum/research fit, reproducibility needs and support burden |

“Beneficiary” and “customer” may be different. A community may use or be affected by a map while an institution pays. Product discovery must include both, not only the buyer.

- **Potential government use:** an evidence-screening/briefing aid for deciding where expert or field review is warranted; never statutory reporting, certification, enforcement evidence, or an official SDG value without the required legal/scientific process.
- **Potential NGO/community use:** transparent prioritization and communication with a contestable source/limitation trail; test whether affected communities can interpret and challenge the result.
- **Potential CSR use:** observational screening and monitoring conversations with explicit separation from causal impact or compliance claims.
- **Potential environmental-consulting use:** reproducible first-pass evidence and provenance that a qualified practitioner reviews, rather than a replacement for professional judgment.

## 3. Value propositions to test

These are hypotheses, not established benefits:

1. **Faster screening:** a versioned district summary may reduce repeated scene-discovery and preprocessing work.
2. **More defensible communication:** visible provenance, quality and caveats may reduce unsupported claims in briefings.
3. **Low-connectivity usability:** an offline immutable pack may work where live GIS portals are unreliable.
4. **Consistent comparison:** fixed same-season methods may make repeated reviews more comparable than ad hoc screenshots.
5. **Auditable handoff:** stable result IDs, item IDs and method versions may make expert/field follow-up easier.

Each must be measured against the user’s current process. “Users liked the dashboard” is insufficient evidence of decision value.

## 4. Plausible business models

| Model hypothesis | Offer | Likely buyer | Revenue mechanism | Strength | Main risk | Minimum validation experiment |
|---|---|---|---|---|---|---|
| Freemium/public evidence tier | Free access to a small, visibly dated set of reviewed district summaries; paid custom periods, validation, support or integration | Public-interest users, NGOs and evaluators who may later sponsor deeper work | Free discovery tier plus paid bounded service/institutional upgrade | Low-friction evaluation and public-benefit access | Free users may mistake illustrative coverage for universal service; hosting/support and scientifically reviewed updates still cost money | Publish one fixed reviewed pack, measure qualified follow-up and test whether any team pays for a clearly different validated deliverable |
| Fixed-scope evidence pack | One district/period pack, briefing and provenance/limitations appendix | NGO, CSR programme or consultant | project fee | simple and compatible with precomputed architecture | becomes bespoke consulting; results may not meet buyer’s proof standard | quote a clearly bounded pilot to 5–10 target teams and test paid intent, inputs and acceptance criteria |
| Annual institutional subscription | Updated approved districts, dashboard access, support and versioned releases | NGO network, enterprise/CSR or public implementation partner | annual contract | recurring relationship and predictable update windows | long procurement/security cycles; update cost may be high | interview procurement, data and programme owners; request a paid design-partner commitment |
| Analyst workspace/API | Contracted access to metadata/results and exports for approved regions | Consulting/research teams | usage tier or seat/organization license | integrates into professional workflows | open source/open data limit defensibility; support/SLA burden | prototype one export/API workflow and measure time saved versus current tools |
| Monitoring service | Scheduled comparable evidence, QA review and field-verification workflow | CSR/environment programmes | recurring service fee | combines software with scientific review | may imply causation/compliance if marketed carelessly | define an observational-only statement of work and have legal/domain buyers review claims |
| Grant/public-interest deployment | Open local instances, training and community validation | Foundations, research/public programmes | grant or implementation funding | aligns with accessibility/open evidence | funding may be non-recurring and donor-driven | seek a bounded funded pilot with clear maintenance ownership |
| White-label/partner delivery | SPARC engine and evidence components embedded in a partner portal | GIS/consulting/implementation partner | licensing plus implementation/support | uses established distribution and domain relationships | customization fragments contract and quality rules | test one contract-compatible integration without forking scientific semantics |

No model is recommended as “the winner” until interviews and paid behavior distinguish a software product from a service-heavy analysis workflow. Early delivery is likely to require expert review; pricing must account for that rather than pretending marginal cost is only hosting.

## 5. What SPARC must not sell

- official UN SDG scores or government certification;
- causal impact attribution from two satellite windows;
- guaranteed accuracy without an applicable validation design;
- real-time monitoring when the result is precomputed;
- water volume, groundwater, water quality or comprehensive wetland measurement from MNDWI;
- forest-loss claims from NDVI;
- air-temperature/health-exposure claims from Landsat LST;
- automated policy recommendations presented as facts; or
- redistribution rights the project does not hold.

Responsible scope is a commercial requirement. Overclaiming creates legal, reputational and decision-harm risk even if it helps a short demo.

## 6. Differentiation hypothesis

Open imagery, common indices and open-source geospatial libraries are available to others. SPARC’s defensible position, if users value it, would need to come from execution rather than data exclusivity:

- a versioned, reproducible pipeline for local boundary/period definitions;
- transparent quality and validation workflow rather than a single confidence score;
- accessible interpretation and offline delivery;
- trusted local/sector partnerships and reference evidence;
- workflow integrations, review history and repeatable update operations; and
- disciplined claim language and traceable provenance.

This differentiation is plausible but untested. A polished map alone is easy to copy.

## 7. Competitive and substitute alternatives

SPARC competes first with an existing workflow, not only with another branded dashboard:

| Alternative | What it already does well | Where the SPARC hypothesis differs | Responsible response |
|---|---|---|---|
| QGIS/GDAL/Python analyst workflow | Flexible, established geospatial processing using proven tools | SPARC may package a narrower repeatable comparison, evidence model and non-specialist delivery | Reuse these tools; do not claim SPARC replaces professional analysis |
| Bhuvan or other public geospatial portals | India-relevant thematic discovery/visualization where a dataset and its terms permit use | SPARC plans a versioned local before/after evidence pack with explicit method/quality provenance | Link/use only dataset-specific permitted material; Bhuvan-first was rejected as an unverified dependency in [ADR-001](decisions/ADR-001-data-access-strategy.md) |
| Earth Engine/custom notebook workflow | Broad catalog and scalable exploratory analysis for skilled users | SPARC’s judged path is provider-independent and offline, with a frozen public contract | Keep Earth Engine optional; do not duplicate mature processing/catalog functionality |
| JRC Global Surface Water, WorldCover and GHSL products | Authoritative global context products for their documented scope | SPARC asks a locally configured, same-method two-period question and exposes local quality limits | Use those products as attributed context/corroboration, not claim they are inferior or local ground truth |
| GIS/environmental consulting report | Expert review, customization and stakeholder interpretation | SPARC may reduce repeat setup and improve versioned evidence delivery | Expect expert review initially; test whether software reduces full-cost effort without weakening judgment |
| Internal spreadsheets, screenshots and manual briefings | Familiar, low-procurement workflow | SPARC may improve reproducibility, provenance and repeat updates | Measure actual time/error/decision value; a polished UI alone is not a reason to switch |

These comparisons are engineering/product hypotheses. No win/loss, adoption, pricing or superiority evidence has been collected.

## 8. Cost structure and operational reality

Before pricing, measure:

| Cost driver | Why it matters | P0 control | Production question |
|---|---|---|---|
| Analyst/scientist time | scene selection, QA, calibration, validation and interpretation are not free | narrow frozen pilot | how much review can be standardized without weakening quality? |
| Imagery egress/processing | open data can still have compute, transfer and storage cost | small precomputed packs and local processing | cost per district/update and provider limits? |
| Reference validation | independent imagery/field labels may dominate credible release cost | exploratory/clearly labelled status | who supplies/licences labels and what precision is required? |
| Boundary licensing/maintenance | administrative geometry changes and terms vary | verify exact source before packaging | update authority, redistribution and version synchronization? |
| Hosting/support | cloud API, incident response and user support create recurring cost | local static primary; cloud optional | required SLA, security review, peak load and retention? |
| Accessibility/localization | real public use needs more than desktop English UI | accessible P0 structure | languages, assistive-tech testing and local facilitation? |
| Liability/governance | decisions may affect communities or funding | proxy/limitation disclosure | contestability, correction process, audit record and insurance/legal review? |

Do not calculate margin until the pilot records actual person-hours, compute, storage, support and validation costs.

## 9. Expansion to districts and indicators

Adding a district is not merely adding a name. Each expansion requires a versioned/redistributable boundary, suitable same-season scenes, locally reviewed threshold behavior, validation/reference evidence, attribution, immutable outputs, offline integrity tests and a user workflow. The public v1 schema should remain stable, but the cost and scientific conclusion may differ by district.

Adding an indicator requires a defensible decision question, official product/method evidence, new method and schema metadata, units/claim boundaries, validation design, processing tests, UI interpretation, accessibility/failure states, licenses and demo assets. LST/SUHI is the first planned example; it stays P1 because it uses Landsat thermal products and separate date/rural-reference governance.

Scale in this order:

1. prove one repeatable Nagpur pack and independently gated Bengaluru recovery;
2. measure marginal analyst, validation, compute, storage, support and update cost for a third district;
3. automate only stable acquisition/packaging steps while retaining scientific release gates;
4. add object storage, PostGIS metadata or bounded workers only after concurrent demand/load requires them; and
5. localize/accessibilize with affected users rather than assuming one national interface.

## 10. Market sizing without invented numbers

Do not publish a top-down TAM based on “all districts × assumed subscription.” Instead:

1. define one buyer type and one recurring decision workflow;
2. identify the number of reachable organizations from verifiable directories;
3. interview a sample across size/maturity, including non-buyers;
4. record current spend, staff time, update frequency and procurement threshold;
5. test a concrete scope and price with a paid pilot or signed budgeted intent;
6. estimate service/validation cost per deployment; and
7. build bottom-up reachable revenue ranges with explicit assumptions and sensitivity.

Until those steps occur, the correct presentation is: “We have identified plausible buyers and experiments, not a validated market size.”

## 11. Ninety-day validation plan

### Phase 1 — problem discovery (weeks 1–3)

- Interview at least three distinct roles in each priority segment rather than only friendly technical users.
- Ask for the last real monitoring/briefing workflow, artifacts, time, pain, decision and consequence—not opinions about a hypothetical dashboard.
- Document what evidence is trusted, what triggers field verification and which claims are prohibited.
- Test whether Nagpur/Bengaluru examples resemble actual tasks without implying those regions are universal.

**Gate:** proceed only if a repeated high-cost/high-risk workflow and an accountable buyer emerge.

### Phase 2 — solution and evidence test (weeks 4–7)

- Run a task-based prototype session using a versioned, claim-safe result.
- Measure task completion, interpretation errors, time to source/limitation and questions asked.
- Compare table/static/offline and interactive-map value.
- Ask the organization to define acceptance for validation, update timing, export, security and audit.

**Gate:** users correctly interpret proxy/quality limitations and the product materially improves a real task.

### Phase 3 — paid-pilot test (weeks 8–12)

- Offer one bounded district/period deliverable with explicit exclusions and acceptance criteria.
- Request real budget, contracting owner and timeline; a free letter of interest is weak evidence.
- Record delivery hours, provider/compute cost, revision/support load and validation burden.
- Hold a post-use review on whether the evidence changed or accelerated a responsible action.

**Gate:** at least one segment shows paid intent and repeatable delivery economics without pressure to overclaim.

Numbers above are experiment design targets, not existing traction.

## 12. Pilot success metrics

| Category | Metric | Why it matters | Guardrail |
|---|---|---|---|
| Comprehension | user correctly explains proxy, period, data mode and top limitation | prevents confident misuse | never optimize completion by hiding caveats |
| Workflow | time/steps from question to reviewable evidence versus current process | tests practical value | compare equivalent quality standards |
| Follow-up | proportion of results leading to an appropriate field/expert check | tests handoff value | not “actions caused by SPARC” without study design |
| Trust | source/provenance/quality panel successfully used | tests differentiation | qualitative trust is not accuracy validation |
| Reliability | successful offline critical journeys and recovery | tests real deployment constraint | record cold starts, not only warmed demos |
| Economics | actual delivery/support/validation cost per pilot | tests sustainable price | include expert labor and licensing |
| Demand | paid pilot, renewal or budgeted procurement step | stronger than compliments | record objections and non-buyers |

## 13. Governance and ethical viability

- Results need a correction/version history and a way to contest boundary/reference interpretation.
- Communities affected by prioritization should be included in discovery and harm review.
- Avoid ranking local areas as “good/bad” when a context-dependent proxy cannot support that judgment.
- Preserve source and method evidence for audits while minimizing personal/field data collection.
- Set retention, access and redistribution rules before accepting customer-supplied reference evidence.
- Separate sales claims from validation status; scientific owners must be able to block unsupported publication.

## 14. Decision gates

- [ ] **Problem gate:** repeated real workflow and accountable buyer confirmed.
- [ ] **Evidence gate:** required accuracy/reference/claim standard is feasible and funded.
- [ ] **Usability gate:** target users interpret results and caveats correctly.
- [ ] **Reliability gate:** delivery environment and update process meet actual constraints.
- [ ] **Security/licensing gate:** procurement, data rights and secret controls are acceptable.
- [ ] **Economic gate:** paid intent and full-cost delivery support a sustainable offer.

Failing a gate should change or stop the model, not manufacture a larger market narrative.

Related documents: [technical research](research/SPARC-technical-research.md), [SRS](../SRS.md), [validation plan](validation-plan.md), [risk register](risk-register.md) and [presentation and Q&A](presentation-and-qa.md).
