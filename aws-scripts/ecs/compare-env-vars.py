import boto3
import os

class ScriptConfig:
    lower_env_cluster = os.getenv('LOWER_ECS_CLUSTER_NAME')
    lower_env_serv = os.getenv('LOWER_ECS_SERVICE_NAME')
    target_env_serv = os.getenv('TARGET_ECS_SERVICE_NAME')
    target_env_cluster = os.getenv('TARGET_ECS_CLUSTER_NAME')
    target_ak = os.getenv('TARGET_ACCESS_KEY')
    target_sec = os.getenv('TARGET_SECRET')
    lower_ak = os.getenv('LOWER_ACCESS_KEY')
    lower_sec = os.getenv('LOWER_SECRET')

def load_params():
    return ScriptConfig()

def describe_service(cluster, service, c):
    response = c.describe_services(
        cluster=str(cluster),
        services=[
            str(service),
        ]
    )
    return response

def describe_tdef(taskDef, cl):
    response = cl.describe_task_definition(
        taskDefinition=str(taskDef)
    )
    return response

def log(m):
  print(m)


def compare_env_vars(lower_envvars, target_envvars):
    missing = []
    for dict_env in lower_envvars:
        n = dict_env['name']
        # Does it exist in the target env?
        found_match = False
        for targ_env in target_envvars:
           if targ_env['name'] == n:
               log('Found env var: {}'.format(targ_env['name']))
               found_match = True

    
        if found_match is False:
            log('[!!] Found missing environment variable: {}'.format(n))
            missing.append(n)

    return missing

# get current task definition of previous environment
def get_tdef_for_service(cluster, service, cl, tol_flag):
    services = describe_service(
        cluster,
        service,
        cl
    )

    # get task definition of currently active task def
    print('{} environment\'s task def. Service: {} Cluster: {}'.format(tol_flag, service, cluster))
    tDef = services.get('services', None)[0]['taskDefinition']

    # describe task def
    tdef_details = describe_tdef(
        taskDef=tDef,
        cl=cl
    )

    if tdef_details is not None:
        log('Successfully described task def for {} environment.'.format(tol_flag))
        return tdef_details

    log('Failed to describe task def.')
    exit(1)

# ------------ [Code Execution Begins] ---------------- #

# Load configuration environment variables into an object
params = load_params()

# Lower environment ECS client
l_cl = boto3.client(
    'ecs',
    aws_access_key_id=params.lower_ak,
    aws_secret_access_key=params.lower_sec
    )

# Target environment ECS client
t_cl = boto3.client(
    'ecs',
    aws_access_key_id=params.target_ak,
    aws_secret_access_key=params.target_sec
)

# Describe the lower environment's ECS service
l_tdef_details = get_tdef_for_service(
    params.lower_env_cluster,
    params.lower_env_serv,
    l_cl, 'Lower'
)

#print(l_tdef_details)
l_env_vars = l_tdef_details['taskDefinition']['containerDefinitions'][0]['environment']

# Describe the target environment
t_tdef_details = get_tdef_for_service(
    params.target_env_cluster or 'nebula-qa',
    params.target_env_serv or 'nebula-retina',
    t_cl, 'Target'
)

# Extract environment variables from target environment ENV vars.
t_env_vars = t_tdef_details['taskDefinition']['containerDefinitions'][0]['environment']

# Convert keys to lower case for robust comparison.
for i in t_env_vars:
    i['name'] = i['name'].lower()

for i in l_env_vars:
    i['name'] = i['name'].lower()

#log('Environment variables of lower environment: {}'.format(l_env_vars))
#log('Environment variables of target (deploy) environment: {}'.format(t_env_vars))

missing_env_vars = compare_env_vars(
    l_env_vars,
    t_env_vars
)

if len(missing_env_vars) > 0 :
    message = '\n'.join('%s' % (key) for key in missing_env_vars)
    log('\n\n[ERROR] Found missing environment variables: \n{}'.format(message))    
    exit(1)

log('SUCCESS! No environment variables exist in {}/{} but not in {}/{}.'.format(params.lower_env_cluster, params.lower_env_serv, params.target_env_cluster,params.target_env_serv))
