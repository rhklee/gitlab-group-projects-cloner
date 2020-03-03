from collections import namedtuple
import argparse
import requests as r
import subprocess
from os import path


Group = namedtuple('Group', ['id'])
Project = namedtuple('Project', ['name', 'web_url', 'ssh_url_to_repo'])
Project_pull_cmd = namedtuple('Project_pull_cmd', ['cmd', 'project'])


def extract_project(proj):
    return Project(name=proj['name'], web_url=proj['web_url'], ssh_url_to_repo=proj['ssh_url_to_repo'])


def get_projects(base_url_project_uri):
    page_index = 1
    projects = []

    while True:
        project_url_full = base_url_project_uri + str(page_index)
        resp = r.get(project_url_full)
        if resp.status_code == 200:
            jsonData = resp.json()
            if len(jsonData) == 0:
                break

            projects += list(map(extract_project, jsonData))
            page_index += 1
        else:
            print("Got a non 200 response when attempting to retrieve data for: {}".format(project_url_full))
            break

    return projects


def create_pull_cmds(projects, destination_dir):
    return [ Project_pull_cmd(cmd=["git", "clone", project.ssh_url_to_repo, path.join(destination_dir, project.name)],
                                                                                 project=project) for project in projects ]


def run_pull_cmds(project_pull_cmds):
    for (ind, project_pull_cmd) in enumerate(project_pull_cmds):
        project = project_pull_cmd.project
        cmd = project_pull_cmd.cmd
        print(" ({}/{}) Pulling project: {}\n".format(str(ind + 1), str(len(project_pull_cmds)), project.name) +
              "         Project URL: {}\n".format(project.web_url) +
              "         SSH URL: {}\n".format(project.ssh_url_to_repo))
        completed_proc = subprocess.run(cmd)

        if completed_proc.returncode != 0:
            print("FAILED to clone repo: (name={}, web_url={})".format(project.name, project.web_url))
            # break to fail fast on first clone error
            # break


def arguments():
    ap = argparse.ArgumentParser(description='Pull all projects in a gitlab group.')
    ap.add_argument('--group-id', type=int, help='Group id for the gitlab project.', required=True)
    ap.add_argument('--destination-dir', type=str, help='Directory to clone projects to.', required=True)
    ap.add_argument('--host', type=str, default='gitlab.com', help='Host for the gitlab instance.')
    return ap.parse_args()


def main():
    args = arguments()
    group = Group(id=args.group_id)
    host = args.host
    base_url_project_uri = "https://{}/api/v4/groups/{}/projects?page=".format(host, group.id)

    run_pull_cmds(create_pull_cmds(get_projects(base_url_project_uri), args.destination_dir))


if __name__ == '__main__':
    main()
