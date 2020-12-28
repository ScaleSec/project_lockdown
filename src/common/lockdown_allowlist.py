from os import getenv

def check_allowlist(project_id):
    """
    This shared function compares the project ID passed in via the Cloud Function
    against a list of projects the user sets (if applicable).
    If the project exists in the allowlist, no action is taken by project lockdown. 
    If the project does not exist, the function continues with the evaluation logic.

    ## Example ##
    If a user creates a public GCS bucket (public_gcs_bucket CFN), but the project ID
    is in the allowlist - the GCS bucket stays public (aka no action is taken to revert)

    The allowlist is passed in as a string that can have multiple values separated by a comma.
    This is due to bash only allowing key/value pairs for environment variables.
    We use the comma delimeter to create a list and then iterate over that list for the project_id.

    ## Args ##
    project_id - passed in via the calling function. Used to check the allowlist.
    """


    allowlist = getenv('ALLOWLIST', default="False")

    allowlist = allowlist.split(",")

    if allowlist == "False":
        return False
    else:
        if project_id in allowlist:
            return True
