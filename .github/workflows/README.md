# CI setup

## What runs where today

| Service | How it deploys |
|---|---|
| `cloudping-frontend-njs` | AWS App Runner, auto-deploys on any push to `main` that touches it. Already automated, no workflow needed. |
| `cloudping-api`, `scheduled_functions`, `ping_from_region`, `ping-function-deployer`, `account-region-manager` | `deploy-chalice.yml`, once the role below exists. Until then, `chalice deploy --stage prod` by hand. |
| `*-eusc` services | Manual only. See "Why EUSC is excluded". |

## One-time AWS setup

`deploy-chalice.yml` authenticates with GitHub's OIDC provider, so there are no
long-lived keys in GitHub. Neither the provider nor the role exists yet.

### 1. Register GitHub as an OIDC provider

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com
```

### 2. Create the deploy role

`trust-policy.json`, scoped so only workflows running on `main` can assume it:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::506666621600:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "repo:mda590/cloudping.co:ref:refs/heads/main"
      }
    }
  }]
}
```

```bash
aws iam create-role \
  --role-name cloudping-github-deploy \
  --assume-role-policy-document file://trust-policy.json
```

### 3. Attach deploy permissions

Chalice creates and updates the Lambda functions, their IAM roles, the
EventBridge schedules and the REST API, so the role needs all of it:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction", "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration", "lambda:GetFunction",
        "lambda:GetFunctionConfiguration", "lambda:AddPermission",
        "lambda:RemovePermission", "lambda:GetPolicy",
        "lambda:TagResource", "lambda:ListTags", "lambda:PublishVersion"
      ],
      "Resource": "arn:aws:lambda:us-east-2:506666621600:function:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "events:PutRule", "events:PutTargets", "events:DescribeRule",
        "events:ListTargetsByRule", "events:ListRules",
        "events:RemoveTargets", "events:DeleteRule", "events:TagResource"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "apigateway:*",
      "Resource": "arn:aws:apigateway:us-east-2::/restapis*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole", "iam:GetRole", "iam:PutRolePolicy",
        "iam:GetRolePolicy", "iam:DeleteRolePolicy",
        "iam:ListRolePolicies", "iam:UpdateAssumeRolePolicy", "iam:TagRole"
      ],
      "Resource": "arn:aws:iam::506666621600:role/*-prod-*"
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::506666621600:role/*-prod-*"
    }
  ]
}
```

**This role is close to administrative.** `iam:CreateRole` plus
`iam:PutRolePolicy` plus `iam:PassRole` lets its holder build a role with any
permissions and hand it to a Lambda. The resource patterns above narrow it to
`*-prod-*` role names, and the trust policy narrows it to this repo's `main`
branch, but anyone who can merge to `main` can effectively reach these
permissions. That is the trade for not running deploys from a laptop; decide
with that in mind.

### 4. Store the role ARN

```bash
gh secret set AWS_DEPLOY_ROLE_ARN \
  --body arn:aws:iam::506666621600:role/cloudping-github-deploy
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
