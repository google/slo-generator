# Deploy SLO Generator in a Cloud Build pipeline

`slo-generator` can also be triggered in a Cloud Build pipeline. This can be useful if we want to compute some SLOs as part of a release process (e.g: to calculate a metric on each `git` commit or push)

To do so, you need to build an image for the `slo-generator` and push it to `Google Container Registry` in your project.

## [Optional] Build and push the image to GCR

If you are not allowed to use the public container image, you can build and push
the image to your project using CloudBuild:

```sh
git clone https://github.com/google/slo-generator
cd slo-generator/
export CLOUDBUILD_PROJECT_ID=<CLOUDBUILD_PROJECT_ID>
export GCR_PROJECT_ID=<GCR_PROJECT_ID>
make cloud_build
```

## Run `slo-generator` as a build step

Once the image is built, you can call the SLO generator using the following
snippet in your `cloudbuild.yaml`:

```yaml
---
steps:

- name: gcr.io/slo-generator-ci-a2b4/slo-generator
  command: slo-generator
  args:
    - -f
    - slo.yaml
    - -c
    - config.yaml
    - --export
```

If your repo is a Cloud Source Repository, you can also configure a trigger for
Cloud Build, so that the pipeline is run automatically when a commit is made.

Here is a Terraform example:

```hcl
resource "google_cloudbuild_trigger" "dev-trigger" {
  trigger_template {
    branch_name = "master"
    repo_name   = var.repo_name
  }

  substitutions = {
    _SLO_CONFIG_FILE = "${path.module}/slo.json"
    _ERROR_BUDGET_POLICY_FILE = "${path.module}/error_budget_policy.json"
  }

  filename = "cloudbuild.yaml"
}

resource "google_cloudbuild_trigger" "prod-trigger" {
  trigger_template {
    branch_name = "master"
    repo_name   = var.repo_name
  }

  substitutions = {
    _SLO_CONFIG_FILE = "${path.module}/slo.json"
    _ERROR_BUDGET_POLICY_FILE = "${path.module}/error_budget_policy.json"
  }

  filename = "cloudbuild.yaml"
}
```
