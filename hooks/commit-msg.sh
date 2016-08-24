#!/bin/bash

#
# This will check 5 from 'The seven rules of a great commit message'.
# See: http://chris.beams.io/posts/git-commit/
#
# To enable this hook, do from your repo root:
#       pushd .git/hooks
#       ln -s -f ../../hooks/commit-msg.sh commit-msg
#       popd
#

ERR1="Separate subject from body with a blank line"
ERR1_0="At least subject line should be specified"
ERR2="Limit the subject line to 50 characters"
ERR3="Capitalize the subject line"
ERR4="Do not end the subject line with a period"
ERR5="Use the imperative mood in the subject line" # not checked
ERR6="Wrap the body at 72 characters"
ERR7="Use the body to explain what and why vs. how" # not checked

# so that we know what we should check
STATE="subject"
COMMIT_MSG="$1"

function abort {
    echo >&2 "Malformed commit message: $1"
    if [[ $# > 1 ]]; then
        echo >&2 ""
        echo >&2 "$2"
        echo >&2 ""
    fi
    # be nice
    echo "Aborting commit.
HINT: commit message can be recovered from '.git/COMMIT_EDITMSG'"
    exit 1
}

function check_subject {
    ll=$1

    # Capitalize subject line (also catches subject lines
    # starting with whitespace)
    if [[ ! $ll =~ ^[A-Z].+$ ]]; then
        abort "$ERR3" "$ll"
    fi

    # Subject line length
    if [[ ! $ll =~ ^.{1,50}$ ]]; then
        abort "$ERR2" "$ll"
    fi

    # No peried at the end of subject line
    if [[ ${ll: -1:1} = "." ]]; then
        abort "$ERR4" "$ll"
    fi
}

function check_body {
    ll=$1

    # Body line length
    if [[ ! $ll =~ ^.{0,72}$ ]]; then
        abort "$ERR6" "$ll"
    fi
}


while IFS='' read -r line || [[ -n "$line" ]]; do
    # don't look further
    if [[ $line = "# ------------------------ >8 ------------------------" ]];then
        break
    fi

    case "$STATE" in
    subject)
        # whitespace only and comment lines are not checked
        if [[ ! $line =~ ^[[:space:]]*$ && ! $line =~ ^\#.*$ ]]; then
            check_subject "$line"
            STATE="separate"
        fi
        ;;
    separate)
        # whitespace only line found
        if [[ $line =~ ^[[:space:]]*$ ]]; then
            STATE="body"
        # we also accept comments here
        elif [[ ! $line =~ ^\#.*$ ]]; then
            abort "$ERR1"
        fi
        ;;
    body)
        # whitespace only and comment lines are not checked
        if [[ ! $line =~ ^[[:space:]]*$ && ! line =~ ^\#.*$ ]]; then
            check_body "$line"
        fi
        ;;
    esac
done < "$COMMIT_MSG"
