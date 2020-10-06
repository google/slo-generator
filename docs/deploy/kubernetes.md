# Deploy SLO Generator in Kubernetes [Alpha]

`slo-generator` can be deployed in Kubernetes using:

* A k8s `CronJob` resource to run the `slo-generator` package on a schedule.

* A `ConfigMap` generated from a folder containing SLOs and mounted to the `CronJob` container.

* A `ConfigMap` generated from the `error_budget_policy.yaml` file and mounted to the `CronJob` container.

For a working example, please see this [example repo](https://github.com/ocervell/slo-generator-gke/).
