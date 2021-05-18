# Migrating `slo-generator` to the next major version

## v1 to v2

Version `v2` of the slo-generator introduces some changes to the structure of 
the SLO configurations.

To migrate your SLO configurations from v1 to v3, please execute the following 
instructions:

**Upgrade `slo-generator`:**
```
pip3 install slo-generator -U # upgrades slo-generator version to the latest version
```

**Run the `slo-generator-migrate` command:**
```
slo-generator-migrate -s <SOURCE_FOLDER> -t <TARGET_FOLDER> -b <ERROR_BUDGET_POLICY_PATH>
```
where:
* <SOURCE_FOLDER> is the source folder containg SLO configurations in v1 format. 
This folder can have nested subfolders containing SLOs. The subfolder structure 
will be reproduced on the target folder.

* <TARGET_FOLDER> is the target folder to drop the SLO configurations in v2
format. If the target folder is identical to the source folder, the existing SLO 
configurations will be updated in-place.

* <ERROR_BUDGET_POLICY_PATH> is the path to your error budget policy configuration.

**Follow the instructions printed to finish the migration:**
This includes committing the resulting files to git and updating your Terraform
modules to the version that supports the v2 configuration format.
