# GuardDuty to Teams

## Description
Automatically send an alert to Microsoft Teams when an alert is created by GuardDuty.

## Environment Variables
| Variable | Description | Default Value |
| -------- | ----------- | ------------- |
| api_url | The URL to send the Teams message to | None |
| severity_threshold | The threshold an event must exceed in order to get sent | 2.0 |

Note that the event severity must be GREATER THAN the severity threshold, so by default this does not alert on "low" severity findings.

## Installation (AWS)
Because this lambda function is sending messages to a web endpoint, you will need to configure a VPC with various subnets, a NAT, and an Internet Gateway to allow it to talk to the outside world.  If you need some instructions on how to do this until I get some automation setup follow these, https://gist.github.com/reggi/dc5f2620b7b4f515e68e46255ac042a7

In order to get events flowing from GuardDuty to the Lambda function you will also need to configure CloudWatch manually with the following commads via the awscli (originally documented [here](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty-ug.pdf))

```bash
aws events put-rule --name <CLOUD WATCH EVENT NAME> --event-pattern '{"source": ["aws.guardduty"]}'
aws events put-targets --rule <CLOUD WATCH EVENT NAME> --targets Id=1,Arn=arn:aws:lambda:us-east-1:<AWS ACCOUNT NUMBER>:function:<LAMBDA FUNCTION>
aws lambda add-permission --function-name <LAMBDA FUNCTION> --statement-id 1 --action 'lambda:InvokeFunction' --principal events.amazonaws.com
```
Just make sure to fill in \<CLOUD WATCH EVENT NAME>, \<AWS ACCOUNT NUMBER>, and \<LAMBDA FUNCTION>.

Cloud Formation: Coming Soon

## Installation (Microsoft Teams)
In order to get this to work with teams you will need to configure a "connector" on the channel you want the messages to end up in.  Int his case you will be doing an "Incoming Webhook" connector where you can give it a name and avatar image, then after you create it, you will get a webhook URL to send the messages to.  Keep this secure as while it doesn't allow reading messages from your chat it would allow nefarious users to spam your chat with whatever they wanted.  This will go into the api_url environment variable.

## Sample Alert:
![Sample Alert](alert.png)