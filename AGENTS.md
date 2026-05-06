All files in this repository should follow the coding standards outlined in this document.

Terraform is the IaC tool used for this migration project. Terraform code should be written in HCL and organized with reusable modules plus per-environment root configurations.

Preferred coding language for all Lambda functions is Python 3.12.

The source CloudFormation project is located at ../uni-portal and should remain unchanged unless explicitly requested.

The project documents for this Terraform migration are located at ./project-doc/*.
The migration stories to be used for implementation are in ./Development.md.
All other md files can only be located in ./reference-materials/*.md.

Each story to be implemented with all its details will have its own md file in ./reference-materials/<story-name>.md.
The Development.md file will have the list of migration stories to be implemented on a high level with links to the corresponding md files in the reference-materials folder.
