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
- `publish_info.json`

The Git definition intentionally starts without a data source. Fabric requires
Lakehouse data source folders to contain a generated `datasource.json` with
physical workspace, artifact, table, and column IDs. Committing a placeholder
file in that location makes the entire item invalid during Git synchronization.

The portable data source template and few-shot queries are stored under
`deployment/templates`. After the base items are synchronized, the deployment
script uses the Data Agent SDK to add the Lakehouse, discover and select the
`home_loans` table, add the examples, and publish the agent. A later commit from
Fabric can then capture the generated `lakehouse-tables-HomeLoansLakehouse`
folder as a valid environment-specific Data Agent definition.

Do not directly edit a generated `published` folder. Update draft configuration,
validate it, and publish through Fabric.

