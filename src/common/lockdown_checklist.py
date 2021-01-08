from os import getenv

def check_list(project_id):
    """
    This shared function compares the project ID passed in via the Cloud Function
    against a list of projects the user sets (if applicable).

    ## Evaluation Logic ##
    If the project exists in the allowlist, no action is taken by project lockdown. 
    If the project does not exist, the function continues with the evaluation logic.

    If the project exists in the denylist, the function continues with the evaluation logic. 
    If the project does not exist, no action is taken by project lockdown.

    If a project list or list type is not set (N/A), project lockdown continues with its evaluation logic,
    because neither a deny or an allowlist is a requirement.

    ## Example ##
    If a user creates a public GCS bucket (public_gcs_bucket CFN), but the project ID
    is in the allowlist - the GCS bucket stays public (aka no action is taken to revert)

    The project list is passed in as a string that can have multiple values separated by a comma.
    This is due to bash only allowing key/value pairs for environment variables.
    We use the comma delimeter to create a list and then iterate over that list for the project_id.

    ## Args ##
    project_id - passed in via the calling function. Used to check the allowlist.
    """

    
    project_list = getenv('PROJECT_LIST', default="N/A")
    # Creates a list with each project
    projects = project_list.split(",")

    # Get the list type from the function's environment variables
    list_type = getenv('LIST_TYPE', default="N/A")

    ##################################################################################
    ## Anything that returns "False" below will exit the Function                   ## 
    ## Lockdown does not require an allowlist or denylist so we return True         ##
    ##################################################################################

    # If a project list is not set we return True to evaluate the resource
    if project_list == "N/A":
        return True
    
    # If a list type is not set we return True to evaluate the resource
    if list_type == "N/A":
        return True
    # If a list type of allow is set (means allowlist)
    elif list_type == "allow":
        # If a project is in a allowlist, we do not want to evaluate the resource
        if project_id in projects:
            return False
        # If the project specified is not in the allowlist
        # and an allowlist exists, we want to evaluate the resource
        else:
            return True
    # The logic below is inverted compared to the allowlist
    # If a list type of deny is set (means denylist)
    elif list_type == "deny":
        # If a project is in a denylist, we want to evaluate the resource
        if project_id in projects:
            return True
        # If the project is not in the denylist,
        # and a denylist is set, we do not evaluate
        else:
            return False