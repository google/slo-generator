# Migrating `slo-generator` to the next major version

## v1 to v2

Version `v2` of the slo-generator introduces some changes to the structure of
the SLO configurations.

To migrate your SLO configurations from v1 to v2, please execute the following
instructions:

**Upgrade `slo-generator`:**
```
pip3 install slo-generator -U # upgrades slo-generator version to the latest version
```

**Run the `slo-generator migrate` command:**
```
slo-generator migrate -s <SOURCE_FOLDER> -t <TARGET_FOLDER> -b <ERROR_BUDGET_POLICY_PATH> -e <EXPORTERS_PATH>
```
where:
* `<SOURCE_FOLDER>` is the source folder containg SLO configurations in v1 format.
This folder can have nested subfolders containing SLOs. The subfolder structure
will be reproduced on the target folder.

* `<TARGET_FOLDER>` is the target folder to drop the SLO configurations in v2
format. If the target folder is identical to the source folder, the existing SLO
configurations will be updated in-place.

* `<ERROR_BUDGET_POLICY_PATH>` is the path to your error budget policy configuration. You can add more by specifying another `-b <PATH>`

* `<EXPORTERS_PATH>` (OPTIONAL) is the path to your exporters configurations.


**Follow the instructions printed to finish the migration:**

This includes committing the resulting files to git and updating your Terraform
modules to the version that supports the v2 configuration format.

## Example

Example bulk migration of [slo-repository](https://github.com/ocervell/slo-repository) SLOs:

```
$ slo-generator migrate -s slos/ -t slos/ -b slos/error_budget_policy.yaml -b slos/error_budget_policy_ssm.yaml -e slos/exporters.yaml

Migrating slo-generator configs to v2 ...
Config does not correspond to any known SLO config versions.
--------------------------------------------------
slos/exporters.yaml [v1]
Invalid configuration: missing required key(s) ['service_name', 'feature_name', 'slo_name', 'backend'].
Config does not correspond to any known SLO config versions.
--------------------------------------------------
slos/platform-slos/slo_pubsub_coverage.yaml [v1]
➞ slos/platform-slos/slo_pubsub_coverage.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/custom-example/slo_test_custom.yaml [v1]
➞ slos/custom-example/slo_test_custom.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/flask-app-prometheus/slo_flask_latency_query_sli.yaml [v1]
➞ slos/flask-app-prometheus/slo_flask_latency_query_sli.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/flask-app-prometheus/slo_flask_availability_ratio.yaml [v1]
➞ slos/flask-app-prometheus/slo_flask_availability_ratio.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/flask-app-prometheus/slo_flask_availability_query_sli.yaml [v1]
➞ slos/flask-app-prometheus/slo_flask_availability_query_sli.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/flask-app-prometheus/slo_flask_latency_distribution_cut.yaml [v1]
➞ slos/flask-app-prometheus/slo_flask_latency_distribution_cut.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/flask-app-datadog/slo_dd_app_availability_query_sli.yaml [v1]
➞ slos/flask-app-datadog/slo_dd_app_availability_query_sli.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/flask-app-datadog/slo_dd_app_availability_query_slo.yaml [v1]
➞ slos/flask-app-datadog/slo_dd_app_availability_query_slo.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/flask-app-datadog/slo_dd_app_availability_ratio.yaml [v1]
➞ slos/flask-app-datadog/slo_dd_app_availability_ratio.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/slo-generator/slo_bq_latency.yaml [v1]
➞ slos/slo-generator/slo_bq_latency.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/slo-generator/slo_pubsub_coverage.yaml [v1]
➞ slos/slo-generator/slo_pubsub_coverage.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/slo-generator/slo_gcf_throughput.yaml [v1]
➞ slos/slo-generator/slo_gcf_throughput.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/slo-generator/slo_gcf_latency.yaml [v1]
➞ slos/slo-generator/slo_gcf_latency.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/slo-generator/slo_gcf_latency pipeline.yaml [v1]
➞ slos/slo-generator/slo_gcf_latency pipeline.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/slo-generator/slo_gcf_errors.yaml [v1]
➞ slos/slo-generator/slo_gcf_errors.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/online-boutique/slo_ob_adservice_availability.yaml [v1]
➞ slos/online-boutique/slo_ob_adservice_availability.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/online-boutique/slo_ob_adservice_latency.yaml [v1]
➞ slos/online-boutique/slo_ob_adservice_latency.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/online-boutique/slo_ob_all_latency_distribution_cut.yaml [v1]
➞ slos/online-boutique/slo_ob_all_latency_distribution_cut.yaml [v2] (replaced)
✅ Success !
--------------------------------------------------
slos/online-boutique/slo_ob_all_availability_basic.yaml [v1]
➞ slos/online-boutique/slo_ob_all_availability_basic.yaml [v2] (replaced)
✅ Success !
==================================================
Writing slo-generator config to slos/config.yaml ...
✅ Success !
==================================================

✅ Migration of `slo-generator` configs to v2 completed successfully ! Configs path: slos/.

==================================================
PLEASE FOLLOW THE MANUAL STEPS BELOW TO FINISH YOUR MIGRATION:

    1 - Commit the updated SLO configs and your shared SLO config to version control.
    2 - [local/k8s/cloudbuild] Update your slo-generator command:
      [-] slo-generator -f slos -b slos/error_budget_policy.yaml
      [+] slo-generator -f slos -c slos/config.yaml
```
