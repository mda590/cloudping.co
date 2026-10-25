# CI setup

## What runs where today

| Service | How it deploys |
|---|---|
| `cloudping-frontend-njs` | AWS App Runner, auto-deploys on any push to `main` that touches it. Already automated, no workflow needed. |
| `cloudping-api`, `scheduled_functions`, `ping_from_region`, `ping-function-deployer`, `account-region-manager` | `deploy-chalice.yml` — on a push to `main` touching the service, or `workflow_dispatch` for one service or all. `chalice deploy --stage prod` by hand still works; mind the Python version. |
| `*-eusc` services | Manual only. See "Why EUSC is excluded". |

## AWS setup (done)

The provider, role and policy below already exist in account `506666621600`.
This section records what was created and why it is scoped the way it is;
there is nothing to run unless you are rebuilding it.

| Resource | Name |
| --- | --- |
| OIDC provider | `token.actions.githubusercontent.com` |
| Role | `cloudping-github-deploy` |
| Policy | `cloudping-github-deploy-policy` (customer managed, attached) |
| Repo secret | `AWS_DEPLOY_ROLE_ARN` |

### Trust

Only workflows running on this repo's `main` can assume the role:

```json
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
    "token.actions.githubusercontent.com:sub": "repo:mda590/cloudping.co:ref:refs/heads/main"
  }
}
```

A workflow on a branch, a tag, or a fork's pull request gets a different `sub`
and cannot assume it. Widening this to `ref:refs/heads/*` or `*` would hand the
permissions below to anyone who can push a branch — don't.

### Permissions

Scoped per service rather than by a shared `*-prod-*` wildcard. That wildcard
is tempting and wrong: this account also contains `CloudFix-prod-*` (four roles
belonging to a third-party cost tool), `twitter-followers-prod-*` and
`cloudping-scheduled-calculations-prod-*`, none of which this repo deploys. The
same goes for `events:*` on `"*"` — the account has unrelated rules like
`StopPingInstances` — and for `apigateway:*` on `/restapis*`, since there are
14 REST APIs here and only `qq1pwh7bv4` is ours.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ManageTheseLambdaFunctionsOnly",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:GetPolicy",
        "lambda:TagResource",
        "lambda:UntagResource",
        "lambda:ListTags",
        "lambda:PublishVersion"
      ],
      "Resource": [
        "arn:aws:lambda:us-east-2:506666621600:function:cloudping-api-prod*",
        "arn:aws:lambda:us-east-2:506666621600:function:scheduled_functions-prod*",
        "arn:aws:lambda:us-east-2:506666621600:function:ping_from_region-prod*",
        "arn:aws:lambda:us-east-2:506666621600:function:ping-function-deployer-prod*",
        "arn:aws:lambda:us-east-2:506666621600:function:account-region-manager-prod*"
      ]
    },
    {
      "Sid": "ReadThePandasLayer",
      "Effect": "Allow",
      "Action": [
        "lambda:GetLayerVersion"
      ],
      "Resource": "arn:aws:lambda:us-east-2:336392948345:layer:AWSSDKPandas-Python313:*"
    },
    {
      "Sid": "ManageTheseScheduleRulesOnly",
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:DeleteRule",
        "events:DescribeRule",
        "events:PutTargets",
        "events:RemoveTargets",
        "events:ListTargetsByRule",
        "events:TagResource",
        "events:UntagResource",
        "events:ListTagsForResource"
      ],
      "Resource": [
        "arn:aws:events:us-east-2:506666621600:rule/cloudping-api-prod-*",
        "arn:aws:events:us-east-2:506666621600:rule/scheduled_functions-prod-*",
        "arn:aws:events:us-east-2:506666621600:rule/ping_from_region-prod-*",
        "arn:aws:events:us-east-2:506666621600:rule/ping-function-deployer-prod-*",
        "arn:aws:events:us-east-2:506666621600:rule/account-region-manager-prod-*"
      ]
    },
    {
      "Sid": "ManageTheCloudpingRestApiOnly",
      "Effect": "Allow",
      "Action": [
        "apigateway:GET",
        "apigateway:POST",
        "apigateway:PUT",
        "apigateway:PATCH",
        "apigateway:DELETE"
      ],
      "Resource": [
        "arn:aws:apigateway:us-east-2::/restapis/qq1pwh7bv4",
        "arn:aws:apigateway:us-east-2::/restapis/qq1pwh7bv4/*"
      ]
    },
    {
      "Sid": "ManageTheseLambdaExecutionRolesOnly",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:GetRole",
        "iam:TagRole",
        "iam:PutRolePolicy",
        "iam:GetRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:ListRolePolicies",
        "iam:UpdateAssumeRolePolicy"
      ],
      "Resource": [
        "arn:aws:iam::506666621600:role/cloudping-api-prod-*",
        "arn:aws:iam::506666621600:role/scheduled_functions-prod-*",
        "arn:aws:iam::506666621600:role/ping_from_region-prod-*",
        "arn:aws:iam::506666621600:role/ping-function-deployer-prod-*",
        "arn:aws:iam::506666621600:role/account-region-manager-prod-*"
      ]
    },
    {
      "Sid": "PassThoseRolesToLambdaOnly",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::506666621600:role/cloudping-api-prod-*",
        "arn:aws:iam::506666621600:role/scheduled_functions-prod-*",
        "arn:aws:iam::506666621600:role/ping_from_region-prod-*",
        "arn:aws:iam::506666621600:role/ping-function-deployer-prod-*",
        "arn:aws:iam::506666621600:role/account-region-manager-prod-*"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "lambda.amazonaws.com"
        }
      }
    }
  ]
}
```

Verified by expanding each pattern against the live account: 8 Lambda
functions, 8 IAM roles and 6 EventBridge rules are in scope, and every
unrelated `-prod-` resource is out. Spot-checked with
`aws iam simulate-principal-policy`, which returns `implicitDeny` for
`iam:PutRolePolicy` on a CloudFix role, `lambda:UpdateFunctionCode` on
`twitter-followers`, `apigateway:DELETE` on another API, `events:DeleteRule` on
`StopPingInstances`, `dynamodb:DeleteTable` on `PingTest`, and `iam:CreateUser`.

### Residual risk

`iam:PutRolePolicy` + `iam:PassRole` still means anyone who can merge to `main`
can give one of the eight cloudping Lambda roles an arbitrary inline policy and
invoke it. The scoping above bounds *which* roles, not what policy they can be
given, so treat merge access to `main` as close to admin on this account.

Two things narrow it. `iam:AttachRolePolicy` is deliberately **not** granted, so
no managed policy — `AdministratorAccess` included — can be attached; Chalice
only writes inline policies, so it does not need it. And `iam:PassRole` is
conditioned on `iam:PassedToService: lambda.amazonaws.com`, so these roles
cannot be handed to EC2 or anything else.

Closing it properly means putting a permissions boundary on the eight Lambda
roles, so an over-broad inline policy has no effect. Chalice's `create_role`
does not set one, so a new function would need the boundary attached by hand
afterwards. Worth doing; not done here, because it changes eight live
production roles and that deserves its own change.

### Rebuilding it

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com

aws iam create-role --role-name cloudping-github-deploy \
  --assume-role-policy-document file://trust-policy.json

aws iam create-policy --policy-name cloudping-github-deploy-policy \
  --policy-document file://deploy-policy.json
aws iam attach-role-policy --role-name cloudping-github-deploy \
  --policy-arn arn:aws:iam::506666621600:policy/cloudping-github-deploy-policy

gh secret set AWS_DEPLOY_ROLE_ARN \
  --body arn:aws:iam::506666621600:role/cloudping-github-deploy
```

To revoke access in a hurry, detach the policy — that leaves the audit trail
intact, unlike deleting the role:

```bash
aws iam detach-role-policy --role-name cloudping-github-deploy \
  --policy-arn arn:aws:iam::506666621600:policy/cloudping-github-deploy-policy
```

## Why the workflow pushes a commit

Chalice keeps the identity of everything it deployed in
`.chalice/deployed/prod.json` — Lambda ARNs, the IAM role names, and for
`cloudping-api` the REST API id. That file is committed to this repo, and
Chalice rewrites it after every deploy.

If a deploy runs without the current file, Chalice does not recognise the
existing resources and creates new ones. For `cloudping-api` that means a new
REST API id, while `api.cloudping.co` stays base-path-mapped to the old one
(`qq1pwh7bv4`, stage `v1`). The deploy reports success and production quietly
serves the old code. The workflow therefore commits the file back with
`[skip ci]`, and fails loudly if the REST API id changes.

This is the known rough edge of `chalice deploy` in CI. The alternative is
`chalice package` plus CloudFormation, which is stateless — but
[the Chalice docs are explicit](https://aws.github.io/chalice/topics/cfn.html)
that the switch is one-way, and it would create a new REST API, so
`api.cloudping.co` would need repointing. Not worth it just to get CI.

## Why EUSC is excluded

The `*-eusc` services deploy into account `075395615672` in the `aws-eusc`
partition, which has no GitHub OIDC provider. GitHub-hosted runners also sit
outside the EU sovereign boundary, which may matter more than the convenience.
Deploy those by hand with the `eusc` profile:

```bash
cd store-region-status-eusc && AWS_PROFILE=eusc chalice deploy --stage prod
```

## Python version

Chalice builds the deployment package with whatever interpreter it runs under,
and that is what sets the function's Lambda runtime. There is no config key to
override it, so the interpreter has to match per service -- and the services do
not agree:

| Service | Runtime |
| --- | --- |
| `scheduled_functions` | `python3.13` |
| `ping_from_region` | `python3.13` |
| `cloudping-api` | `python3.11` |
| `ping-function-deployer` | `python3.11` |
| `account-region-manager` | `python3.11` |

So the `SERVICE_PYTHON` map in the workflow gives each matrix entry its own
version, and the `select` job fails loudly if a service is missing from it.

Getting this wrong is quiet rather than loud: the deploy succeeds and the
function's runtime simply changes. For `scheduled_functions` that also orphans
the `AWSSDKPandas-Python313` layer, so `numpy`/`pandas` stop importing and
`calculate_avgs` fails on its next cron rather than during the deploy.

The same trap applies to deploying from a laptop. Check before you do:

```bash
aws lambda list-functions --region us-east-2 \
  --query 'Functions[].[FunctionName,Runtime]' --output text
chalice --version   # reports the Python it is running under
```

If the local Python does not match, `uv` can fetch the right one without
touching the system install:

```bash
uv venv --python 3.13 /tmp/venv313
uv pip install --python /tmp/venv313/bin/python chalice==1.32.0 boto3
cd scheduled_functions && /tmp/venv313/bin/chalice deploy --stage prod
```

## Build-time imports

Every service's `requirements.txt` is empty, and should stay that way: `boto3`
ships with the Lambda runtime and `numpy` comes from the `AWSSDKPandas-Python313`
layer, so pinning either would vendor a second copy into the deployment package
— and for `scheduled_functions` that copy would shadow the layer's.

But `chalice deploy` imports `app.py` to discover the routes and schedules
before it builds anything, so every module-scope import still has to resolve on
the runner. With an empty `requirements.txt` and nothing else installed, the
deploy dies before it starts:

```
File "account-region-manager/app.py", line 2, in <module>
    import boto3
ModuleNotFoundError: No module named 'boto3'
```

`scheduled_functions` needs `numpy` as well, because `app.py` imports
`chalicelib.calculate_avgs`, which imports it at module scope.

The `SERVICE_BUILD_DEPS` map in the workflow installs these per service.
They are build-time only and never reach production: `chalice` builds the zip
from `requirements.txt` alone, not from what happens to be installed. Verified
by packaging `scheduled_functions` from a clean checkout with both installed —
the resulting zip is 64K and contains only `app.py`, `chalice/` and
`chalicelib/`, with no `boto3`, `botocore`, `numpy` or `pandas` files.

The same applies to deploying by hand: install `boto3` (and `numpy` for
`scheduled_functions`) into the venv you run `chalice` from.
