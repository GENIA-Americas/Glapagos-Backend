import boto3

def aws_ssm_parameter_serialize(path, param):
    name = param['Name'].replace(path, '')
    if param['Type'] == 'String':
        return name, param['Value']
    if param['Type'] == 'StringList':
        return name, param['Value'].split(',')
    if param['Type'] == 'SecureString':
        print('AWS SSM PARAMETER STORE SecureString variables serialization not implemented yet')
        return name, param['Value']
    
def get_params_batch_from_ssm(client, path, parameter_names):
    response = client.get_parameters(
        Names=[path+param_name for param_name in parameter_names],
        WithDecryption=False
    )

    params = {}
    for param in response['Parameters']:
        name, value = aws_ssm_parameter_serialize(path, param)
        params[name] = value
    return params

def get_params_from_ssm(path, parameter_names, region):
    client = boto3.client('ssm', region_name=region)
    params = dict()
    for offest in range(0, len(parameter_names), 10):
        new_params = get_params_batch_from_ssm(client,path, parameter_names[offest:offest+10])
        params.update(new_params)
    return params
