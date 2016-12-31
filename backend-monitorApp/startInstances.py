import boto3

def lambda_handler(event, context):
    
    # ca-central-1
    instances = ['i-0caf6a63d4864408f']
    ec2 = boto3.client('ec2', region_name='ca-central-1')
    ec2.start_instances(InstanceIds=instances)
    print 'started the ca-central-1 pingTest instance: ' + str(instances)
    
    # ap-south-1
    instances = ['i-064799163a45c92e7']
    ec2 = boto3.client('ec2', region_name='ap-south-1')
    ec2.start_instances(InstanceIds=instances)
    print 'started the ap-south-1 pingTest instance: ' + str(instances)
    
    # sa-east-1
    instances = ['i-0d11e9033017e5948']
    ec2 = boto3.client('ec2', region_name='sa-east-1')
    ec2.start_instances(InstanceIds=instances)
    print 'started the sa-east-1 pingTest instance: ' + str(instances)
    
    # eu-west-2
    instances = ['i-02b5c53033335ac8a']
    ec2 = boto3.client('ec2', region_name='eu-west-2')
    ec2.start_instances(InstanceIds=instances)
    print 'started the eu-west-2 pingTest instance: ' + str(instances)
