


## Create the EKS cluster

There are many ways to create a cluster and which specific one to use depends on specifications that are outside of the generic scope.

This is a good starting point: https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html. 
In doubt, [Auto Mode Cluster](https://docs.aws.amazon.com/eks/latest/userguide/getting-started-automode.html) is a good place to start.

## Ingress setup

The following is inspired by https://aws.amazon.com/blogs/containers/exposing-kubernetes-applications-part-3-nginx-ingress-controller/, section "Exposing Ingress-Nginx Controller via a Load Balancer".
Be aware that the article is from 2022 and it doesn't work 100%. 
Following the steps that worked for us on May 2025

### Setup the policy and service account

Note that have to pay attention to the version of the aws-load-balancer-controller to match with the policy. Wrong version will make things fail

```bash
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json
aws iam create-policy     --policy-name AWSLoadBalancerControllerIAMPolicy     --policy-document file://iam-policy.json
AWS_ACCOUNT=123456789 # Your AWS account
eksctl create iamserviceaccount \
    --cluster=metacell-dev \
    --name=aws-load-balancer-controller \
    --namespace=kube-system \
    --attach-policy-arn=arn:aws:iam::${AWS_ACCOUNT}:policy/AWSLoadBalancerControllerIAMPolicy \
    --approve
```

### Install the aws-load-balancer-controller 

First, apply custom resource definition
```bash
wget https://raw.githubusercontent.com/aws/eks-charts/refs/heads/master/stable/aws-load-balancer-controller/crds/crds.yaml
kubectl apply -f crds.yaml
```

Then install the helm chart
From https://github.com/aws/eks-charts/tree/master/stable/aws-load-balancer-controller
```bash
helm repo add eks https://aws.github.io/eks-charts
# If using IAM Roles for service account install as follows -  NOTE: you need to specify both of the chart values `serviceAccount.create=false` and `serviceAccount.name=aws-load-balancer-controller`
helm install aws-load-balancer-controller eks/aws-load-balancer-controller --set clusterName=metacell-dev -n kube-system --set serviceAccount.create=false --set serviceAccount.name=aws-load-balancer-controller
```


### Fix  vpc

If encounter the following error related to vpc

> {"level":"info","ts":"2025-05-21T13:53:48Z","msg":"version","GitVersion":"v2.13.2","GitCommit":"4236bd7928711874ae4d8aff6b97870b5625140f","BuildDate":"2025-05-15T17:37:55+0000"}
> {"level":"error","ts":"2025-05-21T13:53:53Z","logger":"setup","msg":"unable to initialize AWS cloud","error":"failed to get VPC ID: failed to fetch VPC ID from instance metadata: error in fetching vpc id through ec2 metadata: get mac metadata: operation error ec2imds: GetMetadata, canceled, context deadline exceeded"}

First get the vpc id:

```bash
aws eks describe-cluster \
  --name metacell-dev \
  --region us-west-2 \
  --query "cluster.resourcesVpcConfig.vpcId" \
  --output text
```

Then fix the vpc id value
```bash
helm upgrade aws-load-balancer-controller eks/aws-load-balancer-controller   -n kube-system   --reuse-values   --set vpcId=$VPC_ID
```

### Install ingress nginx

```bash
helm upgrade -i ingress-nginx ingress-nginx/ingress-nginx \
    --namespace kube-system \
    --values ingress/values-aws.yaml
    
kubectl -n kube-system rollout status deployment ingress-nginx-controller

kubectl get deployment -n kube-system ingress-nginx-controller
```

### Associate the DNS

The endpoint can be assigned with 2 CNAME entries.
For instance, if you run `harness-deployment ... -d myapp.mydomain.com`,
the following CNAME entries are needed
- myapp [LB_ADDRESS]
- *.myapp [LB_ADDRESS]


The easiest way to get the load balancer addressis to do the deployment and 
from the ingress with

```
kubectl get ingress
```

## Storage class

EKS does not provide a default storage class.
To create one, run 

```bash
kubectl apply -f storageclass-default-aws.yaml
```

## Container registry 

CloudHarness pushes images on a container registry, which has to be readable from EKS

Any public registry can be used seamlessly, while ECR is recommended to pull private images

1. Create a new ECR registry
2. Create all the repositories within the deployment (ECR does not create repositories automatically on push, unless this is implemented https://aws.amazon.com/blogs/containers/dynamically-create-repositories-upon-image-push-to-amazon-ecr/)
3. Give the permissions to the Node IAM role
https://docs.aws.amazon.com/AmazonECR/latest/userguide/ECR_on_EKS.html (the role should be AmazonSSMRoleForInstancesQuickSetup for Auto Mode Clusters)

To push images, have to authenticate to the registry. 

To authenticate from the local console, the command looks like the following:

```bash
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 527966638683.dkr.ecr.us-west-2.amazonaws.com
```

The exact command can also be viewed by hitting "View push commands" from the web console.