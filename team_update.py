#!/usr/bin/env python
"""Update the membership of a team based on GitHub attributes.

e.g. make a team of 'owners' or 'members'. The team must already exist -
see --help output for names
"""
import argparse
import logging
import sys

from client import get_github3_client
import github3


TEAM = "admin-all-org-"
VERBOSE = False
logger = logging.getLogger(__name__)


def team_name(user_type):
    global TEAM
    team_name = TEAM
    if team_name[-1] in "-_":
        team_name = TEAM + user_type
    return team_name


def update_team_membership(org, new_member_list, team_name=None, do_update=False):
    # we're using a team to communicate with these folks, update
    # that team to contain exactly new_member_list members
    # team must already exist in the org
    team = [x for x in org.teams() if x.name == team_name][0]
    # get set of current members
    current = {x.login for x in team.members()}
    # get set of new members
    new = {x.login for x in new_member_list}
    to_remove = current - new
    to_add = new - current
    no_change = new & current
    update_success = True
    print("%5d alumni" % len(to_remove))
    for login in to_remove:
        if do_update and not team.remove_member(login):
            logger.warn(
                "Failed to remove a member" " - you need 'admin:org' permissions"
            )
            update_success = False
            break
        if VERBOSE:
            print(f"    {login} has departed")
    print("%5d new" % len(to_add))
    for login in to_add:
        if VERBOSE:
            print(f"    {login} is new")
        try:
            if do_update and not team.add_member(login):
                logger.warn(
                    "Failed to add a member" " - you need 'admin:org' permissions"
                )
                update_success = False
                break
        except github3.exceptions.ForbiddenError:
            # this occurs occasionally, don't stop work
            logger.warn(f"Failed to add member '{login}'")
            update_success = False
    print("%5d no change" % len(no_change))
    # if we're running in the ipython notebook, the log message isn't
    # displayed. Output something useful
    if not update_success:
        print(f"Updates were not all made to team '{team_name}' in '{org.name}'.")
        print(
            "Make sure your API token has 'admin:org' permissions for that organization."
        )


def check_users(gh, org_name, admins_only=True, update_team=False):

    org = gh.organization(org_name)
    if not org:
        print("No such org found!")
        sys.exit(1)

    role = "admin" if admins_only else "all"
    user_type = "owners" if admins_only else "members"
    members = list(org.members(role=role))

    if members:
        print("There are %d %s for org %s:" % (len(members), user_type, org_name))
    else:
        print(f"Error: no {user_type} found for {org_name}")
    if update_team or VERBOSE:
        update_team_membership(org, members, team_name(user_type), update_team)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--owners",
        action="store_true",
        help="Report only for org owners (default all members)",
    )
    parser.add_argument(
        "orgs",
        nargs="*",
        default=[
            "mozilla",
        ],
        help="github organizations to check (defaults to mozilla)",
    )
    parser.add_argument(
        "--team",
        default=TEAM,
        help='update membership of team "%s{owners,members}"' % TEAM,
    )
    parser.add_argument(
        "--update-team", action="store_true", help="apply changes to GitHub"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="print logins for all changes"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    global VERBOSE
    VERBOSE = args.verbose
    global TEAM
    TEAM = args.team
    if args.orgs:
        gh = get_github3_client()
        for org in args.orgs:
            check_users(gh, org, args.owners, args.update_team)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format="%(asctime)s %(message)s")
    main()
