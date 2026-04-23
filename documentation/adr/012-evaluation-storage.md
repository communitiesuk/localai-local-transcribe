# ADR-012: Evaluation Storage

## Status

Proposed

Date of decision: 2025-01-27

## Context and Problem Statement

Evaluation systems require storage for both inputs (test cases, prompts, configurations) and outputs (results, metrics, scores). These have fundamentally different characteristics:

Inputs are infrequently written (only when tests are added or modified), could contain sensitive data (real transcripts, confidential content), and require stricter access control. They need version control for reproducibility and code review for changes.

Outputs are frequently written (every evaluation run), contain primarily metrics and scores, and need to be queryable for trend analysis and debugging. They require efficient storage and retrieval for dashboards and analysis tools.

We need to determine optimal storage strategies that address these distinct requirements, with particular emphasis on protecting sensitive input data.

## Considered Options

### Input Storage Options
* Azure Blob Storage
* Git repository (version controlled test cases)
* S3 Bucket (versioned test datasets)
* Dedicated test case database

### Output Storage Options
* Azure Blob Storage
* Azure DevOps Artifacts
* CI/CD Artifacts
* S3 Bucket (or similar object storage)
* Dedicated Database

## Decision Outcome

Inputs: Azure Blob Storage, because it handles large binary files (e.g., audio), supports fine-grained access controls and encryption for sensitive data, and aligns with the Azure environment. ADAPT (an MHCLG VDI service) can optionally provide an additional layer of access restriction for writes to the underlying storage.

Outputs: Azure Blob Storage, because it aligns with the Azure environment used for evaluation runners (see ADR-014) and input storage, avoids unnecessary cross-cloud complexity, and provides persistent and reliable storage that is straightforward to set up and integrate.

## Pros and Cons of the Options

### Input Storage Options

#### Azure Blob Storage

Store evaluation inputs as files in Azure Blob Storage containers with fine-grained access controls.

* Good, because handles large binary files efficiently (e.g., audio samples).
* Good, because supports fine-grained access controls and encryption for sensitive data.
* Good, because aligns with the Azure environment used for evaluation runners (ADR-014).
* Good, because ADAPT (an MHCLG VDI service) can optionally be used to provide an additional layer of access restriction for writes to the underlying storage.
* Bad, because requires access management setup.
* Bad, because not suitable for version-controlled test cases without additional tooling.

#### Git repository (version controlled test cases)

Store evaluation test cases, prompts, and configurations in the git repository alongside code.

* Good, because no additional infrastructure required.
* Good, because it is easy to configure and use.
* Bad, because not suitable for large binary test files (e.g., audio samples).
* Bad, because it is completely unsuitable for sensitive data.

#### S3 Bucket (versioned test datasets)

Store evaluation inputs as versioned files in S3 bucket with lifecycle policies.

* Good, because handles large files efficiently and stores binary test data.
* Good, because supports fine-grained IAM policies and encryption for sensitive data.
* Good, because CloudTrail provides audit logs for access.
* Good, because versioning tracks dataset evolution.
* Good, because it is well suited for storing sensitive data, if configured correctly. 
* Bad, because it requires additional setup and access management.

#### Dedicated test case database

Store test cases and configurations in a dedicated database with versioning.

* Good, because enables querying and filtering test cases.
* Good, because can implement row-level security for sensitive test cases.
* Good, because it is well suited for storing sensitive data, if configured correctly. 
* Bad, because requires infrastructure setup and maintenance.
* Bad, because it requires additional access management.

### Output Storage Options

#### Azure Blob Storage

Store evaluation results as files in Azure Blob Storage containers with fine-grained access controls.

* Good, because it aligns with the Azure environment used for evaluation runners (ADR-014) and input storage.
* Good, because it avoids egress costs that would arise from moving data across cloud providers.
* Good, because persistent and reliable with no storage limits beyond cost.
* Good, because easy to set up and integrate, with full control over storage structure.
* Good, because works well with custom dashboards and Jupyter notebooks for analysis.
* Bad, because not optimized for across-file querying of data.
* Bad, because requires a dashboard or Jupyter notebook for most users.

#### Azure DevOps Artifacts

Store evaluation results as pipeline artifacts or Universal Packages within Azure DevOps, scoped to the organisation.

* Good, because it integrates naturally with Azure DevOps CI/CD workflows, aligning with ADR-014.
* Good, because access is restricted to organisation members with minimal additional setup.
* Bad, because it offers less freedom than Blob Storage — access controls are coarser and storage structure is constrained by the package registry model.
* Bad, because pipeline artifacts are tied to pipeline run retention, making long-term persistence unreliable without additional configuration.
* Bad, because there is a 2 GiB free-tier storage limit per organisation; exceeding it requires paid billing.
* Bad, because querying and analysing results across artifacts is difficult.

#### CI/CD Artifacts

Store evaluation results as build artifacts in the CI/CD system.

* Good, because integrates naturally with CI/CD workflows.
* Good, because provides easy access to results per build/PR.
* Bad, because it is not built for long-term persistence.
* Bad, because querying across artifacts is difficult.

#### S3 Bucket (or similar object storage)

Store evaluation results as files in an S3 bucket or similar object storage.

* Good, because persistent and reliable.
* Good, because easy to set up and integrate.
* Good, because works well with custom dashboards.
* Good, because enables versioning and lifecycle policies for cost management.
* Bad, because not optimized for across-file querying of data.
* Bad, because requires a dashboard or jupyter notebook for most users.

#### Dedicated Database

Store evaluation results in a dedicated database (e.g., AuroraDB).

* Good, because enables powerful querying and analysis.
* Good, because supports technical users writing SQL queries.
* Good, because provides efficient time-series analysis.
* Good, because can serve dashboards or jupyter notebooks while supporting direct access.
* Bad, because requires infrastructure setup and maintenance.
* Bad, because non-technical users still need dashboard or jupyter notebook.

## Storage Content Requirements

### Input Storage Should Include
* Test prompts and cases
* Model configurations and parameters
* Dataset versions and references
* Expected outputs or ground truth
* Test case metadata (tags, categories, difficulty)

### Output Storage Should Include
* Evaluation metrics and scores
* Pass/fail status
* Timestamps and execution metadata
* Model versions and configurations used
* Reference to input version used
* Individual test case results
