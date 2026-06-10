# EPA Class VI Completeness Checklist Audit Plan

This document tracks how the SMART CCUS review checklists should be audited
against EPA Class VI completeness review materials.

## Purpose

The goal is to identify checklist gaps before expanding the schema.

The current application supports:

1. Ask Assistant
2. Single Document Review
3. Package Review

The next improvement is to align the checklist content more closely with EPA
permit application completeness review expectations.

## Source documents

Primary source:

- UIC Class VI Permit Application Completeness Checklist

Supporting technical sources:

- UIC Program Class VI Implementation Manual for UIC Program Directors
- Class VI Well Area of Review Evaluation and Corrective Action Guidance
- Class VI Well Site Characterization Guidance
- Class VI Well Testing and Monitoring Guidance
- Class VI Well Construction Guidance

## Completeness versus technical review

The completeness checklist asks whether required information is present and
where it appears in the application.

The technical review asks whether the information is adequate, defensible, and
consistent with Class VI expectations.

The SMART CCUS system should preserve this distinction:

| Review layer | Question answered |
|---|---|
| Completeness review | Is the required information present somewhere in the package? |
| Evidence review | Where was relevant evidence found? |
| Technical review | Does the evidence appear sufficient or does it require reviewer follow-up? |

## Current checklist categories

The current system organizes package review around these plan types:

| Plan type | Review role |
|---|---|
| `project_narrative` | General application and project information |
| `aor_corrective_action` | Area of Review and corrective action |
| `financial_responsibility` | Financial responsibility and cost coverage |
| `well_construction` | Injection well construction |
| `pre_operational_testing` | Pre-operational testing |
| `testing_monitoring` | Testing and monitoring |
| `injection_well_plugging` | Injection well plugging |
| `pisc_site_closure` | Post-injection site care and site closure |
| `emergency_remedial_response` | Emergency and remedial response |

Site characterization and site operating information may be reviewed as
information categories, but they are not currently treated as required standalone
package documents.

## EPA completeness checklist sections to audit

The EPA completeness checklist should be audited against the following major
coverage areas.

### General Information / Project Narrative

Potential mapping:

- `project_narrative`

Audit focus:

- Applicant/operator identity
- Facility name, mailing address, and location
- Facility activities requiring environmental permits
- SIC codes
- Ownership status
- Indian lands information
- Other environmental permits and approvals
- Map of the Area
- Contacts for states, tribes, and territories in the AoR

### Site Characterization

Potential mapping:

- `project_narrative`
- `site_geologic_characterization`
- `aor_corrective_action`
- `testing_monitoring`

Audit focus:

- Regional geology
- Hydrogeology
- Injection and confining zones
- USDWs
- Faults and fractures
- Maps and cross sections
- Geochemical and geomechanical characterization
- Storage capacity
- Confining zone integrity
- Baseline monitoring information

### AoR and Corrective Action

Potential mapping:

- `aor_corrective_action`

Audit focus:

- Computational model description
- AoR delineation
- Plume and pressure front modeling
- Artificial penetrations
- Legacy wells
- Corrective action plan
- AoR reevaluation schedule

### Financial Responsibility

Potential mapping:

- `financial_responsibility`
- `project_narrative`

Audit focus:

- Financial responsibility demonstration
- Cost estimates
- Corrective action cost
- Injection well plugging cost
- PISC and site closure cost
- Emergency and remedial response cost
- Financial instruments
- Inflation adjustment and updates

### Well Construction

Potential mapping:

- `well_construction`
- `injection_well_plugging`

Audit focus:

- Well design
- Casing and cementing
- Tubing and packer
- Materials compatibility
- Corrosion considerations
- Mechanical integrity
- Well schematics
- Surface and down-hole safety systems

### Pre-Operational Testing

Potential mapping:

- `pre_operational_testing`
- `well_construction`
- `testing_monitoring`

Audit focus:

- Formation testing
- Well logging
- Core analyses
- Mechanical integrity testing
- Injectivity testing
- Pressure fall-off testing
- Baseline geochemical data

### Testing and Monitoring

Potential mapping:

- `testing_monitoring`

Audit focus:

- Injection rate and volume monitoring
- Injection pressure monitoring
- Annulus pressure monitoring
- Groundwater monitoring
- Geochemical monitoring
- Plume and pressure front tracking
- Mechanical integrity testing
- Corrosion monitoring
- Surface air and/or soil gas monitoring
- Reporting schedule

### Injection Well Plugging

Potential mapping:

- `injection_well_plugging`

Audit focus:

- Plugging plan
- Plugging materials
- Plug placement
- Verification testing
- Final plugging report
- Site-specific plugging conditions

### PISC and Site Closure

Potential mapping:

- `pisc_site_closure`

Audit focus:

- PISC monitoring
- Alternative PISC timeframe
- Non-endangerment demonstration
- Site closure plan
- Site closure report
- Records retention

### Emergency and Remedial Response

Potential mapping:

- `emergency_remedial_response`

Audit focus:

- Emergency response plan
- Remedial response plan
- Triggering events
- Notification procedures
- Shut-in procedures
- Corrective measures
- Emergency contacts

## Known report-language cleanup items

Current reviewer-facing language should be polished.

| Current language | Proposed reviewer-facing language |
|---|---|
| Detected document types | Covered review topics |
| Missing required document types | Required coverage gaps |
| Missing expected document types | Additional expected topics not found |
| Duplicate document types | Duplicate primary submitted documents |
| Unknown documents | Documents needing manual classification |
| Evidence found | Relevant evidence found; reviewer confirmation recommended |

## Recommended next development branches

1. `feature/expand-completeness-checklists`
   - Add missing checklist items identified during this audit.

2. `feature/explain-package-evidence-routing`
   - Show which document and evidence terms credited each package topic.

3. `feature/polish-completeness-report-language`
   - Replace internal diagnostic language with reviewer-facing completeness language.

4. `feature/comprehensive-reviewer-feedback-report`
   - Produce a final package review report modeled around completeness review,
     evidence location, and reviewer follow-up.