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

## Data agent configuration

`HomeLoansDataAgent.DataAgent` is temporarily excluded from Fabric Git
integration because its `.platform` item marker is intentionally absent. This
allows the Lakehouse, notebook, and pipeline to synchronize without Fabric
attempting to import the data agent.

The retained configuration includes:

- `Files/Config/data_agent.json`
- `Files/Config/draft/stage_config.json`
- `publish_info.json`

Fabric requires
Lakehouse data source folders to contain a generated `datasource.json` with
physical workspace, artifact, table, and column IDs. Committing a placeholder
file in that location makes the entire item invalid during Git synchronization.

The portable data source template and few-shot queries are stored under
`deployment/templates`. After the base items are synchronized, the deployment
script can use the Data Agent SDK to create the agent, add the Lakehouse,
discover and select the `home_loans` table, add the examples, and publish it.
Re-enable Git integration for the agent only by committing a `.platform` file
exported by Fabric with a complete, valid item definition.

Do not directly edit a generated `published` folder. Update draft configuration,
validate it, and publish through Fabric.

