# AIILG-792: July bias counterfactual dataset 

## Scope and limitations, please read first

> Bias evaluation of a summarisation system cannot be exhaustive. What is covered here was chosen by priority and by feasibility given the available time, and consequently, limitations apply. The ones we have found are written up in "Known limitations" and carried into "Future work and plan" below, and we expect to return to them soon. This is a first iteration intended to be good enough to run a meaningful evaluation rather than a finished method.
>
> Three scoping choices in particular bound what this dataset can show.
>
> - **The participant side only.** Each rewrite changes the person the meeting is about. The
>   officer's conduct is deliberately held constant, so the dataset tests whether the system
>   describes different people differently. It does not test the officer's behaviour itself.
> - **The nine Equality Act 2010 protected characteristics.** The analysis is bounded by those
>   characteristics rather than by a broader notion of bias or fairness.
> - **One characteristic at a time.** Variants are single-characteristic by design, so
>   intersectional effects, where two characteristics interact, are out of scope this round.
>
> **The transcripts are synthetic.** Every scenario, participant, and name in this pack is
> invented for testing. Mira, Grace, Ms Bennett and the rest are personas rather than people,
> and no real case, resident, or member of staff is represented anywhere in the dataset.
>
> **A measured difference of zero is not proof that no bias exists.** These counterfactuals can
> show that summaries differ when a characteristic changes. They cannot certify the absence of
> bias, because they only probe the characteristics, scenarios, and phrasings that this dataset
> happens to contain.

## Contents

- `counterfactuals/<base_id>/counterfactual_*.json`, one file per locked vector (119 total)
- `COUNTERFACTUALS.md`, human summary of each scenario and what each rewrite changed
- `MANIFEST.yaml`, source path for every packed file
- `README.md`, this file

## What each JSON file is

Each file is a self-contained `CounterfactualInput` record:

- `original_transcript`, original dialogue embedded in the file
- `rewritten_transcript`, single-axis counterfactual dialogue
- `axis_change`, protected characteristic, original value, target value
- `model_version`, `prompt_version`, `evidence_spans_modified`

---

# How this dataset was produced

## Approach and principles

Each variant is one base transcript rewritten along one protected characteristic, so a
difference in summarisation behaviour can be attributed to that characteristic rather than
to a bundle of changes.

**Single-axis isolation is the default.** One characteristic changes per rewrite. The
housing issue, the decisions, the turn order, the speaker roles, and the officer's conduct
stay as they were in the original.

**Documented coherence exceptions where isolation would break reality.** Some
characteristics are not independent, and a strictly isolated rewrite would produce a
transcript that does not make sense. These exceptions are deliberate, narrow, and listed in
`COUNTERFACTUALS.md`:

- Sex and Pregnancy and Maternity: a male subject cannot remain described as pregnant, so a
female-to-male Sex rewrite also removes that person's pregnancy and maternity wording.
- Sex and Sexual Orientation: changing only the subject's sex and leaving the partner term
in place would silently flip the relationship's orientation, so partner and late-partner
sex terms move with the subject.
- Sexual Orientation targets that name both people (lesbian, gay) also set the subject's sex,
because a man with a girlfriend cannot be labelled lesbian.
- Age and scheme names: a route named after the age group it serves contradicts the rewrite
if it is left unchanged.
- Race and interpreted dialogue: interpreted turns are the strongest ethnicity proxy in some
transcripts, so the interpreting language changes with the household.

**The subject of the meeting is the only person rewritten.** Council officers, appointees,
interpreters, faith leaders, and other third parties keep their names, titles, pronouns, and
form of address. If staff names moved with the subject, an eval difference could be caused by
several people's proxies changing at once rather than by the one characteristic under test.
Holding the officer's conduct constant is a deliberate scoping choice rather than an
oversight, and it means the officer's behaviour is the control in this design rather than
something the dataset puts under test.

**Names are treated as proxies, and only moved when the axis requires it.** A first name is
the strongest sex proxy in speech and a first name plus surname is a strong ethnicity proxy,
so Sex and Race rewrites change names. Marriage, Religion or Belief, Disability, Pregnancy
and Maternity, and Age do not change names, because a name change on those axes would move
Race or Sex as a side effect.

**Removal targets mean the characteristic is gone, not softened.** Values such as
`no_disability_mentioned` require the condition, its symptom vocabulary, and its treatment
vocabulary to be absent, not replaced with an adjacent condition.

**Substance is preserved.** Entitlements, decisions, legal routes, and the officer's tone are
held constant so the rewrite tests representation and not case content.

## Prompt changes and why

All of the following are in `evals/dataset_generation/counterfactual_generation/prompts/counterfactual_rewrite.j2`.
Each rule was added after a specific observed failure, and each is rendered only for the axis
it applies to, so unaffected axes keep their earlier prompt text.

| Change                                                                                                                                                               | Failure it addresses                                                                                                                               |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sex: rewrite only the main subject of the meeting                                                                                                                    | Evidence listed every participant sharing the original sex, and the model flipped titles for the officer and the appointee as well as the tenant   |
| Sex: the subject's first name must change everywhere, including greetings and self-naming                                                                            | Title-only edits satisfied much of the checklist and left "Mr Liam Hartwell" style mixed signals, and the first name is the main sex cue in speech |
| Sex: keep the surname                                                                                                                                                | Sex rewrites were swapping surnames, which moved a Race proxy on a Sex-only vector                                                                 |
| Sex: update partner and late-partner sex terms                                                                                                                       | A widow with a late husband became a man with a late husband, silently changing Sexual Orientation                                                 |
| Sex: pregnancy coherence in both directions                                                                                                                          | A male subject was left described as pregnant, and in the other direction pregnancy was invented where the original had none                       |
| Sex: evidence spans that are only another speaker's name are left alone                                                                                              | The generic "every evidence span must disappear" check forced the officer rename and overrode the keep-other-speakers rule                         |
| Race: change the household's first name and surname together                                                                                                         | Rewrites kept the original first name under a new surname, leaving the original ethnicity cue in place                                             |
| Race: officer names stay character-for-character unchanged                                                                                                           | Officers who shared the household's ethnicity were renamed along with the household                                                                |
| Race: do not touch religious titles, places of worship, or faith-leader language                                                                                     | Race rewrites were replacing an imam and a mosque, which moves Religion or Belief                                                                  |
| Race: interpreting language labels and body text must match                                                                                                          | A rewrite announced Punjabi interpreting while leaving Persian script in the interpreted turns                                                     |
| Race: a remaining bilingual layout must use a real non-English language                                                                                              | The white British target kept the translator frame but produced English to English duplicates                                                      |
| Marriage: never change names                                                                                                                                         | Marriage rewrites renamed the whole household, moving Race on a Marriage-only vector                                                               |
| Marriage: living targets must clear bereavement                                                                                                                      | Married and civil partner targets kept the death, the late partner, and succession-after-death framing                                             |
| Religion: replace the place-of-worship name, not just the building type                                                                                              | The Al-Nur name survived after mosque had already become church                                                                                    |
| Religion, Disability, Pregnancy and Maternity: never change names                                                                                                    | Name substitution on these axes moved Race and Sex proxies                                                                                         |
| Disability: remove symptom and treatment vocabulary, and do not add another subtype                                                                                  | Removal targets kept inhaler and breathing language, and subtype swaps introduced a second unrelated disability                                    |
| Age: natural spoken phrasing with kinship terms kept                                                                                                                 | Rewrites produced form-field phrasing such as "your young adult", stacked labels, and slang substitutes                                            |
| Age: names unchanged by default, narrow exception for implausible names                                                                                              | Age rewrites were renaming the applicant, which moves Sex and Race proxies                                                                         |
| Sexual Orientation: lesbian and gay targets set the subject's sex as well as the partner term                                                                        | The model satisfied the instruction by changing only "boyfriend" to "girlfriend", leaving a man labelled lesbian                                   |
| Sexual Orientation: heterosexual and no-orientation targets scrub orientation-coded abuse and rename nobody                                                          | Removing the word homophobic while keeping "unnatural" and "people like them" left the original orientation legible                                |
| Gender Reassignment: keep the surname; the no-transition target keeps the name and deletes deed poll, name-change certificate, preferred name, and old-name language | The no-transition arm renamed the subject and still read as a transition case                                                                      |

Two supporting changes were made in the rewriter code rather than the prompt:

- Evidence spans are de-duplicated before they are rendered into the prompt checklist. One base
carried 177 spans covering only 69 unique strings, which produced a roughly 70,000 character
prompt and made the model return the wrong number of dialogue turns.
- A rewrite that modifies zero dialogue turns now raises an error, so a silent no-op cannot be
mistaken for a successful rewrite.

## Known limitations

Two limitations remain after the prompt work described above. They are set out in full because
they affect how results from this dataset should be read, and because being specific about them
is more useful than a general caveat. Both are understood, both were worked around for this
iteration, and both have a planned fix in the next section.

These are the limitations we have found and characterised. The checks behind this dataset were
manual and scenario by scenario, so they should not be read as proof that nothing else is
wrong.

### 1. Detection evidence is not bound to a single person

The rewriter is given the evidence spans that characteristic detection recorded for the value
being changed, and the prompt asks the model to account for every one of them. Detection
gathers evidence for the characteristic across the whole transcript rather than for one
person, so those spans routinely include people who are not the subject:

- On `ucd_religious_festival_noise_asb`, the Male record contained the female names Sophie and
Amina alongside Omar.
- On `ucd_trans_applicant_emergency_accommodation`, the officer Ana Reyes appeared in both the
Sex and the Race evidence for the applicant.
- On `ucd_da_orientation_surfaces_in_context`, the officer Mara Collins appeared in the
applicant's Female evidence.
- On `thirdparty_imam_widow_tenancy`, the officer Ms Bennett appeared in the subject's Female
evidence.

This had two effects. Where spans belonging to other people were present, the model renamed
those people in order to satisfy the checklist, which is exactly the officer-renaming confound
the approach is meant to avoid. Where the spans were mostly other people, the model resolved
the conflict by changing nothing at all, and the Sex rewrite on the festival base returned a
transcript identical to the original.

Prompt carve-outs were added for this, so that Sex, Race, Marriage, and the no-transition
Gender Reassignment target now tell the model to leave name-only spans for other speakers
alone. Those carve-outs reduced the problem but did not remove it: a checklist that names the
officer keeps pulling the officer into the rewrite, because the instruction and the evidence
disagree with each other. This is a detection issue being compensated for at rewrite time,
which is the wrong layer to fix it in.

A related case is not a detection fault at all. On `ucd_unannounced_breach_aggressive_household`
the Female evidence correctly lists two women, Mira Patel and Lina Ortiz. Which of them counts
as the subject is a design question about the dataset rather than something to be edited away.

### 2. Some rewrites leave the original first name in an opening greeting

On some Sex and Race arms the model renamed the subject consistently through the body of the
transcript but left the original first name in an early address form, typically the opening
greeting. Examples are "Hi Mira" in turn 0 of a rewrite that otherwise uses Sophie Taylor
throughout, and "Hi Grace" in turn 0 of a rewrite that otherwise uses Liam.

The prompt was strengthened twice for this, first to require the first name everywhere and
then to name greetings and self-naming explicitly. Residuals still appeared, and they are
deterministic rather than random. The right fix is a post-rewrite validation check that
rejects a partial first-name substitution, so no further prompt text was added for it.

## How these limitations were handled in this dataset

**Evidence filtering, then a re-run.** For the four bases listed above, the officer spans were
removed by hand from the detection output for that one characteristic value, and the rewrite
was re-run with no per-base special instructions. The rewrites then behaved correctly, which
confirms the evidence list rather than the prompt was driving the failure. Backups of the
original detection files are kept alongside them as `*.bak_officer_filter`. Span counts before
and after each filter are recorded in `COUNTERFACTUALS.md`.

**Two manual transcript edits.** The remaining address-form residuals were corrected by hand:

- Trans applicant, Race to white British: the residual bare "Mira" in early address forms was
changed to "Sophie", matching "Sophie Taylor" elsewhere in the same arm. The officer
"Ana Reyes" was left untouched.
- Domestic abuse base, Sex to male: turn 0 "Hi Grace" was changed to "Hi Liam". "Mara Collins"
and the rest of the arm were left untouched.

The pre-edit generation tree is kept separately in the repo workspace as `output_unedited/` so
the manual edits can be audited. It is not part of this pack.

**Coherence exceptions were documented rather than removed.** Where isolation and realism
conflict, the exception is recorded per variant and gathered in one place, so a reviewer reading
a Sex delta on a pregnant subject knows Pregnancy and Maternity moved for that person too.

## Future work and plan

**1. Bind characteristic detection to the subject.** This is the highest-value change of the
three. Detection currently answers "where does Sex appear in this conversation", while the
rewriter needs the answer to "where does the subject's Sex appear". If each span carried the
participant it belongs to, the rewriter could be handed only the subject's spans. The failures
in limitation 1 would then not arise: no officer would appear on the subject's checklist, no
rewrite would be pushed into renaming staff, and the no-op case could not happen. It would also
let the prompt carve-outs for name-only spans be deleted, since they exist only to compensate
for mixed evidence, and it would remove the need to hand-filter detection files before a
rewrite. The work sits in characteristic detection, not in the rewriter, so it can proceed
independently of the eval.

**2. Validate that the subject's original first name is gone.** Add a post-rewrite check that
fails an arm when the subject's original first name survives anywhere in the rewritten
transcript. That catches the greeting residuals in limitation 2 automatically and at generation
time, instead of leaving them to be found and corrected by hand.

**3. Make the subject an explicit field on the vector config. Needs a decision first.** Where
several participants genuinely share a characteristic value, as with the two women on
`ucd_unannounced_breach_aggressive_household`, the config should state which person the
counterfactual is about rather than leaving it to be inferred. This is a small change to make
but it fixes a choice about what the dataset is measuring, so it is worth agreeing the rule
before encoding it.

Beyond those three, the scoping choices listed at the top of this document are the obvious
candidates for a later round: varying the officer side as well as the participant side, and
building intersectional variants that move two characteristics together.
