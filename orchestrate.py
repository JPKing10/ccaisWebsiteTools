import sys
import logging
import subprocess

import update_project_publications

PUBLIST_PATH = "_data/publist.yml"


def main(repo_base_dir: str):
    """Update, commit and push the website publications in the specified repository. Assumes that the publication file
    is in '_data/publist.yml' and the branch is called 'master'."""
    logging.info("Updating publications in repository: %s", repo_base_dir)
    publist_path = "/".join([repo_base_dir, PUBLIST_PATH])
    try:
        subprocess.run(["git", "pull"], check=True, cwd=repo_base_dir)
        s = update_project_publications.main(publist_path)
        if s != 0:
            logging.error("Aborted publication update")
            return
        subprocess.run(["git", "add", publist_path], check=True, cwd=repo_base_dir)
        subprocess.run(["git", "commit", "-m", "Update publications"], check=True, cwd=repo_base_dir)
        subprocess.run(["git", "push", "origin", "master"], check=True, cwd=repo_base_dir)
    except subprocess.CalledProcessError as e:
        logging.error("Error with command '%s', status %s", e.cmd, e.returncode)
        logging.error("Aborted publication update")
        return
    logging.info("Publication updated pushed.")


if __name__ == '__main__':
    logging.basicConfig(filename="orchestration.log", level=logging.INFO)
    if 1 < len(sys.argv):
        main(sys.argv[1])
    else:
        logging.error("Repository base directory not specified")
        logging.info("Usage: orchestrate.py <repo_base_dir>")
