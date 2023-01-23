# ccaisWebsiteTools

Tools for the CCAIS website.

## Orchestrate

Runs the update script targeting the specified website repository. Publications are updated and the resulting publist.yml is pushed to remote.

For intervention-free updates, git should be configured for push/pull without intervention (e.g. use SSH keys).

Repository publist path: `_data/publist.yml`

Logfile: `orchestration.log`

### Usage

`python orchestrate.py <path_to_repository>`

## Update Project Publications

Create a list of publications in a YML format for website from Pure API.

### Usage
Run within the university network (such as by connecting to the VPN).

`python update_project_publications.py <optional: output_file.yml>`

If no output file is specified the output is written to stdout, otherwise it is written to the specified file (overwrites without warning).
