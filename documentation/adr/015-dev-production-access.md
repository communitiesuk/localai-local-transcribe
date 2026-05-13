# ADR-015: Developer Access to AWS Environments

## Status

Accepted

Date of decision: 2026-02-06

## Context and Problem Statement

Typically, we want to limit access from the team to AWS environments - especially the production environment, which will contain sensitive data. In exceptional circumstances, we may need access, however, for example to debug an issue, or to manually correct malformed data, etc. How should we enable this access?

## Considered Options

* Session Manager
* VPN
* Read-only replicas

## Decision Outcome

Session Manager, because it provides secure, auditable access without inbound network connectivity or long-lived credentials.

## Pros and Cons of the Options

### Session Manager

AWS Systems Manager Session Manager allows developers to access EC2 instances using IAM-authenticated sessions without SSH, public IPs, or inbound firewall rules. Access to dependent services such as Aurora is mediated by the EC2 instance’s IAM role and network configuration, with access centrally logged.

* Good, because access is authenticated and authorized using IAM roles with time-bound credentials.
* Good, because no public inbound network access (SSH, VPN, public IPs) is required on EC2 instances / accessed resources.
* Good, because session start, end, and activity can be logged to CloudTrail and CloudWatch for auditability.
* Bad, because it requires maintaining EC2 instances as controlled access points.
* Neutral, because it still permits interactive human access to production systems when enabled (a controlled risk accepted for exceptional circumstances).

### VPN

A VPN-based approach allows developers to connect their local machines to the AWS VPC and access resources directly using network-level connectivity. Authentication is typically handled separately from AWS IAM, and access is enforced primarily through network controls and shared or individual credentials.

* Good, because it provides broad network access that supports many tools and workflows.
* Bad, because it introduces a persistent network ingress path into the VPC that is otherwise unnecessary.
* Bad, because auditing user activity beyond connection events is limited.
* Bad, because it relies on long-lived credentials and client configuration on developer machines.
* Neutral, because it is a familiar and commonly understood access model.

### Read-only Replicas

Developer access is provided through read-only Aurora replicas or periodically refreshed copies of production data in a separate AWS environment. Direct access to production resources is not permitted.

* Good, because it eliminates the risk of accidental writes to production systems.
* Bad, because it prevents intentional writes to production systems even in exceptional remediation scenarios.
* Good, because developers do not require network or credential access to production resources.
* Bad, because data may be stale or incomplete compared to live production state.
* Bad, because it introduces additional cost and operational overhead to manage replicas or snapshots.