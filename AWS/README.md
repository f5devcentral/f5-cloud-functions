# AWS

AWS Lambda functions are in the folders below this to help maintain an AWS account.  They should have their own documentation but here is high level documentation on all of them.

* [AMI_Prune](AMI_Prune): Automatically prune all AMIs older than x days that do not have a keep flag.
* [GuardDutyToTeams](GuardDutyToTeams): Send a message to Microsoft Teams when an event over a certain severity threshold is detected by GuardDuty.