#Importing all required modules
import git
from jenkins import Jenkins
import time
import subprocess
import getpass
import argparse
import xml.etree.ElementTree as ET
import sys
import platform
import os
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#identifying the release version
parser = argparse.ArgumentParser()

parser.add_argument('--major', action='store_true')
parser.add_argument('--minor', action='store_true')
parser.add_argument('--patch', action='store_true')
parser.add_argument('--test', action='store_true')

args = parser.parse_args()

release_version = "major"
if(args.minor):
    release_version = "minor"
elif(args.patch):
    release_version = "patch"
elif(args.test):
    release_version = "test"
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#Defining all required helper functions
#Validating config.xml file sdata
def validating_config_data(tag_str, tag_out):
    if tag_out == None:
        print(f"Your {tag_str} tag value is not set. Please check you config.xml file.")
        print("Exiting program...\nExited.")
        sys.exit()

#Cleaning workspace and exiting
def clean_workspace_and_exit(error_msg, Linux):
    if (error_msg != ""):
        print(error_msg)
    print("Cleaning workspace...")

    if Linux:
        subprocess.run("rm -rf workspace", shell=True)
    else:
        subprocess.run("rmdir /Q /S workspace", shell=True)

    print("Exiting program...\nExited.")
    sys.exit()

#Print and exit
def print_and_exit(msg):
    print(msg)
    sys.exit()

#Input y or n
def input_y_or_n(msg):
    provided_input = input(msg)

    while (provided_input.lower() != 'y' and provided_input.lower() != 'n'):
        print("Invalid input")
        provided_input = input(msg)

    return provided_input


#Input y or n or q
def input_y_or_n_or_q(msg):
    provided_input = input(msg)

    while (provided_input.lower() != 'y' and provided_input.lower() != 'n' and provided_input.lower() != 'q'):
        print("Invalid input. ")
        provided_input = input(msg)

    return provided_input

#gives path name assording to underlying os
# def path_name(path):
#     if(True):
#         path = path.split("\\")
#         return_path = ''
#         for str in path:
#             return_path += str + '/'
#
#         return return_path
#
#     else:
#         return path
#---------------------------------------------------------------------------------------------------------------------------------------------------------------
#Checking the underlying OS
Linux = (platform.platform().lower().find('linux') == 0)

# Checking system requirements
print("Checking system requirements...")

# Maven installed or not
maven_status_code = (subprocess.run('mvn --version', shell=True, capture_output=True)).returncode
if (maven_status_code != 0):
    print_and_exit(
        "Systems requirements not met, maven is not installed, please install it.\nExiting program...\nExited")
else:
    print("System requirement met: maven is installed.")

# Git installed or not
git_status_code = (subprocess.run('git --version', shell=True, capture_output=True)).returncode
if (git_status_code != 0):
    print_and_exit("Systems requirements not met, git is not installed, please install it.\nExiting program...\nExited")
else:
    print("System requirement met: git is installed.")

# MATLAB on path or not
#checking underlying platform
if(Linux):
    matlab_status_code = (subprocess.run('which matlab', shell=True, capture_output=True)).returncode
else:
    matlab_status_code = (subprocess.run('where matlab', shell=True, capture_output=True)).returncode

if (matlab_status_code == 0):
    print_and_exit(
        "Systems requirements not met, you have MATLAB on your path, please remove it.\nExiting program...\nExited.")
else:
    print("System requirement met: MATLAB is not on path.")

print("All system requirements successfully met.")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

# Checking if workspace folder is on path or not
workspace_folder_on_path = subprocess.os.path.isdir("workspace")

if (workspace_folder_on_path):
    print("You have a directory named workspace in your path. This file will be deleted before proceeding.")
    proceed_or_not = input_y_or_n("Enter Y to proceed or N to exit program: ")

    if (proceed_or_not == 'y'):
        print("Removing workspace directory...")
        #subprocess.run("rmdir /Q /S workspace", shell=True)
        if Linux:
            subprocess.run("rm -rf workspace", shell=True)
        else:
            subprocess.run("rmdir /Q /S workspace", shell=True)

    else:
        print("Exiting program...\nExited.")
        sys.exit()
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#Checking for config file
print("Checking for config.xml file...")
config_file_present = subprocess.os.path.isfile("config.xml")
if(not(config_file_present)):
    print_and_exit("Config.xml file not present on path. Please inclue it.\nExiting program...\nExited.")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#Parsing config file
print("Parsing config.xml file...")
myTree = ET.parse("config.xml")
myroot = myTree.getroot()

#Parsing pre-release part
sourceGithub_url = myroot.find("preRelease").find("sourceGithub").find("url").text
validating_config_data("sourceGithub url", sourceGithub_url)

targetGithub_url = myroot.find("preRelease").find("targetGithub").find("url").text
validating_config_data("targetGithub url", targetGithub_url)

jenkinsServer_url = myroot.find("preRelease").find("jenkinsServer").find("url").text
validating_config_data("jenkinsServer url", jenkinsServer_url)

jenkinsServer_username = myroot.find("preRelease").find("jenkinsServer").find("userName").text
validating_config_data("jenkinsServer username", jenkinsServer_username)

jenkinsServer_password = myroot.find("preRelease").find("jenkinsServer").find("password").text
validating_config_data("jenkinsServer password", jenkinsServer_password)

jenkinsServer_projectName = myroot.find("preRelease").find("jenkinsServer").find("projectName").text
validating_config_data("jenkinsServer projectName", jenkinsServer_projectName)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#cloning origional repo
print("Cloning matlab repo...")

try:
    matlab_repo = git.Repo.clone_from(sourceGithub_url, os.path.join("workspace","Matlab Repo"))
except:
    clean_workspace_and_exit(
        "Error while cloning from remote matlab (i.e.matlab github).\nPlease check you sourceGithub url tag value in your config.xml file.", Linux)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#cloning jenkins repo
print("Cloning jenkins repo...")

try:
    jenkins_repo = git.Repo.clone_from(targetGithub_url, os.path.join("workspace","Jenkins Repo"))
except:
    clean_workspace_and_exit(
        "Error while cloning from remote jenkins (i.e.jenkins github).\nPlease check you targetGithub url tag value in your config.xml file.", Linux)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

# try connecting to jenkins server
print("Connecting to jenkins server...")

try:
    J = Jenkins(jenkinsServer_url, username=jenkinsServer_username, password=jenkinsServer_password)

except:
    clean_workspace_and_exit(
        "Error while connecting to jenkins server.\nPlease check your jenkinsServer tag values in your config.xml file.", Linux)

print("Connection to jenkins server succeeded.")
# finding the project in jenkins server
try:
    J.get_job_info(jenkinsServer_projectName)
except:
    clean_workspace_and_exit(
        "Error while connecting to jenkins server.\nPlease check your jenkinsServer projectName tag values in your config.xml file.", Linux)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------
# Deleting origin
# matlab_repo.git.remote("rm", "origin")
# jenkins_repo.git.remote("rm", "origin")


# Creating remotes
print("Creating remotes for local matlab repo and local jenkins repo...")

matlabs_remote = matlab_repo.create_remote("jenkins_github", targetGithub_url)

jenkins_remote = jenkins_repo.create_remote("matlab_github", sourceGithub_url)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------
# Validating username and password
print("Credential validation...")
validate_username_password = False

# print("Scanning git config file for github username and password...")
# git_config_have_credentials = True
if Linux:
    try:
        matlab_repo.git.config("--global", "--unset-all", "credential.helper")
        matlab_repo.git.config("--system", "--unset-all", "credential.helper")
        matlab_repo.git.config("--local", "--unset-all", "credential.helper")
    except:
        print("You do not have credential.helper in your git config file.")
# matlab_repo.git.config("--global", "--add", 'credential.helper', "store")
# try:
#     # user_name = matlab_repo.git.config("--global",'--get', 'user.name')
#     # password1 = matlab_repo.git.config("--global",'--get', 'user.password')
#     # st_value = matlab_repo.git.config('--get', 'credential.helper')
#     # if(st_value != "store"):
#     #     git_config_have_credentials = False
#     #     matlab_repo.git.config("--global", "--add", 'credential.helper', "store")
#     #     print("Error while fetching credentilas from your git config file.")
# except:
#     git_config_have_credentials = False
#     # matlab_repo.git.config("--global", "--add", 'credential.helper', "store")
#     print("Error while fetching credentials from your git config file.")

# pass_path = os.path.join(os.path.abspath('.'), "workspace", ".password.txt")
# matlab_repo.git.config("--global","--add", 'credential.helper', f"store --file {pass_path}")
if Linux:
    pass_path = os.path.join(os.path.abspath('.'), "workspace", ".password.txt")
    matlab_repo.git.config("--global","--add", 'credential.helper', f"store --file {pass_path}")

while (not (validate_username_password)):

    # else:
    #     matlab_repo.git.config("--global", "--add", 'credential.helper', "manager")
    # if the git config file do not have credentilas or the provided credentials do not have push access
    # if (not (git_config_have_credentials)):
    #
    #     user_name = input("Enter github username : ")
    #
    #     password_match = False
    #     while (not (password_match)):
    #         password1 = getpass.getpass(prompt="Enter github password : ")
    #         password2 = getpass.getpass(prompt="Confirm password : ")
    #
    #         if password1 == password2:
    #             password_match = True
    #         else:
    #             print("Password Not Matching.")
    #
    #     try:
    #         print("Trying to remove all user.name from your global git config file...")
    #         matlab_repo.git.config("--global", "--unset-all", "user.name")
    #     except:
    #         print("No user.name property present in your global git config file.")
    #
    #     try:
    #         print("Trying to remove all user.password from your global git config file...")
    #         matlab_repo.git.config("--global", "--unset-all", "user.password")
    #     except:
    #         print("No user.password property present in your global git config file.")
    #
    #     print("Saving provided username and password in your global git config file...")
    #     matlab_repo.git.config("--global", "--add", 'user.name', user_name)
    #     matlab_repo.git.config("--global", "--add", 'user.password', password1)

    print("Validating credentials...")
    have_access = True

    #creating remote for both repos
    # newsourceGithub_url = sourceGithub_url.split("//")
    # newtargetGithub_url = targetGithub_url.split("//")
    #
    # newsourceGithub_url = f"{newsourceGithub_url[0]}//{user_name}:{password1}@{newsourceGithub_url[1]}"
    # newtargetGithub_url = f"{newtargetGithub_url[0]}//{user_name}:{password1}@{newtargetGithub_url[1]}"
    # print(newsourceGithub_url)
    # print(newtargetGithub_url)
    #
    # matlab_repo.git.remote("add", "origin", newsourceGithub_url)
    # jenkins_repo.git.remote("add", "origin", newtargetGithub_url)

    try:
        matlab_repo.git.push("origin", "master")

    except:
        have_access = False

    if (not (have_access)):
        print("Invalid credentials or You do not have push access to remote matlab github")

    if (have_access):
        try:
            jenkins_repo.git.push("origin", "master")

        except:
            have_access = False
            print("You do not have push access to remote jenkins github")

    if (not (have_access)):
        another_credential = input_y_or_n("Type 'Y' to provide alternate credential, or 'N' to quit: ")

        if (another_credential.lower() == 'n'):
            clean_workspace_and_exit("Failed to validate credentials.", Linux)

        else:
            git_config_have_credentials = False
            # matlab_repo.git.remote("rm", "origin")
            # jenkins_repo.git.remote("rm", "origin")

            if Linux:
                os.remove(pass_path)
                matlab_repo.git.config("--global", "--unset-all", "credential.helper")
            # try:
            #     matlab_repo.git.config("--global", "--unset-all", "credential.helper")
            #     matlab_repo.git.config("--system", "--unset-all", "credential.helper")
            #     matlab_repo.git.config("--local", "--unset-all", "credential.helper")
            # except:
            #     print("You do not have credential.helper in your git config file.")

    else:
        validate_username_password = True
        print("Successfully validated credentials.")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#Creating tags
#old_tag = str(jenkins_repo.tags[-1])
old_tag = str(jenkins_repo.git.describe("--abbrev=0"))
#print(jenkins_repo.tags)

change_tags = True

while (change_tags):
    version_arr = old_tag.split('-')[1].split('.')
    print("You have selected release version as:" + release_version)

    if (release_version != "test"):

        print("Creating tags...")
        print("Your old tag was " + old_tag)

        if (release_version == "major"):
            new_version = str(int(version_arr[0]) + 1) + ".0.0"
            new_dev_version = str(int(version_arr[0]) + 1) + ".0.1"

        elif (release_version == "minor"):
            new_version = version_arr[0] + "." + str(int(version_arr[1]) + 1) + ".0"
            new_dev_version = version_arr[0] + "." + str(int(version_arr[1]) + 1) + ".1"

        elif (release_version == "patch"):
            new_version = version_arr[0] + "." + version_arr[1] + "." + str(int(version_arr[2]) + 1)
            new_dev_version = version_arr[0] + "." + version_arr[1] + "." + str(int(version_arr[2]) + 2)

        new_tag = "matlab-" + new_version
        new_dev_version += "-SNAPSHOT"

        print(f"New release version : {new_version}")
        print(f"New release tag : {new_tag}")
        print(f"New developer version : {new_dev_version}")

    confirmation_flag = input_y_or_n_or_q("Enter 'Y' proceed, 'N' to change release version or 'Q' to quit: ")

    if (confirmation_flag == 'q'):
        clean_workspace_and_exit("process aborted...", Linux)

    elif (confirmation_flag == 'n'):
        modified_release_version = input("Enter 0 for major, 1 for minor, 2 for patch release or 3 for test: ")
        while (
                modified_release_version != '0' and modified_release_version != '1' and modified_release_version != '2' and modified_release_version != '3'):
            print("Invalid Input.")
            modified_release_version = input("Enter 0 for major, 1 for minor, 2 for patch release or 3 for test: ")

        release_version_arr = ["major", "minor", "patch", "test"]
        release_version = release_version_arr[int(modified_release_version)]

        if (release_version == "test"):
            change_tags = False

    else:
        change_tags = False
        if(release_version != "test"):
            print("Successfully Created Tags.")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

print("All requirements met successfully.")
print("Sit back and relax.\nStarting process...")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#Fetching, merging and Pushing
print("Fetching from jenkins repo's remote(i.e. matlab's github)...")
jenkins_remote.fetch()

print("Merging changes from remote matlab's github master branch to local jenkins repo's master branch...")
jenkins_repo.git.merge(jenkins_remote.refs.master)

if(release_version != "test"):
    print("Pushing changes from local jenkin's repo to remote jenkins github...")
    jenkins_repo.git.push("origin", "master")

    print("Successfully pushed changes to remote jenkins github.")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#polling to jenkins server
if(release_version != "test"):
    print("Will start polling to jenkins server in 120 seconds...")
    time.sleep(10)

    job_number = J.get_job_info("Experiment-1")['lastBuild']['number']
    job_result = J.get_build_info("Experiment-1",job_number)['result']

       #SUCCESS, FAILURE, ABORTED or None
    while job_result == None:
        print("Your build is still runnung. Next poll will be after 60 seconds...")
        time.sleep(10)
        job_result = J.get_build_info("Experiment-1",job_number)['result']
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

    # Checking Job result
    jenkins_build_fail = False

    if (job_result == "FAILURE"):
        print("Your build has FAILED. Exiting the program...")
        clean_before_exit = input_y_or_n("Enter Y to clean workspace before exit, else enter N : ")
        jenkins_build_fail = True

    elif (job_result == "ABORTED"):
        print("Your build has abruptly ABORTED. Exiting the program...")
        clean_before_exit = input_y_or_n("Enter Y to clean workspace before exit, else enter N : ")
        jenkins_build_fail = True

    else:
        print("Your build is SUCCESSFUL.")

    if (jenkins_build_fail):
        if (clean_before_exit.lower() == 'y'):
            clean_workspace_and_exit("", Linux)
        else:
            print("Exited.")
            sys.exit()
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

# Running maven test
if(release_version != "test"):
    print("Preparing to run maven test...\nRunning maven test...")
    subprocess.os.chdir(os.path.join("workspace","Jenkins Repo"))
    maven_test = subprocess.run('mvn verify', shell=True)
    maven_test_result = maven_test.returncode

    if (maven_test_result != 0):
        print('You have some failed tests.')

        print("Exiting program...")
        clean_before_exit = input_y_or_n("Enter Y to clean workspace before exit, else enter N : ")

        if (clean_before_exit.lower() == 'y'):
            subprocess.os.chdir(os.path.join("..",".."))
            clean_workspace_and_exit("", Linux)

        print("Exiting program...\nExited")
        sys.exit()

    else:
        print("Your program has successfully passed all test cases.")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

# If release version is "test"
if (release_version == "test"):
    print("Performing mvn deploy...")
    subprocess.os.chdir(os.path.join("workspace","Jenkins Repo"))
    maven_deploy = subprocess.run("mvn deploy", shell=True)
    maven_deploy_result = maven_deploy.returncode

    if (maven_deploy_result != 0):
        print('You deploy has abruptly failed.')
        print("Exiting program...")

    else:
        print("Your deploy is successful.")
        print("Your test is successful.\nExiting program...")

    clean_before_exit = input_y_or_n("Enter Y to clean workspace before exit, else enter N : ")

    if (clean_before_exit.lower() == 'y'):
        subprocess.os.chdir(os.path.join("..",".."))
        clean_workspace_and_exit("", Linux)

    print("Exiting program...\nExited")
    sys.exit()
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

# preparing and performing release

print("Preparing for release...")
print("Preparing and performing release...")

# -Dusername={user_name} -Dpassword={password1}
mvn_args = f"mvn release:prepare -DreleaseVersion={new_version} -DdevelopmentVersion={new_dev_version} -Dtag={new_tag} release:perform"

maven_release = subprocess.run(mvn_args, shell=True)
maven_release_result = maven_release.returncode

if (maven_release_result != 0):
    print('You release has abruptly failed.')
    print("Exiting program...")
    clean_before_exit = input_y_or_n("Enter Y to clean workspace before exit, else enter N : ")

    if (clean_before_exit.lower() == 'y'):
        subprocess.os.chdir(os.path.join("..",".."))
        clean_workspace_and_exit("", Linux)

    print("Exiting program...\nExited")
    sys.exit()

else:
    print("Your release is successful.")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

# fetch from jenkins github to merge into matlab github

print("Preparing to merge changes from jenkins github to matlab github...")
time.sleep(10)  # remove this line before deploy

print("Fetching from matlab repo's remote(i.e. jenkins github)...")
matlabs_remote.fetch()

postRelease_branch = myroot.find("postRelease")

if (postRelease_branch == None):
    print("No postRelease tag in your config.xml file. No branch to merge.")
    print("Successfully completed everything.")

else:
    total_branch = len(myroot.find("postRelease").findall('branchName'))
    if (total_branch == 0):
        print("No branch to merge. Successfully completed everything.")

    else:
        postRelease_branch = myroot.find("postRelease").findall('branchName')

        for branch in postRelease_branch:
            branch_name = branch.text

            try:
                print(f"Checking out local matlab repo's {branch_name} branch")
                matlab_repo.git.checkout(branch_name)
                print(
                    f"Merging changes from remote jenkins github master branch to local matlab repo's {branch_name} branch...")
                matlab_repo.git.merge(matlabs_remote.refs.master)
                print(f"Pushing changes from local matlab repo to remote matlab github's {branch_name} branch...")
                matlab_repo.git.push("origin", branch_name)
                print("Successfully pushed changes to remote matlab github.")

            except:
                print(f"Error while doing operations on matlabs {branch_name} branch.")
                print("Proceeding without completing operations on matlabs {branch_name} branch...")


        print("Completed everything.")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

#everything working, exiting program
print("Exiting program...")
clean_before_exit = input_y_or_n("Enter Y to clean workspace before exit, else enter N : ")

if(clean_before_exit.lower() == 'y'):
    print("Cleaning workspace...")
    subprocess.os.chdir(os.path.join("..",".."))
    #subprocess.run("rmdir /Q /S workspace" , shell = True)
    if Linux:
        subprocess.run("rm -rf workspace", shell=True)
    else:
        subprocess.run("rmdir /Q /S workspace", shell=True)

print("Exiting program...\nExited.")

########################################################################THE END#######################################
