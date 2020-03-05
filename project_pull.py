from collections import namedtuple
import argparse
import getpass
import requests as r
import subprocess
from os import path, makedirs


Project = namedtuple('Project', ['name', 'web_url', 'ssh_url_to_repo'])
Project_pull_cmd = namedtuple('Project_pull_cmd', ['cmd', 'project'])


def extract_project(proj):
    return Project(name=proj['name'], web_url=proj['web_url'], ssh_url_to_repo=proj['ssh_url_to_repo'])


def get_projects(base_url_project_uri):
    page_index = 1

    while True:
        project_url_full = base_url_project_uri + str(page_index)
        resp = r.get(project_url_full)
        if resp.status_code == 200:
            jsonData = resp.json()
            if len(jsonData) == 0:
                print("No more projects in group...")
                return

            yield extract_project(jsonData[0])
            page_index += 1
        else:
            print("Got a non 200 response when attempting to retrieve data for: {}".format(project_url_full))
            return


def create_pull_cmd(project, destination_dir):
    return Project_pull_cmd(cmd=["git", "clone", project.ssh_url_to_repo, path.join(destination_dir, project.name)],
                                                                                 project=project)



def create_pull_cmds(projects, destination_dir):
    return [ create_pull_cmd(project, destination_dir) for project in projects ]


def run_pull_cmd(project_pull_cmd, ind, total_num_projects='*'):
    project = project_pull_cmd.project
    cmd = project_pull_cmd.cmd
    print(" ({}/{}) Pulling project: {}\n".format(str(ind + 1), str(total_num_projects), project.name) +
          "         Project URL: {}\n".format(project.web_url) +
          "         SSH URL: {}\n".format(project.ssh_url_to_repo))
    completed_proc = subprocess.run(cmd)

    if completed_proc.returncode != 0:
        print("FAILED to clone repo: (name={}, web_url={})".format(project.name, project.web_url))
        # break to fail fast on first clone error
        # break


def run_pull_cmds(project_pull_cmds):
    for (ind, project_pull_cmd) in enumerate(project_pull_cmds):
        run_pull_cmd(project_pull_cmd, ind, len(project_pull_cmds))


def run_clones(group_project_uri, destination_dir):
    """Make all GET requests for all project infos, clone all, done.
    """
    run_pull_cmds(create_pull_cmds(get_projects(group_project_uri), destination_dir))


def run_clones_lazy_get(group_project_uri, destination_dir):
    """Make a GET request for project info, clone, repeat until done. 
    """
    for (ind, project) in enumerate(get_projects(group_project_uri)):
        run_pull_cmd(create_pull_cmd(project, destination_dir), ind)


def arguments():
    ap = argparse.ArgumentParser(description='Pull all projects in a gitlab group.')
    ap.add_argument('--group-id', type=int, help='Group id for the gitlab project.', required=True)
    ap.add_argument('--destination-dir', type=str, help='Directory to clone projects to.', required=True)
    ap.add_argument('--host', type=str, default='gitlab.com', help='Host for the gitlab instance.')
    return ap.parse_args()


def get_group_projects_uri(host, group_id, access_token, per_page=1):
    return "https://{}/api/v4/groups/{}/projects?private_token={}&per_page={}&page=".format(host, group_id, access_token, per_page)


def make_dir_if_nexists(destination_dir):
    if not path.exists(destination_dir):
        makedirs(destination_dir)


def main():
    args = arguments()
    group_id = args.group_id
    host = args.host
    access_token = getpass.getpass(
        prompt='provide your gitlab acces token to obtain all projects (i.e. internal and private projects): '
    )   

    destination_dir = args.destination_dir
    group_project_uri = get_group_projects_uri(host, group_id, access_token)

    make_dir_if_nexists(destination_dir)

    run_clones_lazy_get(group_project_uri, destination_dir)

    # run_clones(group_project_uri, destination_dir)


if __name__ == '__main__':
    main()
