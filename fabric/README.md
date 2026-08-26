# Fabric item definitions

## `HomeLoansLakehouse.Lakehouse`

Contains Lakehouse metadata and ALM tracking settings. Lakehouse Git integration
does not version table data, so the ingestion pipeline must run in each target
workspace.

## `LoadHomeLoans.Notebook`

Fabric Git source for a PySpark notebook. The pipeline supplies the GitHub CSV
URL plus physical workspace and Lakehouse IDs. The notebook:

1. restricts the source to `raw.githubusercontent.com`;
2. writes the CSV to the Lakehouse Files area;
3. applies an explicit schema and data quality checks;
4. adds analysis-friendly derived columns;
5. writes the Delta table to `Tables/home_loans`.

## `IngestHomeLoans.DataPipeline`

`pipeline-content.template.json` contains one `TridentNotebook` activity.
`deployment/deploy_fabric_items.py` replaces the placeholders and writes the
gitignored `pipeline-content.json`.

## `HomeLoansDataAgent.DataAgent`

The folder follows the Fabric data agent definition layout:

- `Files/Config/data_agent.json`
- `Files/Config/draft/stage_config.json`
- one Lakehouse data source folder with `datasource.template.json`
- `fewshots.json`
- `publish_info.json`

The data source element IDs are created by Fabric during schema discovery, so
the deployment script uses the Data Agent SDK to add the Lakehouse and select
the `home_loans` table. The template documents the intended data source
description and instructions for later Git/ALM review.

Do not directly edit a generated `published` folder. Update draft configuration,
validate it, and publish through Fabric.

