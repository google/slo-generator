# Deploy SLO Generator in a Cloud Build pipeline

`slo-generator` can also be triggered in a Cloud Build pipeline. This can be useful if we want to compute some SLOs as part of a release process (e.g: to calculate a metric on each `git` commit or push)

To do so, you need to build an image for the `slo-generator` and push it to `Google Container Registry` in your project.

To build and push the image, run:

```sh
git clone https://github.com/google/slo-generator
cd slo-generator/
gcloud config set project <PROJECT_ID>
gcloud builds submit --tag gcr.io/<PROJECT_ID>/slo-generator .
```

Once the image is built, you can call the SLO generator using the following snippet in your `cloudbuild.yaml`:

```yaml
---
steps:

- name: gcr.io/${_PROJECT_NAME}/slo-generator
  args:
    - -f
    - ${_SLO_CONFIG_FILE}
    - -b
    - ${_ERROR_BUDGET_POLICY_FILE}
    - --export
```

Then, in another repo containing your SLO definitions, simply run the pipeline, substituting the needed variables:

```sh
gcloud builds submit . --config=cloudbuild.yaml --substitutions \
  _SLO_CONFIG_FILE=<YOUR_SLO_CONFIG_FILE> \
  _ERROR_BUDGET_POLICY_FILE=<_ERROR_BUDGET_POLICY_FILE> \
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
