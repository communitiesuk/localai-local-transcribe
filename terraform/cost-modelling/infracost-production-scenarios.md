# Production cost scenarios

This document explains the model's assumptions and limitations. For setup, configuration, and regeneration commands, see the [cost modelling README](README.md).

These scenarios estimate AWS costs for the production application only. The separate [Terraform state backend](../production/backend/main.tf) is excluded (about $1/month at list price). Azure Speech, LLM, APIM, and Azure Blob Storage costs are also excluded.

## Provisioned infrastructure

The baseline and the three workload scenarios use the same provisioned capacity from [production Terraform](../production/main.tf). With the [production defaults](../production/variables.tf), this is one frontend task (1 vCPU / 2 GiB), one backend task (4 vCPU / 8 GiB), and two worker tasks (4 vCPU / 8 GiB each). Worker, frontend, and backend counts and the database class are priced separately.

Production currently configures a single-AZ `db.t4g.small` RDS instance with 50 GiB of storage. Each database variant prices a complete class-and-AZ combination at that storage size. If `database_multi_az` is omitted, variants use the production AZ mode.

## Workload assumptions

| Assumption | Low | Medium | High |
| --- | ---: | ---: | ---: |
| Monthly active users | 1,000 | 1,200 | 1,500 |
| Meetings per month | 50,000 | 60,000 | 75,000 |
| Audio hours per month | 50,000 | 60,000 | 75,000 |
| Source uploads at approximately 53.3 MB each | 2,666.7 GB | 3,200 GB | 4,000 GB |
| Converted MP3 at 192 kbps | 4,320 GB | 5,184 GB | 6,480 GB |
| Steady-state audio storage at 30-day retention | 6,986.7 GB | 8,384 GB | 10,480 GB |
| HTTPS requests | 25 million | 30 million | 37.5 million |
| CloudWatch log ingestion | 200 GB | 240 GB | 300 GB |

Each active user is assumed to produce 50 meetings per month, with a mean duration of 60 minutes (50 audio hours). The request estimate is 500 per meeting: roughly 450 two-second status polls during a 15-minute transcription wait, plus page, asset, and API requests. Audio replay is assumed to be negligible.

Browser recordings are `audio/webm`, while the backend accepts only mono MP3 without conversion. Each one-hour recording is therefore retained as both an approximately 53.3 MB source and an approximately 86.4 MB, 192 kbps MP3 for 30 days.

## How the usage files were estimated

- **Audio storage and transfer:** Scale the 80 MB estimate for a 90-minute WebM recording to one hour. Converted size is 192 kbps times 3,600 seconds, or 86.4 MB. Multiply both sizes by meetings per month to estimate 30-day steady-state storage; multiply only the MP3 size by meetings for Azure uploads. This assumes one upload per meeting and that billable S3 retention is 30 days.
- **Requests:** Apply 500 HTTPS requests per meeting to CloudFront and each WAF ACL. Budget two S3 write-class and three read-class requests per meeting for the uploads bucket, and 20 transcription-queue plus 10 LLM-queue requests per meeting. These are allowances, not measured operation counts.
- **Network and observability:** The low file budgets 1,250 GB of CloudFront viewer transfer and ALB processing, 50 GB of CloudFront origin transfer, 100 GB of other NAT traffic (including responses as an allowance), and 200 GB of CloudWatch log ingestion. Medium and high scale those allowances by their meeting counts (1.2x and 1.5x). Retained logs, access-log activity, and image storage have their own estimates in the usage files; they are not derived from audio size. Replace these assumptions with production measurements when available.
- **Regional NAT and S3:** The worker uploads audio through the regional NAT gateway. Its total monthly processing is 4,420 / 5,304 / 6,630 GB (audio uploads plus other NAT traffic), not multiplied by AZ count. Same-region S3 access uses a free gateway endpoint and contributes no NAT or endpoint processing charge. [AWS bills regional NAT hours per configured AZ](https://aws.amazon.com/vpc/pricing/); production configures two. Infracost 2.10.1 reported only 730 hours at $0.05/hour. The matrix adjusts for the missing 730 hours at that rate ($36.50/month) and adds nothing if the scan already prices both AZs.

## Internet egress

With synchronous Azure Speech, the worker sends the prepared audio to Azure APIM over the internet. This is AWS internet egress from the worker, not S3 egress. Infracost prices audio uploads and background egress together through `aws_data_transfer.internet_egress`, separately from NAT gateway data processing.

Allow 4 GB/month of background internet egress for telemetry and other non-meeting traffic. At idle this fits within the assumed unused free allowance, so there is no billable egress entry. Allow 5 GB/month of NAT processing at idle; the workload scenarios already include this in their other NAT traffic allowance.

| Scenario | Audio egress to Azure | Approximate total egress charge at $0.09/GB after 100 GB free |
| --- | ---: | ---: |
| Low | 4,320 GB | $380.16 |
| Medium | 5,184 GB | $457.92 |
| High | 6,480 GB | $574.56 |

The generator sets `monthly_outbound_internet_gb` to the combined audio and background outbound volume minus the available free allowance, with a floor of zero (4,224 / 5,088 / 6,384 GB by default). If other workloads consume part or all of the shared AWS allowance, set `free_egress_gb` in the [workload inputs](infracost-workload.yml) to the amount still available and regenerate. Any uncovered idle egress is then included automatically. NAT processing still uses the gross upload volume. Confirm the effective rate and free-tier treatment against the AWS bill.

## Baseline and pricing caveats

The [idle baseline](infracost-usage-production-idle.yml) includes background NAT processing and CloudTrail event recording, but no meeting-driven usage. Capacity variants use idle usage; workload variants use baseline capacity. The defaults run 15 scans in temporary copies without applying Terraform. When using `--config`, usage file paths are relative to that config file.

All scenarios budget about 1.72 million additional CloudTrail management events per month on the production trail (about $34.35/month at list price). This is a fixed background allowance that does not scale with meetings. Separate audit analysis, CloudWatch metric publication and retrieval, and RDS monitored vCPU-month charges are not included (as infracost does not seem to support them as inputs, though they have been observed in production, totalling ~$25/month).

Use the [AWS London on-demand price list](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECS/current/eu-west-2/index.json) when checking the configured Fargate rates. The optional scaled view affects corrected ARM64 Fargate vCPU and memory charges, interface endpoint hours, regional NAT hours, RDS instance hours, ALB hours, and KMS keys. Metered workload charges stay at list price. Scaled totals can reveal the factor; omit scaling when sharing reports that should not disclose it.

Start with the baseline row's `List total` or `Scaled total` and add the matching deltas from at most one row per group. Pick one database row, rather than adding a single-AZ size delta to a Multi-AZ delta. The model does not capture interactions such as extra worker polling or logging.

## Usage model details

The generator's `--check` flag detects stale generated files without writing them or contacting AWS or Infracost.

The shared assumptions hold the conversion rates and fixed allowances. Transcriptions drive audio uploads, status polling, and transcription queue requests; summaries drive LLM queue requests; both drive worker log estimates. Converted audio storage assumes one retained MP3 per transcribed meeting, up to the number of meetings, so extra transcription attempts do not increase that storage estimate. The non-audio NAT allowance uses the background rate as a floor. The high scenario retains its separate ALB active-connections assumption.

The VPC endpoint indexes in the usage files follow the [append-only service list](../modules/networking/vpc_endpoints.tf): index 5 is `ecr.dkr` and index 12 is `logs`. Replace indexed addresses if a production plan produces different resource addresses.