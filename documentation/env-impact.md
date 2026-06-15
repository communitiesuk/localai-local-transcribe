# Environmental Impact Assessment

## 1. Overview

The environmental impact of the system is multifaceted and arises from three primary areas:

1. Non-AI infrastructure components (including audio processing)
2. Transcription services
3. Large Language Model (LLM) inference workloads

This assessment focuses on **operational energy use and associated CO₂-equivalent emissions**. Hardware manufacturing, data centre construction, and end-user device impacts are out of scope.

---

## 2. Non-AI Components

The non-AI part of the system handles everything that doesn't involve AI: receiving audio uploads, converting them to a consistent format, routing jobs between services, storing results, and serving the web interface. This layer is entirely deterministic — it performs the same predictable work every time, and its energy use scales linearly with the number of meetings processed.

### 2.1 Infrastructure components

The non-AI infrastructure consists of worker processes, back-end services, front-end applications, databases (RDS), queues, load balancers, and S3 storage. Audio processing uses FFmpeg to convert uploads to mono MP3 at 192k bitrate before transcription; files already in the target format skip conversion. All of this runs on AWS and is captured in the measured monthly emissions reported in Section 2.2.

The primary environmental lever for this layer is infrastructure placement: selecting regions with lower grid carbon intensity and providers with transparent sustainability reporting. AWS publishes market-based (MBM) figures that account for its renewable energy certificate purchases, making its reported footprint lower than a raw grid-average calculation would suggest.

### 2.2 Measured AWS Infrastructure Carbon Footprint

The AWS Sustainability API provides vendor-measured estimates of the carbon footprint of all AWS services consumed by the account each month. This covers the infrastructure described in Section 2.1 — EC2 worker instances, RDS databases, S3 storage, ALBs, audio processing, and supporting services.

> **Scope boundary:** This figure covers only AWS-hosted infrastructure. The AI workloads described in Section 3 — Azure Speech-to-Text transcription and OpenAI/Azure LLM inference — are operated by their respective providers and are **not reflected** in the AWS figures below. The figures here represent the non-AI "back-end" footprint only.

#### April 2026 (most recent complete month)

| Method | MTCO2e | kg CO₂e | g CO₂e |
|--------|-------:|--------:|-------:|
| Location-based (LBM) | 0.064309 | 64.3 | 64,309 |
| Market-based   (MBM) | 0.017317 | 17.3 | 17,317 |

AWS model version: v3.0.1

**MBM** (market-based method) subtracts renewable energy certificates (RECs) purchased by AWS; it is the appropriate figure when comparing against a provider that actively purchases clean energy, as AWS does.  
**LBM** (location-based method) uses regional grid-average carbon intensity and is shown for reference only.

**Homeworking context:** At the UK GHG Conversion Factors 2025 homeworking rate (0.334 kg CO₂e/FTE hour [24]), 17,317 g CO₂e (MBM) is equivalent to **51.9 hours (6.5 working days)** of one person working from home. See Appendix HW. Run `documentation/env_assets/aws_carbon.py` to recompute for the latest month.

---

## 3. AI and ML Services Impact

The AI layer is where most of the variable energy cost arises. Two model tiers are used: a lightweight **FAST** model (GPT-5-nano) for lower-complexity or speed-sensitive steps, and a more capable **BEST** model (GPT-5.1) for tasks requiring richer reasoning or higher output quality.

Processing a single meeting involves multiple sequential AI calls, not one. Summarisation is broken into stages — identifying the meeting structure, drafting each section, extracting action items — and some stages run in parallel, with separate model calls handling different parts of the transcript at the same time. The total AI cost of one meeting is therefore the sum of all individual model invocations across both tiers.

Transcription is handled separately by a dedicated speech-to-text service (Azure Speech), which runs independently of the LLM pipeline.

### 3.1 Service categories

**Transcription services (ASR)**
Peer-reviewed measurements indicate that cloud-based ASR systems exhibit relatively low energy use and CO₂e per hour of audio, particularly when operated in modern data centres [15].

**Large Language Model services**
LLM inference represents a substantial increase in energy consumption compared to traditional web services. EcoLogits [25] modelling of a typical 500-word-output invocation on the BEST model (GPT-5.1) estimates 1.4–2.1 Wh — roughly 5–7× a comparable Google search (0.3 Wh) [2]. The FAST model (GPT-5-nano) is an order of magnitude cheaper per invocation (0.1 Wh for the same output length).

LLM usage is expected to materially increase the environmental footprint of the overall solution. The computational intensity stems from the massive matrix multiplication operations required during autoregressive token generation.

---

## 4. Water Usage Considerations

### 4.1 Context and scale

Water consumption in data centres is driven primarily by cooling system design. Evaporative cooling is the dominant source of consumptive water use, while dry or closed-loop systems can substantially reduce or eliminate it [1], [6].

In the UK, 51% of data centres use waterless cooling, 44% use hybrid systems, and only 5% use water-based cooling exclusively [6]. Among those that do use water, consumption is relatively modest: 64% use less than 10 million litres per year (approximately equivalent to 200 people) [6].

At continental scale, data centres do not represent a major water-consuming sector compared to agriculture and heavy industry [4], [6]. However, 32% of the European population lives in water-stressed areas [5], and England faces a projected 5 billion litre public water shortage by 2055 [3].

### 4.2 Water cycle and local impact

Most data centre water use is non-consumptive—water is returned to the source or hydrologic system shortly after withdrawal, with minimal atmospheric loss and minimal chemical contamination compared to other industrial uses [7], [4].

**The primary concern is placement**: locating high water-use data centres in water-stressed regions compounds existing problems [3], [5]. Water impact is **local and contextual**, not permanent loss.

**Note:** Hardware manufacturing for AI infrastructure requires water in the production process [1], which is not accounted for in this report.

### 4.3 Recommendation

**Infrastructure provider selection should consider water ethics.** Organisations should evaluate whether their cloud providers operate data centres in water-stressed regions and prioritise providers with transparent water usage reporting and responsible placement strategies.

---

## 5. Quantitative Impact for a 1-Hour Meeting

### 5.1 Key Assumptions

* Transcript length: **X = 9,000 words** (1-hour meeting baseline)
* Token conversion: **2 tokens per word**
* ASR and LLM inference run on UK infrastructure
* Carbon intensity (inference): **GBR = 217 g CO₂e/kWh** [25]
* Carbon intensity (training): **US average = 384 g CO₂e/kWh** [25]
* ASR emissions from academic measurements [15]
* LLM inference energy from EcoLogits [25] LCA regression model (Appendix E)
* GPT-5.x training costs are not publicly available
* GPT-4 training cost is a close enough order-of-magnitude proxy for GPT-5.1 (BEST)
* GPT-4o training cost is a close enough order-of-magnitude proxy for GPT-5-nano (FAST)
* LLM training energy from academic papers [11]
* Models used are the actual production deployments (see Appendix A)
* Token usage formulas assume optimal AI behaviour (no retries/failures)

**See Appendix B.1 for detailed parameters, assumptions, and important limitations.**

### 5.2 Confidence Level

These estimates are **order-of-magnitude approximations** suitable for comparative analysis and strategic decision-making, not precise carbon accounting. Actual values may vary significantly based on speaking pace, model selection, geographic location, and operational conditions.

---

## 6. Transcription Impact (1 Hour)

From the ASR study [15], using Whisper as a proxy (similar open-source ASR system):

**Energy:**
* Average: 0.49 kWh for 22 hours of processing
* Per hour: 0.49 ÷ 22 ≈ **22.3 Wh (0.0223 kWh)**

**CO₂e:**
* 22.3 Wh × 217 g/kWh (GBR [25]) ≈ **4.8 g CO₂e**

**Note:** The study also reported a CO₂e figure derived from its own measurements (17.3 g/hour, implying 776 g/kWh carbon intensity). This is far above the GBR grid average and inconsistent with our assumptions, so it is discarded in favour of applying GBR intensity to the measured energy.

**Summary**

| Metric |      Value |
| ------ | ---------: |
| Energy | 22 Wh (0.022 kWh) |
| CO₂e   |  4.8 g |

---

## 7. LLM Processing Impact

### 7.1 Template Comparison (X = 9,000 words, 1-hour baseline)

Token usage formulas and per-invocation breakdowns are in Appendix B.

Energy is computed per API invocation via EcoLogits [25]; ranges reflect GPT-5-nano and GPT-5.1 architecture uncertainty. Output tokens only (input/prefill modelled via per-call TTFT). CO₂e derived as energy × 217 g CO₂e/kWh (GBR).

| Template | Invocations | Output Tokens | LLM Energy | LLM CO₂e |
|----------|-------------|---------------|------------|----------|
| Basic Minutes | 4 | 5,660 | 0.3–0.4 Wh | 0.1 g |
| Short 'n' Sweet | 4 | 5,660 | 7.4–11.0 Wh | 1.6–2.4 g |
| SectionTemplate (Y=6) | 17 | 12,964 | 9.0–13.3 Wh | 2.0–2.9 g |
| Delivery | 6 | 16,160 | 10.3–15.3 Wh | 2.2–3.3 g |
| UserTemplate DOCUMENT | 4 | 9,260 | 12.1–18.1 Wh | 2.6–3.9 g |
| SimpleTemplate | 6 | 20,060 | 12.7–18.8 Wh | 2.8–4.1 g |

The dominant cost driver is the **BEST model (GPT-5.1 MoE)**. Templates that use only the FAST model (GPT-5-nano) — Basic Minutes — are 30–40× cheaper than BEST-model templates because GPT-5-nano operates at 96 tokens/second versus GPT-5.1 at 61 tokens/second, and its active parameter footprint is an order of magnitude smaller. The citations pipeline (extract_claims + cite_claims) adds 10,800 output tokens and distinguishes SimpleTemplate from Short 'n' Sweet (1.2–1.7 g CO₂e extra). Detailed usage-frequency breakdown is in Appendix F.2.

---

## 8. Combined Impact per 1-Hour Meeting

All figures use GBR grid intensity (217 g CO₂e/kWh) [25] applied to measured or modelled energy — consistent with Section 6 and Section 7.

### 8.1 Usage-Weighted Average

Applying production usage shares (Appendix F.1):

| Component | Energy | CO₂e | % of Total |
|-----------|--------|------|-----------|
| Transcription (GBR) | 22.3 Wh (0.022 kWh) | 4.8 g | 61% |
| LLM processing (GBR, midpoint) | 14.2 Wh (0.014 kWh) | 3.1 g | 39% |
| **Usage-weighted total** | **33.6–39.1 Wh (0.034–0.039 kWh)** | **7.3–8.5 g** | **100%** |

### 8.2 Range by Template

| Template | Total Energy | Total CO₂e | ASR % | LLM % |
|----------|-------------|------------|-------|-------|
| Basic Minutes | 22.6–22.7 Wh | 4.9 g | 98.3% | 1.7% |
| Short 'n' Sweet | 29.6–33.3 Wh | 6.4–7.2 g | 70.8% | 29.2% |
| SectionTemplate (Y=6) | 31.3–35.5 Wh | 6.8–7.7 g | 66.6% | 33.4% |
| Delivery | 32.6–37.5 Wh | 7.1–8.2 g | 63.5% | 36.5% |
| UserTemplate DOCUMENT | 34.4–40.4 Wh | 7.5–8.8 g | 59.6% | 40.4% |
| SimpleTemplate | 35.0–41.1 Wh | 7.6–8.9 g | 58.5% | 41.5% |

---

## 9. Interpretation

**Usage-weighted impact:** A typical 1-hour meeting (weighted by production template usage) produces **7.3–8.5 g CO₂e** (midpoint 7.9 g) and consumes **33.6–39.1 Wh (0.034–0.039 kWh)**. Transcription (ASR) contributes approximately **61%** of combined CO₂e, with LLM at **39%** — because GPT-5-nano's high throughput (96 tokens/s) and GPT-5.1's competitive efficiency make the LLM cost much lower than previous-generation models.

**Template variation:** The range across production templates is **4.9–8.9 g CO₂e** total combined — a 1.8× spread. The crucial differentiator is whether a BEST model invocation (GPT-5.1) is present: Basic Minutes is FAST-only and sits at a near-negligible 0.1 g LLM CO₂e, while every template using GPT-5.1 clusters in the 1.6–4.1 g LLM range. Within the BEST-using templates, the citations pipeline (extract_claims + cite_claims) adds 10,800 output tokens and 1.2–1.7 g CO₂e — the primary differentiator between SimpleTemplate and Short 'n' Sweet.

**Transcription is a fixed cost:** The 22.3 Wh transcription cost is identical regardless of template. LLM's share of total CO₂e ranges from 1% (Basic Minutes) to 37% (SimpleTemplate), with ASR dominating at all template levels.

**Infrastructure vs. AI processing cost:** The AWS hosting layer (Section 2.2) emitted **17,317 g CO₂e (MBM)** in April 2026 — equivalent to the AI processing cost of approximately **2,192 complete 1-hour meetings** (at the usage-weighted midpoint of 7.9 g CO₂e/meeting). The two figures cover different layers: non-AI hosting (AWS) vs. transcription and LLM inference (Azure). Together they represent the full system footprint; the infrastructure layer now dominates AI inference cost by a large margin. Run `documentation/env_assets/aws_carbon.py` to recompute against the latest month.

**Homeworking context:** The usage-weighted per-meeting AI cost (7.9 g CO₂e midpoint) is equivalent to **85 seconds (1.5 minutes)** of a single person working from home, using the UK GHG Conversion Factors 2025 homeworking rate of 0.334 kg CO₂e/FTE hour [24]. By contrast, one month of AWS hosting (April 2026: 17.3 kg CO₂e MBM) equates to approximately **51.9 hours (6.5 working days)** of homeworking. Reducing infrastructure waste (idle resources, over-provisioned instances) therefore yields orders of magnitude more carbon savings than optimising AI prompt length or model selection. See Appendix HW.

---

## 10. AI Model Training Impact

Model training represents a substantial one-time energy investment amortised across all users. Following the Final Discovery Report methodology, we distribute training costs equally across all users on a subscription basis. Training emissions are one-time costs, unlike inference costs which recur with each use.

This system uses two types of AI models: Large Language Models (LLMs) for summarisation and Speech-to-Text (ASR) models for transcription. Both contribute to the overall training footprint.

### 10.1 Per-User Training Impact

**LLM models:** This system uses GPT-5-nano (FAST pathway) and GPT-5.1 (BEST pathway). Training energy for these models is not publicly available. As order-of-magnitude proxies we use GPT-4 (57,000 MWh [11]) for the BEST pathway and GPT-4o (1,151 MWh [11] [12]) for the FAST pathway, based on architectural similarity of class. GPT-4 is a large model (1.76 trillion parameters); GPT-4o is a smaller, more efficient model (200 billion parameters) using Gopher as a training proxy. These are likely underestimates for GPT-5.x, but provide the best available order-of-magnitude reference. Training costs are amortised across 800 million weekly active users [13].

**ASR models:** Using OWSM v3 as a proxy for Whisper-style ASR models, training energy is estimated at 7.4 MWh [19]. Training costs are amortised across 300 million Microsoft Teams monthly active users [23].

**Per-user training impacts:**

| Model | Training Energy | Per-User Energy | Per-User CO₂e |
|-------|----------------|-----------------|---------------|
| GPT-4 (proxy for GPT-5.1 class) | 57,000 MWh | 71 Wh (0.071 kWh) | 27.4 g |
| GPT-4o (proxy for GPT-5-nano class) | 1,151 MWh | 1.4 Wh (0.0014 kWh) | 0.553 g |
| ASR (OWSM v3 proxy) | 7.4 MWh | 0.025 Wh (0.000025 kWh) | 0.0095 g |
| **System Total** | - | **72.7 Wh (0.073 kWh)** | **28.0 g** |

*ASR training represents only 0.034% of combined training impact and is negligible.*
*Training figures are proxies — actual GPT-5.x training costs are not publicly available.*

*See Appendices C and D for detailed calculation methodology and data sources.*

### 10.2 Training vs. Inference Comparison

**Combined training impact (both models, proxy):** 72.7 Wh (0.073 kWh), 28.0 g CO₂e per user

**1-hour SimpleTemplate meeting:** 35.0–41.1 Wh (0.035–0.041 kWh), 7.6–8.9 g CO₂e (midpoint 8.2 g)

**Key finding:** Processing a single 1-hour meeting with SimpleTemplate consumes **0.52× the combined training cost** amortised per user (proxy). This means the per-user training investment exceeds the cost of a single meeting:
* The amortised training proxy is 1.9× the per-meeting inference cost (28.0 g ÷ 8.2 g midpoint ≈ 3.4×; energy: 72.7 ÷ 38.1 Wh = 1.9×)
* Inference costs accumulate with each use — after processing about 2 meetings, cumulative inference exceeds the user's share of training costs
* The training proxy figures (GPT-4/GPT-4o) likely underestimate actual GPT-5.x training costs, making this ratio even more favourable to inference

**Limitations:** Equal-distribution approach does not reflect actual usage patterns but provides a tractable baseline. Training estimates are proxies based on similar-class models; actual GPT-5.x training costs are not publicly available. With 800 million users, training costs are well-amortised; smaller user bases would see proportionally higher per-user impact.
* Actual training may have included multiple runs, failed attempts, or iterative improvements not captured in published estimates
* The GPT-4o estimate uses Gopher as a proxy due to similar parameter counts, but architectural differences may affect actual training costs

**Carbon intensity for training:**

Training calculations use US average carbon intensity (384 g CO₂e/kWh) from EcoLogits [25] ElectricityMixRepository (zone='USA'), as most large-scale AI training is conducted in US data centres. This is significantly higher than the GBR average (217 g CO₂e/kWh) used for both ASR and LLM inference, reflecting the carbon-intensive nature of US electricity generation.

**Scope boundaries:**

This analysis includes only the energy consumed during the final training run(s) that produced the deployed models. It excludes:
* Research and development iterations
* Preliminary experiments and ablation studies
* Infrastructure manufacturing and deployment
* Ongoing fine-tuning and model updates

For comprehensive lifecycle assessment, these additional factors would need to be considered, potentially increasing training impact estimates by a factor of 2-10×.

---

# Appendix A: Model Selection

This assessment uses the models actually deployed in production:

* **FAST pathway**: GPT-5-nano — dense architecture, 5–18.5 B parameters, 96.1 tok/s, TTFT 2.29 s
* **BEST pathway**: GPT-5.1 — MoE architecture, 300 B total / 30–90 B active, 60.6 tok/s, TTFT 1.85 s

Model parameters are taken from the EcoLogits [25] ModelRepository. The min–max ranges in all results reflect architecture uncertainty in the active parameter count (particularly for MoE models where the fraction of parameters activated per token is not publicly confirmed). Actual emissions will vary with prompt structure, caching, and batching behaviour.

---

# Appendix B: System Token Usage Analysis

This appendix documents all LLM invocations in the Minute system with per-invocation token estimates and source file references.

## B.1 Parameters and Assumptions

### Parameters

* **X** = words in meeting transcript (9,000 words baseline for 1-hour meeting)
* **Y** = number of sections (SectionTemplate only, typically 6)
* **Q** = number of questions (UserTemplate FORM type)

### Token Conversion Assumptions

* **2 tokens per word** (conservative estimate for English text)
* **Transcript length (X)**: 7,500-9,000 words for 1-hour meeting, based on typical conversation speed
* Actual transcripts may vary significantly (5,000-15,000 words/hour) depending on speaking pace, silences, and meeting dynamics
* Different models use different tokenization schemes; actual token counts will vary

### Key Assumptions

* SimpleTemplate and SectionTemplate are mutually exclusive per meeting
* Hallucination checks follow their corresponding LLM invocations when enabled (assumed on)
* Citations added only when `citations_required = True` (assumed on)
* Formulas assume optimal AI behaviour (no retries, failures, or regenerations)
* Retry logic with exponential backoff (max 6 attempts) not counted in estimates
* Formulas based on rough estimates of AI behaviour and assume non-reasoning models

### Energy Methodology

* **ASR**: Energy scales linearly with audio duration (reasonable for transcription services)
* **LLMs**: Energy is estimated via EcoLogits [25] LCA regression model. Each API invocation is modelled individually; EcoLogits uses active parameter count, output token count, deployment TPS, and TTFT to estimate server runtime, then multiplies by datacenter PUE and electricity mix. Only output tokens drive the generation formula; input/prefill overhead is captured via the per-call TTFT. Results are min–max ranges reflecting architecture uncertainty in model parameter counts.
* Estimates represent order-of-magnitude accuracy; actual values vary with batching, caching, and hardware utilisation.

### Geographic Scope and Carbon Intensity

* **ASR inference**: GBR grid (217 g CO₂e/kWh, EcoLogits [25] ElectricityMixRepository) — transcription runs on UK infrastructure
* **LLM inference**: GBR grid (217 g CO₂e/kWh) — EcoLogits [25] uses UK (GBR) grid parameters for the energy calculation; CO₂e derived as energy × 217 g/kWh
* **Training**: US average (384 g CO₂e/kWh, EcoLogits [25] ElectricityMixRepository, zone='USA') as most large-scale AI training occurs in US data centres
* Actual carbon intensity varies significantly by region, provider, and time of day
* Organisations in different regions will see proportionally different CO₂e impacts
* Relative energy consumption patterns remain valid regardless of location

### Training Impact Methodology

* Training costs distributed equally across all users (subscription basis approach)
* This equal-distribution method is not representative of actual usage patterns but provides tractable estimation framework
* Training is one-time cost amortised over model lifetime, unlike recurring inference costs
* User base estimates based on peak active users and may underestimate total lifetime users

### Scope Limitations

* **Included**: Operational inference and training energy
* **Excluded**:
  * Data collection and experimentation (FacebookAI reported 31% of lifetime ML power use [18])
  * Experiments (FacebookAI reported 10% of lifetime ML power use [18])
  * Model development iterations, infrastructure manufacturing, ongoing fine-tuning
  * Hardware manufacturing emissions for training infrastructure
  * LLM usage for evaluation and template creation (small one-time cost during system setup)
* For comprehensive lifecycle assessment, excluded factors could increase estimates by 2-10×

### Research Quality Considerations

Primary studies [11], [15] represent the best available independent research but have limitations:
* The field is still in its infancy; peer-reviewed energy studies from top venues are rare
* Methodologies are sound with no major red flags identified
* AI company self-reported figures avoided due to falsification incentives and precedence for underreporting [16], [17]
* EcoLogits is an open-source LCA regression model (not empirical measurement); its estimates were cross-validated against Jegham et al. [1] for GPT-4o and GPT-4 Turbo — both approaches gave similar results, providing confidence in the methodology for newer models
* As more rigorous independent research emerges, these estimates should be updated

### Model Definitions

* **FAST**: GPT-5-nano (configured via `FAST_LLM_PROVIDER` and `FAST_LLM_MODEL_NAME`)
* **BEST**: GPT-5.1 (configured via `BEST_LLM_PROVIDER` and `BEST_LLM_MODEL_NAME`)

## B.2 SimpleTemplate Templates

**Templates**: General, ExecutiveSummary, CareAssessmentV2  
**Source**: `common/templates/types.py:92-103`  
**Total invocations**: 6

| # | Invocation      | Model | File Reference | Input (words) | Output (words) |
| - | --------------- | ----- | -------------- | ------------: | -------------: |
| 1 | Speaker ID     | FAST  | `common/audio/generate_speaker_predictions.py` | 110 + X | 40 |
| 2 | Title          | FAST  | `common/generate_meeting_title.py` | 12 + X | 10 |
| 3 | Minutes        | BEST  | `common/templates/types.py:96-97` | 345 + X | 0.5X |
| 4 | Hallucination  | BEST  | `common/templates/types.py:98` | 17 | 80 |
| 5 | extract_claims | FAST  | `common/templates/citations.py` | 336 + 0.5X | 0.1X |
| 6 | cite_claims    | FAST  | `common/templates/citations.py` | 235 + 1.7X | 0.5X |

**Totals (words):**
* FAST: 693 + 4.2X input, 50 + 0.6X output
* BEST: 362 + X input, 80 + 0.5X output

## B.2a Short 'n' Sweet (ExecutiveSummary) — SimpleTemplate without citations

**Template**: Short 'n' Sweet  
**Source**: `common/templates/default/executive_summary.py`  
**Total invocations**: 4 (`citations_required = False` — invocations 5 and 6 skipped)

| # | Invocation      | Model | File Reference | Input (words) | Output (words) |
| - | --------------- | ----- | -------------- | ------------: | -------------: |
| 1 | Speaker ID    | FAST  | `common/audio/generate_speaker_predictions.py` | 110 + X | 40 |
| 2 | Title         | FAST  | `common/generate_meeting_title.py` | 12 + X | 10 |
| 3 | Minutes       | BEST  | `common/templates/default/template_prompts/executive_summary.j2` | 134 + X | 0.3X |
| 4 | Hallucination | BEST  | `common/templates/types.py:98` | 17 | 80 |

*Invocation 3 uses `executive_summary.j2` (129w system prompt, not `general.j2`). Output is 0.3X — a concise summary rather than full minutes.*

**Totals (words):**
* FAST: 122 + 2X input, 50 output
* BEST: 151 + X input, 80 + 0.3X output

**Output tokens at X = 9,000 (EcoLogits charges output only):**
* GPT-5-nano (FAST): 100 tokens (speaker 80 + title 20)
* GPT-5.1 (BEST): 5,560 tokens (minutes 5,400 + hallucination 160)
* Total output: 5,660 tokens

**Energy (EcoLogits, per-invocation, UK GBR grid):** **7.4–11.0 Wh**

**CO₂e (energy × GBR 217 g/kWh):** **1.6–2.4 g**

## B.3 SectionTemplate Templates

**Templates**: Cabinet, PlanningCommittee  
**Source**: `common/templates/types.py:163-196`  
**Total invocations**: 5 + 2Y

| # | Invocation           | Model | File Reference | Input (words) | Output (words) |
| - | -------------------- | ----- | -------------- | ------------: | -------------: |
| 1  | Speaker ID                     | FAST | `common/audio/generate_speaker_predictions.py` | 110 + X | 40 |
| 2  | Title                          | FAST | `common/generate_meeting_title.py` | 12 + X | 10 |
| 3  | Section detection              | FAST | `common/templates/types.py` | 74 + X | 2Y |
| 4a | First section                  | BEST | `common/templates/types.py:176-181` | 345 + 15 | 0.3X/Y |
| 4b | Each section k (×Y-1)          | BEST | `common/templates/types.py:185-186` | grows with history† | 0.3X/Y |
| 5  | Hallucination (×Y)             | BEST | `common/templates/types.py:183,187` | 17 | 80 |
| 6  | extract_claims                 | FAST | `common/templates/citations.py` | 336 + 0.3X | 0.06X |
| 7  | cite_claims                    | FAST | `common/templates/citations.py` | 235 + 1.46X | 0.3X |

*†Section k input = system (345w) + k×15w + (k−1)×0.3X/Y (prior section output). Context window grows by 15 + 0.3X/Y per iteration.*

**Totals (words):**
* FAST: 767 + 4.76X input, 50 + 2Y + 0.36X output
* BEST section calls: Y×345 + 7.5Y(Y+1) + 0.15X(Y−1) input, 0.3X output (context accumulates)
* BEST hallucination (×Y): 17Y input, 80Y output

## B.4 Delivery Template

**Source**: `common/templates/default/delivery.py:73-107`  
**Total invocations**: 6 (4 FAST + 2 BEST)

| # | Invocation                    | Model | File Reference | Input (words) | Output (words) |
| - | ----------------------------- | ----- | -------------- | ------------: | -------------: |
| 1 | Speaker ID                    | FAST  | `common/audio/generate_speaker_predictions.py` | 110 + X | 40 |
| 2 | Title                         | FAST  | `common/generate_meeting_title.py` | 12 + X | 10 |
| 3 | Sections + Actions + Attendees | BEST  | `common/templates/default/delivery.py:81-86` | 199 + X | 0.4X + 30 |
| 4 | Hallucination                 | BEST  | `common/templates/default/delivery.py:84` | 17 | 80 |
| 5 | extract_claims                | FAST  | `common/templates/citations.py` | 336 + 0.4X | 0.08X |
| 6 | cite_claims                   | FAST  | `common/templates/citations.py` | 235 + 1.58X | 0.4X |

**Totals (words):**
* FAST: 693 + 3.98X input, 50 + 0.48X output
* BEST: 216 + X input, 110 + 0.4X output

## B.5 Basic Minutes (Fallback)

**Source**: `common/services/minute_handler_service.py:221-228`  
**Total invocations**: 4

| # | Invocation      | Model | File Reference | Input (words) | Output (words) |
| - | --------------- | ----- | -------------- | ------------: | -------------: |
| 1 | Speaker ID    | FAST  | `common/audio/generate_speaker_predictions.py` | 110 + X | 40 |
| 2 | Title         | FAST  | `common/generate_meeting_title.py` | 12 + X | 10 |
| 3 | Basic summary | FAST  | `common/services/minute_handler_service.py:225-226` | 12 + X | 0.3X |
| 4 | Hallucination | FAST  | `common/services/minute_handler_service.py:227` | 17 | 80 |

**Totals (words):**
* FAST only: 151 + 3X input, 130 + 0.3X output

## B.6 Additional Template Types

### B.6.1 UserTemplate (DOCUMENT type)

**Source**: `common/templates/user_template.py:73-90`  
**Total invocations**: 4 (2 FAST + 2 BEST)

| # | Invocation      | Model | File Reference | Input (words) | Output (words) |
| - | --------------- | ----- | -------------- | ------------: | -------------: |
| 1 | Speaker ID    | FAST  | `common/audio/generate_speaker_predictions.py` | 110 + X | 40 |
| 2 | Title         | FAST  | `common/generate_meeting_title.py` | 12 + X | 10 |
| 3 | Document gen  | BEST  | `common/templates/user_template.py:80-88` | 327 + X | 0.5X |
| 4 | Hallucination | BEST  | `common/templates/user_template.py:89` | 17 | 80 |

*Invocation 3 system prompt = `document_prompt` fixed text (115w) + user-defined template content (200w assumed) + date string (7w) = 322w. Plus transcript wrapper (5w) = 327w input. Actual values vary with template length.*

**Totals (words):**
* FAST: 122 + 2X input, 50 output
* BEST: 344 + X input, 80 + 0.5X output

**Output tokens at X = 9,000 (EcoLogits charges output only):**
* GPT-5-nano (FAST): 100 tokens (speaker 80 + title 20)
* GPT-5.1 (BEST): 9,160 tokens (doc gen 9,000 + hallucination 160)
* Total output: 9,260 tokens

**Energy (EcoLogits, per-invocation, UK GBR grid):** **12.1–18.1 Wh**

**CO₂e (energy × GBR 217 g/kWh):** **2.6–3.9 g**

### B.6.2 UserTemplate (FORM type)

**Total invocations**: Q (FAST only, where Q = number of questions per form)

Each question is answered independently with a FAST invocation that receives the full transcript and all previously answered questions as context.

### B.6.3 AI Edit

**Total invocations**: 2 per edit (all FAST)

### B.6.4 Chat / Interactive Message

**Total invocations**: 1 per message (FAST)

B.6.2–B.6.4 represent specialised workflows. UserTemplate FORM, AI Edit, and Chat are FAST-only and therefore substantially lower-impact than the BEST-model invocations that dominate B.6.1.

---

# Appendix C: Training Impact Calculation Details

## C.1 Data Sources and Assumptions

**GPT-4 Training Energy:**
* Source: Ji, Z. & Jiang, M. "A systematic review of electricity demand for large language models" [11]
* Estimated range: 52,000-62,000 MWh
* Midpoint used: 57,000 MWh (57,000,000 kWh)
* Uncertainty: ±5,000 MWh (±9%)

**GPT-4o Training Energy:**
* Parameter count: 200 billion [12]
* Proxy model: DeepMind Gopher (280 billion parameters)
* Training energy from [11]: 1,151 MWh (1,151,000 kWh)
* Scaling assumption: Linear relationship between parameters and training energy at this scale

**User Base:**
* Source: TechCrunch reporting on OpenAI announcements [13]
* Weekly active users at peak: 800 million
* Assumption: Peak weekly active users represents the relevant amortization base
* Note: This likely underestimates total lifetime users but provides a conservative estimate

**Carbon Intensity:**
* US average: 384 g CO₂e/kWh (EcoLogits [25] ElectricityMixRepository, zone='USA')
* Note: Training calculations use US carbon intensity as most large-scale AI training occurs in US data centres
* This is significantly higher than the GBR average (217 g CO₂e/kWh) used for both ASR and LLM inference, reflecting the carbon-intensive nature of US electricity generation

## C.2 Calculation Methodology

**GPT-4 per-user calculations:**

```
Training energy total: 57,000,000 kWh
User base: 800,000,000 users
Energy per user = 57,000,000 ÷ 800,000,000 = 71.25 Wh (0.07125 kWh)
CO₂e per user = 71.25 Wh × 384.40 g/kWh / 1000 = 27.39 g ≈ 27.4 g
```

**GPT-4o per-user calculations:**

```
Training energy total: 1,151,000 kWh
User base: 800,000,000 users
Energy per user = 1,151,000 ÷ 800,000,000 = 1.4387 Wh (0.0014387 kWh)
CO₂e per user = 1.4387 Wh × 384.40 g/kWh / 1000 = 0.553 g
```

**Combined system impact:**

```
GPT-4 + GPT-4o total: 72.7 Wh (0.073 kWh) per user, 27.94 g ≈ 27.9 g per user
```

**Comparison to 1-hour SimpleTemplate meeting:**

```
SimpleTemplate (1h meeting, midpoint): 38.1 Wh (0.038 kWh), 8.2 g CO₂e
Training (per user, proxy):             72.7 Wh (0.073 kWh), 27.9 g CO₂e
Ratio (midpoint): 38.1 ÷ 72.7 = 0.52×

Amortized training proxy is 1.9× the cost of a single meeting's inference (energy).
After 2 meetings, cumulative inference costs surpass the per-user training share.
Note: GPT-5.x training costs are unpublished; GPT-4/GPT-4o are proxies only.
```

---

# Appendix D: Speech-to-Text Training Impact — OWSM Case Study

## D.1 Context and Relevance

This appendix examines the training energy requirements for **Open Whisper-style Speech Models (OWSM)** [19], which represent open-source alternatives to proprietary ASR systems like OpenAI's Whisper. Understanding S2T training costs provides important context for the transcription services used in this system.

**Why OWSM as a case study:**
- OWSM models explicitly reproduce Whisper-style training using open-source toolkits
- Training methodology and resource requirements are publicly documented

**Relationship to this system:**
While this system uses commercial transcription services (not OWSM), this case study illustrates the one-time training costs that underpin modern ASR capabilities. Similar to LLM training costs (Appendix C), these costs are amortised across all users of the technology.

**Limitation:**
This analysis does not account for the energy used by auxiliary AI systems (e.g. diarization, content moderation) that are bundled in the transcription services used in this system.

---

## D.2 OWSM v3 Training Configuration

This analysis focuses on OWSM v3 [19], which represents a standard medium-sized Whisper-style model:

| Model | GPUs | Duration | Training Data |
|-------|------|----------|---------------|
| OWSM v3 | 64 A100s | 10 days | 180k hours |

The model uses NVIDIA A100 40GB PCIe GPUs with 250W TDP [20].

---

## D.3 Energy Calculation Methodology

### Base GPU Energy

```
64 GPUs × 250W × 24h × 10 days = 3,840 kWh
```

### System Overhead

GPUs do not operate in isolation. According to Netrality Data Centers [22]:
> "A server with eight A100 GPUs draws 3,200 watts just for GPUs, plus another 500-1,000 watts for CPUs, memory, and other components."

Calculation:
- Midpoint: 750W / 3,200W = additional 23.44%
- System overhead multiplier: 1.2344×

This accounts for CPUs, memory, networking, storage, and other server components required to support GPU training.

### Datacenter Infrastructure (PUE)

The Uptime Institute Global Data Center Survey 2024 [21] reports:
> "In the 2024 survey results, the industry average PUE of 1.56 reveals a continuing trend of inertia"

PUE multiplier: 1.56×

PUE (Power Usage Effectiveness) captures cooling, power distribution losses, lighting, and other facility-level overhead. A PUE of 1.56 means that for every 1 kWh consumed by IT equipment providing value directly to users, an additional 0.56 kWh is consumed by everything else.

---

## D.4 Complete Training Energy Impact

| Tier | Description | OWSM v3 |
|------|-------------|----------|
| Tier 1 | GPU only | 3,840 kWh |
| Tier 2 | + System overhead (×1.2344) | 4,740 kWh |
| Tier 3 | + Datacenter PUE (×1.56) | 7,394 kWh |

---

## D.5 Interpretation and Context

### Comparison to LLM Training

| Model Type | Training Energy |
|------------|----------------|
| OWSM v3 | 7,394 kWh |
| GPT-4 (estimated) | 57,000,000 kWh |
| GPT-4o (estimated) | 1,151,000 kWh |

Key observations:
- S2T training is 7,700× less energy-intensive than GPT-4 training
- S2T training is 156× less energy-intensive than GPT-4o training

---

## D.6 Per-User Training Impact

**User base:** Training costs amortised across 300 million Microsoft Teams monthly active users [23], representing a conservative estimate for Azure Speech-to-Text service reach.

**Carbon intensity:** US average 384 g CO₂e/kWh (EcoLogits [25] ElectricityMixRepository, zone='USA'), as most large-scale AI training occurs in US data centres.

## D.7 Calculation Methodology

**OWSM v3 per-user calculations:**

```
Training energy total: 7,394 kWh
User base: 300,000,000 users
Energy per user = 7,394 ÷ 300,000,000 = 0.025 Wh (0.000025 kWh)
CO₂e per user = 0.025 Wh × 384 g/kWh = 0.0095 g
```

**Combined system training impact (LLM + ASR):**

```
GPT-4 + GPT-4o:  72.7 Wh (0.073 kWh) per user,   27.9 g per user
OWSM v3 (ASR):   0.025 Wh (0.000025 kWh) per user, 0.0095 g per user
Total:           72.7 Wh (0.073 kWh) per user,   27.95 g ≈ 28.0 g per user
```

**Key observation:** ASR training represents only 0.034% of the combined training impact per user, making it negligible in the overall training footprint.

---

# Appendix E: LLM Energy Consumption Methodology

All LLM inference energy estimates use **EcoLogits [25]**, an open-source LCA regression model. It was chosen because GPT-5-nano and GPT-5.1 have no published energy measurements; EcoLogits covers any model via architecture parameters and returns min–max ranges reflecting parameter count uncertainty.

EcoLogits is used **for energy estimation only**. CO₂e is derived separately as `energy (kWh) × 217 g/kWh` (GBR grid intensity from EcoLogits ElectricityMixRepository [25]), applied consistently to both LLM and ASR.

Each API invocation is modelled individually using generation latency (`output_tokens / TPS + TTFT`) so that per-call prefill overhead is counted once per real network request rather than amortised across all invocations.

## E.1 Model Parameters

All values loaded at runtime from EcoLogits ModelRepository and PROVIDER_CONFIG_MAP.

| Parameter | GPT-5-nano (FAST) | GPT-5.1 (BEST) |
|-----------|------------------|----------------|
| Architecture | Dense | MoE |
| Active params | 5–18.5 B | 30–90 B |
| Total params | 5–18.5 B | 300 B |
| TPS | 96.1 tok/s | 60.6 tok/s |
| TTFT | 2.29 s | 1.85 s |

| Datacenter (OpenAI) | Grid (GBR) |
|---|---|
| PUE 1.20 | GWP 0.21741 kg CO₂eq/kWh |
| WUE 0.569 L/kWh | — |

## E.2 Cross-Validation

Jegham et al. [1] measured GPT-4o at 1k in / 1k out: **1.215 Wh**; GPT-4 Turbo at the same size: **5.940 Wh**. Both are consistent with EcoLogits estimates for the same models, giving confidence in EcoLogits' estimates for GPT-5-nano and GPT-5.1. As empirical benchmarks for these models emerge, re-run `documentation/env_assets/calculations.py` with updated parameters.


---

# Appendix F: Template Usage Frequency

This appendix documents observed template usage across the production system. Data collected by i.AI from December 2024 to May 2026.

| Template | Share |
|----------|------:|
| General | 52.4% |
| Delivery | 15.2% |
| Short 'n' Sweet | 12.3% |
| User generated | 9.6% |
| Cabinet | 5.9% |
| Care Assessment | 2.6% |
| Planning Committee | 1.2% |
| Care Assessment V2 | 0.7% |

## F.2 Usage-Weighted Environmental Impact

This section maps each production template to its underlying implementation, gives its per-meeting LLM impact, and calculates the usage-weighted average across all templates.

### F.2.1 Template-to-Implementation Mapping

| Template | Combined share | Implementation | Appendix |
|---------|---------------|----------------|----------|
| General | 52.4% | SimpleTemplate (citations) | B.2 |
| Delivery | 15.2% | Delivery Template | B.4 |
| Short 'n' Sweet | 12.3% | SimpleTemplate (no citations) | B.2a |
| User generated | 9.6% | UserTemplate DOCUMENT | B.6.1 |
| Cabinet | 5.9% | SectionTemplate (Y=6) | B.3 |
| Care Assessment | 2.6% | SimpleTemplate (deprecated v1) | B.2 |
| Planning Committee | 1.2% | SectionTemplate (Y=6) | B.3 |
| Care Assessment V2 | 0.7% | SimpleTemplate (citations) | B.2 |

*The lowercase entries "general", "delivery", and "cabinet" in the raw data (F.1) are the same built-in templates stored with different casing, not separate user-created templates. Their shares are merged into the corresponding capitalised entries above.*

### F.2.2 Per-Template LLM Impact (X = 9,000 words, 1-hour baseline)

EcoLogits [25] min–max ranges (UK GBR grid). Output tokens only; CO₂e derived as energy × 217 g/kWh (GBR).

| Template | Output Tokens | LLM Energy | LLM CO₂e |
|---------|--------------|------------|----------|
| Basic Minutes (fallback) | 5,660 | 0.3–0.4 Wh | 0.1 g |
| Short 'n' Sweet | 5,660 | 7.4–11.0 Wh | 1.6–2.4 g |
| Cabinet / Planning Committee (SectionTemplate Y=6) | 12,964 | 9.0–13.3 Wh | 2.0–2.9 g |
| Delivery | 16,160 | 10.3–15.3 Wh | 2.2–3.3 g |
| UserTemplate DOCUMENT | 9,260 | 12.1–18.1 Wh | 2.6–3.9 g |
| General / Care Assessment / Care Assessment V2 | 20,060 | 12.7–18.8 Wh | 2.8–4.1 g |

### F.2.3 Usage-Weighted Average Impact

Applying the combined shares from F.2.1. LLM CO₂e midpoints used for weighting.

| Template | Share | LLM Energy (mid) | LLM CO₂e (mid) | Weighted Energy | Weighted CO₂e |
|---------|-------|-----------------|----------------|----------------|---------------|
| General | 52.4% | 15.75 Wh | 3.45 g | 8.25 Wh | 1.81 g |
| Delivery | 15.2% | 12.8 Wh | 2.75 g | 1.95 Wh | 0.42 g |
| Short 'n' Sweet | 12.3% | 9.2 Wh | 2.0 g | 1.13 Wh | 0.25 g |
| User generated | 9.6% | 15.1 Wh | 3.25 g | 1.45 Wh | 0.31 g |
| Cabinet | 5.9% | 11.15 Wh | 2.45 g | 0.66 Wh | 0.14 g |
| Care Assessment | 2.6% | 15.75 Wh | 3.45 g | 0.41 Wh | 0.09 g |
| Planning Committee | 1.2% | 11.15 Wh | 2.45 g | 0.13 Wh | 0.03 g |
| Care Assessment V2 | 0.7% | 15.75 Wh | 3.45 g | 0.11 Wh | 0.02 g |
| **Usage-weighted total** | **100%** | — | — | **14.2 Wh** | **3.1 g** |

*Exact min–max ranges from `calculations.py`: LLM 11.4–16.9 Wh / 2.5–3.7 g CO₂e.*

**Combined with transcription (ASR GBR / LLM GBR):**

| Component | Energy | CO₂e | % of Total |
|-----------|--------|------|-----------|
| Transcription (GBR) | 22.3 Wh (0.022 kWh) | 4.8 g | 61% |
| LLM processing (GBR, midpoint) | 14.2 Wh (0.014 kWh) | 3.1 g | 39% |
| **Usage-weighted total** | **33.6–39.1 Wh (0.034–0.039 kWh)** | **7.3–8.5 g** | **100%** |

**Comparison to single-template estimates:**

| Basis | Combined Energy | Combined CO₂e |
|-------|----------------|---------------|
| Basic Minutes | 22.6–22.7 Wh | 4.9 g |
| Usage-weighted average | 33.6–39.1 Wh | 7.3–8.5 g |
| SimpleTemplate (General only) | 35.0–41.1 Wh | 7.6–8.9 g |
| SectionTemplate Y=6 | 31.3–35.5 Wh | 6.8–7.7 g |

**Key findings:**
* The usage-weighted average (7.3–8.5 g CO₂e, 33.6–39.1 Wh) is 6% lower than using only the General/SimpleTemplate estimate, because Short 'n' Sweet and Delivery (27.5% combined) use less BEST-model output
* Transcription contributes 61% of combined CO₂e; LLM contributes 39%
* Basic Minutes is negligible in CO₂e terms (0.1 g LLM) due to FAST-only processing; it drags down the weighted average only marginally (2.6% share)
* Short 'n' Sweet has lower LLM impact than General (1.6–2.4 g vs 2.8–4.1 g) due to skipping the citations pipeline (saves 10,800 output tokens)

**Limitations:**
* "User generated" is treated as DOCUMENT type throughout; FORM-type templates are FAST-only and would lower this estimate
* SectionTemplate section count assumed Y=6 for both Cabinet and Planning Committee
* UserTemplate DOCUMENT fixed prompt assumed 200 words of template content; actual values vary

---

# Appendix HW: Homeworking Displacement Context

This appendix expresses the system's carbon costs in terms of a familiar human-scale activity — one person working from home — to help readers calibrate the magnitudes involved.

## HW.1 Source Data

**Emission factor source:** UK Government GHG Conversion Factors 2025, published by DESNZ and DEFRA [24].  
**URL:** https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025

| Activity | Unit | kg CO₂e |
|----------|------|--------:|
| Office equipment | per FTE working hour | 0.03144 |
| Heating | per FTE working hour | 0.30234 |
| **Homeworking (combined)** | **per FTE working hour** | **0.33378** |

Heating dominates at **91%** of the combined factor; office equipment contributes only 9%. The combined rate used throughout this appendix is **333.78 g CO₂e per FTE working hour**.

## HW.2 One Hour of AI Processing

**Question:** how long must one person work from home to emit the same CO₂e as Local Transcribe processing a single 1-hour meeting?

| Metric | Value |
|--------|------:|
| Usage-weighted meeting CO₂e (Section 8.1) | 7.3–8.5 g (midpoint 7.9 g) |
| SimpleTemplate meeting CO₂e (Section 8.2) | 7.6–8.9 g (midpoint 8.2 g) |
| Homeworking rate | 333.78 g CO₂e/h |

```
Usage-weighted (min):  7.3 g ÷ 333.78 g/h = 0.0219 h ≈ 78.9 seconds
Usage-weighted (max):  8.5 g ÷ 333.78 g/h = 0.0255 h ≈ 91.8 seconds
Usage-weighted (mid): 7.9 g ÷ 333.78 g/h = 0.0237 h ≈ 85 seconds

SimpleTemplate (min):  7.6 g ÷ 333.78 g/h ≈ 82.1 seconds
SimpleTemplate (max):  8.9 g ÷ 333.78 g/h ≈ 96.4 seconds
SimpleTemplate (mid): 8.2 g ÷ 333.78 g/h ≈ 89 seconds
```

**Conclusion:** Processing one 1-hour meeting costs the same as approximately **85 seconds (1.5 minutes)** of a single person working from home (usage-weighted midpoint). The AI carbon cost at the per-meeting level is negligibly small in human-activity terms.

## HW.3 One Month of AWS Hosting

**April 2026 AWS hosting (MBM):** 17,317 g CO₂e (Section 2.2)

```
17,317 g ÷ 333.78 g/h = 51.9 hours ≈ 6.5 working days (at 8 h/day)
```

One month of AWS infrastructure hosting is equivalent to approximately **6.5 working days** of one person working from home.

Run `documentation/env_assets/aws_carbon.py` for the current month's figure.

## HW.4 Comparison and Conclusions

| Item | CO₂e | Homeworking equivalent |
|------|-----:|----------------------:|
| One 1-hour meeting — AI, usage-weighted (mid) | 7.9 g | 85 seconds |
| One 1-hour meeting — AI, SimpleTemplate (mid) | 8.2 g | 89 seconds |
| April 2026 AWS hosting (MBM) | 17,317 g | 51.9 hours (6.5 working days) |

The hosting layer emits approximately **2,192×** more CO₂e per month than the AI cost of a single 1-hour meeting (at the usage-weighted midpoint). In homeworking terms the ratio is starker than ever: weeks of infrastructure running time versus about 85 seconds of AI processing per meeting.

**Strategic implication:** Carbon reduction efforts should prioritise the infrastructure layer — right-sizing compute, switching off idle resources, and selecting low-carbon AWS regions — over micro-optimising prompt length or model selection. The AI processing cost, while non-zero, is negligibly small compared to the hosting baseline at current usage volumes.

---

# References

[1] N. Jegham, M. Abdelatti, C. Y. Koh, L. Elmoubarki and A. Hendawi, "How Hungry is AI? Benchmarking Energy, Water, and Carbon Footprint of LLM Inference," arXiv:2505.09598v6, Nov. 2025. [Online]. Available: https://arxiv.org/abs/2505.09598

[2] U. Hölzle, "Powering a Google search," *Google Public Policy Blog*, Jan. 11, 2009. [Online]. Available: https://googleblog.blogspot.com/2009/01/powering-google-search.html

[3] Environment Agency, "England faces 5 billion litre public water shortage by 2055 without urgent action," GOV.UK, Jun. 2025. [Online]. Available: https://www.gov.uk/government/news/england-faces-5-billion-litre-public-water-shortage-by-2055-without-urgent-action

[4] European Environment Agency, "Water abstraction by economic sector in Europe." [Online]. Available: https://www.eea.europa.eu/en/analysis/indicators/water-abstraction-by-source-and/water-abstraction-by-economic-sector

[5] European Environment Agency, “Water scarcity conditions in Europe,” *EEA Briefing*, 2025. [Online]. Available: https://www.eea.europa.eu/en/analysis/indicators/use-of-freshwater-resources-in-europe-1

[6] techUK, "Understanding data centre water use in England," London, UK, Aug. 2025. [Online]. Available: https://www.techuk.org/static/c5d37a41-6eb9-4d41-8ed3036030936814/techUK-ReportUnderstanding-Data-Centre-Water-Use-in-EnglandAugust-2025.pdf

[7] Sustainability Directory, "Non-Consumptive Water Use," 2025. [Online]. Available: https://term.sustainability-directory.com/term/non-consumptive-water-use

[8] U.S. Geological Survey, "Evaporation and the Water Cycle: Evaporation," U.S. Geological Survey Water Science School. [Online]. Available: https://www.usgs.gov/water-science-school/science/evaporation-and-water-cycle

[9] National Oceanic and Atmospheric Administration, "The Water Cycle," NOAA Education. [Online]. Available: https://www.noaa.gov/education/resource-collections/freshwater/water-cycle

[10] European Environment Agency, "Greenhouse Gas Emission Intensity of Electricity Generation in Europe (EU-27)." [Online]. Available: https://www.eea.europa.eu/en/analysis/indicators/greenhouse-gas-emission-intensity-of-1 

[11] Z. Ji and M. Jiang, "A systematic review of electricity demand for large language models: evaluations, challenges, and solutions," *Renewable and Sustainable Energy Reviews*, vol. 225, p. 116159, 2026. [Online]. Available: https://www.sciencedirect.com/science/article/pii/S1364032125008329

[12] A. Ben Abacha, W.-w. Yim, Y. Fu, Z. Sun, M. Yetisgen, F. Xia and T. Lin, "MEDEC: A Benchmark for Medical Error Detection and Correction in Clinical Notes," arXiv:2412.19260, Jan. 2, 2025. [Online]. Available: https://arxiv.org/abs/2412.19260

[13] K. Wiggers, "Sam Altman says ChatGPT has hit 800M weekly active users," *TechCrunch*, Oct. 6, 2025. [Online]. Available: https://techcrunch.com/2025/10/06/sam-altman-says-chatgpt-has-hit-800m-weekly-active-users/

[14] U.S. Environmental Protection Agency, "Emissions & Generation Resource Integrated Database (eGRID)," EPA. [Online]. Available: https://www.epa.gov/egrid

[15] J. El Bahri, M. Kouissi and M. Achkari Begdouri, "Comparative Analysis of Energy Consumption and Carbon Footprint in Automatic Speech Recognition Systems: A Case Study Comparing Whisper and Google Speech-to-Text," *Computer Sciences & Mathematics Forum*, vol. 10, no. 1, p. 6, Jun. 16, 2025. [Online]. Available: https://www.mdpi.com/2813-0324/10/1/6

[16] J. Bhuiyan, "Google undercounts its carbon emissions, report finds," The Guardian, Jul. 2, 2025. [Online]. Available: https://www.theguardian.com/technology/2025/jul/02/google-carbon-emissions-report

[17] K. Robison, "Meta got caught gaming AI benchmarks," The Verge, Apr. 2025. [Online]. Available: https://www.theverge.com/meta/645012/meta-llama-4-maverick-benchmarks-gaming

[18] C.-J. Wu, R. Raghavendra, U. Gupta, B. Acun, N. Ardalani, K. Maeng, G. Chang, F. A. Behram, J. Huang, C. Bai, M. Gschwind, A. Gupta, M. Ott, A. Melnikov, S. Candido, D. Brooks, G. Chauhan, B. Lee, H.-H. S. Lee, B. Akyildiz, M. Balandat, J. Spisak, R. Jain, M. Rabbat and K. Hazelwood, "Sustainable AI: Environmental Implications, Challenges and Opportunities," arXiv preprint arXiv:2111.00364, Jan. 9, 2022. [Online]. Available: https://arxiv.org/abs/2111.00364

[19] Y. Peng et al., "Reproducing Whisper-Style Training Using an Open-Source Toolkit and Publicly Available Data," arXiv:2309.13876v1 [cs.CL], 2023. [Online]. Available: https://arxiv.org/abs/2309.13876v1

[20] NVIDIA Corporation, "NVIDIA A100 40GB PCIe GPU Accelerator Product Brief," NVIDIA, 2020. [Online]. Available: https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/A100-PCIE-Prduct-Brief.pdf

[21] Uptime Institute, "Uptime Institute Global Data Center Survey 2024," UII Keynote Report 146M, 2024. [Online]. Available: https://datacenter.uptimeinstitute.com/rs/711-RIA-145/images/2024.GlobalDataCenterSurvey.Report.pdf

[22] Netrality Data Centers, "High-Density Colocation for AI and GPU Workloads," 2025. [Online]. Available: https://netrality.com/blog/high-density-colocation-ai-gpu-infrastructure/

[23] Microsoft, “Microsoft Teams surpasses 300 million monthly active users,” *Microsoft FY2023 Q3 Earnings Conference Call Transcript*, Apr. 2023. [Online]. Available: https://www.microsoft.com/en-us/investor/events/fy-2023/earnings-fy-2023-q3/

[24] Department for Energy Security and Net Zero (DESNZ) and Department for Environment, Food & Rural Affairs (DEFRA), “Greenhouse Gas Reporting: Conversion Factors 2025,” UK Government, 2025. [Online]. Available: https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025

[25] GenAI Impact, “EcoLogits: Tracking the environmental impacts of generative AI models,” v0.10.2, 2025. [Online]. Available: https://github.com/genai-impact/ecologits
