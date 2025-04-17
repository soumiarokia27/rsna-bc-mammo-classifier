#!/bin/bash

OLD_NAME="AhmedAzzi"
OLD_EMAIL="ahmed@example.com" # Put the exact email if known
NEW_NAME="Soumia Rokia"
NEW_EMAIL="soumia@example.com"

git filter-branch --env-filter '
if [ "$GIT_COMMITTER_NAME" = "'"$OLD_NAME"'" ]; then
    export GIT_COMMITTER_NAME="'"$NEW_NAME"'"
    export GIT_COMMITTER_EMAIL="'"$NEW_EMAIL"'"
fi
if [ "$GIT_AUTHOR_NAME" = "'"$OLD_NAME"'" ]; then
    export GIT_AUTHOR_NAME="'"$NEW_NAME"'"
    export GIT_AUTHOR_EMAIL="'"$NEW_EMAIL"'"
fi
' --tag-name-filter cat -- --branches --tags
